from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import ServiceOffering, ServiceApplication, OfferingPriceResearch
from .workflow_views import _price_for


class PricingAndBrandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="theme-tester", password="ValidPassword321!",
            email="theme@example.com", first_name="Theme", last_name="Tester",
        )

    def test_all_19_offerings_have_research_audit(self):
        self.assertEqual(ServiceOffering.objects.filter(is_published=True).count(), 19)
        self.assertEqual(ServiceOffering.objects.exclude(price_research__isnull=False).count(), 0)
        self.assertEqual(OfferingPriceResearch.objects.filter(source_kind="government").count(), 19)

    def test_source_backed_starting_prices_are_flagged_as_provisional(self):
        expected = {
            "jal-gdl-giro-a": ("4175.00", "MXN"),
            "cdmx-bj-establecimiento": ("3500.00", "MXN"),
            "cdmx-cuauhtemoc-establecimiento": ("3500.00", "MXN"),
            "tx-notarization": ("40.00", "USD"),
            "tx-apostille": ("115.00", "USD"),
            "tx-translation": ("45.00", "USD"),
            "tx-entity-filing": ("450.00", "USD"),
            "fr-translation": ("59.00", "EUR"),
            "fr-apostille-legalization": ("80.00", "EUR"),
        }
        for slug, (amount, currency) in expected.items():
            offering = ServiceOffering.objects.get(service__slug=slug)
            self.assertEqual(str(offering.price), amount)
            self.assertEqual(offering.currency, currency)
            self.assertEqual(offering.price_type, "starting")
            self.assertTrue(offering.is_temporary_price)
            self.assertTrue(offering.pricing_review_required)
            self.assertTrue(offering.price_unit)
            self.assertIsNotNone(offering.estimated_min_business_days)
            self.assertIsNotNone(offering.estimated_max_business_days)

    def test_unverified_jurisdictions_remain_quote_required(self):
        offering = ServiceOffering.objects.get(service__slug="nl-monterrey-uso-suelo")
        self.assertEqual(offering.price_type, "quote")
        self.assertIsNone(offering.price)
        self.assertTrue(offering.pricing_review_required)

    def test_provisional_estimate_never_becomes_stripe_payable(self):
        offering = ServiceOffering.objects.get(service__slug="tx-apostille")
        app = ServiceApplication.objects.create(client=self.user, offering=offering)
        self.assertEqual(_price_for(app), (None, None, None))

    def test_service_api_exposes_research_disclaimer_without_fee_breakdown(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("catalog_api"), {"country": "US", "lang": "en"})
        self.assertEqual(response.status_code, 200)
        item = next(x for x in response.json()["offerings"] if x["code"] == "tx-apostille")
        self.assertEqual(item["price"], "115.00")
        self.assertTrue(item["is_temporary_price"])
        self.assertIn("final cost confirmed", item["estimated_price_note"])
        self.assertNotIn("service_fee_estimate", item)

    def test_marquee_is_css_only_and_links_to_filtered_catalog(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "galiel-marquee")
        self.assertContains(response, 'href="/services/?country=MX"')
        self.assertContains(response, 'href="/services/?country=US"')
        self.assertContains(response, 'href="/services/?country=FR"')
        self.assertContains(response, 'prefers-reduced-motion')

    def test_shared_galiel_design_is_used_in_client_pages(self):
        self.client.force_login(self.user)
        for endpoint in ("dashboard", "service_catalog", "profile", "messages_inbox"):
            response = self.client.get(reverse(endpoint))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "portal/galiel-design.css")
            self.assertContains(response, "portal/galiel-signature.svg")
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "portal/galiel-signature.svg")
