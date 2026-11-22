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


def _authy_record(record: dict, password: str | None) -> Token:
    # Authy's own 7-digit codes use raw hex seed and a 10-second period.
    own_token = bool(record.get("secretSeed"))
    if own_token:
        try:
            seed = base64.b32encode(bytes.fromhex(record["secretSeed"])).decode("ascii")
        except (ValueError, TypeError) as exc:
            raise MigrationError("Authy-specific token has an invalid hex seed") from exc
    elif record.get("decryptedSecret"):
        seed = record["decryptedSecret"]
    elif record.get("encryptedSecret"):
        if not password:
            raise MigrationError("Encrypted entries found: supply Authy backup password when prompted")
        if not isinstance(record.get("salt"), str):
            raise MigrationError("Encrypted Authy entry is missing its salt")
        seed = _decrypt_authy(record["encryptedSecret"], record["salt"], password)
    else:
        raise MigrationError("Authy entry contains no usable decrypted or encrypted secret")
    name = str(record.get("name") or "").strip()
    original_issuer = str(record.get("originalIssuer") or "").strip()
    original_name = str(record.get("originalName") or "").strip()
    account_type = str(record.get("accountType") or "").strip()
    if own_token:
        issuer, name = name or account_type or "Authy", ""
    elif original_issuer:
        issuer = original_issuer
        for prefix in (issuer + ":", issuer + " - "):
            if name.startswith(prefix):
                name = name[len(prefix):].lstrip()
                break
    elif ":" in original_name:
        issuer = original_name.split(":", 1)[0]
        name = re.sub(r"^" + re.escape(issuer) + r":\s*", "", name)
    elif " - " in name:
        issuer, name = name.split(" - ", 1)
    else:
        issuer = account_type.capitalize() or "Authy"
    try:
        digits = int(record.get("digits", 7 if own_token else 6))
    except (TypeError, ValueError) as exc:
        raise MigrationError("Authy token has an invalid digits field") from exc
    return Token(name=name, issuer=issuer, secret=seed, digits=digits,
                 period=10 if own_token else 30)


def load_authy_xml(path: Path, password: str | None = None) -> tuple[list[Token], list[str]]:
    content = _read(path)
    if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise MigrationError("XML document types and entities are not permitted")
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise MigrationError("Authy XML cannot be parsed; filesystem may be encrypted or unsupported") from exc
    if root.tag != "map":
        raise MigrationError("Expected Android shared-preferences XML <map> root")
    names = {"com.authy.storage.tokens.authenticator.key", "com.authy.storage.tokens.authy.key"}
    arrays = [x.text for x in root if x.tag == "string" and x.attrib.get("name") in names]
    if not arrays:
        raise MigrationError("No supported Authy token array found in shared-preferences XML")
    records: list[dict] = []
    for raw in arrays:
        try:
            data = json.loads(raw or "")
        except json.JSONDecodeError as exc:
            raise MigrationError("Authy token array contains invalid JSON") from exc
        if not isinstance(data, list):
            raise MigrationError("Authy token array must be a JSON list")
        if not all(isinstance(row, dict) for row in data):
            raise MigrationError("Authy token array contains invalid entries")
        records.extend(data)
    tokens, errors = [], []
    for index, entry in enumerate(records, start=1):
        try:
            tokens.append(_authy_record(entry, password))
        except MigrationError as exc:
            errors.append(f"Entry #{index}: {exc}")
    return unique_tokens(tokens), errors


def load_uris(path: Path) -> tuple[list[Token], list[str]]:
    tokens, errors = [], []
    try:
        lines = _read(path).decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as exc:
        raise MigrationError("URI input text must be valid UTF-8") from exc
    for index, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            tokens.append(parse_uri(line))
        except MigrationError as exc:
            errors.append(f"Line {index}: {exc}")
    return unique_tokens(tokens), errors
