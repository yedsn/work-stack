#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXECUTABLE = sys.executable


def run_python_snippet(snippet: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON_EXECUTABLE, "-c", snippet],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )


class ConfigStorageTests(unittest.TestCase):
    def test_load_config_returns_defaults_for_empty_user_dir(self):
        with tempfile.TemporaryDirectory() as user_dir:
            env = os.environ.copy()
            env["WORKSTACK_USER_DATA_DIR"] = user_dir
            env["WORKSTACK_LEGACY_CONFIG_PATH"] = str(Path(user_dir) / "legacy.json")
            env["PYTHONIOENCODING"] = "utf-8"

            snippet = """
import json
from utils.config_manager import load_config, CONFIG_PATH
config = load_config()
print(json.dumps(config, ensure_ascii=False))
print(CONFIG_PATH)
"""
            result = run_python_snippet(snippet, env)
            lines = [line for line in result.stdout.splitlines() if line.strip()]
            self.assertGreaterEqual(len(lines), 2, msg=result.stdout)
            config = json.loads(lines[0])

            self.assertEqual(["娱乐", "工作", "文档"], config["categories"])
            self.assertEqual([], config["programs"])
            self.assertTrue(Path(lines[1]).parent.samefile(user_dir))

    def test_migrates_legacy_config_once(self):
        with tempfile.TemporaryDirectory() as user_dir, tempfile.TemporaryDirectory() as legacy_dir:
            legacy_path = Path(legacy_dir) / "config.json"
            payload = {
                "categories": ["Legacy"],
                "programs": [{"name": "Old Item"}],
            }
            legacy_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            env = os.environ.copy()
            env["WORKSTACK_USER_DATA_DIR"] = user_dir
            env["WORKSTACK_LEGACY_CONFIG_PATH"] = str(legacy_path)
            env["PYTHONIOENCODING"] = "utf-8"

            snippet = """
from utils.config_manager import load_config
load_config()
"""
            run_python_snippet(snippet, env)

            config_file = Path(user_dir) / "config.json"
            self.assertTrue(config_file.exists())
            on_disk = json.loads(config_file.read_text(encoding="utf-8"))
            self.assertEqual(payload, on_disk)

            backups = list(Path(legacy_dir).glob("config.json.migrated-*.bak"))
            self.assertEqual(1, len(backups))

            # Running again should not create more backups
            run_python_snippet(snippet, env)
            self.assertEqual(backups, list(Path(legacy_dir).glob("config.json.migrated-*.bak")))

    @unittest.skipUnless(sys.platform.startswith("win"), "Windows-specific expectation")
    def test_windows_user_dir_uses_appdata(self):
        with tempfile.TemporaryDirectory() as appdata_dir:
            env = os.environ.copy()
            env.pop("WORKSTACK_USER_DATA_DIR", None)
            env["APPDATA"] = appdata_dir
            env["PYTHONIOENCODING"] = "utf-8"

            snippet = """
from utils.path_utils import get_user_data_dir
print(get_user_data_dir())
"""
            result = run_python_snippet(snippet, env)
            user_dir = Path(result.stdout.strip())
            self.assertEqual(user_dir, Path(appdata_dir) / "Work Stack")


if __name__ == "__main__":
    unittest.main()
