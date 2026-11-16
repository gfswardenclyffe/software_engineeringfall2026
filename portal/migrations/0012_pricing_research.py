from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("portal", "0011_contact_leads")]
    operations = [
        migrations.AddField(model_name="serviceoffering", name="is_temporary_price", field=models.BooleanField(default=False, help_text="Estimate only; does not authorize charging this amount.")),
        migrations.AddField(model_name="serviceoffering", name="price_unit", field=models.CharField(blank=True, max_length=80, help_text="Examples: per document, per page, per m², or basic project.")),
        migrations.AddField(model_name="serviceoffering", name="estimated_price_note", field=models.TextField(blank=True, default="Estimated price — final cost confirmed after document review; government fees may vary.")),
        migrations.AddField(model_name="serviceoffering", name="government_fee_estimate", field=models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=12, help_text="Research reference, not a confirmed client-specific government assessment.")),
        migrations.AddField(model_name="serviceoffering", name="service_fee_estimate", field=models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=12, help_text="Proposed Wardenclyffe service fee; staff may revise before publication.")),
        migrations.AddField(model_name="serviceoffering", name="pricing_review_required", field=models.BooleanField(default=True, help_text="Flag unsupported or incomplete estimates for manager verification.")),
        migrations.CreateModel(
            name="OfferingPriceResearch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_kind", models.CharField(choices=[("government", "Official government / authority"), ("market", "Provider / market"), ("context", "Procedure and time context")], max_length=14)),
                ("source_title", models.CharField(max_length=200)),
                ("source_url", models.URLField(blank=True, max_length=1000)),
                ("checked_on", models.DateField()),
                ("government_fee", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("market_low", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("market_high", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("currency", models.CharField(max_length=3)),
                ("fee_unit", models.CharField(blank=True, max_length=90)),
                ("research_notes", models.TextField(blank=True)),
                ("verified", models.BooleanField(default=False, help_text="Verified means the manager reviewed this evidence, not that fees are immutable.")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("offering", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="price_research", to="portal.serviceoffering")),
            ],
            options={"ordering": ["-checked_on", "id"]},
        ),
    ]
