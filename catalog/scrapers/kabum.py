from __future__ import annotations

import json
import re
from urllib.parse import quote

from .base import BaseScraper, ScrapedItem

NEXT_DATA_PATTERN = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S
)


class KabumScraper(BaseScraper):
    store_slug = "kabum"
    store_name = "KaBuM!"
    website_url = "https://www.kabum.com.br"

    def search_url(self, query: str, page: int) -> str:
        suffix = f"?page_number={page}" if page > 1 else ""
        return f"{self.website_url}/busca/{quote(query)}{suffix}"

    def parse(self, html: str) -> list[ScrapedItem]:
        match = NEXT_DATA_PATTERN.search(html)
        if not match:
            return []

        try:
            data = json.loads(match.group(1))
            entries = data["props"]["pageProps"]["data"]["catalogServer"]["data"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return []

        items: list[ScrapedItem] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("available") is False:
                continue
            name = self.clean_name(entry.get("name"))
            code = entry.get("code")
            friendly = entry.get("friendlyName") or "p"
            url = f"{self.website_url}/produto/{code}/{friendly}"
            price = self.parse_price(
                entry.get("priceWithDiscount") or entry.get("price")
            )
            original_price = self.parse_price(entry.get("oldPrice"))
            discount_pct = entry.get("discountPercentage") or 0
            try:
                is_promo = float(discount_pct) > 0 and (
                    original_price is None or price is None or original_price > price
                )
            except (TypeError, ValueError):
                is_promo = False
            manufacturer = entry.get("manufacturer") or {}
            brand_name = self.clean_name(manufacturer.get("name")) or None
            category_path = self.clean_name(entry.get("category")) or None
            image_url = self.clean_name(
                entry.get("thumbnail") or entry.get("image")
            ) or None
            if not name or not code:
                continue
            items.append(
                ScrapedItem(
                    name=name,
                    url=url,
                    price=price,
                    brand_name=brand_name,
                    category_path=category_path,
                    image_url=image_url,
                    original_price=original_price,
                    is_promo=is_promo,
                )
            )

        return items
