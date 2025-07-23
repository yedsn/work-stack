#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
import math
import time
import psutil
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QTabWidget, QFileDialog, QInputDialog, QMenu,
                            QAction, QMessageBox, QDialog, QListWidget, QListWidgetItem,
                            QSystemTrayIcon, QApplication, QCheckBox, QPlainTextEdit,
                            QStackedWidget)
from PyQt5.QtCore import Qt, QPoint, QTimer, QThread, pyqtSignal, QObject, QRegExp
from PyQt5.QtGui import (QCursor, QIcon, QColor, QKeySequence, QMovie, QTextCharFormat, 
                       QFont, QSyntaxHighlighter, QTextCursor)
from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QTextDocument
from gui.category_tab import CategoryTab
from utils.config_manager import load_config, save_config, flush_config
from gui.launch_item import LaunchItem
from utils.logger import get_logger
from utils.platform_settings import (get_platform_style, get_platform_setting, 
                                    is_windows, is_mac, is_linux)
from utils.gist_manager import GistManager
from utils.open_gist_manager import OpenGistManager
from utils.webdav_manager import WebDAVManager
from gui.github_settings_dialog import GitHubSettingsDialog
from gui.sync_settings_dialog import SyncSettingsDialog
from gui.config_history_dialog import ConfigHistoryDialog
from utils.config_history import ConfigHistoryManager

# 配置加载器类
class ConfigLoader(QObject):
    """异步配置加载器"""
    config_loaded = pyqtSignal(dict)  # 配置加载完成信号
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger()
    
    def load(self):
        """在后台线程中加载配置"""
        try:
            config = load_config()
            self.config_loaded.emit(config)
        except Exception as e:
            self.logger.error(f"异步加载配置失败: {e}")
            # 发送空配置
            self.config_loaded.emit({})
        finally:
            self.finished.emit()

# 同步操作的Worker类
class SyncWorker(QObject):
    """用于后台执行同步操作的Worker类"""
    finished = pyqtSignal(bool, str, object)  # 成功标志，消息，数据（可选）
    progress = pyqtSignal(str, bool)  # 服务名称，成功标志
    
    def __init__(self, operation_type):
        super().__init__()
        self.operation_type = operation_type  # "upload" 或 "download"
        self.logger = get_logger()
    
    def run(self):
        """执行同步操作"""
        try:
            # 获取所有启用的同步服务
            enabled_services = []
            
            # 检查GitHub Gist
            github_manager = GistManager()
            if github_manager.enabled:
                enabled_services.append(("GitHub Gist", github_manager))
            
            # 检查Open Gist
            open_gist_manager = OpenGistManager()
            if open_gist_manager.enabled:
                enabled_services.append(("Open Gist", open_gist_manager))
                
            # 检查WebDAV
            webdav_manager = WebDAVManager()
            if webdav_manager.enabled:
                enabled_services.append(("WebDAV", webdav_manager))
            
            # 如果没有启用的服务，返回失败
            if not enabled_services:
                self.finished.emit(False, "没有启用的同步服务", None)
                return
            
            # 根据操作类型执行同步
            if self.operation_type == "upload":
                results = []
                for service_name, manager in enabled_services:
                    success, message = manager.upload_config()
                    results.append((service_name, success, message))
                    self.progress.emit(service_name, success)
                
                # 构建结果消息
                result_message = "上传结果:\n\n"
                success_count = 0
                for service_name, success, message in results:
                    status = "成功" if success else "失败"
                    if success:
                        success_count += 1
                    result_message += f"{service_name}: {status} - {message}\n"
                
                # 发送最终结果
                self.finished.emit(success_count > 0, result_message, None)
            
            elif self.operation_type == "download":
                results = []
                downloaded_configs = []
                
                for service_name, manager in enabled_services:
                    success, message, config_data = manager.download_config()
                    results.append((service_name, success, message))
                    self.progress.emit(service_name, success)
                    
                    if success and config_data:
                        downloaded_configs.append((service_name, config_data))
                
                # 构建结果消息
                result_message = "下载结果:\n\n"
                for service_name, success, message in results:
                    status = "成功" if success else "失败"
                    result_message += f"{service_name}: {status} - {message}\n"
                
                # 发送最终结果
                if downloaded_configs:
                    # 如果只有一个配置，直接使用第一个
                    config_to_use = downloaded_configs[0][1]
                    service_name = downloaded_configs[0][0]
                    
                    # 如果有多个配置，返回所有下载的配置，让调用方处理选择
                    if len(downloaded_configs) > 1:
                        self.finished.emit(True, result_message, downloaded_configs)
                    else:
                        self.finished.emit(True, result_message, config_to_use)
                else:
                    self.finished.emit(False, result_message, None)
        except Exception as e:
            self.logger.error(f"同步操作出错: {e}")
            self.finished.emit(False, f"操作出错: {str(e)}", None)

# 加载状态按钮类
class LoadingButton(QPushButton):
    """带有加载动画的按钮"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.default_text = text
        self.default_style = ""
        self.setFixedSize(36, 36)
        self.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #e0e0e0;
                margin-left: 2px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """)
        self.default_style = self.styleSheet()
        
        # 创建加载动画标签
        self.loading_icons = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        self.current_icon_index = 0
        # 优化：使用合并的主定时器管理所有动画
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.update_loading_icon)
        self.loading_timer.setInterval(150)  # 增加间隔以减少CPU使用
        
    def start_loading(self):
        """开始加载动画"""
        self.setEnabled(False)
        self.default_text = self.text()
        self.current_icon_index = 0
        self.loading_timer.start()  # 使用默认间隔150ms
        self.update_loading_icon()
        self.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                border: 1px solid #4a86e8;
                border-radius: 4px;
                background-color: #e8f0fe;
                margin-left: 2px;
                padding: 5px;
            }
        """)
    
    def stop_loading(self):
        """停止加载动画"""
        self.loading_timer.stop()
        self.setText(self.default_text)
        self.setEnabled(True)
        self.setStyleSheet(self.default_style)
    
    def update_loading_icon(self):
        """更新加载图标"""
        self.setText(self.loading_icons[self.current_icon_index])
        self.current_icon_index = (self.current_icon_index + 1) % len(self.loading_icons)

# 加载遮罩类，在视图切换时显示
class LoadingOverlay(QWidget):
    """加载遮罩层，用于提供视图切换时的视觉反馈"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 不要覆盖parent()方法
        # self.parent = parent
        
        # 初始化为隐藏状态
        self.setVisible(False)
        
        # 设置为无边框、透明背景
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置加载文本和样式
        self.loading_text = QLabel("正在切换视图...", self)
        self.loading_text.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
            background-color: transparent;
        """)
        self.loading_text.setAlignment(Qt.AlignCenter)
        
        # 创建加载动画点
        self.dots_timer = QTimer(self)
        self.dots_timer.setInterval(400)  # 增加间隔以减少CPU使用
        self.dots_timer.timeout.connect(self.update_dots)
        self.dot_count = 0
        
        # 设置背景样式
        self.setStyleSheet("""
            background-color: rgba(0, 0, 0, 150);
        """)
    
    def showEvent(self, event):
        """显示时启动动画"""
        self.dots_timer.start()
        super().showEvent(event)
    
    def hideEvent(self, event):
        """隐藏时停止动画"""
        self.dots_timer.stop()
        super().hideEvent(event)
    
    def update_dots(self):
        """更新加载文本中的点数"""
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.loading_text.setText(f"正在切换视图{dots}")
        self.update()
    
    def resizeEvent(self, event):
        """调整大小时重新布局"""
        super().resizeEvent(event)
        # 调整遮罩大小为父窗口大小
        parent_widget = self.parentWidget()
        if parent_widget:
            self.setGeometry(0, 0, parent_widget.width(), parent_widget.height())
            self.loading_text.setGeometry(0, 0, self.width(), self.height())

# 根据平台导入不同的模块
if is_windows():
    # Windows 平台特定导入
    import win32gui
    import win32process
elif is_mac():
    # macOS 平台特定导入
    import subprocess
    import AppKit
else:
    # Linux 平台特定导入
    pass

# JSON语法高亮器
class JsonSyntaxHighlighter(QSyntaxHighlighter):
    """简单的JSON语法高亮"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.highlighting_rules = []
        
        # 字符串格式 - 绿色
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#008000"))
        string_pattern = QRegExp("\".*\"")
        string_pattern.setMinimal(True)  # 非贪婪模式
        self.highlighting_rules.append((string_pattern, string_format))
        
        # 数字格式 - 蓝色
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#0000FF"))
        number_pattern = QRegExp("\\b\\d+\\.?\\d*\\b")
        self.highlighting_rules.append((number_pattern, number_format))
        
        # 键名格式 - 红色
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#A52A2A"))
        key_pattern = QRegExp("\"[^\"]*\"(?=\\s*:)")
        self.highlighting_rules.append((key_pattern, key_format))
        
        # 布尔值和null - 紫色
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#800080"))
        keyword_format.setFontWeight(QFont.Bold)
        keyword_pattern = QRegExp("\\b(true|false|null)\\b")
        self.highlighting_rules.append((keyword_pattern, keyword_format))
        
        # 括号 - 深灰色
        bracket_format = QTextCharFormat()
        bracket_format.setForeground(QColor("#303030"))
        bracket_format.setFontWeight(QFont.Bold)
        bracket_pattern = QRegExp("[\\[\\]{}]")
        self.highlighting_rules.append((bracket_pattern, bracket_format))
        
    def highlightBlock(self, text):
        """实现高亮方法"""
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

