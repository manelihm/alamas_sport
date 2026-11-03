from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import ValidationError

from app_cart.models import Cart, CartItem
from app_product.models import Discount, DiscountCode, ProductOption
from app_users.models import Address

from .stock_services import commit_order_stock
from .models import (
    Order,
    OrderItem,
    ShippingMethod,
    StockReservation,
    DiscountCodeReservation,
)


ZERO = Decimal("0")


def money(value):
    return Decimal(str(value)).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP,
    )


def calculate_discount(price, discount_type, value):
    price = money(price)
    value = Decimal(str(value))

    if value < ZERO:
        raise ValidationError("Invalid discount value.")

    if discount_type == "percentage":
        if value > 100:
            raise ValidationError("Invalid discount percentage.")

        discount = money(
            price * value / Decimal("100")
        )

    elif discount_type == "fixed":
        discount = money(value)

    else:
        raise ValidationError("Invalid discount type.")

    return min(discount, price)


def get_cart_for_checkout(user, lock=False):
    queryset = Cart.objects

    if lock:
        queryset = queryset.select_for_update()

    cart = queryset.filter(
        user=user,
        status=Cart.Status.ACTIVE,
        expires_at__gt=timezone.now(),
    ).order_by("-created_at").first()

    if not cart:
        raise ValidationError("No active cart found.")

    return cart


def get_checkout_address(user, address_id, lock=False):
    queryset = Address.objects

    if lock:
        queryset = queryset.select_for_update()

    address = queryset.filter(
        id=address_id,
        user=user,
    ).first()

    if not address:
        raise ValidationError("Invalid shipping address.")

    return address


def get_shipping_method(method_id, lock=False):
    queryset = ShippingMethod.objects

    if lock:
        queryset = queryset.select_for_update()

    method = queryset.filter(
        id=method_id,
        is_active=True,
    ).first()

    if not method:
        raise ValidationError("Invalid shipping method.")

    return method


def build_address_snapshot(address):
    return {
        "province": address.province,
        "city": address.city,
        "address": address.address,
        "postal_code": address.postal_code,
    }


def build_product_snapshot(option):
    product = option.product

    return {
        "product_id": product.id,
        "product_name": product.name,
        "brand": product.brand,
        "gender": product.gender,
        "color": option.color.name,
        "size": option.size.name,
        "material": option.material.name,
    }


def get_product_discount(option, unit_price, quantity):
    now = timezone.now()

    discounts = Discount.objects.filter(
        product=option,
        start_at__lte=now,
        end_at__gte=now,
    )

    best_discount = ZERO

    for discount in discounts:
        discount_per_unit = calculate_discount(
            unit_price,
            discount.type,
            discount.value,
        )

        total_discount = min(
            discount_per_unit * quantity,
            unit_price * quantity,
        )

        best_discount = max(
            best_discount,
            total_discount,
        )

    return money(best_discount)


def get_valid_discount_code(code_value, user, lock=False):
    if not code_value:
        return None

    queryset = DiscountCode.objects

    if lock:
        queryset = queryset.select_for_update()

    code = queryset.filter(
        code=code_value.strip(),
    ).first()

    now = timezone.now()

    if not code:
        raise ValidationError("Invalid discount code.")

    if code.is_used:
        raise ValidationError("Discount code has already been used.")

    if code.start_at > now or code.end_at < now:
        raise ValidationError(
            "Discount code is expired or inactive."
        )

    if code.assigned_to_id and code.assigned_to_id != user.id:
        raise ValidationError(
            "This discount code is not assigned to you."
        )
    if lock:
        DiscountCodeReservation.objects.filter(
            discount_code=code,
            status=DiscountCodeReservation.Status.ACTIVE,
            expires_at__lte=now,
        ).update(
            status=DiscountCodeReservation.Status.EXPIRED,
            updated_at=now,
        )

    active_reservation = DiscountCodeReservation.objects.filter(
        discount_code=code,
        status=DiscountCodeReservation.Status.ACTIVE,
        expires_at__gt=now,
    ).exists()

    if active_reservation:
        raise ValidationError(
            "This discount code is reserved for another order."
        )
    return code


