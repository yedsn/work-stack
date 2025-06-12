#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Linux平台的全局热键管理器
使用X11库注册全局热键
"""

import sys
import threading
import time

# 检查是否已安装必要的模块
try:
    from Xlib import X, XK, display
    from Xlib.ext import record
    from Xlib.protocol import rq
except ImportError:
    print("错误: 未安装python-xlib库，无法使用全局热键功能")
    print("请安装python-xlib: pip install python-xlib")

# 修饰键映射
MODIFIER_MAPPING = {
    'Shift': X.ShiftMask,
    'Control': X.ControlMask,
    'Ctrl': X.ControlMask,
    'Alt': X.Mod1Mask,
    'Mod1': X.Mod1Mask,
    'Super': X.Mod4Mask,
    'Win': X.Mod4Mask,
}

class HotkeyManagerLinux:
    """Linux平台的全局热键管理器"""
    
    def __init__(self):
        """初始化热键管理器"""
        try:
            self.display = display.Display()
            self.root = self.display.screen().root
            self.context = None
            self.hotkeys = {}  # 存储已注册的热键
            
            # 启动监听线程
            self.running = True
            self.thread = threading.Thread(target=self._event_loop)
            self.thread.daemon = True
            self.thread.start()
        except Exception as e:
            print(f"初始化热键管理器失败: {e}")
            self.display = None
    
    def _parse_hotkey(self, hotkey_str):
        """解析热键字符串，返回修饰键和主键的元组"""
        if not hotkey_str or self.display is None:
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
        try:
            keysym = XK.string_to_keysym(key_str)
            if keysym == 0:
                # 尝试转换为小写
                keysym = XK.string_to_keysym(key_str.lower())
            
            if keysym == 0 and len(key_str) == 1:
                # 对于单个字符，尝试使用ASCII值
                keysym = ord(key_str.lower())
            
            if keysym == 0:
                print(f"无法解析热键: {key_str}")
                return None, None
            
            keycode = self.display.keysym_to_keycode(keysym)
            if keycode == 0:
                print(f"无法获取按键代码: {key_str}")
                return None, None
            
            return modifiers, keycode
        except Exception as e:
            print(f"解析热键出错: {e}")
            return None, None
    
    def register_hotkey(self, hotkey_str, callback):
        """注册全局热键"""
        if self.display is None:
            print("热键管理器未初始化")
            return False
        
        try:
            modifiers, keycode = self._parse_hotkey(hotkey_str)
            if modifiers is None or keycode is None:
                print(f"无效的热键: {hotkey_str}")
                return False
            
            # 尝试注册热键
            self.root.grab_key(
                keycode, modifiers, 
                1, X.GrabModeAsync, X.GrabModeAsync
            )
            
            # 注册其他修饰键组合（处理Caps Lock, Num Lock等状态）
            self.root.grab_key(
                keycode, modifiers | X.Mod2Mask, 
                1, X.GrabModeAsync, X.GrabModeAsync
            )
            
            self.root.grab_key(
                keycode, modifiers | X.LockMask, 
                1, X.GrabModeAsync, X.GrabModeAsync
            )
            
            self.root.grab_key(
                keycode, modifiers | X.Mod2Mask | X.LockMask, 
                1, X.GrabModeAsync, X.GrabModeAsync
            )
            
            # 保存热键信息
            self.hotkeys[hotkey_str] = {
                'modifiers': modifiers,
                'keycode': keycode,
                'callback': callback
            }
            
            print(f"已注册热键: {hotkey_str}")
            self.display.sync()
            return True
        except Exception as e:
            print(f"注册热键出错: {e}")
            return False
    
    def unregister_hotkey(self, hotkey_str):
        """注销全局热键"""
        if self.display is None or hotkey_str not in self.hotkeys:
            print(f"热键未注册: {hotkey_str}")
            return False
        
        try:
            hotkey = self.hotkeys[hotkey_str]
            modifiers, keycode = hotkey['modifiers'], hotkey['keycode']
            
            # 注销热键
            self.root.ungrab_key(keycode, modifiers)
            self.root.ungrab_key(keycode, modifiers | X.Mod2Mask)
            self.root.ungrab_key(keycode, modifiers | X.LockMask)
            self.root.ungrab_key(keycode, modifiers | X.Mod2Mask | X.LockMask)
            
            # 移除热键信息
            del self.hotkeys[hotkey_str]
            
            print(f"已注销热键: {hotkey_str}")
            self.display.sync()
            return True
        except Exception as e:
            print(f"注销热键出错: {e}")
            return False
    
    def _event_loop(self):
        """事件循环，监听热键事件"""
        if self.display is None:
            return
        
        try:
            while self.running:
                event = self.display.next_event()
                
                if event.type == X.KeyPress:
                    # 检查是否是已注册的热键
                    for hotkey_str, info in self.hotkeys.items():
                        modifiers = info['modifiers']
                        keycode = info['keycode']
                        callback = info['callback']
                        
                        # 检查按键是否匹配（考虑NumLock和CapsLock状态）
                        if event.detail == keycode and (
                            event.state & (modifiers | X.LockMask | X.Mod2Mask) == modifiers or
                            event.state & (modifiers | X.LockMask) == modifiers or
                            event.state & (modifiers | X.Mod2Mask) == modifiers or
                            event.state & modifiers == modifiers
                        ):
                            try:
                                callback()
                            except Exception as e:
                                print(f"热键回调错误: {e}")
                
                # 处理其他事件
                self.display.flush()
                
                # 释放CPU时间
                time.sleep(0.01)
        except Exception as e:
            if self.running:
                print(f"热键监听线程错误: {e}")
    
    def __del__(self):
        """析构函数，确保清理所有热键"""
        self.running = False
        
        if hasattr(self, 'hotkeys') and self.display:
            for hotkey_str in list(self.hotkeys.keys()):
                self.unregister_hotkey(hotkey_str)
            
            if hasattr(self, 'context') and self.context:
                self.context.close()
            
            self.display.close() 