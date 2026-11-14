from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    SERVICE_CHOICES = [
        ("consulting", "Consulting"),
        ("finance", "Finance"),
        ("technology", "Technology"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=30, blank=True)
    company = models.CharField(max_length=150, blank=True)
    address = models.CharField(max_length=255, blank=True)
    preferred_service = models.CharField(
        max_length=20,
        choices=SERVICE_CHOICES,
        blank=True,
    )

    def __str__(self):
        return f"{self.user.username} Profile"
