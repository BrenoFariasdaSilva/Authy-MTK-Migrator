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
