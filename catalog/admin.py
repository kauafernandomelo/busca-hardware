from django.contrib import admin

from .models import (
    Brand,
    Category,
    Offer,
    PriceAlert,
    PriceSnapshot,
    Product,
    Store,
)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "website_url", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "products_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="produtos")
    def products_count(self, obj):
        return obj.products.count()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    list_filter = ("parent",)
    search_fields = ("name",)


class OfferInline(admin.TabularInline):
    model = Offer
    extra = 0
    fields = ("store", "url", "current_price", "is_available")


class PriceSnapshotInline(admin.TabularInline):
    model = PriceSnapshot
    extra = 0
    fields = ("price", "captured_at")
    readonly_fields = ("captured_at",)
    ordering = ("-captured_at",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category", "best_price", "offers_count", "is_active")
    list_filter = ("is_active", "category", "brand")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [OfferInline]

    @admin.display(description="melhor preço", ordering="offers__current_price")
    def best_price(self, obj):
        offer = obj.best_offer
        if offer:
            return f"R$ {offer.current_price} ({offer.store.name})"
        return "-"


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("product", "store", "current_price", "is_available", "last_checked_at")
    list_filter = ("store", "is_available")
    search_fields = ("product__name",)
    inlines = [PriceSnapshotInline]


@admin.register(PriceSnapshot)
class PriceSnapshotAdmin(admin.ModelAdmin):
    list_display = ("offer", "price", "captured_at")
    list_filter = ("offer__store",)
    date_hierarchy = "captured_at"


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ("email", "product", "target_price", "is_active", "notified_at", "created_at")
    list_filter = ("is_active",)
    search_fields = ("email", "product__name")
