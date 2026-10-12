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
from app_users.api import views

urlpatterns = [


    path('addresses/', views.address_list),
    path('addresses/create/', views.address_create),
    path('addresses/<int:pk>/update/', views.address_update),
    path('addresses/<int:pk>/delete/', views.address_delete),
    path('addresses/<int:pk>/set-default/', views.address_set_default),

    path('favorites/', views.favorite_list),
    path('favorites/create/', views.favorite_create),
    path('favorites/<int:pk>/delete/', views.favorite_delete),

    path('feedbacks/mine/', views.feedback_my_list),
    path('feedbacks/create/', views.feedback_create),
    path('feedbacks/mine/<int:pk>/', views.feedback_my_detail),
    path('feedbacks/mine/<int:pk>/update/', views.feedback_my_update),
    path('feedbacks/mine/<int:pk>/delete/', views.feedback_my_delete),
    path('products/<int:product_id>/feedbacks/', views.feedback_product_list),

    path('feedbacks/', views.feedback_admin_list),
    path('feedbacks/<int:pk>/', views.feedback_admin_detail),
    path('feedbacks/<int:pk>/approve/', views.feedback_approve),
    path('feedbacks/<int:pk>/reject/', views.feedback_reject),
    path('feedbacks/<int:pk>/admin-delete/', views.feedback_admin_delete),
    
    path('product-requests/create/', views.product_request_create),
    path('product-requests/mine/', views.product_request_my_list),
    path('product-requests/mine/<int:pk>/', views.product_request_my_detail),
    path('product-requests/mine/<int:pk>/delete/', views.product_request_my_delete),

    path('product-requests/', views.product_request_admin_list),
    path('product-requests/<int:pk>/', views.product_request_admin_detail),
    path('product-requests/<int:pk>/change-status/', views.product_request_change_status),
    


  ]