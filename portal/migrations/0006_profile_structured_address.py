from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0005_messaging"),
    ]

    operations = [
        migrations.AddField(model_name="profile", name="street", field=models.CharField(max_length=180, blank=True, default="")),
        migrations.AddField(model_name="profile", name="street_number", field=models.CharField(max_length=30, blank=True, default="")),
        migrations.AddField(model_name="profile", name="unit", field=models.CharField(max_length=60, blank=True, default="")),
        migrations.AddField(model_name="profile", name="city", field=models.CharField(max_length=100, blank=True, default="")),
        migrations.AddField(model_name="profile", name="state_region", field=models.CharField(max_length=100, blank=True, default="")),
        migrations.AddField(model_name="profile", name="postal_code", field=models.CharField(max_length=30, blank=True, default="")),
    ]
