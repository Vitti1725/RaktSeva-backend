from rest_framework import generics, permissions, exceptions
from rest_framework.views import APIView
from .models import Donor, DonorInterest
from .serializers import DonorSerializer, DonorPublicSerializer
from users.permissions import IsDonorUser, IsHospitalOrAdmin, IsActiveDonor
from django_filters.rest_framework import DjangoFilterBackend
from blood_request.serializers import BloodRequestSerializer
from blood_request.models import BloodRequest

class DonorCreateView(generics.CreateAPIView):
    serializer_class = DonorSerializer
    permission_classes = [permissions.IsAuthenticated, IsDonorUser]

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'donor'):
           raise exceptions.PermissionDenied("Donor Profile already exists.")
        serializer.save()


class DonorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = DonorSerializer
    permission_classes = [permissions.IsAuthenticated, IsDonorUser]

    def get_object(self):
        return self.request.user.donor

class DonorListView(generics.ListAPIView):
    queryset = Donor.objects.all().order_by('id')
    serializer_class = DonorPublicSerializer
    permission_classes = [permissions.IsAuthenticated,  IsHospitalOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['blood_group', 'city', 'is_available']

class DonorDetailView(generics.RetrieveAPIView):
    queryset = Donor.objects.all().order_by('id')
    serializer_class = DonorSerializer
    permission_classes = [permissions.IsAuthenticated, IsHospitalOrAdmin]
    lookup_field = 'id'

class MyDonorInterestsView(generics.ListAPIView):
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsActiveDonor]

    def get_queryset(self):
        donor = self.request.user.donor
        request_ids = DonorInterest.objects.filter(
            donor=donor
        ).values_list('blood_request', flat=True)

        return BloodRequest.objects.filter(id__in=request_ids)

