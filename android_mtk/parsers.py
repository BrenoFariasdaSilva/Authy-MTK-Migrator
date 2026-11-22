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
