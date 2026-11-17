"""Create private alerts on relevant case changes and rejected documents.

Only case ownership and existing status transitions are used. Does not touch fees.
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db import transaction
from portal.models import ServiceApplication, ApplicationDocument
from .models import Reminder
from .notifications import send_reminder_copy

@receiver(pre_save,sender=ServiceApplication,dispatch_uid="galiel_reminder_pre_case")
def _capture_case_previous(sender,instance,**kwargs):
    if instance.pk:
        instance._galiel_previous_status = sender.objects.filter(pk=instance.pk).values_list("status",flat=True).first()
    else:
        instance._galiel_previous_status = None

@receiver(post_save,sender=ServiceApplication,dispatch_uid="galiel_reminder_case")
def _case_alert(sender,instance,created,**kwargs):
    if created or instance.status == getattr(instance,"_galiel_previous_status",None):
        return
    spec = {"missing_documents":("documents","Additional documents have been requested for your process."),
            "quoted":("quote","An updated quotation is ready for your review. Payments are currently on hold.")}
    if instance.status not in spec:
        return
    kind,message=spec[instance.status]
    reminder=Reminder.objects.create(user=instance.client,application=instance,kind=kind,message=message,\n        message_es=("" if kind=="other" else ("Se requieren documentos adicionales para tu trámite." if kind=="documents" else "Hay una cotización actualizada disponible. Los pagos están suspendidos.")),\n        message_fr=("" if kind=="other" else ("Des documents supplémentaires sont demandés pour votre démarche." if kind=="documents" else "Un devis mis à jour est disponible. Les paiements sont suspendus.")))
    transaction.on_commit(lambda: send_reminder_copy(reminder.pk))

@receiver(pre_save,sender=ApplicationDocument,dispatch_uid="galiel_reminder_pre_document")
def _capture_document_previous(sender,instance,**kwargs):
    instance._galiel_previous_review = (sender.objects.filter(pk=instance.pk)
        .values_list("review_status",flat=True).first() if instance.pk else None)

@receiver(post_save,sender=ApplicationDocument,dispatch_uid="galiel_reminder_document")
def _document_alert(sender,instance,created,**kwargs):
    if created or instance.review_status!="rejected" or instance._galiel_previous_review=="rejected":
        return
    reminder=Reminder.objects.create(user=instance.application.client,application=instance.application,
        kind="documents",message="A document needs replacement. Please review the file requirements in your process.",\n        message_es="Es necesario reemplazar un documento. Revisa los requisitos en tu trámite.",\n        message_fr="Un document doit être remplacé. Consultez les exigences de votre démarche.")
    transaction.on_commit(lambda: send_reminder_copy(reminder.pk))
