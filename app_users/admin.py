from django.contrib import admin
from .models import Address, Favorite, ProductFeedback, ProductRequest


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("city", "province", "is_default", "created_at")

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("product", "created_at")

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(ProductFeedback)
class ProductFeedbackAdmin(admin.ModelAdmin):
    list_display = ("product", "rating", "status", "created_at")
    list_filter = ("status", "rating")
    readonly_fields = ("product", "content", "rating", "created_at", "updated_at")
    exclude = ("user",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ProductRequest)
class ProductRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("title", "description", "created_at", "updated_at")
    exclude = ("user",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser