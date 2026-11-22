# Authy Android / MediaTek: read-only migration

> **Experimental hardware workflow.** The source method was reported on a Prestigio Wize 3161 3G / MT8321 / Android 7.0 in November 2026. This repository's implementation has **not** been tested on physical MediaTek hardware. It cannot bypass filesystem encryption, secure hardware, or inaccessible BROM/preloader interfaces. Operate only on hardware and accounts you own or administer with explicit permission.

This project is **standalone** and does not modify the separate iOS/mitmproxy repository. It can, however, import the `decrypted_tokens.json` file produced by that project and convert it into the same interoperable export formats.

## What is automated

1. Optional macOS dependency installer (`scripts/setup_macos.sh`), including a dedicated MTKClient virtual environment. It does **not** automatically install a privileged FUSE kernel extension or patch upstream MTKClient code.
2. Invokes **only** the MTKClient **read** command `mtk.py r userdata <image>` (no flash, erase, root, or bootloader unlock operation is requested).
3. Rejects images without an ext2/3/4 superblock signature and uses `debugfs` to export only the two known Authy preferences XML files from a list of fixed filesystem locations.
4. Parses standard, encrypted, and Authy-specific token variants. If encrypted entries are detected, requests the **Authy backup password** using hidden input (not the app-lock PIN).
5. Converts the recovered tokens into **Aegis vault JSON**, **Proton Authenticator JSON**, **otpauth URI text/JSON**, and **one QR code per token**. Supports TOTP 10/30/custom-second periods, digit counts, SHA algorithms, and HOTP from supported external formats.
6. Supports reverse intake from these files and the existing iOS `decrypted_tokens.json` (see supported sources).
7. Supports password-encrypted local `.amtk` backup and local restore, plus opt-in OTP verification.
8. Stops on any unrecognized/invalid token by default. Can explicitly export a partial set after review.

The program **does not** use the cloud to transmit, decrypt, or import secret material and cannot push credentials directly into another authenticator application's private database. The **user imports** the generated files through that app's supported UI.

## Requirements

