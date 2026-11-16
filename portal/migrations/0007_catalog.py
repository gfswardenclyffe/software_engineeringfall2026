from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("portal", "0006_profile_structured_address")]
    operations = [
        migrations.CreateModel(name="CatalogCountry", fields=[
            ("code", models.CharField(max_length=2, primary_key=True, serialize=False)),
            ("name_en", models.CharField(max_length=100)),
            ("name_es", models.CharField(max_length=100)),
            ("name_fr", models.CharField(max_length=100)),
        ], options={"ordering": ["name_en"], "verbose_name_plural": "Catalog countries"}),
        migrations.CreateModel(name="CatalogService", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("slug", models.SlugField(max_length=120, unique=True)),
            ("title_en", models.CharField(max_length=180)),
            ("title_es", models.CharField(max_length=180)),
            ("title_fr", models.CharField(max_length=180)),
            ("description_en", models.TextField(blank=True)),
            ("description_es", models.TextField(blank=True)),
            ("description_fr", models.TextField(blank=True)),
        ], options={"ordering": ["title_en"]}),
        migrations.CreateModel(name="CatalogRegion", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("slug", models.SlugField(max_length=80)),
            ("name_en", models.CharField(max_length=120)),
            ("name_es", models.CharField(max_length=120)),
            ("name_fr", models.CharField(max_length=120)),
            ("country", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="regions", to="portal.catalogcountry")),
        ], options={"ordering": ["name_en"]}),
        migrations.CreateModel(name="CatalogMunicipality", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("slug", models.SlugField(max_length=90)),
            ("name_en", models.CharField(max_length=130)),
            ("name_es", models.CharField(max_length=130)),
            ("name_fr", models.CharField(max_length=130)),
            ("region", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="municipalities", to="portal.catalogregion")),
        ], options={"ordering": ["name_en"]}),
        migrations.CreateModel(name="ServiceOffering", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("price_type", models.CharField(choices=[("fixed", "Fixed price"), ("starting", "Starting at"), ("quote", "Quotation required")], default="quote", max_length=12)),
            ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
            ("currency", models.CharField(choices=[("MXN", "MXN"), ("USD", "USD"), ("EUR", "EUR")], default="MXN", max_length=3)),
            ("estimated_min_business_days", models.PositiveSmallIntegerField(blank=True, null=True)),
            ("estimated_max_business_days", models.PositiveSmallIntegerField(blank=True, null=True)),
            ("is_published", models.BooleanField(default=False)),
            ("manager_notes", models.TextField(blank=True, help_text="Internal only; never shown to clients.")),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("country", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="offerings", to="portal.catalogcountry")),
            ("region", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="offerings", to="portal.catalogregion")),
            ("municipality", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="offerings", to="portal.catalogmunicipality")),
            ("service", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="offerings", to="portal.catalogservice")),
        ], options={"ordering": ["country__name_en", "region__name_en", "municipality__name_en", "service__title_en"]}),
        migrations.CreateModel(name="ServiceRequirement", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("kind", models.CharField(choices=[("question", "Intake question"), ("document", "Required document")], max_length=10)),
            ("label_en", models.CharField(max_length=220)),
            ("label_es", models.CharField(max_length=220)),
            ("label_fr", models.CharField(max_length=220)),
            ("is_required", models.BooleanField(default=True)),
            ("display_order", models.PositiveSmallIntegerField(default=0)),
            ("offering", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="requirements", to="portal.serviceoffering")),
        ], options={"ordering": ["display_order", "id"]}),
        migrations.AddConstraint(model_name="catalogregion", constraint=models.UniqueConstraint(fields=["country", "slug"], name="catalog_region_unique")),
        migrations.AddConstraint(model_name="catalogmunicipality", constraint=models.UniqueConstraint(fields=["region", "slug"], name="catalog_municipality_unique")),
        migrations.AddConstraint(model_name="serviceoffering", constraint=models.UniqueConstraint(fields=["service", "country", "region", "municipality"], name="catalog_offering_location_unique")),
        migrations.AddConstraint(model_name="serviceoffering", constraint=models.CheckConstraint(check=models.Q(price__gte=0) | models.Q(price__isnull=True), name="catalog_price_nonnegative")),
    ]
