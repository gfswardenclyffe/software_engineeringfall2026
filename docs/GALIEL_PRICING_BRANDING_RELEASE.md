# Galiel — source-backed catalog pricing, country marquee and design system (2026-11-15)

## Deployment state
This is a source-only release until HostGator production is tested. The live FastCGI process has been left untouched. Do not enable a new live instance while SMTP is still configured as Django's console backend (the prior v10 Contact form is bundled in main).

## Commercial constraints
Nine carefully scoped provisional **starting** amounts are seeded through migration 0013. Ten services stay **quote required**, flagged for management review because a current municipality-specific official fee or matching market range could not be confirmed. No starting amount is a final quote or automatically chargeable. All provisional prices use `is_temporary_price=True` and `pricing_review_required=True`; `_price_for` returns no payable total. Staff can edit price, currency, days, pricing unit, government fee reference, service fee proposal, and EN/ES/FR disclaimer in ServiceOffering admin; inlined OfferingPriceResearch records retain authority/market URLs, date verified, fee, range and notes. Do not unflag temporary prices without validating the specific applicant, authority, third-party charges, taxes and service scope.

| Service | Provisional starting amount | Government reference | Proposed service fee | Scope |
| --- | ---: | ---: | ---: | --- |
| CDMX Benito Juárez | MXN 3,500 | MXN 0 | MXN 3,500 | SIAPEM low-impact notice only, not zoning/safety |
| CDMX Cuauhtémoc | MXN 3,500 | MXN 0 | MXN 3,500 | SIAPEM low-impact notice only |
| Guadalajara Tipo A | MXN 4,175 | MXN 675 | MXN 3,500 | Standard Type A (MXN 618 + MXN 57) |
| Texas notarization | USD 40 | USD 10 | USD 30 | First signature, optional administrative coordination separate from capped notarial fee |
| Texas apostille | USD 115 | USD 15 | USD 100 | Per Texas-issued/notarized document |
| Texas translation | USD 45 | USD 0 | USD 45 | Per standard page, ordinary language pair |
| Texas business filing | USD 450 | USD 300 | USD 150 | Domestic standard LLC formation only, no other entity types |
| France translation | EUR 59 | EUR 0 | EUR 59 | Per standard page, common language |
| France apostille | EUR 80 | EUR 10 HT | EUR 70 | Per individual document, normal up-to-three-act rate; VAT and postage may apply |

Other services (Monterrey x3, San Pedro x2, Querétaro x2, Colima, Reynosa and France process review) remain quoted because of activity/site/project variables or lack of comparable verified official fee. Their research rows explicitly state the gaps. **Do not treat a nonresponse or a generic municipality homepage as proof of a fee.**

Primary evidence linked in migration 0013 and editable admin:
- Guadalajara: https://tramitesdigitales.guadalajara.gob.mx/detalle/Licencia-de-Giro-Tipo-A/379/informacion
- CDMX SIAPEM: https://www.sedeco.cdmx.gob.mx/tramites/aviso-para-el-funcionamiento-de-establecimientos-mercantiles-con-giro-de-bajo-impacto
- Texas notary: https://www.sos.texas.gov/statdoc/edinfo.shtml
- Texas apostille: https://www.sos.texas.gov/authfaqs.shtml
- Texas LLC formation: https://www.sos.texas.gov/corp/instructions/205.shtml
- France apostille: https://www.service-public.gouv.fr/particuliers/vosdroits/F1400
- Market benchmarks and other source URLs are inside the admin OfferingPriceResearch table.

## Brand
- Reusable tokens: `portal/static/portal/galiel-design.css`
- Signature extracted directly from original homepage header: `portal/static/portal/galiel-signature.svg`
- Common header, name and language links: `portal/templates/portal/_site_header.html`
- Email-friendly PNG endpoint: `/brand/galiel-signature.png`, generated from same underlying signature asset.
- Design inherited by auth screens, dashboard, catalog, profile, checkout, tracking, document upload, messages and receipt.
- Site-wide `#D9714A` accent, `#F2F1EC` background, `#161616` ink; squared buttons and thin-bordered cards.
- Homepage marquee is pure CSS and links to `/services/?country=MX|US|FR`, using exactly matching duplicate tracks, a 52-second linear loop, hover/focus pause, orange separators and reduced-motion scrolling instead of animation.

## HostGator staged deployment (DO NOT ACTIVATE LIVE UNTIL MAIL IS WORKING)
1. Back up `~/galiel/db.sqlite3`, the current app code, and `.htaccess`; preserve `galiel-private-files`, `.git`, FastCGI scripts and production environment.
2. Retrieve main after PR merge and selectively copy application/code/templates/migrations/static files; never overwrite the SQLite DB or HostGator configuration with a GitHub archive.
3. `python manage.py check`
4. `python manage.py migrate` (0012 pricing/research, then 0013 conservative estimates)
5. `python manage.py test portal.tests_pricing_theme portal.tests_checkout portal.tests_contact` plus the full suite.
6. `python manage.py collectstatic --noinput` and verify that `/static/portal/galiel-design.css` and SVG are served. Check `/brand/galiel-signature.png` returns image/png after web process reload.
7. Confirm real SMTP delivery and disable Django DEBUG before new public contact intake becomes active.
8. Only then create a new FastCGI entry point and change `.htaccess` rewrite from the last validated version. Smoke test public homepage, login, filtered services, dashboard, all six checkout steps, EN/ES/FR, contact inquiry, email delivery, responsive widths and reduced-motion behavior.
9. Existing transactions should not be charged using provisional prices. Do not convert provisional into fixed without authority verification.
