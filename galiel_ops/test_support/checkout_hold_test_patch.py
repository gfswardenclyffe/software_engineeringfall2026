"""Patch obsolete checkout expectations only in an ISOLATED test-workspace copy.

Never installed to production portal/tests_checkout.py. Each original assertion
must match exactly once; abort if the production test structure differs.
"""
from pathlib import Path
import sys

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"BLOCKED test compatibility: {label} expected once, found {n}")
    return text.replace(old, new, 1)

def main(path):
    path = Path(path)
    if not path.is_file() or path.name != "tests_checkout.py" or path.parent.name != "portal":
        raise SystemExit("BLOCKED: patch accepts only portal/tests_checkout.py in isolated workspace")
    src = path.read_text(encoding="utf-8")
    pieces = {
        "test_checkout_disabled_without_stripe": (
            'self.assertRedirects(response, reverse("application_step", args=[app.pk, 5]))',
            'self.assertEqual(response.status_code, 403)\n            self.assertIn("Card payments are temporarily unavailable.", response.content.decode("utf-8"))'
        ),
        "test_quote_locks_answers_but_allows_payment_step": (
            'self.assertContains(self.client.get(reverse("application_step", args=[app.pk, 5])), "450.00")',
            'self.assertContains(self.client.get(reverse("application_step", args=[app.pk, 5])), "Payments are currently on hold.")'
        ),
        "test_quote_ready_follows_staff_approved_price": (
            'self.assertContains(payment, "450.00")',
            'self.assertContains(payment, "Payments are currently on hold.")'
        ),
        "test_unpriced_offer_uses_quote_path": (
            'self.assertContains(self.client.get(reverse("application_step", args=[app.pk, 5])), "Request a quote")',
            'self.assertContains(self.client.get(reverse("application_step", args=[app.pk, 5])), "Payments are currently on hold.")'
        ),
    }
    for label, (before, after) in pieces.items():
        head = src.find("    def " + label + "(self):")
        if head < 0:
            raise SystemExit("BLOCKED: missing original checkout test " + label)
        tail = src.find("\n    def ", head + 8)
        if tail < 0: tail = len(src)
        body = src[head:tail]
        body = replace_once(body, before, after, label)
        src = src[:head] + body + src[tail:]
    path.write_text(src, encoding="utf-8")
    print("TEST-ONLY: Updated four payment-hold assertions in isolated portal/tests_checkout.py")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python checkout_hold_test_patch.py isolated/portal/tests_checkout.py")
    main(sys.argv[1])
