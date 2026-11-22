"""Standard RFC 4226/6238 OTP implementation for opt-in verification."""
from __future__ import annotations
import base64
import hashlib
import hmac
import struct
import time

from .model import Token
