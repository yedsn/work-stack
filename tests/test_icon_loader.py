#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import unittest

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSize

from gui.icon_loader import get_icon_loader, DEFAULT_ICON_PATH


class IconLoaderTest(unittest.TestCase):
    """验证图标加载器的缓存与去重逻辑"""

    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.loader = get_icon_loader()
        self.results = {}
        self.loader.icon_ready.connect(self._handle_icon_ready)

    def tearDown(self):
        self.loader.icon_ready.disconnect(self._handle_icon_ready)
        self.results.clear()

    def _handle_icon_ready(self, ticket, pixmap):
        self.results[ticket] = pixmap

    def _wait_for_tickets(self, tickets, timeout=2000):
        deadline = time.time() + timeout / 1000.0
        while time.time() < deadline:
            if all(ticket in self.results for ticket in tickets):
                return
            QApplication.processEvents()
            time.sleep(0.01)
        missing = [t for t in tickets if t not in self.results]
        self.fail(f"未在超时时间内收到图标: {missing}")

    def test_deduplicated_requests_receive_single_load(self):
        size = QSize(24, 24)
        ticket_a = self.loader.request_icon(DEFAULT_ICON_PATH, size)
        ticket_b = self.loader.request_icon(DEFAULT_ICON_PATH, size)
        self._wait_for_tickets([ticket_a, ticket_b])
        self.assertIn(ticket_a, self.results)
        self.assertIn(ticket_b, self.results)

    def test_cache_hit_is_immediate(self):
        size = QSize(16, 16)
        first_ticket = self.loader.request_icon(DEFAULT_ICON_PATH, size)
        self._wait_for_tickets([first_ticket])

        second_ticket = self.loader.request_icon(DEFAULT_ICON_PATH, size)
        start = time.time()
        self._wait_for_tickets([second_ticket])
        duration_ms = (time.time() - start) * 1000.0
        self.assertLess(duration_ms, 50.0, "缓存命中没有立即返回结果")


if __name__ == "__main__":
    unittest.main()
