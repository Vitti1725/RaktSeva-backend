from rest_framework.response import Response
from rest_framework import status
from .models import BloodRequest
from math import radians, cos, sin, asin, sqrt


def get_hospital_owned_request(pk, hospital):
    try:
        request_obj = BloodRequest.objects.get(pk=pk, hospital=hospital)
        return request_obj, None
    except BloodRequest.DoesNotExist:
        return None, Response(
            {"error": "Request not found or does not belong to your hospital."},
            status=status.HTTP_404_NOT_FOUND
        )

def calculate_distance(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return km
