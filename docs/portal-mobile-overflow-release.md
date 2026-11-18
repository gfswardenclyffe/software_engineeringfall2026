# Galiel client portal — mobile overflow repair

This is a **CSS-only, no database** maintenance release. The public homepage is unchanged.

## Design decision
**Hide the nine-tab sidebar below 768px.** The existing accessible hamburger menu already contains links to primary client sections. Do not show a second scrolling navigation row.

## Scope
- `portal/static/portal/galiel-workspace.css`
- `static/portal/galiel-workspace.css` (the Apache-served byte-identical copy)
- `portal/static/portal/galiel-pages.css`
- `static/portal/galiel-pages.css` (the Apache-served byte-identical copy)

No Django templates need to change. The deployed shared header and authentication templates already include viewport metadata and mobile hamburger markup. The dry-run verifies both template anchors, audits document templates for viewport metadata, and pins their SHA-256 values as **read-only** entries in PLAN.json.

## Acceptance checks
- 390px: `document.documentElement.scrollWidth === window.innerWidth` on all protected client routes, wizard steps 1–5 (including upload), Services/filters, profile/fiscal/account request, News/Alerts, login/register/reset.
- The black nine-tab sidebar is hidden; menu remains visible, uses divider-only styling.
- Draft banner and Continue link are both visible; long process names wrap.
- Stats use a single full-width column; process list/cards/filters/uploads never exceed viewport width.
- The help bubble is 42px wide and placed 8px from the bottom/right; content has 84px of bottom breathing room.
- 1440px pixel-identical before and after. Every new CSS declaration is inside @media screen and (max-width:767px).
- Source and Apache-served CSS copies remain byte-identical, with HTTPS GET responses matching the installed bytes.

## Hashes, review, approval
The live CSS baseline SHA values are not included in this prompt. The release requires two full hashes from the live server via `GALIEL_EXPECTED_WS_CSS_SHA256` and `GALIEL_EXPECTED_PAGES_CSS_SHA256`. It refuses blank values, mismatches or divergent served/source copies. A timestamped review contains complete DIFF.patch, PLAN.json and PLAN_SHA256. Apply requires `GALIEL_REVIEWED_PLAN_SHA256` and explicit approval and repeats verification and isolated Django tests. Backups include all four originals. Rollback refuses changed candidate bytes. The FastCGI entry point can be reinstalled byte-identically, followed by a public login-page check.

**Evidence limitation:** The bundled before/after images are reconstructed browser specimens, not screenshots of signed-in production. `capture_real_portal.py` collects real screens using a disposable test-account browser storage-state stored privately on the server. Run it both before and after deploying, and compare 1440px screenshots. Never commit the private storage-state or real client data.
