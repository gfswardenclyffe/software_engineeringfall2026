from unittest.mock import patch
from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import ContactLead, CatalogService


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="Galiel <info@wardenclyffefirm.com>",
)
class ContactLeadTests(TestCase):
    def setUp(self):
        self.url = reverse("contact_submit")
        self.payload = {
            "full_name": "María García",
            "email": "maria@example.com",
            "phone_code": "+52",
            "phone": "5512345678",
            "country": "MX",
            "state_city": "Monterrey, Nuevo León",
            "request_type": "other",
            "message": "Please help me with a municipal permit.",
            "privacy_consent": "on",
            "language": "en",
            "website": "",
        }

    def test_home_has_public_form_and_real_service_options(self):
        page = self.client.get(reverse("home"))
        self.assertContains(page, 'id="galiel-contact-form"')
        self.assertContains(page, reverse("contact_submit"))
        self.assertContains(page, "WhatsApp")
        self.assertContains(page, "contactFormTitle")
        self.assertContains(page, "name=\"privacy_consent\"")
        self.assertContains(page, "name=\"request_type\"")

    def test_valid_guest_lead_sends_two_emails_and_saves_privacy(self):
        result = self.client.post(self.url, self.payload)
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()["ok"])
        lead = ContactLead.objects.get()
        self.assertEqual(lead.status, "new")
        self.assertIsNotNone(lead.privacy_consent_at)
        self.assertIsNone(lead.conversation_id)
        self.assertTrue(lead.visitor_notified)
        self.assertTrue(lead.team_notified)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ["maria@example.com"])
        self.assertEqual(mail.outbox[1].to, ["info@wardenclyffefirm.com"])
        self.assertEqual(mail.outbox[1].reply_to, ["maria@example.com"])
        self.assertIn(self.payload["message"], mail.outbox[0].body)

    def test_signed_in_lead_creates_workspace_thread(self):
        user = User.objects.create_user(
            username="client@example.com", email="client@example.com",
            password="StrongPassword123!", first_name="Alex", last_name="Client",
        )
        self.client.force_login(user)
        result = self.client.post(self.url, self.payload)
        self.assertEqual(result.status_code, 200)
        lead = ContactLead.objects.get()
        self.assertEqual(lead.client, user)
        self.assertEqual(lead.conversation.client, user)
        self.assertEqual(lead.conversation.entries.first().sender, user)
        self.assertEqual(lead.conversation.entries.first().body, self.payload["message"])
        self.assertContains(self.client.get(reverse("messages_inbox")), "GL-")
        self.assertContains(self.client.get(reverse("home")), "Alex Client")

    def test_valid_pdf_is_attached_to_team_email_only(self):
        payload = self.payload.copy()
        payload["attachment"] = SimpleUploadedFile(
            "license.pdf", b"%PDF-1.7\nvalid", content_type="application/pdf",
        )
        result = self.client.post(self.url, payload)
        self.assertEqual(result.status_code, 200)
        lead = ContactLead.objects.get()
        self.assertTrue(lead.attachment.name.startswith("contact_leads/"))
        self.assertEqual(lead.attachment_filename, "license.pdf")
        self.assertEqual(len(mail.outbox[0].attachments), 0)
        self.assertEqual(len(mail.outbox[1].attachments), 1)
        self.assertEqual(mail.outbox[1].attachments[0][0], "license.pdf")

    def test_invalid_signature_and_oversized_files_rejected(self):
        payload = self.payload.copy()
        payload["attachment"] = SimpleUploadedFile(
            "spoofed.pdf", b"not a pdf", content_type="application/pdf",
        )
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("attachment", response.json()["errors"])
        self.assertEqual(ContactLead.objects.count(), 0)

    def test_invalid_email_missing_consent_and_invalid_service(self):
        payload = self.payload.copy()
        payload["email"] = "not-email"
        payload.pop("privacy_consent")
        payload["request_type"] = "fake-service"
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["errors"])
        self.assertIn("privacy_consent", response.json()["errors"])
        self.assertIn("request_type", response.json()["errors"])
        self.assertEqual(ContactLead.objects.count(), 0)

    def test_honeypot_discards_bot_message(self):
        payload = self.payload.copy()
        payload["website"] = "https://spam.example"
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactLead.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_ip_submission_limit(self):
        for i in range(5):
            payload = self.payload.copy()
            payload["email"] = f"valid{i}@example.com"
            response = self.client.post(self.url, payload, REMOTE_ADDR="203.0.113.85")
            self.assertEqual(response.status_code, 200)
        response = self.client.post(self.url, self.payload, REMOTE_ADDR="203.0.113.85")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(ContactLead.objects.count(), 5)

    def test_mail_failure_still_preserves_lead_and_flags_admin(self):
        with patch("portal.contact_views._send_mail", side_effect=OSError("SMTP offline")):
            response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, 200)
        lead = ContactLead.objects.get()
        self.assertFalse(lead.visitor_notified)
        self.assertFalse(lead.team_notified)
        self.assertIn("OSError", lead.delivery_error)

    def test_get_disallowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_lead_attachment_only_available_to_staff(self):
        payload = self.payload.copy()
        payload["attachment"] = SimpleUploadedFile(
            "id.png", b"\x89PNG\r\n\x1a\nOK", content_type="image/png",
        )
        self.client.post(self.url, payload)
        lead = ContactLead.objects.get()
        endpoint = reverse("staff_lead_attachment", args=[lead.pk])
        self.assertEqual(self.client.get(endpoint).status_code, 404)
        staff = User.objects.create_user(
            username="staff@example.com", email="staff@example.com",
            password="StaffPassword123!", is_staff=True,
        )
        self.client.force_login(staff)
        self.assertEqual(self.client.get(endpoint).status_code, 200)

    def test_service_options_are_catalog_services(self):
        service = CatalogService.objects.get(slug="nl-monterrey-uso-suelo")
        payload = self.payload.copy()
        payload["request_type"] = service.slug
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactLead.objects.get().request_type, service.title_en)

    def test_french_and_spanish_responses(self):
        for lang in ("es", "fr"):
            payload = self.payload.copy()
            payload["language"] = lang
            response = self.client.post(self.url, payload)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["ok"])
            self.assertIn("Galiel", mail.outbox[-2].subject)
