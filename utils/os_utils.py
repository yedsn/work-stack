#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
from typing import Dict, Any

def get_os_type() -> str:
    """返回当前操作系统类型"""
    system = platform.system().lower()
    if system == "darwin":
        return "mac"
    elif system == "windows":
        return "windows"
    else:
        return "linux"

def expand_path(path: str) -> str:
    """展开路径中的用户目录 (如 ~/projects)"""
    return os.path.expanduser(path) 