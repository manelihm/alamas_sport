from rest_framework import serializers
from app_users.models import Address, Favorite, ProductFeedback


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