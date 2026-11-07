import secrets
from django.contrib.auth.hashers import make_password, check_password
def generate_verification_code():
    return f"{secrets.randbelow(900000) + 100000}"
def send_sms(phone_number, code):
    # Replace this simulation with the selected SMS provider.
    print(f"[SMS SIMULATION] Sending code {code} to {phone_number}")
def hash_code(code):
    return make_password(code)
def verify_code(raw_code, hashed_code):
    return check_password(raw_code, hashed_code)

from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)


def revoke_user_refresh_tokens(user):
    outstanding_tokens = OutstandingToken.objects.filter(
        user=user,
    )

    for token in outstanding_tokens:
        BlacklistedToken.objects.get_or_create(
            token=token,
        )