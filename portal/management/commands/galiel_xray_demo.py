"""Create isolated X-Ray presentation fixtures. Dry-run by default.

The command never uses real client addresses, sends email, changes existing
users or invokes checkout. Use unique demo-only usernames and password values
from environment variables for --apply. It prints the resulting demo case ID.
"""
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from portal.models import (ServiceOffering, ServiceApplication, ApplicationDocument,
                           ApplicationEvent, ClientConversation, ClientMessage)
from galiel_ops.models import Reminder, Announcement

CLIENT = "galiel-xray-demo-client"
STAFF = "galiel-xray-demo-staff"


def demo_pdf():
    text = b"Galiel X-Ray demonstration document - not a real client record."
    stream = b"BT /F1 12 Tf 40 740 Td (" + text + b") Tj ET"
    entries = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    document = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for n, obj in enumerate(entries, 1):
        offsets.append(len(document))
        document.extend(str(n).encode() + b" 0 obj\n" + obj + b"\nendobj\n")
    offset = len(document)
    document.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for position in offsets[1:]:
        document.extend(f"{position:010d} 00000 n \n".encode())
    document.extend(b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" +
                    str(offset).encode() + b"\n%%EOF\n")
    return bytes(document)


class Command(BaseCommand):
    help = "Review or provision demo-only X-Ray accounts, processes, alerts and news."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true",
                            help="Write demo fixtures (only with both credentials provided via env)")

    def handle(self, *args, **options):
        User = get_user_model()
        offerings = ServiceOffering.objects.filter(is_published=True).select_related("service")
        offering = offerings.first()
        if not offering:
            raise CommandError("No published offering exists; cannot create a demo process.")
        existing = list(User.objects.filter(username__in=(CLIENT, STAFF)).values_list("username", flat=True))
        if existing:
            raise CommandError("Demo usernames already exist: refusing to overwrite or reuse accounts.")
        self.stdout.write("DEMO-ONLY: 2 accounts (client and staff), 4 cases, 1 PDF, 2 unread reminders,")
        self.stdout.write("3 announcements (EN/ES/FR), 2 events and 2 conversation messages.")
        self.stdout.write("Selected existing offering: " + str(offering.pk) + " (no catalog changes)")
        if not options["apply"]:
            self.stdout.write("DRY RUN PASS; no database records, emails or files written")
            return
        client_pw = os.environ.get("GALIEL_XRAY_CLIENT_PASSWORD", "")
        staff_pw = os.environ.get("GALIEL_XRAY_STAFF_PASSWORD", "")
        if (len(client_pw) < 16 or len(staff_pw) < 16
                or client_pw == staff_pw):
            raise CommandError("Supply distinct strong demo passwords (16+ chars) through GALIEL_XRAY_CLIENT_PASSWORD and GALIEL_XRAY_STAFF_PASSWORD.")
        # Do not send activation or notification mail to the example.invalid recipients.
        # Create final statuses directly to avoid triggering status-transition hooks.
        with transaction.atomic():
            client = User.objects.create_user(
                username=CLIENT, password=client_pw, email="xray-client@example.invalid",
                first_name="Galiel", last_name="Demo Client", is_active=True)
            staff = User.objects.create_user(
                username=STAFF, password=staff_pw, email="xray-staff@example.invalid",
                first_name="Galiel", last_name="Demo Staff", is_staff=True,
                is_superuser=False, is_active=True)
            for codename in ("view_serviceapplication", "change_serviceapplication",
                             "view_applicationevent", "view_applicationdocument",
                             "view_clientconversation", "view_clientmessage"):
                permission = Permission.objects.filter(content_type__app_label="portal",
                                                       codename=codename).first()
                if permission:
                    staff.user_permissions.add(permission)
            cases = []
            for status, step in (("draft", 3), ("quote_requested", 5),
                                 ("draft", 1), ("draft", 2)):
                case = ServiceApplication.objects.create(
                    client=client, offering=offering, status=status, step=step,
                    service_title=offering.service.title_en,
                    location_label=str(offering.municipality or offering.region or offering.country),
                    currency=offering.currency,
                    notes="X-Ray demo fixture; not a real client application.")
                cases.append(case)
            primary = cases[0]
            document = ApplicationDocument(application=primary, original_filename="xray-demo.pdf",
                                           content_type="application/pdf", size=len(demo_pdf()))
            document.file.save("xray-demo.pdf", ContentFile(demo_pdf()), save=False)
            document.save()
            ApplicationEvent.objects.create(application=primary, status="draft",
                                            note="Demo application created")
            ApplicationEvent.objects.create(application=primary, status="draft",
                                            note="Demo documents uploaded")
            conversation = ClientConversation.objects.create(
                client=client, subject="X-Ray demo conversation")
            primary.conversation = conversation
            primary.save(update_fields=["conversation"])
            ClientMessage.objects.create(conversation=conversation, sender=client,
                                         body="Can I check the required documents?")
            ClientMessage.objects.create(conversation=conversation, sender=staff,
                                         body="Yes. This is a demo-only reply.")
            for kind, en, es, fr in (
                ("documents", "Missing documents", "Documentos pendientes", "Documents manquants"),
                ("quote", "Quote ready", "Cotización disponible", "Devis disponible"),
            ):
                Reminder.objects.create(user=client, application=primary, kind=kind,
                                        message=en, message_es=es, message_fr=fr)
            for name in ("Service announcement", "Portal update", "Office hours"):
                Announcement.objects.create(
                    title_en="Demo: " + name, title_es="Demostración: " + name,
                    title_fr="Démonstration : " + name,
                    body_en="Demo-only news for X-Ray presentation.",
                    body_es="Noticias de demostración para X-Ray.",
                    body_fr="Actualités de démonstration pour X-Ray.",
                    category="news", published_at=timezone.now(), author=staff)
        self.stdout.write(self.style.SUCCESS(
            "DEMO READY: demo_process_id=" + str(primary.pk)))
        self.stdout.write("Client login: " + CLIENT + " ; Staff login: " + STAFF)
        self.stdout.write("No passwords have been printed or stored in source files.")
        self.stdout.write("Set demo_process_id to " + str(primary.pk) +
                          " in BOTH galiel-xray-stops.json static copies after review.")
