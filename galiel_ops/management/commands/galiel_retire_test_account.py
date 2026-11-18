"""Guarded retirement of an inactive test account.

Reports related records; never cascades a client with business history.
Operator must first complete an approved private DB backup.
"""
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from portal.models import ServiceApplication, ClientDocument, ClientConversation, ClientMessage, ContactLead
from galiel_ops.models import Reminder, InvoiceRequest, AccountDeletionRequest
class Command(BaseCommand):
    help="Audit/retire an unused non-staff test account; no automatic deletion."

    def add_arguments(self,parser):
        parser.add_argument("--email",required=True)
        parser.add_argument("--delete",action="store_true")
        parser.add_argument("--confirm",default="")

    def handle(self,*args,**options):
        email=options["email"].lower().strip()
        user=get_user_model().objects.filter(email__iexact=email).first()
        if not user:
            self.stdout.write("NO MATCH: no account with this email.")
            return
        if user.is_staff or user.is_superuser:
            raise CommandError("Refusing to delete a staff/superuser account.")
        counts={
            "applications":ServiceApplication.objects.filter(client=user).count(),
            "documents":ClientDocument.objects.filter(owner=user).count(),
            "conversations":ClientConversation.objects.filter(client=user).count(),
            "messages":ClientMessage.objects.filter(sender=user).count(),
            "leads":ContactLead.objects.filter(client=user).count(),
            "reminders":Reminder.objects.filter(user=user).count(),
            "invoice_requests":InvoiceRequest.objects.filter(user=user).count(),
            "deletion_requests":AccountDeletionRequest.objects.filter(user=user).count(),
        }
        for name,count in counts.items():
            self.stdout.write(f"{name}: {count}")
        if not options["delete"]:
            self.stdout.write("DRY RUN ONLY. No account removed.")
            return
        if any(counts.values()):
            raise CommandError("Related business records exist; manual retention review required.")
        if (options["confirm"]!=email or os.environ.get("APPROVE_GALIEL_TEST_ACCOUNT_REMOVAL")!="YES"):
            raise CommandError("Confirmation email and approval environment flag required.")
        if not user.is_active:
            self.stdout.write("Account already inactive; deleting unused identity after approval.")
        with transaction.atomic():
            user.delete()
        self.stdout.write("Retired unused test account with no business records.")
