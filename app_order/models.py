import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

def generate_order_number():
    return f"ALM-{uuid.uuid4().hex[:16].upper()}"


class ShippingMethod(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )
    estimated_delivery_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Estimated delivery time in days.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["price", "name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="shipping_method_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(estimated_delivery_time__gte=1),
                name="shipping_delivery_time_positive",
            ),
        ]

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"
        RETURNED = "RETURNED", "Returned"

    class OrderType(models.TextChoices):
        RETAIL = "RETAIL", "Retail"
        WHOLESALE = "WHOLESALE", "Wholesale"
        MIXED = "MIXED", "Mixed"

    order_number = models.CharField(
        max_length=20,
        unique=True,
        default=generate_order_number,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    cart = models.OneToOneField(
        "app_cart.Cart",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order",
    )

    order_type = models.CharField(
        max_length=10,
        choices=OrderType.choices,
        default=OrderType.RETAIL,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    shipping_method = models.ForeignKey(
        "app_order.ShippingMethod",
        on_delete=models.PROTECT,
        related_name="orders",
    )

    shipping_method_name_snapshot = models.CharField(max_length=255)

    estimated_delivery_time_snapshot = models.PositiveSmallIntegerField(
    validators=[MinValueValidator(1)],
)
    shipping_address = models.ForeignKey(
        "app_users.Address",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    shipping_address_snapshot = models.JSONField(default=dict)

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )

    discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
    )

    shipping_cost = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )

    final_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )

    discount_code_snapshot = models.CharField(
        max_length=50,
        blank=True,
    )

    tracking_code = models.CharField(max_length=100, blank=True)

    internal_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-created_at", "-id"]

        indexes = [
            models.Index(
                fields=["user", "-created_at"],
                name="order_user_created_idx",
            ),
            models.Index(
                fields=["status", "-created_at"],
                name="order_status_created_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(total_amount__gte=0),
                name="order_total_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(discount_amount__gte=0),
                name="order_discount_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(shipping_cost__gte=0),
                name="order_shipping_cost_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(final_amount__gte=0),
                name="order_final_amount_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(
                    discount_amount__lte=F("total_amount")
                ),
                name="order_discount_not_over_total",
            ),
            models.CheckConstraint(
                condition=Q(
                    final_amount=(
                        F("total_amount")
                        - F("discount_amount")
                        + F("shipping_cost")
                    )
                ),
                name="order_final_amount_consistent",
            ),
        ]

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    class PriceType(models.TextChoices):
        RETAIL = "retail", "Retail"
        WHOLESALE = "wholesale", "Wholesale"

    order = models.ForeignKey(
        "app_order.Order",
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        "app_product.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )

    product_option = models.ForeignKey(
        "app_product.ProductOption",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )

    product_snapshot = models.JSONField(default=dict)

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    price_type = models.CharField(
        max_length=10,
        choices=PriceType.choices,
    )

    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )

    discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
    )

    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=1),
                name="order_item_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="order_item_unit_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(discount_amount__gte=0),
                name="order_item_discount_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(total_price__gte=0),
                name="order_item_total_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.order.order_number} - Item {self.pk}"


class CancellationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    order = models.ForeignKey(
        "app_order.Order",
        on_delete=models.PROTECT,
        related_name="cancellation_requests",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cancellation_requests",
    )
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    admin_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_cancellation_requests",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["status", "-created_at"],
                name="cancel_req_status_created_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["order"],
                condition=models.Q(status="PENDING"),
                name="one_pending_cancel_per_order",
            ),
        ]

    def __str__(self):
        return f"{self.order.order_number} - {self.status}"

    def approve(self, admin_user, note=""):
        self.status = self.Status.APPROVED
        self.reviewed_by = admin_user
        self.admin_note = note
        self.reviewed_at = timezone.now()
        self.save(
            update_fields=[
                "status",
                "reviewed_by",
                "admin_note",
                "reviewed_at",
            ]
        )

    def reject(self, admin_user, note=""):
        self.status = self.Status.REJECTED
        self.reviewed_by = admin_user
        self.admin_note = note
        self.reviewed_at = timezone.now()
        self.save(
            update_fields=[
                "status",
                "reviewed_by",
                "admin_note",
                "reviewed_at",
            ]
        )