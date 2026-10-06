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
from app_home.api import views

urlpatterns = [
    path("banners/", views.banner_list),
    path('banners/create/', views.banner_create),
    path('banners/apdate/' , views.banner_update),
    path("banners/delete/", views.banner_delete),
    path("banners/change_status" ,views.banner_change_status) ,
    path("banners/banner_display_order" ,views.banner_display_order) ,

    path('trending/', views.trending_product_list),
    path('trending/<int:pk>/', views.trending_product_detail),
    path('trending/create/', views.trending_product_create),
    path('trending/<int:pk>/update/', views.trending_product_update),
    path('trending/<int:pk>/delete/', views.trending_product_delete),
    path('trending/reorder/', views.trending_product_reorder),
    path('trending/<int:pk>/change-status/', views.trending_product_change_status),

    path('company/', views.company_information_detail),
    path('company/update/', views.company_information_update),
    path('company/contents/', views.company_content_list),
    path('company/contents/<int:pk>/', views.company_content_detail),
    path('company/contents/create/', views.company_content_create),
    path('company/contents/<int:pk>/update/', views.company_content_update),
    path('company/contents/<int:pk>/delete/', views.company_content_delete),
    path('company/contents/reorder/', views.company_content_reorder),

    
    path('home-content/', views.home_content_list),
    path('home-content/create/', views.home_content_create),
    path('home-content/<int:pk>/update/', views.home_content_update),
    path('home-content/<int:pk>/delete/', views.home_content_delete),
    path('home-content/reorder/', views.home_content_reorder),
    path('home-content/<int:pk>/change-status/', views.home_content_change_status),
]
