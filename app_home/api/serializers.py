from rest_framework import serializers
from app_home.models import Banner ,HomeContent, TrendingProduct, CompanyInformation, CompanyInformationContent
from app_product.api.serializers import ProductSerializer



class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = [
            "id",
            "title",
            "description",
            "image",
            "button_link",
            "button_text",
            "sort_order",
        ]




class  HomeContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeContent
        fields = ['id', 'type', 'title', 'sort_order', 'is_active', 'banner', 'discount', 'category']

class TrendingProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = TrendingProduct
        fields = ['id', 'product', 'home_content', 'sort_order', 'is_active']


class TrendingProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrendingProduct
        fields = ['id', 'product', 'home_content', 'sort_order', 'is_active']


class CompanyInformationContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyInformationContent
        fields = ['id', 'title', 'value', 'sort_order']


class CompanyInformationSerializer(serializers.ModelSerializer):
    contents = CompanyInformationContentSerializer(many=True, read_only=True)

    class Meta:
        model = CompanyInformation
        fields = ['id', 'title', 'description', 'logo_url', 'is_active', 'contents']


class CompanyInformationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyInformation
        fields = ['title', 'description', 'logo_url']