# Galiel client workspace visual release — November 16, 2026

**Status: branch-only preview candidate. Not staged, QA-verified or production deployed.**

Only the following tracked files changed:
- `portal/templates/portal/dashboard.html`
- `portal/templates/portal/application_track.html`
- `portal/templates/portal/_workspace_header.html` (new)
- `portal/static/portal/galiel-workspace.css` (new)

No model, view, payment, settings, email, or migration changes.

## Design
- Cream `#F2F1EC`, near-black `#161616`, white cards, orange `#D9714A`.
- Header identity, locale navigation and POST sign out.
- Numbered black workspace sidebar and current process strip.
- Responsive overview cards, four-step status display, documents and activity.
- Existing application upload, documents, Stripe links and status records preserved.
- Existing signature SVG is a **temporary asset**. DO NOT recreate the approved logo with a font. Replace only after the original `Galiel-Logotipo.ai` is supplied and the correct dark/light vector exports have been reviewed.

## Existing status display (template only)
- draft / quote_requested / quoted / awaiting_payment: Review
- paid / under_review / missing_documents: Send
- submitted / in_process / ready: Track
- cancelled: explicit cancellation notice, no false completion

These stages do not alter application data. Payment continues through its existing backend and quote approval controls. Per-service checklist and prices are NOT invented.

## Pre-staging and acceptance
1. Review/merge with the latest v10 security branch; do not overwrite working HostGator files.
2. Confirm the staging code, DB, `.git`, media and environment are outside its document root; use test data only.
3. Backup staging code and static files before deploying the branch; record commit SHA.
4. Install dependencies already required by the existing app (none added in this branch).
5. Run `python3.9 manage.py check --deploy` using staging env, Django tests, and `collectstatic` **on staging only**.
6. Preview dashboard and a staging-only example process `GAL-000002` if it exists. Do NOT expose a real client's process.
7. Verify 375px, 768px and desktop widths; keyboard, color contrast, non-empty/empty states, full-name absent, all EN/ES/FR links.
8. Verify file selection, secure document downloads, quote-only payment UI, CSRF POST signout, and 403/404 access boundaries.
9. Capture desktop/mobile screenshots from protected staging, send for user approval.
10. Only then schedule separate production release. Backup before deploy, preserve live .htaccess and .fcgi, verify smoke tests, and roll back to previous SHA if any fail.

## Rollback
Keep the prior staging commit SHA and a private copy of the staging static/template assets. On failure, restore the prior SHA/templates and staticfiles and refresh the staging FastCGI entry atomically via `install` to temp file + `mv` where its working host configuration requires it. Never use `touch` as an assumed worker restart. Recheck login, dashboard, process detail, and protected files.

## Limitations and blockers
The supplied Claude artifact URL was not accessible as an inspectable mockup in this session, so this implementation follows the user's written specification rather than a verified pixel match. The original Illustrator asset has not yet been received. Staging access and screenshots are also outstanding. The approved Nov 17 relocation remains on hold pending review of its scripts, independent of this branch.
