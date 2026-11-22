"""Synthetic-only regression tests. No production credentials or device needed."""
import base64
from contextlib import redirect_stdout, redirect_stderr
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from android_mtk.cli import main
from android_mtk.device import _require_ext4, dump_userdata, extract_authy_xml
from android_mtk.exports import to_uri, write_exports
from android_mtk.model import MigrationError, Token, normalize_secret
from android_mtk.otp import calculate_code
from android_mtk.parsers import load_authy_xml, load_json, load_tokens, load_uris, parse_uri

SEED = "JBSWY3DPEHPK3PXP"  # Public, well-known synthetic example; NOT a real account.


def xml_doc(records, key="com.authy.storage.tokens.authenticator.key"):
    from xml.sax.saxutils import escape
    return f'<map><string name="{key}">{escape(json.dumps(records))}</string></map>'


if __name__ == "__main__":
    unittest.main()
