from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import CatalogCountry, CatalogRegion, CatalogMunicipality, CatalogService, ServiceOffering, ServiceRequirement


class CatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_user = User.objects.create_user(username="catalog-client", password="test_password_123", email="client@example.com")
        cls.manager = User.objects.create_superuser(username="catalog-manager", password="test_password_123", email="manager@example.com")
        cls.country = CatalogCountry.objects.get(code="MX")
        cls.region = CatalogRegion.objects.get(country=cls.country, slug="nuevo-leon")
        cls.city = CatalogMunicipality.objects.get(region=cls.region, slug="san-pedro-garza-garcia")
        cls.service = CatalogService.objects.create(slug="permiso", title_en="Business permit", title_es="Permiso de funcionamiento", title_fr="Permis d'exploitation")
        cls.offering = ServiceOffering.objects.create(service=cls.service, country=cls.country, region=cls.region, municipality=cls.city, price_type="fixed", price=Decimal("1250.00"), currency="MXN", estimated_min_business_days=5, estimated_max_business_days=10, is_published=True)
        ServiceRequirement.objects.create(offering=cls.offering, kind="document", label_en="Proof of address", label_es="Comprobante de domicilio", label_fr="Justificatif de domicile")

    def test_catalog_requires_login(self):
        self.assertEqual(self.client.get(reverse("service_catalog")).status_code, 302)

    def test_filters_and_currency_and_estimate(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("catalog_api"), {
            "country": "MX", "region": str(self.region.pk),
            "municipality": str(self.city.pk),
        })
        self.assertEqual(response.status_code, 200)
        items = response.json()["offerings"]
        selected = next(item for item in items if item["service"] == "Business permit")
        self.assertEqual(selected["currency"], "MXN")
        self.assertEqual(selected["price"], "1250.00")
        self.assertEqual(selected["estimated_min_business_days"], 5)
        self.assertEqual(selected["estimated_max_business_days"], 10)
        self.assertEqual(selected["location"], "San Pedro Garza García")
        response = self.client.get(reverse("catalog_api"), {"country": "FR"})
        self.assertNotIn("Business permit", [
            item["service"] for item in response.json()["offerings"]
        ])

    def test_language_selection(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("catalog_api"), {"lang": "es"})
        self.assertIn("Permiso de funcionamiento", [
            item["service"] for item in response.json()["offerings"]
        ])
        response = self.client.get(reverse("catalog_api"), {"lang": "fr"})
        self.assertIn("Permis d'exploitation", [
            item["service"] for item in response.json()["offerings"]
        ])

    def test_unpublished_service_is_hidden(self):
        self.offering.is_published = False
        self.offering.save(update_fields=["is_published"])
        self.client.force_login(self.client_user)
        self.assertNotContains(self.client.get(reverse("service_catalog")), "Business permit")

    def test_location_validation(self):
        other = CatalogCountry.objects.get(code="FR")
        self.offering.country = other
        with self.assertRaises(ValidationError):
            self.offering.full_clean()

    def test_price_validation(self):
        self.offering.price = None
        with self.assertRaises(ValidationError):
            self.offering.full_clean()

    def test_manager_admin_requires_staff(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("admin:portal_serviceoffering_changelist"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.manager)
        response = self.client.get(reverse("admin:portal_serviceoffering_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_existing_message_workflow_unchanged(self):
        self.client.force_login(self.client_user)
        resp = self.client.get(reverse("messages_inbox"))
        self.assertEqual(resp.status_code, 200)

    def test_offering_prefills_inquiry_subject(self):
        self.client.force_login(self.client_user)
        resp = self.client.get(reverse("messages_inbox"), {"offering": self.offering.pk})
        self.assertContains(resp, "Inquiry: Business permit")
