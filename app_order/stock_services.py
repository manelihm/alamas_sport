from django.db import transaction
from django.db.models import F
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from app_product.models import ProductOption

from .models import Order, StockReservation


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
    Release active stock reservations after payment failure,
    cancellation of an unpaid order, or expiration.
    """

    order = Order.objects.select_for_update().filter(
        id=order_id
    ).first()

    if not order:
        raise ValidationError("Order not found.")

    reservations = list(
        StockReservation.objects.select_for_update()
        .filter(
            order_item__order=order,
            status=StockReservation.Status.ACTIVE,
        )
        .select_related("product_option")
        .order_by("id")
    )

    if not reservations:
        return order

    now = timezone.now()

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

        reservation.save(update_fields=["status", "updated_at"])

    return order