from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from app_payment.models import Payment
from app_payment.api.serializers import PaymentSerializer
from app_payment.services import create_payment
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payment_create(request):
    order_id = request.data.get("order")
    gateway = request.data.get(
        "gateway",
        Payment.Gateway.OTHER,
    )
    if not order_id:
        return Response(
            {"message": "Order ID is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if gateway not in Payment.Gateway.values:
        return Response(
            {"message": "Invalid payment gateway."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        payment = create_payment(
            order_id=order_id,
            user=request.user,
            gateway=gateway,
        )
    except Payment.DoesNotExist:
        return Response(
            {"message": "Order not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except DjangoValidationError as exc:
        return Response(
            {"message": exc.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(
        PaymentSerializer(payment).data,
        status=status.HTTP_201_CREATED,
    )
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_list(request):
    payments = Payment.objects.filter(
        order__user=request.user
    ).select_related("order")
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
    return Response(
        PaymentSerializer(payment).data
    )