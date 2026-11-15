from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import portal.models

class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0003_profile_safe_defaults"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="ClientDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("file", models.FileField(upload_to=portal.models.private_document_path)),
                ("original_filename", models.CharField(max_length=255)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="client_documents", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
    ]
