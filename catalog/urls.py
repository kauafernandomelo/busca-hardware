from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home, name='home'),
    path('busca/', views.search, name='search'),
    path('categoria/<slug:slug>/', views.category_detail, name='category'),
    path('produto/<slug:slug>/', views.product_detail, name='product'),
    path('promocoes/', views.promotions, name='promotions'),
    path('inscrever/', views.subscribe_promo, name='subscribe'),
]
