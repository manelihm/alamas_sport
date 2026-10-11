from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view , permission_classes
from rest_framework.permissions import IsAuthenticated , IsAdminUser
from app_users.models import Address, Favorite, ProductFeedback
from app_users.api.serializers import (
    AddressSerializer,
    FavoriteSerializer, FavoriteCreateSerializer,
    ProductFeedbackSerializer, ProductFeedbackCreateSerializer,
)



@swagger_auto_schema(method='get', operation_summary="List my addresses", 
    responses={200: AddressSerializer(many=True)})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    serializer = AddressSerializer(addresses, many=True)
    return Response({"addresses": serializer.data})


@swagger_auto_schema(method='post', operation_summary="Add a new address", 
    request_body=AddressSerializer,
    responses={201: AddressSerializer, 400: "Invalid data"})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def address_create(request):
    serializer = AddressSerializer(data=request.data)
    if serializer.is_valid():
        address = serializer.save(user=request.user)
        return Response(AddressSerializer(address).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='put', operation_summary="Update an address", 
    request_body=AddressSerializer,
    responses={200: AddressSerializer, 400: "Invalid data", 404: "Not found"})
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def address_update(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    serializer = AddressSerializer(address, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(AddressSerializer(address).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='delete', operation_summary="Delete an address", 
    responses={204: "Deleted successfully", 404: "Not found"})
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(method='patch', operation_summary="Set address as default", 
    responses={200: AddressSerializer, 404: "Not found"})
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def address_set_default(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.is_default = True
    address.save()
    return Response(AddressSerializer(address).data)


@swagger_auto_schema(method='get', operation_summary="List my favorites",
    responses={200: FavoriteSerializer(many=True)})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user)
    serializer = FavoriteSerializer(favorites, many=True)
    return Response({"favorites": serializer.data})


@swagger_auto_schema(method='post', operation_summary="Add a product to favorites",
    request_body=FavoriteCreateSerializer,
    responses={201: FavoriteSerializer, 400: "Invalid data or already favorited"})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def favorite_create(request):
    serializer = FavoriteCreateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            favorite = serializer.save(user=request.user)
        except Exception:
            return Response({"error": "This product is already in your favorites."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(FavoriteSerializer(favorite).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='delete', operation_summary="Remove a product from favorites",
    responses={204: "Deleted successfully", 404: "Not found"})
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def favorite_delete(request, pk):
    favorite = get_object_or_404(Favorite, pk=pk, user=request.user)
    favorite.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(method='get', operation_summary="List my feedback",
    responses={200: ProductFeedbackSerializer(many=True)})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feedback_my_list(request):
    feedbacks = ProductFeedback.objects.filter(user=request.user)
    serializer = ProductFeedbackSerializer(feedbacks, many=True)
    return Response({"feedbacks": serializer.data})


@swagger_auto_schema(method='get', operation_summary="List approved feedback for a product",
    operation_description="Public endpoint. Only shows approved feedback.",
    responses={200: ProductFeedbackSerializer(many=True)})
@api_view(['GET'])
def feedback_product_list(request, product_id):
    feedbacks = ProductFeedback.objects.filter(product_id=product_id, status='APPROVED')
    serializer = ProductFeedbackSerializer(feedbacks, many=True)
    return Response({"feedbacks": serializer.data})


@swagger_auto_schema(method='post', operation_summary="Submit feedback for a product",
    operation_description="Submit a comment and/or a rating (1-5). At least one is required.",
    request_body=ProductFeedbackCreateSerializer,
    responses={201: ProductFeedbackSerializer, 400: "Invalid data or already reviewed"})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def feedback_create(request):
    serializer = ProductFeedbackCreateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            feedback = serializer.save(user=request.user)
        except Exception:
            return Response({"error": "You have already submitted feedback for this product."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ProductFeedbackSerializer(feedback).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='get', operation_summary="Get my feedback detail",
    responses={200: ProductFeedbackSerializer, 404: "Not found"})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feedback_my_detail(request, pk):
    feedback = get_object_or_404(ProductFeedback, pk=pk, user=request.user)
    serializer = ProductFeedbackSerializer(feedback)
    return Response(serializer.data)


@swagger_auto_schema(method='put', operation_summary="Update my feedback",
    operation_description="Only editable while status is still PENDING.",
    request_body=ProductFeedbackCreateSerializer,
    responses={200: ProductFeedbackSerializer, 400: "Invalid data or no longer editable", 404: "Not found"})
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def feedback_my_update(request, pk):
    feedback = get_object_or_404(ProductFeedback, pk=pk, user=request.user)
    if feedback.status != 'PENDING':
        return Response({"error": "This feedback has already been reviewed and can no longer be edited."}, status=status.HTTP_400_BAD_REQUEST)
    serializer = ProductFeedbackCreateSerializer(feedback, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(ProductFeedbackSerializer(feedback).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='delete', operation_summary="Delete my feedback",
    operation_description="Only deletable while status is still PENDING.",
    responses={204: "Deleted successfully", 400: "No longer deletable", 404: "Not found"})
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def feedback_my_delete(request, pk):
    feedback = get_object_or_404(ProductFeedback, pk=pk, user=request.user)
    if feedback.status != 'PENDING':
        return Response({"error": "This feedback has already been reviewed and can no longer be deleted."}, status=status.HTTP_400_BAD_REQUEST)
    feedback.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(method='get', operation_summary="List all feedback (admin)",
    operation_description="Only accessible by admin users.",
    manual_parameters=[
        openapi.Parameter('status', openapi.IN_QUERY, description="PENDING, APPROVED, or REJECTED", type=openapi.TYPE_STRING),
    ],
    responses={200: ProductFeedbackSerializer(many=True)})
@api_view(['GET'])
@permission_classes([IsAdminUser])
def feedback_admin_list(request):
    feedbacks = ProductFeedback.objects.all()
    status_filter = request.GET.get('status')
    if status_filter:
        feedbacks = feedbacks.filter(status=status_filter)
    serializer = ProductFeedbackSerializer(feedbacks, many=True)
    return Response({"feedbacks": serializer.data})


@swagger_auto_schema(method='get', operation_summary="Get feedback detail (admin)",
    responses={200: ProductFeedbackSerializer, 404: "Not found"})
@api_view(['GET'])
@permission_classes([IsAdminUser])
def feedback_admin_detail(request, pk):
    feedback = get_object_or_404(ProductFeedback, pk=pk)
    serializer = ProductFeedbackSerializer(feedback)
    return Response(serializer.data)


@swagger_auto_schema(method='patch', operation_summary="Approve feedback",
    operation_description="Only accessible by admin users.",
    responses={200: ProductFeedbackSerializer, 404: "Not found"})
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def feedback_approve(request, pk):
    feedback = get_object_or_404(ProductFeedback, pk=pk)
    feedback.status = 'APPROVED'
    feedback.save()
    return Response(ProductFeedbackSerializer(feedback).data)


@swagger_auto_schema(method='patch', operation_summary="Reject feedback",
    operation_description="Only accessible by admin users.",
    responses={200: ProductFeedbackSerializer, 404: "Not found"})
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def feedback_reject(request, pk):
    feedback = get_object_or_404(ProductFeedback, pk=pk)
    feedback.status = 'REJECTED'
    feedback.save()
    return Response(ProductFeedbackSerializer(feedback).data)


@swagger_auto_schema(method='delete', operation_summary="Delete feedback (admin)",
    operation_description="Deletes inappropriate feedback. Only accessible by admin users.",
    responses={204: "Deleted successfully", 404: "Not found"})
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def feedback_admin_delete(request, pk):
    feedback = get_object_or_404(ProductFeedback, pk=pk)
    feedback.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
