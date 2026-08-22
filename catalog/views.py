from decimal import Decimal
from json import dumps as json_dumps

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Max, Min, Q
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import Truncator

from .forms import PriceAlertForm, PromoSubscriptionForm
from .models import Category, Offer, PriceSnapshot, Product

SPARK_WIDTH = 640
SPARK_HEIGHT = 150
SPARK_PAD = 14


def home(request):
    context = {
        "root_categories": Category.objects.filter(parent__isnull=True),
        "recent_products": base_product_queryset()[:12],
        "top_promos": promo_offers_queryset()[:8],
        "stats": {
            "products": Product.objects.filter(is_active=True).count(),
            "offers": Offer.objects.filter(is_available=True).count(),
            "stores": Offer.objects.values("store").distinct().count(),
            "promos": Offer.objects.filter(is_promo=True, is_available=True).count(),
        },
    }
    return render(request, "catalog/home.html", context)


def search(request):
    query = request.GET.get("q", "").strip()
    store_slug = request.GET.get("loja", "").strip()
    products = base_product_queryset()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(brand__name__icontains=query)
        )
    if store_slug:
        products = products.filter(
            offers__store__slug=store_slug,
            offers__is_available=True,
            offers__current_price__isnull=False,
        ).distinct()
    products = apply_sorting(products, request.GET.get("ord"))

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "query": query,
        "store_slug": store_slug,
        "page_obj": page_obj,
        "total": paginator.count,
        "sort": request.GET.get("ord", ""),
        "params_without_page": params_without_page(request),
    }
    return render(request, "catalog/search.html", context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    store_slug = request.GET.get("loja", "").strip()
    products = base_product_queryset().filter(category=category)
    if store_slug:
        products = products.filter(
            offers__store__slug=store_slug,
            offers__is_available=True,
            offers__current_price__isnull=False,
        ).distinct()
    products = apply_sorting(products, request.GET.get("ord"))

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "category": category,
        "subcategories": category.children.all(),
        "store_slug": store_slug,
        "page_obj": page_obj,
        "total": paginator.count,
        "sort": request.GET.get("ord", ""),
        "params_without_page": params_without_page(request),
    }
    return render(request, "catalog/category.html", context)


def promotions(request):
    offers = promo_offers_queryset()
    paginator = Paginator(offers, 16)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {
        "page_obj": page_obj,
        "total": paginator.count,
        "promo_form": PromoSubscriptionForm(),
        "params_without_page": "",
    }
    return render(request, "catalog/promotions.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("brand", "category").prefetch_related(
            "offers__store"
        ),
        slug=slug,
        is_active=True,
    )
    offers = list(
        product.offers.filter(is_available=True, current_price__isnull=False)
        .select_related("store")
        .order_by("current_price")
    )
    best_offer = offers[0] if offers else None

    history = build_price_history(product)
    spark = build_sparkline(history)
    history_min = min((h["price"] for h in history), default=None)
    is_record = bool(
        best_offer and history_min is not None and best_offer.current_price <= history_min
    )

    if request.method == "POST":
        alert_form = PriceAlertForm(request.POST)
        if alert_form.is_valid():
            alert = alert_form.save(commit=False)
            alert.product = product
            alert.save()
            messages.success(
                request,
                "Alerta criado! Você receberá um e-mail quando o preço atingir o alvo.",
            )
            return redirect(product)
    else:
        initial = {}
        if best_offer:
            initial["target_price"] = best_offer.current_price
        alert_form = PriceAlertForm(initial=initial)

    context = {
        "product": product,
        "offers": offers,
        "offer_bars": build_offer_bars(offers),
        "best_offer": best_offer,
        "alert_form": alert_form,
        "promo_form": PromoSubscriptionForm(initial={"product": product.pk}),
        "history": history,
        "spark": spark,
        "history_min": history_min,
        "is_record": is_record,
        "breadcrumb_name": Truncator(product.name).chars(48),
        "schema_json": build_schema_json(product, best_offer),
    }
    return render(request, "catalog/product_detail.html", context)


