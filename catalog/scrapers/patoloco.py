from __future__ import annotations

import re
from urllib.parse import urlencode

from selectolax.parser import HTMLParser

from .base import BaseScraper, ScrapedItem

_PRICE_RE = re.compile(r"R\$\s*([\d.,]+)")


class PatolocoScraper(BaseScraper):
    """Plataforma Tray: cards server-side com price-old/price-new e tag de desconto."""

    store_slug = "patoloco"
    store_name = "Patoloco"
    website_url = "https://patoloco.com.br"

    def search_url(self, query: str, page: int) -> str:
        qs = urlencode({"buscar-por": query})
        if page > 1:
            return f"{self.website_url}/busca/{page}/?{qs}"
        return f"{self.website_url}/busca/?{qs}"

    def parse(self, html: str) -> list[ScrapedItem]:
        tree = HTMLParser(html)
        items: list[ScrapedItem] = []

        for card in tree.css("form.form-ajax-adicionar-ao-carrinho"):
            link = card.css_first("a[href][title]")
            if link is None:
                continue
            url = self.absolute_url(link.attributes.get("href"))
            name = self.clean_name(link.attributes.get("title"))

            name_el = card.css_first("h3.tit")
            if not name and name_el:
                name = self.clean_name(name_el.text(strip=True))

            image_el = card.css_first("img[src]")
            image_url = self.clean_name(
                image_el.attributes.get("src") if image_el else None
            ) or None

            original_price = self.parse_price(
                self.first_text(card, "p.price-old del")
            )
            price_text = self.first_text(card, "p.price-new")
            price = None
            if price_text:
                match = _PRICE_RE.search(price_text)
                if match:
                    price = self.parse_price(match.group(1))

            is_promo = original_price is not None and price is not None and (
                original_price > price
            )

            if not name or not url or price is None:
                continue
            items.append(
                ScrapedItem(
                    name=name,
                    url=url,
                    price=price,
                    image_url=image_url,
                    original_price=original_price if is_promo else None,
                    is_promo=is_promo,
                )
            )

        return items
