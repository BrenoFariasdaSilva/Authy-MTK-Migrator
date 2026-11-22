"""Strict XML, URI and JSON readers; input is local and never uploaded."""
from __future__ import annotations

import base64
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, unquote, urlsplit
import xml.etree.ElementTree as ET

from .model import MigrationError, Token, unique_tokens

AUTHY_FILES = (
    "com.authy.storage.tokens.authenticator.xml",
    "com.authy.storage.tokens.authy.xml",
)
MAX_INPUT = 24 * 1024 * 1024


def _read(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise MigrationError(f"Not a regular input file: {path}")
    if path.stat().st_size > MAX_INPUT:
        raise MigrationError(f"Input file exceeds {MAX_INPUT // 1024 // 1024} MiB: {path}")
    return path.read_bytes()


def _decrypt_authy(secret_b64: str, salt: str, password: str) -> str:
    """Match the current Aegis Authy importer: PBKDF2-SHA1/1000 + AES-CBC/zero IV."""
    from cryptography.hazmat.primitives import hashes, padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    try:
        ciphertext = base64.b64decode(secret_b64, validate=True)
        if len(ciphertext) == 0 or len(ciphertext) % 16:
            raise ValueError("Invalid ciphertext length")
        kdf = PBKDF2HMAC(algorithm=hashes.SHA1(), length=32,
                        salt=salt.encode("utf-8"), iterations=1000)
        key = kdf.derive(password.encode("utf-8"))
        cipher = Cipher(algorithms.AES(key), modes.CBC(bytes(16)))
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        return (unpadder.update(padded) + unpadder.finalize()).decode("utf-8")
    except (ValueError, UnicodeError, TypeError) as exc:
        raise MigrationError("Authy backup password is incorrect, or encrypted entry is malformed") from exc
