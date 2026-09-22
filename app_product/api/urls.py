"""
URL configuration for alamas_sport project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from app_product.api import views

from django.urls import path
from app_product.api import views

urlpatterns = [
    # Category
    path('categories/', views.category_list),
    path('categories/<int:pk>/', views.category_detail),
    path('categories/create/', views.category_create),
    path('categories/<int:pk>/update/', views.category_update),
    path('categories/<int:pk>/delete/', views.category_delete),

    # Product
    path('products/', views.product_list),
    path('products/<int:pk>/', views.product_detail),
    path('products/<int:pk>/related/', views.product_related),
    path('products/create/', views.product_create),
    path('products/<int:pk>/update/', views.product_update),
    path('products/<int:pk>/delete/', views.product_delete),
    path('products/<int:pk>/change-status/', views.product_change_status),

    # Product Image
    path('products/images/create/', views.product_image_create),
    path('products/images/<int:pk>/update/', views.product_image_update),
    path('products/images/<int:pk>/delete/', views.product_image_delete),

    # Color
    path('colors/create/', views.product_color_create),
    path('colors/<int:pk>/update/', views.product_color_update),
    path('colors/<int:pk>/delete/', views.product_color_delete),

    # Size
    path('sizes/create/', views.product_size_create),
    path('sizes/<int:pk>/update/', views.product_size_update),
    path('sizes/<int:pk>/delete/', views.product_size_delete),

    # Material
    path('materials/create/', views.product_material_create),
    path('materials/<int:pk>/update/', views.product_material_update),
    path('materials/<int:pk>/delete/', views.product_material_delete),

    # Product Option
    path('products/options/create/', views.product_option_create),
    path('products/options/<int:pk>/update/', views.product_option_update),
    path('products/options/<int:pk>/delete/', views.product_option_delete),
    path('products/options/<int:pk>/update-stock/', views.product_option_update_stock),
    path('products/options/<int:pk>/update-price/', views.product_option_update_price),

    # Discount
    path('discounts/products/', views.discount_product_list),
    path('discounts/create/', views.discount_create),
    path('discounts/<int:pk>/update/', views.discount_update),
    path('discounts/<int:pk>/delete/', views.discount_delete),
    path('discount-codes/', views.discount_code_list),
    path('discount-codes/create/', views.discount_code_create),
    path('discount-codes/<int:pk>/update/', views.discount_code_update),
    path('discount-codes/<int:pk>/delete/', views.discount_code_delete),
    path('discount-codes/apply/', views.discount_code_apply),
]