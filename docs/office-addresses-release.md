# Galiel — Office contact-information-only release (2026-11-18)

Production static homepage: /home2/gfrancossh/galiel/index.html served by Apache at /. Django portal/templates/portal/home.html is a fallback, not the live homepage.

Pinned initial live index SHA-256: 1faa8ca0cb44bebdce2334c28f42664d1341d53316395a71d9352b26930a624e

## Offices in required order

1. Texas office — 1209 S. 10th St., Suite A, Unit 583; McAllen, TX 78501
2. California office — 849 N Lake Ave, Unit 254; Pasadena, CA 91104
3. Mexico office — Manuel Gómez Morín No. 350, PB6A-3; Valle del Campestre; San Pedro Garza García, Nuevo León 66265, Mexico

Footer under existing email: McAllen, TX · Pasadena, CA · San Pedro Garza García, N.L.

| English | Español | Français |
| --- | --- | --- |
| Texas office | Oficina en Texas | Bureau au Texas |
| California office | Oficina en California | Bureau en Californie |
| Mexico office | Oficina en México | Bureau au Mexique |

Django fallback template updates are committed on this branch. The Apache-served index.html remains production-owned and will only be patched by a guarded local deploy utility after the full live source SHA matches. Exact anchors, unified diff, timestamped review, review plan hash, backups, restore and HTTP checks are mandatory. Existing email and phone are preserved. No database, model, migration, secret, FastCGI or Apache routing changes.

## Checkout regression test-only update

The operational HostGator checkout payment hold produces HTTP 403; the four historical checkout expectations are stale. This release includes a third **test-only** file, `portal/tests_checkout.py`, byte-for-byte from the verified GitHub-main commit `9b07cd396210cd82054b78e407d5298eea53eb90` (Git blob SHA-1 `241de652bfc3c1415f369ad32725e11b10cc393e`). The deployment script downloads the immutable blob, verifies the Git object hash before preparing the diff, and backs up / installs / rolls back this test file alongside the two approved HTML files. If GitHub is unreachable, dry-run fails without changing live files. No payment implementation changes.

Live Django tests are run in an isolated source tree with the candidate test module and a no-op environment loader, using a private-media test root outside the application tree. Production files remain unchanged during dry-run. A timestamped review directory includes PLAN.json, DIFF.patch, TESTS.log and a PLAN_SHA256 gate required again at apply.
