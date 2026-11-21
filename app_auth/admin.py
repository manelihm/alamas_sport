from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
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


class UserCreationAdminForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = (
            "phone_number",
            "username",
            "first_name",
            "last_name",
            "image",
            "gender",
            "role",
            "status",
            "is_active",
            "is_phone_verified",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
            self.save_m2m()

        return user


class UserChangeAdminForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = "__all__"
        exclude = ("last_login",)

    def clean_password(self):
        return self.initial["password"]


@admin.register(User)
class UserAdmin(SuperAdminOnlyMixin, BaseUserAdmin):
    form = UserChangeAdminForm
    add_form = UserCreationAdminForm

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

    filter_horizontal = (
        "groups",
        "user_permissions",
    )

    readonly_fields = (
        "created_at",
        "last_login_at",
    )

    fieldsets = (
        ("Account", {
            "fields": (
                "phone_number",
                "username",
                "password",
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

    add_fieldsets = (
        ("Account", {
            "classes": ("wide",),
            "fields": (
                "phone_number",
                "username",
                "password1",
                "password2",
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
    )


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    filter_horizontal = ("permissions",)

