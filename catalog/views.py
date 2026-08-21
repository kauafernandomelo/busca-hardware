from django.shortcuts import render

from .models import Category, Product


def home(request):
    root_categories = Category.objects.filter(parent__isnull=True)
    recent_products = (
        Product.objects.filter(is_active=True)
        .select_related("brand", "category")
        .prefetch_related("offers__store")[:12]
    )
    context = {
        "root_categories": root_categories,
        "recent_products": recent_products,
    }
    return render(request, "catalog/home.html", context)
