from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils import timezone
import nested_admin

from .models import (
    Category,
    Product,
    ProductColor,
    ProductSize,
    ProductMaterial,
    ProductOption,
    ProductImage,
    Discount,
    DiscountCode,
)


@admin.action(description="Activate selected categories")
def activate_categories(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Deactivate selected categories")
def deactivate_categories(modeladmin, request, queryset):
    queryset.update(is_active=False)


class ProductImageInline(nested_admin.NestedTabularInline):
    model = ProductImage
    extra = 1
    fields = ("image_url", "is_primary")


class DiscountInline(nested_admin.NestedTabularInline):
    model = Discount
    extra = 0
    fields = ("type", "value", "start_at", "end_at")


class ProductOptionInline(nested_admin.NestedStackedInline):
    model = ProductOption
    extra = 1
    readonly_fields = ("reserved_stock",)
    fields = (
        ("color", "size", "material"),
        ("retail_price", "wholesale_price"),
        "wholesale_min_quantity",
        ("stock", "reserved_stock", "is_active"),
    )
    inlines = (ProductImageInline, DiscountInline)


@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "brand",
        "gender",
        "is_active",
        "is_trending",
        "trending_is_active",
    )
    list_filter = (
        "category",
        "gender",
        "is_active",
        "is_trending",
        "trending_is_active",
    )
    search_fields = ("name", "brand", "description")
    ordering = ("id",)
    list_per_page = 25
    list_select_related = ("category",)

    fieldsets = (
        ("Product Information", {
            "fields": (
                "name",
                "description",
                "category",
                "brand",
                "gender",
            )
        }),
        ("Product Status", {
            "fields": ("is_active",)
        }),
        ("Trending Settings", {
            "fields": (
                "is_trending",
                "trending_is_active",
                "trending_sort_order",
            )
        }),
    )

    inlines = (ProductOptionInline,)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description", "parent__name")
    ordering = ("parent__name", "name")
    list_select_related = ("parent",)
    list_per_page = 25
    actions = (activate_categories, deactivate_categories)

    def save_model(self, request, obj, form, change):
        if obj.parent_id == obj.pk and obj.pk:
            raise ValidationError("A category cannot be its own parent.")
        super().save_model(request, obj, form, change)
    def clean_parent(self):
        parent = self.cleaned_data.get("parent")

        if not parent:
            return None

        current = parent
        visited = set()

        while current:
            if self.instance.pk and current.pk == self.instance.pk:
                raise forms.ValidationError(
                    "A category cannot be its own parent or a parent of its ancestor."
                )

            if current.pk in visited:
                raise forms.ValidationError(
                    "Invalid category hierarchy detected."
                )

            visited.add(current.pk)
            current = current.parent

        return parent

@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "color_code")
    search_fields = ("name", "color_code")
    ordering = ("name",)


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(ProductMaterial)
class ProductMaterialAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name", "description")
    ordering = ("name",)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "get_product_name", "image_url", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("product__product__name", "product__color__name")
    list_select_related = ("product", "product__product")
    list_per_page = 25

    @admin.display(description="Product")
    def get_product_name(self, obj):
        return obj.product.product.name


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_product_name",
        "product",
        "type",
        "value",
        "start_at",
        "end_at",
    )
    list_filter = ("type", "start_at", "end_at")
    search_fields = ("product__product__name",)
    ordering = ("-start_at",)
    list_select_related = ("product", "product__product")
    list_per_page = 25

    @admin.display(description="Product")
    def get_product_name(self, obj):
        return obj.product.product.name


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "type",
        "value",
        "is_used",
        "start_at",
        "end_at",
    )
    list_filter = ("type", "is_used")
    search_fields = ("code",)
    readonly_fields = ("is_used", "used_by", "used_at")
    list_per_page = 25
