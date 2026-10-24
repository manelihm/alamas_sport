from rest_framework import serializers
from app_cart.models import Cart, CartItem
from app_product.api.serializers import ProductOptionSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product_option = ProductOptionSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product_option', 'quantity', 'total_price']

    def get_total_price(self, obj):
        return obj.product_option.retail_price * obj.quantity


class AddCartItemSerializer(serializers.Serializer):
    product_option_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'status', 'discount_code', 'expires_at', 'items']


class CartSummarySerializer(serializers.Serializer):
    items_count = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=0)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=0)
    final_total = serializers.DecimalField(max_digits=12, decimal_places=0)


class ApplyDiscountCodeSerializer(serializers.Serializer):
    code = serializers.CharField()