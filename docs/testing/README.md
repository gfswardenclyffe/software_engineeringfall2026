# Galiel — Testing and verification

## HostGator acceptance run (reported by project operator)

On **November 18, 2026**, the project operator reported that the deployed operations release passed **95 Django tests with zero reported failures or errors**.

> Ran 95 tests ... OK

This is a **user-reported result summary**, not a verbatim captured console log. The complete HostGator command output was not supplied, so no raw log has been fabricated. For a graded evidence artifact, capture the next real run into `hostgator-tests-YYYYMMDD.log` (remove credentials, email addresses, and client data before committing).

## Independently verified CI

[Main-branch GitHub Actions run #44360360520 — 99 tests OK](https://github.com/gfswardenclyffe/software_engineeringfall2026/actions/runs/44360360520), on November 18, 2026, with isolated data and migrations through portal.0011 plus galiel_ops.0001. A [sanitized authentic log excerpt](github-actions-main-99-tests.log) is included.

## Run locally (Python 3.9+)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export DJANGO_SECRET_KEY="$(python -c 'from secrets import token_urlsafe; print(token_urlsafe(48))')"
export DJANGO_DEBUG=True
python manage.py migrate
python manage.py test portal galiel_ops
```

Test databases are temporary. Do not run the suite against a live production database or actual private client media directory.

## HostGator

Use the verified production virtual environment and private, test-only settings. The preferred command remains:

```bash
PYTHONPATH=/home2/gfrancossh/galiel /path/to/python manage.py test portal galiel_ops --noinput
```

Capture a complete sanitized test output, including the number of tests and final status. Additional backup-scope tests are in `galiel_ops/tests_backup.py` and can also be explicitly run with `python manage.py test galiel_ops.tests_backup`.

## Privacy and safety test cases

- Login required for protected pages.
- Clients cannot view or delete each other's applications, alerts, fiscal information, or documents.
- Submitted applications cannot be deleted.
- Uploaded private documents stay private; draft-only deletion.
- Process-wizard fields and status transitions.
- New announcements filtered by publication/expiry date.
- Client reminder read/dismiss and unread count.
- Email copies and due-soon reminders.
- Checkout initiation blocked while payments are on hold.
- SQLite backup includes only case/client/contact-lead uploads.
