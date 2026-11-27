# Galiel Dec 7 — controlled release playbook (NOT YET EXECUTED)

**No deployment without current production access, an inspected Apache .htaccess and the complete approved fee workbook.**

## Release sequencing
A. X-Ray presentation tour (presentation feature, no schema migration).
B. Pricing display and imported fees (schema migration and data import).
Do not conflate the two go/no-go decisions.

## Pin and verify the reviewed source
```bash
cd ~/galiel
git fetch origin
git rev-parse HEAD
# Pin to the SHA that passed GitHub Actions and the final acceptance review.
RELEASE_SHA="REPLACE_WITH_REVIEWED_FULL_40_CHARACTER_SHA"
test "$(git rev-parse HEAD)" = "$RELEASE_SHA" || exit 1
python manage.py check
python manage.py showmigrations portal galiel_ops
```

The production baseline must show `portal.0011_contact_leads` and `galiel_ops.0001_initial` applied, and `portal.0012_approved_fee_fields` unapplied. Stop if history differs or `0012_pricing_research` appears anywhere in the active graph.

## Preview, hash, and review SQL before migration
```bash
python manage.py migrate portal 0012_approved_fee_fields --plan > /tmp/galiel-0012-plan.txt
cat /tmp/galiel-0012-plan.txt
sha256sum /tmp/galiel-0012-plan.txt
python manage.py sqlmigrate portal 0012_approved_fee_fields
python manage.py makemigrations --check --dry-run
```
Record the verified value as `PLAN_SHA256`. Re-run the plan immediately before migration and confirm the hash is identical. If there are unexpected migrations, **stop**.

## Read-only fee reconciliation (must match ALL 107)
```bash
python manage.py import_approved_fees \
  "$HOME/galiel-private-files/Galiel_Approved_Fees_20261116.xlsx" \
  --expected-rows 107 > /tmp/galiel-fees-dry-run.txt
cat /tmp/galiel-fees-dry-run.txt
```
Review every row. The approved XLSX has SHA256 `24c954415dafdd20b17a012f6d8cc5e12a011f753729bcfc9672e8adb9d20629`; the importer refuses `--apply` for any other workbook bytes. No service is created, and no missing or ambiguous match can be guessed. Import is **blocked until the output is 107 MATCH / 0 blockers**. There is no need to continue to backup/migrate if the match report is incomplete.

## Safe backup
Use SQLite online backup API rather than copying a potentially live DB. Obtain `DATABASES['default']['NAME']` from the production settings without printing credentials. Write a timestamped backup under a private, non-web-served folder with permissions 0600. Verify integrity and perform an isolated restore drill. Back up the relevant code, static files, .htaccess, FastCGI entry, and private upload references as well. Never store a private DB in GitHub.

## Controlled apply only after all gates pass
```bash
# Confirm PLAN_SHA256 again here.
python manage.py migrate portal 0012_approved_fee_fields
python manage.py import_approved_fees \
  "$HOME/galiel-private-files/Galiel_Approved_Fees_20261116.xlsx" --expected-rows 107 --apply
python manage.py test portal galiel_ops --noinput
python manage.py check
```
The import runs in a single database transaction. The new base_fee fields are display-only; the legacy `price` is preserved and `application_checkout` remains hard-blocked.

## FastCGI and live checks
After the approved code swap, refresh the production FastCGI process using the site's **existing, verified** refresh mechanism. Inspect .htaccess route allowlisting before adding any X-Ray route. Confirm health and content with a browser User-Agent:
```bash
curl -sS -I -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36' https://galiel.wardenclyffefirm.com/login/
curl -sS -I -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36' https://galiel.wardenclyffefirm.com/static/portal/galiel-xray.js
```
Check logged-in catalog, wizard, case tracking, three languages, per-m² changes, forbidden cross-client access, no open checkout, mobile, keyboard and reduced motion in a real browser.

## Rollback
- X-Ray-only: revert the reviewed JS/template changes, restore assets, refresh FastCGI, run live checks.
- Pricing before new customer writes: revert import data to the pre-import snapshot and reverse `portal.0012_approved_fee_fields` to `portal.0011_contact_leads` in a supervised maintenance window. Verify SQLite restore drill first.
- **Never** blindly restore a stale DB over later customer writes. Preserve and reconcile any intervening records; DB rollback is deliberately manual.
- If schema rollback cannot safely preserve post-deployment data, disable the pricing feature and retain schema pending a data-preserving repair instead.
