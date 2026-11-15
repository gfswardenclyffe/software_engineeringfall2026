# Galiel Documents — staged deployment checklist

## Status
This branch adds client-owned PDF uploads/downloads, not process-based or staff-shared document folders. The repository's Django checks and tests pass in GitHub Actions. **These are not live HostGator end-to-end tests.**

## Prerequisites
1. Back up the production SQLite database, application, `.htaccess`, and FastCGI bridge. Do not overwrite the database with a repository copy.
2. Verify that the FastCGI process actually loads the updated code. Production currently uses `galiel-v2.fcgi`, **not Passenger**.
3. Configure `DJANGO_PRIVATE_MEDIA_ROOT` to a writable private directory **outside any HTTP-accessible document root** (for example `/home2/gfrancossh/galiel-private-files` only if it is outside the relevant Apache document roots). Do not expose the directory as `/media/`. Restrict filesystem permissions and ensure no other shared-hosting tenant can read files. The default is `BASE_DIR.parent / "galiel-private-files"`, which must still be checked against the actual hosting setup.
4. Existing default secret key / debug configuration must be replaced with production-safe private environment settings before uploading real client documents.

## Django and routing
1. Run `python manage.py check --deploy`, `python manage.py test portal`, and `python manage.py test portal.tests_documents`.
2. Run `python manage.py migrate --plan` and review the new `portal.0004_clientdocument` migration. Then migrate on the approved staging deployment.
3. Add the following rules **above general catch-all rules** in the production Galiel `.htaccess` FastCGI routing:
   ```apache
   RewriteRule ^documents/upload/?$ galiel-v2.fcgi/documents/upload/ [QSA,L]
   RewriteRule ^documents/([0-9]+)/download/?$ galiel-v2.fcgi/documents/$1/download/ [QSA,L]
   ```
   The usual `dashboard/` rule remains in place.
4. Ensure HTTPS and Django security settings are correctly detected in the FastCGI environment.

## Staging acceptance tests (two separate accounts)
- A signs in, uploads a valid small PDF, sees it listed, downloads it, logs out, signs back in, and downloads it again.
- A cannot upload non-PDF content, a fake PDF, or a document over 10 MB.
- B cannot see A's title in their document list and receives 404 if attempting A's download URL.
- Anonymous users cannot upload or download private files.
- Verify a direct HTTP request to the underlying media directory cannot retrieve a file. The storage root must be **outside** any public webroot.
- Test upload/post with CSRF enabled and ensure storage survives app restart.
- Do not merge or deploy until these tests work in the actual hosting setup.

## Remaining limitations
- Files belong to users, not yet to organizations or cases; do not use this release as a multi-user client organization document vault.
- Simple signature check is not deep PDF scanning. Consider malware scanning and stronger content-validation as the platform begins handling untrusted client material.
- No delete, revision history, staff access, or review workflow yet.
