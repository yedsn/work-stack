#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Utilities to package Work Stack into a Windows-friendly executable.

Usage:
    python build_exe.py

Prerequisites:
    * Python 3.10+
    * Requirements installed via ``pip install -r requirements.txt``
    * PyInstaller available in PATH (``pip install pyinstaller``)

The script validates that core assets exist, ensures a sanitized
``config.template.json`` is bundled instead of the local ``config.json``,
embeds basic version information, and invokes PyInstaller with GUI flags so
Windows builds omit the console window.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from utils.path_utils import get_user_config_path

PROJECT_ROOT = Path(__file__).resolve().parent
MAIN_SCRIPT = PROJECT_ROOT / "main.py"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
SPEC_FILE = PROJECT_ROOT / "应用启动器.spec"
APP_NAME = "Work Stack"
EXECUTABLE_NAME = "应用启动器"
ICON_PATH = PROJECT_ROOT / "resources" / "icon.ico"
RESOURCE_DIRS: tuple[tuple[Path, str], ...] = (
    (PROJECT_ROOT / "resources", "resources"),
)
CONFIG_TEMPLATE_PATH = PROJECT_ROOT / "config.template.json"
VERSION_FILE_PATH = BUILD_DIR / "version_info.txt"
DEFAULT_VERSION = "0.1.0"
VERSION_ENV_VARS = ("WORKSTACK_VERSION", "VERSION", "BUILD_VERSION")
SAFE_CONFIG_TEMPLATE = {
    "categories": ["娱乐", "工作", "文档"],
    "available_tags": ["默认"],
    "programs": [
        {
            "name": "示例项目",
            "description": "更新此模板以匹配您的真实启动列表。",
            "category": "工作",
            "launch_items": [
                {
                    "app": "python",
                    "params": ["example.py"],
                    "cwd": "%USERPROFILE%"
                }
            ],
            "tags": ["默认"]
        }
    ],
    "sync_settings": {
        "provider": "gist",
        "enabled": False,
        "local_only_keys": [
            "tag_filter_state",
            "window_size",
            "device_window_sizes",
            "sync_settings"
        ]
    }
}


def ensure_pyinstaller_available() -> None:
    """Abort early with actionable feedback when PyInstaller is missing."""
    if shutil.which("pyinstaller"):
        return
    raise RuntimeError(
        "PyInstaller 未安装。请运行 `pip install pyinstaller` 后再试。"
    )


def ensure_main_script_exists() -> None:
    if not MAIN_SCRIPT.exists():
        raise FileNotFoundError(f"未找到主脚本: {MAIN_SCRIPT}")


def ensure_icon_exists() -> None:
    if not ICON_PATH.exists():
        raise FileNotFoundError(
            f"缺少应用图标: {ICON_PATH}。请确保资源已生成或更新 ICON_PATH 设置。"
        )


def ensure_resources_exist() -> None:
    missing = [path for path, _ in RESOURCE_DIRS if not path.exists()]
    if missing:
        missing_list = "\n".join(f" - {path}" for path in missing)
        raise FileNotFoundError(f"缺少资源目录:\n{missing_list}")


