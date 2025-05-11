from rest_framework import generics, permissions, exceptions
from .models import Hospital
from .serializers import HospitalSerializer
from users.permissions import IsHospitalUser
from django.core.exceptions import ObjectDoesNotExist

class HospitalCreateView(generics.CreateAPIView):
    serializer_class = HospitalSerializer
    permission_classes = [permissions.IsAuthenticated , IsHospitalUser]

    def perform_create(self, serializer):
        try:
            self.request.user.hospital
            raise exceptions.PermissionDenied("Hospital profile already exists.")
        except ObjectDoesNotExist:
            serializer.save()

class HospitalProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = HospitalSerializer
    permission_classes = [permissions.IsAuthenticated, IsHospitalUser]

    def get_object(self):
        return self.request.user.hospital
