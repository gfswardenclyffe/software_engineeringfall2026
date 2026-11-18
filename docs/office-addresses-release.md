# Galiel — Office contact-information-only release (2026-11-18)

Production static homepage: /home2/gfrancossh/galiel/index.html served by Apache at /. Django portal/templates/portal/home.html is a fallback, not the live homepage.

Pinned initial live index SHA-256: d6ab0fd24d75f73ee315863fe7d755475ab1216b54199a04cd08ffe7225789a0

## Offices in required order

1. Texas office — 1209 S. 10th St., Suite A, Unit 583; McAllen, TX 78501
2. California office — 849 N Lake Ave, Unit 254; Pasadena, CA 91104
3. Mexico office — Manuel Gómez Morín No. 350, PB6A-3; Valle del Campestre; San Pedro Garza García, Nuevo León 66265, Mexico

Footer under existing email: McAllen, TX · Pasadena, CA · San Pedro Garza García, N.L.

| English | Español | Français |
| --- | --- | --- |
| Texas office | Oficina en Texas | Bureau au Texas |
| California office | Oficina en California | Bureau en Californie |
| Mexico office | Oficina en México | Bureau au Mexique |

Django fallback template updates are committed on this branch. The Apache-served index.html remains production-owned and will only be patched by a guarded local deploy utility after the full live source SHA matches. Exact anchors, unified diff, timestamped review, review plan hash, backups, restore and HTTP checks are mandatory. Existing email and phone are preserved. No database, model, migration, secret, FastCGI or Apache routing changes.
