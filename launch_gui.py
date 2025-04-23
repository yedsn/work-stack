#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QTabWidget, QListWidget, QListWidgetItem, QFrame,
                            QScrollArea)
from PyQt5.QtCore import Qt, QMimeData, QPoint
from PyQt5.QtGui import QDrag, QFont

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

# 添加调试信息
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"CONFIG_PATH: {CONFIG_PATH}")

# 定义一个简单的替代函数
def launch_app(name, app, *params):
    try:
        print(f"启动应用: {name}, 程序: {app}, 参数: {params}")
        
        # 获取操作系统类型
        os_type = "windows" if sys.platform.startswith("win") else "mac" if sys.platform.startswith("darwin") else "linux"
        
        # 常见浏览器和应用程序的路径映射
        app_paths = {
            "windows": {
                "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
                "vscode": r"C:\Program Files\Microsoft VS Code\Code.exe",
            },
            "mac": {
                "chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "edge": "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                "firefox": "/Applications/Firefox.app/Contents/MacOS/firefox",
                "vscode": "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
            },
            "linux": {
                "chrome": "google-chrome",
                "edge": "microsoft-edge",
                "firefox": "firefox",
                "vscode": "code",
            }
        }
        
        # 获取应用程序的实际路径
        app_path = app
        app_lower = app.lower()
        
        # 如果是常见应用，使用预定义路径
        if app_lower in app_paths.get(os_type, {}):
            app_path = app_paths[os_type][app_lower]
            print(f"使用预定义路径: {app_path}")
        
        # 处理参数
        cmd = [app_path]
        
        # 特殊处理浏览器的新窗口参数
        if app_lower in ["chrome", "edge"]:
            cmd.append("--new-window")
        elif app_lower == "firefox":
            cmd.append("-new-window")
        
        # 添加其他参数
        if params:
            if len(params) == 1 and isinstance(params[0], list):
                cmd.extend(params[0])
            else:
                cmd.extend(params)
        
        print(f"执行命令: {cmd}")
        subprocess.Popen(cmd)
        return True
    except Exception as e:
        print(f"启动应用失败: {e}")
        
        # 尝试使用webbrowser模块（适用于URL）
        try:
            if params and (isinstance(params[0], list) and params[0] and params[0][0].startswith("http")) or \
               (isinstance(params[0], str) and params[0].startswith("http")):
                import webbrowser
                if isinstance(params[0], list):
                    for url in params[0]:
                        webbrowser.open(url)
                else:
                    webbrowser.open(params[0])
                return True
        except Exception as e2:
            print(f"使用webbrowser模块也失败: {e2}")
        
        return False

