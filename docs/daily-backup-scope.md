# Daily backup hardening — scoped private client uploads

This patch is a production maintenance release without migrations, pricing or checkout changes.

## Included source data

Only three logical categories are collected:

1. A consistent SQLite backup of `settings.DATABASES["default"]["NAME"]` using Python's SQLite backup API (validated with `PRAGMA integrity_check`).
2. `settings.MEDIA_ROOT / "case_documents"` (files stored by `ApplicationDocument`).
3. `settings.MEDIA_ROOT / "client_documents"` (files stored by `ClientDocument`).

Archive members follow `db.sqlite3`, `uploads/case_documents/...`, and `uploads/client_documents/...`. Both upload roots are printed, with file counts and total byte sizes, even if a directory does not exist yet.

## Excluded and protected

Do not walk the whole private media root. Never traverse or include `daily-backups/`, `*-backups/`, quarantines, staging folders, dotfiles, `*.env`, `*.lock`, `*.log`, symlinks, or nonregular files. Refuse to run if the archive destination overlaps either included upload root, if there is a media-root symlink, or if media/backup is inside the document root. Archive output uses restrictive permissions, atomic rename, validation, and 14-day time-based retention after successful creation.

**Known scope limitation:** `ContactLead.attachment` lives in `contact_leads/` and is intentionally outside these two specifically approved upload folders. If contact attachments also need daily disaster-recovery coverage, request a separate reviewed allowlist expansion. Do not silently include the whole MEDIA_ROOT.

## Security follow-up

Prior archives may contain staging secrets such as `staging.env`. This release does not delete or overwrite historical backups. Keep historical archives private (owner-only) and review removal/credential rotation separately, since sensitive data may remain in them. Do not enable cPanel cron until the new dry-run prints only the two intended upload roots, the smoke tests pass, and the first new archive's membership has been inspected.

## Translation polish

EN/ES/FR variants are added for sidebar News & updates, Alerts, profile Account & billing requests and links to fiscal details. The unread bell uses inline, accessible outline SVG instead of a device-dependent emoji.

WhatsApp remains unconfigured pending the approved number.
