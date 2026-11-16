from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    CatalogCountry, CatalogRegion, CatalogMunicipality,
    CatalogService, ServiceOffering, ClientConversation, ClientMessage,
)


class UnifiedCatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="catalog-check@example.com", email="catalog-check@example.com", password="StrongPass123"
        )

    def test_seed_has_homepage_regions_and_19_published_services(self):
        self.assertEqual(CatalogCountry.objects.count(), 3)
        self.assertEqual(CatalogRegion.objects.filter(country_id="MX").count(), 6)
        self.assertEqual(CatalogMunicipality.objects.filter(region__country_id="MX").count(), 8)
        self.assertEqual(ServiceOffering.objects.filter(is_published=True).count(), 19)

    def test_homepage_and_catalog_share_published_data(self):
        homepage = self.client.get(reverse("home"))
        self.assertContains(homepage, "Nuevo León")
        self.assertContains(homepage, "Notarization assistance")
        self.assertContains(homepage, "Business operating permit")
        self.client.force_login(self.user)
        catalog = self.client.get(reverse("service_catalog"))
        self.assertEqual(catalog.status_code, 200)
        self.assertContains(catalog, "services/api/catalog/")
        self.assertContains(catalog, "Loading services")
        self.assertContains(catalog, "Unable to load services")

    def test_api_lists_regions_municipalities_and_all_service_cards(self):
        base = reverse("catalog_api")
        all_items = self.client.get(base).json()
        self.assertEqual(len(all_items["offerings"]), 19)
        mx = self.client.get(base, {"country": "MX"}).json()
        self.assertEqual(len(mx["regions"]), 6)
        self.assertEqual(len(mx["offerings"]), 12)
        nl_id = CatalogRegion.objects.get(country_id="MX", slug="nuevo-leon").pk
        nl = self.client.get(base, {"country": "MX", "region": nl_id}).json()
        self.assertEqual(len(nl["municipalities"]), 2)
        self.assertEqual(len(nl["offerings"]), 5)
        sp_id = CatalogMunicipality.objects.get(region_id=nl_id, slug="san-pedro-garza-garcia").pk
        sp = self.client.get(base, {"country": "MX", "region": nl_id, "municipality": sp_id}).json()
        self.assertEqual(len(sp["offerings"]), 2)
        self.assertIn("start_url", sp["offerings"][0])
        self.assertEqual(sp["offerings"][0]["price_type"], "quote")
        self.assertIsNone(sp["offerings"][0]["price"])
        self.assertIsNone(sp["offerings"][0]["estimated_min_business_days"])

    def test_all_region_and_municipality_are_not_exclusionary(self):
        base = reverse("catalog_api")
        response = self.client.get(base, {"country": "MX", "region": "", "municipality": ""})
        self.assertEqual(len(response.json()["offerings"]), 12)
        self.assertEqual(self.client.get(base, {"region": "bad"}).status_code, 400)

    def test_api_returns_translations(self):
        api = reverse("catalog_api")
        for lang, label in [("en", "Business operating permit"), ("es", "Licencia de funcionamiento"), ("fr", "Permis d'exploitation")]:
            response = self.client.get(api, {"country": "MX", "lang": lang})
            self.assertIn(label, [row["service"] for row in response.json()["offerings"]])

    def test_unpublished_offering_disappears_from_both_home_and_api(self):
        offering = ServiceOffering.objects.get(service__slug="tx-apostille")
        offering.is_published = False
        offering.save(update_fields=["is_published"])
        self.assertNotContains(self.client.get(reverse("home")), "Apostille coordination")
        self.assertNotIn("tx-apostille", [
            o["code"] for o in self.client.get(reverse("catalog_api")).json()["offerings"]
        ])

    def test_start_service_requires_login_and_opens_real_intake(self):
        offering = ServiceOffering.objects.get(service__slug="nl-monterrey-uso-suelo")
        url = reverse("service_intake", args=[offering.pk])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.user)
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Start service inquiry")
        result = self.client.post(url, {"details": "Please help me with the property paperwork."})
        thread = ClientConversation.objects.get()
        self.assertEqual(thread.client, self.user)
        self.assertContains(self.client.get(reverse("conversation_detail", args=[thread.pk])), "property paperwork")
        self.assertEqual(ClientMessage.objects.count(), 1)
        self.assertEqual(result.status_code, 302)

    def test_no_intake_for_unpublished_offering(self):
        offering = ServiceOffering.objects.get(service__slug="nl-monterrey-uso-suelo")
        offering.is_published = False
        offering.save(update_fields=["is_published"])
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("service_intake", args=[offering.pk])).status_code, 404)
