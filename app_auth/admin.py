from django.contrib import admin
from app_auth.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "phone_number", "role", "is_active")
    search_fields = ("username", "phone_number")
    list_filter = ("role", "is_active")
    ordering = ("username",)

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
