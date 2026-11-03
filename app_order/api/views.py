from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from drf_yasg.utils import swagger_auto_schema
from app_order.stock_services import release_order_stock
from app_order.models import Order, CancellationRequest
from app_order.api.serializers import (
    Order,
    OrderSerializer,
    CheckoutRequestSerializer,
    CancellationRequestCreateSerializer,
    CancellationRequestSerializer,
    ShippingMethodSerializer,
)
from app_order.services import calculate_checkout, create_order



@swagger_auto_schema(
    method='post',
    operation_summary="Preview checkout",
    operation_description="Calculates checkout totals without creating an order.",
    request_body=CheckoutRequestSerializer,
    responses={200: "Checkout preview"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_preview(request):
    serializer = CheckoutRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    checkout = calculate_checkout(
        user=request.user,
        **serializer.validated_data
    )

    data = {
        "subtotal": checkout["subtotal"],
        "product_discount": checkout["product_discount_total"],
        "code_discount": checkout["code_discount"],
        "total_discount": checkout["total_discount"],
        "shipping_cost": checkout["shipping_cost"],
        "final_amount": checkout["final_amount"],
        "order_type": checkout["order_type"],
        "items": [
            {
                "product": item["product_snapshot"],
                "quantity": item["quantity"],
                "price_type": item["price_type"],
                "unit_price": item["unit_price"],
                "discount_amount": item["discount_amount"],
                "total_price": item["total_price"],
            }
            for item in checkout["items"]
        ],
    }

    return Response({
        "data": data,
        "message": "Checkout preview calculated successfully"
    }, status=status.HTTP_200_OK)



@swagger_auto_schema(
    method='post',
    operation_summary="Create order",
    operation_description="Creates an order from the authenticated user's active cart.",
    request_body=CheckoutRequestSerializer,
    responses={
        201: OrderSerializer,
        400: "Invalid checkout data",
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):
    serializer = CheckoutRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    order = create_order(
        user=request.user,
        **serializer.validated_data
    )

    order_serializer = OrderSerializer(order)

    return Response({
        "data": order_serializer.data,
        "message": "Order created successfully"
    }, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='get',
    operation_summary="List user orders",
    operation_description="Returns all orders belonging to the authenticated user.",
    responses={200: OrderSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list(request):
    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related(
        "items"
    ).order_by(
        "-created_at",
        "-id"
    )

    serializer = OrderSerializer(orders, many=True)

    return Response({
        "data": serializer.data,
        "message": "Orders retrieved successfully"
    }, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_summary="Retrieve order details",
    operation_description="Returns details of a specific order belonging to the authenticated user.",
    responses={
        200: OrderSerializer,
        404: "Order not found"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        pk=pk,
        user=request.user
    )

    serializer = OrderSerializer(order)

    return Response({
        "data": serializer.data,
        "message": "Order details retrieved successfully"
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    operation_summary="Create cancellation request",
    operation_description="Creates a cancellation request for an order belonging to the authenticated user.",
    request_body=CancellationRequestCreateSerializer,
    responses={
        201: CancellationRequestSerializer,
        400: "Invalid cancellation request"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancellation_create(request):
    serializer = CancellationRequestCreateSerializer(
        data=request.data,
        context={"request": request}
    )
    serializer.is_valid(raise_exception=True)

    order_id = serializer.validated_data["order"].id

    try:
        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update(),
                id=order_id,
                user=request.user
            )

            allowed_statuses = [
                Order.Status.PENDING,
                Order.Status.CONFIRMED,
                Order.Status.IN_PROGRESS,
            ]

            if order.status not in allowed_statuses:
                return Response({
                    "data": None,
                    "message": "Cancellation is not allowed for this order."
                }, status=status.HTTP_400_BAD_REQUEST)

            if order.cancellation_requests.filter(
                status=CancellationRequest.Status.PENDING
            ).exists():
                return Response({
                    "data": None,
                    "message": "A pending cancellation request already exists."
                }, status=status.HTTP_400_BAD_REQUEST)

            cancellation_request = CancellationRequest.objects.create(
                order=order,
                user=request.user,
                reason=serializer.validated_data["reason"]
            )

    except IntegrityError:
        return Response({
            "data": None,
            "message": "A pending cancellation request already exists."
        }, status=status.HTTP_400_BAD_REQUEST)

    response_serializer = CancellationRequestSerializer(
        cancellation_request
    )

    return Response({
        "data": response_serializer.data,
        "message": "Cancellation request created successfully"
    }, status=status.HTTP_201_CREATED)



@swagger_auto_schema(
    method='get',
    operation_summary="List cancellation requests",
    operation_description="Returns all cancellation requests belonging to the authenticated user.",
    responses={200: CancellationRequestSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cancellation_list(request):
    cancellation_requests = CancellationRequest.objects.filter(
        user=request.user
    ).select_related(
        "order"
    ).order_by(
        "-created_at",
        "-id"
    )

    serializer = CancellationRequestSerializer(
        cancellation_requests,
        many=True
    )

    return Response({
        "data": serializer.data,
        "message": "Cancellation requests retrieved successfully"
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_summary="Retrieve cancellation request details",
    operation_description="Returns details of a cancellation request belonging to the authenticated user.",
    responses={
        200: CancellationRequestSerializer,
        404: "Cancellation request not found"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cancellation_detail(request, pk):
    cancellation_request = get_object_or_404(
        CancellationRequest.objects.select_related("order"),
        pk=pk,
        user=request.user
    )

    serializer = CancellationRequestSerializer(
        cancellation_request
    )

    return Response({
        "data": serializer.data,
        "message": "Cancellation request details retrieved successfully"
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_summary="List active shipping methods",
    operation_description="Returns all active shipping methods.",
    responses={200: ShippingMethodSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shipping_method_list(request):
    shipping_methods = ShippingMethod.objects.filter(
        is_active=True
    ).order_by(
        "price",
        "name"
    )

    serializer = ShippingMethodSerializer(
        shipping_methods,
        many=True
    )

    return Response({
        "data": serializer.data,
        "message": "Shipping methods retrieved successfully"
    }, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_summary="Retrieve shipping method details",
    operation_description="Returns details of an active shipping method.",
    responses={
        200: ShippingMethodSerializer,
        404: "Shipping method not found"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shipping_method_detail(request, pk):
    shipping_method = get_object_or_404(
        ShippingMethod,
        pk=pk,
        is_active=True
    )

    serializer = ShippingMethodSerializer(shipping_method)

    return Response({
        "data": serializer.data,
        "message": "Shipping method retrieved successfully"
    }, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method="post",
    operation_summary="Approve cancellation request",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancellation_approve(request, pk):
    if not request.user.is_staff:
        return Response(
            {"message": "Admin access required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    with transaction.atomic():
        cancellation_request = get_object_or_404(
            CancellationRequest.objects.select_for_update(),
            pk=pk,
        )

        if cancellation_request.status != CancellationRequest.Status.PENDING:
            return Response(
                {"message": "This request has already been reviewed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = Order.objects.select_for_update().get(
            pk=cancellation_request.order_id
        )

        if order.status not in [
            Order.Status.PENDING,
            Order.Status.CONFIRMED,
            Order.Status.IN_PROGRESS,
        ]:
            return Response(
                {"message": "Order cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        release_order_stock(order.id)

        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])

        cancellation_request.approve(
            reviewer=request.user,
            note=request.data.get("admin_note", ""),
        )

    return Response({
        "message": "Cancellation approved successfully."
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="post",
    operation_summary="Reject cancellation request",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancellation_reject(request, pk):
    if not request.user.is_staff:
        return Response(
            {"message": "Admin access required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    with transaction.atomic():
        cancellation_request = get_object_or_404(
            CancellationRequest.objects.select_for_update(),
            pk=pk,
        )

        if cancellation_request.status != CancellationRequest.Status.PENDING:
            return Response(
                {"message": "This request has already been reviewed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cancellation_request.reject(
            reviewer=request.user,
            note=request.data.get("admin_note", ""),
        )

    return Response({
        "message": "Cancellation rejected successfully."
    }, status=status.HTTP_200_OK)