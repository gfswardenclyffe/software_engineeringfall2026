"""Load Galiel's private HostGator environment without printing credentials.

Production: /home2/gfrancossh/galiel_env/.env
Staging: set GALIEL_ENV_FILE in the staging FastCGI process to its private file.
Import this before Django settings are initialized. Do not expose this file over HTTP.
"""
import os
from pathlib import Path

_DEFAULT_ENV = Path("/home2/gfrancossh/galiel_env/.env")


def load_env():
    env_path = Path(os.environ.get("GALIEL_ENV_FILE", str(_DEFAULT_ENV)))
    if env_path.is_symlink():
        raise RuntimeError("Galiel environment must not be a symbolic link")
    if not env_path.is_file():
        raise RuntimeError("Galiel private environment file is missing")
    if env_path.stat().st_mode & 0o077:
        raise RuntimeError("Galiel environment permissions are too permissive")
    # Accept simple KEY=VALUE lines, quoted or unquoted, without shell execution.
    # Values in the verified private file take precedence over stale process values.
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            raise RuntimeError("Invalid Galiel environment line")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key.isidentifier() or not key.isascii():
            raise RuntimeError("Invalid Galiel environment variable name")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ[key] = value
