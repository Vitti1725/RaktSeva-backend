from django.db import models
from hospital.models import Hospital
from donor.enums import BloodGroupEnum

class BloodRequest(models.Model):

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='blood_requests')
    blood_group = models.CharField(max_length=3,
                                   choices=[(e.value, e.value) for e in BloodGroupEnum],
                                   help_text="Required blood group (e.g. 'O+').")
    city = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    is_fulfilled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.blood_group} - {self.city} ({self.quantity} units)"
