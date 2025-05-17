# coding=utf-8
from rest_framework import generics, permissions, exceptions
from .models import Hospital
from .serializers import HospitalSerializer
from users.permissions import IsHospitalUser
from django.core.exceptions import ObjectDoesNotExist

class HospitalCreateView(generics.CreateAPIView):
    """
        Create the authenticated hospital’s profile.

        **POST** `/api/hospitals/create/`

        Headers:
          - Authorization: Bearer `<access_token>`

        Request JSON:
          - name (string, required)
          - city (string, required)
          - address (string, required)
          - contact_number (string, required)
          - registration_number (string, required)

        Responses:
          - 201 Created: hospital profile data
          - 403 Forbidden: profile exists or wrong role
    """
    serializer_class = HospitalSerializer
    permission_classes = [permissions.IsAuthenticated , IsHospitalUser]

    def perform_create(self, serializer):
        try:
            self.request.user.hospital
            raise exceptions.PermissionDenied("Hospital profile already exists.")
        except ObjectDoesNotExist:
            serializer.save()

class HospitalProfileView(generics.RetrieveUpdateAPIView):
    """
        View or update your hospital profile.

        **GET**  `/api/hospitals/me/`
        **PATCH**`/api/hospitals/me/`

        Headers:
          - Authorization: Bearer `<access_token>`

        PATCH JSON (any of):
          - name, city, address, contact_number, registration_number

        Responses:
          - 200 OK: profile data
          - 403 Forbidden: wrong role
    """
    serializer_class = HospitalSerializer
    permission_classes = [permissions.IsAuthenticated, IsHospitalUser]

    def get_object(self):
        return self.request.user.hospital