def ensure_config_template() -> None:
    """Guarantee that a sanitized config template is available for bundling."""
    if CONFIG_TEMPLATE_PATH.exists():
        return
    CONFIG_TEMPLATE_PATH.write_text(
        json.dumps(SAFE_CONFIG_TEMPLATE, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(
        f"已生成 {CONFIG_TEMPLATE_PATH.name}，请在分发前根据需要更新内容。"
    )


def prepare_dirs() -> None:
    for path in (DIST_DIR, BUILD_DIR):
        if path.exists():
            shutil.rmtree(path)
    if SPEC_FILE.exists():
        SPEC_FILE.unlink()
    BUILD_DIR.mkdir(parents=True, exist_ok=True)


def cleanup_spec_file() -> None:
    """Remove the PyInstaller spec artifact to keep the repo clean."""
    if SPEC_FILE.exists():
        SPEC_FILE.unlink()


def get_version_string() -> str:
    for env_key in VERSION_ENV_VARS:
        value = os.getenv(env_key)
        if value:
            return value.strip()
    version_file = PROJECT_ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return DEFAULT_VERSION


def parse_version_tuple(version: str) -> tuple[int, int, int, int]:
    numeric = []
    for token in version.replace("-", ".").split('.'):
        cleaned = ''.join(ch for ch in token if ch.isdigit())
        if not cleaned:
            continue
        numeric.append(int(cleaned))
    while len(numeric) < 4:
        numeric.append(0)
    return tuple(numeric[:4])


def write_version_file(version: str) -> Path:
    major, minor, patch, build = parse_version_tuple(version)
    VERSION_FILE_PATH.write_text(
        f"VSVersionInfo(\n"
        f"  ffi=FixedFileInfo(\n"
        f"    filevers=({major}, {minor}, {patch}, {build}),\n"
        f"    prodvers=({major}, {minor}, {patch}, {build}),\n"
        f"    mask=0x3f,\n"
        f"    flags=0x0,\n"
        f"    OS=0x40004,\n"
        f"    fileType=0x1,\n"
        f"    subtype=0x0,\n"
        f"    date=(0, 0)\n"
        f"  ),\n"
        f"  kids=[\n"
        f"    StringFileInfo([\n"
        f"      StringTable('040904B0', [\n"
        f"        StringStruct('CompanyName', '{APP_NAME}'),\n"
        f"        StringStruct('FileDescription', '{EXECUTABLE_NAME}'),\n"
        f"        StringStruct('FileVersion', '{version}'),\n"
        f"        StringStruct('InternalName', '{EXECUTABLE_NAME}'),\n"
        f"        StringStruct('OriginalFilename', '{EXECUTABLE_NAME}.exe'),\n"
        f"        StringStruct('ProductName', '{APP_NAME}'),\n"
        f"        StringStruct('ProductVersion', '{version}')\n"
        f"      ])\n"
        f"    ]),\n"
        f"    VarFileInfo([VarStruct('Translation', [0x0409, 0x04B0])])\n"
        f"  ]\n"
        f")\n",
        encoding="utf-8"
    )
    return VERSION_FILE_PATH


def build_add_data_args(paths: Iterable[tuple[Path, str]]) -> list[str]:
    sep = ';' if os.name == 'nt' else ':'
    args: list[str] = []
    for source, target in paths:
        args.append(f"--add-data={source}{sep}{target}")
    return args


def build_exe() -> bool:
    print("开始打包应用……")
    try:
        ensure_pyinstaller_available()
        ensure_main_script_exists()
        ensure_icon_exists()
        ensure_resources_exist()
        ensure_config_template()
        prepare_dirs()
    except Exception as exc:  # pylint: disable=broad-except
        print(f"[ERROR] 无法开始打包: {exc}")
        return False

    version = get_version_string()
    version_file = write_version_file(version)

    add_data_pairs = list(RESOURCE_DIRS)
    add_data_pairs.append((CONFIG_TEMPLATE_PATH, "config.template.json"))
    add_data_args = build_add_data_args(add_data_pairs)

    cmd = [
        "pyinstaller",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--name={EXECUTABLE_NAME}",
        f"--icon={ICON_PATH}",
        f"--version-file={version_file}",
        "--hidden-import=PyQt5.sip",
    ]
    cmd.extend(add_data_args)
    cmd.append(str(MAIN_SCRIPT))

    print("执行打包命令:\n  " + " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"PyInstaller 执行失败: {exc}")
        cleanup_spec_file()
        return False
    cleanup_spec_file()

    output_path = DIST_DIR / EXECUTABLE_NAME / f"{EXECUTABLE_NAME}.exe"
    if not output_path.exists():
        print("[WARN] PyInstaller 完成但未找到预期的 EXE，请检查输出日志。")
        return False

    print(f"[OK] 打包完成: {output_path}")
    print(
        "提示: 将 `config.template.json` 复制为 "
        f"`{get_user_config_path()}` 后再运行，以免包含个人路径或凭据。"
    )
    return True


if __name__ == "__main__":
    sys.exit(0 if build_exe() else 1)
