# X-Ray 2026-11-27: safe HostGator reconciliation gate

**Status: BLOCKED BEFORE APPLY until the live-source reconciliation is complete.**

The prior package `Galiel_XRay_HostGator_Review_20261127.zip` must not be run: its `release.py` overwrote complete templates from GitHub and depended on the HostGator directory being a Git worktree.

The three Nov 18 references (8984b75, a011b45, bf6cbb3) describe mobile releases. Their remote release branches do not contain the production `gm-ws-mobile` / `gm-auth-mobile` markup; merging those branches would not bring the codebase up to live state.

**Required release order:**
1. Capture the current, exact live files privately on HostGator (read-only), including `index.html`, all touched templates, `portal/admin.py`, and both CSS mirrors. Record SHA-256 per file and obtain a reviewable snapshot, keeping personal data and secrets out.
2. Reconcile the captured live files into the repository `main` with no substitutions or guessed CSS; verify main matches the captured production files exactly. Keep this as a separate change from X-Ray.
3. Rebase the X-Ray PR on the reconciled main; confirm mobile markup `gm-ws-mobile`, `gm-auth-mobile`, `by WARDENCLYFFE`, and scrolling tabs remain present.
4. The new HostGator release package must download **pinned raw blobs**, verify their hash, create a private isolated review directory, and produce an exact-anchor patch (never whole-file replacement for existing templates). Before any apply, verify the reviewed original SHA-256 of every touched file and reviewed `PLAN_SHA256` unchanged.
5. All Django tests must execute in an isolated copy, never against the live project, database, or uploaded documents. No Node.js dependency on HostGator.
6. Backup and rollback must be byte-verified, with a browser User-Agent for HTTPS checks. Never apply automatically or import prices.

The X-Ray client code and demo fixtures remain staged, but **do not deploy PR #13 until steps 1–3 pass**.

Independent pricing PR #14 is not changed.
