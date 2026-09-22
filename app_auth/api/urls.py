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
from app_auth.api import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('send-code/', views.send_verification_code),
    path('verify-code/', views.verify_registration_code),
    path('register/', views.register),
    path('login/', views.login),
    path('refresh-token/', TokenRefreshView.as_view()),
    path('logout/', views.logout),
    path('send-login-code/', views.send_login_code),
    path('login-with-code/', views.login_with_code),
    path('request-password-reset/', views.request_password_reset),
    path('reset-password/', views.reset_password),
    path('users/', views.user_list),
    path('users/create/', views.user_create),
    path('users/<int:pk>/', views.user_detail),
    path('users/<int:pk>/update/', views.user_update),
    path('users/<int:pk>/delete/', views.user_delete),
    path('users/<int:pk>/change-status/', views.user_change_status),
    path('users/<int:pk>/change-role/', views.user_change_role),
]