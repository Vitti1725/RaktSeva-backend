from rest_framework import serializers
from .models import Donor
from users.utils import get_coordinates_from_city

class DonorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donor
        fields = ['id', 'blood_group', 'city', 'contact_number', 'is_available']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        city = validated_data.get('city')
        latitude, longitude = get_coordinates_from_city(city)
        donor = Donor.objects.create(
            user=self.context['request'].user,
            latitude=latitude,
            longitude=longitude,
            **validated_data
        )
        return donor



class DonorPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donor
        fields = ['id', 'blood_group', 'city', 'is_available']



