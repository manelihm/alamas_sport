from rest_framework import serializers
from app_product.models import (
    Category, Subcategory, Product,
    ProductColor, ProductSize, ProductOption,
    ProductImage, ProductMaterial ,Discount
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active']


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['id', 'category', 'name', 'description', 'is_active']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'is_primary']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'category', 'subcategory', 'name', 'description', 'brand', 'gender', 'is_active', 'images']


class SubcategoryDetailSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Subcategory
        fields = ['id', 'category', 'name', 'description', 'is_active', 'products']


class ProductColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductColor
        fields = ['id', 'name', 'color_code']


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ['id', 'name', 'is_active']


class ProductOptionSerializer(serializers.ModelSerializer):
    color = ProductColorSerializer(read_only=True)
    size = ProductSizeSerializer(read_only=True)

    class Meta:
        model = ProductOption
        fields = ['id', 'color', 'size', 'retail_price', 'wholesale_price', 'stock', 'status']


class ProductMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMaterial
        fields = ['id', 'name', 'description']

class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['id', 'product', 'type', 'value', 'start_at', 'end_at', 'status']
        

class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    options = ProductOptionSerializer(many=True, read_only=True)
    materials = ProductMaterialSerializer(many=True, read_only=True)
    active_discount = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'category', 'subcategory', 'name', 'description', 'brand', 'gender', 'is_active', 'images', 'options', 'materials', 'active_discount']

    def get_active_discount(self, obj):
        from django.utils import timezone
        discount = obj.discounts.filter(
            status=True,
            start_at__lte=timezone.now(),
            end_at__gte=timezone.now()
        ).first()
        if discount:
            return DiscountSerializer(discount).data
        return None

