from django.contrib import admin

from .models import (
    Address,
    Favorite,
    ProductFeedback,
    ProductRequest,
)


class SuperAdminOnlyMixin:
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


@admin.register(Address)
class AddressAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    list_display = (
        "city",
        "province",
        "is_default",
        "created_at",
    )

    list_filter = (
        "province",
        "is_default",
    )

    search_fields = (
        "city",
        "province",
        "user__phone_number",
    )


@admin.register(Favorite)
class FavoriteAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    list_display = (
        "product",
        "created_at",
    )

    search_fields = (
        "product__name",
        "user__phone_number",
    )


@admin.register(ProductFeedback)
class ProductFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "rating",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "rating",
        "created_at",
    )

    search_fields = (
        "product__name",
        "content",
    )

    readonly_fields = (
        "product",
        "content",
        "rating",
        "created_at",
        "updated_at",
        "user",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ProductRequest)
class ProductRequestAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
    )

    readonly_fields = (
        "title",
        "description",
        "created_at",
        "updated_at",
        "user",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser