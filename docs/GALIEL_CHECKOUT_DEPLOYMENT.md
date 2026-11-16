# Galiel guided checkout — deployment and acceptance checklist

## Scope and safety boundaries

The six-stage flow creates a **draft** before charging anything. Drafts resume from My processes. Intake fields and required-document checklists are configured in Django Admin per service offering. Files are stored in private Django MEDIA_ROOT with ownership checks. Client payments are exclusively via Stripe-hosted Checkout. A user redirect to the success page cannot mark payment successful; a valid Stripe-signed `checkout.session.completed` webhook must report `payment_status=paid`, matching application/session ID, currency and amount.

A service with `price_type=quote` or a starting price without a configured deposit uses **Request a quote**. Staff can set `quoted_amount` (the complete payable total, including applicable taxes) and change the case status to `Quoted` in Admin; this triggers an email. Client can then open Step 5 via My processes to pay. No agency decision or deadline is guaranteed.

**Do not enter test or real card numbers into Galiel:** Stripe collects all card information on Stripe's page.

An itemized payment confirmation is available under Invoices & payments. It is **not a tax invoice or CFDI**. Staff can upload an applicable tax invoice as a private case file and mark `is_invoice`. Automatic country-specific tax invoice issuance, government fees and accounting integrations require a separate reviewed implementation.

No real customer payments should be enabled until Stripe is configured, test payments/webhooks are verified, tax rates are reviewed, and staff have checked service requirements.

## HostGator

On the HostGator shared server, Git fetch may fail under the 25-process limit. The previous deployment used GitHub's main ZIP archive, extracted under `~/galiel-backups`, and carefully copied only changed application files.

Use a new dated ZIP and backup; **never overwrite**:

- `~/galiel/db.sqlite3`
- `~/galiel/.htaccess`
- `~/galiel/galiel-v*.fcgi`
- `~/galiel-private-files`
- host-specific environment configuration, credentials or secret keys
- `.git/`

The new files to copy are:

- `portal/models.py`
- `portal/migrations/0010_service_checkout.py`
- `portal/views.py`
- `portal/workflow_views.py`
- `portal/admin.py`
- `portal/urls.py`
- `portal/templates/portal/service_intake.html`
- `portal/templates/portal/application_step.html`
- `portal/templates/portal/application_track.html`
- `portal/templates/portal/application_receipt.html`
- `portal/templates/portal/dashboard.html`
- `portal/templates/portal/messages.html`
- `portal/templates/portal/conversation_detail.html`
- `portal/tests_unified_catalog.py`
- `portal/tests_checkout.py`
- `requirements.txt`

Backup SQLite using `python -m sqlite3` backup if available or stop writing briefly for a consistent file copy; ensure WAL/shm are included when active. Keep the previous FastCGI entry point and `.htaccess` to roll back.

Once files are copied, install dependencies in the **same Python environment used by FastCGI** using `python -m pip install -r requirements.txt`, then run:

```sh
cd ~/galiel
python manage.py check
python manage.py migrate
python manage.py test portal.tests_checkout portal.tests_unified_catalog
```

After checks succeed, copy `galiel-v8.fcgi` to `galiel-v9.fcgi` and back up `.htaccess`. Switch only Galiel's rewrite targets from v8 to v9. Existing `^services/(.*)$` already covers the new paths, including the payment webhook; add no duplicate route unless the rewrite does not match.

### Stripe configuration (server-side only)

Set environment variables in the FastCGI process environment; **never commit or paste secret keys into the repo/chat**:

- `GALIEL_STRIPE_SECRET_KEY`: Stripe API secret key (start with test mode).
- `GALIEL_STRIPE_WEBHOOK_SECRET`: the signing secret from the webhook endpoint (test mode).
- `DJANGO_SECRET_KEY`: a unique production secret.
- `DJANGO_DEBUG=False`: ensure debug pages are off.
- Production SMTP settings for confirmation and status emails.

Stripe webhook URL: `https://galiel.wardenclyffefirm.com/services/payment/webhook/`
Subscribe to the `checkout.session.completed` event. Configure the webhook secret from the **matching endpoint and mode**. Stripe sends a signature header; the endpoint rejects unsigned/mismatched payloads. Keep mode and webhooks consistent.

Stripe Checkout handles eligible 3-D Secure flows on Stripe's infrastructure. Do not store credit-card numbers, CVV or card data in Galiel.

### Acceptance tests before charging

1. Create a draft and check that it appears under My processes; return and resume.
2. Add one required question and a required document to an offering in Admin; verify Step 2 blocks an empty answer and Step 4 blocks a missing file.
3. Upload valid PDF/JPG/PNG; try replacing/deleting, oversized files and forged image extensions; verify files are private and that other users receive 404.
4. Use a fixed-price test service with the applicable configured tax and verify line-item math.
5. Use a quote-only service, request a quote, have staff provide an approved quoted amount, and verify that Pay now goes straight to Step 5.
6. Complete Stripe test payment with authentication when prompted; confirm that only a **signed paid webhook** changes case status and creates the email/thread/event/receipt.
7. Check failed/cancelled Stripe Checkout returns to Step 5 without marking the order paid.
8. Staff change status and request missing documents; verify client email, event timeline, file upload, finished deliverable, and issued tax-invoice attachment.
9. Verify branded emails arrive in the actual registered client's mailbox and do not expose another client's documents.
10. Verify the active worker is v9 and no other HostGator site was changed.

### Remaining production dependencies

- Billing entity/tax/IVA configuration per service and applicable jurisdiction
- Stripe account ownership, compliance and webhook access
- SMTP deliverability, background email retry mechanism
- Government/third-party fees and legal disclosures
- Formal tax invoice/CFDI issuance integrations where required
- Backups, file retention policy, malware scanning and upload controls before high-volume document handling
- End-to-end tests against the real HostGator FastCGI and Stripe test endpoint

The code intentionally blocks card checkout when Stripe credentials/webhook secret are missing and avoids making up fees, tax or government processing times.
