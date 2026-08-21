from __future__ import annotations

import re
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import quote, urljoin

import requests
from selectolax.parser import HTMLParser

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

BASE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "no-cache",
}


@dataclass
class ScrapedItem:
    name: str
    url: str
    price: Decimal | None = None
    brand_name: str | None = None
    category_path: str | None = None


class ScraperError(Exception):
    pass


class BaseScraper:
    store_slug = ""
    store_name = ""
    website_url = ""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(BASE_HEADERS)
        self.session.headers["Referer"] = self.website_url

    def fetch(self, url: str, *, retries: int = 3, headers: dict | None = None) -> str:
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=25, headers=headers)
                if response.status_code == 200:
                    return response.text
                last_error = ScraperError(f"HTTP {response.status_code} em {url}")
                if response.status_code in (403, 429, 503):
                    time.sleep(3 * (attempt + 1))
                    continue
                break
            except requests.RequestException as exc:
                last_error = exc
                time.sleep(3 * (attempt + 1))
        raise ScraperError(f"Falha ao acessar {url}: {last_error}")

    def search(self, query: str, page: int = 1) -> list[ScrapedItem]:
        html = self.fetch(self.search_url(query, page))
        seen: set[str] = set()
        unique: list[ScrapedItem] = []
        for item in self.parse(html):
            if item.url in seen:
                continue
            seen.add(item.url)
            unique.append(item)
        return unique

    def search_url(self, query: str, page: int) -> str:
        raise NotImplementedError

    def parse(self, html: str) -> list[ScrapedItem]:
        raise NotImplementedError

    def absolute_url(self, href: str | None) -> str | None:
        if not href:
            return None
        return urljoin(self.website_url, href)

    @staticmethod
    def clean_name(text: str | None) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def parse_price(text: str | float | Decimal | None) -> Decimal | None:
        if text is None or text == "":
            return None
        if isinstance(text, Decimal):
            return text
        if isinstance(text, (int, float)):
            return Decimal(str(text))
        cleaned = re.sub(r"[^\d.,]", "", text)
        if not cleaned:
            return None
        if "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    @staticmethod
    def first_text(node, selector: str) -> str | None:
        if node is None:
            return None
        found = node.css_first(selector)
        return found.text(strip=True) if found else None
