from rest_framework.decorators import api_view
from rest_framework.response import Response
from app_shop.models import Banner
from app_shop.api.serializers import BannerSerializer


@api_view()
def banner_list(request):
    # get only the banners that should be shown (is_active = True)
    banners = Banner.objects.filter(is_active=True)

    # convert the banners (Python objects) into JSON-friendly data
    serializer = BannerSerializer(banners, many=True)

    return Response({"banner_list": serializer.data})