def subscribe_promo(request):
    if request.method != "POST":
        return redirect("catalog:home")

    form = PromoSubscriptionForm(request.POST)
    next_url = request.POST.get("next") or ""
    if form.is_valid():
        subscription = form.save()
        messages.success(
            request,
            f"Pronto! Avisaremos {subscription.email} quando surgirem promoções.",
        )
    else:
        first_error = next(
            (e for errors in form.errors.values() for e in errors),
            "Não foi possível criar a assinatura.",
        )
        messages.error(request, first_error)

    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect("catalog:promotions")


def base_product_queryset():
    return (
        Product.objects.filter(is_active=True)
        .select_related("brand", "category")
        .prefetch_related("offers__store")
        .annotate(
            n_offers=Count(
                "offers",
                filter=Q(offers__is_available=True),
                distinct=True,
            ),
            best_price=Min(
                "offers__current_price",
                filter=Q(
                    offers__is_available=True, offers__current_price__isnull=False
                ),
            ),
            max_discount=Max(
                "offers__discount_pct",
                filter=Q(offers__is_promo=True, offers__is_available=True),
            ),
        )
    )


def promo_offers_queryset():
    return (
        Offer.objects.filter(is_promo=True, is_available=True, current_price__isnull=False)
        .exclude(discount_pct__isnull=True)
        .select_related("product", "store", "product__category")
        .order_by("-discount_pct", "current_price")
    )


def apply_sorting(queryset, sort):
    if sort == "preco_asc":
        return queryset.order_by("best_price", "name")
    if sort == "preco_desc":
        return queryset.order_by("-best_price", "name")
    if sort == "desconto":
        return queryset.order_by("-max_discount", "name")
    return queryset.order_by("name")


def build_offer_bars(offers):
    if not offers:
        return []
    max_price = max(float(o.current_price) for o in offers)
    bars = []
    for offer in offers:
        ratio = float(offer.current_price) / max_price if max_price else 1
        bars.append(
            {
                "offer": offer,
                "width": max(int(ratio * 100), 18),
                "is_best": offer is offers[0],
            }
        )
    return bars


def params_without_page(request):
    params = request.GET.copy()
    params.pop("page", None)
    return params.urlencode()


def build_price_history(product):
    return list(
        PriceSnapshot.objects.filter(offer__product=product)
        .annotate(day=TruncDate("captured_at"))
        .values("day")
        .annotate(price=Min("price"))
        .order_by("day")
    )


def build_sparkline(history, width=SPARK_WIDTH, height=SPARK_HEIGHT, pad=SPARK_PAD):
    """Pontos da linha e da área preenchida do gráfico de histórico."""
    if not history:
        return {"line": "", "area": ""}
    prices = [float(h["price"]) for h in history]
    low, high = min(prices), max(prices)
    if high == low:
        high = low + 1
    bottom = height - pad
    if len(prices) == 1:
        x = width / 2
        y = height - pad - (height - 2 * pad) * ((prices[0] - low) / (high - low))
        point = f"{x:.1f},{y:.1f}"
        return {"line": f"{point} {point}", "area": ""}
    span_x = width - 2 * pad
    span_y = height - 2 * pad
    points = []
    for i, price in enumerate(prices):
        x = pad + span_x * i / (len(prices) - 1)
        y = height - pad - span_y * ((price - low) / (high - low))
        points.append(f"{x:.1f},{y:.1f}")
    line = " ".join(points)
    area = f"{points[0].split(',')[0]},{bottom} {line} {points[-1].split(',')[0]},{bottom}"
    return {"line": line, "area": area}


def build_schema_json(product, best_offer):
    """JSON-LD (schema.org) com dados estruturados do produto/oferta."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "category": product.category.name,
        "brand": {"@type": "Brand", "name": product.brand.name} if product.brand else None,
        "image": [product.image_url] if product.image_url else None,
    }
    if best_offer:
        schema["offers"] = {
            "@type": "Offer",
            "url": best_offer.url,
            "priceCurrency": "BRL",
            "price": str(Decimal(best_offer.current_price).quantize(Decimal("0.01"))),
            "availability": (
                "https://schema.org/InStock"
                if best_offer.is_available
                else "https://schema.org/OutOfStock"
            ),
            "seller": {"@type": "Organization", "name": best_offer.store.name},
        }
    return json_dumps({k: v for k, v in schema.items() if v is not None}, ensure_ascii=False)
