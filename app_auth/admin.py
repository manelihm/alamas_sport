from django.contrib import admin
from django.contrib.auth.models import Group

from app_auth.models import User


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


@admin.register(User)
class UserAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    list_display = (
        "phone_number",
        "username",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "status",
    )

    search_fields = (
        "phone_number",
        "username",
        "first_name",
        "last_name",
    )

    ordering = ("-created_at",)

    exclude = (
        "password",
        "last_login",
    )

    readonly_fields = (
        "created_at",
        "last_login_at",
    )

    filter_horizontal = (
        "groups",
        "user_permissions",
    )

    fieldsets = (
        ("Account", {
            "fields": (
                "phone_number",
                "username",
                "first_name",
                "last_name",
                "image",
                "gender",
            )
        }),
        ("Role and status", {
            "fields": (
                "role",
                "status",
                "is_active",
                "is_phone_verified",
                "is_staff",
                "is_superuser",
            )
        }),
        ("Permissions", {
            "fields": (
                "groups",
                "user_permissions",
            )
        }),
        ("Dates", {
            "fields": (
                "created_at",
                "last_login_at",
            )
        }),
    )


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    filter_horizontal = ("permissions",)
