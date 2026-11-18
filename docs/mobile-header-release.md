# Galiel mobile header-only review
This branch pins the approved source for a mobile-only 390px release. The production homepage is guarded by SHA-256 c3d9871bedced20f6c750b790689014effc3440ed407d2827a152a083eb6cc35. The patch changes only inline homepage CSS/header markup, the shared Django workspace and auth headers, and the corresponding two CSS assets. No migrations, database, settings, secrets or business logic are modified.

## Acceptance
- Below 768px: Galiel logo and menu toggle, no by WARDENCLYFFE tagline; Services, How it works, Contact, EN/ES/FR, Sign in/Start a service; closes on link tap and Escape; selection highlighted.
- Hero size clamp(2.4rem,…,3rem), CTA buttons before decorative artwork; no vertical rule background; constrain oversized wordmark.
- Compact location cards and consistent black/cream/orange link styling.
- At 1440px: desktop styling must not change (new rules all in max-width:767px).
- Dry-run validates full live homepage SHA, exact anchors, complete unified diff, plan digest, no other files touched. Only reviewed plan may be applied. Five files backed up and rolled back atomically per file.
- Screenshot comparisons are previews until a byte-for-byte copy of the current live index is provided; a remote browser cannot reconstruct actual before screenshots from a checksum alone.

## Verified uploaded live sources (2026-11-18)
The operator supplied exact live Django templates and two identical copies per CSS asset. The updated release package pins full SHA-256 hashes:

| Production file | SHA-256 |
| --- | --- |
| `index.html` | `c3d9871bedced20f6c750b790689014effc3440ed407d2827a152a083eb6cc35` |
| `_workspace_header.html` | `1ae3845ffaf757e07418a902078ffc987803e44f7040277ee6c497d0a6801a92` |
| `auth_base.html` | `a417d6b31146046a4cf21b75aef6f707393dd762263d5dc5b267771b4821d3a8` |
| both `galiel-workspace.css` copies | `e0bc9ecff5ba7b7ef3ccc6fe33158dc70ee55bbfa0feca2d8f0e1e298e58606d` |
| both `galiel-pages.css` copies | `b672ac8c52290d3ebaa76a2f48d655b44a4feddaab10469efe110cf13defa369` |

Production changes remain seven content files: one public homepage, two shared templates and four CSS files (the latter in source and served locations). The existing `/galiel-v9.fcgi` can be reinstalled atomically **with identical bytes** after apply to request a worker refresh; this is not a code change or guaranteed process restart. Check the live `/login/` markup after apply. Abort and restore if the mobile template is not visible.

The static `index.html` menu language buttons use the existing `.langs button` selector; the patch requires that binding and its active-button logic before injecting mobile buttons. No duplicated language controller is installed.

The public homepage was not retrievable from the assistant environment (DNS unavailable); the HostGator patcher must reject any byte sequence other than the exact full approved SHA-256. Neither an older repository reference nor a synthetic screenshot may substitute for that verification.
