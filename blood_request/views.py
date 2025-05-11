from rest_framework import generics, permissions
from .models import BloodRequest
from donor.models import Donor, DonorInterest
from donor.serializers import DonorPublicSerializer
from .serializers import BloodRequestSerializer, NotifyDonorSerializer
from users.permissions import IsActiveDonor, IsActiveHospital
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from .utils import get_hospital_owned_request, calculate_distance
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from django.core.mail import send_mail


class BloodRequestCreateView(generics.CreateAPIView):
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsActiveHospital]

    def perform_create(self, serializer):
        serializer.save(hospital=self.request.user.hospital)

class BloodRequestListView(generics.ListAPIView):
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsActiveHospital]

    def get_queryset(self):
        return BloodRequest.objects.filter(hospital=self.request.user.hospital).order_by('id')

class AvailableBloodRequestsView(generics.ListAPIView):
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsActiveDonor]

    def get_queryset(self):
        donor = self.request.user.donor
        now = timezone.now()
        expiry_time = now - timedelta(hours=48)

        return BloodRequest.objects.filter(
            blood_group=donor.blood_group,
            city=donor.city,
            is_fulfilled=False,
            created_at__gte=expiry_time
        ).order_by('-created_at')

class FulfillBloodRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveHospital]

    def patch(self, request, pk):
        blood_request, error = get_hospital_owned_request(pk, request.user.hospital)
        if error:
            return error

        if blood_request.is_fulfilled:
            return Response({"message": "Request already fulfilled."}, status=status.HTTP_400_BAD_REQUEST)

        blood_request.is_fulfilled = True
        blood_request.save()
        return Response({"message": "Request marked as fulfilled."})


class ExtendBloodRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveHospital]

    def patch(self, request, pk):
        blood_request, error = get_hospital_owned_request(pk, request.user.hospital)
        if error:
            return error

        if blood_request.is_fulfilled:
            return Response({"message": "Cannot extend a fulfilled request."}, status=status.HTTP_400_BAD_REQUEST)

        blood_request.created_at = timezone.now()
        blood_request.save()
        return Response({"message": "Request extended by 48 hours."})

class CancelBloodRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveHospital]

    def delete(self, request, pk):
        blood_request, error = get_hospital_owned_request(pk, request.user.hospital)
        if error:
            return error

        if blood_request.is_fulfilled:
            return Response({"message": "Cannot cancel a fulfilled request."}, status=status.HTTP_400_BAD_REQUEST)

        blood_request.delete()
        return Response({"message": "Request cancelled successfully."}, status=status.HTTP_200_OK)

class DonorInterestCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveDonor]

    def post(self, request, pk):
        user = request.user
        try:
            donor = user.donor
        except Donor.DoesNotExist:
            return Response({"error": "Donor profile not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            blood_request = BloodRequest.objects.get(pk=pk)
        except BloodRequest.DoesNotExist:
            return Response({"error": "Blood request not found."}, status=status.HTTP_404_NOT_FOUND)

        if hasattr(user, 'hospital') and blood_request.hospital == user.hospital:
            return Response({"error": "You cannot respond to your own hospital's request."}, status=400)

        if DonorInterest.objects.filter(donor=donor, blood_request=blood_request).exists():
            return Response({"message": "You've already offered to help with this request."}, status=400)

        DonorInterest.objects.create(donor=donor, blood_request=blood_request)

        return Response({"message": "Thank you for offering to help!"}, status=status.HTTP_201_CREATED)

class InterestedDonorsView(generics.ListAPIView):
    serializer_class = DonorPublicSerializer
    permission_classes = [permissions.IsAuthenticated, IsActiveHospital]

    def get_queryset(self):
        blood_request = get_object_or_404(BloodRequest, id=self.kwargs['pk'])

        if blood_request.hospital != self.request.user.hospital:
            raise PermissionDenied("You do not have permission to view donors for this request.")

        donor_ids = DonorInterest.objects.filter(blood_request=blood_request).values_list('donor', flat=True)
        return Donor.objects.filter(id__in=donor_ids).order_by('id')

class NearbyDonorsView(generics.ListAPIView):
    serializer_class = DonorPublicSerializer
    permission_classes = [permissions.IsAuthenticated, IsActiveHospital]

    def get_queryset(self):
        user = self.request.user
        hospital = user.hospital

        hospital_lat = hospital.latitude
        hospital_lon = hospital.longitude

        donors = Donor.objects.filter(is_available=True).order_by('id')

        blood_group = self.request.query_params.get('blood_group')
        if blood_group:
            donors = donors.filter(blood_group=blood_group)

        nearby_donors = []

        for donor in donors:
            if donor.latitude and donor.longitude:
                distance = calculate_distance(hospital_lat, hospital_lon, donor.latitude, donor.longitude)
                if distance <= 20:
                    nearby_donors.append(donor.id)

        return Donor.objects.filter(id__in=nearby_donors).order_by('id')

class NotifyDonorView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveHospital]

    def post(self, request, *args, **kwargs):
        serializer = NotifyDonorSerializer(data=request.data)
        if serializer.is_valid():
            donor_ids = serializer.validated_data['donor_ids']
            message = serializer.validated_data['message']

            hospital = request.user.hospital
            hospital_name = hospital.name

            cutomized_message = f"Message from {hospital_name}:\n\n{message}"
            donors = self.get_donors(donor_ids)
            if not donors:
                return Response({"detail": "Donors not found"}, status=status.HTTP_404_NOT_FOUND)

            for donor in donors:
                if not self.send_email(donor, cutomized_message):
                    return Response({"detail": f"Failed to send message to donor {donor.email}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"detail": "Messages sent successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_donors(self, donor_ids):
        return Donor.objects.filter(id__in=donor_ids)

    def send_email(self, donor, message):
        try:
            send_mail(
                f"Blood Donation Request",
                message,
                'from@example.com',
                [donor.user.email],
                fail_silently=False
            )
            return True
        except Exception as e:
            return False