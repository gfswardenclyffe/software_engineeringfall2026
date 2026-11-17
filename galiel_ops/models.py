"""Business operations kept in an independent app, decoupled from pending pricing migration 0012."""
from django.conf import settings
from django.db import models
from django.utils import timezone

class Announcement(models.Model):
    CATEGORIES=[("news","News"),("rule_change","Rule change"),("new_service","New service"),("office_hours","Office hours")]
    title_en=models.CharField(max_length=180)
    title_es=models.CharField(max_length=180)
    title_fr=models.CharField(max_length=180)
    body_en=models.TextField()
    body_es=models.TextField()
    body_fr=models.TextField()
    category=models.CharField(max_length=20,choices=CATEGORIES,db_index=True)
    published_at=models.DateTimeField(default=timezone.now,db_index=True)
    expires_at=models.DateTimeField(null=True,blank=True)
    author=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,related_name="galiel_announcements")
    class Meta:
        ordering=["-published_at","-pk"]
    def __str__(self):
        return self.title_en

class Reminder(models.Model):
    KINDS=[("documents","Documents requested"),("quote","Quotation ready"),("renewal","Permit renewal due"),("invoice","Invoice request"),("other","Other")]
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="galiel_reminders")
    application=models.ForeignKey("portal.ServiceApplication",null=True,blank=True,on_delete=models.SET_NULL,related_name="galiel_reminders")
    kind=models.CharField(max_length=16,choices=KINDS)
    message=models.TextField(max_length=1200)
    due_date=models.DateField(null=True,blank=True)
    read_at=models.DateTimeField(null=True,blank=True)
    dismissed=models.BooleanField(default=False,db_index=True)
    created_at=models.DateTimeField(default=timezone.now,db_index=True)
    emailed_at=models.DateTimeField(null=True,blank=True)
    due_notice_sent_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        ordering=["-created_at","-pk"]
    def __str__(self):
        return f"{self.get_kind_display()} · {self.user_id}"

class AccountDeletionRequest(models.Model):
    STATUS=[("pending","Pending review"),("in_review","In review"),("completed","Completed"),("declined","Declined")]
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="galiel_deletion_requests")
    status=models.CharField(max_length=15,choices=STATUS,default="pending",db_index=True)
    requested_at=models.DateTimeField(default=timezone.now)
    handled_at=models.DateTimeField(null=True,blank=True)
    staff_notes=models.TextField(blank=True)
    class Meta:
        ordering=["-requested_at"]

class FiscalProfile(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="galiel_fiscal_profile")
    rfc=models.CharField(max_length=13,blank=True)
    razon_social=models.CharField(max_length=200,blank=True)
    regimen_fiscal=models.CharField(max_length=12,blank=True)
    uso_cfdi=models.CharField(max_length=12,blank=True)
    invoice_email=models.EmailField(blank=True)
    updated_at=models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Fiscal details · {self.user_id}"

class InvoiceRequest(models.Model):
    application=models.OneToOneField("portal.ServiceApplication",on_delete=models.CASCADE,related_name="galiel_invoice_request")
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="galiel_invoice_requests")
    requested_at=models.DateTimeField(default=timezone.now)
    staff_notified_at=models.DateTimeField(null=True,blank=True)
    handled_at=models.DateTimeField(null=True,blank=True)
    def __str__(self):
        return f"Invoice request · {self.application_id}"
