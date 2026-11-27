from rest_framework import serializers
from django.utils import timezone
from app_product.models import (
    Brand,Category, Product, ProductImage,
    ProductColor, ProductSize, ProductMaterial,
    ProductOption, Discount, DiscountCode
)
from app_order.services import calculate_discount
from PIL import Image, UnidentifiedImageError
from decimal import Decimal, ROUND_HALF_UP

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

    def validate(self, attrs):
        parent = attrs.get(
            "parent",
            self.instance.parent if self.instance else None
        )

        if not parent:
            return attrs

        current = parent
        visited = set()

        while current:
            if current.pk in visited:
                raise serializers.ValidationError({
                    "parent": "Invalid category hierarchy detected."
                })

            visited.add(current.pk)

            if self.instance and current.pk == self.instance.pk:
                raise serializers.ValidationError({
                    "parent": "A category cannot be placed under its descendant."
                })

            current = current.parent

        return attrs
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
            'children',
        ]

    def get_children(self, obj):
        children = obj.subcategories.filter(
            is_active=True
        ).order_by('id')

        return CategoryTreeSerializer(
            children,
            many=True,
            context=self.context
        ).data

        
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
    images = serializers.SerializerMethodField()

    class Meta:
        model = Discount
        fields = [
            'id',
            'product',
            'type',
            'value',
            'start_at',
            'end_at',
            'images',
        ]

    def get_images(self, obj):
        images = obj.product.images.all().order_by('-is_primary', 'id')

        return ProductImageReadSerializer(
            images,
            many=True,
            context=self.context
        ).data
    def validate(self, attrs):
        start_at = attrs.get(
            "start_at",
            getattr(self.instance, "start_at", None)
        )
        end_at = attrs.get(
            "end_at",
            getattr(self.instance, "end_at", None)
        )
        discount_type = attrs.get(
            "type",
            getattr(self.instance, "type", None)
        )
        value = attrs.get(
            "value",
            getattr(self.instance, "value", None)
        )
        product = attrs.get(
            "product",
            getattr(self.instance, "product", None)
        )

        if start_at and end_at and start_at >= end_at:
            raise serializers.ValidationError({
                "end_at": "End date must be after start date."
            })

        if value is not None and value <= 0:
            raise serializers.ValidationError({
                "value": "Discount value must be greater than zero."
            })

        if discount_type == "percentage" and value is not None:
            if value > 100:
                raise serializers.ValidationError({
                    "value": "Percentage discount cannot exceed 100."
                })

        if discount_type == "fixed" and product and value is not None:
            if (
                value > product.retail_price
                or value > product.wholesale_price
            ):
                raise serializers.ValidationError({
                    "value": "Fixed discount cannot exceed the retail or wholesale price."
                })

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
            if value <= 0 or value > 100:
                raise serializers.ValidationError({
                    "value": "Percentage discount must be greater than 0 and at most 100."
                })

        if discount_type == 'fixed' and value is not None:
            if value <= 0:
                raise serializers.ValidationError({
                    "value": "Fixed discount must be greater than 0."
                })
            

        return attrs

class DiscountCodeApplySerializer(serializers.Serializer):
    code = serializers.CharField(
        max_length=50,
        trim_whitespace=True
    )

