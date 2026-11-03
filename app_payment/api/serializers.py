from rest_framework import serializers
from app_payment.models import Payment
class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(
        source="order.order_number",
        read_only=True,
    )
    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "order_number",
            "gateway",
            "amount",
            "status",
            "authority",
            "transaction_id",
            "tracking_code",
            "created_at",
            "updated_at",
            "paid_at",
        ]
        read_only_fields = [
            "id",
            "order_number",
            "status",
            "authority",
            "transaction_id",
            "tracking_code",
            "created_at",
            "updated_at",
            "paid_at",
        ]