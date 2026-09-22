import random
from django.contrib.auth.hashers import make_password, check_password


def generate_verification_code():
    return str(random.randint(100000, 999999))


def send_sms(phone_number, code):
    # TODO: replace this with a real SMS provider (e.g. Kavenegar) later.
    # For now, we just print it to the console so you can test without a real SMS service.
    print(f"[SMS SIMULATION] Sending code {code} to {phone_number}")


def hash_code(code):
    return make_password(code)


def verify_code(raw_code, hashed_code):
    return check_password(raw_code, hashed_code)