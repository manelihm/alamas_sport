from rest_framework import serializers
from django.utils import timezone
from app_product.models import (
    Category, Product, ProductImage,
    ProductColor, ProductSize, ProductMaterial,
    ProductOption, Discount, DiscountCode
)
from PIL import Image, UnidentifiedImageError

try:
    from PIL import DecompressionBombError
except ImportError:
    DecompressionBombError = OSError
from rest_framework import serializers

class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(
        source='parent.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Category
        fields = [
            'id',
            'parent',
            'parent_name',
            'name',
            'description',
            'is_active'
        ]
class CategoryTreeSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(
        source='parent.name',
        read_only=True,
        allow_null=True
    )
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id',
            'parent',
            'parent_name',
            'name',
            'description',
            'is_active',
            'children'
        ]

    def get_children(self, obj):
        children = obj.subcategories.filter(is_active=True)
        return CategoryTreeSerializer(children, many=True).data

        
MAX_PRODUCT_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_PRODUCT_IMAGE_WIDTH = 6000
MAX_PRODUCT_IMAGE_HEIGHT = 6000
ALLOWED_PRODUCT_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}

class ProductImageReadSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image_url', 'is_primary']
        read_only_fields = fields

    def get_image_url(self, obj):
        if not obj.image_url:
            return None
        try:
            url = obj.image_url.url
        except (ValueError, NotImplementedError):
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(url)
        return url

class ProductImageUploadSerializer(serializers.ModelSerializer):
    image_url = serializers.ImageField(
        required=True,
        allow_empty_file=False
    )

    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image_url', 'is_primary']
        read_only_fields = ['id']

    def validate_image_url(self, value):
        # 1. Check file size
        if value.size > MAX_PRODUCT_IMAGE_SIZE:
            raise serializers.ValidationError(
                'Image size must not exceed 5 MB.'
            )

        # 2. Verify that the uploaded file is a valid image
        try:
            value.seek(0)

            with Image.open(value) as image:
                image_format = image.format
                width, height = image.size

                # Verify the internal image structure
                image.verify()

        except (
            UnidentifiedImageError,
            DecompressionBombError,
            OSError,
            ValueError,
        ):
            raise serializers.ValidationError(
                'The uploaded file is not a valid image.'
            )

        finally:
            value.seek(0)

        # 3. Restrict allowed image formats
        if image_format not in ALLOWED_PRODUCT_IMAGE_FORMATS:
            raise serializers.ValidationError(
                'Only JPEG, PNG, and WebP image formats are allowed.'
            )

        # 4. Restrict image dimensions
        if (
            width > MAX_PRODUCT_IMAGE_WIDTH
            or height > MAX_PRODUCT_IMAGE_HEIGHT
        ):
            raise serializers.ValidationError(
                'Image dimensions must not exceed 6000 × 6000 pixels.'
            )

        return value
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

    def validate(self, attrs):
        start_at = attrs.get('start_at', getattr(self.instance, 'start_at', None))
        end_at = attrs.get('end_at', getattr(self.instance, 'end_at', None))
        discount_type = attrs.get('type', getattr(self.instance, 'type', None))
        value = attrs.get('value', getattr(self.instance, 'value', None))

        if start_at and end_at and start_at >= end_at:
            raise serializers.ValidationError(
                {"end_at": "end_at must be after start_at."}
            )

        if discount_type == 'percentage' and value is not None:
            if value < 0 or value > 100:
                raise serializers.ValidationError(
                    {"value": "Percentage discount must be between 0 and 100."}
                )

        if discount_type == 'fixed' and value is not None and value < 0:
            raise serializers.ValidationError(
                {"value": "Fixed discount cannot be negative."}
            )

        return attrs
class DiscountCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCode
        fields = ['id', 'code', 'type', 'value', 'start_at', 'end_at']

    def validate(self, attrs):
        start_at = attrs.get('start_at', getattr(self.instance, 'start_at', None))
        end_at = attrs.get('end_at', getattr(self.instance, 'end_at', None))
        discount_type = attrs.get('type', getattr(self.instance, 'type', None))
        value = attrs.get('value', getattr(self.instance, 'value', None))

        if start_at and end_at and start_at >= end_at:
            raise serializers.ValidationError(
                {"end_at": "end_at must be after start_at."}
            )

        if discount_type == 'percentage' and value is not None:
            if value < 0 or value > 100:
                raise serializers.ValidationError(
                    {"value": "Percentage discount must be between 0 and 100."}
                )

        if discount_type == 'fixed' and value is not None and value < 0:
            raise serializers.ValidationError(
                {"value": "Fixed discount cannot be negative."}
            )

        return attrs

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
            'stock', 'is_active', 'active_discount'
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
    images = serializers.SerializerMethodField()
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Product
        fields = ['id', 'category', 'name', 'description', 'brand', 'gender', 'is_active', 'images']

    def get_images(self, obj):
        images = (
            ProductImage.objects
            .filter(product__product=obj)
            .select_related('product')
            .order_by('-is_primary', 'id')
        )
        return ProductImageReadSerializer(
            images,
            many=True,
            context=self.context
        ).data


class ProductDetailSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    options = ProductOptionSerializer(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Product
        fields = ['id', 'category', 'name', 'description', 'brand', 'gender', 'is_active', 'images', 'options']

    def get_images(self, obj):
        images = (
            ProductImage.objects
            .filter(product__product=obj)
            .select_related('product')
            .order_by('-is_primary', 'id')
        )
        return ProductImageReadSerializer(
            images,
            many=True,
            context=self.context
        ).data












