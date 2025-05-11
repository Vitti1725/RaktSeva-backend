from django.urls import path
from .views import HospitalCreateView , HospitalProfileView

urlpatterns = [
    path('create/', HospitalCreateView.as_view(), name='hospital-create'),
    path('me/', HospitalProfileView.as_view(), name='hospital-profile'),
]