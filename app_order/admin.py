from django.contrib import admin
from django.utils import timezone

from .models import (
    ShippingMethod,
    Order,
    OrderItem,
    StockReservation,
    DiscountCodeReservation,
    CancellationRequest,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = (
        "product",
        "product_option",
        "product_snapshot",
        "quantity",
        "price_type",
        "unit_price",
        "discount_amount",
        "total_price",
        "created_at",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status",
        "order_type",
        "final_amount",
        "created_at",
    )

    list_filter = (
        "status",
        "order_type",
        "created_at",
    )

    search_fields = (
        "order_number",
        "tracking_code",
        "user__phone_number",
        "user__first_name",
        "user__last_name",
    )

    readonly_fields = (
        "order_number",
        "user",
        "cart",
        "shipping_address",
        "shipping_method_name_snapshot",
        "estimated_delivery_time_snapshot",
        "shipping_address_snapshot",
        "total_amount",
        "discount_amount",
        "shipping_cost",
        "final_amount",
        "discount_code_snapshot",
        "discount_code_type_snapshot",
        "discount_code_value_snapshot",
        "created_at",
        "updated_at",
    )

    inlines = (OrderItemInline,)

    fieldsets = (
        ("Order", {
            "fields": (
                "order_number",
                "status",
                "order_type",
                "user",
                "cart",
                "created_at",
                "updated_at",
            )
        }),
        ("Shipping", {
            "fields": (
                "shipping_method",
                "shipping_method_name_snapshot",
                "estimated_delivery_time_snapshot",
                "shipping_address",
                "shipping_address_snapshot",
                "shipping_cost",
                "tracking_code",
            )
        }),
        ("Payment summary", {
            "fields": (
                "total_amount",
                "discount_amount",
                "final_amount",
                "discount_code_snapshot",
                "discount_code_type_snapshot",
                "discount_code_value_snapshot",
            )
        }),
        ("Internal note", {
            "fields": ("internal_note",)
        }),
    )


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "estimated_delivery_time",
        "is_active",
    )

    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(CancellationRequest)
class CancellationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "user",
        "status",
        "created_at",
        "reviewed_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "order__order_number",
        "user__phone_number",
    )

    readonly_fields = (
        "order",
        "user",
        "reason",
        "reviewed_by",
        "created_at",
        "reviewed_at",
    )

    fields = (
        "order",
        "user",
        "reason",
        "status",
        "admin_note",
        "reviewed_by",
        "created_at",
        "reviewed_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()

        super().save_model(request, obj, form, change)


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = (
        "order_item",
        "product_option",
        "quantity",
        "status",
        "expires_at",
    )

    list_filter = ("status",)

    readonly_fields = tuple(
        field.name for field in StockReservation._meta.fields
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DiscountCodeReservation)
class DiscountCodeReservationAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "discount_code",
        "status",
        "expires_at",
    )

    list_filter = ("status",)

    readonly_fields = tuple(
        field.name for field in DiscountCodeReservation._meta.fields
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
