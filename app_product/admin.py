from django.contrib import admin
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
    actions = (activate_categories, deactivate_categories)


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "color_code")
    search_fields = ("name", "color_code")


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(ProductMaterial)
class ProductMaterialAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name", "description")


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "image_url", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("product__product__name",)


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "type",
        "value",
        "start_at",
        "end_at",
    )
    list_filter = ("type", "start_at", "end_at")
    search_fields = ("product__product__name",)
    ordering = ("-start_at",)


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
    exclude = ("assigned_to",)