from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from app_order.models import (
    Order,
    OrderItem,
    CancellationRequest,
    ShippingMethod,
)
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
    original_total_price = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()

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
            "original_total_price",
            "discount_amount",
            "discount_percentage",
            "total_price",
            "created_at",
        ]
        read_only_fields = fields

    def get_original_total_price(self, obj):
        return obj.unit_price * obj.quantity

    def get_discount_percentage(self, obj):
        original = obj.unit_price * obj.quantity

        if original <= 0:
            return Decimal("0")

        return (
            obj.discount_amount * Decimal("100") / original
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )




class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    product_discount_amount = serializers.SerializerMethodField()
    code_discount_amount = serializers.SerializerMethodField()
    code_discount_percentage = serializers.SerializerMethodField()
    total_discount_percentage = serializers.SerializerMethodField()

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
            "product_discount_amount",
            "code_discount_snapshot",
            "code_discount_amount",
            "code_discount_percentage",
            "discount_amount",
            "total_discount_percentage",
            "shipping_cost",
            "final_amount",
            "tracking_code",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_product_discount_amount(self, obj):
        return sum(
            (item.discount_amount for item in obj.items.all()),
            Decimal("0")
        )

    def get_code_discount_amount(self, obj):
        product_discount = self.get_product_discount_amount(obj)

        return max(
            Decimal("0"),
            obj.discount_amount - product_discount
        )

    def get_code_discount_percentage(self, obj):
        product_discount = self.get_product_discount_amount(obj)

        code_base = obj.total_amount - product_discount
        code_discount = self.get_code_discount_amount(obj)

        if code_base <= 0:
            return Decimal("0")

        return (
            code_discount * Decimal("100") / code_base
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    def get_total_discount_percentage(self, obj):
        if obj.total_amount <= 0:
            return Decimal("0")

        return (
            obj.discount_amount * Decimal("100") / obj.total_amount
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

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

