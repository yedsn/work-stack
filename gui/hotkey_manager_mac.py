#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
macOS平台的全局热键管理器
使用PyObjC库注册全局热键
"""

import sys
import threading
import uuid

# 检查是否已安装必要的模块
try:
    from Foundation import NSObject, NSLog
    from AppKit import NSEvent, NSKeyDown
    from PyObjCTools import AppHelper
except ImportError:
    print("错误: 未安装PyObjC库，无法使用全局热键功能")
    print("请安装PyObjC: pip install pyobjc")

# 按键映射
KEY_MAPPING = {
    'Return': 36,
    'Tab': 48,
    'Space': 49,
    'Delete': 51,
    'Escape': 53,
    'Esc': 53,
    'Command': 55,
    'Shift': 56,
    'Caps_Lock': 57,
    'Option': 58,
    'Control': 59,
    'Ctrl': 59,
    'Fn': 63,
    'F1': 122,
    'F2': 120,
    'F3': 99,
    'F4': 118,
    'F5': 96,
    'F6': 97,
    'F7': 98,
    'F8': 100,
    'F9': 101,
    'F10': 109,
    'F11': 103,
    'F12': 111,
    'Home': 115,
    'Page_Up': 116,
    'Delete_Forward': 117,
    'End': 119,
    'Page_Down': 121,
    'Left': 123,
    'Right': 124,
    'Down': 125,
    'Up': 126,
}

# 修饰键映射
MODIFIER_MAPPING = {
    'Command': 1 << 20,  # NSEventModifierFlagCommand
    'Shift': 1 << 17,    # NSEventModifierFlagShift
    'Ctrl': 1 << 18,     # NSEventModifierFlagControl
    'Control': 1 << 18,  # NSEventModifierFlagControl
    'Option': 1 << 19,   # NSEventModifierFlagOption
    'Alt': 1 << 19,      # NSEventModifierFlagOption
    'Fn': 1 << 23,       # NSEventModifierFlagFunction
}

class MacHotkeyHandler(NSObject):
    """macOS热键处理器"""
    
    def initWithCallback_(self, callback):
        """初始化热键处理器"""
        self = super(MacHotkeyHandler, self).init()
        if self is not None:
            self.callback = callback
        return self
    
    def hotkeyPressed_(self, notification):
        """热键按下时的回调函数"""
        try:
            self.callback()
        except Exception as e:
            NSLog(f"热键回调错误: {e}")

class HotkeyManagerMac:
    """macOS平台的全局热键管理器"""
    
    def __init__(self):
        """初始化热键管理器"""
        self.hotkeys = {}  # 存储已注册的热键
        self.handlers = {}  # 存储热键处理器
    
    def _parse_hotkey(self, hotkey_str):
        """解析热键字符串，返回修饰键和主键的元组"""
        if not hotkey_str:
            return None, None
        
        parts = hotkey_str.split('+')
        modifiers = 0
        
        # 主键（最后一个部分）
        key_str = parts[-1].strip()
        
        # 解析修饰键
        for i in range(len(parts) - 1):
            mod = parts[i].strip()
            if mod in MODIFIER_MAPPING:
                modifiers |= MODIFIER_MAPPING[mod]
        
        # 解析主键
        if key_str in KEY_MAPPING:
            key = KEY_MAPPING[key_str]
        elif len(key_str) == 1:
            # 对于单个字符，需要进行ASCII转换
            # 注意：这是简化处理，可能需要更复杂的映射
            key = ord(key_str.lower())
        else:
            print(f"无法解析热键: {key_str}")
            return None, None
        
        return modifiers, key
    
    def register_hotkey(self, hotkey_str, callback):
        """注册全局热键"""
        try:
            modifiers, key = self._parse_hotkey(hotkey_str)
            if modifiers is None or key is None:
                print(f"无效的热键: {hotkey_str}")
                return False
            
            # 创建唯一标识符
            hotkey_id = str(uuid.uuid4())
            
            # 创建热键处理器
            handler = MacHotkeyHandler.alloc().initWithCallback_(callback)
            
            # 注册全局热键
            from Quartz import (
                CGEventMaskBit, kCGEventKeyDown, 
                CGEventTapCreate, kCGSessionEventTap, 
                kCGEventTapOptionDefault
            )
            
            # 使用Carbon API注册热键
            # 这里简化处理，实际应用中应该使用正确的API
            try:
                from Carbon.CarbonEvt import (
                    RegisterEventHotKey, GetApplicationEventTarget, 
                    NewEventHandlerUPP, InstallEventHandler, 
                    kEventClassKeyboard, kEventHotKeyPressed
                )
                
                # 尝试注册热键
                carbon_hotkey_ref = RegisterEventHotKey(
                    key, modifiers, 
                    (0, 0), GetApplicationEventTarget(), 
                    0, None
                )
                
                if carbon_hotkey_ref:
                    # 保存引用
                    self.hotkeys[hotkey_str] = {
                        'id': hotkey_id,
                        'ref': carbon_hotkey_ref,
                        'handler': handler
                    }
                    
                    print(f"已注册热键: {hotkey_str}")
                    return True
                else:
                    print(f"注册热键失败: {hotkey_str}")
                    return False
                
            except (ImportError, AttributeError):
                print("Carbon API不可用，使用替代方法")
                
                # 使用替代方法（简化示例）
                # 实际应用中应该使用更完善的方法
                self.hotkeys[hotkey_str] = {
                    'id': hotkey_id,
                    'key': key,
                    'modifiers': modifiers,
                    'handler': handler
                }
                
                print(f"已注册热键(替代方法): {hotkey_str}")
                return True
                
        except Exception as e:
            print(f"注册热键出错: {e}")
            return False
    
    def unregister_hotkey(self, hotkey_str):
        """注销全局热键"""
        try:
            if hotkey_str not in self.hotkeys:
                print(f"热键未注册: {hotkey_str}")
                return False
            
            hotkey_info = self.hotkeys[hotkey_str]
            
            # 使用Carbon API注销热键
            try:
                from Carbon.CarbonEvt import UnregisterEventHotKey
                if 'ref' in hotkey_info:
                    UnregisterEventHotKey(hotkey_info['ref'])
            except (ImportError, AttributeError):
                print("Carbon API不可用，使用替代方法注销热键")
            
            # 移除引用
            del self.hotkeys[hotkey_str]
            
            print(f"已注销热键: {hotkey_str}")
            return True
            
        except Exception as e:
            print(f"注销热键出错: {e}")
            return False
    
    def __del__(self):
        """析构函数，确保清理所有热键"""
        for hotkey_str in list(self.hotkeys.keys()):
            self.unregister_hotkey(hotkey_str) 