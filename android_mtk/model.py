"""Validated, format-independent OTP account model."""
from __future__ import annotations

from dataclasses import dataclass
import base64
import binascii
import re


class MigrationError(Exception):
    """Expected, actionable migration error (never includes secrets)."""


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
