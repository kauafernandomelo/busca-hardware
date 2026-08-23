from __future__ import annotations

from urllib.parse import urlencode

from selectolax.parser import HTMLParser

from .base import BaseScraper, ScrapedItem


class GkInfostoreScraper(BaseScraper):
    """Loja Integrada: listagem server-side com preco de/por e classe de promocao."""

    store_slug = "gkinfostore"
    store_name = "GK Infostore"
    website_url = "https://www.gkinfostore.com.br"

    def search_url(self, query: str, page: int) -> str:
        suffix = f"&pagina={page}" if page > 1 else ""
        return f"{self.website_url}/buscar?{urlencode({'q': query})}{suffix}"

    def parse(self, html: str) -> list[ScrapedItem]:
        tree = HTMLParser(html)
        items: list[ScrapedItem] = []

        for card in tree.css("div.listagem-item"):
            classes = card.attributes.get("class") or ""
            if "indisponivel" in classes:
                continue

            link = card.css_first("a.produto-sobrepor[href]") or card.css_first(
                "a.nome-produto[href]"
            )
            if link is None:
                continue
            url = self.absolute_url(link.attributes.get("href"))

            name_el = card.css_first("a.nome-produto")
            name = self.clean_name(
                name_el.text(strip=True) if name_el else None
            ) or self.clean_name(link.attributes.get("title"))

            price_el = card.css_first("strong.preco-promocional[data-sell-price]")
            price = self.parse_price(
                price_el.attributes.get("data-sell-price") if price_el else None
            )
            if price is None:
                price = self.parse_price(self.first_text(card, "strong.preco-promocional"))

            original_price = self.parse_price(
                self.first_text(card, "s.preco-venda")
            )

            is_promo = card.css_first("div.preco-produto.com-promocao") is not None or (
                original_price is not None
                and price is not None
                and original_price > price
            )

            image_el = card.css_first("img.imagem-principal[src]") or card.css_first(
                "img[src]"
            )
            image_url = self.clean_name(
                image_el.attributes.get("src") if image_el else None
            ) or None

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
