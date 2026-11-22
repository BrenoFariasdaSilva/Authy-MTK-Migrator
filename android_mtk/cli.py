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
