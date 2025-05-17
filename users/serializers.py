from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import OTP

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
        User creation schema.

        Fields:
        - id (int, read-only)
        - email (string, required)
        - name (string, required)
        - password (string, write-only, required)
        - role (string, required; one of 'donor', 'hospital')
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'required': True}
            }
        swagger_schema_fields = {'title': 'User'}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class OTPVerifySerializer(serializers.Serializer):
    """
        Schema to verify a one-time code.

        Input:
        - email (string, required)
        - code (string, required; 6 digits)

        Output:
        - message (string)
    """
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)


class UserListSerializer(serializers.ModelSerializer):
    """
        Public user list schema (admin only).

        Fields:
        - id (int, read-only)
        - email (string)
        - name (string)
        - is_verified (bool)
        - is_staff (bool)
        - is_superuser (bool)
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'is_verified', 'is_staff', 'is_superuser']



class ResendOTPSerializer(serializers.Serializer):
    """
        Schema to resend an OTP.

        Input:
        - email (string, required)

        Output:
        - message (string)
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        from .models import User
        try:
            user = User.objects.get(email=value)
            if user.is_verified:
                raise serializers.ValidationError("User is already verified.")
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email.")
        return value
