# Busca Hardware

Comparador de preços de hardware que monitora **KaBuM!**, **Pichau** e **Terabyte**, detecta promoções automaticamente e avisa por e-mail quando o produto que você quer fica barato. *(Coleta do Pichau pausada — WAF bloqueia IPs de cloud; ver [Deploy](#deploy) › Sobre o Pichau.)*

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.x-06B6D4?logo=tailwindcss&logoColor=white)
![Coleta de preços](https://github.com/kauafernandomelo/busca-hardware/actions/workflows/scrape.yml/badge.svg)

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
| Banco | SQLite no dev, PostgreSQL em produção (dj-database-url) |
| Deploy | Render (Gunicorn + Whitenoise), infra como código em `render.yaml` |
| Coleta agendada | GitHub Actions, a cada 6 horas, gravando direto no banco de produção |

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
#    DJANGO_DEBUG=1
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

Em produção esses comandos rodam automaticamente no workflow do GitHub Actions (ver abaixo).

## Deploy

O site roda no **Render** e a coleta de preços no **GitHub Actions** — nenhuma execução acontece na máquina local.

### 1. Site no Render (blueprint)

O arquivo `render.yaml` já descreve web service + PostgreSQL. No dashboard:

1. **New** → **Blueprint** → selecione este repositório → **Apply**
2. O Render cria o banco, injeta `DATABASE_URL`, gera a `DJANGO_SECRET_KEY` e roda `build.sh` (dependências, Tailwind, `collectstatic`, `migrate`)
3. O host público (`*.onrender.com`) é detectado automaticamente via `RENDER_EXTERNAL_HOSTNAME`

### 2. Coleta agendada no GitHub Actions

O workflow `.github/workflows/scrape.yml` roda a cada 6 horas (cron UTC) e executa: `migrate` → `import_catalog --all` → `check_alerts` → `check_promotions`, gravando direto no PostgreSQL do Render.

Configuração única necessária:

1. No Render, abra o banco criado pelo blueprint e copie a **External Database URL**
2. No GitHub: *Settings* → *Secrets and variables* → *Actions* → **New repository secret**
   - Name: `DATABASE_URL`
   - Secret: a URL copiada (contém usuário/senha — nunca coloque em arquivos)
3. Aba **Actions** → workflow "Coleta de precos" → **Run workflow** para a primeira coleta manual

Opcional: crie a variável de repositório `SITE_URL` com a URL pública do site para os links dos e-mails de alerta.

### 3. E-mails (SMTP)

Sem configuração, os e-mails são apenas impressos no log (backend console) — nada quebra. Para envio real, use qualquer provedor SMTP (Brevo, Mailgun, Gmail com senha de app etc.):

1. No GitHub: *Settings* → *Secrets and variables* → *Actions*:
   - **Secret** `EMAIL_HOST_PASSWORD`: a senha/SMTP key do provedor
   - **Variables**: `EMAIL_HOST` (ex.: `smtp-relay.brevo.com`), `EMAIL_HOST_USER`, e se quiser `EMAIL_PORT` (padrão 587), `EMAIL_USE_TLS` (padrão 1), `DEFAULT_FROM_EMAIL`
2. Rode o workflow manualmente e confira nos logs os `[ALERTA]`/`[PROMO]` enviados

No dev, as mesmas variáveis podem ir no `.env`; sem `EMAIL_HOST`, o Django imprime os e-mails no terminal.

### Sobre o Pichau

O WAF do Pichau bloqueia IPs de datacenter (GitHub Actions) mesmo com TLS de navegador — só passa por IP residencial. Por isso o workflow usa a variável de repositório `SCRAPER_STORES` (padrão: `kabum,terabyte`). Para religar o Pichau: contrate um proxy residencial barato (ou registre um runner self-hosted na sua máquina), aponte o scraper para ele e mude a variável para `kabum,pichau,terabyte`.

### Variáveis de ambiente

| Variável | Onde | Função |
|---|---|---|
| `DJANGO_SECRET_KEY` | .env / Render | Chave secreta do Django |
| `DJANGO_DEBUG` | .env / Render | `1` só no dev; default fechado em `0` |
| `DATABASE_URL` | secret do Actions / Render | String PostgreSQL (fallback: SQLite) |
| `SITE_URL` | vars do Actions / opcional | URL base usada nos links dos alertas |
| `EMAIL_HOST` | vars do Actions / .env | Sem esta var, e-mails vão para o console/log |
| `EMAIL_PORT` | vars do Actions / .env | Porta SMTP (padrão 587) |
| `EMAIL_HOST_USER` | vars do Actions / .env | Usuário SMTP |
| `EMAIL_HOST_PASSWORD` | secret do Actions / .env | Senha SMTP (nunca versionar) |
| `EMAIL_USE_TLS` / `EMAIL_USE_SSL` | vars do Actions / .env | Padrão: TLS ligado, SSL desligado |
| `DEFAULT_FROM_EMAIL` | vars do Actions / .env | Remetente dos alertas e promoções |
| `NPM_BIN_PATH` | .env (Windows) | Caminho do npm quando fora do PATH |

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
build.sh               # Build de produção (Render): deps, Tailwind, estáticos, migrate
render.yaml            # Infra como código: web service + PostgreSQL
```

## Roadmap

- [x] Deploy com PostgreSQL (Render, Gunicorn + Whitenoise)
- [x] Coleta agendada sem servidor próprio (GitHub Actions a cada 6h)
- [x] Envio real de e-mails (SMTP) para alertas e promoções
- [ ] API REST pública
- [ ] Comparação de parcelamento e preço à vista

## Aviso

Projeto independente, sem qualquer afiliação com as lojas monitoradas. Os preços são coletados automaticamente e podem estar desatualizados — sempre confirme o valor final no site da loja antes de comprar.

## Licença

[MIT](LICENSE)
