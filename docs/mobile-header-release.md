# Galiel mobile header-only review
This branch pins the approved source for a mobile-only 390px release. The production homepage is guarded by SHA-256 c3d9871bedced20f6c750b790689014effc3440ed407d2827a152a083eb6cc35. The patch changes only inline homepage CSS/header markup, the shared Django workspace and auth headers, and the corresponding two CSS assets. No migrations, database, settings, secrets or business logic are modified.

## Acceptance
- Below 768px: Galiel logo and menu toggle, no by WARDENCLYFFE tagline; Services, How it works, Contact, EN/ES/FR, Sign in/Start a service; closes on link tap and Escape; selection highlighted.
- Hero size clamp(2.4rem,…,3rem), CTA buttons before decorative artwork; no vertical rule background; constrain oversized wordmark.
- Compact location cards and consistent black/cream/orange link styling.
- At 1440px: desktop styling must not change (new rules all in max-width:767px).
- Dry-run validates full live homepage SHA, exact anchors, complete unified diff, plan digest, no other files touched. Only reviewed plan may be applied. Five files backed up and rolled back atomically per file.
- Screenshot comparisons are previews until a byte-for-byte copy of the current live index is provided; a remote browser cannot reconstruct actual before screenshots from a checksum alone.
