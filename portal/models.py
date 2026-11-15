from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("es", "Español"),
        ("fr", "Français"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=40, blank=True)
    company = models.CharField(max_length=180, blank=True)
    tax_id = models.CharField(max_length=80, blank=True)
    address = models.CharField(max_length=300, blank=True)
    country = models.CharField(max_length=100, blank=True)
    preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="en")

    def __str__(self):
        return f"{self.user.username} profile"
