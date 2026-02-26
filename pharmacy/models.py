from django.db import models

class Medicine(models.Model):

    MEDICINE_TYPES = [
        ("TABLET", "Tablet"),
        ("SYRUP", "Syrup"),
        ("INJECTION", "Injection"),
    ]

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=MEDICINE_TYPES)
    cold_storage = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class PreparationLog(models.Model):

    prescription_id = models.IntegerField()

    total_medicines = models.IntegerField()
    injection_count = models.IntegerField()
    syrup_count = models.IntegerField()
    cold_storage_count = models.IntegerField()

    actual_prepare_time = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

from django.db import models
from reception.models import Token

class Preparation(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PREPARING", "Preparing"),
        ("DISPATCHED", "Dispatched"),
    ]

    token = models.OneToOneField(Token, on_delete=models.CASCADE)

    medicine_count = models.IntegerField(default=0)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    expected_dispatch_time = models.DateTimeField(null=True, blank=True)  # 🔥 ADD THIS

    actual_prepare_time = models.FloatField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    def __str__(self):
        return f"Preparation {self.token.id}"