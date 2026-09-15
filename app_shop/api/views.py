from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from app_shop.models import Banner
from app_shop.api.serializers import BannerSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions  import IsAdminUser
from rest_framework import status

@swagger_auto_schema(
    method='get',
    operation_summary="List active banners",
    operation_description="Returns all banners where status is active. This is a public endpoint, no login required.",
    responses={200: BannerSerializer(many=True)}
)
@api_view(['GET'])
def banner_list(request):
    banners = Banner.objects.filter(is_active=True)
    serializer = BannerSerializer(banners, many=True)
    return Response({"banner_list": serializer.data})
    

@swagger_auto_schema(
    method='post',
    operation_summary="Create a new banner",
    operation_description="Creates a new banner. Only accessible by admin users.",
    request_body=BannerSerializer,
    responses={201: BannerSerializer, 400: "Invalid data"}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def banner_create(request):
    serializer = BannerSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='put',
    operation_summary="Update a banner",
    operation_description="Updates all fields of an existing banner. Only accessible by admin users.",
    request_body=BannerSerializer,
    responses={200: BannerSerializer, 400: "Invalid data", 404: "Banner not found"}
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def banner_update(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    serializer = BannerSerializer(banner, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a banner",
    operation_description="Deletes a banner permanently. Only accessible by admin users.",
    responses={204: "Banner deleted successfully", 404: "Banner not found"}
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def banner_delete(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    banner.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(
    method='patch',
    operation_summary="Change banner status",
    operation_description="Activates or deactivates a banner. Only accessible by admin users.",
    responses={200: BannerSerializer, 404: "Banner not found"}
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def banner_change_status(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    banner.is_active = not banner.is_active
    banner.save()
    serializer = BannerSerializer(banner)
    return Response(serializer.data)

@swagger_auto_schema(
    method='patch',
    operation_summary="Change banners display order",
    operation_description="Updates the sort_order of multiple banners at once. Only accessible by admin users." ,
    responses={200: "Banners order updated successfully"}
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def banner_display_order(request):
    for item in request.data:
        Banner.objects.filter(id=item['id']).update(sort_order=item['sort_order'])
    return Response({"message": "Banners order updated successfully"})