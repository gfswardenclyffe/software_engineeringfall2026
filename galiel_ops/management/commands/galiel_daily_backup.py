"""Private, consistent SQLite + upload archive with 14-day retention.

Requires the operator to set a private directory outside the web document root.
A complete archive is written atomically, with no symlinks followed.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import os
import sqlite3
import tarfile
import tempfile
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help="Back up the live SQLite database and private uploads; retain the last 14 daily archives."

    def add_arguments(self,parser):
        parser.add_argument("--dry-run",action="store_true")
        parser.add_argument("--keep",type=int,default=14)

    def handle(self,*args,**options):
        if options["keep"]<1:
            raise CommandError("Retention must be positive.")
        database=Path(settings.DATABASES["default"]["NAME"]).resolve()
        media=Path(settings.MEDIA_ROOT).resolve()
        destination=media/"daily-backups"
        base=Path(settings.BASE_DIR).resolve()
        if not database.is_file() or not media.is_dir():
            raise CommandError("Database or private media directory missing.")
        if not (base != media and base not in media.parents):
            raise CommandError("Media root is not private.")
        if base in destination.parents or base==destination:
            raise CommandError("Backups cannot be under the public document root.")
        self.stdout.write(f"Database: {database}\nPrivate uploads: {media}\nBackup destination: {destination}")
        if options["dry_run"]:
            self.stdout.write("DRY RUN — no files written or pruned.")
            return
        destination.mkdir(mode=0o700,parents=True,exist_ok=True)
        os.chmod(destination,0o700)
        date=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        completed=destination/f"galiel-{date}.tar.gz"
        if completed.exists():
            raise CommandError("Snapshot timestamp collision.")
        with tempfile.TemporaryDirectory(prefix="galiel-backup-",dir=destination) as temp:
            snapshot=Path(temp)/"db.sqlite3"
            connection=sqlite3.connect(f"file:{database}?mode=ro",uri=True)
            target=sqlite3.connect(str(snapshot))
            try:
                connection.backup(target)
            finally:
                target.close()
                connection.close()
            pending=Path(temp)/"archive.tar.gz"
            with tarfile.open(pending,mode="w:gz") as archive:
                archive.add(snapshot,arcname="db.sqlite3",recursive=False)
                for root,dirs,files in os.walk(media,followlinks=False):
                    rootpath=Path(root)
                    dirs[:]=[d for d in dirs if (rootpath/d).resolve()!=destination and
                              not (rootpath/d).is_symlink()]
                    for name in files:
                        item=rootpath/name
                        if not item.is_file() or item.is_symlink() or destination in item.parents:
                            continue
                        archive.add(item,arcname=str(Path("uploads")/item.relative_to(media)),recursive=False)
            with tarfile.open(pending,mode="r:gz") as archive:
                if "db.sqlite3" not in archive.getnames():
                    raise CommandError("Backup validation failed.")
            os.chmod(pending,0o600)
            os.replace(pending,completed)
        archives=sorted(destination.glob("galiel-????????T??????Z.tar.gz"))
        for obsolete in archives[:-options["keep"]]:
            obsolete.unlink()
        digest=hashlib.sha256(completed.read_bytes()).hexdigest()
        self.stdout.write(f"BACKUP OK: {completed} SHA256 {digest}")
