#!/usr/bin/env python3
"""Check *tracked current-tree files* for disallowed private data and common credential forms.

This is a targeted safety check, NOT a complete secret scanner and NOT a
Git-history audit. Run proper GitHub secret scanning and push protection too.
"""
from pathlib import Path
import re
import subprocess
import sys

SENSITIVE_DIRS = {
    "case_documents", "client_documents", "contact_leads",
    "galiel-private-files", "daily-backups", "release-backups",
    "quarantine", "private_media", "private-media",
}
TEXT_SUFFIXES = {".py", ".html", ".js", ".css", ".md", ".txt", ".yml", ".yaml", ".json", ".sh", ".svg", ".xml"}
SECRET_PATTERNS = {
    "private key PEM": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "AWS access key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "Stripe live secret": re.compile(rb"\bsk_live_[A-Za-z0-9]{10,}\b"),
    "GitHub access token": re.compile(rb"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    "GitHub fine-grained token": re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    "Google API key": re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b"),
}

def forbidden(path):
    lower = [p.casefold() for p in path.parts]
    name = lower[-1]
    if name in ("wp-config.php", ".env", "db.sqlite3") or name.endswith(".sqlite3"):
        return True
    if name.endswith(".env") or name.startswith(".env."):
        return True
    return any(p in SENSITIVE_DIRS or p.endswith("-backups") for p in lower[:-1])

def main():
    output = subprocess.check_output(["git", "ls-files", "-z"])
    paths = [Path(x.decode("utf-8")) for x in output.split(b"\0") if x]
    problems = []
    for path in paths:
        if forbidden(path):
            problems.append("Forbidden tracked file path: " + str(path))
        if path.suffix.lower() in TEXT_SUFFIXES:
            try:
                content = path.read_bytes()
            except OSError as exc:
                problems.append("Unreadable file: {}: {}".format(path, exc))
                continue
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(content):
                    problems.append("Potential {} in {}".format(label, path))
    for problem in problems:
        print("FAIL:", problem)
    if problems:
        print("AUDIT FAILED: {} finding(s)".format(len(problems)))
        return 1
    print("AUDIT PASS: {} tracked paths checked; no disallowed private files or known token formats found.".format(len(paths)))
    print("NOTE: This does not inspect historical commits or replace dedicated secret scanning.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
