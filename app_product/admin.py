from django import forms
from django.contrib import admin
import nested_admin

from .models import (
    Brand,
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


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"

    def clean_parent(self):
        parent = self.cleaned_data.get("parent")

        if not parent:
            return None

        current = parent
        visited = set()

        while current:
            if current.pk in visited:
                raise forms.ValidationError(
                    "Invalid category hierarchy detected."
                )

            visited.add(current.pk)

            if self.instance.pk and current.pk == self.instance.pk:
                raise forms.ValidationError(
                    "A category cannot be placed under its descendant."
                )

            current = current.parent

        return parent


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

    inlines = (
        ProductImageInline,
        DiscountInline,
    )




@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "product_brands",
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

    search_fields = (
        "name",
        "options__brand__name",
        "description",
    )

    ordering = ("-id",)
    list_per_page = 25
    list_select_related = ("category",)
    save_on_top = True

    fieldsets = (
        (
            "Product Information",
            {
                "fields": (
                    "name",
                    "description",
                    "category",
                    "gender",
                )
            },
        ),
        (
            "Product Status",
            {
                "fields": ("is_active",)
            },
        ),
        (
            "Trending Settings",
            {
                "fields": (
                    "is_trending",
                    "trending_is_active",
                    "trending_sort_order",
                )
            },
        ),
    )

    inlines = (ProductOptionInline,)

    @admin.display(description="Brands")
    def product_brands(self, obj):
        brands = (
            obj.options
            .filter(brand__isnull=False)
            .values_list("brand__name", flat=True)
            .distinct()
        )
        return ", ".join(brands) or "—"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm

    list_display = (
        "id",
        "name",
        "parent",
        "is_active",
    )

    list_filter = ("is_active",)

    search_fields = (
        "name",
        "description",
        "parent__name",
    )

    ordering = ("parent__name", "name")
    list_select_related = ("parent",)
    list_per_page = 25

    actions = (
        activate_categories,
        deactivate_categories,
    )


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


@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "color",
        "size",
        "material",
        "retail_price",
        "wholesale_price",
        "wholesale_min_quantity",
        "stock",
        "reserved_stock",
        "is_active",
    )

    list_filter = (
        "color",
        "size",
        "material",
        "is_active",
    )

    search_fields = (
        "product__name",
        "color__name",
        "size__name",
        "material__name",
    )

    readonly_fields = ("reserved_stock",)
    list_select_related = (
        "product",
        "color",
        "size",
        "material",
    )
    ordering = ("-id",)
    list_per_page = 25


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_product_name",
        "product",
        "image_url",
        "is_primary",
    )

    list_filter = ("is_primary",)

    search_fields = (
        "product__product__name",
        "product__color__name",
        "product__size__name",
    )

    list_select_related = (
        "product",
        "product__product",
        "product__color",
        "product__size",
    )

    ordering = ("-id",)
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

    list_filter = (
        "type",
        "start_at",
        "end_at",
    )

    search_fields = (
        "product__product__name",
        "product__color__name",
        "product__size__name",
    )

    list_select_related = (
        "product",
        "product__product",
    )

    ordering = ("-start_at",)
    list_per_page = 25

    @admin.display(description="Product")
    def get_product_name(self, obj):
        return obj.product.product.name


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "assigned_to",
        "type",
        "value",
        "is_used",
        "used_by",
        "start_at",
        "end_at",
    )

    list_filter = (
        "type",
        "is_used",
        "start_at",
        "end_at",
    )

    search_fields = (
        "code",
        "assigned_to__username",
        "used_by__username",
    )

    readonly_fields = (
        "is_used",
        "used_by",
        "used_at",
    )

    ordering = ("-id",)
    list_per_page = 25


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['name']