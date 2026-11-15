from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0001_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="country",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="profile",
            name="preferred_language",
            field=models.CharField(
                choices=[("en", "English"), ("es", "Español"), ("fr", "Français")],
                default="en",
                max_length=2,
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="tax_id",
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
