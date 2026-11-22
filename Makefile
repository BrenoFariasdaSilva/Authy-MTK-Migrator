# Authy-MTK-Migrator: portable GNU Make development commands.
# Requires GNU Make and Python 3.11+; hardware recovery has additional OS/device requirements.
# Commands use the virtual environment's Python directly (no activation necessary).

.DEFAULT_GOAL := all

VENV ?= .venv
ARGS ?=

# Windows normally provides the Python Launcher (py -3). Override with PYTHON=python
# when using an installation without the launcher. Forward slashes work in Windows paths.
ifeq ($(OS),Windows_NT)
PYTHON ?= py -3
VENV_PYTHON := $(VENV)/Scripts/python.exe
else
PYTHON ?= python3
VENV_PYTHON := $(VENV)/bin/python
endif

.PHONY: all help setup install dependencies doctor test check check-build lint \
        fix-style format-check freeze run convert recover dump extract verify \
        backup restore-backup macos-setup clean

# No network access or package installation just to display help.
help:
	@echo "Authy-MTK-Migrator commands (requires GNU Make and Python 3.11+):"
	@echo "  make setup / make install / make dependencies   Create .venv and install requirements"
	@echo "  make doctor                                     Check the environment"
	@echo "  make test / make check                          Run unit tests / syntax plus unit tests"
	@echo "  make check-build                                Check Python syntax"
	@echo "  make lint / make format-check                   Optional Ruff / Black checks"
	@echo "  make fix-style                                  Explicitly apply Ruff and Black formatting"
	@echo "  make freeze                                     Display installed package versions"
	@echo "  make run ARGS=...                               Pass arguments to python -m android_mtk"
	@echo "  make convert ARGS=...                           Convert existing Authy/OTP files"
	@echo "  make recover ARGS=...                           Run supported device recovery"
	@echo "  make dump / extract / verify ARGS=...           Run an individual operation"
	@echo "  make backup / restore-backup ARGS=...           Create or restore an encrypted backup"
	@echo "  make macos-setup                                Optional macOS MTKClient setup (interactive)"
	@echo "  make clean                                      Remove local .venv and Python caches"
	@echo "Every runtime/check target installs requirements before executing."
	@echo "Hardware acquisition is NOT universal; Windows supports local file conversion."

all: doctor

# Recreate the environment when its interpreter is absent; do not install globally.
$(VENV_PYTHON):
	@echo "Creating isolated Python environment in $(VENV)..."
	$(PYTHON) -m venv "$(VENV)"

# Intentionally PHONY: run pip on EVERY invocation to install/validate pinned packages.
# pip normally reports 'Requirement already satisfied' if no changes are needed.
dependencies: $(VENV_PYTHON) requirements.txt
	@echo "Installing/checking project dependencies..."
	"$(VENV_PYTHON)" -m pip install -r requirements.txt

setup install: dependencies
	@echo "Environment ready: $(VENV_PYTHON)"

doctor: dependencies
	"$(VENV_PYTHON)" -m android_mtk doctor

test: dependencies
	"$(VENV_PYTHON)" -m unittest discover -s tests -p test_android_mtk.py -v

check-build: dependencies
	"$(VENV_PYTHON)" -m compileall -q android_mtk tests

# Prerequisites share the same dependencies target, so pip runs once per make invocation.
check: check-build test
	@echo "Syntax checks and unit tests completed."

# Developer tools are deliberately optional and are not added to requirements.txt.
lint: dependencies
	"$(VENV_PYTHON)" -m pip install ruff
	"$(VENV_PYTHON)" -m ruff check android_mtk tests

format-check: dependencies
	"$(VENV_PYTHON)" -m pip install black
	"$(VENV_PYTHON)" -m black --check --line-length 120 android_mtk tests

# WARNING: this explicitly modifies source files; never executed by setup/test.
fix-style: dependencies
	"$(VENV_PYTHON)" -m pip install ruff black
	"$(VENV_PYTHON)" -m ruff check --fix android_mtk tests
	"$(VENV_PYTHON)" -m black --line-length 120 android_mtk tests

# Non-destructive alternative to overwriting the project's pinned requirements.txt.
freeze: dependencies
	"$(VENV_PYTHON)" -m pip freeze

# All CLI targets pass ARGS through to the matching subcommand. Sensitive secrets
# are never copied into Makefile variables or stored in an automatic log file.
run: dependencies
	"$(VENV_PYTHON)" -m android_mtk $(ARGS)

convert: dependencies
	"$(VENV_PYTHON)" -m android_mtk convert $(ARGS)

recover: dependencies
	"$(VENV_PYTHON)" -m android_mtk recover $(ARGS)

dump: dependencies
	"$(VENV_PYTHON)" -m android_mtk dump $(ARGS)

extract: dependencies
	"$(VENV_PYTHON)" -m android_mtk extract $(ARGS)

verify: dependencies
	"$(VENV_PYTHON)" -m android_mtk verify $(ARGS)

backup: dependencies
	"$(VENV_PYTHON)" -m android_mtk backup $(ARGS)

restore-backup: dependencies
	"$(VENV_PYTHON)" -m android_mtk restore-backup $(ARGS)

# This target is deliberately macOS-only; it prepares separate MTKClient tooling.
# It runs its own pip setup and must not run automatically for file-only operations.
macos-setup:
	bash scripts/setup_macos.sh

# Python handles deletion portably; avoid rm/find/del/rmdir shell differences.
# Restrict cleanup to the local venv and Python bytecode caches in source/test trees.
clean:
	$(PYTHON) -c "from pathlib import Path; import shutil; v=Path('$(VENV)'); assert len(v.parts)==1 and v.name not in ('.','..'), 'Unsafe VENV path'; shutil.rmtree(v) if v.is_dir() else None; roots=(Path('android_mtk'),Path('tests')); [shutil.rmtree(p) for r in roots if r.is_dir() for p in r.rglob('__pycache__')]; [p.unlink() for r in roots if r.is_dir() for p in r.rglob('*.pyc')]"
