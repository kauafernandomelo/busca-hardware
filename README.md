# Busca Hardware

Comparador de preços de hardware que monitora **KaBuM!**, **Pichau** e **Terabyte**, detecta promoções automaticamente e avisa por e-mail quando o produto que você quer fica barato.

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.x-06B6D4?logo=tailwindcss&logoColor=white)

## Funcionalidades

- **Busca unificada** de produtos nas três lojas, com ordenação por preço e desconto
- **Página de promoções** com os maiores descontos detectados na última coleta
- **Histórico de preços** com gráfico por dia e destaque para "melhor preço desde o primeiro registro"
- **Alertas de preço-alvo**: e-mail quando o menor preço fica igual ou abaixo do valor escolhido
- **Assinaturas de promoção** por categoria ou por produto, com desconto mínimo configurável
- **Buy-box comparativo** entre lojas por produto, com preços formatados em pt-BR
- Dados estruturados **schema.org (JSON-LD)** para SEO

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Django 6.1 (sem dependências pesadas) |
| Front-end | Django Templates + Tailwind CSS 4 (via django-tailwind) |
| Scraping | requests + selectolax, com retries/backoff contra WAF |
| Banco | SQLite (portátil, trocável por PostgreSQL) |

## Como funciona a coleta

Cada loja tem um scraper próprio em `catalog/scrapers/`, especializado no formato de resposta do site:

| Loja | Estratégia de extração |
|---|---|
| KaBuM | JSON embutido em `<script id="__NEXT_DATA__">` |
| Pichau | Payload RSC (React Server Components) via header `RSC: 1`, extração por bracket-matching |
| Terabyte | HTML renderizado (`div.product-item` + atributos `data-tss-*`) |

A classe base (`scrapers/base.py`) centraliza sessão HTTP, headers, retries com backoff e parsing de preços.

## Como rodar

Requisitos: Python 3.12+, Node.js 18+ (apenas para compilar o CSS).

```bash
# 1. Ambiente virtual + dependências
python -m venv .venv
.venv\Scripts\activate            # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt

# 2. Variáveis de ambiente — crie um arquivo .env na raiz:
#    DJANGO_SECRET_KEY=<sua chave>
#    DJANGO_DEBUG=0
# Gere uma chave segura com:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 3. Banco de dados
python manage.py migrate

# 4. Front-end (primeira vez ou ao alterar templates/CSS)
cd theme/static_src && npm install && cd ../..
python manage.py tailwind build

# 5. Popular o catálogo (~500 produtos, leva alguns minutos)
python manage.py import_catalog --all

# 6. Servidor
python manage.py runserver
```

### Comandos de gerenciamento

| Comando | Função |
|---|---|
| `import_catalog --all` | Importa o catálogo curado (13 categorias, ~25 buscas por loja) |
| `scrape --store kabum --query "rtx 4070"` | Coleta pontual por termo de busca |
| `check_alerts` | Verifica alertas de preço-alvo e dispara e-mails |
| `check_promotions` | Detecta novas promoções e notifica assinantes (cooldown 24h) |

Em produção, agende `check_alerts` e `check_promotions` no cron/Agendador de Tarefas.

## Estrutura

```
catalog/
├── models.py          # Store, Brand, Category, Product, Offer, PriceSnapshot, PriceAlert, PromoSubscription
├── scrapers/          # Um scraper por loja + base compartilhada
├── templatetags/      # Ícones SVG inline, filtro de moeda BRL, badges por loja
└── management/commands/
    ├── scrape.py              # Coleta ad-hoc
    ├── import_catalog.py      # População do catálogo curado
    ├── check_alerts.py        # Alertas de preço-alvo
    └── check_promotions.py    # Detecção de promoções + notificações
config/settings.py     # Configurações (segredos via variáveis de ambiente)
templates/             # Templates com UI dark responsiva
theme/                 # App django-tailwind (source do CSS)
```

## Roadmap

- [ ] Deploy com PostgreSQL + Redis
- [ ] Agendamento interno de coletas (celery beat ou management loop)
- [ ] API REST pública
- [ ] Comparação de parcelamento e preço à vista

## Aviso

Projeto independente, sem qualquer afiliação com as lojas monitoradas. Os preços são coletados automaticamente e podem estar desatualizados — sempre confirme o valor final no site da loja antes de comprar.

## Licença

[MIT](LICENSE)
