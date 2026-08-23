from .base import BaseScraper, ScrapedItem, ScraperError
from .gkinfostore import GkInfostoreScraper
from .kabum import KabumScraper
from .patoloco import PatolocoScraper
from .pichau import PichauScraper
from .terabyte import TerabyteScraper

SCRAPERS = {
    scraper.store_slug: scraper
    for scraper in (
        GkInfostoreScraper,
        KabumScraper,
        PatolocoScraper,
        PichauScraper,
        TerabyteScraper,
    )
}

__all__ = [
    "BaseScraper",
    "ScrapedItem",
    "ScraperError",
    "GkInfostoreScraper",
    "KabumScraper",
    "PatolocoScraper",
    "PichauScraper",
    "TerabyteScraper",
    "SCRAPERS",
]
