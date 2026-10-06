# ============================================================
# app_core/models.py
# ============================================================
from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides created_at and updated_at
    fields for any model that needs timestamp tracking.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at",
    )

    class Meta:
        abstract = True


# ============================================================
# app_core/choices.py
# ============================================================
class ApprovalStatus(models.TextChoices):
    """
    Shared approval statuses for moderated content
    (comments and reviews).
    """

    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


# ============================================================
# app_account/models.py
# ============================================================
from django.conf import settings
from django.db import models

from app_core.models import TimeStampedModel


class Address(TimeStampedModel):
    """
    User addresses. A user can have multiple addresses,
    but only one of them can be the default.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name="User",
    )
    province = models.CharField(
        max_length=100,
        verbose_name="Province",
    )
    city = models.CharField(
        max_length=100,
        verbose_name="City",
        db_index=True,
    )
    address = models.TextField(
        verbose_name="Full address",
    )
    postal_code = models.CharField(
        max_length=20,
        verbose_name="Postal code",
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name="Is default",
    )

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        ordering = ["-is_default", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="unique_default_address_per_user",
            )
        ]
        indexes = [
            models.Index(fields=["user", "is_default"]),
        ]

    def __str__(self) -> str:
        return f"Address #{self.pk} - {self.city}"

    def save(self, *args, **kwargs):
        """
        Ensure that only one default address exists per user.
        """
        if self.is_default:
            Address.objects.filter(
                user=self.user,
                is_default=True,
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# ============================================================
# app_interaction/models.py
# ============================================================
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from app_core.choices import ApprovalStatus
from app_core.models import TimeStampedModel


class Favorite(TimeStampedModel):
    """
    Products favorited by users.
    A user can only favorite a product once.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="User",
    )
    product = models.ForeignKey(
        "app_product.Product",
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Product",
    )

    class Meta:
        verbose_name = "Favorite"
        verbose_name_plural = "Favorites"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_product_favorite",
            )
        ]
        indexes = [
            models.Index(fields=["user", "product"]),
        ]

    def __str__(self) -> str:
        return f"Favorite #{self.pk}"


class Comment(TimeStampedModel):
    """
    User comments on products.
    Comments are displayed after admin approval.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="User",
    )
    product = models.ForeignKey(
        "app_product.Product",
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Product",
    )
    content = models.TextField(
        verbose_name="Content",
    )
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        db_index=True,
        verbose_name="Status",
    )

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "status"]),
        ]

    def __str__(self) -> str:
        return f"Comment #{self.pk}"


class Review(TimeStampedModel):
    """
    User ratings for products (1 to 5).
    A user can only rate a product once.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="User",
    )
    product = models.ForeignKey(
        "app_product.Product",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Product",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
        verbose_name="Rating",
    )
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        db_index=True,
        verbose_name="Status",
    )

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_product_review",
            )
        ]
        indexes = [
            models.Index(fields=["product", "status"]),
        ]

    def __str__(self) -> str:
        return f"Review #{self.pk} - {self.rating}★"


# ============================================================
# app_product/models.py (reference only)
# ============================================================
from django.db import models

from app_core.models import TimeStampedModel


class Product(TimeStampedModel):
    name = models.CharField(max_length=255, verbose_name="Name")
    # ... other fields

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self) -> str:
        return self.name