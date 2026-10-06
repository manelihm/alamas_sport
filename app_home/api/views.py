from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from app_home.models import Banner ,HomeContent, TrendingProduct, CompanyInformation, CompanyInformationContent
from app_home.api.serializers import BannerSerializer,HomeContentCreateSerializer,HomeContentSerializer, TrendingProductSerializer, TrendingProductCreateSerializer,CompanyInformationSerializer, CompanyInformationUpdateSerializer,CompanyInformationContentSerializer
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



@swagger_auto_schema(method='get', operation_summary="List trending products",
    operation_description="Returns active trending products ordered by sort_order.",
    responses={200: TrendingProductSerializer(many=True)})
@api_view(['GET'])
def trending_product_list(request):
    trending = TrendingProduct.objects.filter(is_active=True).order_by('sort_order')
    serializer = TrendingProductSerializer(trending, many=True)
    return Response({"trending_products": serializer.data})




@swagger_auto_schema(method='get', operation_summary="Get trending product detail",
    responses={200: TrendingProductSerializer, 404: "Not found"})
@api_view(['GET'])
def trending_product_detail(request, pk):
    trending = get_object_or_404(TrendingProduct, pk=pk, is_active=True)
    serializer = TrendingProductSerializer(trending)
    return Response(serializer.data)


@swagger_auto_schema(method='post', operation_summary="Add product to trending list", 
    operation_description="Only accessible by admin users.",
    request_body=TrendingProductCreateSerializer,
    responses={201: TrendingProductCreateSerializer, 400: "Invalid data"})
@api_view(['POST'])
@permission_classes([IsAdminUser])
def trending_product_create(request):
    serializer = TrendingProductCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='put', operation_summary="Update trending product", 
    operation_description="Only accessible by admin users.",
    request_body=TrendingProductCreateSerializer,
    responses={200: TrendingProductCreateSerializer, 400: "Invalid data", 404: "Not found"})
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def trending_product_update(request, pk):
    trending = get_object_or_404(TrendingProduct, pk=pk)
    serializer = TrendingProductCreateSerializer(trending, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='delete', operation_summary="Remove from trending list", 
    operation_description="Only accessible by admin users.",
    responses={204: "Deleted successfully", 404: "Not found"})
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def trending_product_delete(request, pk):
    trending = get_object_or_404(TrendingProduct, pk=pk)
    trending.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(method='patch', operation_summary="Reorder trending products", 
    operation_description="Updates sort_order of multiple trending entries. Only accessible by admin users. Example body: [{\"id\": 1, \"sort_order\": 2}]",
    responses={200: "Order updated successfully"})
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def trending_product_reorder(request):
    for item in request.data:
        TrendingProduct.objects.filter(id=item['id']).update(sort_order=item['sort_order'])
    return Response({"message": "Trending order updated successfully"})


@swagger_auto_schema(method='patch', operation_summary="Change trending status", 
    operation_description="Toggles active/inactive status. Only accessible by admin users.",
    responses={200: TrendingProductSerializer, 404: "Not found"})
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def trending_product_change_status(request, pk):
    trending = get_object_or_404(TrendingProduct, pk=pk)
    trending.is_active = not trending.is_active
    trending.save()
    return Response(TrendingProductSerializer(trending).data)

@swagger_auto_schema(method='get', operation_summary="Get company main information",
    operation_description="Returns the company's main info: title, description, logo, status.",
    responses={200: CompanyInformationSerializer})
@api_view(['GET'])
def company_information_detail(request):
    company = CompanyInformation.objects.filter(is_active=True).first()
    if not company:
        return Response({"error": "Company information not set yet."}, status=status.HTTP_404_NOT_FOUND)
    serializer = CompanyInformationSerializer(company)
    return Response(serializer.data)


