"""Strict XML, URI and JSON readers; input is local and never uploaded."""
from __future__ import annotations

import base64
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, unquote, urlsplit
import xml.etree.ElementTree as ET

from .model import MigrationError, Token, unique_tokens
