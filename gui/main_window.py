#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QTabWidget, QFileDialog, QInputDialog, QMenu,
                            QAction, QMessageBox, QDialog, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QIcon, QColor
from gui.category_tab import CategoryTab
from utils.config_manager import load_config, save_config
from gui.launch_item import LaunchItem
import win32gui
import win32process
import psutil

class LaunchGUI(QMainWindow):
    """应用启动器GUI"""
    def __init__(self):
        super().__init__()
        
        # 设置窗口标题和大小
        self.setWindowTitle("应用启动器")

        # 从配置中读取窗口大小
        config = load_config()
        window_size = config.get("window_size", {})
        width = window_size.get("width", 900)  # 默认宽度增加到900
        height = window_size.get("height", 700)  # 默认高度增加到700

        self.resize(width, height)
        self.setMinimumSize(800, 600)
        
        # 创建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tabs = {}  # 存储分类标签页
        
        # 默认分类
        default_categories = ["全部", "娱乐", "工作", "文档"]
        for category in default_categories:
            self.add_category(category)
        
        # 添加一个"+"按钮到标签栏的右侧
        add_tab_button = QPushButton("+")
        add_tab_button.setFixedSize(25, 25)  # 设置按钮大小
        add_tab_button.setStyleSheet("""
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
        """)
        add_tab_button.setToolTip("添加新分类")
        add_tab_button.clicked.connect(self.add_new_category)
        
        # 将按钮添加到标签栏右侧
        self.tab_widget.setCornerWidget(add_tab_button, Qt.TopRightCorner)
        
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
        search_layout.addWidget(self.search_input)

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
                margin-left: 5px;
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

        main_layout.addLayout(search_layout)
        
        main_layout.addWidget(self.tab_widget)
        
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
        
        main_layout.addLayout(control_layout)
        
        # 加载配置
        self.load_config()
        
        # 设置窗口样式
        self.setStyleSheet("""
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
        """)
        
        # 设置接受拖放
        self.setAcceptDrops(True)
        
        # 设置窗口图标
        self.setWindowIcon(QIcon("resources/icon.png"))
    
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
            self.update_config()
    
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
            self.update_config()
    
    def delete_category(self, index, name):
        """删除分类"""
        confirm = QMessageBox.question(self, "确认删除", 
                                     f"确定要删除分类 '{name}' 吗？\n该分类下的所有启动项也将被删除。",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            self.tab_widget.removeTab(index)
            self.tabs.pop(name)
            self.update_config()
    
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
            self.update_config()
    
    def browse_app(self):
        """浏览选择应用"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择应用", "", "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if file_path:
            self.app_input.setText(file_path)
    
    def load_config(self):
        """加载配置"""
        try:
            # 读取配置
            config = load_config()
            
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
            
            # 创建标签页
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
        except Exception as e:
            print(f"加载配置失败: {e}")
    
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
            
            # 保存配置
            save_config(config)
            
            # 如果不跳过，则更新"全部"分类
            if not skip_all_update:
                self.update_all_category()
        except Exception as e:
            print(f"更新配置失败: {e}")
    
    def handle_tab_click(self, index):
        """处理标签页点击事件"""
        pass
    
    def show_menu(self):
        """显示菜单"""
        menu = QMenu(self)
        
        # 设置快捷键
        shortcut_action = QAction("设置启动快捷键", self)
        shortcut_action.triggered.connect(self.set_shortcut)
        
        # 导出配置
        export_action = QAction("导出配置", self)
        export_action.triggered.connect(self.export_config)
        
        # 导入配置
        import_action = QAction("导入配置", self)
        import_action.triggered.connect(self.import_config)
        
        menu.addAction(shortcut_action)
        menu.addSeparator()
        menu.addAction(export_action)
        menu.addAction(import_action)
        
        # 显示菜单
        menu.exec_(QCursor.pos())
    
    def set_shortcut(self):
        """设置启动快捷键"""
        shortcut, ok = QInputDialog.getText(self, "设置启动快捷键", 
                                          "请输入快捷键组合 (例如: Ctrl+Alt+L):")
        if ok and shortcut:
            # 保存快捷键设置
            config = load_config()
            config["shortcut"] = shortcut
            save_config(config)
            QMessageBox.information(self, "设置成功", f"启动快捷键已设置为: {shortcut}")
    
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
                
                # 重新加载配置
                self.load_config()
                
                QMessageBox.information(self, "导入成功", "配置已导入并应用")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"导入配置时出错: {e}")
    
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
        """窗口关闭事件，保存窗口大小"""
        # 保存当前窗口大小
        config = load_config()
        config["window_size"] = {
            "width": self.width(),
            "height": self.height()
        }
        save_config(config)
        
        # 接受关闭事件
        event.accept()

    def get_window_handle(self):
        """获取窗口句柄"""
        import win32gui
        import win32process
        import psutil
        
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(pid)
                    windows.append({
                        'hwnd': hwnd,
                        'title': win32gui.GetWindowText(hwnd),
                        'exe': process.exe(),
                        'pid': pid
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return True
        
        windows = []
        win32gui.EnumWindows(callback, windows)
        
        # 创建窗口选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("选择打开的应用")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        
        # 添加搜索框
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        search_input = QLineEdit()
        search_input.setPlaceholderText("输入关键词过滤应用...")
        search_layout.addWidget(search_input)
        layout.addLayout(search_layout)
        
        # 创建列表控件
        list_widget = QListWidget()
        list_widget.setAlternatingRowColors(True)  # 交替行颜色
        list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;  /* 增加项目内边距 */
                margin: 2px 0;  /* 增加项目间距 */
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #e6f0ff;
                color: black;
                border: 1px solid #4a86e8;
            }
            QListWidget::item:hover {
                background-color: #f0f8ff;
            }
        """)
        
        # 添加窗口列表
        for window in windows:
            item = QListWidgetItem(f"{window['title']} - {window['exe']}")
            item.setData(Qt.UserRole, window)
            list_widget.addItem(item)
        
        layout.addWidget(list_widget)
        
        # 创建按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # 实现搜索过滤功能
        def filter_windows(text):
            search_text = text.lower()
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                window_data = item.data(Qt.UserRole)
                if (search_text in window_data['title'].lower() or 
                    search_text in window_data['exe'].lower()):
                    item.setHidden(False)
                else:
                    item.setHidden(True)
        
        search_input.textChanged.connect(filter_windows)
        
        # 双击项目自动选择
        list_widget.itemDoubleClicked.connect(dialog.accept)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            current_item = list_widget.currentItem()
            if current_item:
                window_data = current_item.data(Qt.UserRole)
                
                # 设置到输入框
                self.name_input.setText(window_data['title'])
                self.app_input.setText(window_data['exe'])
                
                return window_data
        
        return None

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
        self.update_config() 