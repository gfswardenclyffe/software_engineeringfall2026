# Verified GitHub Actions test run — 18 November 2026

**Result:** 99 tests executed successfully; no failures or errors.

- **Run:** [Django checks #44359860542](https://github.com/gfswardenclyffe/software_engineeringfall2026/actions/runs/44359860542)
- **Source commit:** `97e8ddcd5e6ac69206c1ae78e1383921ef4f2e95`
- **Job:** `django`
- **Test command:** `.venv/bin/python manage.py test portal galiel_ops --noinput --verbosity 2`
- **Environment:** Ubuntu GitHub Actions runner, isolated Python virtual environment and ephemeral CI signing key.
- **Migration guard:** `portal/migrations/0012_pricing_research.py` absent, `makemigrations --check --dry-run` passed.
- **Applied test-database migrations:** `portal.0001` through `portal.0011_contact_leads` and `galiel_ops.0001_initial`.
- **Django system checks:** 0 issues.

Verified job-log ending:

```text
System check identified no issues (0 silenced).
Ran 99 tests in 14.288s
OK
```

This is **actual GitHub CI evidence**, distinct from the operator-reported 95-test HostGator run. The two runs may have different test counts because of the added backup regression tests and test-file changes. No production client records were used by GitHub Actions.

The job log includes a deliberate mocked SMTP failure test, which is reported as `ok` and does **not** indicate a failing test.
