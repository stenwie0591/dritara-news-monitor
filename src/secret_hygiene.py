"""Controlli centralizzati sui permessi dei file contenenti segreti."""

import os
import stat
from pathlib import Path

from src.config import BASE_DIR


class SecretPermissionError(RuntimeError):
    """Un file sensibile esiste con tipo o permessi non sicuri."""


def ensure_private_file(path: Path, *, required: bool = False) -> bool:
    """Richiede un file regolare, non symlink, leggibile solo dal proprietario."""
    if path.is_symlink():
        raise SecretPermissionError(f"File sensibile non valido (symlink): {path}")
    if not path.exists():
        if required:
            raise FileNotFoundError(f"File sensibile non trovato: {path}")
        return False

    metadata = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(metadata.st_mode):
        raise SecretPermissionError(f"Percorso sensibile non regolare: {path}")
    mode = stat.S_IMODE(metadata.st_mode)
    if mode != 0o600:
        raise SecretPermissionError(
            f"Permessi non sicuri per {path}: {mode:04o}; richiesti 0600"
        )
    return True


def ensure_private_directory(path: Path, *, required: bool = False) -> bool:
    """Richiede una directory non symlink accessibile solo dal proprietario."""
    if path.is_symlink():
        raise SecretPermissionError(f"Directory sensibile non valida (symlink): {path}")
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Directory sensibile non trovata: {path}")
        return False

    metadata = path.stat(follow_symlinks=False)
    if not stat.S_ISDIR(metadata.st_mode):
        raise SecretPermissionError(f"Percorso sensibile non è una directory: {path}")
    mode = stat.S_IMODE(metadata.st_mode)
    if mode != 0o700:
        raise SecretPermissionError(
            f"Permessi non sicuri per {path}: {mode:04o}; richiesti 0700"
        )
    return True


def write_private_text(path: Path, content: str) -> None:
    """Scrive/tronca un file imponendo 0600 anche quando esiste già."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def read_private_text(path: Path) -> str:
    """Legge un file 0600 dal descriptor validato, senza seguire symlink."""
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        mode = stat.S_IMODE(metadata.st_mode)
        if not stat.S_ISREG(metadata.st_mode) or mode != 0o600:
            raise SecretPermissionError(
                f"File sensibile non sicuro: {path}; richiesti file regolare e 0600"
            )
        with os.fdopen(descriptor, encoding="utf-8") as stream:
            descriptor = -1
            return stream.read()
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def validate_runtime_secret_modes(base_dir: Path = BASE_DIR) -> None:
    """Valida i file sensibili locali presenti prima del bootstrap runtime."""
    for filename in (".env", "credentials_oauth.json", "token_drive.json"):
        ensure_private_file(base_dir / filename)
