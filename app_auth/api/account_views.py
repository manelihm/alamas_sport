from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes,
)
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app_auth.models import User, PhoneVerification
from app_auth.utils import generate_verification_code, hash_code, send_sms
from app_auth.utils import verify_code as check_code

from app_auth.api.account_serializers import (
    MyAccountSerializer,
    MyAccountUpdateSerializer,
    ChangePasswordSerializer,
    RequestPhoneChangeSerializer,
    VerifyPhoneChangeSerializer,
    DeactivateAccountSerializer,
)


@swagger_auto_schema(
    method="get",
    operation_id="getMyAccount",
    operation_summary="Get My Account",
    operation_description=(
        "Returns the authenticated user's account information."
    ),
    responses={
        200: MyAccountSerializer,
        401: "Authentication required.",
    },
    security=[{"Bearer": []}],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_account(request):
    serializer = MyAccountSerializer(request.user)

    return Response({
        "data": serializer.data,
        "message": "Account information retrieved successfully.",
    })


@swagger_auto_schema(
    method="patch",
    operation_id="updateMyAccount",
    operation_summary="Update My Account",
    operation_description=(
        "Updates the authenticated user's username, first name, last name, "
        "gender, or profile image. Phone number, role, status, and verification "
        "fields cannot be modified through this endpoint. Use multipart/form-data "
        "when uploading an image."
    ),
    request_body=MyAccountUpdateSerializer,
    responses={
        200: MyAccountSerializer,
        400: "Invalid account information.",
        401: "Authentication required.",
    },
    security=[{"Bearer": []}],
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def update_my_account(request):
    serializer = MyAccountUpdateSerializer(
        request.user,
        data=request.data,
        partial=True,
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({
        "data": MyAccountSerializer(request.user).data,
        "message": "Account information updated successfully.",
    })


@swagger_auto_schema(
    method="post",
    operation_id="changeMyPassword",
    operation_summary="Change My Password",
    operation_description=(
        "Changes the authenticated user's password after validating "
        "the current password and applying Django password validators."
    ),
    request_body=ChangePasswordSerializer,
    responses={
        200: "Password changed successfully.",
        400: "Invalid current or new password.",
        401: "Authentication required.",
    },
    security=[{"Bearer": []}],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_my_password(request):
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)

    user = request.user

    if not user.check_password(
        serializer.validated_data["current_password"]
    ):
        return Response(
            {"current_password": ["Current password is incorrect."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(serializer.validated_data["new_password"])
    user.save(update_fields=["password"])

    return Response({
        "message": "Password changed successfully.",
    })


@swagger_auto_schema(
    method="post",
    operation_id="requestPhoneChange",
    operation_summary="Request Phone Number Change",
    operation_description=(
        "Requests a phone number change. The current password is required. "
        "A verification code is sent to the new phone number. The code expires "
        "after two minutes and allows up to five attempts."
    ),
    request_body=RequestPhoneChangeSerializer,
    responses={
        200: "Verification code sent.",
        400: "Invalid password or phone number.",
        401: "Authentication required.",
    },
    security=[{"Bearer": []}],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_phone_change(request):
    serializer = RequestPhoneChangeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user

    if not user.check_password(
        serializer.validated_data["current_password"]
    ):
        return Response(
            {"current_password": ["Current password is incorrect."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    new_phone = serializer.validated_data["new_phone_number"]

    if new_phone == user.phone_number:
        return Response(
            {"new_phone_number": ["This is already your current phone number."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    code = generate_verification_code()

    PhoneVerification.objects.filter(
    user=user,
    purpose="phone_change",
    ).delete()

    PhoneVerification.objects.create(
    user=user,
    phone=new_phone,
    code_hash=hash_code(code),
    purpose="phone_change",
    expires_at=timezone.now() + timedelta(minutes=2),
    )

    send_sms(new_phone, code)

    return Response({
        "message": "Phone verification code sent successfully.",
    })


@swagger_auto_schema(
    method="post",
    operation_id="verifyPhoneChange",
    operation_summary="Verify Phone Number Change",
    operation_description=(
        "Verifies the code sent to the new phone number and updates "
        "the authenticated user's phone number. The new number must "
        "not belong to another account."
    ),
    request_body=VerifyPhoneChangeSerializer,
    responses={
        200: "Phone number updated successfully.",
        400: "Invalid, expired, or already used verification code.",
        401: "Authentication required.",
    },
    security=[{"Bearer": []}],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def verify_phone_change(request):
    serializer = VerifyPhoneChangeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    verification = (
        PhoneVerification.objects
        .select_for_update()
        .filter(
        user=request.user,
        purpose="phone_change",
    )
        .order_by("-created_at")
        .first()
    )

    if not verification:
        return Response(
            {"message": "No phone change verification request found."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if verification.expires_at <= timezone.now():
        verification.delete()
        return Response(
            {"message": "Verification code has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if verification.attempt_count >= 5:
        verification.delete()
        return Response(
            {"message": "Maximum verification attempts exceeded."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not check_code(
        serializer.validated_data["code"],
        verification.code_hash,
    ):
        verification.attempt_count += 1
        verification.save(update_fields=["attempt_count"])

        return Response(
            {"message": "Incorrect verification code."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.select_for_update().get(pk=request.user.pk)

    if User.objects.filter(
        phone_number=verification.phone
    ).exclude(pk=user.pk).exists():
        verification.delete()
        return Response(
            {"message": "This phone number is already in use."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.phone_number = verification.phone
    user.is_phone_verified = True
    user.save(update_fields=["phone_number", "is_phone_verified"])

    verification.delete()

    return Response({
        "message": "Phone number updated successfully.",
        "phone_number": user.phone_number,
        "is_phone_verified": user.is_phone_verified,
    })


@swagger_auto_schema(
    method="post",
    operation_id="deactivateMyAccount",
    operation_summary="Deactivate My Account",
    operation_description=(
        "Deactivates the authenticated user's account after password "
        "verification and explicit confirmation. The user record is retained "
        "to preserve order and payment history. This operation does not "
        "permanently delete personal data."
    ),
    request_body=DeactivateAccountSerializer,
    responses={
        200: "Account deactivated successfully.",
        400: "Invalid password or missing confirmation.",
        401: "Authentication required.",
    },
    security=[{"Bearer": []}],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def deactivate_my_account(request):
    serializer = DeactivateAccountSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user

    if not user.check_password(
        serializer.validated_data["current_password"]
    ):
        return Response(
            {"current_password": ["Current password is incorrect."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.status = "inactive"
    user.is_active = False
    user.save(update_fields=["status", "is_active"])

    return Response({
        "message": "Account deactivated successfully.",
    })