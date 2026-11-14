from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "phone", "preferred_service")
    search_fields = ("user__username", "user__email", "company")
