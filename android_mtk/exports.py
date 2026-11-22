"""Offline multi-authenticator exports; never writes secrets to stdout."""
from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import quote, urlencode
import uuid

from .model import MigrationError, Token

EXPORTS = {"uris", "aegis", "proton", "qr"}


def to_uri(token: Token) -> str:
    # Encode issuer/name separately, keeping only the separator colon literal.
    label = (f"{quote(token.issuer, safe='')}:{quote(token.name, safe='')}"
             if token.issuer and token.name else quote(token.name or token.issuer, safe=""))
    query = {"secret": token.secret, "algorithm": token.algorithm, "digits": str(token.digits)}
    if token.issuer:
        query["issuer"] = token.issuer
    if token.kind == "hotp":
        query["counter"] = str(token.counter)
    else:
        query["period"] = str(token.period)
    return f"otpauth://{token.kind}/{label}?{urlencode(query)}"


def aegis_document(tokens: list[Token]) -> dict:
    entries = []
    for token in tokens:
        info = {"secret": token.secret, "algo": token.algorithm, "digits": token.digits}
        info["period" if token.kind == "totp" else "counter"] = (
            token.period if token.kind == "totp" else token.counter
        )
        entries.append({"type": token.kind, "uuid": str(uuid.uuid4()),
                        "name": token.name, "issuer": token.issuer, "icon": None,
                        "info": info})
    return {"version": 1, "header": {"slots": None, "params": None},
            "db": {"version": 3, "entries": entries, "groups": []}}


def proton_document(tokens: list[Token]) -> dict:
    return {"version": 1, "entries": [
        {"id": str(uuid.uuid4()), "content": {"uri": to_uri(t), "entry_type":
            "Hotp" if t.kind == "hotp" else "Totp", "name": t.name or t.issuer},
         "note": None} for t in tokens
    ]}


def _is_safe_dir(path: Path) -> None:
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        raise MigrationError(f"Unsafe output directory: {path}")
    parent = path
    while not parent.exists():
        parent = parent.parent
    if parent.is_symlink():
        raise MigrationError(f"Parent output path is a symbolic link: {parent}")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt":
        os.chmod(path, 0o700)


def _save_bytes(path: Path, content: bytes, overwrite: bool) -> None:
    """Atomic new-file creation; refuse clobbering any existing file unless requested."""
    if path.exists() or path.is_symlink():
        if not overwrite or path.is_symlink() or not path.is_file():
            raise MigrationError(f"Output exists; use --force to replace a regular file: {path}")
    fd, tmp = tempfile.mkstemp(prefix=".staging-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(tmp, 0o600)
        if not overwrite and (path.exists() or path.is_symlink()):
            raise MigrationError(f"Output already exists: {path}")
        if path.is_symlink():
            raise MigrationError(f"Refusing symlink output: {path}")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _json(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
