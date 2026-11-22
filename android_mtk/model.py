"""Validated, format-independent OTP account model."""
from __future__ import annotations

from dataclasses import dataclass
import base64
import binascii
import re


class MigrationError(Exception):
    """Expected, actionable migration error (never includes secrets)."""


def normalize_secret(raw: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise MigrationError("Missing OTP secret")
    secret = re.sub(r"\s+", "", raw).upper().rstrip("=")
    if not re.fullmatch(r"[A-Z2-7]+", secret):
        raise MigrationError("Secret is not valid Base32")
    try:
        decoded = base64.b32decode(secret + "=" * ((-len(secret)) % 8), casefold=True)
    except (binascii.Error, ValueError) as exc:
        raise MigrationError("Secret is not valid Base32") from exc
    if not decoded:
        raise MigrationError("OTP secret decodes to no bytes")
    return base64.b32encode(decoded).decode("ascii").rstrip("=")


@dataclass(frozen=True)
class Token:
    name: str
    issuer: str
    secret: str
    digits: int = 6
    period: int = 30
    algorithm: str = "SHA1"
    kind: str = "totp"
    counter: int = 0
