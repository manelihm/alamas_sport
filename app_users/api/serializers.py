from rest_framework import serializers
from app_users.models import Address, Favorite, ProductFeedback ,ProductRequest


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