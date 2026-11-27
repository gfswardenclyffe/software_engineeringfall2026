#!/usr/bin/env python3
"""Safely add opt-in presenter assets to Apache's EXISTING Galiel index.html.

No database, credentials, or Django settings are touched. Exact byte backup,
atomic replacement, and a hash-checked rollback are included.

Examples:
  python scripts/galiel_xray_homepage.py --file "$HOME/galiel/index.html" --dry-run
  python scripts/galiel_xray_homepage.py --file "$HOME/galiel/index.html" --apply
  python scripts/galiel_xray_homepage.py --file "$HOME/galiel/index.html" --rollback --manifest PATH
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from datetime import datetime, timezone

CSS = b'<link rel="stylesheet" href="/static/portal/galiel-xray.css">'
JS = b'<script src="/static/portal/galiel-xray.js" defer></script>'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def compose(source):
    if b"</head>" not in source.lower() or b"</body>" not in source.lower():
        raise ValueError("Unrecognized homepage structure: expected closing head and body")
    data = source
    if CSS not in data:
        data = re.sub(b"</head>", lambda m: CSS + b"\n" + m.group(0), data,
                      count=1, flags=re.IGNORECASE)
    if JS not in data:
        data = re.sub(b"</body>", lambda m: JS + b"\n" + m.group(0), data,
                      count=1, flags=re.IGNORECASE)
    return data


def atomic_replace(path, payload, mode):
    fd, temp = tempfile.mkstemp(prefix=".galiel-xray-", dir=str(path.parent))
    try:
        os.fchmod(fd, stat.S_IMODE(mode))
        with os.fdopen(fd, "wb") as out:
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", type=Path, required=True)
    ap.add_argument("--backup-dir", type=Path, default=Path.home() / "galiel-private-files" / "xray-backups")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--rollback", action="store_true")
    ap.add_argument("--manifest", type=Path, help="Manifest generated during --apply")
    a = ap.parse_args()
    path = a.file.expanduser().resolve(strict=True)
    old = path.read_bytes()
    if a.rollback:
        if not a.manifest:
            ap.error("--rollback requires --manifest")
        m = json.loads(a.manifest.read_text())
        if str(path) != m["path"] or digest(old) != m["installed_sha256"]:
            raise SystemExit("STOP: current homepage differs from installed release. Do not overwrite changes.")
        backup = Path(m["backup"])
        original = backup.read_bytes()
        if digest(original) != m["original_sha256"]:
            raise SystemExit("STOP: backup hash mismatch.")
        atomic_replace(path, original, path.stat().st_mode)
        print("ROLLED BACK: " + digest(original))
        return
    new = compose(old)
    print(json.dumps({"path": str(path), "original_sha256": digest(old),
                      "installed_sha256": digest(new),
                      "changed": old != new, "mode": "dry-run" if a.dry_run else "apply"}, indent=2))
    if a.dry_run:
        return
    if new == old:
        print("Already installed; no files changed.")
        return
    backup_dir = a.backup_dir.expanduser().resolve()
    backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = backup_dir / ("index.html." + ts + ".before-xray")
    with backup.open("xb") as out:
        os.fchmod(out.fileno(), 0o600)
        out.write(old)
    manifest = backup_dir / ("xray-" + ts + ".manifest.json")
    data = {"path": str(path), "backup": str(backup), "original_sha256": digest(old),
            "installed_sha256": digest(new), "timestamp_utc": ts}
    with manifest.open("x") as out:
        os.fchmod(out.fileno(), 0o600)
        json.dump(data, out, indent=2)
    atomic_replace(path, new, path.stat().st_mode)
    print("INSTALLED; rollback manifest: " + str(manifest))


if __name__ == "__main__":
    main()
