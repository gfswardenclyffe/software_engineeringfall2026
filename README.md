# Galiel by Wardenclyffe

**Galiel** is Wardenclyffe's client portal for administrative services in Mexico, Texas and France. Clients can create accounts, select administrative services, manage applications, exchange private documents, communicate with staff, track process status, receive reminders, and submit optional invoice and account-deletion requests.

Production business site: https://galiel.wardenclyffefirm.com

## Features

- **Accounts and profiles:** registration, email verification, password reset, EN/ES/FR client experience, structured contact information and optional fiscal details.
- **Services and workflow:** jurisdiction-based service discovery, six-step application wizard, configurable requirements, draft autosave, status tracking, and client-owned draft deletion.
- **Private files and messages:** PDF/JPG/PNG uploads, secure downloads, client/staff conversations and document review.
- **News & updates:** staff-created announcements with three-language titles/bodies, publication/expiration dates and category filtering.
- **Process alerts:** private reminders, unread bell count, email copies, read/dismiss actions and staff-scheduled renewal dates.
- **Client requests:** review-only account-deletion request and manual fiscal-invoice request.
- **Scripted help:** a deterministic, non-AI button assistant for catalog, requirements, case status and contacting staff.
- **Operations:** Django admin management, daily due-soon reminder command, and private SQLite/client-upload backup with 14-day retention.

**On hold:** approved pricing import, automated payments, and production filesystem relocation. No automated SAT invoices are issued by this application.

## Technology

Python **3.9+**, Django, SQLite, HTML/CSS, vanilla JavaScript, Django templates, Django admin, Git/GitHub and SMTP. Production currently uses HostGator cPanel/Apache with a FastCGI entry point. Files containing private client uploads and credentials belong **outside the public document root**.

The code is organized as:
- `portal/`: authentication, catalog, workflows, client documents, messaging, views, forms, templates and baseline migrations through `0011_contact_leads`.
- `galiel_ops/`: announcements, reminders, fiscal records, deletion requests, scripted-help endpoints, daily commands and related tests.
- `wardenclyffe_portal/`: Django settings and URL configuration.
- `docs/`: requirements, UML, user stories, operational instructions and design/test evidence.

## Local setup

Use an isolated project directory. **Never download or copy the production database, client uploads, credentials or staging environment into Git.**

```bash
git clone https://github.com/gfswardenclyffe/software_engineeringfall2026.git
cd software_engineeringfall2026
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Development-only secret generated on your own machine:
export DJANGO_SECRET_KEY="$(python -c 'from secrets import token_urlsafe; print(token_urlsafe(48))')"
export DJANGO_DEBUG=True
export DJANGO_PRIVATE_MEDIA_ROOT="$(pwd)/../galiel-local-private-media"
python manage.py migrate
python manage.py runserver
```

The private media root must be **outside** the Django application directory. SQLite for local development is created automatically by migrations and should not be committed.

## Tests

```bash
python manage.py test portal galiel_ops
```

The operations tests cover client ownership boundaries, draft deletion, alerts, published announcements, account requests and backup allowlists. The real production checkout remains on hold. Before grading, run the entire suite in a fresh isolated environment and retain the complete sanitized output.

The operator reported a production-compatible HostGator run of **95 tests OK** on November 18, 2026; see [testing evidence](docs/testing/README.md) for provenance and instructions. This statement is not a claim that GitHub CI has independently reproduced that run.

## Documentation

- [Functional requirements](docs/requirements.md)
- [User stories](docs/user-stories.md)
- [UML: use-case, class and sequence diagrams](docs/uml.md)
- [User manual](docs/user-manual.md)
- [Approved design mockups](docs/mockups/README.md)
- [EN/ES screenshot index](docs/screenshots/README.md)
- [Testing and HostGator results](docs/testing/README.md)
- [Operations and security deployment review](docs/deployment-review.md)
- [Scoped backup design](docs/daily-backup-scope.md)

## Team

Michelle Lopez Dieckmann · Gustavo Franco-Sanchez · Ryan Garza

## Security notes

Do not add `.env`, `db.sqlite3`, private uploads, API keys, credentials or real-client screenshots to this repository. Case and document views must always enforce authentication and client ownership. Production deployment requires a separate reviewed migration plan, backup, dry-run, and rollback.
