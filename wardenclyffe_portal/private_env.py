"""Fail-closed, dependency-free private configuration loader for Galiel (Python 3.9).

Production secrets are stored only in ~/galiel_env/.env, never in the
document root, repository, or FastCGI entrypoint. Does not execute shell code.
"""
import os
import stat
from pathlib import Path


_PRIVATE_KEYS = frozenset((
    "GALIEL_ENV", "DJANGO_SECRET_KEY", "DJANGO_DEBUG", "DJANGO_ALLOWED_HOSTS",
    "DJANGO_EMAIL_BACKEND", "DJANGO_EMAIL_HOST", "DJANGO_EMAIL_PORT",
    "DJANGO_EMAIL_USER", "DJANGO_EMAIL_PASSWORD", "DJANGO_EMAIL_USE_SSL",
    "DJANGO_EMAIL_USE_TLS", "DJANGO_DEFAULT_FROM_EMAIL",
    "GALIEL_STRIPE_SECRET_KEY", "GALIEL_STRIPE_WEBHOOK_SECRET",
    "DJANGO_PRIVATE_MEDIA_ROOT",
))


def load_private_env():
    """Read a single private production file or explicitly enter development.

    Production is the default. A missing/unsafe file is fatal. In development,
    an optional local .env is deliberately NOT loaded automatically; developers
    may export values or use a gitignored file with their own tooling.
    """
    env_mode = os.environ.get("GALIEL_ENV", "production")
    if env_mode == "development":
        return
    if env_mode != "production":
        raise RuntimeError("GALIEL_ENV must be production or development.")

    home = Path.home().resolve()
    directory = home / "galiel_env"
    file_path = directory / ".env"

    # Symlinks must not redirect secrets into a web-accessible directory.
    if directory.is_symlink() or file_path.is_symlink():
        raise RuntimeError("Private environment directory/file must not be symlinks.")
    if not directory.is_dir():
        raise RuntimeError("Private production environment directory is missing.")

    ds = directory.stat()
    if ds.st_uid != os.getuid() or stat.S_IMODE(ds.st_mode) != 0o700:
        raise RuntimeError("Private environment directory must be owned by this user and chmod 700.")

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(str(file_path), flags)
    try:
        fs = os.fstat(fd)
        if not stat.S_ISREG(fs.st_mode):
            raise RuntimeError("Private environment file must be a regular file.")
        if fs.st_uid != os.getuid() or stat.S_IMODE(fs.st_mode) != 0o600:
            raise RuntimeError("Private environment file must be owned by this user and chmod 600.")
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            fd = -1
            raw_lines = stream.read(65537)
    finally:
        if fd >= 0:
            os.close(fd)
    if len(raw_lines) > 65536:
        raise RuntimeError("Private environment file exceeds 64 KiB.")

    values = {}
    for line_number, raw_line in enumerate(raw_lines.splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise RuntimeError("Malformed private configuration on line {}.".format(line_number))
        name, value = line.split("=", 1)
        name = name.strip()
        if name not in _PRIVATE_KEYS:
            raise RuntimeError("Unknown private configuration name on line {}.".format(line_number))
        if name in values:
            raise RuntimeError("Duplicate private configuration name on line {}.".format(line_number))
        if not value.strip() or "\x00" in value or "\r" in value:
            raise RuntimeError("Empty/invalid private configuration value on line {}.".format(line_number))
        values[name] = value

    if values.get("GALIEL_ENV") != "production":
        raise RuntimeError("Private configuration must explicitly set GALIEL_ENV=production.")
    if values.get("DJANGO_DEBUG") != "False":
        raise RuntimeError("Private production configuration must set DJANGO_DEBUG=False.")
    if not values.get("DJANGO_SECRET_KEY") or len(values["DJANGO_SECRET_KEY"]) < 50:
        raise RuntimeError("Private production secret key must be at least 50 characters.")
    if values.get("DJANGO_ALLOWED_HOSTS") != (
        "galiel.wardenclyffefirm.com,www.galiel.wardenclyffefirm.com"
    ):
        raise RuntimeError("Private production allowed-host configuration is invalid.")

    # File is authoritative even if the web server inherited stale variables.
    os.environ.update(values)
