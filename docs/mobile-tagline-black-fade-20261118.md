# Galiel mobile tagline and black-edge fade — guarded release

**Production status:** Review candidate only. Do not deploy without an explicit approved `PLAN_SHA256`.

## Scope

Exactly seven deployed paths are validated, backed up and covered by rollback:

- `/home2/gfrancossh/galiel/index.html`
- `portal/templates/portal/_workspace_header.html` (already contains the byline; verified but no new bytes required)
- `portal/templates/portal/auth_base.html`
- `portal/static/portal/galiel-workspace.css`
- `static/portal/galiel-workspace.css`
- `portal/static/portal/galiel-pages.css`
- `static/portal/galiel-pages.css`

Below 768px only: show **by WARDENCLYFFE** below and left-aligned with the logo on the public, workspace and authentication headers. Replace the translucent `.quick` alpha mask with two noninteractive 24px black-to-transparent pseudo-element overlays. Keep existing menus, hero geometry, artwork, and desktop styling unchanged.

## Source hash policy

The current post-polish static homepage SHA was not provided. The full value must be supplied through `GALIEL_EXPECTED_INDEX_SHA256`; the executable refuses placeholders, mismatches, or a changed source between dry-run and apply.

The following expected SHA-256 values were calculated from the previously approved seven-file mobile release's original uploaded source files and its exact patch logic. **HostGator must verify them against the actual current files**. No bypass is allowed:

| File | Expected SHA-256 |
| --- | --- |
| Workspace header | `2b7e15bcbd110dda70edbf9d461d5459e06d09062ff3bb703f2aece55ee180d1` |
| Auth base | `4b4fb04f2b25e746c511389ac23b14e021a991d6861b27f3e6a994ab8a0e259c` |
| Both workspace CSS copies | `6a6b560022aaf3a7b7cc122a2cad1eed764ad76447b632e2928db53e32c98029` |
| Both pages CSS copies | `984b64ab847a3783b36758612b4d171e2f3d20ba23074fcdad243f05d2246588` |

Dry-run outputs a timestamped review with full unified diff, deterministic plan, SHA-256, and isolated Django tests. At apply, the reviewed plan hash, all seven source hashes, byte equality of duplicate CSS copies, and post-apply public HTTPS/CSS/live-login checks must pass. FastCGI entry-point bytes stay unchanged by the requested reload. Rollback restores the original seven files.

No database, migrations, settings, secrets or third-party systems are modified.