class LaunchGUI(QMainWindow):
    """应用启动器GUI"""
    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self.logger.debug("初始化主窗口")
        
        # 缓存平台检测结果，避免重复判断
        self._platform_cache = {
            'activate_method': get_platform_setting('app_activate_method'),
            'is_windows': is_windows(),
            'is_mac': is_mac()
        }
        
        # 配置缓存机制
        self._config_cache = None
        self._config_cache_time = 0
        self._config_cache_timeout = 5  # 缓存5秒
        
        # 热键管理器引用（由主程序设置）
        self.hotkey_manager = None
        
        # 设置窗口标题和大小
        self.setWindowTitle("应用启动器")

        # 获取设备唯一标识
        import platform
        import uuid
        # 获取设备唯一标识（使用主机名和MAC地址组合）
        device_id = platform.node() + "-" + str(uuid.getnode())
        self.device_id = device_id
        
        # 创建加载遮罩
        self.loading_overlay = LoadingOverlay(self)
        
        # 初始化配置历史管理器
        self.history_manager = ConfigHistoryManager()

        # 从配置中读取窗口大小
        config = load_config()
        
        # 获取屏幕大小用于计算默认值
        screen_rect = QApplication.desktop().screenGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()
        
        # 计算默认尺寸，使用平台设置中的比例
        width_ratio = get_platform_setting('default_window_size.width_ratio')
        height_ratio = get_platform_setting('default_window_size.height_ratio')
        min_width = get_platform_setting('default_window_size.min_width')
        min_height = get_platform_setting('default_window_size.min_height')
        
        default_width = max(int(screen_width * width_ratio), min_width)
        default_height = max(int(screen_height * height_ratio), min_height)
        
        # 尝试获取当前设备的窗口大小设置
        device_window_sizes = config.get("device_window_sizes", {})
        device_window_size = device_window_sizes.get(device_id)
        
        # 如果当前设备有保存的设置，则使用；否则使用默认值
        if device_window_size:
            width = device_window_size.get("width", default_width)
            height = device_window_size.get("height", default_height)
            self.logger.debug(f"使用设备 {device_id} 保存的窗口大小: {width}x{height}")
        else:
            width = default_width
            height = default_height
            self.logger.debug(f"未找到设备 {device_id} 的窗口大小设置，使用默认值: {width}x{height}")

        self.resize(width, height)
        self.setMinimumSize(900, 600)
        
        # 系统托盘图标
        self.tray_icon = None
        
        # 当前选中的项目索引（用于键盘导航）
        self.current_selected_index = -1
        
        # 创建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建堆叠小部件，用于切换操作视图和配置文件视图
        self.stacked_widget = QStackedWidget()
        
        # 创建操作视图小部件
        self.operation_widget = QWidget()
        operation_layout = QVBoxLayout(self.operation_widget)
        operation_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建配置文件视图小部件
        self.config_widget = QWidget()
        config_layout = QVBoxLayout(self.config_widget)
        config_layout.setContentsMargins(0, 0, 0, 0)
        
        # 将两个视图添加到堆叠小部件
        self.stacked_widget.addWidget(self.operation_widget)
        self.stacked_widget.addWidget(self.config_widget)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tabs = {}  # 存储分类标签页
        
        # 默认分类
        default_categories = ["全部", "娱乐", "工作", "文档"]
        for category in default_categories:
            self.add_category(category)
        
        # 添加一个"+"按钮到标签栏的右侧
        add_tab_button = QPushButton("+")
        add_tab_button.setFixedSize(30, 30)  # 增加按钮大小
        add_tab_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 4px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                font-size: 16px;
                padding: 0px;
                text-align: center;
                margin: 2px;
                line-height: 1;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
                border-color: #4a86e8;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """)
        add_tab_button.setToolTip("添加新分类")
        add_tab_button.clicked.connect(self.add_new_category)
        
        # 创建一个容器来放置添加按钮，确保位置正确
        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 0, 5, 0)
        corner_layout.addWidget(add_tab_button)
        corner_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 将容器添加到标签栏右侧
        self.tab_widget.setCornerWidget(corner_widget, Qt.TopRightCorner)
        
        # 设置标签页可右键菜单
        self.tab_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self.show_tab_context_menu)
        
        # 启用标签页拖动
        self.tab_widget.setMovable(True)
        
        # 在控制布局上方添加搜索框和菜单按钮
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索...")
        self.search_input.textChanged.connect(self.filter_items)
        # 为搜索框设置回车键处理
        self.search_input.returnPressed.connect(self.handle_search_return)
        # 为搜索框添加键盘事件处理
        self.search_input.installEventFilter(self)
        
        # 添加清空搜索按钮
        clear_search_button = QPushButton("✕")
        clear_search_button.setFixedSize(36, 36)
        clear_search_button.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #e0e0e0;
                margin-left: 2px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """)
        clear_search_button.setToolTip("清空搜索")
        clear_search_button.clicked.connect(self.clear_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(clear_search_button)
        
        # 添加刷新按钮
        refresh_button = QPushButton("↻")  # 刷新图标
        refresh_button.setFixedSize(36, 36)
        refresh_button.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #e0e0e0;
                margin-left: 2px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """)
        refresh_button.setToolTip("刷新 (F5)")
        refresh_button.clicked.connect(self.refresh_from_config)
        search_layout.addWidget(refresh_button)
        
        # 添加GitHub上传按钮
        self.upload_button = LoadingButton("↑")  # 上传图标
        self.upload_button.setToolTip("上传配置到同步服务")
        self.upload_button.clicked.connect(self.upload_to_github)
        search_layout.addWidget(self.upload_button)
        
        # 添加GitHub下载按钮
        self.download_button = LoadingButton("↓")  # 下载图标
        self.download_button.setToolTip("从同步服务下载配置")
        self.download_button.clicked.connect(self.download_from_github)
        search_layout.addWidget(self.download_button)
        
        # 添加菜单按钮到搜索行
        menu_button = QPushButton("☰")  # 汉堡菜单图标
        menu_button.setFixedSize(36, 36)  # 增加按钮大小
        menu_button.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #e0e0e0;
                margin-left: 2px;
                padding: 5px;  /* 增加内边距 */
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """)
        menu_button.setToolTip("菜单")
        menu_button.clicked.connect(self.show_menu)
        search_layout.addWidget(menu_button)

        # 将搜索布局添加到操作视图
        operation_layout.addLayout(search_layout)
        operation_layout.addWidget(self.tab_widget)
        
        # 创建控制布局
        control_layout = QHBoxLayout()
        
        # 创建输入控件
        control_layout.addWidget(QLabel("名称:"))
        self.name_input = QLineEdit()
        control_layout.addWidget(self.name_input)
        
        control_layout.addWidget(QLabel("应用:"))
        self.app_input = QLineEdit()
        control_layout.addWidget(self.app_input)
        
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self.browse_app)
        control_layout.addWidget(browse_button)
        
        # 在浏览按钮后添加句柄按钮
        handle_button = QPushButton("选择打开的应用")
        handle_button.setToolTip("从当前运行的窗口中选择应用")
        handle_button.clicked.connect(self.get_window_handle)
        control_layout.addWidget(handle_button)
        
        control_layout.addWidget(QLabel("参数:"))
        self.params_input = QLineEdit()
        control_layout.addWidget(self.params_input)
        
        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_launch_item)
        control_layout.addWidget(add_button)
        
        # 将控制布局添加到操作视图
        operation_layout.addLayout(control_layout)
        
        # 配置文件编辑器设置
        config_editor_label = QLabel("配置文件编辑器 (自动保存):")
        config_layout.addWidget(config_editor_label)
        
        # 添加搜索框布局
        config_search_layout = QHBoxLayout()
        config_search_layout.setContentsMargins(0, 5, 0, 5)
        
        self.config_search_input = QLineEdit()
        self.config_search_input.setPlaceholderText("搜索配置...")
        self.config_search_input.returnPressed.connect(self.search_in_config)
        
        # 样式定义
        search_button_style = """
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #e0e0e0;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
                border-color: #4a86e8;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """
        
        search_prev_button = QPushButton("↑")
        search_prev_button.setFixedSize(36, 36)
        search_prev_button.setToolTip("查找上一个 (Shift+F3)")
        search_prev_button.setStyleSheet(search_button_style)
        search_prev_button.clicked.connect(lambda: self.search_in_config(direction="prev"))
        
        search_next_button = QPushButton("↓")
        search_next_button.setFixedSize(36, 36)
        search_next_button.setToolTip("查找下一个 (F3)")
        search_next_button.setStyleSheet(search_button_style)
        search_next_button.clicked.connect(lambda: self.search_in_config(direction="next"))
        
        config_search_layout.addWidget(QLabel("搜索:"))
        config_search_layout.addWidget(self.config_search_input)
        config_search_layout.addWidget(search_prev_button)
        config_search_layout.addWidget(search_next_button)
        
        # 添加搜索布局到配置视图
        config_layout.addLayout(config_search_layout)
        
        # 创建配置文件编辑器
        self.config_editor = QPlainTextEdit()
        self.config_editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.config_editor.setTabStopWidth(40)  # 设置制表符宽度
        # 设置固定白色背景
        self.config_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #efefef;
                color: black;
                font-family: Consolas, Menlo, Monaco, 'Courier New', monospace;
                font-size: 20px;
                border: 1px solid #cccccc;
            }
        """)
        # 应用JSON语法高亮
        self.json_highlighter = JsonSyntaxHighlighter(self.config_editor.document())
        config_layout.addWidget(self.config_editor)
        
        # 设置自动保存定时器
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.setInterval(1500)  # 增加延迟以减少频繁保存
        self.auto_save_timer.timeout.connect(self.save_config_from_editor)
        
        # 连接编辑器内容变化信号
        self.config_editor.textChanged.connect(self.on_config_text_changed)
        
        # 创建状态标签
        self.config_status_label = QLabel("就绪")
        config_layout.addWidget(self.config_status_label)
        
        # 创建切换视图按钮布局
        view_switch_layout = QHBoxLayout()
        
        # 创建切换视图按钮
        self.switch_view_button = QPushButton("切换到配置文件视图")
        self.switch_view_button.clicked.connect(self.toggle_view)
        view_switch_layout.addWidget(self.switch_view_button)
        
        # 添加弹性空间，确保统计信息显示在右侧
        view_switch_layout.addStretch()
        
        # 添加统计信息标签
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.stats_label.setStyleSheet("color: #666666; font-size: 18px;")
        view_switch_layout.addWidget(self.stats_label)
        
        # 将切换视图按钮添加到主布局
        main_layout.addWidget(self.stacked_widget)
        main_layout.addLayout(view_switch_layout)
        
        # 加载配置
        self.load_config()
        
        # 初始化加载配置文件到编辑器
        self.load_config_to_editor()
        
        # 更新统计信息
        self.update_statistics()
        
        # 为主窗口添加键盘事件过滤器
        self.installEventFilter(self)
        
        # 设置窗口样式
        self.setStyleSheet(get_platform_style('main_window'))
        
        # 设置接受拖放
        self.setAcceptDrops(True)
        
        # 设置窗口图标
        self.setWindowIcon(QIcon("resources/icon.png"))
        
        # 添加F5快捷键用于刷新
        refresh_shortcut = QAction("刷新", self)
        refresh_shortcut.setShortcut(QKeySequence("F5"))
        refresh_shortcut.triggered.connect(self.refresh_from_config)
        self.addAction(refresh_shortcut)
        
        # 添加配置编辑器快捷键
        # 查找下一个 - F3
        find_next_shortcut = QAction("查找下一个", self)
        find_next_shortcut.setShortcut(QKeySequence("F3"))
        find_next_shortcut.triggered.connect(lambda: self.search_in_config(direction="next"))
        self.addAction(find_next_shortcut)
        
        # 查找上一个 - Shift+F3
        find_prev_shortcut = QAction("查找上一个", self)
        find_prev_shortcut.setShortcut(QKeySequence("Shift+F3"))
        find_prev_shortcut.triggered.connect(lambda: self.search_in_config(direction="prev"))
        self.addAction(find_prev_shortcut)
        
        # 查找 - Ctrl+F 
        find_shortcut = QAction("查找", self)
        find_shortcut.setShortcut(QKeySequence("Ctrl+F"))
        find_shortcut.triggered.connect(self.focus_config_search)
        self.addAction(find_shortcut)
        
        # 安装事件过滤器
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)
        
        # 创建自动同步定时器，每小时执行一次同步
        self.auto_sync_timer = QTimer(self)
        self.auto_sync_timer.setInterval(3600000)  # 1小时 = 3600000毫秒
        self.auto_sync_timer.timeout.connect(self.check_auto_sync)
        # 不在初始化时启动定时器，而是在窗口隐藏时启动
        # self.auto_sync_timer.start()
        
        # 检查是否需要自动同步配置
        # self.check_auto_sync() # 禁用启动时的自动同步
    
    def add_category(self, name):
        """添加分类标签页"""
        if name in self.tabs:
            return
        
        # 添加新分类标签页
        tab = CategoryTab(name)
        tab.set_main_window(self)  # 设置主窗口引用
        self.tabs[name] = tab
        self.tab_widget.addTab(tab, name)
        
        return tab
    
    def add_new_category(self):
        """添加新分类"""
        category_name, ok = QInputDialog.getText(self, "新建分类", "请输入分类名称:")
        if ok and category_name:
            self.add_category(category_name)
            self.update_config_debounced()
    
    def show_tab_context_menu(self, position):
        """显示标签页右键菜单"""
        index = self.tab_widget.tabBar().tabAt(position)
        if index >= 0:
            tab_name = self.tab_widget.tabText(index)
            
            menu = QMenu()
            rename_action = QAction("重命名", self)
            delete_action = QAction("删除", self)
            
            menu.addAction(rename_action)
            menu.addAction(delete_action)
            
            action = menu.exec_(self.tab_widget.tabBar().mapToGlobal(position))
            
            if action == rename_action:
                self.rename_category(index, tab_name)
            elif action == delete_action:
                self.delete_category(index, tab_name)
    
    def rename_category(self, index, old_name):
        """重命名分类"""
        new_name, ok = QInputDialog.getText(self, "重命名分类", 
                                          "请输入新的分类名称:", 
                                          text=old_name)
        if ok and new_name and new_name != old_name:
            # 更新标签页文本
            self.tab_widget.setTabText(index, new_name)
            
            # 更新tabs字典
            tab = self.tabs.pop(old_name)
            tab.category_name = new_name
            self.tabs[new_name] = tab
            
            # 更新配置
            self.update_config_debounced()
    
    def delete_category(self, index, name):
        """删除分类"""
        confirm = QMessageBox.question(self, "确认删除", 
                                     f"确定要删除分类 '{name}' 吗？\n该分类下的所有启动项也将被删除。",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            self.tab_widget.removeTab(index)
            self.tabs.pop(name)
            self.update_config_debounced()
    
    def move_launch_item(self, item, from_category, to_category):
        """将启动项移动到其他分类"""
        if to_category not in self.tabs:
            return False
        
        # 从原分类中移除
        if from_category in self.tabs:
            self.tabs[from_category].remove_launch_item(item)
        
        # 添加到新分类
        self.tabs[to_category].add_launch_item(item.name, item.app, item.params)
        
        # 更新配置 - 但不触发全部分类更新
        self.update_config(skip_all_update=True)
        
        # 返回成功
        return True
    
    def get_categories(self):
        """获取所有分类名称"""
        return list(self.tabs.keys())
    
    def add_launch_item(self):
        """添加启动项"""
        name = self.name_input.text().strip()
        app = self.app_input.text().strip()
        params = self.params_input.text().strip()
        
        if not name or not app:
            return
        
        # 处理参数
        if params:
            if params.startswith("[") and params.endswith("]"):
                try:
                    params = json.loads(params)
                except:
                    params = params.split()
            else:
                params = params.split()
        else:
            params = []
        
        # 获取当前标签页
        current_tab = self.tab_widget.currentWidget()
        if current_tab and isinstance(current_tab, CategoryTab):
            current_tab.add_launch_item(name, app, params)
            
            # 清空输入框
            self.name_input.clear()
            self.app_input.clear()
            self.params_input.clear()
            
            # 更新配置
            self.update_config_debounced()
    
    def browse_app(self):
        """浏览选择应用"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择应用", "", "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if file_path:
            self.app_input.setText(file_path)
    
    def load_config(self):
        """同步加载配置（保留用于初始化）"""
        config = load_config()
        self.update_ui_with_config(config)
        
    def update_ui_with_config(self, config):
        """使用配置更新UI"""
        try:
            # 清空现有标签页
            while self.tab_widget.count() > 0:
                self.tab_widget.removeTab(0)
            self.tabs.clear()
            
            # 获取所有分类
            categories = config.get("categories", [])
            
            # 确保"全部"分类在第一位
            if "全部" not in categories:
                categories.insert(0, "全部")
            else:
                # 将"全部"移到第一位
                categories.remove("全部")
                categories.insert(0, "全部")
            
            # 如果没有其他分类，添加默认分类
            if len(categories) <= 1:
                categories.extend(["娱乐", "工作", "文档"])
            
            # 批量创建标签页（减少重绘次数）
            self.tab_widget.setUpdatesEnabled(False)
            try:
                for category in categories:
                    self.add_category(category)
                
                # 添加启动项
                for program in config.get("programs", []):
                    name = program.get("name", "")
                    category = program.get("category", "娱乐")
                    
                    if not name or category not in self.tabs:
                        continue
                    
                    for launch_item in program.get("launch_items", []):
                        app = launch_item.get("app", "")
                        params = launch_item.get("params", [])
                        
                        if not app:
                            continue
                        
                        self.tabs[category].add_launch_item(name, app, params)
                
                # 更新"全部"分类 - 直接从配置加载所有程序
                self.update_all_category_from_config(config)
                
            finally:
                self.tab_widget.setUpdatesEnabled(True)
            
            # 确保所有项目都安装了事件过滤器
            self.install_event_filters_to_all_items()
        except Exception as e:
            self.logger.error(f"更新UI失败: {e}")
            raise
            
            # 更新统计信息
            self.update_statistics()
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
    
    def install_event_filters_to_all_items(self):
        """为所有启动项安装事件过滤器"""
        try:
            for category, tab in self.tabs.items():
                for i in range(tab.content_layout.count()):
                    widget = tab.content_layout.itemAt(i).widget()
                    if widget and isinstance(widget, LaunchItem):
                        widget.setFocusPolicy(Qt.StrongFocus)
                        widget.installEventFilter(self)
        except Exception as e:
            self.logger.error(f"安装事件过滤器失败: {e}")
    
    def update_config(self, skip_all_update=False):
        """更新配置文件"""
        try:
            # 读取现有配置
            config = load_config()
            
            # 保留可能存在的其他配置项，但更新程序和分类
            config["programs"] = []
            config["categories"] = list(self.tabs.keys())
            
            # 遍历所有标签页
            for category, tab in self.tabs.items():
                # 跳过"全部"分类，因为它只是其他分类的集合
                if category == "全部":
                    continue
                
                # 遍历标签页中的所有启动项
                for i in range(tab.content_layout.count()):
                    widget = tab.content_layout.itemAt(i).widget()
                    if widget and isinstance(widget, LaunchItem):
                        # 检查是否已存在相同名称的程序
                        program = None
                        for p in config["programs"]:
                            if p["name"] == widget.name:
                                program = p
                                break
                        
                        # 如果不存在，创建新程序
                        if program is None:
                            program = {
                                "name": widget.name,
                                "description": "",
                                "category": category,
                                "launch_items": []
                            }
                            config["programs"].append(program)
                        else:
                            # 更新分类
                            program["category"] = category
                        
                        # 添加启动项
                        # 检查是否已存在相同的启动项
                        launch_item_exists = False
                        for item in program["launch_items"]:
                            if item["app"] == widget.app and item["params"] == widget.params:
                                launch_item_exists = True
                                break
                        
                        if not launch_item_exists:
                            program["launch_items"].append({
                                "app": widget.app,
                                "params": widget.params
                            })
            
            # 保存配置（使用延迟保存）
            save_config(config, immediate=False)
            
            # 保存历史记录（仅在非跳过更新的情况下）
            if not skip_all_update:
                self.history_manager.save_history(config, "操作界面更新配置")
            
            # 添加自动上传功能
            self.auto_upload_config()
            
            # 如果不跳过，则更新"全部"分类
            if not skip_all_update:
                self.update_all_category()
                
            # 更新统计信息
            self.update_statistics()
        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
    
    def update_config_debounced(self, skip_all_update=False):
        """防抖动的配置更新"""
        # 取消之前的定时器
        if hasattr(self, 'config_update_timer') and self.config_update_timer:
            self.config_update_timer.stop()
        
        # 设置新的定时器，500ms 后执行
        self.config_update_timer = QTimer()
        self.config_update_timer.setSingleShot(True)
        self.config_update_timer.timeout.connect(lambda: self.update_config(skip_all_update))
        self.config_update_timer.start(500)
    
    def handle_tab_click(self, index):
        """处理标签页点击事件"""
        pass
    
    def show_menu(self):
        """显示应用菜单"""
        menu = QMenu()
        config = load_config()
        
        # ===== 1. 配置管理 =====
        config_menu = menu.addMenu("配置管理")
        
        # 刷新配置
        refresh_action = QAction("刷新配置", self)
        refresh_action.setShortcut(QKeySequence("F5"))  # 设置快捷键
        refresh_action.triggered.connect(self.refresh_from_config)
        config_menu.addAction(refresh_action)
        
        # 编辑配置文件
        edit_config_action = QAction("编辑配置文件", self)
        edit_config_action.triggered.connect(lambda: self.toggle_view() if self.stacked_widget.currentIndex() == 0 else None)
        config_menu.addAction(edit_config_action)
        
        # 查看配置历史
        history_action = QAction("历史变更记录", self)
        history_action.triggered.connect(self.show_config_history)
        config_menu.addAction(history_action)
        
        config_menu.addSeparator()
        
        # 导入配置
        import_action = QAction("导入配置", self)
        import_action.triggered.connect(self.import_config)
        config_menu.addAction(import_action)
        
        # 导出配置
        export_action = QAction("导出配置", self)
        export_action.triggered.connect(self.export_config)
        config_menu.addAction(export_action)
        
        # ===== 2. 同步设置 =====
        sync_settings_action = QAction("同步设置", self)
        sync_settings_action.triggered.connect(self.show_sync_settings)
        menu.addAction(sync_settings_action)
        
        menu.addSeparator()
        
        # ===== 3. 应用设置 =====
        settings_menu = menu.addMenu("应用设置")
        
        # 窗口行为设置
        window_menu = settings_menu.addMenu("窗口行为")
        
        # 打开应用后自动关闭设置
        auto_close_action = QAction("打开应用后自动关闭窗口", self)
        auto_close_action.setCheckable(True)
        auto_close_action.setChecked(config.get("auto_close_after_launch", True))
        auto_close_action.triggered.connect(self.toggle_auto_close)
        window_menu.addAction(auto_close_action)
        
        # 启用/禁用最小化到托盘
        minimize_to_tray = config.get("minimize_to_tray", True)
        minimize_action = QAction("关闭窗口时最小化到托盘", self)
        minimize_action.setCheckable(True)
        minimize_action.setChecked(minimize_to_tray)
        minimize_action.triggered.connect(self.toggle_minimize_to_tray)
        window_menu.addAction(minimize_action)
        
        # 全局热键设置
        hotkey_menu = settings_menu.addMenu("全局热键")
        
        # 启用/禁用全局热键
        enable_hotkey = config.get("enable_hotkey", True)
        enable_hotkey_action = QAction("启用全局热键", self)
        enable_hotkey_action.setCheckable(True)
        enable_hotkey_action.setChecked(enable_hotkey)
        enable_hotkey_action.triggered.connect(self.toggle_enable_hotkey)
        hotkey_menu.addAction(enable_hotkey_action)
        
        # 设置全局热键
        set_hotkey_action = QAction("设置热键组合", self)
        set_hotkey_action.triggered.connect(self.set_global_hotkey)
        hotkey_menu.addAction(set_hotkey_action)
        
        menu.addSeparator()
        
        # ===== 4. 关于和退出 =====
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.force_quit)
        menu.addAction(exit_action)
        
        # 在按钮旁边显示菜单
        button = self.sender()
        if button:
            menu.exec_(button.mapToGlobal(QPoint(0, button.height())))
        else:
            menu.exec_(QCursor.pos())

    def refresh_from_config(self):
        """刷新并从配置文件重新加载数据"""
        try:
            # 显示加载遮罩
            self.loading_overlay.raise_()
            self.loading_overlay.show()
            
            # 使用QTimer延迟执行，让UI有时间刷新显示遮罩
            QTimer.singleShot(100, self._perform_refresh)
        except Exception as e:
            self.logger.error(f"启动刷新失败: {e}")
            self.loading_overlay.hide()
            QMessageBox.critical(self, "刷新失败", f"启动刷新时出错: {e}")

    def _perform_refresh(self):
        """执行实际的刷新操作"""
        # 异步加载配置，避免阻塞主线程
        self.load_config_async()
        
    def load_config_async(self):
        """异步加载配置"""
        # 创建加载线程
        self.config_loader = QThread()
        self.config_worker = ConfigLoader()
        self.config_worker.moveToThread(self.config_loader)
        
        # 连接信号
        self.config_loader.started.connect(self.config_worker.load)
        self.config_worker.config_loaded.connect(self.on_config_loaded)
        self.config_worker.finished.connect(self.config_loader.quit)
        self.config_worker.finished.connect(self.config_worker.deleteLater)
        self.config_loader.finished.connect(self.config_loader.deleteLater)
        
        # 启动线程
        self.config_loader.start()
        
    def on_config_loaded(self, config):
        """配置加载完成后的处理"""
        try:
            # 清空搜索框
            self.clear_search()
            
            # 在主线程中更新UI
            self.update_ui_with_config(config)
            
            # 隐藏加载遮罩
            self.loading_overlay.hide()
        except Exception as e:
            self.logger.error(f"刷新配置失败: {e}")
            self.loading_overlay.hide()
            QMessageBox.critical(self, "刷新失败", f"刷新配置时出错: {e}")

    def toggle_minimize_to_tray(self, checked):
        """切换最小化到托盘的设置"""
        try:
            config = self.get_cached_config()
            config["minimize_to_tray"] = checked
            save_config(config)
            # 配置更新后使缓存失效
            self.invalidate_config_cache()
            self.logger.debug(f"已更新最小化到托盘设置: {checked}")
        except Exception as e:
            self.logger.error(f"更新最小化到托盘设置失败: {e}")

    def toggle_enable_hotkey(self, checked):
        """切换启用全局热键的设置"""
        try:
            config = load_config()
            config["enable_hotkey"] = checked
            save_config(config)
            self.logger.debug(f"已更新启用全局热键设置: {checked}")
            
            # 显示提示信息，需要重启应用
            QMessageBox.information(self, "设置已更新", "全局热键设置已更新，需要重启应用才能生效。")
        except Exception as e:
            self.logger.error(f"更新启用全局热键设置失败: {e}")

    def set_global_hotkey(self):
        """设置全局热键"""
        try:
            config = load_config()
            current_hotkey = config.get("toggle_hotkey", "ctrl+shift+z")
            
            # 使用输入对话框获取新的热键设置
            new_hotkey, ok = QInputDialog.getText(
                self, "设置全局热键", 
                "请输入新的全局热键组合\n格式例如：ctrl+shift+z", 
                QLineEdit.Normal, 
                current_hotkey
            )
            
            if ok and new_hotkey:
                # 检查热键格式是否有效
                if "+" in new_hotkey:
                    config["toggle_hotkey"] = new_hotkey
                    save_config(config)
                    self.logger.debug(f"已更新全局热键设置: {new_hotkey}")
                    
                    # 显示提示信息，需要重启应用
                    QMessageBox.information(self, "设置已更新", "全局热键设置已更新，需要重启应用才能生效。")
                else:
                    QMessageBox.warning(self, "格式错误", "热键格式无效，请使用“+”号连接修饰键和主键，例如：ctrl+shift+z")
        except Exception as e:
            self.logger.error(f"设置全局热键失败: {e}")

    def force_quit(self):
        """强制退出应用"""
        # 保存窗口大小配置
        self.save_settings()
        
        # 退出应用
        QApplication.quit()

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于应用启动器", 
                         "应用启动器 v1.0\n\n"
                         "一个便捷的应用程序和网站启动工具，\n"
                         "支持 Windows 和 Mac 系统优化。\n\n"
                         "© 2023 YourCompany")

    def dragEnterEvent(self, event):
        """拖动进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """拖放事件"""
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            file_path = url.toLocalFile()
            
            if os.path.exists(file_path):
                # 获取文件名作为默认名称
                name = os.path.basename(file_path).split('.')[0]
                
                # 设置到输入框
                self.name_input.setText(name)
                self.app_input.setText(file_path)
                
                # 提示用户
                QMessageBox.information(self, "文件已添加", 
                                      f"已添加文件: {file_path}\n请点击'添加'按钮完成添加")

    def filter_items(self, text):
        """根据搜索文本过滤显示项目"""
        search_text = text.lower()
        
        # 重置当前选中索引
        self.current_selected_index = -1
        
        # 清除所有标签页中项目的选中状态
        for category, tab in self.tabs.items():
            for i in range(tab.content_layout.count()):
                widget = tab.content_layout.itemAt(i).widget()
                if widget and isinstance(widget, LaunchItem):
                    widget.set_selected(False)
        
        # 如果是在"全部"标签页中搜索
        current_tab = self.tab_widget.currentWidget()
        if current_tab and isinstance(current_tab, CategoryTab) and current_tab.category_name == "全部":
            # 直接在"全部"标签页中过滤
            for i in range(current_tab.content_layout.count()):
                widget = current_tab.content_layout.itemAt(i).widget()
                if widget and isinstance(widget, LaunchItem):
                    # 检查是否匹配搜索文本
                    if (search_text in widget.name.lower() or 
                        search_text in widget.app.lower() or 
                        any(search_text in param.lower() for param in widget.params) or
                        (hasattr(widget, 'source_category') and search_text in widget.source_category.lower())):
                        widget.setVisible(True)
                    else:
                        widget.setVisible(False)
            return
        
        # 其他标签页的搜索
        for category, tab in self.tabs.items():
            # 如果是"全部"分类，跳过，因为它会在最后更新
            if category == "全部":
                continue
            
            # 遍历标签页中的所有启动项
            for i in range(tab.content_layout.count()):
                widget = tab.content_layout.itemAt(i).widget()
                if widget and isinstance(widget, LaunchItem):
                    # 检查是否匹配搜索文本
                    if (search_text in widget.name.lower() or 
                        search_text in widget.app.lower() or 
                        any(search_text in param.lower() for param in widget.params)):
                        widget.setVisible(True)
                    else:
                        widget.setVisible(False)
        
        # 更新"全部"分类
        self.update_all_category()

    def update_all_category(self):
        """更新"全部"分类的内容"""
        if "全部" not in self.tabs:
            return
        
        all_tab = self.tabs["全部"]
        
        # 清空"全部"分类
        while all_tab.content_layout.count():
            widget = all_tab.content_layout.itemAt(0).widget()
            if widget:
                all_tab.content_layout.removeWidget(widget)
                widget.setParent(None)
        
        # 添加所有分类的启动项
        for category, tab in self.tabs.items():
            if category == "全部":
                continue
            
            for i in range(tab.content_layout.count()):
                widget = tab.content_layout.itemAt(i).widget()
                if widget and isinstance(widget, LaunchItem):
                    # 只添加可见的项目（如果有搜索过滤）
                    if self.search_input.text() and not widget.isVisible():
                        continue
                    
                    # 创建副本，添加所属分类信息
                    clone = LaunchItem(widget.name, widget.app, widget.params, category)
                    clone.set_category_tab(all_tab)
                    
                    # 设置右键菜单
                    clone.setContextMenuPolicy(Qt.CustomContextMenu)
                    clone.customContextMenuRequested.connect(
                        lambda pos, i=clone: all_tab.show_item_context_menu(pos, i)
                    )
                    
                    all_tab.content_layout.addWidget(clone)

    def update_all_category_from_config(self, config):
        """从配置直接加载全部分类的内容"""
        if "全部" not in self.tabs:
            return
        
        all_tab = self.tabs["全部"]
        
        # 清空"全部"分类
        while all_tab.content_layout.count():
            widget = all_tab.content_layout.itemAt(0).widget()
            if widget:
                all_tab.content_layout.removeWidget(widget)
                widget.setParent(None)
        
        # 直接从配置加载所有程序
        for program in config.get("programs", []):
            name = program.get("name", "")
            category = program.get("category", "娱乐")
            
            if not name:
                continue
            
            for launch_item in program.get("launch_items", []):
                app = launch_item.get("app", "")
                params = launch_item.get("params", [])
                
                if not app:
                    continue
                
                # 创建启动项，添加所属分类信息
                item = LaunchItem(name, app, params, category)
                item.set_category_tab(all_tab)
                
                # 设置右键菜单
                item.setContextMenuPolicy(Qt.CustomContextMenu)
                item.customContextMenuRequested.connect(
                    lambda pos, i=item: all_tab.show_item_context_menu(pos, i)
                )
                
                all_tab.content_layout.addWidget(item)

    def closeEvent(self, event):
        """重写关闭事件，实现最小化到托盘而不是关闭"""
        # 清空搜索框，确保下次打开时不会保留上次的搜索结果
        self.clear_search()
        
        # 保存设置
        self.save_settings()
        
        # 清理资源（仅在完全退出时）
        close_behavior = get_platform_setting('window_close_behavior')
        if close_behavior != 'hide' and close_behavior != 'minimize_to_tray':
            self.cleanup_resources()
        
        # 获取平台关闭窗口行为设置
        close_behavior = get_platform_setting('window_close_behavior')
        
        if close_behavior == 'hide':
            # macOS 风格：点击关闭按钮时只隐藏窗口，不关闭程序
            self.hide()
            event.ignore()
            return
        elif close_behavior == 'minimize_to_tray':
            # 托盘行为 - 根据配置决定
            if self.tray_icon and self.tray_icon.isVisible():
                # 使用缓存的配置，避免频繁文件I/O
                config = self.get_cached_config()
                if config.get("minimize_to_tray", True):
                    self.hide()
                    event.ignore()
                    return
        
        # 如果不是隐藏到托盘，则清理资源
        self.cleanup_resources()
        event.accept()
    
    def cleanup_resources(self):
        """清理所有资源"""
        try:
            # 刷新未保存的配置
            flush_config()
            
            # 停止所有定时器
            if hasattr(self, 'main_timer') and self.main_timer:
                self.main_timer.stop()
            if hasattr(self, 'config_update_timer') and self.config_update_timer:
                self.config_update_timer.stop()
            if hasattr(self, 'auto_sync_timer') and self.auto_sync_timer:
                self.auto_sync_timer.stop()
            
            # 取消正在进行的同步操作
            if hasattr(self, 'sync_worker') and self.sync_worker:
                self.sync_worker.cancel()
            
            # 清理配置加载器
            if hasattr(self, 'config_loader') and self.config_loader:
                self.config_loader.quit()
                
            self.logger.info("已清理所有资源")
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")

    def set_tray_icon(self, tray_icon):
        """设置系统托盘图标"""
        self.tray_icon = tray_icon
    
    def set_hotkey_manager(self, hotkey_manager):
        """设置热键管理器引用"""
        self.hotkey_manager = hotkey_manager

    def toggle_visibility(self):
        """切换主窗口显示/隐藏状态"""
        if self.isVisible():
            self.hide()
        else:
            # 优化窗口状态恢复逻辑
            # 首先确保窗口不是最小化状态
            if self.isMinimized():
                self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
            
            self.show()
            self.raise_()  # 将窗口提升到顶层
            self.activateWindow()  # 确保窗口激活
            
            # 使用缓存的平台检测结果，避免重复判断
            activate_method = self._platform_cache['activate_method']
            
            # 根据不同平台的激活方法执行特定操作
            if activate_method == 'windows_api' and self._platform_cache['is_windows']:
                # Windows平台特定处理：立即设置窗口为活动状态
                self.setWindowState(self.windowState() | Qt.WindowActive)
                # 强制将窗口带到前台
                self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
                self.show()
                self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
                self.show()
            elif activate_method == 'appkit' and self._platform_cache['is_mac']:
                # macOS平台特定处理
                # 使用AppKit将应用程序带到前台
                AppKit.NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            
            # 移除重复的焦点设置延迟，让showEvent处理焦点设置

    def get_cached_config(self):
        """获取缓存的配置，如果缓存过期则重新加载"""
        import time
        current_time = time.time()
        
        # 检查缓存是否有效
        if (self._config_cache is None or 
            current_time - self._config_cache_time > self._config_cache_timeout):
            
            # 缓存过期，重新加载
            from utils.config_manager import load_config
            self._config_cache = load_config()
            self._config_cache_time = current_time
            self.logger.debug("配置缓存已更新")
        
        return self._config_cache
    
    def invalidate_config_cache(self):
        """使配置缓存失效"""
        self._config_cache = None
        self._config_cache_time = 0
        self.logger.debug("配置缓存已失效")

    def focus_search_input(self):
        """将焦点设置到搜索输入框"""
        self.search_input.setFocus()
        self.search_input.selectAll()  # 全选当前文本，方便用户直接输入

    def get_window_handle(self):
        """获取窗口句柄"""
        if is_windows():
            # Windows 平台
            def callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        try:
                            proc = psutil.Process(pid)
                            # 获取进程可执行文件路径
                            exe = proc.exe()
                            # 获取窗口标题
                            title = win32gui.GetWindowText(hwnd)
                            # 将信息添加到列表
                            windows.append({
                                'hwnd': hwnd,
                                'title': title,
                                'exe': exe,
                                'pid': pid
                            })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    except Exception as e:
                        self.logger.error(f"获取窗口信息出错: {e}")
                return True
            
            # 获取所有窗口信息
            windows = []
            win32gui.EnumWindows(callback, windows)
            
            # 过滤掉不需要的窗口
            filtered_windows = [w for w in windows if w['title'] and w['exe']]
            
            # 如果没有找到任何窗口，显示提示
            if not filtered_windows:
                QMessageBox.information(self, "提示", "未找到任何可用窗口")
                return
            
            # 创建窗口选择对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("选择窗口")
            dialog.setMinimumSize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # 添加搜索框
            search_layout = QHBoxLayout()
            search_layout.addWidget(QLabel("搜索:"))
            search_input = QLineEdit()
            search_input.setPlaceholderText("输入关键词筛选窗口...")
            search_layout.addWidget(search_input)
            layout.addLayout(search_layout)
            
            # 添加窗口列表
            window_list = QListWidget()
            layout.addWidget(window_list)
            
            # 添加确定和取消按钮
            button_layout = QHBoxLayout()
            ok_button = QPushButton("确定")
            cancel_button = QPushButton("取消")
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            # 定义筛选函数
            def filter_windows(text):
                window_list.clear()
                for window in filtered_windows:
                    if text.lower() in window['title'].lower() or text.lower() in window['exe'].lower():
                        item = QListWidgetItem(f"{window['title']} - {window['exe']}")
                        item.setData(Qt.UserRole, window)
                        window_list.addItem(item)
            
            # 连接搜索框信号
            search_input.textChanged.connect(filter_windows)
            
            # 初始加载所有窗口
            filter_windows("")
            
            # 处理按钮点击
            selected_window = [None]
            
            def on_ok():
                # 获取选中的窗口
                selected_items = window_list.selectedItems()
                if selected_items:
                    selected_window[0] = selected_items[0].data(Qt.UserRole)
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "警告", "请选择一个窗口")
            
            def on_cancel():
                dialog.reject()
            
            ok_button.clicked.connect(on_ok)
            cancel_button.clicked.connect(on_cancel)
            
            # 显示对话框
            if dialog.exec_() == QDialog.Accepted and selected_window[0]:
                window = selected_window[0]
                # 设置应用路径
                self.app_input.setText(window['exe'])
                # 设置应用名称（从路径中提取）
                app_name = os.path.basename(window['exe'])
                if '.' in app_name:
                    app_name = app_name.split('.')[0]
                self.name_input.setText(app_name)
                
        elif is_mac():
            # macOS 平台
            # 获取当前运行的应用列表
            running_apps = []
            workspace = AppKit.NSWorkspace.sharedWorkspace()
            for app in workspace.runningApplications():
                if app.isActive() and app.bundleIdentifier():
                    app_name = app.localizedName()
                    bundle_url = app.bundleURL()
                    bundle_path = bundle_url.path() if bundle_url else ""
                    pid = app.processIdentifier()
                    
                    # 尝试获取可执行文件路径
                    exe_path = bundle_path
                    if bundle_path.endswith('.app'):
                        # 添加标准的 macOS 可执行文件路径
                        app_name_no_space = app_name.replace(' ', '')
                        exe_path = os.path.join(bundle_path, 'Contents/MacOS', app_name_no_space)
                    
                    if app_name and bundle_path:
                        running_apps.append({
                            'title': app_name,
                            'exe': exe_path,
                            'bundle_path': bundle_path,
                            'pid': pid
                        })
            
            # 如果没有找到任何应用，显示提示
            if not running_apps:
                QMessageBox.information(self, "提示", "未找到任何运行中的应用")
                return
            
            # 创建应用选择对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("选择应用")
            dialog.setMinimumSize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # 添加搜索框
            search_layout = QHBoxLayout()
            search_layout.addWidget(QLabel("搜索:"))
            search_input = QLineEdit()
            search_input.setPlaceholderText("输入关键词筛选应用...")
            search_layout.addWidget(search_input)
            layout.addLayout(search_layout)
            
            # 添加应用列表
            app_list = QListWidget()
            layout.addWidget(app_list)
            
            # 添加确定和取消按钮
            button_layout = QHBoxLayout()
            ok_button = QPushButton("确定")
            cancel_button = QPushButton("取消")
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            # 定义筛选函数
            def filter_apps(text):
                app_list.clear()
                for app in running_apps:
                    if text.lower() in app['title'].lower() or text.lower() in app['bundle_path'].lower():
                        item = QListWidgetItem(f"{app['title']} - {app['bundle_path']}")
                        item.setData(Qt.UserRole, app)
                        app_list.addItem(item)
            
            # 连接搜索框信号
            search_input.textChanged.connect(filter_apps)
            
            # 初始加载所有应用
            filter_apps("")
            
            # 处理按钮点击
            selected_app = [None]
            
            def on_ok():
                # 获取选中的应用
                selected_items = app_list.selectedItems()
                if selected_items:
                    selected_app[0] = selected_items[0].data(Qt.UserRole)
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "警告", "请选择一个应用")
            
            def on_cancel():
                dialog.reject()
            
            ok_button.clicked.connect(on_ok)
            cancel_button.clicked.connect(on_cancel)
            
            # 显示对话框
            if dialog.exec_() == QDialog.Accepted and selected_app[0]:
                app = selected_app[0]
                # 设置应用路径
                self.app_input.setText(app['exe'])
                # 设置应用名称
                self.name_input.setText(app['title'])
        else:
            # Linux 平台 (未实现)
            QMessageBox.information(self, "提示", "在当前平台上不支持此功能")

    def show_item_context_menu(self, pos, item):
        """显示启动项右键菜单"""
        menu = QMenu()
        
        # 添加菜单项
        run_action = menu.addAction("运行")
        edit_action = menu.addAction("编辑")
        
        delete_action = menu.addAction("删除")
        
        # 添加复制名称、应用路径和参数的选项
        copy_name_action = menu.addAction("复制名称")
        copy_app_action = menu.addAction("复制应用路径")
        copy_params_action = menu.addAction("复制参数")
        
        # 添加移动到子菜单
        move_menu = menu.addMenu("移动到")
        
        # 连接信号
        run_action.triggered.connect(lambda: item.launch())
        edit_action.triggered.connect(lambda: self.edit_item(item))
        
        delete_action.triggered.connect(lambda: self.delete_item(item))
        
        # ... 其余代码 ... 

    def find_item_original_category(self, item):
        """查找项目所在的原始分类（非"全部"分类）"""
        for category, tab in self.tabs.items():
            if category != "全部":
                # 检查项目是否在这个分类中
                for i in range(tab.content_layout.count()):
                    widget = tab.content_layout.itemAt(i).widget()
                    if widget and widget.name == item.name and widget.app == item.app:
                        # 参数比较
                        if (widget.params is None and item.params is None) or \
                           (widget.params == item.params):
                            return category
        return None

    def update_category(self, category):
        """更新指定分类的内容"""
        if category not in self.tabs:
            return
        
        # 这里可以添加特定分类的更新逻辑
        # 例如重新加载该分类的项目等
        
        # 更新配置
        self.update_config_debounced() 

    def export_config(self):
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "", "JSON文件 (*.json)"
        )
        if file_path:
            try:
                # 获取当前配置
                config = load_config()
                
                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "导出成功", f"配置已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出配置时出错: {e}")
    
    def import_config(self):
        """导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON文件 (*.json)"
        )
        if file_path:
            try:
                # 读取文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 保存配置
                save_config(config)
                
                # 保存历史记录
                self.history_manager.save_history(config, f"从文件导入配置: {os.path.basename(file_path)}")
                
                # 重新加载配置
                self.load_config()
                
                QMessageBox.information(self, "导入成功", "配置已导入并应用")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"导入配置时出错: {e}")

    def clear_search(self):
        """清空搜索框并重置过滤"""
        self.search_input.clear()
        self.search_input.setFocus()
        # 重置当前选中索引
        self.current_selected_index = -1
        
        # 清除所有标签页中的选中状态
        for category, tab in self.tabs.items():
            for i in range(tab.content_layout.count()):
                widget = tab.content_layout.itemAt(i).widget()
                if widget and isinstance(widget, LaunchItem):
                    widget.set_selected(False)

    def hide_and_clear_search(self):
        """隐藏窗口并清空搜索框"""
        self.clear_search()
        self.hide()

    def focus_search(self):
        """将焦点设置到搜索输入框"""
        if hasattr(self, 'search_input'):
            # 清除当前选中
            current_tab = self.tab_widget.currentWidget()
            if current_tab and isinstance(current_tab, CategoryTab):
                visible_items = []
                for i in range(current_tab.content_layout.count()):
                    widget = current_tab.content_layout.itemAt(i).widget()
                    if widget and isinstance(widget, LaunchItem) and widget.isVisible():
                        if widget.is_selected:
                            widget.set_selected(False)
                            
            # 重置选中索引
            self.current_selected_index = -1
            self.search_input.setFocus()
            
    def keyPressEvent(self, event):
        """处理主窗口的键盘事件"""
        if event.key() == Qt.Key_Down and self.search_input.hasFocus():
            self.navigate_down()
            event.accept()
        elif event.key() == Qt.Key_Escape:
            self.hide_and_clear_search()
            event.accept()
        else:
            super().keyPressEvent(event)

    def navigate_down(self):
        """向下导航到列表第一项"""
        current_tab = self.tab_widget.currentWidget()
        if not current_tab or not isinstance(current_tab, CategoryTab):
            return
            
        # 获取可见项目
        visible_items = []
        for i in range(current_tab.content_layout.count()):
            widget = current_tab.content_layout.itemAt(i).widget()
            if widget and isinstance(widget, LaunchItem) and widget.isVisible():
                visible_items.append(widget)
                
        if visible_items:
            # 清除当前选中状态
            if self.current_selected_index >= 0 and self.current_selected_index < len(visible_items):
                visible_items[self.current_selected_index].set_selected(False)
                
            # 选中第一项
            self.current_selected_index = 0
            visible_items[0].set_selected(True)
            visible_items[0].setFocus()
            
            # 确保可见
            current_tab.scroll_area.ensureWidgetVisible(visible_items[0])
            
    def eventFilter(self, obj, event):
        """事件过滤器，用于处理键盘导航"""
        if event.type() == QEvent.KeyPress:
            current_tab = self.tab_widget.currentWidget()
            
            # 检查当前标签页是否有效且是CategoryTab类型
            if not current_tab or not isinstance(current_tab, CategoryTab):
                return super().eventFilter(obj, event)
            
            # 计算当前标签页中可见的项目数量
            visible_items = []
            for i in range(current_tab.content_layout.count()):
                widget = current_tab.content_layout.itemAt(i).widget()
                if widget and isinstance(widget, LaunchItem) and widget.isVisible():
                    visible_items.append(widget)
            
            # 如果没有可见项目，默认处理
            if not visible_items:
                return super().eventFilter(obj, event)
            
            # 打印调试信息
            self.logger.debug(f"键盘事件：{event.key()}, 当前选中索引: {self.current_selected_index}, 当前焦点对象: {obj}")
            
            # 处理上下键导航
            if event.key() == Qt.Key_Down:
                # 搜索框处理下键 - 进入列表第一项
                if self.search_input.hasFocus():
                    self.logger.debug("搜索框按下键")
                    if visible_items:
                        self.current_selected_index = 0
                        visible_items[0].set_selected(True)
                        visible_items[0].setFocus()
                        # 确保选中的项目可见
                        current_tab.scroll_area.ensureWidgetVisible(visible_items[0])
                        return True
                # 列表项处理下键 - 选择下一项
                elif self.current_selected_index >= 0 and self.current_selected_index < len(visible_items) - 1:
                    self.logger.debug(f"列表从 {self.current_selected_index} 到 {self.current_selected_index + 1}")
                    if self.current_selected_index >= 0:
                        visible_items[self.current_selected_index].set_selected(False)
                    self.current_selected_index += 1
                    visible_items[self.current_selected_index].set_selected(True)
                    visible_items[self.current_selected_index].setFocus()
                    # 确保选中的项目可见
                    current_tab.scroll_area.ensureWidgetVisible(visible_items[self.current_selected_index])
                    return True
            
            elif event.key() == Qt.Key_Up:
                # 列表项处理上键 - 选择上一项
                if self.current_selected_index > 0:
                    self.logger.debug(f"列表从 {self.current_selected_index} 到 {self.current_selected_index - 1}")
                    visible_items[self.current_selected_index].set_selected(False)
                    self.current_selected_index -= 1
                    visible_items[self.current_selected_index].set_selected(True)
                    visible_items[self.current_selected_index].setFocus()
                    # 确保选中的项目可见
                    current_tab.scroll_area.ensureWidgetVisible(visible_items[self.current_selected_index])
                    return True
                # 如果是第一个项目，回到搜索框
                elif self.current_selected_index == 0:
                    self.logger.debug("从第一个项目回到搜索框")
                    visible_items[0].set_selected(False)
                    self.current_selected_index = -1
                    self.search_input.setFocus()
                    return True
            
            elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                # 处理回车键
                if self.search_input.hasFocus():
                    # 如果焦点在搜索框上且有可见项目，选中第一个项目
                    if visible_items:
                        self.logger.debug("搜索框按回车，选中第一项")
                        self.current_selected_index = 0
                        visible_items[0].set_selected(True)
                        visible_items[0].setFocus()
                    return True
                # 如果焦点在可见项目上，启动该项目
                elif self.current_selected_index >= 0 and self.current_selected_index < len(visible_items):
                    # 获取当前选中的项目
                    self.logger.debug(f"项目 {self.current_selected_index} 按回车，启动应用")
                    selected_item = visible_items[self.current_selected_index]
                    
                    # 启动应用
                    selected_item.launch()

                    # 清空搜索框
                    self.clear_search()
                    
                    # 如果勾选了自动关闭选项，关闭窗口
                    config = load_config()
                    if config.get("auto_close_after_launch", True):
                        self.hide()
                    
                    return True
        
        # 键盘事件来自列表项目处理
        elif event.type() == QEvent.ShortcutOverride:
            if isinstance(obj, LaunchItem) and (event.key() == Qt.Key_Up or event.key() == Qt.Key_Down):
                # 强制应用程序层面处理上下键
                event.accept()
                return True
        
        # 默认处理
        return super().eventFilter(obj, event)

    def save_settings(self):
        """保存所有设置"""
        config = load_config()
        
        # 获取设备窗口大小字典
        device_window_sizes = config.get("device_window_sizes", {})
        
        # 更新当前设备的窗口大小
        device_window_sizes[self.device_id] = {
            "width": self.width(),
            "height": self.height()
        }
        
        # 保存回配置
        config["device_window_sizes"] = device_window_sizes
        
        # 保留向后兼容的设置
        config["window_size"] = {
            "width": self.width(),
            "height": self.height()
        }
        
        save_config(config)

    def handle_search_return(self):
        """处理搜索框回车键"""
        self.navigate_down()  # 导航到第一个项目

    def toggle_auto_close(self, state):
        """切换打开应用后自动关闭窗口的设置"""
        config = load_config()
        config["auto_close_after_launch"] = state
        save_config(config)

    def show_sync_settings(self):
        """显示同步设置对话框"""
        try:
            dialog = SyncSettingsDialog(self)
            if dialog.exec_():
                # 如果对话框被接受，可能需要刷新配置
                pass
        except Exception as e:
            self.logger.error(f"显示同步设置对话框时出错: {e}")
            QMessageBox.critical(self, "错误", f"显示同步设置对话框时出错: {e}")

    def upload_to_github(self):
        """上传配置到所有启用的同步服务（异步）"""
        try:
            # 创建线程和Worker
            self.upload_thread = QThread()
            self.upload_worker = SyncWorker("upload")
            self.upload_worker.moveToThread(self.upload_thread)
            
            # 连接信号
            self.upload_thread.started.connect(self.upload_worker.run)
            self.upload_worker.finished.connect(self.upload_completed)
            self.upload_worker.finished.connect(self.upload_thread.quit)
            self.upload_worker.finished.connect(self.upload_worker.deleteLater)
            self.upload_thread.finished.connect(self.upload_thread.deleteLater)
            
            # 开始加载动画并启动线程
            self.upload_button.start_loading()
            self.upload_thread.start()
        except Exception as e:
            self.logger.error(f"上传配置时出错: {e}")
            self.upload_button.stop_loading()
            QMessageBox.critical(self, "上传失败", f"上传配置时出错: {e}")

    def download_from_github(self):
        """从所有启用的同步服务下载配置（异步）"""
        try:
            # 确认是否要覆盖本地配置
            confirm = QMessageBox.question(
                self, "确认下载", 
                "从同步服务下载配置将覆盖本地配置，是否继续？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                # 创建线程和Worker
                self.download_thread = QThread()
                self.download_worker = SyncWorker("download")
                self.download_worker.moveToThread(self.download_thread)
                
                # 连接信号
                self.download_thread.started.connect(self.download_worker.run)
                self.download_worker.finished.connect(self.download_completed)
                self.download_worker.finished.connect(self.download_thread.quit)
                self.download_worker.finished.connect(self.download_worker.deleteLater)
                self.download_thread.finished.connect(self.download_thread.deleteLater)
                
                # 开始加载动画并启动线程
                self.download_button.start_loading()
                self.download_thread.start()
        except Exception as e:
            self.logger.error(f"下载配置时出错: {e}")
            self.download_button.stop_loading()
            QMessageBox.critical(self, "下载失败", f"下载配置时出错: {e}")

    def download_completed(self, success, message, config_data):
        """下载完成后的处理"""
        # 停止加载动画
        self.download_button.stop_loading()
        
        # 处理结果
        if success and config_data:
            # 保存配置
            from utils.config_manager import save_config
            save_config(config_data)
            
            # 保存历史记录
            self.history_manager.save_history(config_data, "从同步服务下载配置")
            
            # 重新加载配置
            self.load_config()
            # 更新统计信息
            self.update_statistics()
            QMessageBox.information(self, "下载成功", f"{message}，配置已应用")
        else:
            QMessageBox.warning(self, "下载失败", message)

    def check_auto_sync(self):
        """检查是否需要自动同步配置（下载）"""
        try:
            # 如果窗口可见，跳过同步
            if self.isVisible():
                self.logger.debug("窗口可见，跳过自动同步")
                return
                
            self.logger.debug("执行定时自动同步检查")
            # 获取所有启用的自动同步服务
            enabled_auto_sync_services = []
            
            # 检查GitHub Gist
            github_manager = GistManager()
            if github_manager.enabled and github_manager.auto_sync:
                enabled_auto_sync_services.append(("GitHub Gist", github_manager))
            
            # 检查Open Gist
            open_gist_manager = OpenGistManager()
            if open_gist_manager.enabled and open_gist_manager.auto_sync:
                enabled_auto_sync_services.append(("Open Gist", open_gist_manager))
                
            # 检查WebDAV
            webdav_manager = WebDAVManager()
            if webdav_manager.enabled and webdav_manager.auto_sync:
                enabled_auto_sync_services.append(("WebDAV", webdav_manager))
            
            # 如果没有启用的自动同步服务，返回
            if not enabled_auto_sync_services:
                self.logger.debug("没有启用的自动同步服务，跳过自动下载")
                return
            
            # 创建线程和Worker进行下载
            self.auto_download_thread = QThread()
            self.auto_download_worker = SyncWorker("download")
            self.auto_download_worker.moveToThread(self.auto_download_thread)
            
            # 连接信号
            self.auto_download_thread.started.connect(self.auto_download_worker.run)
            self.auto_download_worker.finished.connect(self.auto_sync_completed)
            self.auto_download_worker.finished.connect(self.auto_download_thread.quit)
            self.auto_download_worker.finished.connect(self.auto_download_worker.deleteLater)
            self.auto_download_thread.finished.connect(self.auto_download_thread.deleteLater)
            
            # 启动线程
            self.auto_download_thread.start()
            self.logger.debug("已启动自动下载配置")
            
        except Exception as e:
            self.logger.error(f"自动同步配置时出错: {e}")

    def auto_sync_completed(self, success, message, config_data):
        """自动同步完成后的处理"""
        try:
            if success and config_data:
                # 保存配置
                from utils.config_manager import save_config
                save_config(config_data)
                
                # 保存历史记录
                self.history_manager.save_history(config_data, "自动同步配置")
                
                # 重新加载配置
                self.load_config()
                # 更新统计信息
                self.update_statistics()
                self.logger.info("已自动从同步服务同步配置")
            else:
                self.logger.warning(f"自动同步配置失败: {message}")
        except Exception as e:
            self.logger.error(f"处理自动同步结果时出错: {e}")

    def toggle_view(self):
        """切换视图"""
        current_index = self.stacked_widget.currentIndex()
        
        # 显示加载遮罩
        self.loading_overlay.raise_()
        self.loading_overlay.show()
        
        # 使用QTimer延迟执行，让UI有时间刷新显示遮罩
        QTimer.singleShot(100, lambda: self._perform_view_toggle(current_index))
    
    def _perform_view_toggle(self, current_index):
        """执行实际的视图切换操作"""
        try:
            if current_index == 0:
                # 当前是操作视图，切换到配置文件视图
                # 先更新配置文件内容
                self.load_config_to_editor()
                self.stacked_widget.setCurrentIndex(1)
                self.switch_view_button.setText("返回启动界面")
            else:
                # 当前是配置文件视图，切换到操作视图
                # 确保配置已保存且格式正确
                try:
                    # 如果定时器正在运行，说明有未保存的更改
                    if self.auto_save_timer.isActive():
                        self.auto_save_timer.stop()
                        # 立即执行保存
                        if not self.save_config_from_editor():
                            # 保存失败，隐藏遮罩并返回
                            self.loading_overlay.hide()
                            return
                        
                    # 进行额外的配置格式验证
                    config_text = self.config_editor.toPlainText()
                    json.loads(config_text)  # 尝试解析，验证格式
                    
                    # 切换到操作视图
                    self.stacked_widget.setCurrentIndex(0)
                    self.switch_view_button.setText("编辑配置文件")
                    # 刷新操作视图
                    self.refresh_from_config()
                except json.JSONDecodeError as e:
                    # JSON格式错误，不切换视图
                    line_no = e.lineno
                    col_no = e.colno
                    error_msg = f"JSON格式错误: 第 {line_no} 行, 第 {col_no} 列\n{e.msg}"
                    QMessageBox.critical(self, "格式错误", error_msg)
                    # 将光标放在出错位置
                    cursor = self.config_editor.textCursor()
                    cursor.setPosition(0)
                    for _ in range(line_no - 1):
                        cursor.movePosition(cursor.Down)
                    for _ in range(col_no - 1):
                        cursor.movePosition(cursor.Right)
                    self.config_editor.setTextCursor(cursor)
                    self.config_editor.setFocus()
                except Exception as e:
                    QMessageBox.critical(self, "切换失败", f"切换视图失败: {str(e)}\n请检查配置格式。")
        finally:
            # 不管成功还是失败，最后都要隐藏遮罩
            # 延迟一小段时间，让视图有时间刷新和渲染
            QTimer.singleShot(300, self.loading_overlay.hide)

    def load_config_to_editor(self):
        """加载配置到编辑器"""
        try:
            config = load_config()
            self.config_editor.setPlainText(json.dumps(config, ensure_ascii=False, indent=4))
        except Exception as e:
            self.logger.error(f"加载配置到编辑器失败: {e}")
            QMessageBox.critical(self, "加载失败", f"加载配置到编辑器失败: {e}")

    def save_config_from_editor(self):
        """从编辑器保存配置"""
        try:
            config_text = self.config_editor.toPlainText()
            config = json.loads(config_text)
            save_config(config)
            # 更新状态标签
            self.config_status_label.setText("已保存")
            self.config_status_label.setStyleSheet("color: green;")
            
            # 保存历史记录
            self.history_manager.save_history(config, "编辑器更新配置")
            
            # 更新统计信息
            self.update_statistics()
            
            # 添加自动上传功能
            self.auto_upload_config()
            
            return True
        except json.JSONDecodeError as e:
            line_no = e.lineno
            col_no = e.colno
            error_msg = f"JSON格式错误: 第 {line_no} 行, 第 {col_no} 列\n{e.msg}"
            self.config_status_label.setText("保存失败 - JSON格式错误")
            self.config_status_label.setStyleSheet("color: red;")
            # 将光标放在出错位置
            cursor = self.config_editor.textCursor()
            cursor.setPosition(0)
            for _ in range(line_no - 1):
                cursor.movePosition(cursor.Down)
            for _ in range(col_no - 1):
                cursor.movePosition(cursor.Right)
            self.config_editor.setTextCursor(cursor)
            self.config_editor.setFocus()
            return False
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            self.config_status_label.setText(f"保存失败 - {str(e)}")
            self.config_status_label.setStyleSheet("color: red;")
            return False

    def auto_upload_config(self):
        """配置修改后自动上传配置"""
        try:
            self.logger.debug("开始自动上传配置")

            # 获取所有启用了自动同步的服务
            enabled_auto_sync_services = []
            
            # 检查GitHub Gist
            github_manager = GistManager()
            if github_manager.enabled and github_manager.auto_sync:
                enabled_auto_sync_services.append(("GitHub Gist", github_manager))
            
            # 检查Open Gist
            open_gist_manager = OpenGistManager()
            if open_gist_manager.enabled and open_gist_manager.auto_sync:
                enabled_auto_sync_services.append(("Open Gist", open_gist_manager))
                
            # 检查WebDAV
            webdav_manager = WebDAVManager()
            if webdav_manager.enabled and webdav_manager.auto_sync:
                enabled_auto_sync_services.append(("WebDAV", webdav_manager))
                
            # 如果没有启用的自动同步服务，直接返回
            if not enabled_auto_sync_services:
                self.logger.debug("没有启用的自动同步服务，跳过自动上传")
                return
            
            # 创建线程和Worker进行上传
            self.auto_upload_thread = QThread()
            self.auto_upload_worker = SyncWorker("upload")
            self.auto_upload_worker.moveToThread(self.auto_upload_thread)
            
            # 连接信号
            self.auto_upload_thread.started.connect(self.auto_upload_worker.run)
            self.auto_upload_worker.finished.connect(self.auto_upload_completed)
            self.auto_upload_worker.finished.connect(self.auto_upload_thread.quit)
            self.auto_upload_worker.finished.connect(self.auto_upload_worker.deleteLater)
            self.auto_upload_thread.finished.connect(self.auto_upload_thread.deleteLater)
            
            # 启动线程
            self.auto_upload_thread.start()
            self.logger.debug("已启动自动上传配置")
            
        except Exception as e:
            self.logger.error(f"自动上传配置时出错: {e}")
    
    def auto_upload_completed(self, success, message, _):
        """自动上传完成后的处理"""
        try:
            if success:
                self.logger.info("自动上传配置成功")
                # 更新状态标签但不打扰用户
                self.config_status_label.setText("已保存并上传")
                self.config_status_label.setStyleSheet("color: green;")
            else:
                self.logger.warning(f"自动上传配置失败: {message}")
        except Exception as e:
            self.logger.error(f"处理自动上传结果时出错: {e}")

    def on_config_text_changed(self):
        """处理配置文本变化"""
        # 显示正在编辑状态
        self.config_status_label.setText("编辑中...")
        self.config_status_label.setStyleSheet("color: orange;")
        # 重置定时器，1秒后自动保存
        self.auto_save_timer.start()

    def search_in_config(self, direction="next"):
        """搜索配置文件内容"""
        # 获取搜索文本
        search_text = self.config_search_input.text()
        if not search_text:
            return
            
        # 获取当前光标位置和整个文本
        cursor = self.config_editor.textCursor()
        document = self.config_editor.document()
        
        # 创建查找选项
        find_flags = QTextDocument.FindFlags()
        
        # 如果是向上搜索，添加向上搜索标志
        if direction == "prev":
            find_flags |= QTextDocument.FindBackward
            
        # 从当前位置开始搜索
        if cursor.hasSelection():
            # 如果有选择，则从选择的开始或结束位置开始搜索
            if direction == "prev":
                # 向上搜索，从选择的开始位置搜索
                cursor.setPosition(cursor.selectionStart())
            else:
                # 向下搜索，从选择的结束位置搜索
                cursor.setPosition(cursor.selectionEnd())
                
        # 执行搜索
        result_cursor = document.find(search_text, cursor, find_flags)
        
        # 如果没有找到结果，从文档开始或结束处再次搜索
        if result_cursor.isNull():
            # 创建一个新光标
            new_cursor = QTextCursor(document)
            
            if direction == "prev":
                # 从文档末尾开始向上搜索
                new_cursor.movePosition(QTextCursor.End)
            else:
                # 从文档开始处向下搜索
                new_cursor.movePosition(QTextCursor.Start)
                
            # 再次查找
            result_cursor = document.find(search_text, new_cursor, find_flags)
            
            # 如果还是没找到，显示提示
            if result_cursor.isNull():
                self.config_status_label.setText(f"未找到: {search_text}")
                self.config_status_label.setStyleSheet("color: red;")
                return
                
        # 设置编辑器光标为搜索结果并选择文本
        self.config_editor.setTextCursor(result_cursor)
        
        # 确保光标可见
        self.config_editor.ensureCursorVisible()
        
        # 更新状态标签
        self.config_status_label.setText(f"已找到: {search_text}")
        self.config_status_label.setStyleSheet("color: green;")

    def focus_config_search(self):
        """将焦点设置到配置搜索框"""
        # 只有当前是配置视图时才设置焦点
        if self.stacked_widget.currentIndex() == 1:
            self.config_search_input.setFocus()
            self.config_search_input.selectAll()  # 全选当前文本，方便用户直接输入

    def upload_completed(self, success, message, _):
        """上传完成后的处理"""
        # 停止加载动画
        self.upload_button.stop_loading()
        
        # 显示结果
        if success:
            QMessageBox.information(self, "上传成功", message)
        else:
            QMessageBox.warning(self, "上传失败", message)

    def showEvent(self, event):
        """重写显示事件，用于在显示窗口时执行操作"""
        super().showEvent(event)
        
        # 暂停热键检测在窗口恢复期间，减少CPU竞争
        if self.hotkey_manager and hasattr(self.hotkey_manager, 'pause_checking'):
            self.hotkey_manager.pause_checking()
            # 300ms后恢复热键检测，给窗口足够时间完成恢复
            QTimer.singleShot(300, lambda: (
                self.hotkey_manager.resume_checking() 
                if self.hotkey_manager and hasattr(self.hotkey_manager, 'resume_checking') 
                else None
            ))
        
        # 优化自动同步定时器启停：避免重复操作
        if hasattr(self, 'auto_sync_timer') and self.auto_sync_timer.isActive():
            self.logger.debug("窗口显示，停止自动同步定时器")
            self.auto_sync_timer.stop()
        
        # 优化焦点设置：减少延迟并只在窗口真正可见时设置
        if self.isVisible() and not self.isMinimized():
            QTimer.singleShot(50, self.focus_search_input)  # 减少延迟从100ms到50ms
        
    def hideEvent(self, event):
        """重写隐藏事件，用于在窗口隐藏时执行操作"""
        super().hideEvent(event)
        
        # 优化自动同步定时器启停：延迟启动，避免快速显示/隐藏时的频繁切换
        if hasattr(self, 'auto_sync_timer') and not self.auto_sync_timer.isActive():
            # 延迟1秒启动同步定时器，避免快速切换时的性能损失
            QTimer.singleShot(1000, self._start_auto_sync_timer)
    
    def _start_auto_sync_timer(self):
        """延迟启动自动同步定时器"""
        # 只有在窗口真正隐藏时才启动定时器
        if (hasattr(self, 'auto_sync_timer') and 
            not self.auto_sync_timer.isActive() and 
            not self.isVisible()):
            self.logger.debug("窗口隐藏，启动自动同步定时器")
            self.auto_sync_timer.start()

    def update_statistics(self):
        """更新统计信息"""
        try:
            # 加载配置
            config = load_config()
            
            # 计算启动项总数
            total_launch_items = 0
            for program in config.get("programs", []):
                total_launch_items += len(program.get("launch_items", []))
            
            # 获取分类总数
            total_categories = len(config.get("categories", []))
            if "全部" in config.get("categories", []):
                total_categories -= 1  # 排除"全部"分类
            
            
            # 更新统计标签
            stats_text = f"启动项: {total_launch_items} | 分类: {total_categories}"
            self.stats_label.setText(stats_text)
        except Exception as e:
            self.logger.error(f"更新统计信息失败: {e}")
            self.stats_label.setText("统计信息加载失败")

    def show_config_history(self):
        """显示历史变更记录对话框"""
        try:
            dialog = ConfigHistoryDialog(self)
            dialog.exec_()
        except Exception as e:
            self.logger.error(f"显示历史变更记录对话框时出错: {e}")
            QMessageBox.critical(self, "错误", f"显示历史变更记录对话框时出错: {e}")