class LaunchItem(QFrame):
    """可拖拽的启动项目"""
    def __init__(self, name, app, params, parent=None):
        super().__init__(parent)
        self.name = name
        self.app = app
        self.params = params
        
        self.setFrameShape(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setMinimumHeight(80)
        self.setMaximumHeight(120)
        
        # 设置鼠标样式
        self.setCursor(Qt.PointingHandCursor)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(name)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 应用信息
        app_label = QLabel(f"应用: {app}")
        app_label.setStyleSheet("color: gray;")
        layout.addWidget(app_label)
        
        # 参数信息
        if isinstance(params, list):
            params_text = " ".join(params)
        else:
            params_text = str(params)
            
        if len(params_text) > 50:
            params_text = params_text[:47] + "..."
            
        params_label = QLabel(f"参数: {params_text}")
        params_label.setStyleSheet("color: blue; text-decoration: underline;")
        layout.addWidget(params_label)
        
        # 设置样式
        self.setStyleSheet("""
            LaunchItem {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
            LaunchItem:hover {
                background-color: #f0f8ff;
                border: 1px solid #4a86e8;
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
            
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # 存储项目数据
        item_data = {
            "name": self.name,
            "app": self.app,
            "params": self.params
        }
        mime_data.setText(json.dumps(item_data))
        drag.setMimeData(mime_data)
        
        # 设置拖拽时的半透明效果
        drag.setHotSpot(event.pos())
        drag.exec_(Qt.MoveAction)
    
    def mouseDoubleClickEvent(self, event):
        # 双击启动应用
        try:
            if isinstance(self.params, list):
                launch_app(self.name, self.app, self.params)
            else:
                launch_app(self.name, self.app, self.params)
        except Exception as e:
            print(f"启动应用失败: {e}")


class CategoryTab(QWidget):
    """分类标签页"""
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # 创建内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(10)
        
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
        
        # 设置接受拖放
        self.setAcceptDrops(True)
    
    def add_launch_item(self, name, app, params):
        """添加启动项"""
        item = LaunchItem(name, app, params, self)
        self.content_layout.addWidget(item)
        return item
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasText():
            try:
                item_data = json.loads(event.mimeData().text())
                # 检查是否已存在相同名称的项目
                for i in range(self.content_layout.count()):
                    widget = self.content_layout.itemAt(i).widget()
                    if widget and isinstance(widget, LaunchItem) and widget.name == item_data["name"]:
                        # 如果是从其他标签页拖过来的，需要删除原来的
                        if event.source().parent() != self:
                            event.source().setParent(None)
                        return
                
                # 如果是从其他标签页拖过来的，需要删除原来的并添加到当前标签页
                if event.source().parent() != self:
                    event.source().setParent(None)
                    self.add_launch_item(item_data["name"], item_data["app"], item_data["params"])
                    # 更新配置文件
                    self.window().update_config()
                else:
                    # 同一标签页内的拖拽，处理排序
                    pos = event.pos()
                    target_idx = -1
                    
                    # 找到目标位置
                    for i in range(self.content_layout.count()):
                        widget = self.content_layout.itemAt(i).widget()
                        if widget:
                            widget_pos = widget.mapTo(self, QPoint(0, 0))
                            if pos.y() < widget_pos.y() + widget.height() / 2:
                                target_idx = i
                                break
                    
                    # 移动项目
                    if target_idx != -1:
                        source_idx = -1
                        for i in range(self.content_layout.count()):
                            if self.content_layout.itemAt(i).widget() == event.source():
                                source_idx = i
                                break
                        
                        if source_idx != -1 and source_idx != target_idx:
                            item = self.content_layout.takeAt(source_idx)
                            if target_idx > source_idx:
                                self.content_layout.insertItem(target_idx - 1, item)
                            else:
                                self.content_layout.insertItem(target_idx, item)
                            # 更新配置文件
                            self.window().update_config()
                
                event.acceptProposedAction()
            except Exception as e:
                print(f"Drop error: {e}")


class LaunchGUI(QMainWindow):
    """启动器GUI主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("应用启动器")
        self.setMinimumSize(800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tabs = {}
        
        # 默认分类
        default_categories = ["娱乐", "工作", "文档"]
        for category in default_categories:
            self.add_category(category)
        
        # 添加"+"标签页
        self.add_tab_button = QPushButton("+")
        self.add_tab_button.setFixedSize(30, 30)
        self.tab_widget.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)
        self.add_tab_button.clicked.connect(self.add_new_category)
        
        main_layout.addWidget(self.tab_widget)
        
        # 创建底部控制栏
        control_layout = QHBoxLayout()
        
        # 名称输入
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("名称")
        
        # 应用输入
        self.app_input = QLineEdit()
        self.app_input.setPlaceholderText("应用")
        
        # 参数输入
        self.params_input = QLineEdit()
        self.params_input.setPlaceholderText("参数")
        
        # 浏览按钮
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self.browse_app)
        
        # 添加按钮
        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_launch_item)
        
        # 添加控件到布局
        control_layout.addWidget(QLabel("名称"))
        control_layout.addWidget(self.name_input)
        control_layout.addWidget(QLabel("应用"))
        control_layout.addWidget(self.app_input)
        control_layout.addWidget(browse_button)
        control_layout.addWidget(QLabel("参数"))
        control_layout.addWidget(self.params_input)
        control_layout.addWidget(add_button)
        
        main_layout.addLayout(control_layout)
        
        # 加载配置
        self.load_config()
    
    def add_category(self, name):
        """添加分类标签页"""
        if name in self.tabs:
            return
            
        tab = CategoryTab(name)
        self.tabs[name] = tab
        self.tab_widget.addTab(tab, name)
        return tab
    
    def add_new_category(self):
        """添加新分类"""
        # 这里可以弹出对话框让用户输入分类名称
        # 简化起见，直接添加一个新分类
        new_category = f"新分类{len(self.tabs) + 1}"
        self.add_category(new_category)
        self.update_config()
    
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
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择应用", "", "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if file_path:
            self.app_input.setText(file_path)
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 清空现有标签页
                for name in list(self.tabs.keys()):
                    tab = self.tabs[name]
                    index = self.tab_widget.indexOf(tab)
                    if index != -1:
                        self.tab_widget.removeTab(index)
                self.tabs.clear()
                
                # 添加分类
                categories = config.get("categories", [])
                
                # 如果没有分类或分类为空，使用默认分类
                if not categories:
                    # 从程序中提取分类
                    for program in config.get("programs", []):
                        category = program.get("category", "娱乐")
                        if category not in categories:
                            categories.append(category)
                    
                    # 确保至少有默认分类
                    if not categories:
                        categories = ["娱乐", "工作", "文档"]
                
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
        except Exception as e:
            print(f"加载配置失败: {e}")
    
    def update_config(self):
        """更新配置文件"""
        try:
            # 读取现有配置
            config = {"programs": [], "categories": []}
            if os.path.exists(CONFIG_PATH):
                try:
                    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                        existing_config = json.load(f)
                        # 保留可能存在的其他配置项
                        for key, value in existing_config.items():
                            if key not in ["programs", "categories"]:
                                config[key] = value
                except:
                    pass
            
            # 更新分类列表
            config["categories"] = list(self.tabs.keys())
            
            # 遍历所有标签页
            for category, tab in self.tabs.items():
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
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"更新配置失败: {e}")


def main():
    app = QApplication(sys.argv)
    window = LaunchGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 