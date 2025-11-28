#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
import math
import time
import copy
import psutil
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QTabWidget, QFileDialog, QInputDialog, QMenu,
                            QAction, QMessageBox, QDialog, QListWidget, QListWidgetItem,
                            QSystemTrayIcon, QApplication, QCheckBox)
from PyQt5.QtCore import Qt, QPoint, QTimer, QThread, pyqtSignal, QObject, QRegExp
from PyQt5.QtGui import (QCursor, QIcon, QColor, QKeySequence, QMovie, QFont)
from PyQt5.QtCore import QEvent
from gui.category_tab import CategoryTab
from utils.config_manager import (load_config, save_config, flush_config, 
                                  get_available_tags, get_tag_filter_state, 
                                  update_tag_filter_state, filter_programs_by_tags,
                                  add_available_tag, is_launch_icon_enabled,
                                  set_launch_icon_enabled, get_icon_cache_capacity,
                                  set_icon_cache_capacity)
from gui.launch_item import LaunchItem
from utils.logger import get_logger
from utils.platform_settings import (get_platform_style, get_platform_setting, 
                                    is_windows, is_mac, is_linux)
from utils.gist_manager import GistManager
from utils.open_gist_manager import OpenGistManager
from utils.webdav_manager import WebDAVManager
from gui.sync_settings_dialog import SyncSettingsDialog
from gui.config_history_dialog import ConfigHistoryDialog
from utils.config_history import ConfigHistoryManager
from gui.tag_filter_compact import TagFilterCompact
from gui.tag_manager_dialog import TagManagerDialog
from gui.icon_loader import get_icon_loader

# 配置加载器类
class ConfigLoader(QObject):
    """异步配置加载器"""
    config_loaded = pyqtSignal(dict)  # 配置加载完成信号
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self._is_reloading_ui = False
    
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
        self.should_stop = False  # 中断标志
    
    def run(self):
        """执行同步操作"""
        try:
            # 检查是否应该停止
            if self.should_stop:
                self.logger.debug("同步操作被中断")
                self.finished.emit(False, "操作已中断", None)
                return
                
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
                    # 检查是否应该停止
                    if self.should_stop:
                        self.logger.debug(f"上传{service_name}时被中断")
                        break
                        
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
                    # 检查是否应该停止
                    if self.should_stop:
                        self.logger.debug(f"下载{service_name}时被中断")
                        break
                        
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
    import win32con
elif is_mac():
    # macOS 平台特定导入
    import AppKit
