from rest_framework.decorators import api_view, permission_classes
from drf_yasg import openapi
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from django.db import models
from app_auth.models import PhoneVerification
from app_auth.api.serializers import SendVerificationCodeSerializer
from app_auth.utils import generate_verification_code, send_sms, hash_code
from django.core import signing
from app_auth.api.serializers import VerifyCodeSerializer , RegisterSerializer , LoginSerializer ,SendLoginCodeSerializer, LoginWithCodeSerializer ,RequestPasswordResetSerializer, ResetPasswordSerializer ,UserListSerializer, UserDetailSerializer, UserCreateSerializer,UserUpdateSerializer, UserStatusSerializer, UserRoleSerializer

from app_auth.utils import verify_code as check_code
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken as RefreshTokenObj
from rest_framework_simplejwt.exceptions import TokenError
from app_auth.api.serializers import LogoutSerializer
from rest_framework.permissions import BasePermission


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)




@swagger_auto_schema(
    method='post',
    operation_summary="Send verification code",
    operation_description="Sends a 6-digit verification code by SMS to the given phone number, for the registration flow. The code expires in 2 minutes.",
    request_body=SendVerificationCodeSerializer,
    responses={200: "Code sent successfully", 400: "Invalid phone number or already registered"}
)
@api_view(['POST'])
def send_verification_code(request):
    serializer = SendVerificationCodeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    phone_number = serializer.validated_data['phone_number']
    code = generate_verification_code()

    PhoneVerification.objects.create(
        phone=phone_number,
        code_hash=hash_code(code),
        purpose='register',
        expires_at=timezone.now() + timedelta(minutes=2),
    )

    send_sms(phone_number, code)

    return Response({"message": "Verification code sent successfully."})



