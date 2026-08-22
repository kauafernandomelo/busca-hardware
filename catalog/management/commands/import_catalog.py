from __future__ import annotations

import time
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify

from catalog.models import Brand, Category, Offer, PriceSnapshot, Product, Store
from catalog.scrapers import SCRAPERS, ScrapedItem, ScraperError

# Dicionário curado: categoria -> termos de busca usados em todas as lojas.
CATALOG = {
    "Placas de Vídeo": ["rtx 4060", "rx 7600", "rtx 4070", "rx 7800 xt"],
    "Processadores": ["ryzen 5 5600", "ryzen 5 7500f", "i5 12400f"],
    "Memórias RAM": ["ddr4 16gb", "ddr5 16gb"],
    "SSDs": ["ssd nvme 500gb", "ssd nvme 1tb", "ssd nvme 2tb"],
    "Monitores": ["monitor 144hz 24", "monitor 144hz 27"],
    "Fontes": ["fonte 650w", "fonte 750w"],
    "Placas-Mãe": ["placa mãe b550", "placa mãe am5"],
    "Notebooks": ["notebook gamer"],
    "Teclados": ["teclado mecânico"],
    "Mouses": ["mouse gamer"],
    "Headsets": ["headset gamer"],
    "Coolers": ["water cooler", "air cooler"],
    "Gabinetes": ["gabinete gamer"],
}


class Command(BaseCommand):
    help = (
        "Popula o catálogo com um dicionário curado de categorias e buscas "
        "em todas as lojas suportadas."
    )

    def add_arguments(self, parser):
        parser.add_argument("--store", help="slug da loja (kabum, pichau, terabyte)")
        parser.add_argument(
            "--all", action="store_true", help="executa todas as lojas suportadas"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=8,
            help="máximo de produtos por busca em cada loja (padrão: 8)",
        )
        parser.add_argument(
            "--category",
            help="processa apenas a categoria informada (nome exato do dicionário)",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=1.0,
            help="pausa em segundos entre buscas (educação com o servidor)",
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="não grava nada no banco"
        )

    def handle(self, *args, **options):
        if options["all"]:
            store_slugs = sorted(SCRAPERS)
        elif options["store"]:
            store_slugs = [options["store"].strip().lower()]
        else:
            raise CommandError("Informe --store <slug> ou use --all.")

        unknown = [s for s in store_slugs if s not in SCRAPERS]
        if unknown:
            raise CommandError(
                f"Loja desconhecida: {', '.join(unknown)}. "
                f"Disponíveis: {', '.join(sorted(SCRAPERS))}."
            )

        wanted = options["category"]
        categories = {
            name: queries
            for name, queries in CATALOG.items()
            if not wanted or name.lower() == wanted.strip().lower()
        }
        if wanted and not categories:
            raise CommandError(
                f"Categoria '{wanted}' não está no dicionário. Opções: "
                f"{'; '.join(CATALOG)}"
            )

        totals = {"categories": len(categories), "queries": 0, "products": 0, "offers": 0, "snapshots": 0}
        started = timezone.now()

        for cat_name, queries in categories.items():
            category = self.get_or_create_category(cat_name)
            self.stdout.write(self.style.MIGRATE_HEADING(f"== {cat_name} =="))

            for slug in store_slugs:
                stats = self.import_store(slug, category, queries, options)
                totals["queries"] += stats["queries"]
                totals["products"] += stats["products"]
                totals["offers"] += stats["offers"]
                totals["snapshots"] += stats["snapshots"]

        minutes = (timezone.now() - started).total_seconds() / 60
        if not options["dry_run"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Concluído em {minutes:.1f} min: {totals['products']} produto(s) novo(s), "
                    f"{totals['offers']} oferta(s) atualizada(s), {totals['snapshots']} snapshot(s) "
                    f"em {totals['queries']} busca(s)."
                )
            )

    def get_or_create_category(self, name: str) -> Category:
        slug = slugify(name)
        category = Category.objects.filter(slug=slug).first()
        if category is None:
            category = Category.objects.create(name=name)
            self.stdout.write(f"  categoria criada: {name}")
        return category

    def import_store(self, slug: str, category: Category, queries: list[str], options) -> dict:
        scraper = SCRAPERS[slug]()
        dry_run = options["dry_run"]
        limit = max(1, options["limit"])
        sleep_s = max(0.0, options["sleep"])

        store = Store.objects.filter(slug=slug).first()
        if store is None and not dry_run:
            store = Store.objects.create(
                name=scraper.store_name, website_url=scraper.website_url
            )

        stats = {"queries": 0, "products": 0, "offers": 0, "snapshots": 0}
        now = timezone.now()

        for query in queries:
            stats["queries"] += 1
            try:
                items: list[ScrapedItem] = scraper.search(query, page=1)
            except ScraperError as exc:
                self.stdout.write(self.style.WARNING(f"  [{slug}] erro em '{query}': {exc}"))
                continue
            finally:
                if sleep_s:
                    time.sleep(sleep_s)

            imported = 0
            for item in items[:limit]:
                if item.price is None:
                    continue
                result = self.import_item(item, store, category, dry_run)
                if result is None:
                    continue
                created_product, created_offer, created_snapshot = result
                stats["products"] += int(created_product)
                stats["offers"] += int(created_offer)
                stats["snapshots"] += int(created_snapshot)
                imported += 1

            self.stdout.write(f"  [{slug}] '{query}': {len(items)} resultado(s), {imported} aproveitado(s)")

        return stats

    def import_item(self, item: ScrapedItem, store: Store | None, category: Category, dry_run: bool):
        if dry_run or store is None:
            return None

        brand = None
        if item.brand_name:
            brand = Brand.objects.filter(name__iexact=item.brand_name).first() or Brand.objects.create(
                name=item.brand_name
            )

        product = Product.objects.filter(name__iexact=item.name).first()
        created_product = False
        if product is None:
            product = Product.objects.create(
                name=item.name, brand=brand, category=category, image_url=item.image_url or ""
            )
            created_product = True
        elif item.image_url and not product.image_url:
            product.image_url = item.image_url
            product.save(update_fields=["image_url"])

        discount_pct = None
        if item.original_price and item.original_price > item.price:
            discount_pct = round((1 - item.price / item.original_price) * 100, 1)

        offer, created_offer_flag = Offer.objects.update_or_create(
            product=product,
            store=store,
            defaults={
                "url": item.url,
                "current_price": item.price,
                "original_price": item.original_price,
                "discount_pct": discount_pct,
                "is_promo": bool(item.is_promo or discount_pct),
                "is_available": True,
                "last_checked_at": timezone.now(),
            },
        )
        created_offer = bool(created_offer_flag)

        last_snapshot = offer.snapshots.order_by("-captured_at").first()
        created_snapshot = False
        if last_snapshot is None or Decimal(last_snapshot.price) != Decimal(item.price):
            PriceSnapshot.objects.create(offer=offer, price=item.price, captured_at=timezone.now())
            created_snapshot = True

        return created_product, created_offer, created_snapshot
