from .base import BaseScraper, ScrapedItem, ScraperError
from .kabum import KabumScraper
from .pichau import PichauScraper
from .terabyte import TerabyteScraper

SCRAPERS = {
    scraper.store_slug: scraper
    for scraper in (KabumScraper, PichauScraper, TerabyteScraper)
}

__all__ = [
    "BaseScraper",
    "ScrapedItem",
    "ScraperError",
    "KabumScraper",
    "PichauScraper",
    "TerabyteScraper",
    "SCRAPERS",
]
