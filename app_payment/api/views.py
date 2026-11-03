from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from app_payment.api.serializers import (
    CreatePaymentSerializer,
    PaymentSerializer,
)
from app_payment.models import Payment
from app_payment.services import create_payment
from app_order.models import Order
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
    return Response(serializer.data)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_detail(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related("order"),
        pk=pk,
        order__user=request.user,
    )
    serializer = PaymentSerializer(payment)
    return Response(serializer.data)