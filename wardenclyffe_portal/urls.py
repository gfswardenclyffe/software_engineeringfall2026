"""
URL configuration for wardenclyffe_portal project.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("portal.urls")),
]
