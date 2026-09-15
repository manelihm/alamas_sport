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
from app_shop.api import views

urlpatterns = [
    path("banners/", views.banner_list),
    path('banners/create/', views.banner_create),
    path('banners/apdate/' , views.banner_update),
    path("banners/delete/", views.banner_delete),
    path("banners/change_status" ,views.banner_change_status) ,
    path("banners/banner_display_order" ,views.banner_display_order)
]