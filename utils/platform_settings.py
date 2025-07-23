#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, Any
from utils.os_utils import get_os_type as get_platform

# 各平台样式设置
PLATFORM_STYLES = {
    'mac': {
        'main_window': """
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
                border-radius: 2px;
            }
            QTabBar::tab {
                background-color: #e6e6e6;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 10px;
                margin-right: 2px;
                font-size: 12px;
                color: #333333;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
                color: black;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #f0f0f0;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 2px;
                background-color: white;
                min-height: 20px;
                color: black;
            }
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #4a86e8;
                border-radius: 2px;
                background-color: #4a86e8;
                color: white;
                font-size: 12px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #3a76d8;
                border-color: #3a76d8;
            }
            QPushButton:pressed {
                background-color: #2a66c8;
                border-color: #2a66c8;
            }
            QLabel {
                color: black;
            }
            QDialog {
                background-color: #f5f5f5;
            }
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 2px;
                background-color: white;
                padding: 2px;
                color: black;
            }
            QListWidget::item {
                padding: 5px;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background-color: #e5efff;
                color: black;
                border: 1px solid #b3d7ff;
            }
            QListWidget::item:hover:!selected {
                background-color: #f0f8ff;
            }
        """,
        # ParamLabel样式
        'param_label': """
            QLabel {
                color: #0066cc;
                text-decoration: underline;
                padding: 2px 4px;
                background-color: #f0f0f0;
                border-radius: 3px;
                margin-right: 3px;
                font-size: 13px;
                border: none;
            }
            QLabel:hover {
                background-color: #e0e0e0;
            }
        """,
        'param_label_selected': """
            QLabel {
                color: #0066cc;
                text-decoration: underline;
                padding: 2px 4px;
                background-color: #d0e0ff;
                border-radius: 3px;
                margin-right: 3px;
                border: none;
            }
            QLabel:hover {
                background-color: #c0d0ff;
            }
        """,
        # LaunchItem样式
        'launch_item': """
            LaunchItem {
                background-color: white;
                border: 1px solid #dddddd;
                border-radius: 6px;
            }
            LaunchItem:hover {
                background-color: #f0f8ff;
                border: 1px solid #4a86e8;
            }
        """,
        'launch_item_selected': """
            LaunchItem {
                background-color: white;
                border: 1px solid #4a86e8;
                border-radius: 6px;
            }
        """,
        # 标题栏样式
        'title_bar': """
            background-color: #f0f0f0;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        """,
        'title_bar_selected': """
            background-color: #e5efff;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        """,
        # 标题标签样式
        'title_label': """
            color: black; 
            background-color: transparent;
        """,
        'title_label_selected': """
            color: black; 
            background-color: transparent;
        """,
        # 内容区域样式
        'content_widget': """
            background-color: white;
        """,
        'content_widget_selected': """
            background-color: white;
        """,
        'content_label_selected': """
            background-color: transparent;
        """,
        # 应用标签样式
        'app_label': """
            color: #333333; 
            font-size: 14px;
        """,
        # 分类标签样式
        'category_label': """
            color: #0066cc; 
            font-style: italic; 
            font-size: 14px;
        """,
        # 参数标签样式
        'params_label': """
            color: #333333; 
            font-size: 14px;
        """
    },
    'windows': {
        'main_window': """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 5px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #f0f0f0;
            }
            QLineEdit, QPushButton {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #4a86e8;
                color: white;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
        """,
        # ParamLabel样式
        'param_label': """
            QLabel {
                color: #0066cc;
                text-decoration: underline;
                padding: 2px 5px;
                background-color: #f0f0f0;
                border-radius: 3px;
                margin-right: 5px;
                font-size: 18px;
            }
            QLabel:hover {
                background-color: #e0e0e0;
            }
        """,
        'param_label_selected': """
            QLabel {
                color: #0066cc;
                text-decoration: underline;
                padding: 2px 5px;
                background-color: #d0e0ff;
                border-radius: 3px;
                margin-right: 5px;
                font-size: 18px;
            }
            QLabel:hover {
                background-color: #c0d0ff;
            }
        """,
        # LaunchItem样式
        'launch_item': """
            LaunchItem {
                background-color: white;
                border: 1px solid #dddddd;
                border-radius: 5px;
            }
            LaunchItem:hover {
                background-color: #f0f8ff;
                border: 1px solid #4a86e8;
            }
        """,
        'launch_item_selected': """
            LaunchItem {
                background-color: #e6f0ff;
                border: 2px solid #4a86e8;
                border-radius: 5px;
            }
        """,
        # 标题栏样式
        'title_bar': """
            background-color: #f0f0f0;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        """,
        'title_bar_selected': """
            background-color: #e5efff;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        """,
        # 标题标签样式
        'title_label': """
            color: black; 
            background-color: transparent;
        """,
        'title_label_selected': """
            color: black; 
            background-color: transparent;
        """,
        # 内容区域样式
        'content_widget': """
            background-color: white;
        """,
        'content_widget_selected': """
            background-color: #f5f9ff;
        """,
        'content_label_selected': """
            background-color: transparent;
        """,
        # 应用标签样式
        'app_label': """
            color: #333333; 
            font-size: 20px;
        """,
        # 分类标签样式
        'category_label': """
            color: #0066cc; 
            font-style: italic; 
            font-size: 20px;
        """,
        # 参数标签样式
        'params_label': """
            color: #333333; 
            font-size: 20px;
        """
    },
    'linux': {
        'main_window': """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 5px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #f0f0f0;
            }
            QLineEdit, QPushButton {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #4a86e8;
                color: white;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
        """,
        # ParamLabel样式 (Linux使用与Windows相似的样式)
        'param_label': """
            QLabel {
                color: #0066cc;
                text-decoration: underline;
                padding: 2px 5px;
                background-color: #f0f0f0;
                border-radius: 3px;
                margin-right: 5px;
                font-size: 18px;
            }
            QLabel:hover {
                background-color: #e0e0e0;
            }
        """,
        'param_label_selected': """
            QLabel {
                color: #0066cc;
                text-decoration: underline;
                padding: 2px 5px;
                background-color: #d0e0ff;
                border-radius: 3px;
                margin-right: 5px;
                font-size: 18px;
            }
            QLabel:hover {
                background-color: #c0d0ff;
            }
        """,
        # LaunchItem样式
        'launch_item': """
            LaunchItem {
                background-color: white;
                border: 1px solid #dddddd;
                border-radius: 5px;
            }
            LaunchItem:hover {
                background-color: #f0f8ff;
                border: 1px solid #4a86e8;
            }
        """,
        'launch_item_selected': """
            LaunchItem {
                background-color: #e6f0ff;
                border: 2px solid #4a86e8;
                border-radius: 5px;
            }
        """,
        # 标题栏样式
        'title_bar': """
            background-color: #f0f0f0;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        """,
        'title_bar_selected': """
            background-color: #e5efff;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        """,
        # 标题标签样式
        'title_label': """
            color: black; 
            background-color: transparent;
        """,
        'title_label_selected': """
            color: black; 
            background-color: transparent;
        """,
        # 内容区域样式
        'content_widget': """
            background-color: white;
        """,
        'content_widget_selected': """
            background-color: #f5f9ff;
        """,
        'content_label_selected': """
            background-color: transparent;
        """,
        # 应用标签样式
        'app_label': """
            color: #333333; 
            font-size: 18px;
        """,
        # 分类标签样式
        'category_label': """
            color: #0066cc; 
            font-style: italic; 
            font-size: 18px;
        """,
        # 参数标签样式
        'params_label': """
            color: #333333; 
            font-size: 18px;
        """
    }
}

