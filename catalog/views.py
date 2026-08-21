from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Min, Q
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import Truncator

from .forms import PriceAlertForm
from .models import Category, PriceSnapshot, Product

SPARK_WIDTH = 640
SPARK_HEIGHT = 150
SPARK_PAD = 14


def home(request):
    root_categories = Category.objects.filter(parent__isnull=True)
    recent_products = recent_products_queryset()[:12]
    context = {
        "root_categories": root_categories,
        "recent_products": recent_products,
    }
    return render(request, "catalog/home.html", context)


def search(request):
    query = request.GET.get("q", "").strip()
    products = recent_products_queryset()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(brand__name__icontains=query)
        ).order_by("name")

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "query": query,
        "page_obj": page_obj,
        "total": paginator.count,
        "params_without_page": params_without_page(request),
    }
    return render(request, "catalog/search.html", context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = recent_products_queryset().filter(category=category).order_by("name")

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    subcategories = category.children.all()

    context = {
        "category": category,
        "subcategories": subcategories,
        "page_obj": page_obj,
        "total": paginator.count,
        "params_without_page": params_without_page(request),
    }
    return render(request, "catalog/category.html", context)


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
    spark_points = build_sparkline(history)

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
        "best_offer": best_offer,
        "alert_form": alert_form,
        "history": history,
        "spark_points": spark_points,
        "history_min": min((h["price"] for h in history), default=None),
        "breadcrumb_name": Truncator(product.name).chars(48),
    }
    return render(request, "catalog/product_detail.html", context)


def recent_products_queryset():
    return (
        Product.objects.filter(is_active=True)
        .select_related("brand", "category")
        .prefetch_related("offers__store")
    )


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
    if not history:
        return ""
    prices = [float(h["price"]) for h in history]
    low, high = min(prices), max(prices)
    if high == low:
        high = low + 1
    if len(prices) == 1:
        x = width / 2
        y = height - pad - (height - 2 * pad) * ((prices[0] - low) / (high - low))
        return f"{x:.1f},{y:.1f} {x:.1f},{y:.1f}"
    span_x = width - 2 * pad
    span_y = height - 2 * pad
    points = []
    for i, price in enumerate(prices):
        x = pad + span_x * i / (len(prices) - 1)
        y = height - pad - span_y * ((price - low) / (high - low))
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)
