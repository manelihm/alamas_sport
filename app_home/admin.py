from django import forms
from django.contrib import admin

from app_home.models import (
    Banner,
    CompanyInformation,
    CompanyInformationContent,
    HomeContent,
)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "sort_order",
        "is_active",
    )

    list_filter = ("is_active",)
    search_fields = ("title", "description")
    ordering = ("id",)

    fieldsets = (
        ("Banner Information", {
            "fields": (
                "title",
                "description",
                "image",
            )
        }),
        ("Button Settings", {
            "fields": (
                "button_text",
                "button_link",
            )
        }),
        ("Display Settings", {
            "fields": (
                "sort_order",
                "is_active",
            )
        }),
    )


class CompanyInformationContentInline(admin.TabularInline):
    model = CompanyInformationContent
    extra = 1
    fields = ("title", "value", "sort_order")
    ordering = ("sort_order",)


@admin.register(CompanyInformation)
class CompanyInformationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "is_active",
    )

    list_filter = ("is_active",)
    search_fields = ("title", "description")

    fieldsets = (
        ("Company Information", {
            "fields": (
                "title",
                "description",
                "logo_url",
                "is_active",
            )
        }),
    )

    inlines = (CompanyInformationContentInline,)


class HomeContentAdminForm(forms.ModelForm):

    class Meta:
        model = HomeContent
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        content_type = cleaned_data.get("type")

        selected_field = {
            "banner": "banner",
            "discount": "discount",
            "category": "category",
        }.get(content_type)

        if selected_field and not cleaned_data.get(selected_field):
            self.add_error(
                selected_field,
                "Select an item for the chosen content type."
            )

        for field_name in ("banner", "discount", "category"):
            if field_name != selected_field:
                cleaned_data[field_name] = None

        return cleaned_data


@admin.register(HomeContent)
class HomeContentAdmin(admin.ModelAdmin):
    form = HomeContentAdminForm

    list_display = (
        "id",
        "type",
        "title",
        "sort_order",
        "is_active",
    )

    list_filter = ("type", "is_active")
    search_fields = ("title",)
    ordering = ("sort_order",)

    fieldsets = (
        ("Section Information", {
            "fields": (
                "type",
                "title",
            )
        }),
        ("Related Content", {
            "fields": (
                "banner",
                "discount",
                "category",
            )
        }),
        ("Display Settings", {
            "fields": (
                "sort_order",
                "is_active",
            )
        }),
    )