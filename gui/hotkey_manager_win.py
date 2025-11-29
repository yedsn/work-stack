#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Windows 平台的全局热键管理器。
使用 RegisterHotKey + Qt 原生事件过滤器，避免在多桌面/虚拟桌面切换时丢失 keyboard 库的钩子。
"""

import ctypes
from ctypes import wintypes
import itertools
import traceback
from typing import Callable, Optional, Tuple

from PyQt5.QtCore import QAbstractNativeEventFilter, QTimer
from PyQt5.QtWidgets import QApplication

from gui.hotkey_manager_base import BaseHotkeyManager
from utils.config_manager import DEFAULT_TOGGLE_HOTKEY
from utils.logger import get_logger

user32 = ctypes.windll.user32
WM_HOTKEY = 0x0312

MODIFIERS = {
    "alt": 0x0001,
    "ctrl": 0x0002,
    "shift": 0x0004,
    "meta": 0x0008,
    "win": 0x0008,
}

SPECIAL_KEYS = {
    "enter": 0x0D,
    "return": 0x0D,
    "esc": 0x1B,
    "escape": 0x1B,
    "space": 0x20,
    "tab": 0x09,
    "backspace": 0x08,
    "delete": 0x2E,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "insert": 0x2D,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
}


class _WinHotkeyEventFilter(QAbstractNativeEventFilter):
    """集中处理 WM_HOTKEY 消息并回调主线程。"""

    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self._callbacks = {}

    def register_callback(self, hotkey_id: int, callback: Callable):
        self._callbacks[hotkey_id] = callback

    def unregister_callback(self, hotkey_id: int):
        self._callbacks.pop(hotkey_id, None)

    def nativeEventFilter(self, event_type, message):
        if event_type != "windows_generic_MSG":
            return False, 0
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            callback = self._callbacks.get(msg.wParam)
            if callback:
                QTimer.singleShot(0, callback)
            return True, 0
        return False, 0


class HotkeyManagerWin(BaseHotkeyManager):
    """Windows 平台的全局热键管理器。"""

    _event_filter: Optional[_WinHotkeyEventFilter] = None
    _hotkey_ids = itertools.count(1)

    def __init__(self, window, settings):
        super().__init__(window, settings)
        self.logger.debug("初始化 Windows 热键管理器")
        self.hotkey_id: Optional[int] = None
        self._ensure_event_filter()

    @classmethod
    def _ensure_event_filter(cls):
        if cls._event_filter is None:
            app = QApplication.instance()
            if app is None:
                raise RuntimeError("QApplication 尚未初始化，无法注册全局热键")
            cls._event_filter = _WinHotkeyEventFilter(get_logger())
            app.installNativeEventFilter(cls._event_filter)

    def register_hotkey(self, hotkey_str: str = None, callback: Callable = None) -> bool:
        """注册全局快捷键。"""
        try:
            if hotkey_str is None:
                hotkey_str = getattr(self.settings, 'toggle_hotkey', DEFAULT_TOGGLE_HOTKEY)
            hotkey_str = hotkey_str.strip().lower()
            if callback is None:
                callback = self.toggle_window

            modifiers, vk_code = self._parse_hotkey(hotkey_str)
            if vk_code is None:
                self.logger.error(f"无法解析热键: {hotkey_str}")
                return False

            self.unregister_hotkey()

            hotkey_id = next(self._hotkey_ids)
            result = user32.RegisterHotKey(None, hotkey_id, modifiers, vk_code)
            if not result:
                err = ctypes.GetLastError()
                self.logger.error(f"注册全局热键失败 (code={err}): {hotkey_str}")
                return False

            self.hotkey_id = hotkey_id
            self.registered_hotkeys = {hotkey_str: callback}
            if hasattr(self.settings, 'toggle_hotkey'):
                self.settings.toggle_hotkey = hotkey_str
            else:
                setattr(self.settings, 'toggle_hotkey', hotkey_str)

            if self._event_filter:
                self._event_filter.register_callback(hotkey_id, callback)

            self.is_enabled = True
            self.logger.info(f"全局热键注册成功: {hotkey_str}")
            return True

        except Exception as exc:
            self.logger.error(f"注册热键失败: {exc}")
            self.logger.error(traceback.format_exc())
            return False

    def _parse_hotkey(self, hotkey_str: str) -> Tuple[int, Optional[int]]:
        parsed = self.parse_hotkey_string(hotkey_str)
        modifiers = 0
        if parsed['ctrl']:
            modifiers |= MODIFIERS['ctrl']
        if parsed['alt']:
            modifiers |= MODIFIERS['alt']
        if parsed['shift']:
            modifiers |= MODIFIERS['shift']
        if parsed['meta']:
            modifiers |= MODIFIERS['win']

        vk_code = self._key_to_vk(parsed.get('key'))
        return modifiers, vk_code

    def _key_to_vk(self, key: Optional[str]) -> Optional[int]:
        if not key:
            return None
        normalized = key.strip().lower()
        if normalized in SPECIAL_KEYS:
            return SPECIAL_KEYS[normalized]
        if normalized.startswith('f') and normalized[1:].isdigit():
            index = int(normalized[1:])
            if 1 <= index <= 24:
                return 0x6F + index  # F1=0x70
        if len(normalized) == 1:
            return ord(normalized.upper())
        self.logger.warning(f"不支持的主键: {key}")
        return None

    def pause_checking(self):
        """兼容旧接口，无操作。"""
        self.logger.debug("暂停热键检测（占位，无实际操作）")

    def resume_checking(self):
        """兼容旧接口，无操作。"""
        self.logger.debug("恢复热键检测（占位，无实际操作）")

    def unregister_hotkey(self, hotkey_str: Optional[str] = None) -> bool:
        """注销全局快捷键。"""
        try:
            if self.hotkey_id is not None:
                if self._event_filter:
                    self._event_filter.unregister_callback(self.hotkey_id)
                user32.UnregisterHotKey(None, self.hotkey_id)
                self.logger.info("已注销全局热键")
                self.hotkey_id = None
            self.registered_hotkeys.clear()
            self.is_enabled = False
            return True
        except Exception as exc:
            self.logger.error(f"注销热键时出错: {exc}")
            return False

    def cleanup(self):
        """清理资源。"""
        try:
            self.unregister_hotkey()
            self.logger.info("已清理 Windows 热键管理器资源")
        except Exception as exc:
            self.logger.error(f"清理热键管理器资源失败: {exc}")

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass
