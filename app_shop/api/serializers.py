from rest_framework import serializers
from app_shop.models import Banner


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