class ProductOptionSerializer(serializers.ModelSerializer):
    color = ProductColorSerializer(read_only=True)
    size = ProductSizeSerializer(read_only=True)
    material = ProductMaterialSerializer(read_only=True)

    active_discount = serializers.SerializerMethodField()

    retail_original_price = serializers.SerializerMethodField()
    retail_discount_price = serializers.SerializerMethodField()
    retail_discount_amount = serializers.SerializerMethodField()
    retail_discount_percentage = serializers.SerializerMethodField()

    wholesale_original_price = serializers.SerializerMethodField()
    wholesale_discount_price = serializers.SerializerMethodField()
    wholesale_discount_amount = serializers.SerializerMethodField()
    wholesale_discount_percentage = serializers.SerializerMethodField()

    def get_discount_data(self, obj, price_field):
        now = timezone.now()
        original = Decimal(str(getattr(obj, price_field)))

        discounts = obj.discounts.filter(
            start_at__lte=now,
            end_at__gte=now,
        )

        best_discount = None
        best_amount = Decimal("0")

        for discount in discounts:
            amount = calculate_discount(
                original,
                discount.type,
                discount.value,
            )

            if amount > best_amount:
                best_discount = discount
                best_amount = amount

        final_price = original - best_amount

        percentage = (
            best_amount * Decimal("100") / original
            if original > 0 else Decimal("0")
        )

        return {
            "original_price": original,
            "discount_price": final_price,
            "discount_amount": best_amount,
            "discount_percentage": percentage.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            ),
        }

    def get_retail_original_price(self, obj):
        return self.get_discount_data(obj, "retail_price")["original_price"]

    def get_retail_discount_price(self, obj):
        return self.get_discount_data(obj, "retail_price")["discount_price"]

    def get_retail_discount_amount(self, obj):
        return self.get_discount_data(obj, "retail_price")["discount_amount"]

    def get_retail_discount_percentage(self, obj):
        return self.get_discount_data(obj, "retail_price")["discount_percentage"]

    def get_wholesale_original_price(self, obj):
        return self.get_discount_data(obj, "wholesale_price")["original_price"]

    def get_wholesale_discount_price(self, obj):
        return self.get_discount_data(obj, "wholesale_price")["discount_price"]

    def get_wholesale_discount_amount(self, obj):
        return self.get_discount_data(obj, "wholesale_price")["discount_amount"]

    def get_wholesale_discount_percentage(self, obj):
        return self.get_discount_data(obj, "wholesale_price")["discount_percentage"]

    def get_active_discount(self, obj):
        now = timezone.now()
        discounts = obj.discounts.filter(
            start_at__lte=now,
            end_at__gte=now,
        )

        best_discount = None
        best_amount = Decimal("0")

        for discount in discounts:
            amount = calculate_discount(
                obj.retail_price,
                discount.type,
                discount.value,
            )

            if amount > best_amount:
                best_discount = discount
                best_amount = amount

        return (
            DiscountSerializer(best_discount).data
            if best_discount else None
        )

    class Meta:
        model = ProductOption
        fields = [
            "id",
            "color",
            "size",
            "material",
            "retail_price",
            "wholesale_price",
            "retail_original_price",
            "retail_discount_price",
            "retail_discount_amount",
            "retail_discount_percentage",
            "wholesale_original_price",
            "wholesale_discount_price",
            "wholesale_discount_amount",
            "wholesale_discount_percentage",
            "stock",
            "is_active",
            "active_discount",
        ]
class ProductOptionCreateSerializer(serializers.ModelSerializer):
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = ProductOption
        fields = [
            'id', 'product', 'color', 'size', 'brand', 'material',
            'retail_price', 'wholesale_price', 'wholesale_min_quantity',
            'stock', 'is_active',
        ]
class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    brands = serializers.SerializerMethodField()
    options = ProductOptionSerializer(
        many=True,
        read_only=True
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'name', 'description', 'gender',
            'is_active', 'images', 'brands', 'options',
            'is_trending', 'trending_sort_order', 'trending_is_active',
        ]

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

    def get_brands(self, obj):
        brands = Brand.objects.filter(
            options__product=obj,
            options__is_active=True,
            is_active=True,
        ).distinct().order_by('name')

        return BrandSerializer(
            brands,
            many=True,
            context=self.context
        ).data


class ProductDetailSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    brands = serializers.SerializerMethodField()
    options = ProductOptionSerializer(
        many=True,
        read_only=True
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'name', 'description', 'gender',
            'is_active', 'images', 'brands', 'options',
            'is_trending', 'trending_sort_order', 'trending_is_active',
        ]

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

    def get_brands(self, obj):
        brands = Brand.objects.filter(
            options__product=obj,
            options__is_active=True,
            is_active=True,
        ).distinct().order_by('name')

        return BrandSerializer(
            brands,
            many=True,
            context=self.context
        ).data
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']