- Python 3.11+ recommended (the format converter can run on Windows, macOS, or Linux).
- For the USB dump: compatible, user-owned MediaTek hardware exposing a readable preloader/BROM interface and a working [MTKClient](https://github.com/bkerler/mtkclient) installation.
- For raw image extraction: unencrypted readable **ext2/3/4** userdata; `debugfs` from e2fsprogs. F2FS, Android file-based encryption (FBE), full-disk encryption (FDE), dynamic/locked partitions, USB driver limitations, and modern locked hardware are **not** automatically handled.
- For QR generation: the existing Python `qrcode` and `Pillow` dependencies.
- For encrypted entries: the Authy backup password, which may not exist/be available for all accounts.
- Disk space at least as large as the `userdata` partition, plus room for temporary files and recovery output. Never use an untrusted shared/cloud folder.

### macOS setup (Apple Silicon or Intel)

From the root of this repository:

```bash
bash scripts/setup_macos.sh
. .venv/bin/activate
python -m android_mtk doctor
```

The setup script asks before installing Homebrew dependencies (`python@3.11`, `git`, `libusb`, `cmake`, `e2fsprogs`) and checking out MTKClient under ignored `.tools/mtkclient`. It installs a second venv under `.tools/mtkclient/.venv`. The exact upstream dependencies may change; review MTKClient before installation. It does not modify system security policy. If upstream MTKClient requires FUSE or raises a libfuse import error, consult upstream compatibility instructions instead of blindly patching code.

### Linux setup

```bash
sudo apt-get install python3 python3-venv python3-pip git e2fsprogs libusb-1.0-0
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
mkdir -p .tools
git clone --recursive https://github.com/bkerler/mtkclient.git .tools/mtkclient
python -m android_mtk doctor
```

Install MTKClient's own requirements into its own venv following [MTKClient's installer docs](https://github.com/bkerler/mtkclient/blob/main/README-INSTALL.md), then specify its interpreter with `--mtk-python`. Linux USB permissions/udev rules are device-dependent. Windows supports conversion from an existing XML/JSON/URI file; hardware imaging/extraction require suitable third-party tools/OS-specific paths.

## Start-to-finish workflow (own compatible device only)

1. Confirm the Authy tokens are synchronized on the **old Android device**. Open a code there before shutdown if necessary for Authy to populate its local decrypted state. Do not delete Authy.
2. Power the device off. Connect via the device-specific BROM/preloader button combination **only when prompted by MTKClient**. The commenter's Volume Up + Power method is not universal.
3. Run (from repo root):

```bash
umask 077
. .venv/bin/activate
python -m android_mtk recover \
  --mtk-dir .tools/mtkclient \
  --mtk-python .tools/mtkclient/.venv/bin/python \
  --out ./authy-recovery \
  --owned-device \
  --acknowledge-secrets \
  --formats all
```

This command creates `authy-recovery/userdata.img`, `authy-recovery/extracted/*.xml` and `authy-recovery/exports/*`. **Files are plaintext, private, and security-sensitive.** If the USB operation fails, inspect partial output before retrying. The program never removes your source image without asking you to manage it.

**Existing image/no USB:**

```bash
python -m android_mtk recover --out ./authy-recovery \
  --reuse-image --acknowledge-secrets --formats aegis,proton,uris
```

If extraction already exists, use `convert` below rather than repeating `recover` (which refuses to overwrite existing extracted XML).

**Separate stages (recommended for diagnosing errors):**

```bash
python -m android_mtk dump --mtk-dir .tools/mtkclient \
  --mtk-python .tools/mtkclient/.venv/bin/python \
  --image ./authy-recovery/userdata.img --owned-device

python -m android_mtk extract --image ./authy-recovery/userdata.img \
  --out ./authy-recovery/extracted

python -m android_mtk convert --input ./authy-recovery/extracted \
  --out ./authy-recovery/exports --formats all --acknowledge-secrets
```

The recovery directory must exist before `dump` if using the separate commands (`mkdir -m 700 -p authy-recovery`). The `recover` command creates it for you.

## Import or convert from another authenticator

```bash
# Existing repository's output (no Android device required)
python -m android_mtk convert --input ./decrypted_tokens.json \
  --out ./exports --formats aegis,proton,uris,qr --acknowledge-secrets

# Import a compatible Aegis unencrypted JSON vault
python -m android_mtk convert --input ./aegis-export.json \
  --out ./exports --formats proton,uris --acknowledge-secrets

# Import Proton JSON export
python -m android_mtk convert --input ./proton-export.json \
  --out ./exports --formats aegis,uris --acknowledge-secrets

# Import one otpauth:// URI per line
python -m android_mtk convert --input ./secrets.txt \
  --out ./exports --formats all --acknowledge-secrets

# Import a recovered Authy XML directly
python -m android_mtk convert \
  --input ./com.authy.storage.tokens.authenticator.xml \
  --out ./exports --formats all --acknowledge-secrets
```

For data with unsupported tokens, the default is to **fail the export** and report the problem. Only use `--allow-partial` after checking the count. `--force` allows replacing regular **export** files but never overwrites `userdata.img` or extracted XML.

## Output compatibility

| Generated file | Use | Important details |
| --- | --- | --- |
| `aegis.json` | Aegis → Settings → Import & Export → Import from file → Aegis | Plaintext Aegis vault, preserves TOTP period, digits, SHA1/256/512 and supported HOTP metadata. Also useful for apps with Aegis import, such as 2FAS. |
| `proton_authenticator.json` | Proton Authenticator → import from Proton-format file | Matches the unencrypted Proton JSON structure used by the existing iOS project. Check version compatibility. |
| `otpauth.txt` | Apps supporting plain-text `otpauth://` import (for example, Aegis); copy a URI for per-account import into other apps | Vendor import capabilities differ and may change. |
| `URIs.json` | Compatible with this repository's existing `generate_qr_codes.py` input structure and human-readable export tooling | Generic JSON, not guaranteed app-native import. |
| `qr_codes/otp-0001.png`, etc. + `qr_codes/index.csv` | Use the index to identify each account and scan QR images individually into Google Authenticator, Microsoft Authenticator, Apple Passwords, 2FAS, and other OTP URI scanner apps | Not a Google bulk migration QR. Some apps **cannot accept 10-second/7-digit Authy-specific codes**. Always compare the actual generated codes. |

Although 2FAS, Google, and Microsoft are supported **as destinations through supported URI/QR/Aegis import paths**, this utility does **not** generate proprietary native files for all of them, nor can it insert tokens automatically into their app storage.

## Verify codes before switching

Display a **single** current OTP code on demand (with extreme care around terminal recordings and screen shares):

```bash
python -m android_mtk verify --input ./authy-recovery/extracted \
  --index 1 --show-code
```

Indices are sorted case-insensitively by issuer/name and start at 1. Time on the computer and both phones must be synchronized. For HOTP, compare the counter, since HOTP is event-based. For best assurance, import a token into the destination and compare both apps side-by-side before deleting Authy. **Authy's 7-digit/10-second codes may not be portable to every app.**

## Encrypt a portable offline backup

The exports described above **must** be plaintext for app import; this command makes an additional password-encrypted archive using scrypt and AES-256-GCM. It is not an app-native format:

```bash
python -m android_mtk backup --input ./authy-recovery/exports \
  --output ./authy-recovery/backup.amtk

python -m android_mtk restore-backup --input ./authy-recovery/backup.amtk \
  --out ./restored-authy-exports
```

The password is requested interactively and never supplied as a CLI argument. **Plaintext originals remain on disk.** Manage them separately after validating the encrypted archive. Deleting SSD data does not guarantee secure erasure. Consider an encrypted disk/volume, and never commit, synchronize, or paste secret-containing files anywhere public.

## Problems and troubleshooting

- **MTKClient cannot connect:** chipset/support/drivers/USB cable/access restrictions. Consult upstream MTKClient diagnostics. This utility does not bypass security controls or auto-patch upstream code.
- **`Unable to find libfuse`:** the gist commenter described a local workaround, but this implementation does not alter installed third-party source files. Consult MTKClient upstream and FUSE install notes first.
- **Not ext4:** F2FS, sparse/split images, full-disk encryption, and FBE are not supported by the raw `debugfs` path. No data is automatically decrypted.
- **Authy XML not found:** Authy may be on a different partition/profile, not synchronized, absent, or encrypted. Check that the original app still contains your codes.
- **Wrong backup password:** use Authy's backup password, not the 4-digit app-lock PIN. The utility fails closed if decryption is incomplete.
- **One or more entries invalid:** fix source data or explicitly choose `--allow-partial`; never treat a partial export as a complete migration.
- **QR code import fails:** many apps assume 6 digits and 30 seconds; use Aegis or another destination that supports your token's parameters. Some app-specific/Authy-specific 2FA methods may not be migratable via a generic `otpauth://` URI.
- **Disk full:** userdata images can be many GB. The tool never overwrites an existing dump and never silently deletes partial or sensitive files.

## Reproducible validation

```bash
python -m unittest discover -s tests -p 'test_android_mtk.py' -v
```

The included tests cover synthetic XML, existing iOS JSON, AES-CBC/PBKDF2 Authy encrypted tokens, malformed inputs, Authy-specific token periods, RFC 6238 code generation, Aegis/Proton/URI round-trips, QR creation, permission flags, safe overwrites, encrypted archive backup/restore, and mocked MTKClient/debugfs subprocess boundaries. **No physical MediaTek, actual filesystem image, or real destination-app import has been tested as part of this artifact.**

## Primary implementation references

- [Original November 2026 observation on gboudreau's gist](https://gist.github.com/gboudreau/94bb0c11a6209c82418d01a59d958c93)
- [MTKClient official repository](https://github.com/bkerler/mtkclient)
- [MTKClient installation instructions](https://github.com/bkerler/mtkclient/blob/main/README-INSTALL.md)
- [Aegis Authy importer source code](https://github.com/beemdevelopment/Aegis/blob/master/app/src/main/java/com/beemdevelopment/aegis/importers/AuthyImporter.java)
- [Aegis plaintext vault specification](https://github.com/beemdevelopment/Aegis/blob/master/docs/vault.md)
- [2FAS supported imports](https://2fas.com/support/2fas-auth-mobile-app/which-imports-are-supported-in-the-2fas-app/)
- [Proton Authenticator import support](https://proton.me/support/import-2fa-codes)
