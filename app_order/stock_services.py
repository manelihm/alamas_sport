from django.db import transaction
from django.db.models import F
from django.utils import timezone

from rest_framework.exceptions import ValidationError



from app_product.models import ProductOption, DiscountCode
from .models import (
    Order,
    StockReservation,
    DiscountCodeReservation,
)

@transaction.atomic
def commit_order_stock(order_id):
    """
    Commit reserved stock after successful payment.
    """

    order = Order.objects.select_for_update().filter(
        id=order_id
    ).first()

    if not order:
        raise ValidationError("Order not found.")

    now = timezone.now()

    reservations = list(
        StockReservation.objects.select_for_update()
        .filter(
            order_item__order=order,
            status=StockReservation.Status.ACTIVE,
            expires_at__gt=now,
        )
        .select_related("product_option")
        .order_by("id")
    )

    if not reservations:
        raise ValidationError(
            "No active stock reservations found."
        )

    for reservation in reservations:
        updated = ProductOption.objects.filter(
            id=reservation.product_option_id,
            stock__gte=reservation.quantity,
            reserved_stock__gte=reservation.quantity,
        ).update(
            stock=F("stock") - reservation.quantity,
            reserved_stock=F("reserved_stock") - reservation.quantity,
        )

        if updated != 1:
            raise ValidationError(
                "Unable to commit reserved stock."
            )

        reservation.status = StockReservation.Status.COMMITTED
        reservation.save(update_fields=["status", "updated_at"])

    return order


@transaction.atomic
def release_order_stock(order_id, expired=False):
    """
    Release stock and discount reservations after
    cancellation, payment failure, or expiration.
    """

    order = Order.objects.select_for_update().filter(
        id=order_id
    ).first()

    if not order:
        raise ValidationError("Order not found.")

    now = timezone.now()

    reservations = list(
        StockReservation.objects.select_for_update()
        .filter(
            order_item__order=order,
            status=StockReservation.Status.ACTIVE,
        )
        .select_related("product_option")
        .order_by("id")
    )

    for reservation in reservations:
        if expired and reservation.expires_at > now:
            continue

        updated = ProductOption.objects.filter(
            id=reservation.product_option_id,
            reserved_stock__gte=reservation.quantity,
        ).update(
            reserved_stock=F("reserved_stock") - reservation.quantity
        )

        if updated != 1:
            raise ValidationError(
                "Unable to release reserved stock."
            )

        reservation.status = (
            StockReservation.Status.EXPIRED
            if expired
            else StockReservation.Status.RELEASED
        )

        reservation.save(
            update_fields=["status", "updated_at"]
        )

    discount_reservations = DiscountCodeReservation.objects.select_for_update().filter(
        order=order,
        status=DiscountCodeReservation.Status.ACTIVE,
    )

    if expired:
        discount_reservations = discount_reservations.filter(
            expires_at__lte=now
        )

    discount_reservations.update(
        status=(
            DiscountCodeReservation.Status.EXPIRED
            if expired
            else DiscountCodeReservation.Status.RELEASED
        ),
        updated_at=now,
    )

    return order

@transaction.atomic
def complete_paid_order(order_id):
    """
    Complete an order after confirmed successful payment.
    Commit stock, consume discount code, and confirm order.
    """

    order = Order.objects.select_for_update().filter(
        id=order_id
    ).first()

    if not order:
        raise ValidationError("Order not found.")

    if order.final_amount <= 0:
        raise ValidationError(
            "Free orders must not use the payment flow."
        )

    if order.status != Order.Status.PENDING:
        raise ValidationError(
            "Order is not awaiting payment."
        )

    # Commit reserved stock.
    commit_order_stock(order.id)

    # Consume discount code if this order used one.
    if order.discount_code_snapshot:
        discount_reservation = (
            DiscountCodeReservation.objects.select_for_update()
            .filter(
                order=order,
                status=DiscountCodeReservation.Status.ACTIVE,
                expires_at__gt=timezone.now(),
            )
            .first()
        )

        if not discount_reservation:
            raise ValidationError(
                "Active discount reservation not found or expired."
            )

        discount_code = DiscountCode.objects.select_for_update().get(
            id=discount_reservation.discount_code_id
        )

        if discount_code.is_used:
            raise ValidationError(
                "Discount code has already been used."
            )

        discount_code.is_used = True
        discount_code.used_by = order.user
        discount_code.used_at = timezone.now()
        discount_code.save(
            update_fields=[
                "is_used",
                "used_by",
                "used_at",
            ]
        )

        discount_reservation.status = (
            DiscountCodeReservation.Status.CONSUMED
        )
        discount_reservation.save(
            update_fields=["status", "updated_at"]
        )

    order.status = Order.Status.CONFIRMED
    order.save(update_fields=["status", "updated_at"])

    return order