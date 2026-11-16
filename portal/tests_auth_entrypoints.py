"""Authenticated/anonymous account entrypoint regression coverage."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountEntrypointsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="already-logged-in@example.test",
            email="already-logged-in@example.test",
            password="RegressionPassword123!",
            first_name="Alex",
            last_name="Client",
        )

    def test_guest_create_account_link_opens_registration_form(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/register/"')
        registration = self.client.get(reverse("register"))
        self.assertEqual(registration.status_code, 200)
        self.assertContains(registration, "Create account and send confirmation")
        self.assertContains(registration, 'name="email"')

    def test_guest_service_query_preserved_on_create_account_link(self):
        response = self.client.get(reverse("login"), {"service": "nl-monterrey-uso-suelo"})
        self.assertContains(response, "/register/?service=nl-monterrey-uso-suelo")
        response = self.client.get(reverse("register"), {"service": "nl-monterrey-uso-suelo"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="email"')

    def test_signed_in_login_and_registration_show_account_state(self):
        self.client.force_login(self.user)
        for name in ("login", "register"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "You're already signed in")
            self.assertContains(response, "Alex Client")
            self.assertContains(response, "already-logged-in@example.test")
            self.assertContains(response, "Go to my workspace")
            self.assertContains(response, 'action="/logout/"')
            self.assertNotContains(response, 'name="password1"')
            self.assertNotContains(response, 'name="password2"')

    def test_signed_in_post_does_not_create_account_or_log_out(self):
        self.client.force_login(self.user)
        count = User.objects.count()
        response = self.client.post(reverse("register"), {"email": "someone@example.test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), count)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        response = self.client.post(reverse("login"), {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_sign_out_requires_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
