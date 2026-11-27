"""Display-only approved Galiel estimates. No charge or payment is initiated."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from .fee_note_translations import TRANSLATIONS

CENT = Decimal("0.01")
MAX_AREA = Decimal("100000000")


def clean_area(value):
    if value in (None, ""):
        return None
    try:
        area = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Enter a valid area in square meters.")
    if not area.is_finite() or area <= 0 or area > MAX_AREA:
        raise ValueError("Area must be positive and within the allowed range.")
    return area


def estimate(offering, area=None):
    """Return pretax Decimal estimate or None; never infer unknown area."""
    if offering.base_fee is None:
        return None
    base = offering.base_fee
    if offering.price_type == "fixed":
        return base.quantize(CENT, rounding=ROUND_HALF_UP)
    if offering.price_type != "per_m2":
        return None
    sqm = clean_area(area)
    if sqm is None or offering.included_m2 is None or offering.per_extra_m2 is None:
        return None
    return (base + max(Decimal("0"), sqm - offering.included_m2) *
            offering.per_extra_m2).quantize(CENT, rounding=ROUND_HALF_UP)


def fee_note(offering, language="en"):
    """Return the exact approved note, or its reviewed EN/ES/FR translation."""
    note = (offering.fee_covers or "").strip()
    if language == "es" and note in TRANSLATIONS:
        return TRANSLATIONS[note][0]
    if language == "fr" and note in TRANSLATIONS:
        return TRANSLATIONS[note][1]
    return note
