from django.db import models
from django.conf import settings
from blood_request.models import BloodRequest
from .enums import BloodGroupEnum

class Donor(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=3,
                                   choices=[(e.value, e.value) for e in BloodGroupEnum],
                                   help_text="Required blood group (e.g. 'O+').")
    city = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering =  ['id']

    def __str__(self):
        return f"{self.user.name} ({self.blood_group})"

class DonorInterest(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    blood_request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)


    class Meta:
        unique_together = ('donor', 'blood_request')
        ordering = ['id']

    def __str__(self):
        return f"{self.donor.user.email} interested in {self.blood_request.blood_group}"