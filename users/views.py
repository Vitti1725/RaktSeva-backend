from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import UserSerializer, OTPVerifySerializer, UserListSerializer, ResendOTPSerializer
from .models import User, OTP
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.exceptions import ValidationError
from .utils import generate_otp

class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        generate_otp(user.email)


class VerifyOTPView(generics.GenericAPIView):
    serializer_class = OTPVerifySerializer

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("No user found with this email. Kindly register yourself as a donor or hospital user.")

        if user.is_verified:
            return Response({"message": "User is already verified."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp = OTP.objects.filter(email=email, code=code).latest('created_at')
        except OTP.DoesNotExist:
            return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired():
            return Response({"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_verified = True
        user.save()

        return Response({"message": "OTP verified. You can now login."}, status=status.HTTP_200_OK)

class ResendOTPView(generics.GenericAPIView):
    serializer_class = ResendOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        generate_otp(email)

        return Response({"message": "OTP resent to your email."})

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "email": user.email,
            "name": user.name,
            "is_verified": user.is_verified
        }
        return Response(data)

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsAdminUser]




