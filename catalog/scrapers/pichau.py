from __future__ import annotations

import json
from urllib.parse import quote

from .base import BaseScraper, ScrapedItem

PRODUCTS_MARKER = '"products":{"items":'


class PichauScraper(BaseScraper):
    store_slug = "pichau"
    store_name = "Pichau"
    website_url = "https://www.pichau.com.br"

    def search(self, query: str, page: int = 1) -> list[ScrapedItem]:
        payload = self.fetch(
            self.search_url(query, page),
            headers={"RSC": "1", "Accept": "text/x-component"},
        )
        return self.parse(payload)

    def search_url(self, query: str, page: int) -> str:
        suffix = f"&page={page}" if page > 1 else ""
        return f"{self.website_url}/search?q={quote(query)}{suffix}"

    def parse(self, html: str) -> list[ScrapedItem]:
        marker_idx = html.find(PRODUCTS_MARKER)
        if marker_idx < 0:
            return []

        array_start = marker_idx + len(PRODUCTS_MARKER)
        try:
            raw = self._extract_balanced(html, array_start)
            entries = json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            return []

        items: list[ScrapedItem] = []
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("hide_from_search"):
                continue
            stock = entry.get("stock_status")
            if stock and stock != "IN_STOCK":
                continue
            name = self.clean_name(entry.get("name"))
            url_key = entry.get("url_key")
            url = f"{self.website_url}/{url_key}" if url_key else None
            prices = entry.get("pichau_prices") or {}
            price = (
                self.parse_price(prices.get("avista"))
                or self.parse_price(entry.get("special_price"))
                or self.parse_price(prices.get("final_price"))
            )
            special = self.parse_price(entry.get("special_price"))
            final = self.parse_price(prices.get("final_price"))
            is_promo = special is not None and final is not None and special < final
            original_price = special if is_promo else None
            image = entry.get("image") or {}
            image_url = self.clean_name(image.get("url")) or None
            if not name or not url:
                continue
            items.append(
                ScrapedItem(
                    name=name,
                    url=url,
                    price=price,
                    image_url=image_url,
                    original_price=original_price,
                    is_promo=is_promo,
                )
            )

        return items

    @staticmethod
    def _extract_balanced(source: str, start: int) -> str:
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(source)):
            ch = source[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
                if depth == 0:
                    return source[start : i + 1]
        raise ValueError("payload RSC não balanceado")
