# Operations release: HostGator test compatibility and payment hold

These are the reviewed follow-up corrections after the first isolated dry-run stopped (82 tests; 4 obsolete assertions and an initial-data collision).

- `galiel_ops/tests.py`: use `CatalogCountry.objects.get_or_create(code="MX", ...)` because `portal.0008_seed_countries` already adds MX. Never insert a duplicate seeded row in a TestCase.
- The package's `prepare.py`: insert the account-deletion section at the final content-block anchor `\n{% endblock %}`, not the title's inline `{% endblock %}`.
- The package's `prepare.py`: the live Apache rules have distinct FastCGI suffixes. Require a capture-based `services/(.*)` rewrite and insert an independently captured `galiel-v9.fcgi/$1 [QSA,L]` rule for operations URLs. Preserve every existing rule. A non-matching rewrite fails closed.
- The package's `ops_deploy.sh`: use `\${testdir}-media` outside the test application root, as required by production's private-media safety check.
- `galiel_ops/test_support/checkout_hold_test_patch.py` is an **isolated-test-only** update to four outdated assertions in the copied `portal/tests_checkout.py`. It asserts the 403 checkout block and the Step 5 payment-hold message. It never writes to production `portal/tests_checkout.py` and is excluded from the deploy candidate.
- The package keeps test logs and exits nonzero unless Django explicitly reports both `Ran N tests` and `OK`.

The isolated suite uses the exact production `portal` snapshot including migrations only through `0011_contact_leads`, plus this pinned operations app. No `portal.0012_pricing_research` migration is included. No payment integration, approved fee import, or relocation is authorized.

All production changes remain pending an actual successful HostGator dry-run. Never report tests green based on compilation or synthetic fixtures.
