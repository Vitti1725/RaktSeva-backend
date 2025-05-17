# coding=utf-8
from rest_framework import generics, permissions, exceptions
from rest_framework.views import APIView
from .models import Donor, DonorInterest
from .serializers import DonorSerializer, DonorPublicSerializer
from users.permissions import IsDonorUser, IsHospitalOrAdmin, IsActiveDonor
from django_filters.rest_framework import DjangoFilterBackend
from blood_request.serializers import BloodRequestSerializer
from blood_request.models import BloodRequest

class DonorCreateView(generics.CreateAPIView):
    """
        Create the authenticated donor’s profile.

        **POST** `/api/donors/create/`

        Headers:
          - Authorization: Bearer `<access_token>`

        Request JSON:
          - blood_group (string, required)
          - city (string, required)
          - contact_number (string, required)
          - is_available (boolean, required)

        Responses:
          - 201 Created: donor profile data
          - 403 Forbidden: profile exists or wrong role
        """
    serializer_class = DonorSerializer
    permission_classes = [permissions.IsAuthenticated, IsDonorUser]

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'donor'):
           raise exceptions.PermissionDenied("Donor Profile already exists.")
        serializer.save()


class DonorProfileView(generics.RetrieveUpdateAPIView):
    """
        Retrieve or update your donor profile.

        **GET**  `/api/donors/me/`
        **PATCH**`/api/donors/me/`

        Headers:
          - Authorization: Bearer `<access_token>`

        PATCH JSON (any of):
          - blood_group, city, contact_number, is_available

        Responses:
          - 200 OK: profile data
          - 403 Forbidden: wrong role
    """
    serializer_class = DonorSerializer
    permission_classes = [permissions.IsAuthenticated, IsDonorUser]

    def get_object(self):
        return self.request.user.donor

class DonorListView(generics.ListAPIView):
    """
        List all available donors (hospital-only).

        **GET** `/api/donors/`

        Headers:
          - Authorization: Bearer `<access_token>`

        Optional query params:
          - blood_group, city, is_available

        Responses:
          - 200 OK: paginated list of donors
          - 403 Forbidden: non-hospital access
    """
    queryset = Donor.objects.all().order_by('id')
    serializer_class = DonorPublicSerializer
    permission_classes = [permissions.IsAuthenticated,  IsHospitalOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['blood_group', 'city', 'is_available']

class DonorDetailView(generics.RetrieveAPIView):
    """
        Retrieve a specific donor’s profile.

        **GET** `/api/donors/{id}/`

        Headers:
          - Authorization: Bearer `<access_token>`

        Responses:
          - 200 OK: donor data
          - 403/404: forbidden or not found
    """
    queryset = Donor.objects.all().order_by('id')
    serializer_class = DonorSerializer
    permission_classes = [permissions.IsAuthenticated, IsHospitalOrAdmin]
    lookup_field = 'id'

class MyDonorInterestsView(generics.ListAPIView):
    """
       List blood requests you’ve expressed interest in.

       **GET** `/api/donors/interests/my/`

       Headers:
         - Authorization: Bearer `<access_token>`

       Responses:
         - 200 OK: list of BloodRequest objects
         - 403/401: wrong role or unauthenticated
    """
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsActiveDonor]

    def get_queryset(self):
        donor = self.request.user.donor
        request_ids = DonorInterest.objects.filter(
            donor=donor
        ).values_list('blood_request', flat=True)

        return BloodRequest.objects.filter(id__in=request_ids)