def calculate_checkout(
    user,
    shipping_address_id,
    shipping_method_id,
    discount_code="",
    lock=False,
):
    cart = get_cart_for_checkout(user, lock=lock)

    address = get_checkout_address(
        user,
        shipping_address_id,
        lock=lock,
    )

    shipping_method = get_shipping_method(
        shipping_method_id,
        lock=lock,
    )

    # Do not join the nullable product_option relation
    # when using select_for_update.
    items_queryset = cart.items.all().order_by("id")

    if lock:
        items_queryset = items_queryset.select_for_update()

    cart_items = list(items_queryset)

    if not cart_items:
        raise ValidationError("Your cart is empty.")

    option_ids = [
        item.product_option_id
        for item in cart_items
        if item.product_option_id is not None
    ]

    options_queryset = ProductOption.objects.filter(
        id__in=option_ids,
    ).select_related(
        "product",
        "color",
        "size",
        "material",
    )

    if lock:
        options_queryset = options_queryset.select_for_update()

    options_by_id = {
        option.id: option
        for option in options_queryset
    }

    subtotal = ZERO
    product_discount_total = ZERO
    calculated_items = []
    price_types = set()

    for cart_item in cart_items:
        option = options_by_id.get(
            cart_item.product_option_id
        )

        if not option:
            raise ValidationError(
                "A cart product is no longer available."
            )

        if not option.is_active or not option.product.is_active:
            raise ValidationError(
                "A cart product is inactive."
            )

        quantity = cart_item.quantity

        if quantity < 1:
            raise ValidationError("Invalid product quantity.")

        available_stock = option.stock - option.reserved_stock

        if available_stock < quantity:
            raise ValidationError(
                f"Insufficient stock for {option.product.name}."
        )
        if cart_item.price_type == CartItem.PriceType.RETAIL:
            unit_price = money(option.retail_price)

        elif cart_item.price_type == CartItem.PriceType.WHOLESALE:
            if quantity < option.wholesale_min_quantity:
                raise ValidationError(
                    "Minimum wholesale quantity has not been reached."
                )

            unit_price = money(option.wholesale_price)

        else:
            raise ValidationError("Invalid price type.")

        if unit_price < ZERO:
            raise ValidationError("Invalid product price.")

        line_subtotal = money(unit_price * quantity)

        line_discount = get_product_discount(
            option,
            unit_price,
            quantity,
        )

        line_total = money(
            line_subtotal - line_discount
        )

        subtotal += line_subtotal
        product_discount_total += line_discount

        price_types.add(cart_item.price_type)

        calculated_items.append({
            "cart_item": cart_item,
            "option": option,
            "quantity": quantity,
            "price_type": cart_item.price_type,
            "unit_price": unit_price,
            "discount_amount": line_discount,
            "total_price": line_total,
            "product_snapshot": build_product_snapshot(option),
        })

    subtotal = money(subtotal)
    product_discount_total = money(product_discount_total)

    selected_code = (
        discount_code.strip()
        if discount_code and discount_code.strip()
        else (
            cart.discount_code.code
            if cart.discount_code_id
            else ""
        )
    )

    code = get_valid_discount_code(
        selected_code,
        user,
        lock=lock,
    )

    amount_after_product_discounts = money(
        subtotal - product_discount_total
    )

    code_discount = ZERO

    if code:
        code_discount = calculate_discount(
            amount_after_product_discounts,
            code.type,
            code.value,
        )

    total_discount = money(
        product_discount_total + code_discount
    )

    shipping_cost = money(shipping_method.price)

    final_amount = money(
        subtotal - total_discount + shipping_cost
    )

    if len(price_types) == 1:
        order_type = (
            Order.OrderType.RETAIL
            if CartItem.PriceType.RETAIL in price_types
            else Order.OrderType.WHOLESALE
        )
    else:
        order_type = Order.OrderType.MIXED

    return {
        "cart": cart,
        "address": address,
        "shipping_method": shipping_method,
        "items": calculated_items,
        "subtotal": subtotal,
        "product_discount_total": product_discount_total,
        "code_discount": code_discount,
        "total_discount": total_discount,
        "shipping_cost": shipping_cost,
        "final_amount": final_amount,
        "discount_code": code,
        "order_type": order_type,
        "address_snapshot": build_address_snapshot(address),
    }


@transaction.atomic
def create_order(
    user,
    shipping_address_id,
    shipping_method_id,
    discount_code="",
):
    checkout = calculate_checkout(
        user=user,
        shipping_address_id=shipping_address_id,
        shipping_method_id=shipping_method_id,
        discount_code=discount_code,
        lock=True,
    )

    cart = checkout["cart"]

    order = Order.objects.create(
        user=user,
        cart=cart,
        order_type=checkout["order_type"],
        shipping_method=checkout["shipping_method"],
        shipping_method_name_snapshot=checkout["shipping_method"].name,
        estimated_delivery_time_snapshot=(
            checkout["shipping_method"].estimated_delivery_time
        ),
        shipping_address=checkout["address"],
        shipping_address_snapshot=checkout["address_snapshot"],
        total_amount=checkout["subtotal"],
        discount_amount=checkout["total_discount"],
        shipping_cost=checkout["shipping_cost"],
        final_amount=checkout["final_amount"],
        discount_code_snapshot=(
            checkout["discount_code"].code
            if checkout["discount_code"]
            else ""
        ),
    )

    reservation_expiry = timezone.now() + timedelta(hours=24)

    for item in checkout["items"]:
        option = item["option"]
        quantity = item["quantity"]

        updated = ProductOption.objects.filter(
            id=option.id,
            stock__gte=F("reserved_stock") + quantity,
            is_active=True,
            product__is_active=True,
        ).update(
            reserved_stock=F("reserved_stock") + quantity
        )

        if updated != 1:
            raise ValidationError(
                f"Insufficient stock for {option.product.name}."
            )

        order_item = OrderItem.objects.create(
            order=order,
            product=option.product,
            product_option=option,
            product_snapshot=item["product_snapshot"],
            quantity=quantity,
            price_type=item["price_type"],
            unit_price=item["unit_price"],
            discount_amount=item["discount_amount"],
            total_price=item["total_price"],
        )

        StockReservation.objects.create(
            order_item=order_item,
            product_option=option,
            quantity=quantity,
            expires_at=reservation_expiry,
        )
# Complete free orders immediately without payment.
    if order.final_amount == ZERO:
        commit_order_stock(order.id)

        order.status = Order.Status.CONFIRMED
        order.save(update_fields=["status", "updated_at"])

        # Consume the discount code immediately for free orders.
        discount_code_obj = checkout["discount_code"]

        if discount_code_obj:
            discount_code_obj.is_used = True
            discount_code_obj.used_by = user
            discount_code_obj.used_at = timezone.now()
            discount_code_obj.save(
                update_fields=[
                    "is_used",
                    "used_by",
                    "used_at",
                ]
            )

    if (
        order.final_amount > ZERO
        and checkout["discount_code"]
    ):
        DiscountCodeReservation.objects.create(
            order=order,
            discount_code=checkout["discount_code"],
            expires_at=reservation_expiry,
        )
    cart.status = Cart.Status.ORDERED
    cart.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return order