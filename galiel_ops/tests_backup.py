"""Regression coverage for strictly scoped nightly backups; no live database access."""
from pathlib import Path
import os
import sqlite3
import tarfile
import tempfile
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

class BackupScopeTests(SimpleTestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory(prefix="galiel-backup-test-")
        self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name)
        self.app=self.root/"app"
        self.app.mkdir()
        self.db=self.app/"db.sqlite3"
        con=sqlite3.connect(self.db)
        con.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)")
        con.execute("INSERT INTO sample(value) VALUES ('consistent')")
        con.commit();con.close()
        self.media=self.root/"galiel-private-files"
        self.media.mkdir()
        for name in ("case_documents", "client_documents", "daily-backups", "release-backups",
                     "workflow-deploy-backups", "homepage-release-backups", "quarantine-staging"):
            (self.media/name).mkdir()
        (self.media/"case_documents"/"valid.pdf").write_bytes(b"%PDF test fixture")
        (self.media/"client_documents"/"other.pdf").write_bytes(b"%PDF client test fixture")
        (self.media/"case_documents"/"staging.env").write_text("SECRET_DO_NOT_BACK_UP")
        (self.media/"case_documents"/"trace.log").write_text("NOT_A_CLIENT_UPLOAD")
        (self.media/"case_documents"/"sessions.lock").write_text("NOT_A_CLIENT_UPLOAD")
        (self.media/"case_documents"/"quarantine").mkdir()
        (self.media/"case_documents"/"quarantine"/"old.pdf").write_bytes(b"QUARANTINED")
        (self.media/"release-backups"/"staging.env").write_text("SECRET_DO_NOT_BACK_UP")
        (self.media/"daily-backups"/"old.tar.gz").write_bytes(b"NOT_A_CLIENT_UPLOAD")
        self.config=override_settings(BASE_DIR=self.app, MEDIA_ROOT=self.media,
            DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":self.db}})
        self.config.enable()
        self.addCleanup(self.config.disable)

    def test_dry_run_lists_only_uploads_and_writes_nothing(self):
        out=StringIO()
        call_command("galiel_daily_backup",dry_run=True,stdout=out)
        report=out.getvalue()
        self.assertIn("case_documents",report)
        self.assertIn("client_documents",report)
        self.assertIn("Archive will contain 3 files total",report)
        self.assertFalse(list((self.media/"daily-backups").glob("galiel-*.tar.gz")))

    def test_archive_contains_only_db_and_two_client_documents(self):
        call_command("galiel_daily_backup",stdout=StringIO())
        files=list((self.media/"daily-backups").glob("galiel-*.tar.gz"))
        self.assertEqual(len(files),1)
        with tarfile.open(files[0],"r:gz") as archive:
            names=set(archive.getnames())
            self.assertEqual(names,{"db.sqlite3","uploads/case_documents/valid.pdf",
                                  "uploads/client_documents/other.pdf"})
            extracted=archive.extractfile("db.sqlite3").read()
            snap=self.root/"restored.sqlite3"
            snap.write_bytes(extracted)
            database=sqlite3.connect(snap)
            try:
                self.assertEqual(database.execute("SELECT value FROM sample").fetchone()[0],"consistent")
            finally:
                database.close()

    def test_upload_symlink_refused(self):
        outside=self.root/"outside.txt"
        outside.write_text("PRIVATE OTHER FILE")
        link=self.media/"case_documents"/"outside.pdf"
        link.symlink_to(outside)
        with self.assertRaises(CommandError):
            call_command("galiel_daily_backup",dry_run=True,stdout=StringIO())

    def test_backup_destination_symlink_refused(self):
        other=self.root/"other"
        other.mkdir()
        target=self.media/"daily-backups"
        target.rmdir()
        target.symlink_to(other,target_is_directory=True)
        with self.assertRaises(CommandError):
            call_command("galiel_daily_backup",dry_run=True,stdout=StringIO())
