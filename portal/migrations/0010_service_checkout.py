from django.db import migrations, models
import django.db.models.deletion
import portal.models


class Migration(migrations.Migration):
    dependencies = [("portal", "0009_seed_homepage_catalog"), migrations.swappable_dependency("auth.User")]
    operations = [
        migrations.AddField(model_name="serviceoffering", name="deposit_amount",
            field=models.DecimalField(blank=True, decimal_places=2, help_text="Starting-price services: optional payable deposit, not final price.", max_digits=12, null=True)),
        migrations.AddField(model_name="serviceoffering", name="tax_rate",
            field=models.DecimalField(decimal_places=2, default=0, help_text="Applicable checkout tax percentage configured by staff; do not assume IVA applies.", max_digits=5)),
        migrations.CreateModel(name="ServiceApplication", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("status", models.CharField(choices=[
                ("draft", "Draft"), ("quote_requested", "Quote requested"), ("quoted", "Quote ready"),
                ("awaiting_payment", "Awaiting payment"), ("paid", "Paid"), ("under_review", "Under review"),
                ("missing_documents", "Missing documents"), ("submitted", "Submitted to authority"),
                ("in_process", "In process"), ("ready", "Ready / Delivered"), ("cancelled", "Cancelled"),
            ], db_index=True, default="draft", max_length=25)),
            ("step", models.PositiveSmallIntegerField(default=1)),
            ("answers", models.JSONField(blank=True, default=dict)),
            ("notes", models.TextField(blank=True)),
            ("terms_accepted_at", models.DateTimeField(blank=True, null=True)),
            ("service_title", models.CharField(blank=True, max_length=180)),
            ("location_label", models.CharField(blank=True, max_length=240)),
            ("currency", models.CharField(blank=True, max_length=3)),
            ("subtotal", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
            ("tax_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
            ("total", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
            ("quoted_amount", models.DecimalField(blank=True, decimal_places=2, help_text="Staff-approved amount payable, including any tax.", max_digits=12, null=True)),
            ("estimated_delivery", models.DateField(blank=True, null=True)),
            ("stripe_checkout_session", models.CharField(blank=True, max_length=255)),
            ("stripe_payment_intent", models.CharField(blank=True, max_length=255)),
            ("stripe_receipt_url", models.URLField(blank=True, max_length=1000)),
            ("payment_confirmed_at", models.DateTimeField(blank=True, null=True)),
            ("confirmation_sent_at", models.DateTimeField(blank=True, null=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_galiel_cases", to="auth.user")),
            ("client", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="galiel_applications", to="auth.user")),
            ("conversation", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="application", to="portal.clientconversation")),
            ("offering", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="applications", to="portal.serviceoffering")),
        ], options={"ordering": ["-updated_at"]}),
        migrations.CreateModel(name="ApplicationDocument", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("original_filename", models.CharField(max_length=255)),
            ("file", models.FileField(upload_to=portal.models.case_file_path)),
            ("content_type", models.CharField(max_length=40)),
            ("size", models.PositiveIntegerField()),
            ("is_deliverable", models.BooleanField(default=False)),
            ("uploaded_at", models.DateTimeField(auto_now_add=True)),
            ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to="portal.serviceapplication")),
            ("requirement", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="portal.servicerequirement")),
        ], options={"ordering": ["uploaded_at"]}),
        migrations.CreateModel(name="ApplicationEvent", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("status", models.CharField(choices=[
                ("draft", "Draft"), ("quote_requested", "Quote requested"), ("quoted", "Quote ready"),
                ("awaiting_payment", "Awaiting payment"), ("paid", "Paid"), ("under_review", "Under review"),
                ("missing_documents", "Missing documents"), ("submitted", "Submitted to authority"),
                ("in_process", "In process"), ("ready", "Ready / Delivered"), ("cancelled", "Cancelled"),
            ], max_length=25)),
            ("note", models.CharField(blank=True, max_length=400)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="portal.serviceapplication")),
        ], options={"ordering": ["created_at", "pk"]}),
    ]
