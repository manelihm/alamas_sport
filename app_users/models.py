
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Address(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses"
    )
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()
    postal_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="unique_default_address"
            )
        ]

    def __str__(self):
        return f"{self.city} - {self.user}"


class Favorite(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites"
    )
    product = models.ForeignKey(
        "app_product.Product",
        on_delete=models.CASCADE,
        related_name="favorites"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_favorite"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.product}"


class ProductFeedback(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "در انتظار بررسی"
        APPROVED = "APPROVED", "تأیید شده"
        REJECTED = "REJECTED", "رد شده"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_feedbacks"
    )
    product = models.ForeignKey(
        "app_product.Product",
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )
    content = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_product_feedback"
            ),
            models.CheckConstraint(
             condition=(
                    ~models.Q(content="")
                    | models.Q(rating__isnull=False)
                ),
                name="feedback_content_or_rating_required"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.product}"


class ProductRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "در انتظار"
        IN_REVIEW = "IN_REVIEW", "در حال بررسی"
        APPROVED = "APPROVED", "تایید شده"
        REJECTED = "REJECTED", "رد شده"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_requests"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    admin_note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - {self.user}"