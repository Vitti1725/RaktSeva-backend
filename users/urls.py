from django.urls import path
from .views import RegisterView, VerifyOTPView, MeView, UserListView, ResendOTPView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify/', VerifyOTPView.as_view(), name='verify-otp'),
    path('me/', MeView.as_view(), name='user-profile'),
    path('all/', UserListView.as_view(), name='user-list'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
]