@swagger_auto_schema(
    method='post',
    operation_summary="Verify registration code",
    operation_description="Verifies the 6-digit code sent to the phone number. On success, returns a short-lived verification token needed to complete registration. Fails after 5 incorrect attempts or if the code has expired.",
    request_body=VerifyCodeSerializer,
    responses={200: "Verification token returned", 400: "Invalid or expired code"}
)
@api_view(['POST'])
def verify_registration_code(request):
    serializer = VerifyCodeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    phone_number = serializer.validated_data['phone_number']
    code = serializer.validated_data['code']

    verification = PhoneVerification.objects.filter(
        phone=phone_number, purpose='register'
    ).order_by('-created_at').first()

    if not verification:
        return Response({"error": "No verification code found for this phone number."}, status=status.HTTP_400_BAD_REQUEST)

    if verification.expires_at < timezone.now():
        return Response({"error": "This code has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

    if verification.attempt_count >= 5:
        return Response({"error": "Too many failed attempts. Please request a new code."}, status=status.HTTP_400_BAD_REQUEST)

    if not check_code(code, verification.code_hash):
        verification.attempt_count += 1
        verification.save()
        return Response({"error": "Incorrect code."}, status=status.HTTP_400_BAD_REQUEST)

    verification.delete()

    token = signing.dumps({"phone_number": phone_number, "purpose": "register"})

    return Response({"verification_token": token})


@swagger_auto_schema(
    method='post',
    operation_summary="Register",
    operation_description="Completes registration using the verification token from the previous step, along with a chosen username and password. The verification token expires after 10 minutes.",
    request_body=RegisterSerializer,
    responses={201: "Account created successfully", 400: "Invalid data or expired token"}
)
@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    token = serializer.validated_data['verification_token']

    try:
        data = signing.loads(token, max_age=600)
    except signing.BadSignature:
        return Response({"error": "Invalid or tampered verification token."}, status=status.HTTP_400_BAD_REQUEST)
    except signing.SignatureExpired:
        return Response({"error": "Verification token has expired. Please verify your phone number again."}, status=status.HTTP_400_BAD_REQUEST)

    if data.get('purpose') != 'register':
        return Response({"error": "Invalid token purpose."}, status=status.HTTP_400_BAD_REQUEST)

    phone_number = data['phone_number']

    if User.objects.filter(phone_number=phone_number, is_phone_verified=True).exists():
        return Response({"error": "This phone number is already registered."}, status=status.HTTP_400_BAD_REQUEST)

    password = serializer.validated_data['password']
    try:
        validate_password(password)
    except DjangoValidationError as e:
        return Response({"password": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        phone_number=phone_number,
        password=password,
        username=serializer.validated_data['username'],
        first_name=serializer.validated_data.get('first_name', ''),
        last_name=serializer.validated_data.get('last_name', ''),
        is_phone_verified=True,
    )

    return Response({"message": "Account created successfully."}, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    operation_summary="Login",
    operation_description="Logs in a user using either their phone number or username, along with their password. Returns access and refresh JWT tokens on success.",
    request_body=LoginSerializer,
    responses={200: "Access and refresh tokens returned", 400: "Invalid credentials"}
)
@api_view(['POST'])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    identifier = serializer.validated_data['identifier']
    password = serializer.validated_data['password']

    user = User.objects.filter(phone_number=identifier).first() or User.objects.filter(username=identifier).first()

    if user is None or not user.check_password(password):
        return Response({"error": "Invalid phone number/username or password."}, status=status.HTTP_400_BAD_REQUEST)

    if not user.is_active:
        return Response({"error": "This account is inactive."}, status=status.HTTP_400_BAD_REQUEST)

    user.last_login_at = timezone.now()
    user.save(update_fields=['last_login_at'])

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    })



@swagger_auto_schema(
    method='post',
    operation_summary="Logout",
    operation_description="Logs out the current user by blacklisting their refresh token, so it can no longer be used to get new access tokens. Only accessible by logged-in users.",
    request_body=LogoutSerializer,
    responses={200: "Logged out successfully", 400: "Invalid or already blacklisted token"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    serializer = LogoutSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshTokenObj(serializer.validated_data['refresh'])
        token.blacklist()
    except TokenError:
        return Response({"error": "Invalid or already blacklisted token."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": "Logged out successfully."})


@swagger_auto_schema(
    method='post',
    operation_summary="Send login code",
    operation_description="Sends a 6-digit verification code by SMS for passwordless login. The phone number must already belong to a registered account. The code expires in 2 minutes.",
    request_body=SendLoginCodeSerializer,
    responses={200: "Code sent successfully", 400: "No account found with this phone number"}
)
@api_view(['POST'])
def send_login_code(request):
    serializer = SendLoginCodeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    phone_number = serializer.validated_data['phone_number']
    code = generate_verification_code()

    PhoneVerification.objects.create(
        phone=phone_number,
        code_hash=hash_code(code),
        purpose='passwordless_login',
        expires_at=timezone.now() + timedelta(minutes=2),
    )

    send_sms(phone_number, code)

    return Response({"message": "Login code sent successfully."})


@swagger_auto_schema(
    method='post',
    operation_summary="Login with code",
    operation_description="Logs in a user using their phone number and the verification code sent to it, without a password. Returns access and refresh JWT tokens on success. Fails after 5 incorrect attempts or if the code has expired.",
    request_body=LoginWithCodeSerializer,
    responses={200: "Access and refresh tokens returned", 400: "Invalid or expired code"}
)
@api_view(['POST'])
def login_with_code(request):
    serializer = LoginWithCodeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    phone_number = serializer.validated_data['phone_number']
    code = serializer.validated_data['code']

    verification = PhoneVerification.objects.filter(
        phone=phone_number, purpose='passwordless_login'
    ).order_by('-created_at').first()

    if not verification:
        return Response({"error": "No login code found for this phone number."}, status=status.HTTP_400_BAD_REQUEST)

    if verification.expires_at < timezone.now():
        return Response({"error": "This code has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

    if verification.attempt_count >= 5:
        return Response({"error": "Too many failed attempts. Please request a new code."}, status=status.HTTP_400_BAD_REQUEST)

    if not check_code(code, verification.code_hash):
        verification.attempt_count += 1
        verification.save()
        return Response({"error": "Incorrect code."}, status=status.HTTP_400_BAD_REQUEST)

    verification.delete()

    user = User.objects.filter(phone_number=phone_number, is_phone_verified=True).first()
    if user is None or not user.is_active:
        return Response({"error": "This account is not available."}, status=status.HTTP_400_BAD_REQUEST)

    user.last_login_at = timezone.now()
    user.save(update_fields=['last_login_at'])

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    })


@swagger_auto_schema(
    method='post',
    operation_summary="Request password reset",
    operation_description="Sends a 6-digit verification code by SMS to reset the account password. The phone number must belong to a registered account. The code expires in 2 minutes.",
    request_body=RequestPasswordResetSerializer,
    responses={200: "Code sent successfully", 400: "No account found with this phone number"}
)
@api_view(['POST'])
def request_password_reset(request):
    serializer = RequestPasswordResetSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    phone_number = serializer.validated_data['phone_number']
    code = generate_verification_code()

    PhoneVerification.objects.create(
        phone=phone_number,
        code_hash=hash_code(code),
        purpose='password_reset',
        expires_at=timezone.now() + timedelta(minutes=2),
    )

    send_sms(phone_number, code)

    return Response({"message": "Password reset code sent successfully."})


@swagger_auto_schema(
    method='post',
    operation_summary="Reset password",
    operation_description="Sets a new password using the verification code sent to the phone number. Fails after 5 incorrect attempts or if the code has expired.",
    request_body=ResetPasswordSerializer,
    responses={200: "Password reset successfully", 400: "Invalid or expired code, or invalid password"}
)
@api_view(['POST'])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    phone_number = serializer.validated_data['phone_number']
    code = serializer.validated_data['code']
    new_password = serializer.validated_data['new_password']

    verification = PhoneVerification.objects.filter(
        phone=phone_number, purpose='password_reset'
    ).order_by('-created_at').first()

    if not verification:
        return Response({"error": "No password reset code found for this phone number."}, status=status.HTTP_400_BAD_REQUEST)

    if verification.expires_at < timezone.now():
        return Response({"error": "This code has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

    if verification.attempt_count >= 5:
        return Response({"error": "Too many failed attempts. Please request a new code."}, status=status.HTTP_400_BAD_REQUEST)

    if not check_code(code, verification.code_hash):
        verification.attempt_count += 1
        verification.save()
        return Response({"error": "Incorrect code."}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(phone_number=phone_number, is_phone_verified=True).first()
    if user is None:
        return Response({"error": "This account is not available."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as e:
        return Response({"new_password": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    verification.delete()

    return Response({"message": "Password reset successfully."})


@swagger_auto_schema(
    method='get',
    operation_summary="List all users",
    operation_description="Returns a list of all users, with optional search by phone number or username. Only accessible by super admins.",
    manual_parameters=[
        openapi.Parameter('search', openapi.IN_QUERY, description="Search by phone number or username", type=openapi.TYPE_STRING),
    ],
    responses={200: UserListSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsSuperUser])
def user_list(request):
    users = User.objects.all()
    search = request.GET.get('search')
    if search:
        users = users.filter(
            models.Q(phone_number__icontains=search) | models.Q(username__icontains=search)
        )
    serializer = UserListSerializer(users, many=True)
    return Response({"users": serializer.data})


@swagger_auto_schema(
    method='post',
    operation_summary="Create a new user",
    operation_description="Creates a new user account directly (without phone verification flow). Only accessible by super admins.",
    request_body=UserCreateSerializer,
    responses={201: UserDetailSerializer, 400: "Invalid data"}
)
@api_view(['POST'])
@permission_classes([IsSuperUser])
def user_create(request):
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserDetailSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    operation_summary="Get user detail",
    operation_description="Returns full details of a single user. Only accessible by super admins.",
    responses={200: UserDetailSerializer, 404: "User not found"}
)
@api_view(['GET'])
@permission_classes([IsSuperUser])
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    serializer = UserDetailSerializer(user)
    return Response(serializer.data)


@swagger_auto_schema(
    method='put',
    operation_summary="Update a user",
    operation_description="Updates basic information of a user. Only accessible by super admins.",
    request_body=UserUpdateSerializer,
    responses={200: UserDetailSerializer, 400: "Invalid data", 404: "User not found"}
)
@api_view(['PUT'])
@permission_classes([IsSuperUser])
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    serializer = UserUpdateSerializer(user, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(UserDetailSerializer(user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a user",
    operation_description="Deletes a user account permanently. Only accessible by super admins.",
    responses={204: "User deleted successfully", 404: "User not found"}
)
@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method='patch',
    operation_summary="Change user status",
    operation_description="Sets a user's status to active, inactive, or blocked. Only accessible by super admins.",
    request_body=UserStatusSerializer,
    responses={200: UserDetailSerializer, 400: "Invalid data", 404: "User not found"}
)
@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def user_change_status(request, pk):
    user = get_object_or_404(User, pk=pk)
    serializer = UserStatusSerializer(data=request.data)
    if serializer.is_valid():
        user.status = serializer.validated_data['status']
        user.is_active = (user.status != 'blocked')
        user.save()
        return Response(UserDetailSerializer(user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='patch',
    operation_summary="Change user role",
    operation_description="Changes a user's role between user, admin, and super admin. Only accessible by super admins.",
    request_body=UserRoleSerializer,
    responses={200: UserDetailSerializer, 400: "Invalid data", 404: "User not found"}
)
@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def user_change_role(request, pk):
    user = get_object_or_404(User, pk=pk)
    serializer = UserRoleSerializer(data=request.data)
    if serializer.is_valid():
        role = serializer.validated_data['role']
        user.role = role
        user.is_staff = role in ('admin', 'super_admin')
        user.is_superuser = (role == 'super_admin')
        user.save()
        return Response(UserDetailSerializer(user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
