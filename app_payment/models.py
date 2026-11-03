from django.db import models


import uuid

from django.db import models


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    class Gateway(models.TextChoices):
        ZARINPAL = "ZARINPAL", "Zarinpal"
        IDPAY = "IDPAY", "IDPay"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    order = models.ForeignKey(
        "app_order.Order",
        on_delete=models.PROTECT,
        related_name="payments",
    )

    gateway = models.CharField(
        max_length=20,
        choices=Gateway.choices,
        default=Gateway.OTHER,
    )

    amount = models.PositiveBigIntegerField(
        help_text="Payment amount in IRR"
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    authority = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    tracking_code = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    gateway_response = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["order", "status"]),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.status}"

