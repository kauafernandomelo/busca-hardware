# Busca Hardware

Comparador de preços de hardware que monitora **KaBuM!**, **Terabyte**, **GK Infostore** e **Patoloco**, detecta promoções automaticamente e avisa por e-mail.

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.x-06B6D4?logo=tailwindcss&logoColor=white)

## Sobre

Sistema completo de monitoramento de preços com coleta automatizada, alertas por e-mail e interface de marketplace.

## Funcionalidades

- Busca unificada de produtos com ordenação por preço e desconto
- Página de promoções com maiores descontos
- Histórico de preços com gráfico e destaque para "melhor preço desde o primeiro registro"
- Alertas de preço-alvo por e-mail
- Assinaturas de promoção por categoria ou produto
- Buy-box comparativo entre lojas
- SEO com dados estruturados schema.org (JSON-LD)

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Django 6.1 |
| Frontend | Django Templates + Tailwind CSS 4 |
| Scraping | requests + selectolax, retries/backoff |
| Banco | SQLite (dev) / PostgreSQL (produção) |
| Deploy | Render (Gunicorn + Whitenoise) |
| CI/CD | GitHub Actions (coleta a cada 6h) |

## Scrapers

| Loja | Estratégia |
|---|---|
| KaBuM | JSON embutido em `<script id="__NEXT_DATA__">` |
| Terabyte | HTML renderizado (`div.product-item` + atributos `data-tss-*`) |
| GK Infostore | HTML Loja Integrada (`div.listagem-item`, preço via `data-sell-price`) |
| Patoloco | HTML Tray (`form.form-ajax-adicionar-ao-carrinho`, `price-old`/`price-new`) |

## Estrutura

```
catalog/
├── models.py
├── scrapers/
├── templatetags/
└── management/commands/
config/settings.py
templates/
theme/
render.yaml
```

## Licença

[MIT](LICENSE)
