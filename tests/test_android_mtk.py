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

    def test_password_protected_uses_aegis_kdf(self):
        from cryptography.hazmat.primitives import hashes, padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        salt, password = "test-salt", "correct horse battery staple"
        kdf = PBKDF2HMAC(algorithm=hashes.SHA1(), length=32, salt=salt.encode(), iterations=1000)
        pad = padding.PKCS7(128).padder()
        padded = pad.update(SEED.encode()) + pad.finalize()
        encryptor = Cipher(algorithms.AES(kdf.derive(password.encode())), modes.CBC(bytes(16))).encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()
        p = self.make_xml([{"name": "example", "accountType": "sample", "digits": 6,
                            "salt": salt, "encryptedSecret": base64.b64encode(ciphertext).decode()}])
        self.assertEqual(len(load_authy_xml(p)[1]), 1)
        tokens, errors = load_authy_xml(p, password)
        self.assertEqual(errors, [])
        self.assertEqual(tokens[0].secret, SEED)
        self.assertEqual(len(load_authy_xml(p, "wrong")[1]), 1)

    def test_malformed_xml_rejected(self):
        p = self.root / "invalid.xml"
        p.write_text("<!DOCTYPE map [<!ENTITY x 'x'>]><map>&x;</map>")
        with self.assertRaises(MigrationError):
            load_authy_xml(p)

    def test_malformed_secret_not_imported(self):
        p = self.make_xml([{"name": "good", "decryptedSecret": SEED, "digits": 6},
                           {"name": "bad", "decryptedSecret": "!!!!!", "digits": 6}])
        tokens, errors = load_authy_xml(p)
        self.assertEqual(len(tokens), 1)
        self.assertEqual(len(errors), 1)

    def test_parse_uri_roundtrip_hotp_and_totp(self):
        tokens = [Token(name="alice+bob@example.com", issuer="Example: Inc", secret=SEED,
                        digits=8, period=20, algorithm="SHA256"),
                  Token(name="john", issuer="GitHub", secret=SEED, kind="hotp", counter=44)]
        for token in tokens:
            self.assertEqual(parse_uri(to_uri(token)), token)

    def test_parse_uri_conflicting_issuer_is_rejected(self):
        with self.assertRaises(MigrationError):
            parse_uri(f"otpauth://totp/Foo:alice?issuer=Bar&secret={SEED}")

    def test_normalize_bad_base32_rejected(self):
        for value in ("", "not-base32!", "A", "1234567890"):
            with self.subTest(value=value):
                with self.assertRaises(MigrationError):
                    normalize_secret(value)

    def test_multi_xml_directory(self):
        self.make_xml([{"name": "GitHub - alice", "decryptedSecret": SEED, "digits": 6}])
        self.make_xml([{"name": "Authy", "secretSeed": "4142434445", "digits": 7}],
                      "com.authy.storage.tokens.authy.xml", "com.authy.storage.tokens.authy.key")
        tokens, errors = load_tokens(self.root)
        self.assertEqual(len(tokens), 2)
        self.assertEqual(errors, [])

    def test_rfc6238_vector(self):
        # RFC 6238 8-digit SHA1 test vector, T=59 seconds.
        raw = b"12345678901234567890"
        t = Token(name="RFC", issuer="example", secret=base64.b32encode(raw).decode(), digits=8)
        self.assertEqual(calculate_code(t, 59), "94287082")

    def test_exports_roundtrip(self):
        tokens = [Token(name="user", issuer="Example", secret=SEED, digits=7, period=10)]
        dest = self.root / "exports"
        paths = write_exports(tokens, dest, {"uris", "aegis", "proton", "qr"})
        self.assertEqual(len(paths), 6)
        self.assertEqual(load_uris(dest / "otpauth.txt")[0], tokens)
        self.assertEqual(load_json(dest / "aegis.json", "aegis")[0], tokens)
        self.assertEqual(load_json(dest / "proton_authenticator.json", "proton")[0], tokens)
        self.assertEqual(len(list((dest / "qr_codes").glob("*.png"))), 1)
        self.assertIn("Example", (dest / "qr_codes/index.csv").read_text())
        if os.name != "nt":
            self.assertEqual((dest / "aegis.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual(dest.stat().st_mode & 0o777, 0o700)
        with self.assertRaises(MigrationError):
            write_exports(tokens, dest, {"uris"})
        write_exports(tokens, dest, {"uris"}, force=True)

    def test_no_symlink_overwrite(self):
        target = self.root / "private"
        target.write_text("important")
        dest = self.root / "exports"
        dest.mkdir()
        try:
            (dest / "aegis.json").symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        with self.assertRaises(MigrationError):
            write_exports([Token(name="a", issuer="b", secret=SEED)], dest, {"aegis"}, force=True)
        self.assertEqual(target.read_text(), "important")

    def test_cli_fail_closed_on_partial(self):
        p = self.make_xml([{"name": "good", "decryptedSecret": SEED},
                           {"name": "bad", "decryptedSecret": "!"}])
        out = self.root / "result"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(main(["convert", "--input", str(p), "--out", str(out),
                                   "--acknowledge-secrets", "--formats", "aegis"]), 1)
        self.assertFalse((out / "aegis.json").exists())
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(main(["convert", "--input", str(p), "--out", str(out),
                                   "--acknowledge-secrets", "--allow-partial", "--formats", "aegis"]), 0)
        self.assertTrue((out / "aegis.json").is_file())

    def test_ios_json_import(self):
        p = self.root / "input.json"
        p.write_text(json.dumps({"decrypted_authenticator_tokens": [{
            "name": "Alice", "issuer": "Example", "decrypted_seed": SEED, "digits": 6
        }]}))
        tokens, errors = load_tokens(p)
        self.assertEqual(len(tokens), 1)
        self.assertEqual(errors, [])

    def test_ext4_signature(self):
        path = self.root / "userdata.img"
        data = bytearray(2048)
        with path.open("wb") as f: f.write(data)
        with self.assertRaises(MigrationError):
            _require_ext4(path)
        data[1024 + 0x38:1024 + 0x3a] = b"\x53\xef"
        path.write_bytes(data)
        _require_ext4(path)

    def test_read_only_mtkclient_invocation(self):
        import sys
        mtk = self.root / "mtkclient"
        mtk.mkdir()
        (mtk / "mtk.py").write_text("""import pathlib, sys
assert sys.argv[1:3] == ['r', 'userdata']
pathlib.Path(sys.argv[3]).write_bytes(b'0' * 4096)
""")
        image = self.root / "userdata.img"
        self.assertEqual(dump_userdata(mtk, image, sys.executable), image)
        with self.assertRaises(MigrationError):
            dump_userdata(mtk, image, sys.executable)

    def test_relative_mtk_interpreter_uses_absolute_path(self):
        import sys
        mtk = self.root / "mtkclient"
        mtk.mkdir()
        (mtk / "mtk.py").write_text("import pathlib,sys; pathlib.Path(sys.argv[3]).write_bytes(b'0'*4096)")
        image = self.root / "userdata.img"
        import os
        python_path = os.path.relpath(sys.executable, Path.cwd())
        self.assertEqual(dump_userdata(mtk, image, python_path), image)

    def test_extract_fake_debugfs(self):
        # Mock the debugfs boundary; real ext4 and device support require hardware testing.
        data = bytearray(2048)
        data[1080:1082] = b"\x53\xef"
        image = self.root / "userdata.img"
        image.write_bytes(data)
        output = self.root / "extracted"
        source = xml_doc([{"name": "Example", "decryptedSecret": SEED}])
        def fake_run(cmd, **kwargs):
            command = cmd[2]
            if command.split(" ")[1].endswith("authenticator.xml"):
                Path(command.split(" ")[-1]).write_text(source)
            return type("Result", (), {"returncode": 0})()
        with patch("android_mtk.device._find_debugfs", return_value="/usr/bin/debugfs"):
            with patch("android_mtk.device.subprocess.run", side_effect=fake_run):
                files = extract_authy_xml(image, output)
        self.assertEqual(len(files), 1)
        self.assertEqual(load_authy_xml(files[0])[1], [])


if __name__ == "__main__":
    unittest.main()
