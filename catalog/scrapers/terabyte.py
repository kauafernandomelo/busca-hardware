from __future__ import annotations

from urllib.parse import quote

from selectolax.parser import HTMLParser

from .base import BaseScraper, ScrapedItem


class TerabyteScraper(BaseScraper):
    store_slug = "terabyte"
    store_name = "Terabyte"
    website_url = "https://www.terabyteshop.com.br"

    def search_url(self, query: str, page: int) -> str:
        suffix = f"&pagina={page}" if page > 1 else ""
        return f"{self.website_url}/busca?str={quote(query)}{suffix}"

    def parse(self, html: str) -> list[ScrapedItem]:
        tree = HTMLParser(html)
        items: list[ScrapedItem] = []

        for card in tree.css("div.product-item"):
            link = card.css_first("a.product-item__name[href]") or card.css_first(
                "a[href*='/produto/']"
            )
            if link is None:
                continue
            url = self.absolute_url(link.attributes.get("href"))
            name_el = card.css_first("h2") or link
            name = self.clean_name(
                name_el.text(strip=True) if name_el else None
            ) or self.clean_name(link.attributes.get("title"))

            price = self.parse_price(card.attributes.get("data-tss-price"))
            if price is None:
                price = self.parse_price(
                    self.first_text(card, "div.product-item__new-price span")
                )

            brand_name = self.clean_name(card.attributes.get("data-tss-brand")) or None

            if not name or not url:
                continue
            items.append(ScrapedItem(name=name, url=url, price=price, brand_name=brand_name))

        return items
