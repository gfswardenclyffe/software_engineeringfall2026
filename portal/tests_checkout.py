from decimal import Decimal
from io import BytesIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    CatalogCountry, CatalogRegion, CatalogMunicipality, CatalogService,
    ServiceOffering, ServiceRequirement, ServiceApplication,
    ApplicationDocument, ClientConversation, ApplicationEvent,
)
from .workflow_views import _confirm_paid


class CheckoutFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="client-flow@example.org", email="client-flow@example.org",
            first_name="María", last_name="García", password="flow-testing-password",
        )
        cls.other = User.objects.create_user(
            username="other-client@example.org", email="other-client@example.org",
            password="flow-testing-password",
        )
        cls.offering = ServiceOffering.objects.get(service__slug="nl-monterrey-uso-suelo")
        cls.offering.price_type = "fixed"
        cls.offering.price = Decimal("200.00")
        cls.offering.tax_rate = Decimal("16.00")
        cls.offering.save()
        cls.question = ServiceRequirement.objects.create(
            offering=cls.offering, kind="question", label_en="Business name",
            label_es="Razón social", label_fr="Raison sociale", is_required=True,
        )
        cls.document = ServiceRequirement.objects.create(
            offering=cls.offering, kind="document", label_en="Proof of address",
            label_es="Comprobante de domicilio", label_fr="Justificatif de domicile", is_required=True,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def start(self):
        result = self.client.post(reverse("application_start", args=[self.offering.pk]))
        self.assertEqual(result.status_code, 302)
        return ServiceApplication.objects.get(client=self.user)

    def complete_to_review(self, app):
        self.client.post(reverse("application_step", args=[app.pk, 1]))
        response = self.client.post(
            reverse("application_step", args=[app.pk, 2]),
            {"answer_" + str(self.question.pk): "María García LLC"},
        )
        self.assertEqual(response.status_code, 302)
        file = SimpleUploadedFile("address.pdf", b"%PDF-1.4\nproof", content_type="application/pdf")
        response = self.client.post(
            reverse("application_upload", args=[app.pk, self.document.pk]), {"file": file}
        )
        self.assertEqual(response.status_code, 302)
        self.client.post(reverse("application_step", args=[app.pk, 3]), {"notes": "Please check documents."})
        result = self.client.post(reverse("application_step", args=[app.pk, 4]), {"terms": "yes"})
        self.assertEqual(result.status_code, 302)
        app.refresh_from_db()

    def test_draft_saved_and_visible_in_dashboard(self):
        app = self.start()
        self.assertEqual(app.status, "draft")
        self.assertEqual(app.events.first().status, "draft")
        self.assertContains(self.client.get(reverse("dashboard")), app.number)
        self.assertContains(self.client.get(reverse("dashboard")), "Draft")
        self.assertContains(self.client.get(reverse("application_track", args=[app.pk])), "María García")

    def test_step2_autosaves_and_refuses_foreign_fields(self):
        app = self.start()
        response = self.client.post(reverse("application_autosave", args=[app.pk]), {
            "answer_" + str(self.question.pk): "Autosaved LLC",
            "answer_999999": "not allowed",
        })
        self.assertEqual(response.status_code, 200)
        app.refresh_from_db()
        self.assertEqual(app.answers[str(self.question.pk)], "Autosaved LLC")
        self.assertNotIn("999999", app.answers)

    def test_required_questions_and_document_block_review(self):
        app = self.start()
        self.client.post(reverse("application_step", args=[app.pk, 1]))
        page = self.client.post(reverse("application_step", args=[app.pk, 2]), {})
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "This field is required")
        self.client.post(reverse("application_step", args=[app.pk, 2]), {
            "answer_" + str(self.question.pk): "Company"
        })
        self.client.post(reverse("application_step", args=[app.pk, 3]), {"notes": ""})
        self.client.post(reverse("application_step", args=[app.pk, 4]), {"terms": "yes"})
        app.refresh_from_db()
        self.assertIsNone(app.terms_accepted_at)
        self.assertEqual(app.step, 4)

    def test_valid_document_upload_replacement_and_delete(self):
        app = self.start()
        good = SimpleUploadedFile("file.png", b"\x89PNG\r\n\x1a\nabc", content_type="image/png")
        self.assertEqual(self.client.post(reverse("application_upload", args=[app.pk, self.document.pk]), {"file": good}).status_code, 302)
        first = app.documents.get()
        invalid = SimpleUploadedFile("bad.png", b"fake", content_type="image/png")
        self.client.post(reverse("application_upload", args=[app.pk, self.document.pk]), {"file": invalid})
        self.assertEqual(app.documents.count(), 1)
        replacement = SimpleUploadedFile("proof.jpg", b"\xff\xd8\xff1234567", content_type="image/jpeg")
        self.client.post(reverse("application_upload", args=[app.pk, self.document.pk]), {"file": replacement})
        self.assertEqual(app.documents.count(), 1)
        last = app.documents.get()
        self.assertNotEqual(first.pk, last.pk)
        self.assertEqual(last.original_filename, "proof.jpg")
        self.assertEqual(self.client.get(reverse("application_download", args=[app.pk, last.pk])).status_code, 200)
        self.client.post(reverse("application_delete_file", args=[app.pk, last.pk]))
        self.assertEqual(app.documents.count(), 0)

    def test_review_snapshots_tax_and_requires_terms(self):
        app = self.start()
        self.complete_to_review(app)
        self.assertEqual(app.subtotal, Decimal("200.00"))
        self.assertEqual(app.tax_amount, Decimal("32.00"))
        self.assertEqual(app.total, Decimal("232.00"))
        self.assertIsNotNone(app.terms_accepted_at)
        self.assertEqual(app.step, 5)

    def test_unpriced_offer_uses_quote_path(self):
        self.offering.price_type = "quote"
        self.offering.price = None
        self.offering.save()
        app = self.start()
        self.complete_to_review(app)
        self.assertIsNone(app.total)
        self.assertContains(self.client.get(reverse("application_step", args=[app.pk, 5])), "Request a quote")
        self.client.post(reverse("application_step", args=[app.pk, 5]), {"action": "quote"})
        app.refresh_from_db()
        self.assertEqual(app.status, "quote_requested")
        self.assertIsNotNone(app.conversation_id)
        self.assertContains(self.client.get(reverse("dashboard")), "Quote requested")

    def test_quote_ready_follows_staff_approved_price(self):
        self.offering.price_type = "quote"
        self.offering.price = None
        self.offering.save()
        app = self.start()
        self.complete_to_review(app)
        self.client.post(reverse("application_step", args=[app.pk, 5]), {"action": "quote"})
        app.status = "quoted"
        app.quoted_amount = Decimal("450.00")
        app.save(update_fields=["status", "quoted_amount"])
        payment = self.client.get(reverse("application_step", args=[app.pk, 5]))
        self.assertContains(payment, "450.00")

    def test_client_cannot_see_other_clients_cases_or_files(self):
        app = self.start()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("application_track", args=[app.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("application_step", args=[app.pk, 1])).status_code, 404)
        self.assertEqual(self.client.post(reverse("application_autosave", args=[app.pk]), {}).status_code, 404)
        self.assertNotContains(self.client.get(reverse("dashboard")), app.number)

    def test_checkout_disabled_without_stripe(self):
        app = self.start()
        self.complete_to_review(app)
        with patch.dict("os.environ", {"GALIEL_STRIPE_SECRET_KEY": "", "GALIEL_STRIPE_WEBHOOK_SECRET": ""}):
            response = self.client.post(reverse("application_checkout", args=[app.pk]))
            self.assertRedirects(response, reverse("application_step", args=[app.pk, 5]))
        app.refresh_from_db()
        self.assertEqual(app.status, "draft")
        self.assertIsNone(app.payment_confirmed_at)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_verified_payment_creates_case_event_and_thread(self):
        app = self.start()
        self.complete_to_review(app)
        app.stripe_checkout_session = "cs_test_application_verified"
        app.save(update_fields=["stripe_checkout_session"])
        with self.captureOnCommitCallbacks(execute=True):
            _confirm_paid(app, {
                "id": "cs_test_application_verified", "client_reference_id": str(app.pk),
                "payment_status": "paid", "amount_total": 23200,
                "currency": "mxn", "payment_intent": "pi_test_123",
            })
        app.refresh_from_db()
        self.assertEqual(app.status, "paid")
        self.assertIsNotNone(app.payment_confirmed_at)
        self.assertEqual(app.stripe_payment_intent, "pi_test_123")
        self.assertIsNotNone(app.conversation_id)
        self.assertTrue(app.events.filter(status="paid").exists())
        self.assertIsNotNone(app.confirmation_sent_at)
        self.assertEqual(self.client.get(reverse("application_step", args=[app.pk, 6])).status_code, 200)

    def test_forged_payment_mismatch_does_not_activate_case(self):
        from decimal import Decimal
        app = self.start()
        self.complete_to_review(app)
        app.stripe_checkout_session = "cs_good"
        app.save(update_fields=["stripe_checkout_session"])
        with self.assertRaises(ValueError):
            _confirm_paid(app, {
                "id": "cs_other", "client_reference_id": str(app.pk),
                "payment_status": "paid", "amount_total": 23200, "currency": "mxn",
            })
        app.refresh_from_db()
        self.assertEqual(app.status, "draft")

    def test_unsigned_webhook_is_rejected(self):
        with patch.dict("os.environ", {"GALIEL_STRIPE_WEBHOOK_SECRET": "whsec_PLACEHOLDER"}):
            response = self.client.post(reverse("stripe_webhook"), data="invalid", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_status_timeline_and_no_direct_success_redirect(self):
        app = self.start()
        self.assertEqual(self.client.get(reverse("application_step", args=[app.pk, 6])).status_code, 302)
        self.assertContains(self.client.get(reverse("application_track", args=[app.pk])), "Draft")

    def test_quote_locks_answers_but_allows_payment_step(self):
        self.offering.price_type = "quote"
        self.offering.price = None
        self.offering.save(update_fields=["price_type", "price"])
        app = self.start()
        self.complete_to_review(app)
        self.client.post(reverse("application_step", args=[app.pk, 5]), {"action": "quote"})
        app.refresh_from_db()
        original = dict(app.answers)
        app.status = "quoted"
        app.quoted_amount = Decimal("450.00")
        app.save(update_fields=["status", "quoted_amount"])
        post = self.client.post(reverse("application_step", args=[app.pk, 2]), {
            "answer_" + str(self.question.pk): "Tampered company",
        })
        self.assertRedirects(post, reverse("application_track", args=[app.pk]))
        app.refresh_from_db()
        self.assertEqual(app.answers, original)
        self.assertContains(self.client.get(reverse("application_step", args=[app.pk, 5])), "450.00")

    def test_receipts_only_after_verified_payment_and_are_private(self):
        app = self.start()
        self.assertEqual(self.client.get(reverse("application_receipt", args=[app.pk])).status_code, 404)
        self.complete_to_review(app)
        app.stripe_checkout_session = "cs_receipt_verified"
        app.save(update_fields=["stripe_checkout_session"])
        with self.captureOnCommitCallbacks(execute=True):
            _confirm_paid(app, {"id": "cs_receipt_verified", "client_reference_id": str(app.pk),
                "payment_status": "paid", "amount_total": 23200, "currency": "mxn",
                "payment_intent": "pi_test_receipt"})
        receipt = self.client.get(reverse("application_receipt", args=[app.pk]))
        self.assertContains(receipt, "Payment confirmation")
        self.assertContains(receipt, "232.00")
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("application_receipt", args=[app.pk])).status_code, 404)

    def test_stripe_redirect_without_webhook_is_pending_not_paid(self):
        app = self.start()
        self.complete_to_review(app)
        app.stripe_checkout_session = "cs_pending"
        app.save(update_fields=["stripe_checkout_session"])
        response = self.client.get(reverse("application_step", args=[app.pk, 6]), {
            "session_id": "cs_pending",
        })
        self.assertContains(response, "Payment verification in progress")
        app.refresh_from_db()
        self.assertEqual(app.status, "draft")

    def test_only_staff_can_view_private_file_via_staff_preview(self):
        app = self.start()
        document = ApplicationDocument.objects.create(
            application=app, requirement=self.document,
            file=SimpleUploadedFile("private.pdf", b"%PDF-1.4 test"),
            original_filename="private.pdf", content_type="application/pdf", size=13,
        )
        url = reverse("staff_document_download", args=[document.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        staff = User.objects.create_user(
            username="reviewer@example.com", email="reviewer@example.com",
            password="a-strong-staff-password", is_staff=True,
        )
        self.client.force_login(staff)
        self.assertEqual(self.client.get(url).status_code, 200)
