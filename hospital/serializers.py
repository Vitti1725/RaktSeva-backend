from .models import Hospital
from rest_framework import serializers
from users.utils import get_coordinates_from_city

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        exclude = ['user', 'latitude', 'longitude']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        city = validated_data.get('city')
        latitude, longitude = get_coordinates_from_city(city)

        hospital = Hospital.objects.create(
            user=self.context['request'].user,
            latitude=latitude,
            longitude=longitude,
            **validated_data
        )
        return hospital

    def update(self, instance, validated_data):
        if 'city' in validated_data:
            city = validated_data.get('city')
            latitude, longitude = get_coordinates_from_city(city)
            instance.latitude = latitude
            instance.longitude = longitude

        return super().update(instance, validated_data)

class HospitalPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id', 'name', 'city']