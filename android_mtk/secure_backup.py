"""Optional password-encrypted offline backup of generated export files.

Format: magic + 16-byte salt + 12-byte nonce + AES-256-GCM ciphertext of ZIP.
Compatible with this project's `restore-backup` command, not an app-native file.
"""
from __future__ import annotations

from io import BytesIO
import os
from pathlib import Path, PurePosixPath
import zipfile

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .model import MigrationError
from .exports import _is_safe_dir, _save_bytes

MAGIC = b"AMTKBACKUP01\x00"
MAX_ENCRYPTED = 128 * 1024 * 1024
MAX_UNCOMPRESSED = 256 * 1024 * 1024


def _key(password: str, salt: bytes) -> bytes:
    if not password or len(password) < 12:
        raise MigrationError("Backup password must be at least 12 characters")
    # scrypt slows offline guessing. Existing files remain plaintext until removed.
    try:
        return __import__("hashlib").scrypt(password.encode(), salt=salt, n=2**15, r=8, p=1, dklen=32,
                                              maxmem=128 * 1024 * 1024)
    except (ValueError, MemoryError) as exc:
        raise MigrationError("Insufficient memory for backup password derivation") from exc


def create_backup(files: list[Path], root: Path, target: Path, password: str, force: bool = False) -> None:
    if target.is_symlink() or (target.exists() and not force):
        raise MigrationError("Encrypted backup already exists or is a symlink")
    _is_safe_dir(target.parent)
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in files:
            if not source.is_file() or source.is_symlink():
                raise MigrationError("Backup includes unsafe input file")
            rel = source.relative_to(root).as_posix()
            archive.write(source, rel)
            if buf.tell() > MAX_UNCOMPRESSED:
                raise MigrationError("Too much data for encrypted backup")
    payload = buf.getvalue()
    if len(payload) > MAX_ENCRYPTED:
        raise MigrationError("Encrypted backup too large")
    salt, nonce = os.urandom(16), os.urandom(12)
    ciphertext = AESGCM(_key(password, salt)).encrypt(nonce, payload, MAGIC)
    _save_bytes(target, MAGIC + salt + nonce + ciphertext, force)
