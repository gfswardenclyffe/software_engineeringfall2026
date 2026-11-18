"""Consistent SQLite + explicitly allowlisted private client uploads only.

Other MEDIA_ROOT children, including historic backups, staging, quarantine,
environment files and logs are NEVER traversed.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
import hashlib
import os
import sqlite3
import stat
import tarfile
import tempfile
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

UPLOAD_FOLDERS = ("case_documents", "client_documents", "contact_leads")
BLOCKED_SUFFIXES = (".env", ".lock", ".log")

def inside(child, parent):
    return child == parent or parent in child.parents

def excluded(name, directory=False):
    lower = name.casefold()
    if lower.startswith(".") or lower.endswith(BLOCKED_SUFFIXES):
        return True
    return bool(directory and ("quarantine" in lower or "staging" in lower
        or lower == "daily-backups" or lower.endswith("-backups")
        or lower in ("backup", "backups", "logs", "__pycache__", ".git")))

def collect_uploads(media):
    result = []
    roots = []
    for folder_name in UPLOAD_FOLDERS:
        root = media / folder_name
        if root.is_symlink():
            raise CommandError("Upload directory cannot be a symlink: " + str(root))
        if root.exists() and (not root.is_dir() or root.resolve() != root):
            raise CommandError("Unexpected upload directory: " + str(root))
        roots.append((folder_name, root))
        if not root.exists():
            continue
        for current, directories, names in os.walk(root, topdown=True, followlinks=False):
            base = Path(current)
            permitted_dirs = []
            for name in sorted(directories):
                path = base / name
                if excluded(name, directory=True):
                    continue
                if path.is_symlink():
                    raise CommandError("Symlink in upload directory: " + str(path))
                permitted_dirs.append(name)
            directories[:] = permitted_dirs
            for name in sorted(names):
                if excluded(name):
                    continue
                path = base / name
                if path.is_symlink():
                    raise CommandError("Symlink in upload directory: " + str(path))
                if not stat.S_ISREG(path.lstat().st_mode):
                    raise CommandError("Special file in upload directory: " + str(path))
                relative = Path(folder_name) / path.relative_to(root)
                result.append((path, relative))
    return roots, result

class Command(BaseCommand):
    help = "Snapshot SQLite and case_documents/client_documents/contact_leads only; 14-day retention."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--keep", type=int, default=14)

    def handle(self, *args, **options):
        days = options["keep"]
        if not 1 <= days <= 365:
            raise CommandError("--keep must be between 1 and 365 days")
        if settings.DATABASES["default"].get("ENGINE") != "django.db.backends.sqlite3":
            raise CommandError("SQLite database required")
        database = Path(settings.DATABASES["default"]["NAME"]).resolve(strict=True)
        configured_media = Path(settings.MEDIA_ROOT)
        if configured_media.is_symlink():
            raise CommandError("Private media root cannot be a symlink")
        media = configured_media.resolve(strict=True)
        configured_destination = media / "daily-backups"
        if configured_destination.is_symlink():
            raise CommandError("Backup destination cannot be a symlink")
        destination = configured_destination.resolve(strict=False)
        app_root = Path(settings.BASE_DIR).resolve()
        if not database.is_file() or not media.is_dir():
            raise CommandError("Private media or database missing")
        if inside(media, app_root) or inside(destination, app_root):
            raise CommandError("Private media and backups must be outside application")
        if not inside(destination, media):
            raise CommandError("Destination must be inside private media root")
        roots, uploads = collect_uploads(media)
        for _, root in roots:
            if inside(destination, root) or inside(root, destination):
                raise CommandError("Backup destination overlaps an included upload folder")
        if inside(database, destination):
            raise CommandError("Database must not be within backup destination")
        self.stdout.write("INCLUDED: SQLite snapshot: " + str(database))
        self.stdout.write("INCLUDED UPLOAD FOLDERS (and only these):")
        for name, root in roots:
            selected = [p for p, rel in uploads if rel.parts[0] == name]
            count = len(selected)
            size = sum(p.stat().st_size for p in selected)
            self.stdout.write(f"  {root}: {count} files, {size} bytes" +
                              (" (not yet created)" if not root.is_dir() else ""))
        self.stdout.write("EXCLUDED: all other private media folders, *-backups/, "
                          "daily-backups/, quarantine/, staging/, *.env, *.lock, *.log, symlinks")
        self.stdout.write(f"Backup destination: {destination}")
        self.stdout.write(f"Archive will contain {len(uploads)+1} files total")
        if options["dry_run"]:
            self.stdout.write("DRY RUN PASS; no snapshot or rotation")
            return
        destination.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(destination, 0o700)
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%dT%H%M%SZ")
        final = destination / f"galiel-{timestamp}.tar.gz"
        if final.exists():
            raise CommandError("Snapshot timestamp already exists")
        with tempfile.TemporaryDirectory(prefix="galiel-new-", dir=destination) as temp:
            db_copy = Path(temp) / "db.sqlite3"
            source = sqlite3.connect("file:" + quote(str(database), safe="/") + "?mode=ro", uri=True)
            target = sqlite3.connect(str(db_copy))
            try:
                source.backup(target)
                if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise CommandError("SQLite snapshot integrity check failed")
            finally:
                target.close()
                source.close()
            staged = Path(temp) / "archive.tar.gz"
            with tarfile.open(staged, "w:gz") as archive:
                archive.add(db_copy, arcname="db.sqlite3", recursive=False)
                for absolute, relative in uploads:
                    if absolute.is_symlink() or not absolute.is_file():
                        raise CommandError("Upload changed during snapshot: " + str(absolute))
                    archive.add(absolute, arcname=str(Path("uploads")/relative), recursive=False)
            with tarfile.open(staged, "r:gz") as archive:
                entries = archive.getmembers()
                expected = {"db.sqlite3"} | {str(Path("uploads")/rel) for _, rel in uploads}
                if {entry.name for entry in entries} != expected or len(entries) != len(expected):
                    raise CommandError("Archive file membership mismatch")
                if not all(entry.isfile() and not entry.issym() and not entry.islnk() for entry in entries):
                    raise CommandError("Archive contains nonregular member")
            os.chmod(staged, 0o600)
            os.replace(staged, final)
        cutoff = now - timedelta(days=days)
        for old in destination.glob("galiel-????????T??????Z.tar.gz"):
            try:
                stamp = datetime.strptime(old.name[7:-7], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            if stamp < cutoff and old.is_file() and not old.is_symlink():
                old.unlink()
        digest = hashlib.sha256()
        with final.open("rb") as fd:
            for block in iter(lambda: fd.read(1048576), b""):
                digest.update(block)
        self.stdout.write(f"BACKUP OK: {final} SHA256 {digest.hexdigest()}")
