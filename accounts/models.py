from django.contrib.auth.models import AbstractUser
from django.db import models
from hospitals.models import *  


class User(AbstractUser):

    ROLE_CHOICES = (
        ('PLATFORM_ADMIN', 'Platform Admin'),
        ('HOSPITAL_ADMIN', 'Hospital Admin'),
        ('PHARMACY_MANAGER', 'Pharmacy Manager'),
        ('RECEPTION_STAFF', 'Reception Staff'),
        ('BILLING_STAFF', 'Billing Staff'),
        ('PHARMACIST', 'Pharmacist'),
        ('DISPATCH_STAFF', 'Dispatch Staff'),
        ('ANALYTICS_VIEWER', 'Analytics Viewer'),
    )

    role = models.CharField(max_length=30, choices=ROLE_CHOICES)

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users'
    )

    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.username} - {self.role}"

# 🔹 GLOBAL AUDIT LOG
class AuditLog(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    action = models.CharField(max_length=255)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action}"


# 🔹 HOSPITAL LEVEL AUDIT LOG
class HospitalAuditLog(models.Model):

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    action = models.CharField(max_length=255)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hospital.name} - {self.action}"