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


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def make_xml(self, rows, filename="com.authy.storage.tokens.authenticator.xml", key="com.authy.storage.tokens.authenticator.key"):
        p = self.root / filename
        p.write_text(xml_doc(rows, key), encoding="utf-8")
        return p

    def test_authenticator_ordinary(self):
        p = self.make_xml([{"name": "GitHub - alice", "originalIssuer": "GitHub",
                            "decryptedSecret": SEED, "digits": 6, "accountType": "github"}])
        tokens, errors = load_authy_xml(p)
        self.assertEqual(errors, [])
        self.assertEqual((tokens[0].issuer, tokens[0].name, tokens[0].period), ("GitHub", "alice", 30))

    def test_authy_10_second_hex_seed(self):
        p = self.make_xml([{"name": "Authy", "secretSeed": "0102030405060708090a", "digits": 7}],
                          "com.authy.storage.tokens.authy.xml", "com.authy.storage.tokens.authy.key")
        tokens, errors = load_authy_xml(p)
        self.assertEqual(errors, [])
        self.assertEqual(tokens[0].period, 10)
        self.assertEqual(tokens[0].digits, 7)
        self.assertEqual(tokens[0].secret, base64.b32encode(bytes.fromhex("0102030405060708090a")).decode().rstrip("="))


if __name__ == "__main__":
    unittest.main()
