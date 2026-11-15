# Galiel authentication release checklist

This release changes the account flow:

1. Visitor selects **Sign in** or **Create account**.
2. Registration creates a **disabled** Django user and sends a one-use email verification link.
3. The user clicks the link (valid up to 24 hours); Django activates the account, authenticates it, and redirects to the selected service or dashboard.
4. Returning clients use verified email + password. Recovery uses Django's password-reset email flow.
5. A phone number is an **optional contact field** only. SMS OTP is **not implemented**. Do not claim phone verification is available until an SMS provider and verified webhook flow are added.

Existing active Django users are not automatically disabled.

## Required before public deployment

- Restore cPanel/HostGator shell process capacity first; investigate the `jailshell: fork: Resource temporarily unavailable` condition. **Do not kill or restart all Python processes**.
- Back up the live `db.sqlite3`, application directory, `.htaccess`, and existing FastCGI bridge configuration.
- Confirm the correct deployment directory and app entrypoint. This site previously used a custom `galiel-v2.fcgi` FastCGI bridge. The repository `passenger_wsgi.py` does **not** prove that production uses Passenger.
- Configure a functioning outbound SMTP service. Set the following as **server-side environment variables**, not tracked repository files:
  - `DJANGO_EMAIL_HOST`
  - `DJANGO_EMAIL_PORT`
  - `DJANGO_EMAIL_USER`
  - `DJANGO_EMAIL_PASSWORD`
  - `DJANGO_EMAIL_USE_TLS` (normally True for port 587)
  - `DJANGO_EMAIL_USE_SSL` (normally False with STARTTLS)
  - `DJANGO_DEFAULT_FROM_EMAIL` (must match a verified sender allowed by your SMTP provider)
- Set a **unique private** `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=False`. Keep the signing key stable across application restarts; changing it invalidates existing sessions and token links. Never copy keys into GitHub or screenshots.
- Verify that Django detects HTTPS under the actual reverse-proxy/FastCGI setup: `request.is_secure()` must be true for production registration.
- Protect the application database from direct public HTTP access; ensure `db.sqlite3` is not within a public web-served path.

## Validation procedure

Use the approved production deployment mechanism only after service recovery.

1. Check Git branch, remote, unstaged changes, and live database backups **before** updating code.
2. Run `python manage.py check --deploy`, `python manage.py test portal`, and `python manage.py migrate --plan`; inspect migrations before applying them.
3. Verify SMTP can deliver a test email to a mailbox you control, with no secrets printed in terminal output.
4. Test `/register/` with a fresh email account (not your primary admin account). Registration must show the check-email page.
5. Test that the inactive account cannot log in using its email and password before confirmation.
6. Click the emailed activation link. It should reach `/dashboard/` (or selected-service page), and the link must not work again.
7. Test logout (POST), normal login, forgotten-password reset, resend activation, profile view/edit, and mobile layout.
8. Check `/register/complete/`: if Django tests pass but live gives 404, diagnose `.htaccess`, FastCGI dispatcher, application root, deployed version, and restart mechanism. **Do not assume it's a missing Django URL**.

## Scope limitation

The dashboard no longer displays invented processes, invoices, documents, balances or client messages. Those sections now show empty states until real per-client data models and authorized permissions are implemented. Do not enable mock buttons that appear to upload, pay, or send messages.

## Important production security follow-up

The existing project predates this release and has permissive default development settings. Confirm secure cookie, host, HTTPS, and secret-key configuration using `check --deploy` before exposing real client information. Implement meaningful abuse/rate limits and email-change re-verification before handling sensitive cases at scale.
