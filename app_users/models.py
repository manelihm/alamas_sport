from django.db import models


class Address(models.Model):

    user = models.ForeignKey(
        "app_auth.User",
        on_delete=models.CASCADE,
        related_name="addresses"
    )

    province = models.CharField(
        max_length=100
    )

    city = models.CharField(
        max_length=100
    )

    address = models.TextField()

    postal_code = models.CharField(
        max_length=20
    )

    is_default = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.phone_number} - {self.city}"


class Favorite(models.Model):

    user = models.ForeignKey(
        "app_auth.User",
        on_delete=models.CASCADE,
        related_name="favorites"
    )

    product = models.ForeignKey(
        "app_product.Product",
        on_delete=models.CASCADE,
        related_name="favorites"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_product_favorite"
            )
        ]

    def __str__(self):
        return f"{self.user.phone_number} - {self.product}"


class Comment(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    user = models.ForeignKey(
        "app_auth.User",
        on_delete=models.CASCADE,
        related_name="comments"
    )

    product = models.ForeignKey(
        "app_product.Product",
        on_delete=models.CASCADE,
        related_name="comments"
    )

    content = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.phone_number} - Comment"


class Review(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    user = models.ForeignKey(
        "app_auth.User",
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    product = models.ForeignKey(
        "app_product.Product",
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    rating = models.PositiveSmallIntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
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
                fields=["user", "product"],
                name="unique_user_product_review"
            )
        ]

    def __str__(self):
        return f"{self.user.phone_number} - Review"