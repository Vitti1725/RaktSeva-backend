from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
        JWT obtain pair schema.

        Input:
        - email (string, required)
        - password (string, required)

        Output:
        - access (string)
        - refresh (string)
    """
    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.is_superuser and not self.user.is_verified:
            raise AuthenticationFailed("Please verify your email before logging in.")

        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    """
        Obtain JWT access & refresh tokens.

        **POST** `/api/token/`

        Request JSON:
          - email (string, required)
          - password (string, required)

        Responses:
          - 200 OK: `{ access, refresh }`
          - 401 Unauthorized: bad credentials
    """
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
        JWT refresh schema.

        Input:
        - refresh (string, required)

        Output:
        - access (string)
    """
    def validate(self, attrs):
        data = super().validate(attrs)

        # Decode refresh token to get the user ID
        refresh = RefreshToken(attrs['refresh'])
        user_id = refresh['user_id']

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found.")

        # Check is_verified only for non-superusers
        if not user.is_superuser and not user.is_verified:
            raise AuthenticationFailed("Please verify your email before refreshing token.")

        return data


class CustomTokenRefreshView(TokenRefreshView):
    """
        Refresh JWT access token.

        **POST** `/api/token/refresh/`

        Request JSON:
          - refresh (string, required)

        Responses:
          - 200 OK: `{ access }`
          - 401 Unauthorized: invalid or expired refresh token
    """

    serializer_class = CustomTokenRefreshSerializer
