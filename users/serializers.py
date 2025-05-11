from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import OTP

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'required': True}
            }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'is_verified', 'is_staff', 'is_superuser']


class ResendOTPSerializer(serializers.Serializer):
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
