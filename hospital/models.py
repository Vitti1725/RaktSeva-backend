from django.db import models
from django.conf import settings

class Hospital(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=False, blank=False)
    city = models.CharField(max_length=100)
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    registration_number = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)


    def __str__(self):
        return self.name