# 平台特定设置（除样式外的配置）
PLATFORM_SETTINGS = {
    'mac': {
        'window_close_behavior': 'hide',  # macOS点击关闭时隐藏窗口而不是退出
        'app_activate_method': 'appkit',  # 使用AppKit激活窗口
        'default_window_size': {
            'width_ratio': 0.8,
            'height_ratio': 0.8,
            'min_width': 1200,
            'min_height': 800,
        },
        # 字体大小设置
        'font_sizes': {
            'title': 18,
            'app_label': 14,
            'category_label': 14,
            'params_label': 14,
            'param_label': 13
        },
        # 布局边距和间距
        'layouts': {
            'launch_item_margins': [5, 0, 5, 5],  # 左、上、右、下
            'launch_item_spacing': 0,
            'content_margins': [8, 3, 8, 3],
            'content_spacing': 1,
            'params_spacing': 1,
            'params_top_margin': 1,
            'param_labels_spacing': 1
        },
        # 基础高度设置
        'base_heights': {
            'launch_item': 40,  # 基础高度
            'category_add': 15,  # 有分类标签时增加的高度
            'param_base': 20,    # 参数基础高度
            'param_per_row': 10  # 每行参数增加的高度
        },
        # 参数数量阈值 - 超过此值时需要增加额外高度
        'param_count_threshold': 3,
        # 标题最大长度
        'max_title_length': 20
    },
    'windows': {
        'window_close_behavior': 'minimize_to_tray',  # 根据托盘设置决定
        'app_activate_method': 'windows_api',  # 使用Windows API激活窗口
        'default_window_size': {
            'width_ratio': 0.8,
            'height_ratio': 0.8,
            'min_width': 1200,
            'min_height': 800,
        },
        # 字体大小设置
        'font_sizes': {
            'title': 18,
            'app_label': 20,
            'category_label': 20,
            'params_label': 20,
            'param_label': 16
        },
        # 布局边距和间距
        'layouts': {
            'launch_item_margins': [15, 15, 15, 15],  # 左、上、右、下
            'launch_item_spacing': 8,
            'content_margins': [10, 10, 10, 5],
            'content_spacing': 6,
            'params_spacing': 2,
            'params_top_margin': 2,
            'param_labels_spacing': 2
        },
        # 基础高度设置
        'base_heights': {
            'launch_item': 60,  # 基础高度
            'category_add': 20,  # 有分类标签时增加的高度
            'param_base': 20,    # 参数基础高度
            'param_per_row': 25  # 每行参数增加的高度
        },
        # 参数数量阈值 - 超过此值时需要增加额外高度
        'param_count_threshold': 3,
        # 不对标题长度做限制
        'max_title_length': None
    },
    'linux': {
        'window_close_behavior': 'minimize_to_tray',  # 根据托盘设置决定
        'app_activate_method': 'standard',  # 使用标准Qt方法
        'default_window_size': {
            'width_ratio': 0.8,
            'height_ratio': 0.8,
            'min_width': 1200,
            'min_height': 800,
        },
        # 字体大小设置
        'font_sizes': {
            'title': 16,
            'app_label': 18,
            'category_label': 18,
            'params_label': 18,
            'param_label': 16
        },
        # 布局边距和间距
        'layouts': {
            'launch_item_margins': [12, 12, 12, 12],  # 左、上、右、下
            'launch_item_spacing': 6,
            'content_margins': [10, 8, 10, 5],
            'content_spacing': 5,
            'params_spacing': 2,
            'params_top_margin': 2,
            'param_labels_spacing': 2
        },
        # 基础高度设置
        'base_heights': {
            'launch_item': 50,  # 基础高度
            'category_add': 18,  # 有分类标签时增加的高度
            'param_base': 20,    # 参数基础高度
            'param_per_row': 22  # 每行参数增加的高度
        },
        # 参数数量阈值 - 超过此值时需要增加额外高度
        'param_count_threshold': 3,
        # 不对标题长度做限制
        'max_title_length': 30
    }
}

# 获取当前平台的设置
def get_platform_style(style_name: str = 'main_window') -> str:
    """获取当前平台的样式设置"""
    platform = get_platform()
    return PLATFORM_STYLES.get(platform, PLATFORM_STYLES['windows']).get(style_name, '')

def get_platform_setting(setting_path: str = None) -> Any:
    """获取当前平台的特定设置
    
    参数:
        setting_path: 设置路径，例如 'window_close_behavior'
    """
    platform = get_platform()
    settings = PLATFORM_SETTINGS.get(platform, PLATFORM_SETTINGS['windows'])
    
    if not setting_path:
        return settings
    
    # 处理嵌套路径，例如 'default_window_size.width_ratio'
    if '.' in setting_path:
        parts = setting_path.split('.')
        current = settings
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current
    
    return settings.get(setting_path, None)

# 单独检查平台是否是Windows/Mac/Linux
def is_windows() -> bool:
    """检查当前平台是否是Windows"""
    return get_platform() == 'windows'

def is_mac() -> bool:
    """检查当前平台是否是macOS"""
    return get_platform() == 'mac'

def is_linux() -> bool:
    """检查当前平台是否是Linux"""
    return get_platform() == 'linux' 