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
