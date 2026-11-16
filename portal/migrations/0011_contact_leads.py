from django.db import migrations, models
import django.db.models.deletion
import portal.models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0010_service_checkout"),
        migrations.swappable_dependency("auth.User"),
    ]
    operations = [
        migrations.CreateModel(
            name="ContactLead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=180)),
                ("email", models.EmailField(max_length=254)),
                ("phone_code", models.CharField(blank=True, default="+52", max_length=6)),
                ("phone", models.CharField(blank=True, max_length=32)),
                ("country", models.CharField(choices=[("MX", "Mexico"), ("US-TX", "United States – Texas"), ("FR", "France")], max_length=5)),
                ("state_city", models.CharField(max_length=150)),
                ("request_type", models.CharField(max_length=190)),
                ("message", models.TextField(max_length=5000)),
                ("attachment", models.FileField(blank=True, upload_to=portal.models.lead_attachment_path)),
                ("attachment_filename", models.CharField(blank=True, max_length=255)),
                ("privacy_consent_at", models.DateTimeField()),
                ("status", models.CharField(choices=[("new", "New"), ("contacted", "Contacted"), ("converted", "Converted to client"), ("closed", "Closed")], db_index=True, default="new", max_length=12)),
                ("language", models.CharField(default="en", max_length=2)),
                ("ip_digest", models.CharField(blank=True, db_index=True, max_length=64)),
                ("visitor_notified", models.BooleanField(default=False)),
                ("team_notified", models.BooleanField(default=False)),
                ("delivery_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("client", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="galiel_contact_leads", to="auth.user")),
                ("conversation", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="contact_lead", to="portal.clientconversation")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
