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

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", self.name.strip() if isinstance(self.name, str) else "")
        object.__setattr__(self, "issuer", self.issuer.strip() if isinstance(self.issuer, str) else "")
        object.__setattr__(self, "secret", normalize_secret(self.secret))
        object.__setattr__(self, "algorithm", self.algorithm.upper().replace("-", ""))
        object.__setattr__(self, "kind", self.kind.lower())
        if not (self.name or self.issuer):
            raise MigrationError("OTP account has no name or issuer")
        if self.kind not in {"totp", "hotp"}:
            raise MigrationError("Unsupported OTP type")
        if self.algorithm not in {"SHA1", "SHA256", "SHA512"}:
            raise MigrationError("Unsupported OTP algorithm")
        if type(self.digits) is not int or not 4 <= self.digits <= 10:
            raise MigrationError("Unsupported OTP digit count")
        if type(self.period) is not int or not 1 <= self.period <= 3600:
            raise MigrationError("Unsupported OTP period")
        if type(self.counter) is not int or self.counter < 0:
            raise MigrationError("Invalid HOTP counter")
