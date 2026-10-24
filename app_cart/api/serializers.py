from rest_framework import serializers

from app_cart.models import Cart, CartItem
from app_product.api.serializers import ProductOptionSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product_option = ProductOptionSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product_option",
            "quantity",
            "price_type",
            "unit_price",
            "total_price",
            "snapshot",
        ]
        read_only_fields = [
            "id",
            "product_option",
            "unit_price",
            "total_price",
            "snapshot",
        ]

    def get_total_price(self, obj):
        return obj.unit_price * obj.quantity


class AddCartItemSerializer(serializers.Serializer):
    product_option_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)
    price_type = serializers.ChoiceField(
        choices=CartItem.PriceType.choices,
        default=CartItem.PriceType.RETAIL,
    )


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    discount_code = serializers.CharField(
        source="discount_code.code",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Cart
        fields = [
            "id",
            "status",
            "discount_code",
            "created_at",
            "updated_at",
            "expires_at",
            "items",
        ]
        read_only_fields = fields


class CartSummarySerializer(serializers.Serializer):
    items_count = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=0)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=0)
    final_total = serializers.DecimalField(max_digits=12, decimal_places=0)


class ApplyDiscountCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50, trim_whitespace=True)