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
        self.assertContains(response, "Licencia / permiso de funcionamiento")
        self.assertContains(response, "Apostille coordination")

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
        self.assertContains(dashboard, "View client messages")
        messages_page = self.client.get(reverse("messages_inbox"), {"service": "tx-apostille"})
        self.assertNotContains(messages_page, "New message to Wardenclyffe")
