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


def restore_backup(source: Path, dest: Path, password: str, force: bool = False) -> list[Path]:
    if not source.is_file() or source.is_symlink() or source.stat().st_size > MAX_ENCRYPTED:
        raise MigrationError("Backup missing, unsafe, or too large")
    data = source.read_bytes()
    if not data.startswith(MAGIC) or len(data) < len(MAGIC) + 16 + 12 + 16:
        raise MigrationError("Invalid encrypted backup header")
    at = len(MAGIC)
    try:
        payload = AESGCM(_key(password, data[at:at + 16])).decrypt(
            data[at + 16:at + 28], data[at + 28:], MAGIC)
    except InvalidTag as exc:
        raise MigrationError("Incorrect password or damaged encrypted backup") from exc
    _is_safe_dir(dest)
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        items = [entry for entry in archive.infolist() if not entry.is_dir()]
        if sum(i.file_size for i in items) > MAX_UNCOMPRESSED:
            raise MigrationError("Decrypted archive too large")
        paths: list[Path] = []
        for info in items:
            rel = PurePosixPath(info.filename)
            if (rel.is_absolute() or ".." in rel.parts or len(rel.parts) > 4 or
                    (info.external_attr >> 16) & 0o170000 == 0o120000):
                raise MigrationError("Unsafe path in encrypted archive")
            path = dest.joinpath(*rel.parts)
            if path.is_symlink() or (path.exists() and not force):
                raise MigrationError("Existing or unsafe restored file; use --force only for regular files")
            paths.append(path)
        for info, path in zip(items, paths):
            _is_safe_dir(path.parent)
            _save_bytes(path, archive.read(info), force)
    return paths
