# Generated for the isolated Galiel operations app; independent of portal/0012_pricing_research.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("portal", "0011_contact_leads"),
    ]
    operations = [
        migrations.CreateModel(name="Announcement", fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("title_en",models.CharField(max_length=180)),
            ("title_es",models.CharField(max_length=180)),
            ("title_fr",models.CharField(max_length=180)),
            ("body_en",models.TextField()),
            ("body_es",models.TextField()),
            ("body_fr",models.TextField()),
            ("category",models.CharField(max_length=20,db_index=True,choices=[("news","News"),("rule_change","Rule change"),("new_service","New service"),("office_hours","Office hours")])),
            ("published_at",models.DateTimeField(db_index=True,default=django.utils.timezone.now)),
            ("expires_at",models.DateTimeField(blank=True,null=True)),
            ("author",models.ForeignKey(null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="galiel_announcements",to=settings.AUTH_USER_MODEL)),
        ],options={"ordering":["-published_at","-pk"]}),
        migrations.CreateModel(name="Reminder",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("kind",models.CharField(max_length=16,choices=[("documents","Documents requested"),("quote","Quotation ready"),("renewal","Permit renewal due"),("invoice","Invoice request"),("other","Other")])),
            ("message",models.TextField(max_length=1200)),
            ("message_es",models.TextField(max_length=1200,blank=True)),
            ("message_fr",models.TextField(max_length=1200,blank=True)),
            ("due_date",models.DateField(blank=True,null=True)),
            ("read_at",models.DateTimeField(blank=True,null=True)),
            ("dismissed",models.BooleanField(db_index=True,default=False)),
            ("created_at",models.DateTimeField(db_index=True,default=django.utils.timezone.now)),
            ("emailed_at",models.DateTimeField(blank=True,null=True)),
            ("due_notice_sent_at",models.DateTimeField(blank=True,null=True)),
            ("application",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="galiel_reminders",to="portal.serviceapplication")),
            ("user",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="galiel_reminders",to=settings.AUTH_USER_MODEL)),
        ],options={"ordering":["-created_at","-pk"]}),
        migrations.CreateModel(name="FiscalProfile",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("rfc",models.CharField(blank=True,max_length=13)),
            ("razon_social",models.CharField(blank=True,max_length=200)),
            ("regimen_fiscal",models.CharField(blank=True,max_length=12)),
            ("uso_cfdi",models.CharField(blank=True,max_length=12)),
            ("invoice_email",models.EmailField(blank=True,max_length=254)),
            ("updated_at",models.DateTimeField(auto_now=True)),
            ("user",models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name="galiel_fiscal_profile",to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="AccountDeletionRequest",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("status",models.CharField(choices=[("pending","Pending review"),("in_review","In review"),("completed","Completed"),("declined","Declined")],db_index=True,default="pending",max_length=15)),
            ("requested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ("handled_at",models.DateTimeField(blank=True,null=True)),
            ("staff_notes",models.TextField(blank=True)),
            ("user",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="galiel_deletion_requests",to=settings.AUTH_USER_MODEL)),
        ],options={"ordering":["-requested_at"]}),
        migrations.CreateModel(name="InvoiceRequest",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("requested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ("staff_notified_at",models.DateTimeField(blank=True,null=True)),
            ("handled_at",models.DateTimeField(blank=True,null=True)),
            ("application",models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name="galiel_invoice_request",to="portal.serviceapplication")),
            ("user",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="galiel_invoice_requests",to=settings.AUTH_USER_MODEL)),
        ]),
    ]
