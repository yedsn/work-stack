#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Windows平台的全局热键管理器
使用keyboard库注册全局快捷键
"""

import sys
import threading
import time
import traceback
import logging
import keyboard
from tkinter import messagebox
from utils.logger import get_logger
# keyboard 库已经内置了按键映射，不需要额外定义

class HotkeyManagerWin:
    """Windows平台的全局热键管理器"""
    
    def __init__(self, window, settings):
        """初始化热键管理器"""
        self.logger = get_logger()
        self.logger.debug("初始化Windows热键管理器")
        
        self.window = window  # 主窗口引用
        self.settings = settings  # 设置引用
        self.hotkey_registered = False  # 记录热键是否成功注册
        self.hotkey_retry_count = 0  # 热键重试次数
        self.hotkey_pressed = False  # 热键是否被按下
        
        # 创建一个定时器，在主线程中定期检查热键状态
        from PyQt5.QtCore import QTimer
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_hotkey_pressed)
        self.check_timer.start(100)  # 每 100 毫秒检查一次
        
    def register_hotkey(self):
        """注册全局快捷键"""
        try:
            # 先清除已有的快捷键绑定
            keyboard.unhook_all()
            self.logger.info("已清除之前的热键绑定")
            
            def hotkey_callback():
                try:
                    # 使用 PyQt5 的 QApplication.postEvent 在主线程中处理
                    # 这里我们简单地设置一个标志，在主线程中定期检查这个标志
                    self.hotkey_pressed = True
                    self.logger.debug('热键已按下')
                except Exception as e:
                    self.logger.error(f"热键回调函数出错: {str(e)}")
                    self.logger.error(f"错误追踪:\n{traceback.format_exc()}")

            # 注册新的快捷键
            keyboard.add_hotkey(
                self.settings.toggle_hotkey,
                hotkey_callback,
                suppress=True,
                trigger_on_release=True
            )
            self.hotkey_registered = True
            self.hotkey_retry_count = 0
            self.logger.info(f"全局热键注册成功: {self.settings.toggle_hotkey}")
            
        except Exception as e:
            error_msg = f"注册热键失败: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(f"错误追踪:\n{traceback.format_exc()}")
            self.retry_register_hotkey()
    
    def retry_register_hotkey(self):
        """重试注册快捷键"""
        MAX_RETRY_COUNT = 5  # 最大重试次数
        try:
            if self.hotkey_retry_count < MAX_RETRY_COUNT:
                self.hotkey_retry_count += 1
                retry_delay = min(1000 * (2 ** self.hotkey_retry_count), 30000)  # 指数退避，最大30秒
                self.logger.info(f"尝试重新注册热键 (第 {self.hotkey_retry_count} 次尝试) 将在 {retry_delay}ms 后进行")
                
                # 使用 QTimer.singleShot 在一定时间后重试
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(retry_delay, self.register_hotkey)
            else:
                self.logger.error("已达到热键注册最大重试次数")
                self.hotkey_retry_count = 0  # 重置重试计数
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(None, "错误", "快捷键注册失败，请尝试重启应用")
        except Exception as e:
            self.logger.error(f"重试注册热键时出错: {str(e)}")
            self.logger.error(f"错误追踪:\n{traceback.format_exc()}")
    
    def _check_hotkey_pressed(self):
        """在主线程中检查热键是否被按下"""
        if self.hotkey_pressed:
            self._handle_hotkey_action()
            self.hotkey_pressed = False
    
    def _handle_hotkey_action(self):
        """处理快捷键动作"""
        try:
            # 使用 PyQt5 的方式检查窗口状态
            is_visible = self.window.isVisible()
            self.logger.debug(f"窗口可见状态: {is_visible}")
            
            if not is_visible:
                self.logger.info("热键按下: 显示窗口")
                self.settings.show_window()
            else:
                self.logger.info("热键按下: 最小化窗口")
                self.settings.minimize_to_tray()
        except Exception as e:
            self.logger.error(f"处理热键动作时出错: {str(e)}")
    
    # 这些方法现在由settings对象提供，不再需要在这里实现
    
    def unregister_hotkey(self):
        """注销全局快捷键"""
        try:
            keyboard.unhook_all()
            self.hotkey_registered = False
            self.logger.info("全局热键已注销")
        except Exception as e:
            self.logger.error(f"注销热键时出错: {str(e)}")
    
    def __del__(self):
        """析构函数，确保清理所有热键"""
        try:
            self.unregister_hotkey()
            # 停止定时器
            if hasattr(self, 'check_timer'):
                self.check_timer.stop()
        except Exception as e:
            # 在析构函数中不应该引发异常
            pass