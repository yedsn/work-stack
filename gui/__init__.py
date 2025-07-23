#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GUI组件包

包含应用程序的所有图形用户界面组件：
- main_window: 主窗口
- category_tab: 分类标签页
- launch_item: 启动项组件
- base_dialog: 对话框基类
- 各种设置对话框
- 热键管理器
"""

# 条件导入GUI组件（需要PyQt5）
__all__ = []

try:
    from .base_dialog import BaseDialog
    __all__.append('BaseDialog')
except ImportError:
    pass

try:
    from .flow_layout import FlowLayout
    __all__.append('FlowLayout')
except ImportError:
    pass

try:
    from .main_window import LaunchGUI
    __all__.append('LaunchGUI')
except ImportError:
    pass

try:
    from .category_tab import CategoryTab
    __all__.append('CategoryTab')
except ImportError:
    pass

try:
    from .launch_item import LaunchItem
    __all__.append('LaunchItem')
except ImportError:
    pass 