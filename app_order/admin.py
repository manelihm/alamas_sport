from django.contrib import admin
from django.utils import timezone
from django.db import transaction
from django.contrib import messages

from .stock_services import cancel_order_stock
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
        "get_customer_name",
        "get_customer_phone",
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

    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 25
    list_select_related = (
        "user",
        "shipping_address",
        "shipping_method",
    )

    readonly_fields = (
        "order_number",
        "user",
        "cart",
        "status",
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
        ("Order Information", {
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
        ("Shipping Information", {
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
        ("Payment Summary", {
            "fields": (
                "total_amount",
                "discount_amount",
                "final_amount",
                "discount_code_snapshot",
                "discount_code_type_snapshot",
                "discount_code_value_snapshot",
            )
        }),
        ("Internal Note", {
            "fields": ("internal_note",)
        }),
    )

    @admin.display(description="Customer Name", ordering="user__first_name")
    def get_customer_name(self, obj):
        if not obj.user:
            return "—"

        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return full_name or obj.user.username

    @admin.display(description="Customer Phone", ordering="user__phone_number")
    def get_customer_phone(self, obj):
        return obj.user.phone_number if obj.user else "—"

    actions = (
        "mark_in_progress",
        "mark_shipped",
        "mark_delivered",
    )

    def _set_order_status(self, request, queryset, new_status, allowed_statuses):
        updated_count = 0

        for order in queryset:
            if order.status not in allowed_statuses:
                continue

            order.status = new_status
            order.save(update_fields=["status", "updated_at"])
            updated_count += 1

        self.message_user(request, f"{updated_count} order(s) updated.")

    @admin.action(description="Mark selected orders as in progress")
    def mark_in_progress(self, request, queryset):
        self._set_order_status(
            request,
            queryset,
            Order.Status.IN_PROGRESS,
            [Order.Status.CONFIRMED],
        )

    @admin.action(description="Mark selected orders as shipped")
    def mark_shipped(self, request, queryset):
        self._set_order_status(
            request,
            queryset,
            Order.Status.SHIPPED,
            [Order.Status.IN_PROGRESS],
        )

    @admin.action(description="Mark selected orders as delivered")
    def mark_delivered(self, request, queryset):
        self._set_order_status(
            request,
            queryset,
            Order.Status.DELIVERED,
            [Order.Status.SHIPPED],
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
        "status",
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
actions = (
        "approve_cancellation_requests",
        "reject_cancellation_requests",
    )

    @admin.action(description="Approve selected cancellation requests")
    def approve_cancellation_requests(self, request, queryset):
        approved_count = 0

        for item in queryset:
            with transaction.atomic():
                cancellation_request = (
                    CancellationRequest.objects
                    .select_for_update()
                    .get(pk=item.pk)
                )

                if cancellation_request.status != CancellationRequest.Status.PENDING:
                    continue

                order = Order.objects.select_for_update().get(
                    pk=cancellation_request.order_id
                )

                allowed_statuses = [
                    Order.Status.PENDING,
                    Order.Status.CONFIRMED,
                    Order.Status.IN_PROGRESS,
                ]

                if order.status not in allowed_statuses:
                    continue

                cancel_order_stock(order.id)

                order.status = Order.Status.CANCELLED
                order.save(update_fields=["status", "updated_at"])

                cancellation_request.approve(
                    admin_user=request.user,
                    note=cancellation_request.admin_note,
                )

                approved_count += 1

        self.message_user(
            request,
            f"{approved_count} cancellation request(s) approved.",
            messages.SUCCESS,
        )

    @admin.action(description="Reject selected cancellation requests")
    def reject_cancellation_requests(self, request, queryset):
        rejected_count = 0

        for item in queryset:
            with transaction.atomic():
                cancellation_request = (
                    CancellationRequest.objects
                    .select_for_update()
                    .get(pk=item.pk)
                )

                if cancellation_request.status != CancellationRequest.Status.PENDING:
                    continue

                cancellation_request.reject(
                    admin_user=request.user,
                    note=cancellation_request.admin_note,
                )

                rejected_count += 1

        self.message_user(
            request,
            f"{rejected_count} cancellation request(s) rejected.",
            messages.SUCCESS,
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
