#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import copy

from PyQt5.QtWidgets import QApplication

from gui.main_window import LaunchGUI
from utils.config_manager import load_config, save_config


class DeferredRefreshTest(unittest.TestCase):
    """验证后台刷新延迟策略"""

    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self):
        self._original_config = copy.deepcopy(load_config())
        self.window = LaunchGUI()
        self.window.hide()

    def tearDown(self):
        save_config(self._original_config, immediate=True)
        self.window.close()

    def test_background_refresh_is_applied_on_demand(self):
        new_config = copy.deepcopy(self._original_config)
        new_config["test_case"] = "deferred-refresh"

        applied = self.window.apply_background_config(new_config, "单元测试")
        self.assertTrue(applied, "后台配置写入失败")
        self.assertTrue(self.window._pending_ui_refresh, "未记录待刷新状态")

        refreshed = self.window.apply_pending_refresh_if_needed(reason="unit-test", force=True)
        self.assertTrue(refreshed, "窗口未按需刷新")
        self.assertFalse(self.window._pending_ui_refresh, "刷新后未清除待刷新标记")


if __name__ == "__main__":
    unittest.main()
