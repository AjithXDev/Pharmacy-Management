from django.db import models
from django.conf import settings
from django.contrib.auth.models import User




class Hospital(models.Model):

    name = models.CharField(max_length=255)

    location = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Pharmacy(models.Model):

    PHARMACY_TYPE = (
        ('OP', 'Outpatient'),
        ('IP', 'Inpatient'),
    )

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        related_name='pharmacies'
    )

    name = models.CharField(max_length=255)

    floor_name = models.CharField(max_length=100)

    pharmacy_type = models.CharField(
        max_length=10,
        choices=PHARMACY_TYPE
    )

    # 🔥 Manager Mandatory
    manager = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # manager delete panna mudiyadhu
        limit_choices_to={'role': 'PHARMACY_MANAGER'},
        related_name='managed_pharmacy' ,  # 🔥 ADD THIS
        null=True,      # 👈 TEMP ADD
        blank=True 
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.hospital.name}"


class Pharmacist(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
class Counter(models.Model):
    pharmacy = models.ForeignKey(
        "hospitals.Pharmacy",
        on_delete=models.CASCADE,
        related_name="counters"
    )

    counter_number = models.IntegerField()
    is_active = models.BooleanField(default=True)
    is_busy = models.BooleanField(default=False)

    class Meta:
        unique_together = ('pharmacy', 'counter_number')

    def __str__(self):
        return f"{self.pharmacy.name} - Counter {self.counter_number}"