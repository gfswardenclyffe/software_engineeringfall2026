# Galiel static-homepage mobile polish — source checksum pending

Production file scope: **only** /home2/gfrancossh/galiel/index.html.

Mobile breakpoint: max-width: 767px. All desktop styles and markup are preserved byte-for-byte, except for insertion of a narrowly gated iframe handler that is inert at desktop width.

## Changes
- Mobile hero headline clamp(2rem, 6.5vw, 2.4rem); line-height:1.05.
- Mobile wordmark iframe height clamp(110px, 31vw, 130px), centered with reduced surrounding spacing.
- In the existing same-origin wordmark animation iframe, only when the parent viewport is below 768px, limit SVG height to 110px and hide the internal REPLAY button to prevent overlap. No change to galiel_wordmark_animation.html itself.
- Mobile-only 24px left/right gradient mask for rotating .quick strip.

## Required SHA gate
The operator's request contains the literal placeholder PASTE_SHA_HERE. The public homepage could not be fetched from the build environment. **The full current SHA-256 is not known** and must NOT be guessed or silently set to the previous mobile baseline.

The deployment script requires GALIEL_EXPECTED_INDEX_SHA256 to be supplied as 64 hexadecimal digits and refuses a mismatched live homepage. PLAN.json embeds that source SHA, the candidate SHA, and this release commit pin. A separate GALIEL_REVIEWED_PLAN_SHA256 must match exactly at apply. Review files and backups are timestamped.

## Guardrails
- Exactly one production file in the install/rollback allowlist.
- Full unified diff plus exact-anchor checks; no unrelated HTML replacements.
- Back up before replacement; atomic file swap; verify public HTTPS response byte-for-byte.
- One-command guarded rollback; refuse rollback if current installed bytes diverged.
- Execute existing Django tests in isolated copy if GALIEL_PYTHON_BIN is configured.
- Real 390/1440 before/after screenshots can be generated from HostGator's actual review HTML using Playwright. The bundled synthetic specimen screenshots do not prove the live page was captured.
- No Django templates, models, settings, database, migrations, payments, mail, or private files modified.
