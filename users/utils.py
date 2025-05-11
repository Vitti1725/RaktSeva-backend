import random
from django.core.mail import send_mail
from users.models import OTP
from django.conf import settings
import requests

def generate_otp(email):
    code = f"{random.randint(100000, 999999)}"
    OTP.objects.create(email=email, code=code)

    send_mail(
        "RaktSeva OTP Verification",
        f"Your OTP code is {code}",
        settings.EMAIL_HOST_USER,
        [email],
    )

def get_coordinates_from_city(city_name):
    api_key = settings.GOOGLE_MAPS_API_KEY
    endpoint = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": city_name,
        "key": api_key
    }
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        results = response.json().get('results')
        if results:
            location = results[0]['geometry']['location']
            return location['lat'], location['lng']
    return None, None

