from rest_framework import serializers
from .models import BloodRequest
from hospital.serializers import HospitalPublicSerializer
from datetime import timedelta
from django.utils import timezone

class BloodRequestSerializer(serializers.ModelSerializer):
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
    donor_ids = serializers.ListField()
    message = serializers.CharField(max_length=500)

