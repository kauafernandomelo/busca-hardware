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

## Como rodar

```bash
# Clone o repositório
git clone https://github.com/kauafernandomelo/busca-hardware.git
cd busca-hardware

# Ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# Dependências
pip install -r requirements.txt

# Variáveis de ambiente (crie um .env na raiz)
# DJANGO_SECRET_KEY=<sua-chave>
# DJANGO_DEBUG=1

# Banco de dados
python manage.py migrate

# Build do CSS (primeira vez)
cd theme/static_src && npm install && cd ../..
python manage.py tailwind build

# Popular catálogo (~500 produtos)
python manage.py import_catalog --all

# Rodar
python manage.py runserver
```

## Comandos úteis

| Comando | Função |
|---|---|
| `import_catalog --all` | Importa catálogo completo |
| `scrape --store kabum --query "rtx 4070"` | Coleta por termo de busca |
| `check_alerts` | Verifica alertas e envia e-mails |
| `check_promotions` | Detecta promoções e notifica assinantes |

