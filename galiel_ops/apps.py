from django.apps import AppConfig

class GalielOpsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "galiel_ops"

    def ready(self):
        from . import signals  # noqa: F401
