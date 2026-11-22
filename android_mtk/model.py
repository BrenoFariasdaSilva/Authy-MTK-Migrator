"""Validated, format-independent OTP account model."""
from __future__ import annotations

from dataclasses import dataclass
import base64
import binascii
import re
