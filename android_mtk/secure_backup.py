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
