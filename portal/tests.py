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