else:
    # Linux 平台特定导入
    pass

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
        # 后台刷新挂起状态
        self._pending_ui_refresh = False
        self._pending_config_snapshot = None
        self._pending_refresh_timestamp = 0
        self._pending_refresh_source = ""
        
        # 热键管理器引用（由主程序设置）
        self.hotkey_manager = None
        
        # 同步状态管理
        self._sync_in_progress = False
        self._sync_threads = []  # 跟踪活跃的同步线程
        
        # 配置版本管理（用于增量更新）
        self._config_hash = None
        self._last_update_time = 0
        
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
        
        # 创建操作视图小部件
        self.operation_widget = QWidget()
        operation_layout = QVBoxLayout(self.operation_widget)
        operation_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.operation_widget)
        
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
        
        # 创建紧凑型标签过滤器
        self.tag_filter_widget = TagFilterCompact()
        self.tag_filter_widget.filter_changed.connect(self.on_tag_filter_changed)
        operation_layout.addWidget(self.tag_filter_widget)
        
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
        
        # 创建底部统计信息布局
        stats_layout = QHBoxLayout()
        stats_layout.addStretch()
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.stats_label.setStyleSheet("color: #666666; font-size: 18px;")
        stats_layout.addWidget(self.stats_label)
        main_layout.addLayout(stats_layout)
        
        # 加载配置
        self.load_config()
        
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
        self.tabs[to_category].add_launch_item(item.name, item.app, item.params, item.tags)
        
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
        
        # 如果正在重新加载UI，忽略此次请求
        if self._is_reloading_ui:
            return
        
        # 获取当前标签页
        current_tab = self.tab_widget.currentWidget()
        target_tab = current_tab if isinstance(current_tab, CategoryTab) else None

        # "全部" 分类不允许直接添加项目，需要用户选择具体分类
        if target_tab and target_tab.category_name == "全部":
            categories = [c for c in self.tabs.keys() if c != "全部"]
            if not categories:
                QMessageBox.warning(self, "无法添加", "请先创建一个分类再添加启动项。")
                return
            category, ok = QInputDialog.getItem(
                self,
                "选择分类",
                "请选择要添加到的分类：",
                categories,
                0,
                False
            )
            if not ok or not category:
                return
            target_tab = self.tabs.get(category)

        if target_tab and isinstance(target_tab, CategoryTab):
            target_tab.add_launch_item(name, app, params, [])
        else:
            QMessageBox.warning(self, "无法添加", "请先选择一个有效的分类标签。")
            return
        
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
            self._is_reloading_ui = True
            import time
            import hashlib
            import json
            
            start_time = time.time()
            
            icon_enabled = is_launch_icon_enabled(config)
            LaunchItem.ICONS_ENABLED = icon_enabled
            icon_loader = get_icon_loader()
            icon_loader.set_enabled(icon_enabled)
            icon_loader.set_cache_capacity(get_icon_cache_capacity(config))
            
            # 计算配置的哈希值，用于检测变化
            config_str = json.dumps(config, sort_keys=True, ensure_ascii=False)
            current_hash = hashlib.md5(config_str.encode()).hexdigest()
            
            # 如果配置没有变化，跳过更新
            if self._config_hash == current_hash and time.time() - self._last_update_time < 1:
                self.logger.debug("配置未变化，跳过UI更新")
                self._is_reloading_ui = False
                return
            
            self.logger.debug(f"开始更新UI，配置哈希: {current_hash[:8]}")
            
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
                category_start = time.time()
                for category in categories:
                    self.add_category(category)
                category_end = time.time()
                self.logger.debug(f"创建 {len(categories)} 个分类耗时: {(category_end - category_start)*1000:.2f}ms")
                
                # 添加启动项
                item_start = time.time()
                item_count = 0
                batch_tabs = []
                for tab in self.tabs.values():
                    if hasattr(tab, 'begin_batch_update'):
                        tab.begin_batch_update()
                        batch_tabs.append(tab)
                for program in config.get("programs", []):
                    name = program.get("name", "")
                    category = program.get("category", "娱乐")
                    tags = program.get("tags", [])
                    
                    if not name or category not in self.tabs:
                        continue
                    
                    for launch_item in program.get("launch_items", []):
                        app = launch_item.get("app", "")
                        params = launch_item.get("params", [])
                        
                        if not app:
                            continue
                        
                        self.tabs[category].add_launch_item(name, app, params, tags, defer_refresh=True)
                        item_count += 1
                
                for tab in batch_tabs:
                    tab.end_batch_update(reset_to_first=True)
                
                item_end = time.time()
                self.logger.debug(f"添加 {item_count} 个启动项耗时: {(item_end - item_start)*1000:.2f}ms")
                
                # 更新"全部"分类 - 先加载所有程序（不过滤）
                all_start = time.time()
                self.update_all_category_from_config(config, apply_filter=False)
                all_end = time.time()
                self.logger.debug(f"更新全部分类耗时: {(all_end - all_start)*1000:.2f}ms")
                
            finally:
                self.tab_widget.setUpdatesEnabled(True)
            
            # 确保所有项目都安装了事件过滤器
            filter_start = time.time()
            self.install_event_filters_to_all_items()
            filter_end = time.time()
            self.logger.debug(f"安装事件过滤器耗时: {(filter_end - filter_start)*1000:.2f}ms")
            
            # 初始化标签过滤器
            tag_start = time.time()
            self.refresh_tag_filter()
            
            # 应用保存的标签过滤状态
            self.apply_tag_filter()
            tag_end = time.time()
            self.logger.debug(f"刷新标签过滤器耗时: {(tag_end - tag_start)*1000:.2f}ms")
            
            # 更新配置哈希和时间戳
            self._config_hash = current_hash
            self._last_update_time = time.time()
            
            # 更新统计信息
            self.update_statistics()
            
            # 记录总耗时
            end_time = time.time()
            self.logger.info(f"UI更新完成，总耗时: {(end_time - start_time)*1000:.2f}ms")
            
        except Exception as e:
            self.logger.error(f"更新UI失败: {e}")
            raise
    
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
        finally:
            self._is_reloading_ui = False
    
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
        
        # 使用系统默认编辑器打开配置文件
        external_edit_action = QAction("打开配置文件", self)
        external_edit_action.triggered.connect(self.open_config_in_system_editor)
        config_menu.addAction(external_edit_action)
        
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
        
        # ===== 标签管理 =====
        tag_management_action = QAction("标签管理", self)
        tag_management_action.triggered.connect(self.show_tag_manager)
        menu.addAction(tag_management_action)
        
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

        icon_menu = settings_menu.addMenu("图标")
        icons_enabled = is_launch_icon_enabled(config)
        icon_toggle_action = QAction("显示启动项图标", self)
        icon_toggle_action.setCheckable(True)
        icon_toggle_action.setChecked(icons_enabled)
        icon_toggle_action.triggered.connect(self.toggle_launch_icons)
        icon_menu.addAction(icon_toggle_action)

        cache_action = QAction("设置图标缓存大小", self)
        cache_action.triggered.connect(self.prompt_icon_cache_capacity)
        icon_menu.addAction(cache_action)
        
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
            import time
            start_time = time.time()
            self.logger.debug("开始刷新配置")
            
            # 显示加载遮罩
            self.loading_overlay.raise_()
            self.loading_overlay.show()
            
            # 使用QTimer延迟执行，让UI有时间刷新显示遮罩
            QTimer.singleShot(100, lambda: self._perform_refresh(start_time))
        except Exception as e:
            self.logger.error(f"启动刷新失败: {e}")
            self.loading_overlay.hide()
            QMessageBox.critical(self, "刷新失败", f"启动刷新时出错: {e}")

    def _perform_refresh(self, start_time=None):
        """执行实际的刷新操作"""
        if start_time:
            import time
            self.logger.debug(f"遮罩显示耗时: {(time.time() - start_time)*1000:.2f}ms")
        
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
            import time
            start_time = time.time()
            
            # 清空搜索框
            self.clear_search()
            
            # 在主线程中更新UI
            self.update_ui_with_config(config)
            
            # 隐藏加载遮罩
            self.loading_overlay.hide()
            
            # 记录总刷新耗时
            end_time = time.time()
            self.logger.info(f"配置刷新完成，总耗时: {(end_time - start_time)*1000:.2f}ms")
            
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

    def toggle_launch_icons(self, checked):
        """切换启动项图标显示"""
        try:
            config = load_config()
            set_launch_icon_enabled(config, checked)
            save_config(config)
            self.invalidate_config_cache()
            loader = get_icon_loader()
            loader.set_enabled(checked)
            LaunchItem.ICONS_ENABLED = checked
            self.update_ui_with_config(config)
            state = "启用" if checked else "禁用"
            self.logger.info(f"启动项图标已{state}")
        except Exception as e:
            self.logger.error(f"切换启动项图标失败: {e}")
            QMessageBox.critical(self, "操作失败", f"无法更新图标设置: {e}")

    def prompt_icon_cache_capacity(self):
        """设置图标缓存容量"""
        try:
            config = load_config()
            current_capacity = get_icon_cache_capacity(config)
            value, ok = QInputDialog.getInt(
                self,
                "图标缓存大小",
                "请输入缓存的最大图标数量（16-1024）：",
                current_capacity,
                16,
                1024,
                16
            )
            if ok:
                set_icon_cache_capacity(config, value)
                save_config(config)
                get_icon_loader().set_cache_capacity(value)
                self.logger.info(f"图标缓存容量已更新为 {value}")
        except Exception as e:
            self.logger.error(f"更新图标缓存容量失败: {e}")
            QMessageBox.critical(self, "操作失败", f"无法更新图标缓存容量: {e}")

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
        
        current_tab = self.tab_widget.currentWidget()
        if current_tab and isinstance(current_tab, CategoryTab) and hasattr(current_tab, 'reset_to_first_page'):
            current_tab.reset_to_first_page()
        
        # 如果是在"全部"标签页中搜索
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
                    clone = LaunchItem(widget.name, widget.app, widget.params, category, widget.tags)
                    clone.set_category_tab(all_tab)
                    
                    # 设置右键菜单
                    clone.setContextMenuPolicy(Qt.CustomContextMenu)
                    clone.customContextMenuRequested.connect(
                        lambda pos, i=clone: all_tab.show_item_context_menu(pos, i)
                    )
                    
                    all_tab.content_layout.addWidget(clone)

    def update_all_category_from_config(self, config, apply_filter=True):
        """从配置直接加载全部分类的内容
        
        Args:
            config: 配置数据
            apply_filter: 是否应用标签过滤
        """
        if "全部" not in self.tabs:
            return
        
        all_tab = self.tabs["全部"]
        
        if hasattr(all_tab, 'begin_batch_update'):
            all_tab.begin_batch_update()
        if hasattr(all_tab, '_clear_all_launch_items'):
            all_tab._clear_all_launch_items()
        else:
            while all_tab.content_layout.count():
                widget = all_tab.content_layout.itemAt(0).widget()
                if widget:
                    all_tab.content_layout.removeWidget(widget)
                    widget.setParent(None)
        
        # 获取要显示的程序列表（可能经过过滤）
        programs_to_show = config.get("programs", [])
        if apply_filter:
            programs_to_show = filter_programs_by_tags(config)
        
        # 加载程序
        for program in programs_to_show:
            name = program.get("name", "")
            category = program.get("category", "娱乐")
            tags = program.get("tags", [])
            
            if not name:
                continue
            
            for launch_item in program.get("launch_items", []):
                app = launch_item.get("app", "")
                params = launch_item.get("params", [])
                
                if not app:
                    continue
                
                if hasattr(all_tab, 'add_launch_item'):
                    all_tab.add_launch_item(name, app, params, tags=tags, source_category=category, defer_refresh=True)
                else:
                    item = LaunchItem(name, app, params, category, tags)
                    item.set_category_tab(all_tab)
                    item.setContextMenuPolicy(Qt.CustomContextMenu)
                    item.customContextMenuRequested.connect(
                        lambda pos, i=item: all_tab.show_item_context_menu(pos, i)
                    )
                    all_tab.content_layout.addWidget(item)
        
        if hasattr(all_tab, 'end_batch_update'):
            all_tab.end_batch_update(reset_to_first=True)

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
            import time
            start_time = time.time()
            self.logger.debug("开始恢复窗口显示")
            
            # 中断正在进行的同步操作
            self._interrupt_sync_operations()
            
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
            
            # 记录窗口恢复耗时
            end_time = time.time()
            self.logger.info(f"窗口恢复耗时: {(end_time - start_time)*1000:.2f}ms")
            
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
    
    def _interrupt_sync_operations(self):
        """中断正在进行的同步操作"""
        try:
            # 停止自动同步定时器
            if hasattr(self, 'auto_sync_timer') and self.auto_sync_timer.isActive():
                self.auto_sync_timer.stop()
                self.logger.debug("已停止自动同步定时器")
            
            # 中断正在进行的同步线程
            interrupted_count = 0
            for thread_info in self._sync_threads.copy():
                thread, worker = thread_info
                if thread and thread.isRunning():
                    # 设置中断标志
                    if hasattr(worker, 'should_stop'):
                        worker.should_stop = True
                    # 等待线程结束（最多等100ms）
                    if not thread.wait(100):
                        # 如果线程不响应，强制终止
                        thread.terminate()
                        thread.wait(100)
                    interrupted_count += 1
                    self._sync_threads.remove(thread_info)
            
            if interrupted_count > 0:
                self.logger.info(f"已中断 {interrupted_count} 个同步操作")
                self._sync_in_progress = False
                
        except Exception as e:
            self.logger.error(f"中断同步操作时出错: {e}")
    
    def _stop_sync_operations_immediately(self):
        """立即停止同步操作（在窗口显示时调用）"""
        try:
            # 停止自动同步定时器
            if hasattr(self, 'auto_sync_timer') and self.auto_sync_timer.isActive():
                self.auto_sync_timer.stop()
                self.logger.debug("窗口显示，立即停止自动同步定时器")
            
            # 检查是否有正在进行的同步操作
            active_sync_count = len([t for t in self._sync_threads if t[0].isRunning()])
            if active_sync_count > 0:
                self.logger.warning(f"检测到 {active_sync_count} 个活跃同步操作，将在后台继续执行")
                
        except Exception as e:
            self.logger.error(f"停止同步操作时出错: {e}")
    
    def _cleanup_finished_threads(self):
        """清理已完成的线程"""
        try:
            finished_threads = []
            for thread_info in self._sync_threads.copy():
                thread, worker = thread_info
                if not thread.isRunning():
                    finished_threads.append(thread_info)
                    self._sync_threads.remove(thread_info)
            
            if finished_threads:
                self.logger.debug(f"已清理 {len(finished_threads)} 个已完成的同步线程")
                
        except Exception as e:
            self.logger.error(f"清理已完成线程时出错: {e}")

    def focus_search_input(self):
        """将焦点设置到搜索输入框"""
        self.search_input.setFocus()
        self.search_input.selectAll()  # 全选当前文本，方便用户直接输入

    def apply_background_config(self, config_data, source="后台刷新"):
        """仅更新配置数据并标记下次显示时刷新UI"""
        if not config_data:
            self.logger.warning("收到空配置，跳过后台刷新")
            return False
        try:
            save_config(config_data)
            # 保存历史记录
            if hasattr(self, 'history_manager') and self.history_manager:
                try:
                    self.history_manager.save_history(config_data, source)
                except Exception as history_err:
                    self.logger.warning(f"保存历史记录失败: {history_err}")

            snapshot = copy.deepcopy(config_data)
            # 更新本地缓存以便 get_cached_config 使用
            self._config_cache = snapshot
            self._config_cache_time = time.time()
            self._set_pending_refresh_state(snapshot, source)
            self.logger.info(f"已记录后台配置刷新，来源: {source}")
            return True
        except Exception as e:
            self.logger.error(f"后台刷新配置失败: {e}")
            return False

    def _set_pending_refresh_state(self, snapshot, source):
        """保存待刷新快照"""
        self._pending_config_snapshot = snapshot
        self._pending_refresh_timestamp = time.time()
        self._pending_refresh_source = source
        self._pending_ui_refresh = True

    def apply_pending_refresh_if_needed(self, reason="showEvent", force=False):
        """在窗口可见/需要立即刷新时应用后台配置"""
        if not self._pending_ui_refresh and not force:
            return False

        config_to_apply = self._pending_config_snapshot
        if config_to_apply is None:
            # 快照缺失时退回磁盘配置
            config_to_apply = load_config()

        applied = False
        try:
            snapshot = copy.deepcopy(config_to_apply)
            self.update_ui_with_config(snapshot)
            self.update_statistics()
            elapsed_ms = 0
            if self._pending_refresh_timestamp:
                elapsed_ms = (time.time() - self._pending_refresh_timestamp) * 1000
            self.logger.info(
                f"已应用待刷新配置 (原因: {reason}, 来源: {self._pending_refresh_source}, 延迟: {elapsed_ms:.0f}ms)"
            )
            applied = True
        except Exception as e:
            self.logger.error(f"应用后台刷新配置失败: {e}")
        finally:
            if applied or force:
                self._pending_ui_refresh = False
                self._pending_config_snapshot = None
                self._pending_refresh_timestamp = 0
                self._pending_refresh_source = ""
        return applied

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

    def find_launch_item_widget(self, category, name, app, params):
        """在指定分类中查找与给定信息匹配的启动项"""
        tab = self.tabs.get(category)
        if not tab:
            return None
        for i in range(tab.content_layout.count()):
            widget = tab.content_layout.itemAt(i).widget()
            if widget and isinstance(widget, LaunchItem):
                if widget.name == name and widget.app == app and widget.params == params:
                    return widget
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

    def open_config_in_system_editor(self):
        """使用系统默认编辑器打开配置文件"""
        try:
            from utils.config_manager import CONFIG_PATH
            if not os.path.exists(CONFIG_PATH):
                QMessageBox.warning(self, "未找到配置", f"配置文件不存在:\n{CONFIG_PATH}")
                return

            if is_windows():
                os.startfile(CONFIG_PATH)
            elif is_mac():
                import subprocess
                subprocess.Popen(["open", CONFIG_PATH])
            elif is_linux():
                import subprocess
                subprocess.Popen(["xdg-open", CONFIG_PATH])
            else:
                raise RuntimeError("当前平台不支持自动打开配置文件")
        except Exception as e:
            self.logger.error(f"调用系统编辑器打开配置失败: {e}")
            QMessageBox.critical(self, "打开失败", f"无法用系统编辑器打开配置文件:\n{e}")

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

    def show_tag_manager(self):
        """显示标签管理对话框"""
        try:
            config = load_config()
            available_tags = get_available_tags(config)
            
            dialog = TagManagerDialog(available_tags, self)
            dialog.tags_updated.connect(self.on_tags_updated)
            
            if dialog.exec_():
                # 更新配置中的可用标签
                updated_tags = dialog.get_updated_tags()
                config["available_tags"] = updated_tags
                save_config(config)
                
                # 更新UI
                self.refresh_tag_filter()
                self.logger.info("标签管理更新完成")
                
        except Exception as e:
            self.logger.error(f"显示标签管理对话框时出错: {e}")
            QMessageBox.critical(self, "错误", f"显示标签管理对话框时出错: {e}")
    
    def on_tags_updated(self, updated_tags):
        """标签更新时的处理"""
        try:
            config = load_config()  
            config["available_tags"] = updated_tags
            save_config(config)
            
            # 更新标签过滤器
            self.refresh_tag_filter()
            
        except Exception as e:
            self.logger.error(f"更新标签时出错: {e}")
    
    def refresh_tag_filter(self):
        """刷新标签过滤器"""
        try:
            config = load_config()
            available_tags = get_available_tags(config)
            filter_state = get_tag_filter_state(config)
            
            # 更新标签过滤器组件
            self.tag_filter_widget.set_available_tags(available_tags)
            self.tag_filter_widget.set_filter_state(
                filter_state.get("selected_tags", []),
                filter_state.get("filter_mode", "OR")
            )
            
        except Exception as e:
            self.logger.error(f"刷新标签过滤器时出错: {e}")
    
    def on_tag_filter_changed(self, selected_tags, filter_mode):
        """标签过滤器改变时的处理"""
        try:
            config = load_config()
            
            # 更新配置
            update_tag_filter_state(config, selected_tags, filter_mode)
            save_config(config)
            
            # 刷新显示的程序列表
            self.apply_tag_filter()
            
            self.logger.debug(f"标签过滤器更新: 选中标签={selected_tags}, 模式={filter_mode}")
            
        except Exception as e:
            self.logger.error(f"处理标签过滤器改变时出错: {e}")
    
    def apply_tag_filter(self):
        """应用标签过滤"""
        try:
            config = load_config()
            
            # 获取过滤后的程序列表
            filtered_programs = filter_programs_by_tags(config)
            
            # 特殊处理"全部"分类
            if "全部" in self.tabs:
                self.update_all_category_from_config(config, apply_filter=True)
            
            # 更新其他标签页的显示
            for category_name, tab in self.tabs.items():
                if category_name == "全部":
                    continue  # 已经在上面处理了
                    
                if hasattr(tab, 'update_programs_with_filter'):
                    # 如果标签页支持过滤，使用过滤后的程序列表
                    tab.update_programs_with_filter(filtered_programs)
                else:
                    # 否则使用传统方式更新（为了兼容性）
                    if hasattr(tab, 'update_programs'):
                        tab.update_programs(filtered_programs)
            
        except Exception as e:
            self.logger.error(f"应用标签过滤时出错: {e}")

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
            source_desc = "从同步服务下载配置"
            if not self.apply_background_config(config_data, source_desc):
                QMessageBox.warning(self, "下载成功但应用失败", "配置已下载，但写入本地时出错。")
                return
            if self.isVisible():
                self.apply_pending_refresh_if_needed(reason="download-visible", force=True)
            else:
                self.logger.info("窗口隐藏，延迟应用下载的配置刷新")
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
            
            # 如果已有同步操作在进行，跳过
            if self._sync_in_progress:
                self.logger.debug("同步操作正在进行，跳过本次自动同步")
                return
                
            self.logger.debug("执行定时自动同步检查")
            self._sync_in_progress = True
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
                self._sync_in_progress = False
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
            
            # 记录线程信息
            self._sync_threads.append((self.auto_download_thread, self.auto_download_worker))
            
            # 启动线程
            self.auto_download_thread.start()
            self.logger.debug("已启动自动下载配置")
            
        except Exception as e:
            self.logger.error(f"自动同步配置时出错: {e}")
            self._sync_in_progress = False

    def auto_sync_completed(self, success, message, config_data):
        """自动同步完成后的处理"""
        try:
            # 清理线程记录
            self._cleanup_finished_threads()
            self._sync_in_progress = False
            
            if success and config_data:
                source_desc = "自动同步配置"
                deferred = self.apply_background_config(config_data, source_desc)
                if not deferred:
                    self.logger.error("自动同步配置写入失败，已跳过刷新")
                    return
                if self.isVisible():
                    self.apply_pending_refresh_if_needed(reason="auto-sync-visible", force=True)
                else:
                    self.logger.info("窗口隐藏，已记录自动同步结果，待下次显示时刷新")
            else:
                self.logger.warning(f"自动同步配置失败: {message}")
        except Exception as e:
            self.logger.error(f"处理自动同步结果时出错: {e}")
            self._sync_in_progress = False



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
            else:
                self.logger.warning(f"自动上传配置失败: {message}")
        except Exception as e:
            self.logger.error(f"处理自动上传结果时出错: {e}")


    def upload_completed(self, success, message, _):
        """上传完成后的处理"""
        # 停止加载动画
        self.upload_button.stop_loading()
        
        # 显示结果
        if success:
            QMessageBox.information(self, "上传成功", message)
        else:
            QMessageBox.warning(self, "上传失败", message)

    def show_normal_and_raise(self):
        """恢复窗口用于响应外部激活请求。"""
        try:
            self.logger.debug("处理激活请求，尝试恢复窗口")
            if self.isMinimized():
                self.showNormal()
            else:
                self.show()

            # 统一处理焦点与前置
            self.raise_()
            self.activateWindow()
            self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)

            if self._platform_cache.get('is_windows'):
                try:
                    hwnd = int(self.winId())
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                except Exception as exc:
                    self.logger.warning(f"调用 Windows API 激活窗口失败: {exc}")
            elif self._platform_cache.get('is_mac'):
                try:
                    AppKit.NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
                except Exception as exc:
                    self.logger.warning(f"调用 macOS API 激活窗口失败: {exc}")

            QTimer.singleShot(50, self.focus_search_input)
        except Exception as exc:
            self.logger.error(f"处理激活请求时出错: {exc}")

    def showEvent(self, event):
        """重写显示事件，用于在显示窗口时执行操作"""
        super().showEvent(event)
        
        import time
        start_time = time.time()

        if self._pending_ui_refresh:
            self.logger.debug("检测到待刷新配置，showEvent 中立即应用")
            self.apply_pending_refresh_if_needed(reason="showEvent")
        
        # 暂停热键检测在窗口恢复期间，减少CPU竞争
        if self.hotkey_manager and hasattr(self.hotkey_manager, 'pause_checking'):
            self.hotkey_manager.pause_checking()
            # 300ms后恢复热键检测，给窗口足够时间完成恢复
            QTimer.singleShot(300, lambda: (
                self.hotkey_manager.resume_checking() 
                if self.hotkey_manager and hasattr(self.hotkey_manager, 'resume_checking') 
                else None
            ))
        
        # 立即停止自动同步定时器和相关操作
        self._stop_sync_operations_immediately()
        
        # 优化焦点设置：减少延迟并只在窗口真正可见时设置
        if self.isVisible() and not self.isMinimized():
            QTimer.singleShot(30, self.focus_search_input)  # 进一步减少延迟到30ms
        
        # 记录showEvent耗时
        end_time = time.time()
        self.logger.debug(f"showEvent耗时: {(end_time - start_time)*1000:.2f}ms")
        
    def hideEvent(self, event):
        """重写隐藏事件，用于在窗口隐藏时执行操作"""
        super().hideEvent(event)
        
        # 优化自动同步定时器启停：延迟启动，避免快速显示/隐藏时的频繁切换
        if hasattr(self, 'auto_sync_timer') and not self.auto_sync_timer.isActive():
            # 延迟2秒启动同步定时器，避免快速切换时的性能损失
            QTimer.singleShot(2000, self._start_auto_sync_timer)
            self.logger.debug("窗口隐藏，将在2秒后启动自动同步定时器")
    
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
