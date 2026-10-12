from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
def get_cart_expiration():
    return timezone.now() + timedelta(hours=24)
class Cart(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ORDERED = "ORDERED", "Ordered"
        EXPIRED = "EXPIRED", "Expired"
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carts"
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    discount_code = models.ForeignKey(
        "app_product.DiscountCode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carts"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    expires_at = models.DateTimeField(
        default=get_cart_expiration
    )
    def __str__(self):
        return f"Cart #{self.pk} - {self.user}"
class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product_option = models.ForeignKey(
        "app_product.ProductOption",
        on_delete=models.CASCADE,
        related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(
        default=1
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product_option"],
                name="unique_cart_item"
            )
        ]
    def __str__(self):
        return f"{self.product_option} x{self.quantity}"