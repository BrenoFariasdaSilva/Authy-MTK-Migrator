"""Read-only, opt-in CLI for legacy Authy-on-MediaTek migration."""
from __future__ import annotations

import argparse
from getpass import getpass
import os
from pathlib import Path
import shutil
import sys

from . import __version__
from .device import dump_userdata, extract_authy_xml, _find_debugfs
from .exports import EXPORTS, write_exports
from .model import MigrationError
from .parsers import load_tokens
from .otp import calculate_code
from .secure_backup import create_backup, restore_backup


def _formats(value: str) -> set[str]:
    result = set(value.lower().replace(" ", "").split(","))
    if "all" in result:
        return set(EXPORTS)
    if not result or not result <= EXPORTS:
        raise argparse.ArgumentTypeError("Formats: all or comma-separated uris,aegis,proton,qr")
    return result


def _parser() -> argparse.ArgumentParser:
    main = argparse.ArgumentParser(
        prog="python -m android_mtk", description="Local Authy migration from readable legacy MediaTek userdata")
    main.add_argument("--version", action="version", version=__version__)
    subs = main.add_subparsers(dest="command", required=True)
    subs.add_parser("doctor", help="Inspect installed dependencies; no device access")
    dump = subs.add_parser("dump", help="READ ONLY: obtain userdata.img using MTKClient")
    dump.add_argument("--mtk-dir", type=Path, default=Path(__file__).resolve().parents[1] / ".tools/mtkclient")
    dump.add_argument("--mtk-python", default=None, help="Python executable in MTKClient virtual environment")
    dump.add_argument("--image", required=True, type=Path)
    dump.add_argument("--owned-device", action="store_true", help="Confirm this is your device and account")
    extract = subs.add_parser("extract", help="Extract only Authy XML files from ext4 userdata.img")
    extract.add_argument("--image", required=True, type=Path)
    extract.add_argument("--out", required=True, type=Path)
    extract.add_argument("--debugfs", default=None)
    convert = subs.add_parser("convert", help="Convert local Authy XML, URI list, or supported JSON to formats")
    _convert_args(convert)
    recover = subs.add_parser("recover", help="End-to-end dump → extract → convert → exports")
    recover.add_argument("--mtk-dir", type=Path, default=Path(__file__).resolve().parents[1] / ".tools/mtkclient")
    recover.add_argument("--mtk-python", default=None)
    recover.add_argument("--out", required=True, type=Path, help="New or existing protected recovery directory")
    recover.add_argument("--reuse-image", action="store_true", help="Use existing out/userdata.img without any device access")
    recover.add_argument("--debugfs", default=None)
    recover.add_argument("--owned-device", action="store_true")
    recover.add_argument("--acknowledge-secrets", action="store_true")
    recover.add_argument("--formats", type=_formats, default=set(EXPORTS))
    recover.add_argument("--allow-partial", action="store_true")
    recover.add_argument("--force", action="store_true", help="Overwrite existing regular export files; never userdata.img or XML")
    backup = subs.add_parser("backup", help="Encrypt an exports folder into a password-protected offline backup")
    backup.add_argument("--input", required=True, type=Path, help="Folder of generated exports")
    backup.add_argument("--output", required=True, type=Path, help="Output .amtk file")
    backup.add_argument("--force", action="store_true")
    restore = subs.add_parser("restore-backup", help="Decrypt a .amtk archive locally")
    restore.add_argument("--input", required=True, type=Path)
    restore.add_argument("--out", required=True, type=Path)
    restore.add_argument("--force", action="store_true")
    verify = subs.add_parser("verify", help="Opt-in display of one OTP code for comparison with Authy")
    verify.add_argument("--input", required=True, type=Path)
    verify.add_argument("--source", default="auto", choices=("auto", "xml", "uris", "json", "aegis", "proton", "ios-json", "uris-json"))
    verify.add_argument("--index", type=int, required=True, help="1-based index in alphabetically sorted import")
    verify.add_argument("--show-code", action="store_true", help="Explicitly allow display of 2FA code")
    return main


def _convert_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--input", required=True, type=Path, help="Authy XML, directory containing XML, URI text, or JSON")
    p.add_argument("--source", default="auto", choices=("auto", "xml", "uris", "json", "aegis", "proton", "ios-json", "uris-json"))
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--formats", type=_formats, default=set(EXPORTS))
    p.add_argument("--acknowledge-secrets", action="store_true", help="Required to create plaintext sensitive exports")
    p.add_argument("--allow-partial", action="store_true", help="Explicitly export valid tokens despite skipped entries")
    p.add_argument("--force", action="store_true", help="Replace existing regular export files (not symlinks)")


def _require(flag: bool, message: str) -> None:
    if not flag:
        raise MigrationError(message)


def _doctor() -> None:
    print(f"Platform: {sys.platform}; Python: {sys.version.split()[0]}")
    for exe in (("git", "brew") if sys.platform == "darwin" else ("git",)):
        print(f"{exe}: {shutil.which(exe) or 'not found'}")
    try:
        print(f"debugfs: {_find_debugfs(None)}")
    except MigrationError:
        print("debugfs: not found (needed only for extraction)")
    for module in ("cryptography", "qrcode", "PIL"):
        try:
            __import__(module)
            print(f"{module}: available")
        except ImportError:
            print(f"{module}: not found")
    mtk = Path(__file__).resolve().parents[1] / ".tools/mtkclient/mtk.py"
    print(f"MTKClient: {'found' if mtk.exists() else 'not installed'}")


def _load(path: Path, source: str, allow_partial: bool):
    tokens, errors = load_tokens(path, source)
    if any("Encrypted entries found" in error for error in errors):
        password = getpass("Authy BACKUP password (hidden; not the app-lock PIN): ")
        tokens, errors = load_tokens(path, source, password)
    if errors:
        print(f"Skipped/failed entries: {len(errors)}", file=sys.stderr)
        # Only benign, fixed error explanations, never secret values.
        for item in errors[:25]:
            print(f"  {item}", file=sys.stderr)
        if len(errors) > 25:
            print(f"  ... and {len(errors) - 25} more", file=sys.stderr)
        if not allow_partial:
            raise MigrationError("One or more tokens failed. Refusing partial export; use --allow-partial only after reviewing errors")
    if not tokens:
        raise MigrationError("No valid tokens were found")
    print(f"Loaded {len(tokens)} unique token(s). No secrets displayed.")
    return tokens
