from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

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

    if order.final_amount <= 0:
        raise ValidationError("Free orders do not require payment.")

    if gateway not in Payment.Gateway.values:
        raise ValidationError("Invalid payment gateway.")

    successful_payment = Payment.objects.filter(
        order=order,
        status=Payment.Status.SUCCESS,
    ).exists()

    if successful_payment:
        raise ValidationError("This order has already been paid.")

    pending_payment = Payment.objects.filter(
        order=order,
        status=Payment.Status.PENDING,
    ).first()

    if pending_payment:
        if pending_payment.gateway != gateway:
            raise ValidationError(
                "A pending payment already exists for another gateway."
            )

        return pending_payment

    return Payment.objects.create(
        order=order,
        gateway=gateway,
        amount=order.final_amount,
        status=Payment.Status.PENDING,
    )


@transaction.atomic
def complete_payment(
    payment_id,
    *,
    gateway_verified,
    transaction_id=None,
    tracking_code=None,
    gateway_response=None,
):
    if gateway_verified is not True:
        raise ValidationError(
            "Payment must be verified by the payment gateway."
        )

    payment_order_id = Payment.objects.values_list(
        "order_id",
        flat=True,
    ).get(pk=payment_id)

    order = Order.objects.select_for_update().get(
        pk=payment_order_id,
    )

    payment = Payment.objects.select_for_update().get(
        pk=payment_id,
        order=order,
    )

    if payment.status == Payment.Status.SUCCESS:
        return payment

    if payment.status != Payment.Status.PENDING:
        raise ValidationError("This payment is not pending.")

    if order.status != Order.Status.PENDING:
        raise ValidationError("This order cannot be completed.")

    if payment.amount != order.final_amount:
        raise ValidationError(
            "Payment amount does not match order total."
        )

    another_successful_payment = Payment.objects.filter(
        order=order,
        status=Payment.Status.SUCCESS,
    ).exclude(
        pk=payment.pk,
    ).exists()

    if another_successful_payment:
        raise ValidationError(
            "This order already has a successful payment."
        )

    payment.status = Payment.Status.SUCCESS
    payment.transaction_id = transaction_id
    payment.tracking_code = tracking_code
    payment.gateway_response = gateway_response or {}
    payment.paid_at = timezone.now()

    payment.save(
        update_fields=[
            "status",
            "transaction_id",
            "tracking_code",
            "gateway_response",
            "paid_at",
            "updated_at",
        ]
    )

    complete_paid_order(order.id)

    return payment


@transaction.atomic
def fail_payment(
    payment_id,
    gateway_response=None,
):
    payment_order_id = Payment.objects.values_list(
        "order_id",
        flat=True,
    ).get(pk=payment_id)

    order = Order.objects.select_for_update().get(
        pk=payment_order_id,
    )

    payment = Payment.objects.select_for_update().get(
        pk=payment_id,
        order=order,
    )

    if payment.status == Payment.Status.SUCCESS:
        raise ValidationError(
            "Successful payment cannot be marked as failed."
        )

    if payment.status in [
        Payment.Status.FAILED,
        Payment.Status.EXPIRED,
    ]:
        return payment

    if payment.status != Payment.Status.PENDING:
        raise ValidationError("Invalid payment status.")

    payment.status = Payment.Status.FAILED
    payment.gateway_response = gateway_response or {}

    payment.save(
        update_fields=[
            "status",
            "gateway_response",
            "updated_at",
        ]
    )

    return payment
