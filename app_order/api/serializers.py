from rest_framework import serializers

from app_order.models import Order, OrderItem, ShippingMethod ,CancellationRequest


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = [
            "id",
            "name",
            "description",
            "price",
            "estimated_delivery_time",
        ]
        read_only_fields = fields


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_option",
            "product_snapshot",
            "quantity",
            "price_type",
            "unit_price",
            "discount_amount",
            "total_price",
            "created_at",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "order_type",
            "status",
            "shipping_method_name_snapshot",
            "shipping_method",
            "estimated_delivery_time_snapshot",
            "shipping_address_snapshot",
            "total_amount",
            "discount_amount",
            "shipping_cost",
            "final_amount",
            "discount_code_snapshot",
            "tracking_code",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CheckoutRequestSerializer(serializers.Serializer):
    shipping_address_id = serializers.IntegerField(min_value=1)
    shipping_method_id = serializers.IntegerField(min_value=1)
    discount_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )



class CancellationRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CancellationRequest
        fields = ["order", "reason"]

    def validate_reason(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Reason is required."
        )

        return value
    def validate_order(self, order):
        user = self.context["request"].user

        if order.user_id != user.id:
            raise serializers.ValidationError(
            "Invalid order."
        )

        allowed_statuses = [
            Order.Status.PENDING,
            Order.Status.CONFIRMED,
            Order.Status.IN_PROGRESS,
    ]

        if order.status not in allowed_statuses:
            raise serializers.ValidationError(
                "Cancellation is not allowed for this order."
        )

        if CancellationRequest.objects.filter(
            order=order,
            status=CancellationRequest.Status.PENDING,
        ).exists():
            raise serializers.ValidationError(
                "A pending cancellation request already exists."
        )

        return order

class CancellationRequestSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(
        source="order.order_number",
        read_only=True,
    )

    class Meta:
        model = CancellationRequest
        fields = [
            "id",
            "order",
            "order_number",
            "reason",
            "status",
            "admin_note",
            "created_at",
            "reviewed_at",
        ]
        read_only_fields = fields