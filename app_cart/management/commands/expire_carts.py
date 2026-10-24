from django.core.management.base import BaseCommand
from django.utils import timezone

from app_cart.models import Cart


class Command(BaseCommand):
    help = "Expire carts whose expiration time has passed."

    def handle(self, *args, **options):
        now = timezone.now()

        expired_count = Cart.objects.filter(
            status=Cart.Status.ACTIVE,
            expires_at__lte=now,
        ).update(
            status=Cart.Status.EXPIRED
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {expired_count} cart(s)."
            )
        )