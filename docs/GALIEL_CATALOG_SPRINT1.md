# Galiel service catalog — Sprint 1

The new catalog is **staging only** until prices, legal terms, required files and processing estimates have been reviewed by Wardenclyffe.

## Manager workflow

1. Sign in as the manager. The Django administration site is at `/admin/` (requires appropriate staff/superuser permissions and matching HostGator rewrite).
2. Under Portal, confirm Catalog countries: MX, US, FR.
3. Add each Catalog region (state / province / region) under its correct country.
4. Add each Catalog municipality under its correct region.
5. Add a Catalog service with English, Spanish and French names.
6. Add a Service offering linked to the service and the correct location. Set price type (fixed, starting at, quotation required), currency, and an estimated range of business days. Prices should be verified and disclosed carefully; do **not** invent government fees.
7. Add Service requirements (questions and documents) as inline rows.
8. Check `is_published` only when information is ready for clients.

The authenticated browse page is `/services/`. Service cards display only published database-backed offerings, and "Ask about this service" opens a messaging inquiry. **It does not place an order or charge the client.** No card/payment/order flows are implemented in Sprint 1.

Existing legacy service links with `?service=` remain functional until the intake workflow replaces their placeholder.

## HostGator deployment

Back up `db.sqlite3` and `.htaccess`. After merging a validated PR:

```sh
cd ~/galiel
git pull --ff-only origin main
python manage.py migrate
python manage.py check
```

A new FastCGI entry-point version is needed to avoid stale worker code on HostGator. Add an Apache route **before** the broad `^services/(.*)$` route (or rely on that broad existing route if it routes correctly):
```apache
RewriteRule ^services/?$ galiel-v7.fcgi/services/ [QSA,L]
```
Replace `galiel-v7.fcgi` with whichever current entrypoint version is in use. The Django admin route may need its own explicit `RewriteRule ^admin/(.*)$ galiel-v7.fcgi/admin/$1 [QSA,L]`.

Confirm `/services/` returns 302 when unauthenticated and displays a catalog when authenticated. No payment processor or real customer orders are connected. All staff configuration happens via admin with built-in permission checks.

## Deployment limitation

The current FastCGI setup is a custom HostGator bridge. A new entrypoint must be tested separately and the `.htaccess` backup kept for rollback. Do not remove the existing database or client uploads.
