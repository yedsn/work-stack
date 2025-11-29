#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
热键管理器基类

定义所有平台热键管理器的统一接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable
from utils.logger import get_logger


class BaseHotkeyManager(ABC):
    """
    热键管理器基类
    
    定义统一的热键注册/注销接口，各平台实现具体功能
    """
    
    def __init__(self, window=None, settings=None):
        """
        初始化热键管理器
        
        Args:
            window: 主窗口对象，用于热键回调
            settings: 设置对象，包含热键配置
        """
        self.window = window
        self.settings = settings
        self.logger = get_logger()
        self.registered_hotkeys = {}
        self.is_enabled = False
    
    @abstractmethod
    def register_hotkey(self, hotkey_str: str, callback: Callable = None) -> bool:
        """
        注册全局热键
        
        Args:
            hotkey_str: 热键字符串，如 'alt+w'
            callback: 热键触发回调函数，默认使用 toggle_window
            
        Returns:
            bool: 注册是否成功
        """
        pass
    
    @abstractmethod
    def unregister_hotkey(self, hotkey_str: Optional[str] = None) -> bool:
        """
        注销全局热键
        
        Args:
            hotkey_str: 要注销的热键字符串，None表示注销所有热键
            
        Returns:
            bool: 注销是否成功
        """
        pass
    
    def toggle_window(self):
        """
        切换窗口显示/隐藏状态
        
        默认的热键回调函数
        """
        if not self.window:
            self.logger.warning("没有设置主窗口，无法切换窗口状态")
            return
            
        try:
            if self.window.isVisible() and self.window.isActiveWindow():
                self.window.hide()
                self.logger.debug("通过热键隐藏窗口")
            else:
                self.window.show()
                self.window.raise_()
                self.window.activateWindow()
                self.logger.debug("通过热键显示窗口")
        except Exception as e:
            self.logger.error(f"切换窗口状态时出错: {e}")
    
    def enable_hotkey(self, enable: bool = True):
        """
        启用/禁用热键功能
        
        Args:
            enable: 是否启用热键
        """
        self.is_enabled = enable
        if not enable:
            self.unregister_hotkey()
            self.logger.info("热键功能已禁用")
        else:
            self.logger.info("热键功能已启用")
    
    def is_hotkey_enabled(self) -> bool:
        """
        检查热键是否已启用
        
        Returns:
            bool: 热键是否已启用
        """
        return self.is_enabled
    
    def get_registered_hotkeys(self) -> dict:
        """
        获取已注册的热键列表
        
        Returns:
            dict: 已注册的热键字典
        """
        return self.registered_hotkeys.copy()
    
    def cleanup(self):
        """
        清理资源
        
        在应用退出时调用，清理所有注册的热键
        """
        try:
            self.unregister_hotkey()
            self.logger.debug("热键管理器清理完成")
        except Exception as e:
            self.logger.error(f"清理热键管理器时出错: {e}")
    
    def parse_hotkey_string(self, hotkey_str: str) -> dict:
        """
        解析热键字符串
        
        Args:
            hotkey_str: 热键字符串，如 'alt+w'
            
        Returns:
            dict: 解析后的热键信息，包含修饰键和主键
        """
        hotkey_str = hotkey_str.lower().strip()
        parts = [part.strip() for part in hotkey_str.split('+')]
        
        result = {
            'ctrl': False,
            'alt': False,
            'shift': False,
            'meta': False,  # Windows键或Cmd键
            'key': None
        }
        
        for part in parts:
            if part in ['ctrl', 'control']:
                result['ctrl'] = True
            elif part in ['alt', 'option']:
                result['alt'] = True  
            elif part == 'shift':
                result['shift'] = True
            elif part in ['meta', 'cmd', 'win', 'windows']:
                result['meta'] = True
            else:
                result['key'] = part
        
        return result
    
    def hotkey_to_string(self, parsed_hotkey: dict) -> str:
        """
        将解析后的热键信息转换为字符串
        
        Args:
            parsed_hotkey: 解析后的热键信息
            
        Returns:
            str: 热键字符串
        """
        parts = []
        
        if parsed_hotkey.get('ctrl'):
            parts.append('Ctrl')
        if parsed_hotkey.get('alt'):
            parts.append('Alt')
        if parsed_hotkey.get('shift'):
            parts.append('Shift')
        if parsed_hotkey.get('meta'):
            parts.append('Meta')
        
        if parsed_hotkey.get('key'):
            parts.append(parsed_hotkey['key'].upper())
        
        return '+'.join(parts)
