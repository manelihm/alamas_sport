import random

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create many sample users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=500,
            help="Number of sample users to create",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        count = options["count"]

        if count < 1:
            self.stdout.write(
                self.style.ERROR("Count must be at least 1.")
            )
            return

        created = 0
        skipped = 0

        for i in range(count):
            phone = f"0999{i:07d}"
            username = f"test_user_{i + 1}"

            if (
                User.objects.filter(phone_number=phone).exists()
                or User.objects.filter(username=username).exists()
            ):
                skipped += 1
                continue

            user = User(
                phone_number=phone,
                username=username,
                first_name=random.choice(
                    ["Ali", "Sara", "Reza", "Neda", "Amir", "Mina"]
                ),
                last_name=random.choice(
                    ["Ahmadi", "Mohammadi", "Karimi", "Hosseini"]
                ),
                gender=random.choice(["male", "female"]),
                role="user",
                is_phone_verified=True,
                is_active=True,
                status="active",
            )
            user.set_password("Test@12345")
            user.save()
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Created: {created}, Skipped: {skipped}"
            )
        )