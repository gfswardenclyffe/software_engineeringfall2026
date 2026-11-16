# HostGator security sync — isolated v10 branch

The tested live site is authoritative; these are code and configuration templates, **not a mandate to overwrite production**.

## Confirmed live layout
- Document root and app: `/home2/gfrancossh/galiel`.
- Active entry point: `/home2/gfrancossh/galiel/galiel-v9.fcgi`.
- Environment: `/home2/gfrancossh/galiel_env/.env`, mode 600.
- Private media: `/home2/gfrancossh/galiel-private-files`, subfolders `case_documents`, `client_documents`, `contact_leads`.
- Existing SQLite DB is **inside** the current document root; relocation is still pending.
- Cleanly rotated key already active as of Nov 16, 2026. Do not rotate again to deploy this branch.
- Confirmed SSL: `RequestHeader set X-Forwarded-Proto "https" "expr=%{HTTPS} == 'on'"`. The `env=HTTPS` alternative failed on this HostGator configuration.
- Worker refresh: atomic replacement of actual .fcgi; do not rely on touch.
- Python packages installed in `~/.local/lib/python3.9`; do not set `PYTHONNOUSERSITE=1`.

## Files and placement
- `galiel_env_loader.py` -> `/home2/gfrancossh/galiel/galiel_env_loader.py` (after verifying existing live loader; preserve it if behavior differs).
- `wardenclyffe_portal/settings.py` -> `/home2/gfrancossh/galiel/wardenclyffe_portal/settings.py` (only via reviewed deployment).
- `deploy/hostgator/galiel-v9.fcgi.loader-snippet.txt` -> insert its Python statements into the existing `/home2/gfrancossh/galiel/galiel-v9.fcgi`, not a drop-in replacement.
- `deploy/hostgator/production.htaccess.security-block` -> merge with existing `/home2/gfrancossh/galiel/.htaccess`; don't replace it.
- `deploy/hostgator/staging.htaccess.security-block` -> merge with `/home2/gfrancossh/galiel-staging-web/.htaccess`; don't replace it.
- `.env.example` is documentation only; do not deploy it as live secrets.
- Stage Django project, database, and `.git` outside `galiel-staging-web` and outside `public_html`.

## Configuration review gate
This GitHub settings module uses `load_env()`, `DEBUG=False`, `SECRET_KEY_FALLBACKS=[]`, mandatory `DJANGO_SECRET_KEY`, and an optional `DJANGO_DB_PATH` to support the eventual DB relocation. Currently, the DB path defaults to `BASE_DIR/db.sqlite3`, *inside* the production document root. Moving it is a separate supervised operation.

The loader uses `os.environ.setdefault`, so already-present environment variables have precedence. Confirm this matches the live loader before deploying; a stale inherited secret must not silently override the private file. It does not execute .env as shell script.

## Must-pass acceptance tests
1. Compare live settings, FastCGI, and .htaccess to candidates without exposing any secrets. Never replace them wholesale.
2. Confirm environment mode 600, DEBUG=False, configured secret and no fallbacks.
3. Check migration plan and DB path; do not automatically migrate.
4. HTTP: homepage/login/register 200; protected dashboard redirects appropriately; missing path 404; blocked python/database/.git paths 403 or 404; no debug page.
5. Register -> activation mail -> confirmation -> authenticated dashboard.
6. Verify media privacy for case_documents, client_documents and contact_leads.
7. Confirm no unexpected worker processes and perform atomic .fcgi replacement only after explicit production approval.

## Important
- W004 (HSTS) intentionally deferred, W008 resolved by verified HTTPS forwarding.
- Gitleaks/secret scanning and GitHub push protection need independent verification; they have NOT been performed here.
- Visual staging -> user approval -> production; followed by contact, prices, checkout/Stripe, each with preview and approval.
