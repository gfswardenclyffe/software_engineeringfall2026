from django.db import migrations


def seed_countries(apps, schema_editor):
    Country = apps.get_model("portal", "CatalogCountry")
    for code, en, es, fr in [
        ("MX", "Mexico", "México", "Mexique"),
        ("US", "United States", "Estados Unidos", "États-Unis"),
        ("FR", "France", "Francia", "France"),
    ]:
        Country.objects.get_or_create(
            code=code,
            defaults={"name_en": en, "name_es": es, "name_fr": fr},
        )


class Migration(migrations.Migration):
    dependencies = [("portal", "0007_catalog")]
    operations = [migrations.RunPython(seed_countries, migrations.RunPython.noop)]
