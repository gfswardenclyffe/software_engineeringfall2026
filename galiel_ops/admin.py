"""Operational staff tools, with no public write endpoints for announcements."""
import logging
from django.contrib import admin
from django.db import transaction
from django.utils import timezone
from .models import Announcement, Reminder, AccountDeletionRequest, FiscalProfile, InvoiceRequest
from .notifications import send_reminder_copy

logger=logging.getLogger(__name__)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display=("title_en","category","published_at","expires_at","author")
    list_filter=("category","published_at")
    search_fields=("title_en","title_es","title_fr","body_en","body_es","body_fr")
    fields=("title_en","title_es","title_fr","body_en","body_es","body_fr","category","published_at","expires_at")
    def save_model(self,request,obj,form,change):
        if not obj.author_id:
            obj.author=request.user
        super().save_model(request,obj,form,change)

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display=("user","application","kind","due_date","read_at","dismissed","emailed_at","due_notice_sent_at")
    list_filter=("kind","dismissed","due_date")
    search_fields=("user__email","message","application__service_title")
    readonly_fields=("created_at","emailed_at","due_notice_sent_at")
    def save_model(self,request,obj,form,change):
        if obj.application_id and obj.application.client_id!=obj.user_id:
            from django.core.exceptions import ValidationError
            raise ValidationError("Reminder recipient must own the associated application.")
        super().save_model(request,obj,form,change)
        if not change:
            transaction.on_commit(lambda: send_reminder_copy(obj.pk))

@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    list_display=("user","status","requested_at","handled_at")
    list_filter=("status",)
    search_fields=("user__email","user__username")
    readonly_fields=("user","requested_at")
    def save_model(self,request,obj,form,change):
        if obj.status in ("completed","declined") and not obj.handled_at:
            obj.handled_at=timezone.now()
        super().save_model(request,obj,form,change)

@admin.register(FiscalProfile)
class FiscalProfileAdmin(admin.ModelAdmin):
    list_display=("user","rfc","razon_social","invoice_email","updated_at")
    search_fields=("user__email","rfc","razon_social")
    def has_add_permission(self,request):
        return False

@admin.register(InvoiceRequest)
class InvoiceRequestAdmin(admin.ModelAdmin):
    list_display=("application","user","requested_at","staff_notified_at","handled_at")
    list_filter=("handled_at",)
    search_fields=("application__service_title","user__email")
    readonly_fields=("application","user","requested_at","staff_notified_at")
