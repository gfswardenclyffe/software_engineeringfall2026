from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0002_profile_client_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="country",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AlterField(
            model_name="profile",
            name="tax_id",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
    ]
