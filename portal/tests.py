from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile


class ClientProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="client@example.com",
            email="client@example.com",
            password="a-strong-test-password",
            first_name="Client",
            last_name="Example",
        )
        self.user.profile.phone = "555-1234"
        self.user.profile.company = "Example LLC"
        self.user.profile.tax_id = "TAX123"
        self.user.profile.address = "100 Example Street"
        self.user.profile.country = "USA"
        self.user.profile.save()

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_profile_displays_existing_user_data(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Client Example")
        self.assertContains(response, "Example LLC")
        self.assertContains(response, "TAX123")

    def test_profile_update_saves_and_redirects_to_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("profile_edit"),
            {
                "first_name": "Updated",
                "last_name": "Example",
                "email": "client@example.com",
                "phone": "555-6789",
                "company": "Updated LLC",
                "tax_id": "TAX456",
                "address": "200 Example Street",
                "country": "USA",
                "preferred_language": "es",
            },
        )
        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.profile.company, "Updated LLC")
        self.assertEqual(self.user.profile.preferred_language, "es")

    def test_registration_complete_route_exists(self):
        response = self.client.get(reverse("registration_complete"))
        self.assertEqual(response.status_code, 200)

    def test_logout_uses_post(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)


from unittest.mock import patch
from django.core import mail
from django.test import override_settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEBUG=True)
class AccountLifecycleTests(TestCase):
    def registration_data(self):
        return {
            "first_name": "Alex",
            "last_name": "Client",
            "email": "alex@example.com",
            "phone": "",
            "company": "",
            "tax_id": "",
            "address": "",
            "country": "",
            "preferred_language": "en",
            "password1": "StrongTestingPass789!",
            "password2": "StrongTestingPass789!",
        }

    def test_signup_sends_confirmation_and_blocks_login(self):
        response = self.client.post(reverse("register"), self.registration_data())
        self.assertRedirects(response, reverse("registration_complete"))
        user = User.objects.get(email="alex@example.com")
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/activate/", mail.outbox[0].body)
        response = self.client.post(reverse("login"), {
            "username": "alex@example.com", "password": "StrongTestingPass789!"
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_verification_activates_and_signs_in_user(self):
        self.client.post(reverse("register"), self.registration_data())
        user = User.objects.get(email="alex@example.com")
        activation = reverse("activate_account", kwargs={
            "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
        })
        response = self.client.get(activation)
        self.assertRedirects(response, reverse("dashboard"))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        # Activation link cannot be reused after activation.
        self.client.logout()
        self.assertEqual(self.client.get(activation).status_code, 400)

    def test_bad_confirmation_link_does_not_activate(self):
        self.client.post(reverse("register"), self.registration_data())
        user = User.objects.get(email="alex@example.com")
        response = self.client.get(reverse("activate_account", kwargs={
            "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": "not-a-valid-token",
        }))
        self.assertEqual(response.status_code, 400)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_email_delivery_failure_rolls_back_registration(self):
        with patch("portal.verification.send_mail", side_effect=OSError("SMTP unavailable")):
            response = self.client.post(reverse("register"), self.registration_data())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="alex@example.com").exists())
        self.assertContains(response, "confirmation email")

    def test_resend_confirmation_is_throttled(self):
        self.client.post(reverse("register"), self.registration_data())
        mail.outbox.clear()
        response = self.client.post(reverse("resend_activation"), {"email": "alex@example.com"})
        self.assertRedirects(response, reverse("registration_complete"))
        self.assertEqual(len(mail.outbox), 1)
        self.client.post(reverse("resend_activation"), {"email": "alex@example.com"})
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_for_verified_account(self):
        user = User.objects.create_user(
            username="verified@example.com", email="verified@example.com",
            password="ValidPassword123!",
        )
        response = self.client.post(reverse("password_reset"), {
            "email": "verified@example.com",
        })
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/password-reset/confirm/", mail.outbox[0].body)

    def test_profile_email_cannot_be_changed_without_verification(self):
        user = User.objects.create_user(
            username="verified@example.com", email="verified@example.com",
            password="ValidPassword123!",
        )
        self.client.force_login(user)
        response = self.client.post(reverse("profile_edit"), {
            "first_name": "Verified", "last_name": "Client",
            "email": "unverified@example.com",
            "phone": "", "company": "", "tax_id": "",
            "address": "", "country": "", "preferred_language": "en",
        })
        self.assertRedirects(response, reverse("profile"))
        user.refresh_from_db()
        self.assertEqual(user.email, "verified@example.com")

    def test_registration_and_login_forms_are_responsive(self):
        for url in ("login", "register", "password_reset"):
            response = self.client.get(reverse(url))
            self.assertContains(response, 'name="viewport"')


