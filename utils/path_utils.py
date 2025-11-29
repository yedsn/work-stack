#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helpers for resolving file system paths when running from source or a PyInstaller bundle,
including the per-user storage conventions used for configs and credentials.
"""

from __future__ import annotations

import os
import sys
import shutil
from datetime import datetime
from functools import lru_cache
from pathlib import Path

APP_NAME = "Work Stack"
LINUX_APP_DIR = "work-stack"
USER_DATA_ENV = "WORKSTACK_USER_DATA_DIR"
LEGACY_CONFIG_ENV = "WORKSTACK_LEGACY_CONFIG_PATH"
LEGACY_HISTORY_ENV = "WORKSTACK_LEGACY_HISTORY_DIR"
LEGACY_CREDENTIALS_ENV = "WORKSTACK_LEGACY_CREDENTIALS_PATH"


@lru_cache(maxsize=1)
def get_project_root() -> Path:
    """
    Return the absolute project root regardless of whether the app runs from source or PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> str:
    """
    Build an absolute path to a resource bundled with the application.
    """
    return str(get_project_root().joinpath(*parts))


def _expand_path(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve()


def _default_user_base_dir() -> Path:
    if override := _expand_path(os.getenv(USER_DATA_ENV)):
        return override
    home = Path.home()
    if sys.platform.startswith("win"):
        roaming = os.getenv("APPDATA")
        base = Path(roaming) if roaming else home / "AppData" / "Roaming"
        return base / APP_NAME
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / APP_NAME
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    base = Path(xdg_config).expanduser() if xdg_config else home / ".config"
    return base / LINUX_APP_DIR


@lru_cache(maxsize=1)
def get_user_data_dir() -> Path:
    """Return (and create) the per-user data directory for configs and credentials."""
    path = _default_user_base_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_user_config_path() -> Path:
    return get_user_data_dir() / "config.json"


def get_user_credentials_path() -> Path:
    return get_user_data_dir() / "credentials.enc"


def get_user_history_dir() -> Path:
    path = get_user_data_dir() / "config_history"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_legacy_config_path() -> Path:
    if override := _expand_path(os.getenv(LEGACY_CONFIG_ENV)):
        return override
    return get_project_root() / "config.json"


def get_legacy_history_dir() -> Path:
    if override := _expand_path(os.getenv(LEGACY_HISTORY_ENV)):
        return override
    return get_project_root() / "config_history"


def get_legacy_credentials_path() -> Path:
    if override := _expand_path(os.getenv(LEGACY_CREDENTIALS_ENV)):
        return override
    return get_project_root() / "credentials.enc"


def _timestamp_suffix() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def migrate_legacy_file(legacy_path: Path, target_path: Path) -> Path | None:
    """Copy a legacy file into the user directory and archive the original once."""
    if not legacy_path.exists() or target_path.exists():
        return None
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(legacy_path, target_path)
    backup = legacy_path.with_name(f"{legacy_path.name}.migrated-{_timestamp_suffix()}.bak")
    shutil.move(str(legacy_path), str(backup))
    return backup


def migrate_legacy_directory(legacy_dir: Path, target_dir: Path) -> Path | None:
    """Copy a legacy directory into the user directory and archive the original once."""
    if not legacy_dir.exists() or target_dir.exists():
        return None
    shutil.copytree(legacy_dir, target_dir)
    backup = legacy_dir.with_name(f"{legacy_dir.name}.migrated-{_timestamp_suffix()}")
    shutil.move(str(legacy_dir), str(backup))
    return backup
