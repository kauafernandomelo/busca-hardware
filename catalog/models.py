from decimal import Decimal

from django.db import models
from django.utils.text import slugify


class Store(models.Model):
    name = models.CharField("nome", max_length=120, unique=True)
    slug = models.SlugField("slug", max_length=140, unique=True, blank=True)
    website_url = models.URLField("site", blank=True)
    logo_url = models.URLField("logo", blank=True)
    is_active = models.BooleanField("ativa", default=True)
    created_at = models.DateTimeField("criada em", auto_now_add=True)

    class Meta:
        verbose_name = "loja"
        verbose_name_plural = "lojas"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Brand(models.Model):
    name = models.CharField("nome", max_length=120, unique=True)
    slug = models.SlugField("slug", max_length=140, unique=True, blank=True)
    logo_url = models.URLField("logo", blank=True)

    class Meta:
        verbose_name = "marca"
        verbose_name_plural = "marcas"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Category(models.Model):
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="categoria pai",
    )
    name = models.CharField("nome", max_length=120)
    slug = models.SlugField("slug", max_length=140, unique=True, blank=True)
    icon = models.CharField("ícone", max_length=40, blank=True)
    description = models.TextField("descrição", blank=True)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "slug"], name="unique_slug_per_parent"
            )
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug, i = base_slug, 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base_slug}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField("nome", max_length=255)
    slug = models.SlugField("slug", max_length=280, unique=True, blank=True)
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="marca",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="categoria",
    )
    image_url = models.URLField("imagem", blank=True)
    specs = models.JSONField("especificações", default=dict, blank=True)
    is_active = models.BooleanField("ativo", default=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "produto"
        verbose_name_plural = "produtos"
        ordering = ["name"]
        indexes = [models.Index(fields=["category"], name="idx_product_category")]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:280]
            slug, i = base_slug, 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                suffix = f"-{i}"
                slug = f"{base_slug[:280 - len(suffix)]}{suffix}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def best_offer(self):
        return (
            self.offers.filter(is_available=True, current_price__isnull=False)
            .select_related("store")
            .order_by("current_price")
            .first()
        )

    @property
    def offers_count(self):
        return self.offers.filter(is_available=True).count()


class Offer(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name="produto",
    )
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name="offers", verbose_name="loja"
    )
    url = models.URLField("URL da oferta")
    current_price = models.DecimalField(
        "preço atual",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
    )
    is_available = models.BooleanField("disponível", default=True)
    last_checked_at = models.DateTimeField("última verificação", null=True, blank=True)
    created_at = models.DateTimeField("criada em", auto_now_add=True)

    class Meta:
        verbose_name = "oferta"
        verbose_name_plural = "ofertas"
        ordering = ["current_price"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "store"], name="unique_product_per_store"
            )
        ]

    def __str__(self):
        return f"{self.product} @ {self.store}"

    @property
    def lowest_price_30d(self):
        agg = self.snapshots.aggregate(v=models.Min("price"))
        return agg["v"]


class PriceSnapshot(models.Model):
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name="snapshots",
        verbose_name="oferta",
    )
    price = models.DecimalField("preço", max_digits=12, decimal_places=2)
    captured_at = models.DateTimeField("capturado em", db_index=True)

    class Meta:
        verbose_name = "snapshot de preço"
        verbose_name_plural = "snapshots de preço"
        ordering = ["-captured_at"]

    def __str__(self):
        return f"{self.offer} - R$ {self.price} em {self.captured_at:%d/%m/%Y %H:%M}"


class PriceAlert(models.Model):
    email = models.EmailField("e-mail")
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="alerts",
        verbose_name="produto",
    )
    target_price = models.DecimalField(
        "preço alvo", max_digits=12, decimal_places=2
    )
    is_active = models.BooleanField("ativo", default=True)
    notified_at = models.DateTimeField("notificado em", null=True, blank=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "alerta de preço"
        verbose_name_plural = "alertas de preço"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} aguardando {self.product} <= R$ {self.target_price}"
