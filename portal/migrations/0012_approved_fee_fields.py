from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("portal", "0011_contact_leads")]
    operations = [
        migrations.AddField(model_name="serviceoffering", name="base_fee",
            field=models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)),
        migrations.AddField(model_name="serviceoffering", name="included_m2",
            field=models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)),
        migrations.AddField(model_name="serviceoffering", name="per_extra_m2",
            field=models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)),
        migrations.AddField(model_name="serviceoffering", name="fee_covers",
            field=models.TextField(blank=True)),
        migrations.AlterField(model_name="serviceoffering", name="price_type",
            field=models.CharField(max_length=12, default="quote", choices=[
                ("fixed", "Fixed price"), ("per_m2", "Area-based fee"),
                ("starting", "Starting at"), ("quote", "Quotation required"),
            ])),
    ]
