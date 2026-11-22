#!/usr/bin/env bash
# Explicit, non-destructive setup for MTKClient on macOS. No device commands.
set -euo pipefail
umask 077
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This setup script is for macOS; see docs/ANDROID_MTK.md for Linux." >&2
  exit 1
fi
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew required: https://brew.sh" >&2
  exit 1
fi
if ! command -v git >/dev/null 2>&1; then
  echo "Git required" >&2
  exit 1
fi
printf '%s\n' 'This will install Homebrew dependencies, clone upstream MTKClient, and install its Python requirements.'
printf '%s\n' 'It will not unlock, root, flash, erase, or access any device.'
read -r -p 'Proceed? [y/N] ' ANSWER
[[ "$ANSWER" == "y" || "$ANSWER" == "Y" ]] || exit 1
brew install python@3.11 git libusb cmake e2fsprogs
PYTHON="$(brew --prefix python@3.11)/bin/python3.11"
mkdir -p "$ROOT/.tools"
if [[ ! -e "$ROOT/.tools/mtkclient" ]]; then
  git clone --recursive https://github.com/bkerler/mtkclient.git "$ROOT/.tools/mtkclient"
elif [[ ! -f "$ROOT/.tools/mtkclient/mtk.py" ]]; then
  echo "Existing .tools/mtkclient is not an MTKClient checkout; refusing to replace." >&2
  exit 1
fi
if [[ ! -d "$ROOT/.tools/mtkclient/.venv" ]]; then
  "$PYTHON" -m venv "$ROOT/.tools/mtkclient/.venv"
fi
MTKPY="$ROOT/.tools/mtkclient/.venv/bin/python"
"$MTKPY" -m pip install --pre --no-binary capstone capstone
"$MTKPY" -m pip install -r "$ROOT/.tools/mtkclient/requirements.txt"
if [[ ! -d "$ROOT/.venv" ]]; then
  "$PYTHON" -m venv "$ROOT/.venv"
fi
"$ROOT/.venv/bin/python" -m pip install -r "$ROOT/requirements.txt"
printf '\nReady. Run:\n  %q -m android_mtk doctor\n' "$ROOT/.venv/bin/python"
printf 'To dump, add --mtk-python %q to the dump/recover command.\n' "$MTKPY"
printf '\nSome MTKClient builds may require macFUSE; see the upstream installer docs.\n'
