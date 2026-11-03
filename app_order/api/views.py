from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from app_order.models import Order
from app_payment.api.serializers import (
    CreatePaymentSerializer,
    PaymentSerializer,
)
from app_payment.models import Payment
from app_payment.services import create_payment


ERROR_RESPONSE = openapi.Response(
    description="Invalid or rejected request."
)


@swagger_auto_schema(
    method="post",
    operation_id="createPayment",
    operation_summary="Create Payment",
    operation_description=(
        "Creates a payment for an order belonging to the authenticated user. "
        "The payment amount is taken from the order's final amount and cannot "
        "be provided or modified by the client. If a pending payment already "
        "exists for the same order and gateway, the existing payment is returned. "
        "Free orders and orders that cannot be paid are rejected."
    ),
    request_body=CreatePaymentSerializer,
    responses={
        200: openapi.Response(
            description="Payment created or an existing pending payment returned.",
            schema=PaymentSerializer,
        ),
        400: ERROR_RESPONSE,
        401: openapi.Response(
            description="Authentication credentials were not provided or are invalid."
        ),
        404: openapi.Response(
            description="Order not found or does not belong to the authenticated user."
        ),
    },
    security=[{"Bearer": []}],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payment_create(request):
    input_serializer = CreatePaymentSerializer(
        data=request.data,
    )
    input_serializer.is_valid(raise_exception=True)

    try:
        payment = create_payment(
            order_id=input_serializer.validated_data["order"],
            user=request.user,
            gateway=input_serializer.validated_data["gateway"],
        )

    except Order.DoesNotExist:
        return Response(
            {"message": "Order not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    except DjangoValidationError as exc:
        return Response(
            {"message": exc.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )

    output_serializer = PaymentSerializer(payment)

    return Response(
        output_serializer.data,
        status=status.HTTP_200_OK,
    )


@swagger_auto_schema(
    method="get",
    operation_id="listPayments",
    operation_summary="List User Payments",
    operation_description=(
        "Returns all payments associated with orders belonging to the "
        "authenticated user. Payments belonging to other users are excluded. "
        "Results are ordered by creation date, newest first."
    ),
    responses={
        200: openapi.Response(
            description="List of the authenticated user's payments.",
            schema=PaymentSerializer(many=True),
        ),
        401: openapi.Response(
            description="Authentication credentials were not provided or are invalid."
        ),
    },
    security=[{"Bearer": []}],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_list(request):
    payments = (
        Payment.objects
        .filter(order__user=request.user)
        .select_related("order")
        .order_by("-created_at")
    )

    serializer = PaymentSerializer(
        payments,
        many=True,
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )


@swagger_auto_schema(
    method="get",
    operation_id="retrievePayment",
    operation_summary="Retrieve Payment Details",
    operation_description=(
        "Retrieves the details of a payment using its UUID. "
        "The payment must belong to an order owned by the authenticated user. "
        "Returns 404 if the payment does not exist or does not belong to the user."
    ),
    manual_parameters=[
        openapi.Parameter(
            name="pk",
            in_=openapi.IN_PATH,
            description="Payment UUID",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
            required=True,
        ),
    ],
    responses={
        200: openapi.Response(
            description="Payment details.",
            schema=PaymentSerializer,
        ),
        401: openapi.Response(
            description="Authentication credentials were not provided or are invalid."
        ),
        404: openapi.Response(
            description="Payment not found or does not belong to the authenticated user."
        ),
    },
    security=[{"Bearer": []}],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_detail(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related("order"),
        pk=pk,
        order__user=request.user,
    )

    serializer = PaymentSerializer(payment)

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )
