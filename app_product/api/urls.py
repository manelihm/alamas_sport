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

urlpatterns = [
    path('categories/', views.category_list),
    path('categories/<int:pk>/', views.category_detail),
    path('categories/create/', views.category_create),
    path('categories/<int:pk>/update/', views.category_update),
    path('categories/<int:pk>/delete/', views.category_delete),

    path('categories/<int:category_id>/subcategories/', views.subcategory_list),
    path('subcategories/<int:pk>/', views.subcategory_detail),
    path('subcategories/create/', views.subcategory_create),
    path('subcategories/<int:pk>/update/', views.subcategory_update),
    path('subcategories/<int:pk>/delete/', views.subcategory_delete),

    path('products/', views.product_list),
    path('products/<int:pk>/', views.product_detail),
    path('products/<int:pk>/related/', views.product_related),
    path('products/create/', views.product_create),
    path('products/images/create/', views.product_image_create),
    path('products/options/create/', views.product_option_create),
    path('products/materials/create/', views.product_material_create),
    path('products/<int:pk>/update/', views.product_update),
    path('products/images/<int:pk>/update/', views.product_image_update),
    path('products/options/<int:pk>/update/', views.product_option_update),
    path('products/materials/<int:pk>/update/', views.product_material_update),
    path('products/<int:pk>/delete/', views.product_delete),
    path('products/images/<int:pk>/delete/', views.product_image_delete),
    path('products/options/<int:pk>/delete/', views.product_option_delete),
    path('products/materials/<int:pk>/delete/', views.product_material_delete),
    path('products/<int:pk>/change-status/', views.product_change_status),
    path('products/options/<int:pk>/update-stock/', views.product_option_update_stock),
    path('products/options/<int:pk>/update-price/', views.product_option_update_price),

    path('discounts/products/', views.discount_product_list),
    path('discounts/create/', views.discount_create),
    path('discounts/<int:pk>/update/', views.discount_update),
    path('discounts/<int:pk>/delete/', views.discount_delete),
    path('discounts/<int:pk>/change-status/', views.discount_change_status),
]