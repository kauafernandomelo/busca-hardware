from catalog.models import Category, Store


def marketplace(request):
    """Categorias e lojas ativas disponíveis em todas as páginas."""
    return {
        "nav_categories": (
            Category.objects.filter(parent__isnull=True).order_by("name")
        ),
        "active_stores": (
            Store.objects.filter(is_active=True, offers__is_available=True)
            .distinct()
            .order_by("name")
        ),
    }
