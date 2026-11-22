"""Read-only MTKClient acquisition and debugfs extraction."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from .model import MigrationError
from .parsers import AUTHY_FILES

# These are fixed, known Android userdata paths. Nothing user-controlled is
# interpolated as an internal filesystem path to debugfs.
ANDROID_LOCATIONS = (
    "/data/com.authy.authy/shared_prefs",
    "/user/0/com.authy.authy/shared_prefs",
    "/data/data/com.authy.authy/shared_prefs",
    "/data/user/0/com.authy.authy/shared_prefs",
)


def _check_output(path: Path) -> None:
    if path.exists() or path.is_symlink():
        raise MigrationError(f"Refusing to overwrite or follow existing destination: {path}")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise MigrationError(f"Destination parent is not a safe directory: {path.parent}")


def dump_userdata(mtk_dir: Path, image: Path, python_path: str | None = None) -> Path:
    """Invoke only `mtk.py r userdata <file>`; never write/erase/format partitions."""
    script = mtk_dir.resolve() / "mtk.py"
    if not script.is_file():
        raise MigrationError("MTKClient mtk.py not found. Run scripts/setup_macos.sh or pass --mtk-dir")
    image = image.absolute()
    _check_output(image)
    if python_path:
        if Path(python_path).is_file():
            interpreter = str(Path(python_path).absolute())
        else:
            interpreter = shutil.which(python_path)
            if not interpreter:
                raise MigrationError("MTKClient Python interpreter not found")
    else:
        interpreter = sys.executable
    try:
        proc = subprocess.run([interpreter, str(script), "r", "userdata", str(image)],
                              cwd=str(mtk_dir.resolve()), check=False)
    except OSError as exc:
        raise MigrationError("Unable to launch MTKClient; check installation and USB access") from exc
    if proc.returncode or not image.is_file() or image.stat().st_size < 2048:
        raise MigrationError("MTKClient partition read failed or produced no image; any partial image must be reviewed and securely handled")
    return image


def _find_debugfs(explicit: str | None) -> str:
    if explicit:
        if Path(explicit).is_file():
            return explicit
        found = shutil.which(explicit)
        if found:
            return found
        raise MigrationError("Specified debugfs executable not found")
    path = shutil.which("debugfs")
    if path:
        return path
    for prefix in ("/opt/homebrew", "/usr/local"):
        p = Path(prefix) / "opt/e2fsprogs/sbin/debugfs"
        if p.is_file():
            return str(p)
    if shutil.which("brew"):
        proc = subprocess.run(["brew", "--prefix", "e2fsprogs"], capture_output=True, text=True)
        if proc.returncode == 0:
            p = Path(proc.stdout.strip()) / "sbin/debugfs"
            if p.is_file():
                return str(p)
    raise MigrationError("debugfs unavailable; install e2fsprogs (macOS: brew install e2fsprogs)")


def _require_ext4(image: Path) -> None:
    if not image.is_file() or image.is_symlink():
        raise MigrationError("Userdata image is missing or is not a regular file")
    with image.open("rb") as stream:
        stream.seek(1024 + 0x38)
        magic = stream.read(2)
    if magic != b"\x53\xef":
        raise MigrationError("Userdata image is not recognized as an ext2/3/4 filesystem. Encrypted, sparse, F2FS, or unsupported filesystems cannot be processed by debugfs")


def extract_authy_xml(image: Path, output: Path, debugfs: str | None = None) -> list[Path]:
    """Dump ONLY the two Authy preferences files, never whole app data."""
    _require_ext4(image)
    binary = _find_debugfs(debugfs)
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise MigrationError("Unsafe extraction output directory")
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt": os.chmod(output, 0o700)
    files: list[Path] = []
    # Temporary destination avoids quoting paths with spaces in debugfs -R.
    with tempfile.TemporaryDirectory(prefix="authy-debugfs-") as temp:
        for filename in AUTHY_FILES:
            final = output / filename
            _check_output(final)
            for internal in ANDROID_LOCATIONS:
                scratch = Path(temp) / filename
                if scratch.exists(): scratch.unlink()
                # temp path has no whitespace for normal macOS/Linux TMPDIR.
                if any(x.isspace() for x in str(scratch)):
                    raise MigrationError("Temporary path contains whitespace; configure TMPDIR without spaces")
                command = f"dump {internal}/{filename} {scratch}"
                run = subprocess.run([binary, "-R", command, str(image)],
                                     capture_output=True, text=True, check=False)
                if run.returncode == 0 and scratch.is_file() and scratch.stat().st_size:
                    # Inspect XML structure before storing (encrypted fscrypt data fails).
                    from .parsers import load_authy_xml
                    try:
                        # A valid but fully encrypted-token XML parses as zero tokens + warnings;
                        # this is fine, actual password can be provided at export time.
                        load_authy_xml(scratch)
                    except MigrationError as exc:
                        if "Encrypted entries found" not in str(exc):
                            raise MigrationError(f"Recovered Authy XML cannot be parsed: {exc}") from exc
                    fd = os.open(final, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with os.fdopen(fd, "wb") as dest:
                        dest.write(scratch.read_bytes())
                    files.append(final)
                    break
    if not files:
        raise MigrationError("Authy XML not found in readable ext4 userdata; it may be encrypted, absent, or located on an unsupported filesystem")
    return files
