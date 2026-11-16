"""One-time HostGator helper; execute only with explicit authorization.

Creates ~/galiel_env/.env with a new random secret (0600), without printing it.
Does not modify the live FastCGI process. Refuses to overwrite an existing file.
"""
import os
from pathlib import Path
from secrets import token_urlsafe

directory = Path.home() / "galiel_env"
file_path = directory / ".env"
old_umask = os.umask(0o077)
try:
    directory.mkdir(mode=0o700, exist_ok=True)
    if directory.is_symlink() or (directory.stat().st_mode & 0o077):
        raise RuntimeError("Refusing insecure directory. Require chmod 700.")
    content = (
        "GALIEL_ENV=production\n"
        "DJANGO_SECRET_KEY=" + token_urlsafe(64) + "\n"
        "DJANGO_DEBUG=False\n"
        "DJANGO_ALLOWED_HOSTS=galiel.wardenclyffefirm.com,www.galiel.wardenclyffefirm.com\n"
    )
    fd = os.open(str(file_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(content)
finally:
    os.umask(old_umask)
print("Private production environment created; no secret values displayed.")
