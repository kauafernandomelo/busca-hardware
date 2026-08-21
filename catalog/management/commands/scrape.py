from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify

from catalog.models import Brand, Category, Offer, PriceSnapshot, Product, Store
from catalog.scrapers import SCRAPERS, ScrapedItem, ScraperError


class Command(BaseCommand):
    help = "Importa produtos e ofertas das lojas suportadas via scraping."

    def add_arguments(self, parser):
        parser.add_argument("--store", help="slug da loja (kabum, pichau, terabyte)")
        parser.add_argument(
            "--all", action="store_true", help="executa todas as lojas suportadas"
        )
        parser.add_argument("--query", required=True, help="termo de busca")
        parser.add_argument(
            "--category",
            default="outros",
            help="categoria atribuída aos produtos importados",
        )
        parser.add_argument("--pages", type=int, default=1)
        parser.add_argument("--limit", type=int, default=40)
        parser.add_argument(
            "--dry-run", action="store_true", help="não grava nada no banco"
        )

    def handle(self, *args, **options):
        if options["all"]:
            slugs = sorted(SCRAPERS)
        elif options["store"]:
            slugs = [options["store"].strip().lower()]
        else:
            raise CommandError("Informe --store <slug> ou use --all.")

        unknown = [slug for slug in slugs if slug not in SCRAPERS]
        if unknown:
            raise CommandError(
                f"Loja desconhecida: {', '.join(unknown)}. "
                f"Disponíveis: {', '.join(sorted(SCRAPERS))}."
            )

        category = self.get_category(options["category"])
        totals = {"products": 0, "offers": 0, "snapshots": 0}

        for slug in slugs:
            stats = self.import_store(slug, options["query"], category, options)
            for key in totals:
                totals[key] += stats[key]

        if not options["dry_run"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Concluído: {totals['products']} produto(s) novo(s), "
                    f"{totals['offers']} oferta(s) atualizada(s), "
                    f"{totals['snapshots']} snapshot(s)."
                )
            )

    def get_category(self, name: str) -> Category:
        slug = slugify(name)
        category = Category.objects.filter(slug=slug).first() or Category.objects.filter(
            name__iexact=name.strip()
        ).first()
        if category is None:
            category = Category.objects.create(name=name.strip().title())
            self.stdout.write(f"Categoria criada: {category}")
        return category

    def import_store(self, slug: str, query: str, category: Category, options) -> dict:
        scraper = SCRAPERS[slug]()
        dry_run = options["dry_run"]
        limit = max(1, options["limit"])

        store = Store.objects.filter(slug=slug).first()
        if store is None and not dry_run:
            store = Store.objects.create(
                name=scraper.store_name, website_url=scraper.website_url
            )

        self.stdout.write(self.style.MIGRATE_HEADING(f"[{scraper.store_name}] buscando '{query}'..."))

        try:
            items: list[ScrapedItem] = []
            for page in range(1, max(1, options["pages"]) + 1):
                items.extend(scraper.search(query, page))
        except ScraperError as exc:
            self.stdout.write(self.style.ERROR(f"[{scraper.store_name}] {exc}"))
            return {"products": 0, "offers": 0, "snapshots": 0}

        now = timezone.now()
        stats = {"products": 0, "offers": 0, "snapshots": 0}

        for item in items[:limit]:
            product = self.get_or_create_product(item, category, dry_run, stats)
            if product is None or store is None:
                continue
            if item.price is None:
                continue

            discount_pct = None
            if item.original_price and item.original_price > item.price:
                discount_pct = round(
                    (1 - item.price / item.original_price) * 100, 1
                )

            offer, created = Offer.objects.update_or_create(
                product=product,
                store=store,
                defaults={
                    "url": item.url,
                    "current_price": item.price,
                    "original_price": item.original_price,
                    "discount_pct": discount_pct,
                    "is_promo": bool(item.is_promo or discount_pct),
                    "is_available": True,
                    "last_checked_at": now,
                },
            )
            if created:
                stats["offers"] += 1
            last_snapshot = offer.snapshots.order_by("-captured_at").first()
            if last_snapshot is None or last_snapshot.price != item.price:
                PriceSnapshot.objects.create(
                    offer=offer, price=item.price, captured_at=now
                )
                stats["snapshots"] += 1

        self.stdout.write(
            f"[{scraper.store_name}] {len(items)} resultado(s); "
            f"{stats['products']} produto(s) novo(s), "
            f"{stats['snapshots']} snapshot(s)."
        )
        return stats

    def get_or_create_product(
        self, item: ScrapedItem, category: Category, dry_run: bool, stats: dict
    ) -> Product | None:
        existing = Product.objects.filter(name__iexact=item.name).first()
        if existing:
            if item.image_url and not existing.image_url:
                existing.image_url = item.image_url
                existing.save(update_fields=["image_url"])
            return existing
        if dry_run:
            return None

        brand = None
        brand_name = item.brand_name or self.guess_brand(item.name)
        if brand_name:
            brand = Brand.objects.filter(name__iexact=brand_name).first() or (
                Brand.objects.create(name=brand_name)
            )

        product_category = category
        if item.category_path:
            leaf = item.category_path.split("/")[-1].strip()
            if leaf and leaf.lower() != category.name.lower():
                cat_slug = slugify(leaf)
                product_category = (
                    Category.objects.filter(slug=cat_slug).first()
                    or Category.objects.filter(name__iexact=leaf).first()
                    or Category.objects.create(name=leaf)
                )

        product = Product.objects.create(
            name=item.name,
            brand=brand,
            category=product_category,
            image_url=item.image_url or "",
        )
        stats["products"] += 1
        return product

    @staticmethod
    def guess_brand(name: str) -> str | None:
        known = [
            "Asus", "MSI", "Gigabyte", "EVGA", "Zotac", "Galax", "AMD", "Intel",
            "Ryzen", "Radeon", "Nvidia", "Corsair", "Kingston", "HyperX", "Crucial",
            "Samsung", "Western Digital", "WD", "Seagate", "Adata", "XPG", "Logitech",
            "Redragon", "Razer", "Hyperx", "Aorus", "Evolut", "Dell", "Lenovo", "Acer",
        ]
        lowered = name.lower()
        for brand in known:
            if lowered.startswith(brand.lower()) or f" {brand.lower()} " in lowered:
                return brand.title() if brand.lower() != "wd" else "WD"
        return None
