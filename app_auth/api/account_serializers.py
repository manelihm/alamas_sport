from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from app_auth.models import User
class MyAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "username",
            "first_name",
            "last_name",
            "gender",
            "image",
            "role",
            "status",
            "is_phone_verified",
            "created_at",
            "last_login_at",
        ]
        read_only_fields = fields
class MyAccountUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "gender",
            "image",
        ]
        extra_kwargs = {
            "username": {
                "required": False,
                "allow_null": True,
                "allow_blank": True,
            },
            "first_name": {
                "required": False,
                "allow_blank": True,
            },
            "last_name": {
                "required": False,
                "allow_blank": True,
            },
            "gender": {
                "required": False,
                "allow_blank": True,
            },
            "image": {
                "required": False,
                "allow_null": True,
            },
        }
class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False,
    )
    def validate_new_password(self, value):
        validate_password(value, user=self.context["request"].user)
        return value
    def validate(self, attrs):
        if attrs["current_password"] == attrs["new_password"]:
            raise serializers.ValidationError({
                "new_password": "The new password must differ from the current password."
            })
        return attrs
class RequestPhoneChangeSerializer(serializers.Serializer):
    new_phone_number = serializers.CharField(max_length=20)
    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    def validate_new_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "This phone number is already in use."
            )
        return value
class VerifyPhoneChangeSerializer(serializers.Serializer):
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        trim_whitespace=False,
    )
class DeactivateAccountSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    confirmation = serializers.BooleanField()
    def validate_confirmation(self, value):
        if value is not True:
            raise serializers.ValidationError(
                "Account deactivation must be explicitly confirmed."
            )
        return value