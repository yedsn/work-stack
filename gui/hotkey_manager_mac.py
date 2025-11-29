#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
macOS 平台的全局热键管理器。
使用 keyboard 库（内部基于 Quartz）监听全局快捷键，并通过 Qt 计时器在主线程中执行回调。
"""

import traceback
from typing import Callable, Optional

import keyboard
from PyQt5.QtCore import QTimer

from gui.hotkey_manager_base import BaseHotkeyManager
from utils.config_manager import DEFAULT_TOGGLE_HOTKEY


class HotkeyManagerMac(BaseHotkeyManager):
    """macOS 平台的全局热键管理器。"""

    def __init__(self, window, settings):
        super().__init__(window, settings)
        self.logger.debug("初始化 macOS 热键管理器")

        self.hotkey_registered = False
        self.hotkey_pressed = False

        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_hotkey_pressed)
        self.check_timer.start(200)

    def register_hotkey(self, hotkey_str: Optional[str] = None, callback: Callable = None) -> bool:
        """注册全局热键"""
        try:
            if hotkey_str is None:
                hotkey_str = getattr(self.settings, "toggle_hotkey", DEFAULT_TOGGLE_HOTKEY)
            if callback is None:
                callback = self.toggle_window

            if hasattr(self.settings, "toggle_hotkey"):
                self.settings.toggle_hotkey = hotkey_str
            else:
                setattr(self.settings, "toggle_hotkey", hotkey_str)

            keyboard.unhook_all()
            self.registered_hotkeys.clear()

            def hotkey_callback():
                try:
                    self.hotkey_pressed = True
                    self.logger.debug("macOS 热键已按下")
                except Exception as exc:
                    self.logger.error(f"macOS 热键回调出错: {exc}")
                    self.logger.error(traceback.format_exc())

            keyboard.add_hotkey(
                hotkey_str,
                hotkey_callback,
                suppress=True,
                trigger_on_release=True
            )
            self.hotkey_registered = True
            self.registered_hotkeys[hotkey_str] = callback
            self.is_enabled = True
            self.logger.info(f"macOS 全局热键注册成功: {hotkey_str}")
            return True

        except Exception as exc:
            self.logger.error(f"macOS 全局热键注册失败: {exc}")
            self.logger.error(traceback.format_exc())
            return False

    def unregister_hotkey(self, hotkey_str: Optional[str] = None) -> bool:
        """注销全局热键"""
        try:
            if hotkey_str:
                if hotkey_str in self.registered_hotkeys:
                    del self.registered_hotkeys[hotkey_str]
                    keyboard.unhook_all()
                    self.hotkey_registered = False
                    if self.registered_hotkeys:
                        for remaining_hotkey, callback in self.registered_hotkeys.items():
                            self.register_hotkey(remaining_hotkey, callback)
                else:
                    self.logger.warning(f"macOS 热键 {hotkey_str} 未注册，无法注销")
            else:
                keyboard.unhook_all()
                self.hotkey_registered = False
                self.registered_hotkeys.clear()

            if not self.registered_hotkeys:
                self.is_enabled = False
                self.logger.info("macOS 全局热键已全部注销")
            return True
        except Exception as exc:
            self.logger.error(f"注销 macOS 全局热键失败: {exc}")
            return False

    def _check_hotkey_pressed(self):
        """在主线程中检查热键状态"""
        if self.hotkey_pressed:
            self._handle_hotkey_action()
            self.hotkey_pressed = False

    def _handle_hotkey_action(self):
        """处理热键触发动作"""
        try:
            is_visible = self.window.isVisible() if self.window else False
            self.logger.debug(f"macOS 窗口可见状态: {is_visible}")

            if not is_visible:
                self.logger.info("macOS 热键触发: 显示窗口")
                self.settings.show_window()
            else:
                self.logger.info("macOS 热键触发: 隐藏窗口")
                self.settings.minimize_to_tray()
        except Exception as exc:
            self.logger.error(f"处理 macOS 热键动作失败: {exc}")

    def cleanup(self):
        """清理资源"""
        try:
            self.unregister_hotkey()
            if hasattr(self, "check_timer") and self.check_timer:
                self.check_timer.stop()
                self.check_timer.deleteLater()
                self.check_timer = None
            self.logger.info("macOS 热键管理器已清理")
        except Exception as exc:
            self.logger.error(f"清理 macOS 热键管理器失败: {exc}")

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass
