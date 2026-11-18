# Galiel — production client portal requirements

Scope: news, client reminders, client-owned draft controls, account-deletion requests, fiscal invoicing requests, scripted help, privacy and daily operations. The public site represents an operating business; do not add course, classroom, mock, or demonstration terminology.

## Functional requirements
1. Staff publish localized EN/ES/FR announcements, filterable by category, hidden after expiration, newest first.
2. Clients see only their own reminders; staff can issue renewal reminders and automated reminders for document requests or quotations. Alerts support read/dismiss state and email delivery.
3. A daily idempotent management command delivers due-soon alerts; no secrets in cron output.
4. Clients may delete only their own draft applications after explicit confirmation; submitted, quoted, paid or completed applications cannot be deleted.
5. Clients may delete their own uploaded draft files; secure downloads and the owner predicate remain mandatory.
6. Account deletion creates a staff-review request; no immediate account removal.
7. The help widget is deterministic, bilingual/trilingual, and exposes no client data to anonymous visitors.
8. Fiscal information is optional and private; client invoice requests notify staff, not a tax-invoicing provider.
9. Daily backups use SQLite's backup API and retain 14 dated snapshots plus private uploaded files.

## Invariants
- Never expose other customers' applications, documents, messages, reminders, fiscal details, or deletion requests.
- POST + CSRF is required for any write action; admin-only functions check is_staff and relevant authorization.
- Payments, fee imports, and document-root relocation remain out of scope.
- All candidate migrations and SQL plans must be reviewed BEFORE apply.
- The deployed production baseline is migration 0011_contact_leads; GitHub main has additional unapproved 0012_pricing_research. A release must not silently apply pricing migrations.
- Backup and rollback procedure must be tested against an isolated snapshot. Do not roll back database over later real customer writes.
- High-risk maintenance: user/account deletion, wp-config.php permission changes, HSTS, secret-scanning settings require separate explicit approval after read-only audit.
