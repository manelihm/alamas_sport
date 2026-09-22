from rest_framework import serializers
from app_auth.models import User


class SendVerificationCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value, is_phone_verified=True).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value

class VerifyCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6)


class RegisterSerializer(serializers.Serializer):
    verification_token = serializers.CharField()
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(help_text="Phone number or username")
    password = serializers.CharField(write_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class SendLoginCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        if not User.objects.filter(phone_number=value, is_phone_verified=True).exists():
            raise serializers.ValidationError("No account found with this phone number.")
        return value


class LoginWithCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6)


class RequestPasswordResetSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        if not User.objects.filter(phone_number=value, is_phone_verified=True).exists():
            raise serializers.ValidationError("No account found with this phone number.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8, write_only=True)

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'username', 'first_name', 'last_name', 'role', 'status', 'created_at']


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'username', 'first_name', 'last_name',
            'gender', 'image', 'role', 'status', 'is_phone_verified',
            'created_at', 'last_login_at'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, write_only=True)

    class Meta:
        model = User
        fields = ['phone_number', 'username', 'password', 'first_name', 'last_name', 'role']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_phone_verified = True
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'gender']


class UserStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=User.STATUS_CHOICES)


class UserRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)