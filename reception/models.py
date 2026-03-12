from django.db import models
from hospitals.models import *
from pharmacy.models import *


class Patient(models.Model):

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Prescription(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription {self.id} - {self.patient.name}"


class Token(models.Model):

    STATUS_CHOICES = [
        ('WAITING', 'Waiting'),
        ('BILLED', 'Billed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    token_number = models.IntegerField()

    # 🔥 ADD THIS
    counter = models.ForeignKey(
        Counter,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="WAITING")

    created_at = models.DateTimeField(auto_now_add=True)

  
    billing_start_time = models.DateTimeField(null=True, blank=True)
    billing_expected_time = models.DateTimeField(null=True, blank=True)
    billing_completed_time = models.DateTimeField(null=True, blank=True)
    alert_message_sent = models.BooleanField(default=False)



class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(
        Prescription,
        related_name="items",
        on_delete=models.CASCADE
    )

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"