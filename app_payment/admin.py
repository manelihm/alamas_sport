from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "gateway",
        "amount",
        "status",
        "created_at",
        "paid_at",
    )
    list_filter = ("status", "gateway", "created_at")
    search_fields = (
        "id",
        "order__order_number",
        "authority",
        "transaction_id",
        "tracking_code",
    )
    readonly_fields = tuple(
        field.name for field in Payment._meta.fields
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False