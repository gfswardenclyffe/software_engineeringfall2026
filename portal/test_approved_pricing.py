from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook

from .models import CatalogCountry, CatalogRegion, CatalogMunicipality, CatalogService, ServiceOffering
from .pricing import estimate, clean_area


class ApprovedPricingTests(TestCase):
    def setUp(self):
        self.country, _ = CatalogCountry.objects.get_or_create(
            code="MX", defaults={"name_en": "Mexico", "name_es": "México", "name_fr": "Mexique"})
        self.region, _ = CatalogRegion.objects.get_or_create(
            country=self.country, slug="nuevo-leon",
            defaults={"name_en": "Nuevo León", "name_es": "Nuevo León", "name_fr": "Nuevo León"})
        self.city, _ = CatalogMunicipality.objects.get_or_create(
            region=self.region, slug="monterrey",
            defaults={"name_en": "Monterrey", "name_es": "Monterrey", "name_fr": "Monterrey"})
        self.service, _ = CatalogService.objects.get_or_create(
            slug="test-fee-licence",
            defaults={"title_en": "Business licence", "title_es": "Licencia empresarial",
                      "title_fr": "Licence d'exploitation"})
        self.offering = ServiceOffering.objects.create(
            service=self.service, country=self.country, region=self.region, municipality=self.city,
            price_type="fixed", price=None, base_fee=Decimal("4500.00"), currency="MXN",
            fee_covers="Fee + IVA; derechos paid to authority", is_published=True)

    def test_fixed_price(self):
        self.assertEqual(estimate(self.offering), Decimal("4500.00"))

    def test_per_m2_included_and_extra(self):
        self.offering.price_type = "per_m2"
        self.offering.included_m2 = Decimal("100.00")
        self.offering.per_extra_m2 = Decimal("10.00")
        self.assertEqual(estimate(self.offering, "80"), Decimal("4500.00"))
        self.assertEqual(estimate(self.offering, "125.5"), Decimal("4755.00"))
        self.assertIsNone(estimate(self.offering))
        for value in ("-1", "NaN", "Infinity", "0"):
            with self.assertRaises(ValueError):
                clean_area(value)

    def test_catalog_display_is_not_payable(self):
        response = self.client.get(reverse("catalog_api"))
        self.assertEqual(response.status_code, 200)
        candidates = [x for x in response.json()["offerings"] if x["id"] == self.offering.pk]
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["base_fee"], "4500.00")
        self.assertTrue(candidates[0]["fee_covers"])

    def test_unmatched_import_does_not_write(self):
        from tempfile import NamedTemporaryFile
        from pathlib import Path
        from .management.commands.import_approved_fees import HEADERS
        book = Workbook()
        sheet = book.active
        sheet.title = "Fees"
        sheet.append(HEADERS)
        sheet.append(["SVC-001", "Mexico", "Nuevo León", "Monterrey",
                      "Service that does not exist", 3000, "MXN", "flat", None, None, "Fee + IVA"])
        with NamedTemporaryFile(suffix=".xlsx") as tmp:
            book.save(tmp.name)
            out = StringIO()
            call_command("import_approved_fees", tmp.name, expected_rows=1, stdout=out)
            self.assertIn("MISSING", out.getvalue())
            self.assertIn("DRY RUN", out.getvalue())
            with self.assertRaises(CommandError):
                call_command("import_approved_fees", tmp.name, expected_rows=1, apply=True,
                             stdout=StringIO())
        self.offering.refresh_from_db()
        self.assertEqual(self.offering.base_fee, Decimal("4500.00"))
