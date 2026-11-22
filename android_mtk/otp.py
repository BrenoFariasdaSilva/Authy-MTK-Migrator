"""Standard RFC 4226/6238 OTP implementation for opt-in verification."""
from __future__ import annotations
import base64
import hashlib
import hmac
import struct
import time

from .model import Token


def calculate_code(token: Token, timestamp: int | None = None) -> str:
    if token.kind == "totp":
        counter = int((time.time() if timestamp is None else timestamp) // token.period)
    else:
        counter = token.counter
    key = base64.b32decode(token.secret + "=" * ((-len(token.secret)) % 8))
    digest = hmac.new(key, struct.pack(">Q", counter), getattr(hashlib, token.algorithm.lower())).digest()
    offset = digest[-1] & 15
    binary = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(binary % (10 ** token.digits)).zfill(token.digits)
