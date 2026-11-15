import uuid
from pathlib import Path
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
    tax_id = models.CharField(max_length=80, blank=True, default="")
    address = models.CharField(max_length=300, blank=True)
    country = models.CharField(max_length=100, blank=True, default="")
    preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="en")

    def __str__(self):
        return f"{self.user.username} profile"

def private_document_path(instance, filename):
    return f"client_documents/{instance.owner_id}/{uuid.uuid4().hex}.pdf"


class ClientDocument(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="client_documents")
    title = models.CharField(max_length=180)
    file = models.FileField(upload_to=private_document_path)
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title
