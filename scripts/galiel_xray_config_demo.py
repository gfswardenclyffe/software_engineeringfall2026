#!/usr/bin/env python3
"""Set the X-Ray demo process ID in both identical, Apache-served JSON files.

Dry-run by default. A single integer is supplied by `galiel_xray_demo --apply`.
No private account credentials or names are stored in the public JSON file.
"""
import argparse
import hashlib
import json
from pathlib import Path


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--demo-process-id", type=int, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.demo_process_id < 1:
        parser.error("Demo process ID must be positive.")
    root = args.root.expanduser().resolve()
    paths = [root / "portal/static/portal/galiel-xray-stops.json",
             root / "static/portal/galiel-xray-stops.json"]
    if not all(p.is_file() and not p.is_symlink() for p in paths):
        parser.error("Both X-Ray JSON source files must exist and be regular files.")
    if paths[0].read_bytes() != paths[1].read_bytes():
        parser.error("Static JSON mirrors differ; do not continue.")
    data = json.loads(paths[0].read_text(encoding="utf-8"))
    if len(data.get("stops", [])) != 28:
        parser.error("Unexpected stop count.")
    current = data["settings"].get("demo_process_id")
    if current not in (None, args.demo_process_id):
        parser.error("Existing demo process ID differs; refusing to overwrite.")
    data["settings"]["demo_process_id"] = args.demo_process_id
    replacement = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    print("Original SHA256:", checksum(paths[0]))
    print("Configured SHA256:", hashlib.sha256(replacement).hexdigest())
    print("Demo process ID:", args.demo_process_id)
    if not args.apply:
        print("DRY RUN: no writes.")
        return
    # Deployment wrapper must have backed up the original files beforehand.
    for path in paths:
        path.write_bytes(replacement)
    print("APPLIED: both JSON copies are byte identical.")


if __name__ == "__main__":
    main()
