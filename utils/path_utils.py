#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helpers for resolving file system paths when running from source or a PyInstaller bundle.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path


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
