from rest_framework import serializers
from app_users.models import Address, Favorite, ProductFeedback ,ProductRequest
from app_auth.models import User


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'province', 'city', 'address', 'postal_code', 'is_default']




class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'product', 'created_at']


class FavoriteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'product']


class ProductFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFeedback
        fields = ['id', 'user', 'product', 'content', 'rating', 'status', 'created_at']
        read_only_fields = ['user', 'status']


class ProductFeedbackCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProductFeedback
        fields = ['id', 'product', 'content', 'rating']

        rating = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=5,
    )

    def validate(self, data):
        if not data.get('content') and not data.get('rating'):
            raise serializers.ValidationError("Provide at least a comment or a rating.")
        return data



class ProductRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRequest
        fields = ['id', 'user', 'title', 'description', 'status', 'admin_note', 'created_at']
        read_only_fields = ['user', 'status', 'admin_note']


class ProductRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRequest
        fields = ['id', 'title', 'description']


class ProductRequestStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ProductRequest.Status.choices)
    admin_note = serializers.CharField(required=False, allow_blank=True)



class ProfileOverviewSerializer(serializers.ModelSerializer):
    addresses_count = serializers.IntegerField(read_only=True)
    favorites_count = serializers.IntegerField(read_only=True)
    feedbacks_count = serializers.IntegerField(read_only=True)
    product_requests_count = serializers.IntegerField(read_only=True)
    orders_count = serializers.IntegerField(read_only=True)

    default_address = AddressSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "username",
            "first_name",
            "last_name",
            "gender",
            "image",
            "created_at",
            "addresses_count",
            "favorites_count",
            "feedbacks_count",
            "product_requests_count",
            "orders_count",
            "default_address",
        ]