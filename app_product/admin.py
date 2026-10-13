from django.contrib import admin
from app_product.models import (
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
# تصاویر هر گزینه محصول
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
# گزینه‌های هر محصول
class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 1
    show_change_link = True
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'category',
        'brand',
        'gender',
        'is_active',
    ]
    list_filter = ['category', 'gender', 'is_active']
    search_fields = ['name', 'brand']
    ordering = ['id']
    inlines = [ProductOptionInline]
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'parent',
        'is_active',
    ]
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['id']
@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'color_code']
    search_fields = ['name']
    ordering = ['id']
@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']
    ordering = ['id']
@admin.register(ProductMaterial)
class ProductMaterialAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']
    ordering = ['id']
@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'product',
        'color',
        'size',
        'material',
        'retail_price',
        'wholesale_price',
        'wholesale_min_quantity',
        'stock',
        'is_active',
    ]
    list_filter = [
        'color',
        'size',
        'material',
        'is_active',
    ]
    search_fields = ['product__name']
    ordering = ['id']
    inlines = [ProductImageInline]
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'product',
        'image_url',
        'is_primary',
    ]
    list_filter = ['is_primary']
    ordering = ['id']
@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'product',
        'type',
        'value',
        'start_at',
        'end_at',
    ]
    list_filter = ['type']
    search_fields = ['product__product__name']
    ordering = ['id']
@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'code',
        'type',
        'value',
        'is_used',
        'used_by',
        'start_at',
        'end_at',
    ]
    list_filter = ['type', 'is_used']
    search_fields = ['code']
    ordering = ['id']