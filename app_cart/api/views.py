from django.db import transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema

from app_cart.models import Cart, CartItem
from app_cart.api.serializers import CartSerializer


from app_cart.api.serializers import AddCartItemSerializer, CartItemSerializer ,UpdateCartItemSerializer ,ApplyDiscountCodeSerializer,CartSummarySerializer
from app_product.models import ProductOption ,DiscountCode
from drf_yasg import openapi
from decimal import Decimal




def get_active_cart(user, lock=False):
    now = timezone.now()

    expired_carts = Cart.objects.filter(
        user=user,
        status=Cart.Status.ACTIVE,
        expires_at__lte=now,
    )

    if lock:
        expired_carts = expired_carts.select_for_update()

    expired_carts.update(status=Cart.Status.EXPIRED)

    carts = Cart.objects.filter(
        user=user,
        status=Cart.Status.ACTIVE,
        expires_at__gt=now,
    ).order_by("-created_at")

    if lock:
        carts = carts.select_for_update()

    cart = carts.first()

    if cart is None:
        cart = Cart.objects.create(user=user)

    return cart


@swagger_auto_schema(
    method="get",
    operation_summary="Get my cart",
    operation_description=(
        "Returns the authenticated user's active cart, including its items. "
        "Creates a new cart if no active cart exists and marks expired carts "
        "as expired."
    ),
    responses={
        200: CartSerializer,
        401: "Authentication credentials were not provided or are invalid.",
    },
    
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cart_detail(request):
    with transaction.atomic():
        cart = get_active_cart(request.user, lock=True)
        serializer = CartSerializer(cart)

    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="post",
    operation_summary="Add item to cart",
    operation_description=(
        "Adds a product option to the authenticated user's active cart. "
        "Validates stock, price type, and minimum wholesale quantity. "
        "The unit price is determined by the server."
    ),
    request_body=AddCartItemSerializer,
    responses={
        201: CartItemSerializer,
        400: "Invalid quantity, insufficient stock, or invalid wholesale quantity.",
        401: "Authentication credentials were not provided or are invalid.",
        404: "Product option not found or inactive.",
    },
    
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_cart_item(request):
    serializer = AddCartItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    option_id = serializer.validated_data["product_option_id"]
    quantity = serializer.validated_data["quantity"]
    price_type = serializer.validated_data["price_type"]

    with transaction.atomic():
        try:
            option = ProductOption.objects.select_for_update().select_related(
                "product",
                "color",
                "size",
                "material",
            ).get(
                pk=option_id,
                is_active=True,
                product__is_active=True,
            )
        except ProductOption.DoesNotExist:
            return Response(
                {"detail": "Product option not found or inactive."},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart = get_active_cart(request.user, lock=True)

        item = CartItem.objects.filter(
            cart=cart,
            product_option=option,
        ).first()

        final_quantity = quantity

        if item:
            if item.price_type != price_type:
                return Response(
                    {
                        "detail": (
                            "This product option already exists in the cart "
                            "with a different price type."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            final_quantity += item.quantity

        if final_quantity > option.stock:
            return Response(
                {"detail": "Requested quantity exceeds available stock."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            price_type == CartItem.PriceType.WHOLESALE
            and final_quantity < option.wholesale_min_quantity
        ):
            return Response(
                {
                    "detail": "Minimum wholesale quantity not met.",
                    "minimum_quantity": option.wholesale_min_quantity,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        unit_price = (
            option.wholesale_price
            if price_type == CartItem.PriceType.WHOLESALE
            else option.retail_price
        )

        snapshot = {
            "product_name": option.product.name,
            "color": option.color.name,
            "size": option.size.name,
            "material": option.material.name,
        }

        if item:
            item.quantity = final_quantity
            item.unit_price = unit_price
            item.snapshot = snapshot
            item.save(
                update_fields=[
                    "quantity",
                    "unit_price",
                    "snapshot",
                    "updated_at",
                ]
            )
        else:
            item = CartItem.objects.create(
                cart=cart,
                product_option=option,
                quantity=quantity,
                price_type=price_type,
                unit_price=unit_price,
                snapshot=snapshot,
            )

    return Response(
        CartItemSerializer(item).data,
        status=status.HTTP_201_CREATED,
    )



@swagger_auto_schema(
    method="patch",
    operation_summary="Update cart item quantity",
    operation_description=(
        "Updates the quantity of an item in the authenticated user's "
        "active cart. Validates stock and minimum wholesale quantity."
    ),
    request_body=UpdateCartItemSerializer,
    responses={
        200: CartItemSerializer,
        400: "Invalid quantity, insufficient stock, or minimum wholesale quantity not met.",
        401: "Authentication credentials were not provided or are invalid.",
        404: "Cart item not found.",
    },
    
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    serializer = UpdateCartItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    quantity = serializer.validated_data["quantity"]

    with transaction.atomic():
        cart = get_active_cart(request.user, lock=True)

        try:
            item = CartItem.objects.select_for_update().select_related(
                "product_option"
            ).get(
                pk=item_id,
                cart=cart,
            )
        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        option = item.product_option

        if option is None or not option.is_active or not option.product.is_active:
            return Response(
                {"detail": "Product option is no longer available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity > option.stock:
            return Response(
                {"detail": "Requested quantity exceeds available stock."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            item.price_type == CartItem.PriceType.WHOLESALE
            and quantity < option.wholesale_min_quantity
        ):
            return Response(
                {
                    "detail": "Minimum wholesale quantity not met.",
                    "minimum_quantity": option.wholesale_min_quantity,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])

    return Response(
        CartItemSerializer(item).data,
        status=status.HTTP_200_OK,
    )


@swagger_auto_schema(
    method="delete",
    operation_summary="Remove item from cart",
    operation_description=(
        "Removes an item from the authenticated user's active cart. "
        "Users can only remove items belonging to their own cart."
    ),
    responses={
        200: openapi.Response(
            description="Cart item removed successfully.",
            examples={
                "application/json": {
                    "detail": "Cart item removed successfully."
                }
            },
        ),
        401: "Authentication credentials were not provided or are invalid.",
        404: "Cart item not found.",
    },
    
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_cart_item(request, item_id):
    with transaction.atomic():
        cart = get_active_cart(request.user, lock=True)

        try:
            item = CartItem.objects.get(
                pk=item_id,
                cart=cart,
            )
        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        item.delete()

    return Response(
        {"detail": "Cart item removed successfully."},
        status=status.HTTP_200_OK,
    )



@swagger_auto_schema(
    method="post",
    operation_summary="Apply discount code",
    operation_description=(
        "Validates a discount code and applies it to the authenticated "
        "user's active cart. The code is not marked as used until checkout."
    ),
    request_body=ApplyDiscountCodeSerializer,
    responses={
        200: openapi.Response(
            description="Discount code applied successfully."
        ),
        400: "Invalid, expired, already used, or ineligible discount code.",
        401: "Authentication credentials were not provided or are invalid.",
        404: "Discount code not found.",
    },
    
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def apply_discount_code(request):
    serializer = ApplyDiscountCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    code = serializer.validated_data["code"].strip()

    with transaction.atomic():
        cart = get_active_cart(request.user, lock=True)

        if not cart.items.exists():
            return Response(
                {"detail": "Cannot apply a discount code to an empty cart."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            discount_code = DiscountCode.objects.select_for_update().get(
                code=code
            )
        except DiscountCode.DoesNotExist:
            return Response(
                {"detail": "Discount code not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        now = timezone.now()

        if discount_code.is_used:
            return Response(
                {"detail": "This discount code has already been used."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (
            discount_code.start_at <= now <= discount_code.end_at
        ):
            return Response(
                {"detail": "This discount code is not currently valid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            discount_code.assigned_to_id is not None
            and discount_code.assigned_to_id != request.user.id
        ):
            return Response(
                {"detail": "This discount code is not assigned to you."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart.discount_code = discount_code
        cart.save(update_fields=["discount_code", "updated_at"])

    return Response(
        {
            "detail": "Discount code applied successfully.",
            "discount_code": discount_code.code,
        },
        status=status.HTTP_200_OK,
    )


@swagger_auto_schema(
    method="delete",
    operation_summary="Remove discount code",
    operation_description=(
        "Removes the applied discount code from the authenticated "
        "user's active cart."
    ),
    responses={
        200: openapi.Response(
            description="Discount code removed successfully."
        ),
        401: "Authentication credentials were not provided or are invalid.",
    },
    
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_discount_code(request):
    with transaction.atomic():
        cart = get_active_cart(request.user, lock=True)

        if cart.discount_code_id is None:
            return Response(
                {"detail": "No discount code is applied to this cart."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart.discount_code = None
        cart.save(update_fields=["discount_code", "updated_at"])

    return Response(
        {"detail": "Discount code removed successfully."},
        status=status.HTTP_200_OK,
    )

@swagger_auto_schema(
    method="get",
    operation_summary="Get cart summary",
    operation_description=(
        "Returns the item count, subtotal, discount amount, "
        "and final total for the authenticated user's active cart."
    ),
    responses={
        200: CartSummarySerializer,
        401: "Authentication credentials were not provided or are invalid.",
    },
    
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cart_summary(request):
    cart = get_active_cart(request.user)

    items = cart.items.all()

    items_count = sum(item.quantity for item in items)
    subtotal = sum(
        (item.unit_price * item.quantity for item in items),
        start=Decimal("0"),
    )

    discount_amount = Decimal("0")
    discount_code = cart.discount_code
    now = timezone.now()

    if (
        discount_code
        and not discount_code.is_used
        and discount_code.start_at <= now <= discount_code.end_at
        and (
            discount_code.assigned_to_id is None
            or discount_code.assigned_to_id == request.user.id
        )
    ):
        if discount_code.type == "percentage":
            discount_amount = (
                subtotal * discount_code.value / Decimal("100")
            )
        elif discount_code.type == "fixed":
            discount_amount = discount_code.value

        discount_amount = min(
            max(discount_amount, Decimal("0")),
            subtotal,
        )

    final_total = subtotal - discount_amount

    data = {
        "items_count": items_count,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "final_total": final_total,
    }

    serializer = CartSummarySerializer(data)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="get",
    operation_summary="Get my cart history",
    operation_description=(
        "Returns the authenticated user's previous carts, "
        "excluding the current active cart."
    ),
    responses={
        200: CartSerializer(many=True),
        401: "Authentication credentials were not provided or are invalid.",
    },
    
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cart_history(request):
    carts = Cart.objects.filter(
        user=request.user,
    ).exclude(
        status=Cart.Status.ACTIVE,
    ).prefetch_related(
        "items",
    ).order_by("-created_at")

    serializer = CartSerializer(carts, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method="get",
    operation_summary="Get cart history detail",
    operation_description=(
        "Returns the details of a specific historical cart "
        "belonging to the authenticated user."
    ),
    responses={
        200: CartSerializer,
        401: "Authentication credentials were not provided or are invalid.",
        404: "Historical cart not found.",
    },

)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cart_history_detail(request, cart_id):
    try:
        cart = Cart.objects.prefetch_related("items").get(
            pk=cart_id,
            user=request.user,
        )
    except Cart.DoesNotExist:
        return Response(
            {"detail": "Historical cart not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if cart.status == Cart.Status.ACTIVE:
        return Response(
            {"detail": "This cart is not part of the purchase history."},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = CartSerializer(cart)
    return Response(serializer.data, status=status.HTTP_200_OK)


