from rest_framework import serializers
from .models import BloodRequest
from hospital.serializers import HospitalPublicSerializer
from datetime import timedelta
from django.utils import timezone

class BloodRequestSerializer(serializers.ModelSerializer):
    """
        Blood request schema.

        Fields:
        - id (int, read-only)
        - hospital (HospitalPublicSerializer)
        - city (string)
        - blood_group (string)
        - quantity (int)
        - is_fulfilled (bool)
        - expired (bool, read-only)
        - created_at (datetime, read-only)
    """
    hospital = HospitalPublicSerializer(read_only=True)
    city = serializers.CharField(write_only=True)
    expired = serializers.SerializerMethodField()

    class Meta:
        model = BloodRequest
        fields = '__all__'
        read_only_fields = ['hospital', 'created_at']

    def get_expired(self, obj):
        return obj.created_at + timedelta(hours=48) < timezone.now()

class NotifyDonorSerializer(serializers.Serializer):
    """
        Schema to notify donors.

        Input:
        - donor_ids (list of ints, required)
        - message (string, required)

        Output:
        - sent (int): number of messages sent
    """
    donor_ids = serializers.ListField()
    message = serializers.CharField(max_length=500)

