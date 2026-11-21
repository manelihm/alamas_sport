from django.contrib import admin
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


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 1
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "brand", "gender", "is_active")
    list_filter = ("category", "gender", "is_active")
    search_fields = ("name", "brand")
    inlines = (ProductOptionInline,)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "color_code")
    search_fields = ("name",)


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(ProductMaterial)
class ProductMaterialAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "product", "color", "size", "material",
        "retail_price", "wholesale_price", "stock", "is_active",
    )
    list_filter = ("color", "size", "material", "is_active")
    search_fields = ("product__name",)
    inlines = (ProductImageInline,)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "image_url", "is_primary")
    list_filter = ("is_primary",)


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "type", "value", "start_at", "end_at")
    list_filter = ("type",)
    search_fields = ("product__product__name",)


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "type", "value", "is_used", "start_at", "end_at")
    list_filter = ("type", "is_used")
    search_fields = ("code",)
    exclude = ("assigned_to", "used_by", "used_at")