class LogoutCsrfTests(TestCase):
    """Authenticated pages should issue fresh CSRF tokens and never be cached."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="logout-test@example.com",
            email="logout-test@example.com",
            password="StrongPassword123!",
        )
        from django.test import Client
        self.csrf_client = Client(enforce_csrf_checks=True)

    def test_dashboard_is_not_cached_and_logout_post_succeeds(self):
        self.csrf_client.force_login(self.user)
        page = self.csrf_client.get(reverse("dashboard"))
        self.assertEqual(page.status_code, 200)
        self.assertIn("no-store", page["Cache-Control"])
        self.assertIn("csrftoken", self.csrf_client.cookies)
        import re
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page.content.decode())
        self.assertIsNotNone(match)
        result = self.csrf_client.post(
            reverse("logout"), {"csrfmiddlewaretoken": match.group(1)},
            HTTP_REFERER="https://galiel.wardenclyffefirm.com/dashboard/",
        )
        self.assertEqual(result.status_code, 302)
        self.assertNotIn("_auth_user_id", self.csrf_client.session)

    def test_profile_not_cached(self):
        self.csrf_client.force_login(self.user)
        page = self.csrf_client.get(reverse("profile"))
        self.assertEqual(page.status_code, 200)
        self.assertIn("no-store", page["Cache-Control"])


class WorkspaceServicesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="services-test@example.com", email="services-test@example.com",
            password="StrongTestingPass123!",
        )

    def test_services_are_inside_client_workspace(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, 'id="services"')
        self.assertContains(response, 'href="#services"')
        self.assertNotContains(response, 'href="/#services"')
        self.assertContains(response, "Browse services by location")
        self.assertContains(response, reverse("service_catalog"))

    def test_service_inquiry_prefills_message_subject(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("messages_inbox"),
            {"service": "tx-apostille"},
        )
        self.assertContains(response, "Inquiry: Apostille coordination")
        self.assertEqual(response.status_code, 200)

    def test_invalid_service_does_not_prefill_message(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("messages_inbox"),
            {"service": "unknown-service"},
        )
        self.assertNotContains(response, "Inquiry:")
        self.assertEqual(response.status_code, 200)

    def test_staff_can_browse_catalog_without_client_message_form(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.client.force_login(self.user)
        dashboard = self.client.get(reverse("dashboard"))
        self.assertContains(dashboard, "Browse services by location")
        messages_page = self.client.get(reverse("messages_inbox"), {"service": "tx-apostille"})
        self.assertNotContains(messages_page, "New message to Wardenclyffe")


class StructuredProfileAddressTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="address@example.com", email="address@example.com", password="StrongPass123!")
        self.user.profile.address = "Previous address 44, Some City"
        self.user.profile.save()

    def test_legacy_address_visible_until_user_updates(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("profile")), "Previous address 44")
        self.assertContains(self.client.get(reverse("profile_edit")), "Previously saved address")

    def test_structured_address_is_saved_without_erasing_previous_address(self):
        self.client.force_login(self.user)
        result = self.client.post(reverse("profile_edit"), {
            "first_name": "Address", "last_name": "Tester", "phone": "",
            "company": "", "tax_id": "AB-123", "street": "Main Street",
            "street_number": "123", "unit": "Suite 4", "city": "Edinburg",
            "state_region": "Texas", "postal_code": "78539",
            "country": "United States", "preferred_language": "en",
        })
        self.assertRedirects(result, reverse("profile"))
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.street, "Main Street")
        self.assertEqual(self.user.profile.postal_code, "78539")
        self.assertEqual(self.user.profile.address, "Previous address 44, Some City")

    def test_tax_id_label(self):
        self.client.force_login(self.user)
        page = self.client.get(reverse("profile_edit"))
        self.assertContains(page, "Tax ID (if applicable)")
        self.assertNotContains(page, "RFC / Tax ID")


# Production operations regression tests: run via python manage.py test portal.
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.contrib.auth.models import User as PortalTestUser
from portal.models import CatalogCountry, CatalogService, ServiceOffering, ServiceApplication, ApplicationDocument, ServiceRequirement
from galiel_ops.models import Announcement, Reminder, FiscalProfile, InvoiceRequest, AccountDeletionRequest


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ProductionOperationsPrivacyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = PortalTestUser.objects.create_user(username="client-one@example.test", email="client-one@example.test",
                                                       password="StrongPrivatePass001!")
        cls.bob = PortalTestUser.objects.create_user(username="client-two@example.test", email="client-two@example.test",
                                                     password="StrongPrivatePass002!")
        cls.staff = PortalTestUser.objects.create_user(username="staff@example.test",email="staff@example.test",
                                                       password="StrongPrivatePass003!",is_staff=True)
        cls.country = CatalogCountry.objects.create(code="MX",name_en="Mexico",name_es="México",name_fr="Mexique")
        cls.service = CatalogService.objects.create(slug="portal-smoke",title_en="Administrative filing",
                                                     title_es="Trámite administrativo",title_fr="Démarche administrative")
        cls.offering = ServiceOffering.objects.create(service=cls.service,country=cls.country,
                                                      is_published=True,currency="MXN",price_type="quote")
        cls.app_a = ServiceApplication.objects.create(client=cls.alice,offering=cls.offering,
            status="draft",step=5,service_title=cls.service.title_en,currency="MXN")
        cls.app_b = ServiceApplication.objects.create(client=cls.bob,offering=cls.offering,
            status="draft",step=5,service_title=cls.service.title_en,currency="MXN")

    def test_login_required_for_private_operations(self):
        for name in ("galiel_announcements","galiel_reminders","galiel_fiscal_profile","galiel_help_processes"):
            response=self.client.get(reverse(name))
            self.assertEqual(response.status_code,302,name)
            self.assertIn("/login/",response.url)

    def test_announcements_filter_and_expiry(self):
        self.client.force_login(self.alice)
        Announcement.objects.create(title_en="Current",title_es="Actual",title_fr="Actuelle",body_en="EN",body_es="ES",
            body_fr="FR",category="news",author=self.staff,published_at=timezone.now()-timedelta(days=1))
        Announcement.objects.create(title_en="Expired",title_es="Caducada",title_fr="Expirée",
            body_en="x",body_es="x",body_fr="x",category="news",
            published_at=timezone.now()-timedelta(days=2),expires_at=timezone.now()-timedelta(days=1))
        Announcement.objects.create(title_en="Future",title_es="Futura",title_fr="À venir",
            body_en="x",body_es="x",body_fr="x",category="news",published_at=timezone.now()+timedelta(days=1))
        response=self.client.get(reverse("galiel_announcements")+"?category=news&lang=es")
        self.assertContains(response,"Actual")
        self.assertNotContains(response,"Expired")
        self.assertNotContains(response,"Future")

    def test_alerts_never_leak_between_clients(self):
        alert=Reminder.objects.create(user=self.bob,application=self.app_b,
            kind="renewal",message="Bob private renewal",due_date=timezone.localdate())
        self.client.force_login(self.alice)
        response=self.client.get(reverse("galiel_reminders"))
        self.assertNotContains(response,"Bob private renewal")
        self.assertEqual(self.client.post(reverse("galiel_reminder_read",args=[alert.pk])).status_code,404)
        self.assertEqual(self.client.post(reverse("galiel_reminder_dismiss",args=[alert.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse("galiel_unread_count")).json()["unread"],0)

    def test_read_and_dismiss_own_alert(self):
        alert=Reminder.objects.create(user=self.alice,kind="other",message="Private update")
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(reverse("galiel_unread_count")).json()["unread"],1)
        self.assertEqual(self.client.post(reverse("galiel_reminder_read",args=[alert.pk])).status_code,302)
        self.assertEqual(self.client.get(reverse("galiel_unread_count")).json()["unread"],0)
        self.assertEqual(self.client.post(reverse("galiel_reminder_dismiss",args=[alert.pk])).status_code,302)
        self.assertFalse(Reminder.objects.filter(pk=alert.pk,dismissed=False).exists())

    def test_client_cannot_delete_another_clients_draft(self):
        self.client.force_login(self.alice)
        response=self.client.post(reverse("galiel_delete_draft",args=[self.app_b.pk]),
            {"confirm":self.app_b.number})
        self.assertEqual(response.status_code,404)
        self.assertTrue(ServiceApplication.objects.filter(pk=self.app_b.pk).exists())

    def test_submitted_application_is_immutable(self):
        self.app_a.status="submitted"
        self.app_a.save(update_fields=["status"])
        self.client.force_login(self.alice)
        self.assertEqual(self.client.post(reverse("galiel_delete_draft",args=[self.app_a.pk]),
            {"confirm":self.app_a.number}).status_code,403)
        self.assertTrue(ServiceApplication.objects.filter(pk=self.app_a.pk).exists())

    def test_delete_own_draft_requires_exact_confirmation(self):
        self.client.force_login(self.alice)
        url=reverse("galiel_delete_draft",args=[self.app_a.pk])
        self.assertContains(self.client.get(url),self.app_a.number)
        self.assertEqual(self.client.post(url,{"confirm":"wrong"}).status_code,403)
        self.assertTrue(ServiceApplication.objects.filter(pk=self.app_a.pk).exists())
        self.assertEqual(self.client.post(url,{"confirm":self.app_a.number}).status_code,302)
        self.assertFalse(ServiceApplication.objects.filter(pk=self.app_a.pk).exists())

    def test_private_documents_and_upload_validation(self):
        upload=SimpleUploadedFile("private.pdf",b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF",content_type="application/pdf")
        document=ApplicationDocument.objects.create(application=self.app_b,requirement=None,
            original_filename="private.pdf",file=upload,content_type="application/pdf",size=upload.size)
        self.client.force_login(self.alice)
        self.assertEqual(self.client.post(reverse("galiel_delete_draft_file",args=[self.app_b.pk,document.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse("application_download",args=[self.app_b.pk,document.pk])).status_code,404)
        self.assertTrue(ApplicationDocument.objects.filter(pk=document.pk).exists())

    def test_wizard_steps_do_not_show_other_clients_data(self):
        self.client.force_login(self.alice)
        for step in range(1,7):
            response=self.client.get(reverse("application_step",args=[self.app_b.pk,step]))
            self.assertEqual(response.status_code,404,step)
        for step in range(1,6):
            response=self.client.get(reverse("application_step",args=[self.app_a.pk,step]))
            self.assertIn(response.status_code,(200,302),step)

    def test_payment_hold(self):
        self.client.force_login(self.alice)
        response=self.client.post(reverse("application_checkout",args=[self.app_a.pk]))
        self.assertNotEqual(response.status_code,200)
        self.assertFalse(ServiceApplication.objects.get(pk=self.app_a.pk).payment_confirmed_at)

    def test_invoice_request_is_owner_only(self):
        self.client.force_login(self.alice)
        url=reverse("galiel_request_invoice",args=[self.app_b.pk])
        self.assertEqual(self.client.post(url,{"invoice_requested":"yes"}).status_code,404)
        url=reverse("galiel_request_invoice",args=[self.app_a.pk])
        self.assertEqual(self.client.post(url,{"invoice_requested":"yes"}).status_code,302)
        self.assertEqual(InvoiceRequest.objects.filter(application=self.app_a,user=self.alice).count(),1)

    def test_fiscal_data_and_deletion_request_are_private(self):
        self.client.force_login(self.alice)
        data={"rfc":"ABCD990101XYZ","razon_social":"Alice Enterprise","regimen_fiscal":"601",
              "uso_cfdi":"G03","invoice_email":"invoice-alice@example.test"}
        self.assertEqual(self.client.post(reverse("galiel_fiscal_profile"),data).status_code,302)
        self.assertEqual(FiscalProfile.objects.get(user=self.alice).rfc,"ABCD990101XYZ")
        self.client.force_login(self.bob)
        self.assertNotContains(self.client.get(reverse("galiel_fiscal_profile")),"Alice Enterprise")
        self.client.force_login(self.alice)
        self.assertEqual(self.client.post(reverse("galiel_request_account_deletion")).status_code,302)
        self.assertTrue(PortalTestUser.objects.filter(pk=self.alice.pk,is_active=True).exists())
        self.assertEqual(AccountDeletionRequest.objects.filter(user=self.alice,status="pending").count(),1)

    def test_help_processes_list_owner_only(self):
        self.client.force_login(self.alice)
        result=self.client.get(reverse("galiel_help_processes"))
        self.assertEqual(result.status_code,200)
        self.assertIn(self.app_a.number,str(result.json()))
        self.assertNotIn(self.app_b.number,str(result.json()))

    def test_staff_status_generates_alert(self):
        self.app_a.status="missing_documents"
        self.app_a.save(update_fields=["status"])
        self.assertTrue(Reminder.objects.filter(user=self.alice,application=self.app_a,kind="documents").exists())
        self.assertFalse(Reminder.objects.filter(user=self.bob,application=self.app_a).exists())
