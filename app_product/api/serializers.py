from rest_framework import serializers
from django.utils import timezone
from app_product.models import (
    Category, Product, ProductImage,
    ProductColor, ProductSize, ProductMaterial,
    ProductOption, Discount , DiscountCode
)



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'parent', 'name', 'description', 'is_active']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'is_primary']


class ProductColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductColor
        fields = ['id', 'name', 'color_code']


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ['id', 'name']


class ProductMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMaterial
        fields = ['id', 'name', 'description']


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['id', 'product', 'type', 'value', 'start_at', 'end_at']

class DiscountCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCode
        fields = ['id', 'code', 'type', 'value', 'start_at', 'end_at',]


class DiscountCodeApplySerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCode
        fields = ['id', 'code', 'type', 'value', 'is_used', 'used_at']


class ProductOptionSerializer(serializers.ModelSerializer):
    color = ProductColorSerializer(read_only=True)
    size = ProductSizeSerializer(read_only=True)
    material = ProductMaterialSerializer(read_only=True)
    active_discount = serializers.SerializerMethodField()

    class Meta:
        model = ProductOption
        fields = [
            'id', 'color', 'size', 'material',
            'retail_price', 'wholesale_price', 'wholesale_min_quantity',
            'stock','is_active', 'active_discount'
        ]

    def get_active_discount(self, obj):
        now = timezone.now()
        discount = obj.discounts.filter(
            start_at__lte=now, end_at__gte=now
        ).first()
        if discount:
            return DiscountSerializer(discount).data
        return None


class ProductOptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOption
        fields = [
            'id', 'product', 'color', 'size', 'material',
            'retail_price', 'wholesale_price', 'wholesale_min_quantity',
            'stock', 'is_active',
        ]


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'category', 'name', 'description', 'brand', 'gender', 'is_active', 'images']


class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    options = ProductOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'category', 'name', 'description', 'brand', 'gender', 'is_active', 'images', 'options']




