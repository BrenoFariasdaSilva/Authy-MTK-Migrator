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
