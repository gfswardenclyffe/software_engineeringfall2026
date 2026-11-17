"""Email delivery for reminders. Errors are logged, not silently discarded."""
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from .models import Reminder
logger=logging.getLogger(__name__)

def send_reminder_copy(reminder_id, *, due_notice=False):
    reminder=Reminder.objects.select_related("user","application").filter(pk=reminder_id).first()
    if not reminder or not reminder.user.is_active or not reminder.user.email or reminder.dismissed:
        return False
    field="due_notice_sent_at" if due_notice else "emailed_at"
    if getattr(reminder,field):
        return False
    language = "en"\n    try:\n        language = reminder.user.profile.preferred_language\n    except (AttributeError, Exception):\n        pass\n    body_text = reminder.message_es if language=="es" and reminder.message_es else (reminder.message_fr if language=="fr" and reminder.message_fr else reminder.message)\n    application_label = reminder.application.number if reminder.application_id else ""
    message=(f"Galiel · {reminder.get_kind_display()}\n\n{reminder.message}\n"
             f"{application_label}\n\nSign in securely: https://galiel.wardenclyffefirm.com/alerts/\n")
    try:
        send_mail(f"Galiel · {reminder.get_kind_display()}",message,settings.DEFAULT_FROM_EMAIL,
                  [reminder.user.email],fail_silently=False)
    except Exception:
        logger.exception("Could not email reminder %s", reminder_id)
        return False
    Reminder.objects.filter(pk=reminder_id,**{field+"__isnull":True}).update(**{field:timezone.now()})
    return True
