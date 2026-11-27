# X-Ray tour — spec-aligned release review (Nov 27, 2026)

Basis: `Galiel_XRay_Developer_Spec.pdf` (12 pages) and approved `Galiel_XRay_Mockup.html`.

## Implemented in this review branch
- Exactly 28 stops/6 parts in `galiel-xray-stops.json`; approved explanatory copy and layer colors.
- Opt-in `?xray=1`; local session flag guarded by try/catch; `?xray=0`/Exit clears state.
- Scoped stylesheet, X-Ray tint, 1.5 s scan, numbered click targets, target outlines, 400 px explanations, keyboard navigation, source links and 1.1 s exit animation.
- Presenter assets embedded in workspace, auth pages, dashboard, case tracking and staff ServiceApplication change form.
- `data-xray` targets in supported Django templates.
- JS/CSS/JSON byte-identical copies under `portal/static/portal` and `static/portal`; CI enforces parity.
- Independent from pricing. No X-Ray migrations or changes to payment, secrets, settings or database schema.
- `scripts/galiel_xray_homepage.py`: surgical, reversible installation to existing Apache-served `~/galiel/index.html`. This has **not** been run on production.

## Blockers before merging or December 3 deployment
1. Live Apache homepage injection must be dry-run, reviewed and applied with its backup/manifest. Repository's `portal/templates/portal/home.html` is NOT the same live Apache `index.html`.
2. Set `settings.demo_process_id` in BOTH copies of the stops data (same bytes). Use demo records only; do not include real client information. The demo process must exist and be viewable by the presenter client and a separate staff user.
3. Demo client account: four draft/quote processes, one PDF, two unread reminders and three EN/ES/FR announcements. Demo staff account: `is_staff` only, permissions to view/change the demo process. Use separate login transitions; never embed passwords in the stops JSON.
4. Test navigation across / → /register/ → /login/ → /dashboard/ → /services/applications/{demo id}/step/3/ → /alerts/ and /updates/ → /admin/portal/serviceapplication/{demo id}/change/.
5. Do a **real Chrome and Safari visual check** at 1280/1440/1920 px; compare before/after no-flag screenshots at 1440 and 390 px. Check target alignment, scan, part intros, Back/Next, restart, number clicks, Esc, `?xray=0`, and no secret/client content.
6. HostGator live checks must send browser User-Agent; verify actual Apache static URL behavior, route allowlisting and FastCGI process refresh.
7. Pinned reviewed commit SHA, dry-run/PLAN_SHA256, private backup, verified rollback and self-test are deployment gates, not mere documentation.

## Public homepage preflight and install
Do NOT run before a private backup and release approval.

```bash
cd ~/galiel
python scripts/galiel_xray_homepage.py --file "$HOME/galiel/index.html" --dry-run
# Confirm original hash/installed hash and review exact diff, then only after approval:
python scripts/galiel_xray_homepage.py --file "$HOME/galiel/index.html" --apply
# The installer prints a private manifest for hash-checked, one-command rollback:
python scripts/galiel_xray_homepage.py --file "$HOME/galiel/index.html" --rollback --manifest "$HOME/galiel-private-files/xray-backups/xray-YYYYMMDDTHHMMSSZ.manifest.json"
```

## Self-test after deployment
```bash
git rev-parse HEAD
node --check portal/static/portal/galiel-xray.js
cmp portal/static/portal/galiel-xray.js static/portal/galiel-xray.js
cmp portal/static/portal/galiel-xray.css static/portal/galiel-xray.css
cmp portal/static/portal/galiel-xray-stops.json static/portal/galiel-xray-stops.json
python manage.py check
python manage.py test portal.tests_xray portal galiel_ops --noinput
curl -sSI -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36' https://galiel.wardenclyffefirm.com/static/portal/galiel-xray.js
```

**Do not merge or promote the branch solely because unit tests pass.** Visual and real-page demo checks remain required by the developer specification.
