from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from portal.models import ServiceApplication, ServiceOffering


class XRayPresenterTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client_user = User.objects.create_user(
            username="xray-client@example.test", email="xray-client@example.test",
            password="TestPass123!Strong",
        )
        self.staff = User.objects.create_superuser(
            username="xray-admin@example.test", email="xray-admin@example.test",
            password="TestPass123!Strong",
        )

    def test_dashboard_and_staff_admin_include_opt_in_script(self):
        self.client.force_login(self.client_user)
        page = self.client.get(reverse("dashboard"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "portal/galiel-xray.js")
        self.assertContains(page, "portal/galiel-xray.css")
        self.client.force_login(self.staff)
        page = self.client.get(reverse("admin:index"))
        self.assertEqual(page.status_code, 200)
        offering = ServiceOffering.objects.first()
        case = ServiceApplication.objects.create(
            client=self.client_user, offering=offering, status="draft", step=3,
            currency="MXN", service_title=offering.service.title_en)
        page = self.client.get(reverse("admin:portal_serviceapplication_change", args=[case.pk]))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "portal/galiel-xray.js")
        self.assertContains(page, "portal/galiel-xray.css")

    def test_auth_pages_include_same_presentation_loader(self):
        for name in ("login", "register"):
            page = self.client.get(reverse(name))
            self.assertEqual(page.status_code, 200)
            self.assertContains(page, "portal/galiel-xray.js")
            self.assertContains(page, "portal/galiel-xray.css")
