from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view , permission_classes
from rest_framework.permissions import IsAuthenticated , IsAdminUser
from django.db.models import Count, Q
from app_cart.models import Cart
from app_order.models import Order
from app_users.models import Address, Favorite, ProductFeedback ,ProductRequest
from app_users.api.serializers import (
    AddressSerializer,
    FavoriteSerializer, FavoriteCreateSerializer,
    ProductFeedbackSerializer, ProductFeedbackCreateSerializer,ProductRequestSerializer, ProductRequestCreateSerializer, ProductRequestStatusSerializer,ProfileOverviewSerializer,
)

from django.utils import timezone
from app_order.api.serializers import OrderSerializer
from django.db import transaction
from django.db import IntegrityError
from app_product.api.serializers import ProductSerializer
from app_product.models import Product
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response


@swagger_auto_schema(method='get', operation_summary="List my addresses", 
    responses={200: AddressSerializer(many=True)})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def address_list(request):
    addresses = Address.objects.filter(
    user=request.user).order_by("-is_default", "-created_at", "-id")
    serializer = AddressSerializer(addresses, many=True)
    return Response({"data": serializer.data, "message": "Addresses retrieved successfully"})


@swagger_auto_schema(
    method="post",
    operation_summary="Add a new address",
    request_body=AddressSerializer,
    responses={
        201: AddressSerializer,
        400: "Invalid data",
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def address_create(request):
    serializer = AddressSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    with transaction.atomic():
        is_default = serializer.validated_data.get("is_default", False)

        if is_default:
            Address.objects.filter(
                user=request.user,
                is_default=True,
            ).update(is_default=False)

        address = serializer.save(user=request.user)

        if Address.objects.filter(user=request.user).count() == 1:
            address.is_default = True
            address.save(update_fields=["is_default", "updated_at"])

    return Response(
        {
            "data": AddressSerializer(address).data,
            "message": "Address created successfully",
        },
        status=status.HTTP_201_CREATED,
    )
@swagger_auto_schema(
    method="put",
    operation_summary="Update an address",
    request_body=AddressSerializer,
    responses={
        200: AddressSerializer,
        400: "Invalid data",
        404: "Address not found",
    },
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def address_update(request, pk):
    with transaction.atomic():
        address = get_object_or_404(
            Address.objects.select_for_update(),
            pk=pk,
            user=request.user,
        )

        serializer = AddressSerializer(address, data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get("is_default", False):
            Address.objects.filter(
                user=request.user,
                is_default=True,
            ).exclude(pk=address.pk).update(is_default=False)

        address = serializer.save()

    return Response(
        {
            "data": AddressSerializer(address).data,
            "message": "Address updated successfully",
        },
        status=status.HTTP_200_OK,
    )

@swagger_auto_schema(
    method="delete",
    operation_summary="Delete an address",
    responses={
        204: "Deleted successfully",
        404: "Address not found",
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def address_delete(request, pk):
    with transaction.atomic():
        address = get_object_or_404(
            Address.objects.select_for_update(),
            pk=pk,
            user=request.user,
        )

        was_default = address.is_default
        address.delete()

        if was_default:
            next_address = Address.objects.filter(
                user=request.user,
            ).order_by("-created_at", "-id").first()

            if next_address:
                next_address.is_default = True
                next_address.save(
                    update_fields=["is_default", "updated_at"]
                )

    return Response(status=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(
    method="patch",
    operation_summary="Set address as default",
    responses={
        200: AddressSerializer,
        404: "Address not found",
    },
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def address_set_default(request, pk):
    with transaction.atomic():
        address = get_object_or_404(
            Address.objects.select_for_update(),
            pk=pk,
            user=request.user,
        )

        Address.objects.filter(
            user=request.user,
            is_default=True,
        ).exclude(pk=address.pk).update(is_default=False)

        address.is_default = True
        address.save(update_fields=["is_default", "updated_at"])

    return Response(
        {
            "data": AddressSerializer(address).data,
            "message": "Default address set successfully",
        },
        status=status.HTTP_200_OK,
    )
@swagger_auto_schema(method='get', operation_summary="List my favorites",
    responses={200: FavoriteSerializer(many=True)})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def favorite_list(request):
    favorites = Favorite.objects.filter(
    user=request.user).select_related(
    "product").order_by("-created_at", "-id")
    serializer = FavoriteSerializer(favorites, many=True)
    return Response({"data": serializer.data, "message": "Favorites retrieved successfully"})


@swagger_auto_schema(
    method="post",
    operation_summary="Add a product to favorites",
    request_body=FavoriteCreateSerializer,
    responses={
        201: FavoriteSerializer,
        400: "Invalid data or already favorited",
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def favorite_create(request):
    serializer = FavoriteCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    product = serializer.validated_data["product"]

    if not product.is_active:
        return Response(
            {"detail": "This product is not available."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        favorite = serializer.save(user=request.user)
    except IntegrityError:
        return Response(
            {"detail": "This product is already in your favorites."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if Favorite.objects.filter(
        user=request.user,
        product=product,).exists():
        return Response(
            {"detail": "This product is already in your favorites."},
            status=status.HTTP_400_BAD_REQUEST,
    )

    return Response(
        {
            "data": FavoriteSerializer(favorite).data,
            "message": "Product added to favorites successfully",
        },
        status=status.HTTP_201_CREATED,
    )

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
    feedbacks = ProductFeedback.objects.filter(
    user=request.user).select_related(
    "product").order_by("-created_at", "-id")
    serializer = ProductFeedbackSerializer(feedbacks, many=True)
    return Response({"data": serializer.data, "message": "Your feedback retrieved successfully"})


@swagger_auto_schema(method='get', operation_summary="List approved feedback for a product",
    operation_description="Public endpoint. Only shows approved feedback.",
    responses={200: ProductFeedbackSerializer(many=True)})
@api_view(['GET'])
def feedback_product_list(request, product_id):
    feedbacks = ProductFeedback.objects.filter(product_id=product_id, status='APPROVED')
    serializer = ProductFeedbackSerializer(feedbacks, many=True)
    return Response({"data": serializer.data, "message": "Product feedback retrieved successfully"})


@swagger_auto_schema(
    method="post",
    operation_summary="Submit feedback for a product",
    operation_description=(
        "Submit a comment and/or a rating (1-5). "
        "At least one is required."
    ),
    request_body=ProductFeedbackCreateSerializer,
    responses={
        201: ProductFeedbackSerializer,
        400: "Invalid data or feedback already exists",
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def feedback_create(request):
    serializer = ProductFeedbackCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    product = serializer.validated_data["product"]

    if not product.is_active:
        return Response(
            {"detail": "Feedback cannot be submitted for an inactive product."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        feedback = serializer.save(user=request.user)
    except IntegrityError:
        return Response(
            {
                "detail": (
                    "You have already submitted feedback "
                    "for this product."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "data": ProductFeedbackSerializer(feedback).data,
            "message": "Feedback submitted successfully",
        },
        status=status.HTTP_201_CREATED,
    )

@swagger_auto_schema(method='get', operation_summary="Get my feedback detail",
    responses={200: ProductFeedbackSerializer, 404: "Not found"})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feedback_my_detail(request, pk):
    feedback = get_object_or_404(ProductFeedback, pk=pk, user=request.user)
    serializer = ProductFeedbackSerializer(feedback)
    return Response({"data": serializer.data, "message": "Feedback retrieved successfully"})


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
        return Response({"data": ProductFeedbackSerializer(feedback).data, "message": "Feedback updated successfully"})
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
    return Response({"data": serializer.data, "message": "Feedback list retrieved successfully"})


@swagger_auto_schema(method='get', operation_summary="Get feedback detail (admin)",
    responses={200: ProductFeedbackSerializer, 404: "Not found"})
@api_view(['GET'])
@permission_classes([IsAdminUser])
def feedback_admin_detail(request, pk):
    feedback = get_object_or_404(ProductFeedback, pk=pk)
    serializer = ProductFeedbackSerializer(feedback)
    return Response({"data": serializer.data, "message": "Feedback retrieved successfully"})


@swagger_auto_schema(method='patch', operation_summary="Approve feedback",
    operation_description="Only accessible by admin users.",
    responses={200: ProductFeedbackSerializer, 404: "Not found"})
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def feedback_approve(request, pk):
    feedback = get_object_or_404(ProductFeedback, pk=pk)
    feedback.status = 'APPROVED'
    feedback.save()
    return Response({"data": ProductFeedbackSerializer(feedback).data, "message": "Feedback approved successfully"})


@swagger_auto_schema(method='patch', operation_summary="Reject feedback",
    operation_description="Only accessible by admin users.",
    responses={200: ProductFeedbackSerializer, 404: "Not found"})
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def feedback_reject(request, pk):
    feedback = get_object_or_404(ProductFeedback, pk=pk)
    feedback.status = 'REJECTED'
    feedback.save()
    return Response({"data": ProductFeedbackSerializer(feedback).data, "message": "Feedback rejected successfully"})

@swagger_auto_schema(method='delete', operation_summary="Delete feedback (admin)",
    operation_description="Deletes inappropriate feedback. Only accessible by admin users.",
    responses={204: "Deleted successfully", 404: "Not found"})
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def feedback_admin_delete(request, pk):
    feedback = get_object_or_404(ProductFeedback, pk=pk)
    feedback.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)




@swagger_auto_schema(method='post', operation_summary="Submit a product request", 
    operation_description="Logged-in user requests a new product to be added to the store.",
    request_body=ProductRequestCreateSerializer,
    responses={201: ProductRequestSerializer, 400: "Invalid data"})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def product_request_create(request):
    serializer = ProductRequestCreateSerializer(data=request.data)
    if serializer.is_valid():
        product_request = serializer.save(user=request.user)
        return Response({"data": ProductRequestSerializer(product_request).data, "message": "Product request submitted successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='get', operation_summary="List my product requests", 
    responses={200: ProductRequestSerializer(many=True)})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_request_my_list(request):
    requests_qs = ProductRequest.objects.filter(
    user=request.user).order_by("-created_at", "-id")
    serializer = ProductRequestSerializer(requests_qs, many=True)
    return Response({"data": serializer.data, "message": "Your product requests retrieved successfully"})

@swagger_auto_schema(method='get', operation_summary="Get my request detail", 
    responses={200: ProductRequestSerializer, 404: "Not found"})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_request_my_detail(request, pk):
    product_request = get_object_or_404(ProductRequest, pk=pk, user=request.user)
    serializer = ProductRequestSerializer(product_request)
    return Response({"data": serializer.data, "message": "Product request retrieved successfully"})

@swagger_auto_schema(method='delete', operation_summary="Delete my request", 
    operation_description="Only deletable while status is PENDING.",
    responses={204: "Deleted successfully", 400: "No longer deletable", 404: "Not found"})
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def product_request_my_delete(request, pk):
    product_request = get_object_or_404(ProductRequest, pk=pk, user=request.user)
    if product_request.status != ProductRequest.Status.PENDING:
        return Response({"error": "This request is already being processed and can no longer be deleted."}, status=status.HTTP_400_BAD_REQUEST)
    product_request.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(method='get', operation_summary="List all product requests (admin)", 
    operation_description="Only accessible by admin users.",
    manual_parameters=[
        openapi.Parameter('status', openapi.IN_QUERY, description="PENDING, IN_REVIEW, APPROVED, or REJECTED", type=openapi.TYPE_STRING),
    ],
    responses={200: ProductRequestSerializer(many=True)})
@api_view(['GET'])
@permission_classes([IsAdminUser])
def product_request_admin_list(request):
    requests_qs = ProductRequest.objects.all().order_by(
    "-created_at",
    "-id",)
    status_filter = request.GET.get('status')
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    serializer = ProductRequestSerializer(requests_qs, many=True)
    return Response({"data": serializer.data, "message": "Product requests retrieved successfully"})

@swagger_auto_schema(method='get', operation_summary="Get request detail (admin)", 
    responses={200: ProductRequestSerializer, 404: "Not found"})
@api_view(['GET'])
@permission_classes([IsAdminUser])
def product_request_admin_detail(request, pk):
    product_request = get_object_or_404(ProductRequest, pk=pk)
    serializer = ProductRequestSerializer(product_request)
    return Response({"data": serializer.data, "message": "Product request retrieved successfully"})

@swagger_auto_schema(method='patch', operation_summary="Change request status", 
    operation_description="Only accessible by admin users.",
    request_body=ProductRequestStatusSerializer,
    responses={200: ProductRequestSerializer, 400: "Invalid data", 404: "Not found"})
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def product_request_change_status(request, pk):
    product_request = get_object_or_404(ProductRequest, pk=pk)
    serializer = ProductRequestStatusSerializer(data=request.data)
    if serializer.is_valid():
        product_request.status = serializer.validated_data['status']
        product_request.admin_note = serializer.validated_data.get('admin_note', product_request.admin_note)
        product_request.save()
        return Response({"data": ProductRequestSerializer(product_request).data, "message": "Product request status updated successfully"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method="get",
    operation_summary="Get profile overview",
    operation_description=(
        "Returns the authenticated user's profile information, "
        "default address, and activity counts."
    ),
    responses={
        200: ProfileOverviewSerializer,
        401: "Authentication required.",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_overview(request):
    user = (
        request.user.__class__.objects
        .annotate(
            addresses_count=Count("addresses", distinct=True),
            favorites_count=Count("favorites", distinct=True),
            feedbacks_count=Count("product_feedbacks", distinct=True),
            product_requests_count=Count("product_requests", distinct=True),
            orders_count=Count("orders", distinct=True),
        )
        .get(pk=request.user.pk)
    )

    default_address = Address.objects.filter(
        user=request.user,
        is_default=True,
    ).first()

    data = ProfileOverviewSerializer(user).data
    data["default_address"] = (
        AddressSerializer(default_address).data
        if default_address else None
    )

    active_cart = Cart.objects.filter(
        user=request.user,
        status=Cart.Status.ACTIVE,
        expires_at__gt=timezone.now(),
    ).order_by("-created_at").first()

    if active_cart:
        cart_items = active_cart.items.all()
        data["cart"] = {
            "id": active_cart.id,
            "items_count": sum(
                item.quantity for item in cart_items
            ),
        }
    else:
        data["cart"] = None

    recent_orders = Order.objects.filter(
        user=request.user,
    ).order_by("-created_at", "-id")[:5]

    data["recent_orders"] = OrderSerializer(
        recent_orders,
        many=True,
    ).data

    return Response({
        "data": data,
        "message": "Profile overview retrieved successfully.",
    })

