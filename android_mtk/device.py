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