@swagger_auto_schema(method='put', operation_summary="Update company main information",
    operation_description="Only accessible by admin users.",
    request_body=CompanyInformationUpdateSerializer,
    responses={200: CompanyInformationSerializer, 400: "Invalid data"})
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def company_information_update(request):
    company = CompanyInformation.objects.get_or_create(id=1)
    serializer = CompanyInformationUpdateSerializer(company, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(CompanyInformationSerializer(company).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='get', operation_summary="List company text sections",
    operation_description="Returns text content sections ordered by sort_order.",
    responses={200: CompanyInformationContentSerializer(many=True)})
@api_view(['GET'])
def company_content_list(request):
    contents = CompanyInformationContent.objects.all().order_by('sort_order')
    serializer = CompanyInformationContentSerializer(contents, many=True)
    return Response({"contents": serializer.data})


@swagger_auto_schema(method='get', operation_summary="Get a text section detail",
    responses={200: CompanyInformationContentSerializer, 404: "Not found"})
@api_view(['GET'])
def company_content_detail(request, pk):
    content = get_object_or_404(CompanyInformationContent, pk=pk)
    serializer = CompanyInformationContentSerializer(content)
    return Response(serializer.data)


@swagger_auto_schema(method='post', operation_summary="Add a new text section",
    operation_description="Only accessible by admin users.",
    request_body=CompanyInformationContentSerializer,
    responses={201: CompanyInformationContentSerializer, 400: "Invalid data"})
@api_view(['POST'])
@permission_classes([IsAdminUser])
def company_content_create(request):
    company, _ = CompanyInformation.objects.get_or_create(id=1)
    serializer = CompanyInformationContentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(company_information=company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='put', operation_summary="Update a text section",
    operation_description="Only accessible by admin users.",
    request_body=CompanyInformationContentSerializer,
    responses={200: CompanyInformationContentSerializer, 400: "Invalid data", 404: "Not found"})
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def company_content_update(request, pk):
    content = get_object_or_404(CompanyInformationContent, pk=pk)
    serializer = CompanyInformationContentSerializer(content, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='delete', operation_summary="Delete a text section",
    operation_description="Only accessible by admin users.",
    responses={204: "Deleted successfully", 404: "Not found"})
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def company_content_delete(request, pk):
    content = get_object_or_404(CompanyInformationContent, pk=pk)
    content.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(method='patch', operation_summary="Reorder text sections",
    operation_description="Only accessible by admin users. Example body: [{\"id\": 1, \"sort_order\": 2}]",
    responses={200: "Order updated successfully"})
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def company_content_reorder(request):
    for item in request.data:
        CompanyInformationContent.objects.filter(id=item['id']).update(sort_order=item['sort_order'])
    return Response({"message": "Content order updated successfully"})




@swagger_auto_schema(
    method='get',
    operation_summary="Get home page structure",
    operation_description="Returns the full current structure of the home page (all sections, including banners, trending, discounts, categories, company info) ordered by sort_order. Only accessible by admin users.",
    responses={200: HomeContentSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def home_content_list(request):
    contents = HomeContent.objects.all().order_by('sort_order')
    serializer = HomeContentSerializer(contents, many=True)
    return Response({"home_contents": serializer.data})


@swagger_auto_schema(
    method='post',
    operation_summary="Create a home page section",
    operation_description="Creates a new home content section, linked to a banner, discount, or category depending on type. Only accessible by admin users.",
    request_body=HomeContentCreateSerializer,
    responses={201: HomeContentSerializer, 400: "Invalid data"}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def home_content_create(request):
    serializer = HomeContentCreateSerializer(data=request.data)
    if serializer.is_valid():
        content = serializer.save()
        return Response(HomeContentSerializer(content).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='put',
    operation_summary="Update a home page section",
    operation_description="Fully updates a home content section: title, sort_order, status, and the linked banner/discount/category id. Only accessible by admin users.",
    request_body=HomeContentCreateSerializer,
    responses={200: HomeContentSerializer, 400: "Invalid data", 404: "Not found"}
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def home_content_update(request, pk):
    content = get_object_or_404(HomeContent, pk=pk)
    serializer = HomeContentCreateSerializer(content, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(HomeContentSerializer(content).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a home page section",
    operation_description="Only accessible by admin users.",
    responses={204: "Deleted successfully", 404: "Not found"}
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def home_content_delete(request, pk):
    content = get_object_or_404(HomeContent, pk=pk)
    content.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method='patch',
    operation_summary="Reorder home page sections",
    operation_description="Updates sort_order of multiple home content sections. Only accessible by admin users. Example body: [{\"id\": 1, \"sort_order\": 2}]",
    responses={200: "Order updated successfully"}
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def home_content_reorder(request):
    for item in request.data:
        HomeContent.objects.filter(id=item['id']).update(sort_order=item['sort_order'])
    return Response({"message": "Home page order updated successfully"})


@swagger_auto_schema(
    method='patch',
    operation_summary="Change home section status",
    operation_description="Toggles active/inactive status of a home content section. Only accessible by admin users.",
    responses={200: HomeContentSerializer, 404: "Not found"}
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def home_content_change_status(request, pk):
    content = get_object_or_404(HomeContent, pk=pk)
    content.is_active = not content.is_active
    content.save()
    return Response(HomeContentSerializer(content).data)

