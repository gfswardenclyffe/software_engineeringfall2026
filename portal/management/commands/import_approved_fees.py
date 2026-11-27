"""Import a reviewed 107-row XLSX into EXISTING offerings only.

Default is a zero-write row-by-row dry-run. --apply must be deliberately
requested after a clean dry run. Any unmatched, duplicate, or invalid row
aborts the entire write transaction.
"""
import unicodedata
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from portal.models import ServiceOffering

HEADERS = ("ID", "Country", "State / region", "Municipality", "Service",
           "Base fee", "Currency", "Pricing", "Included m²", "Per extra m²", "Fee covers")
COUNTRIES = {"mexico": "MX", "united states": "US", "france": "FR"}


def norm(value):
    text = unicodedata.normalize("NFKD", str(value or "").strip())
    return " ".join("".join(ch for ch in text if not unicodedata.combining(ch)).casefold().split())


def parse_money(value, name):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{name} must be numeric")
    if not result.is_finite() or result < 0 or result.as_tuple().exponent < -2:
        raise ValueError(f"{name} must be nonnegative, finite, and have at most 2 decimals")
    return result


def matching_offerings(row, offerings):
    code = COUNTRIES.get(norm(row[1]))
    if not code:
        return []
    region = norm(row[2])
    municipality = norm(row[3])
    service = norm(row[4])
    # Exact normalized label or existing service slug only; no approximate matching.
    return [o for o in offerings if o.country_id == code
            and norm(o.region.name_en if o.region else "") == region
            and norm(o.municipality.name_en if o.municipality else "") == municipality
            and (service in (norm(o.service.title_en), norm(o.service.title_es),
                             norm(o.service.title_fr), norm(o.service.slug)))]


class Command(BaseCommand):
    help = "Row-by-row approved fee match report; dry-run by default."

    def add_arguments(self, parser):
        parser.add_argument("workbook", help="Approved Galiel .xlsx path")
        parser.add_argument("--apply", action="store_true", help="Apply ONLY if all rows match uniquely")
        parser.add_argument("--expected-rows", type=int, default=107)

    def handle(self, *args, **opts):
        try:
            from openpyxl import load_workbook
        except ImportError as exc:
            raise CommandError("Install the pinned openpyxl dependency first") from exc
        try:
            wb = load_workbook(opts["workbook"], read_only=True, data_only=True)
            ws = wb["Fees"]
            rows = list(ws.values)
        except (OSError, KeyError, ValueError) as exc:
            raise CommandError(f"Cannot load the approved Fees sheet: {exc}") from exc
        if tuple(rows[0]) != HEADERS:
            raise CommandError("Workbook headers differ from the approved 11-column schema.")
        data = rows[1:]
        if len(data) != opts["expected_rows"]:
            raise CommandError(f"Expected {opts['expected_rows']} fee rows; got {len(data)}.")
        offerings = list(ServiceOffering.objects.select_related("service", "country", "region", "municipality"))
        review = []
        seen_ids, seen_offerings = set(), set()
        problems = 0
        for n, row in enumerate(data, start=2):
            status, target, details = "MATCH", None, ""
            try:
                if len(row) != 11 or not row[0]:
                    raise ValueError("Incomplete row/ID")
                if row[0] in seen_ids:
                    raise ValueError("Duplicate spreadsheet ID")
                seen_ids.add(row[0])
                pricing = {"flat": "fixed", "per_m2": "per_m2"}.get(row[7])
                if not pricing:
                    raise ValueError("Unsupported pricing type")
                base = parse_money(row[5], "Base fee")
                extra = parse_money(row[9], "Per extra m²") if pricing == "per_m2" else None
                included = parse_money(row[8], "Included m²") if pricing == "per_m2" else None
                if pricing == "per_m2" and included <= 0:
                    raise ValueError("Included m² must be positive")
                if row[6] not in ("MXN", "USD", "EUR"):
                    raise ValueError("Unsupported currency")
                matches = matching_offerings(row, offerings)
                if len(matches) != 1:
                    status = "MISSING" if not matches else "AMBIGUOUS"
                    details = f"{len(matches)} exact matches"
                else:
                    target = matches[0]
                    if target.pk in seen_offerings:
                        raise ValueError("Two rows target the same ServiceOffering")
                    seen_offerings.add(target.pk)
                    details = f"offering={target.pk}"
            except (ValueError, TypeError) as exc:
                status, details = "INVALID", str(exc)
            if status != "MATCH":
                problems += 1
            review.append((n, row, status, target, details))
            self.stdout.write(f"row={n} id={row[0]!s} location={row[1]!s}/{row[2]!s}/{row[3]!s} "
                              f"service={row[4]!s} status={status} {details}")
        self.stdout.write(f"RESULT: {len(review)} rows, {len(review)-problems} unique matches, {problems} blockers")
        if not opts["apply"]:
            self.stdout.write("DRY RUN: no writes made")
            return
        if problems:
            raise CommandError("Import refused: all rows must have one unambiguous, reviewed match.")
        with transaction.atomic():
            for _, row, _, target, _ in review:
                target.base_fee = parse_money(row[5], "Base fee")
                target.price_type = "fixed" if row[7] == "flat" else "per_m2"
                target.included_m2 = parse_money(row[8], "Included m²") if row[7] == "per_m2" else None
                target.per_extra_m2 = parse_money(row[9], "Per extra m²") if row[7] == "per_m2" else None
                target.fee_covers = str(row[10] or "")
                target.currency = row[6]
                # Keep payment price NULL: approved fees are DISPLAY ONLY.
                target.price = None
                target.save(update_fields=["base_fee", "price_type", "included_m2",
                                           "per_extra_m2", "fee_covers", "currency", "price", "updated_at"])
        self.stdout.write(self.style.SUCCESS(f"APPLIED {len(review)} approved fees; checkout remains on hold."))
