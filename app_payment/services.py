from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from app_order.models import Order
from app_order.stock_services import complete_paid_order
from app_payment.models import Payment
@transaction.atomic
def create_payment(order_id, user, gateway=Payment.Gateway.OTHER):
    order = Order.objects.select_for_update().get(
        pk=order_id,
        user=user,
    )
    if order.status != Order.Status.PENDING:
        raise ValidationError("This order cannot be paid.")
    if order.total_price <= 0:
        raise ValidationError("Free orders do not require payment.")
    successful_payment = Payment.objects.filter(
        order=order,
        status=Payment.Status.SUCCESS,
    ).exists()
    if successful_payment:
        raise ValidationError("This order has already been paid.")
    payment = Payment.objects.create(
        order=order,
        gateway=gateway,
        amount=order.total_price,
        status=Payment.Status.PENDING,
    )
    return payment
@transaction.atomic
def complete_payment(
    payment_id,
    transaction_id=None,
    tracking_code=None,
    gateway_response=None,
):
    payment = Payment.objects.select_for_update().get(
        pk=payment_id,
    )
    if payment.status == Payment.Status.SUCCESS:
        return payment
    if payment.status != Payment.Status.PENDING:
        raise ValidationError("This payment is not pending.")
    order = Order.objects.select_for_update().get(
        pk=payment.order_id,
    )
    if order.status != Order.Status.PENDING:
        raise ValidationError("This order cannot be completed.")
    if payment.amount != order.total_price:
        raise ValidationError("Payment amount does not match order total.")
    payment.status = Payment.Status.SUCCESS
    payment.transaction_id = transaction_id
    payment.tracking_code = tracking_code
    payment.gateway_response = gateway_response or {}
    payment.paid_at = timezone.now()
    payment.save()
    complete_paid_order(order.id)
    return payment
@transaction.atomic
def fail_payment(
    payment_id,
    gateway_response=None,
):
    payment = Payment.objects.select_for_update().get(
        pk=payment_id,
    )
    if payment.status == Payment.Status.SUCCESS:
        raise ValidationError("Successful payment cannot be marked as failed.")
    if payment.status == Payment.Status.FAILED:
        return payment
    payment.status = Payment.Status.FAILED
    payment.gateway_response = gateway_response or {}
    payment.save(update_fields=[
        "status",
        "gateway_response",
        "updated_at",
    ])
    return payment