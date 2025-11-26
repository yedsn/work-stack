#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, 
                           QMenu, QAction, QInputDialog, QMessageBox, QApplication, QDialog, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFileDialog, QFrame, QAbstractItemView)
from PyQt5.QtCore import Qt, QPoint
from gui.launch_item import LaunchItem
from PyQt5.QtGui import QFont
from utils.logger import get_logger

logger = get_logger()

class CategoryTab(QWidget):
    """分类标签页"""
    def __init__(self, category_name):
        super().__init__()
        self.category_name = category_name
        self.main_window = None
        self.title_label = None
        self.separator = None
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        import sys
        if sys.platform == 'darwin':
            # Mac特定布局设置 - 更接近Windows版本，更紧凑
            layout.setContentsMargins(5, 5, 5, 5)  # 减小内边距
            layout.setSpacing(5)  # 减小间距
        else:
            # Windows平台更紧凑的布局
            layout.setContentsMargins(8, 8, 8, 8)  # 减小内边距
            layout.setSpacing(8)  # 减小间距
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setAlignment(Qt.AlignHCenter | Qt.AlignTop)  # 水平居中和顶部对齐
        
        # 保存滚动位置
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.save_scroll_position)
        self.scroll_position = 0
        
        # 创建内容控件
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: white;")
        content_widget.setMinimumWidth(500)  # 设置最小宽度防止内容挤压
        
        # 创建内容的主布局（改用垂直布局）
        main_content_layout = QVBoxLayout(content_widget)
        main_content_layout.setContentsMargins(5, 5, 5, 5)  # 设置相同的左右边距
        main_content_layout.setSpacing(0)
        
        # 创建内容区域用于存放列表项
        items_widget = QWidget()
        # Mac上根据内容自动调整大小，不设置较大的最小高度
        if sys.platform == 'darwin':
            items_widget.setMinimumHeight(50)  # 减小最小高度，根据内容自动调整
        else:
            # Windows平台也使用较小的最小高度，让内容自适应
            items_widget.setMinimumHeight(50)  # 减小最小高度
            
        self.content_layout = QVBoxLayout(items_widget)
        self.content_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # 确保列表项居上对齐和水平居中
        
        if sys.platform == 'darwin':
            # Mac特定内容布局设置 - 更接近Windows版本
            self.content_layout.setSpacing(8)  # 减小间距
            self.content_layout.setContentsMargins(3, 3, 3, 3)  # 设置相同的左右边距
            
            # 添加空列表提示（初始隐藏）
            self.empty_label = QLabel("暂无内容")
            self.empty_label.setAlignment(Qt.AlignCenter)
            self.empty_label.setStyleSheet("color: #999999; font-size: 14px; padding: 10px;")  # 减少padding
            self.empty_label.hide()  # 默认隐藏
            self.content_layout.addWidget(self.empty_label)
            
            # 设置滚动区域样式
            self.scroll_area.setStyleSheet("""
                QScrollArea {
                    background-color: white;
                    border: none;
                }
                QScrollBar:vertical {
                    background: #f0f0f0;
                    width: 10px;  /* 更紧凑的滚动条 */
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #c0c0c0;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #a0a0a0;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
            """)
        else:
            # Windows平台更紧凑的布局
            self.content_layout.setSpacing(8)  # 减小间距
            self.content_layout.setContentsMargins(3, 3, 3, 3)  # 设置相同的左右边距
            
            # 添加空列表提示（初始隐藏）
            self.empty_label = QLabel("暂无内容")
            self.empty_label.setAlignment(Qt.AlignCenter)
            self.empty_label.setStyleSheet("color: #999999; font-size: 14px; padding: 20px;")
            self.empty_label.hide()  # 默认隐藏
            self.content_layout.addWidget(self.empty_label)
        
        # 将列表项区域添加到主布局
        main_content_layout.addWidget(items_widget)
        
        # 添加空白区域到底部（使用伸展因子）
        main_content_layout.addStretch(1)
        
        self.scroll_area.setWidget(content_widget)
        layout.addWidget(self.scroll_area)
        
        # 确保内容控件宽度至少与滚动区域一样宽
        content_widget.setMinimumWidth(self.scroll_area.viewport().width())
        
        # 存储选中的项目
        self.selected_items = []
        
        # 检查是否为空列表
        self.check_empty_list()
    
    def set_main_window(self, main_window):
        """设置主窗口引用"""
        self.main_window = main_window
    
    def save_scroll_position(self, value):
        """保存滚动条位置"""
        self.scroll_position = value
        
    def restore_scroll_position(self):
        """恢复滚动条位置"""
        self.scroll_area.verticalScrollBar().setValue(self.scroll_position)
    
    def reset_scroll_position(self):
        """重置滚动条到顶部"""
        self.scroll_area.verticalScrollBar().setValue(0)
    
    def update_programs_with_filter(self, filtered_programs):
        """使用过滤后的程序列表更新显示"""
        try:
            app_set = set()
            for program in filtered_programs:
                for launch_item in program.get("launch_items", []):
                    app = launch_item.get("app")
                    if app:
                        app_set.add(app)
            LaunchItem.preload_icons(app_set)

            # 清除现有项目
            for i in reversed(range(self.content_layout.count())):
                widget = self.content_layout.itemAt(i).widget()
                if widget and isinstance(widget, LaunchItem):
                    widget.setParent(None)

            # 添加过滤后的程序
            if self.category_name == "全部":
                for program in filtered_programs:
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
                        item = LaunchItem(name, app, params, source_category=category, tags=tags)
                        item.set_category_tab(self)
                        item.setFocusPolicy(Qt.StrongFocus)
                        if self.main_window:
                            item.installEventFilter(self.main_window)
                        item.setContextMenuPolicy(Qt.CustomContextMenu)
                        item.customContextMenuRequested.connect(lambda pos, i=item: self.show_item_context_menu(pos, i))
                        self.content_layout.addWidget(item)
            else:
                for program in filtered_programs:
                    name = program.get("name", "")
                    category = program.get("category", "娱乐")
                    tags = program.get("tags", [])
                    if not name or category != self.category_name:
                        continue
                    for launch_item in program.get("launch_items", []):
                        app = launch_item.get("app", "")
                        params = launch_item.get("params", [])
                        if not app:
                            continue
                        item = LaunchItem(name, app, params, tags=tags)
                        item.set_category_tab(self)
                        item.setFocusPolicy(Qt.StrongFocus)
                        if self.main_window:
                            item.installEventFilter(self.main_window)
                        item.setContextMenuPolicy(Qt.CustomContextMenu)
                        item.customContextMenuRequested.connect(lambda pos, i=item: self.show_item_context_menu(pos, i))
                        self.content_layout.addWidget(item)

            self.check_empty_list()
            self._sort_launch_items()
        except Exception as e:
            logger.error(f"使用过滤器更新程序列表时出错: {e}")

    def add_launch_item(self, name, app, params, tags=None, source_category=None, defer_refresh=False):
        """添加启动项"""
        item = LaunchItem(name, app, params, source_category=source_category, tags=tags)
        item.set_category_tab(self)
        item.setFocusPolicy(Qt.StrongFocus)
        if self.main_window:
            item.installEventFilter(self.main_window)
        item.setContextMenuPolicy(Qt.CustomContextMenu)
        item.customContextMenuRequested.connect(lambda pos, i=item: self.show_item_context_menu(pos, i))
        self.content_layout.insertWidget(0, item)
        self.reset_scroll_position()
        self.check_empty_list()
        self._sort_launch_items()
        import sys
        if sys.platform == 'darwin' and self.main_window:
            self.main_window.adjustSize()
        return item
    
    def remove_launch_item(self, item):
        """移除启动项"""
        self.content_layout.removeWidget(item)
        item.deleteLater()
        self.check_empty_list()
        import sys
        if sys.platform == 'darwin' and self.main_window:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self.main_window.adjustSize)
    
    def show_item_context_menu(self, position, item):
        """显示启动项右键菜单"""
        menu = QMenu()
        
        # 检查是否有多个项目被选中
        if len(self.selected_items) > 1 and item in self.selected_items:
            # 多选情况下的菜单
            run_all_action = QAction("运行所有选中项", self)
            run_all_action.triggered.connect(self.run_selected_items)
            
            # 添加删除所有选中项的选项
            delete_all_action = QAction("删除所有选中项", self)
            delete_all_action.triggered.connect(self.delete_selected_items)
            
            # 添加移动所有选中项的子菜单
            move_all_menu = QMenu("移动所有选中项到", self)
            
            # 获取所有分类
            if self.main_window:
                categories = self.main_window.get_categories()
                for category in categories:
                    if category != self.category_name:
                        action = QAction(category, self)
                        action.triggered.connect(lambda checked, c=category: 
                                              self.move_selected_items_to_category(c))
                        move_all_menu.addAction(action)
            
            # 添加复制所有选中项的选项
            duplicate_all_action = QAction("复制所有选中项", self)
            duplicate_all_action.triggered.connect(self.duplicate_selected_items)
            
            menu.addAction(run_all_action)
            menu.addSeparator()
            menu.addAction(duplicate_all_action)
            menu.addSeparator()
            menu.addAction(delete_all_action)
            menu.addMenu(move_all_menu)
            
            menu.exec_(item.mapToGlobal(position))
        else:
            # 单选情况下的菜单
            run_action = QAction("运行", self)
            edit_action = QAction("编辑", self)
            edit_tags_action = QAction("编辑标签", self)
            delete_action = QAction("删除", self)
            
            # 添加复制相关的菜单项
            copy_menu = QMenu("复制", self)
            copy_item_action = QAction("复制项", self)
            copy_name_action = QAction("复制名称", self)
            copy_path_action = QAction("复制路径", self)
            copy_params_action = QAction("复制参数", self)
            
            copy_menu.addAction(copy_item_action)
            copy_menu.addAction(copy_name_action)
            copy_menu.addAction(copy_path_action)
            copy_menu.addAction(copy_params_action)
            
            # 连接复制功能的信号
            copy_item_action.triggered.connect(lambda: self.duplicate_item(item))
            copy_name_action.triggered.connect(lambda: self.copy_item_data(item, "name"))
            copy_path_action.triggered.connect(lambda: self.copy_item_data(item, "path"))
            copy_params_action.triggered.connect(lambda: self.copy_item_data(item, "params"))
            
            # 移动到其他分类子菜单
            move_menu = QMenu("移动到", self)
            
            # 获取所有分类
            if self.main_window:
                categories = self.main_window.get_categories()
                for category in categories:
                    if category != self.category_name:
                        action = QAction(category, self)
                        action.triggered.connect(lambda checked, c=category, i=item: 
                                              self.move_item_to_category(i, c))
                        move_menu.addAction(action)
            
            menu.addAction(run_action)
            menu.addSeparator()
            menu.addAction(edit_action)
            menu.addAction(edit_tags_action)
            menu.addAction(delete_action)
            menu.addSeparator()
            menu.addMenu(copy_menu)  # 添加复制菜单
            menu.addSeparator()
            menu.addMenu(move_menu)
            
            action = menu.exec_(item.mapToGlobal(position))
            
            if action == run_action:
                item.launch()
            elif action == edit_action:
                self.edit_launch_item(item)
            elif action == edit_tags_action:
                self.edit_item_tags(item)
            elif action == delete_action:
                self.delete_launch_item(item)
    
    def edit_launch_item(self, item):
        """编辑启动项"""
        # 如果在"全部"分类中，定位真实所属分类的项目
        real_item = None
        source_category = getattr(item, "source_category", None)
        original_name = item.name
        original_app = item.app
        original_params = item.params.copy() if item.params else []

        if self.category_name == "全部" and self.main_window:
            if not source_category:
                source_category = self.main_window.find_item_original_category(item)
            if source_category:
                real_item = self.main_window.find_launch_item_widget(
                    source_category,
                    original_name,
                    original_app,
                    original_params
                )
        else:
            source_category = self.category_name
            real_item = item

        # 创建编辑对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑启动项")
        dialog.setMinimumWidth(400)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名称:"))
        name_input = QLineEdit(item.name)
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)
        
        # 应用路径
        app_layout = QHBoxLayout()
        app_layout.addWidget(QLabel("应用路径:"))
        app_input = QLineEdit(item.app)
        app_layout.addWidget(app_input)
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(lambda: self.browse_app_for_edit(app_input))
        app_layout.addWidget(browse_button)
        layout.addLayout(app_layout)
        
        # 参数
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("参数:"))
        params_input = QLineEdit(" ".join(item.params) if item.params else "")
        params_layout.addWidget(params_input)
        layout.addLayout(params_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # 连接信号
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 更新启动项
            new_name = name_input.text().strip()
            new_app = app_input.text().strip()
            params_text = params_input.text().strip()
            if params_text:
                if params_text.startswith("[") and params_text.endswith("]"):
                    try:
                        new_params = json.loads(params_text)
                    except Exception:
                        new_params = params_text.split()
                else:
                    new_params = params_text.split()
            else:
                new_params = []

            item.name = new_name
            item.app = new_app
            item.params = new_params.copy()
            item.update_display()

            # 如果在"全部"分类中，更新真实分类下的项目
            if self.category_name == "全部" and self.main_window and real_item and real_item is not item:
                real_item.name = new_name
                real_item.app = new_app
                real_item.params = new_params.copy()
                real_item.update_display()
                item.source_category = source_category
            
            # 更新配置
            if self.main_window:
                self.main_window.update_config()

    def browse_app_for_edit(self, line_edit):
        """为编辑对话框浏览选择应用"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择应用", "", "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if file_path:
            line_edit.setText(file_path)
    
    def delete_launch_item(self, item):
        """删除启动项"""
        confirm = QMessageBox.question(self, "确认删除", 
                                     f"确定要删除启动项 '{item.name}' 吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            self.remove_launch_item(item)
            
            # 更新配置
            if self.main_window:
                self.main_window.update_config()
    
    def edit_item_tags(self, item):
        """编辑启动项标签"""
        try:
            from gui.item_tags_dialog import ItemTagsDialog
            from utils.config_manager import load_config, save_config, get_available_tags
            
            # 获取当前配置
            config = load_config()
            available_tags = get_available_tags(config)
            current_tags = item.tags.copy() if item.tags else []
            
            # 创建标签编辑对话框
            dialog = ItemTagsDialog(item.name, available_tags, current_tags, self)
            
            # 连接标签更新信号
            def on_tags_updated(updated_tags):
                # 实时更新项目的标签（预览）
                item.tags = updated_tags.copy()
            
            dialog.tags_updated.connect(on_tags_updated)
            
            # 显示对话框
            if dialog.exec_():
                # 用户确认，保存标签更改
                final_tags = dialog.get_selected_tags()
                updated_available_tags = dialog.get_updated_available_tags()
                
                # 更新项目标签
                item.tags = final_tags
                
                # 更新配置中的可用标签
                config["available_tags"] = updated_available_tags
                
                # 找到并更新配置中对应的程序项
                programs = config.get("programs", [])
                for program in programs:
                    if program.get("name") == item.name:
                        program["tags"] = final_tags
                        break
                
                # 保存配置
                save_config(config)
                
                # 刷新主窗口的标签过滤器
                if self.main_window:
                    self.main_window.refresh_tag_filter()
                    # 如果当前有过滤器激活，重新应用过滤
                    self.main_window.apply_tag_filter()
                
                logger.info(f"更新了启动项 '{item.name}' 的标签: {final_tags}")
            else:
                # 用户取消，恢复原标签
                item.tags = current_tags
            
        except Exception as e:
            logger.error(f"编辑启动项标签时出错: {e}")
            QMessageBox.critical(self, "错误", f"编辑标签时出错: {e}")
    
    def move_item_to_category(self, item, category):
        """将启动项移动到其他分类"""
        if self.main_window:
            # 检查是否是"全部"分类
            if self.category_name == "全部":
                # 找到项目的原始分类
                original_category = self.main_window.find_item_original_category(item)
                if original_category and original_category != "全部":
                    # 从原始分类移动到目标分类
                    success = self.main_window.move_launch_item(item, original_category, category)
                    if success:
                        # 只从"全部"分类中移除，不触发额外的更新
                        self.remove_launch_item(item)
                        
                        # 最后一步更新"全部"分类
                        self.main_window.update_all_category()
                        return
            
            # 正常的移动逻辑（非"全部"分类或找不到原始分类）
            success = self.main_window.move_launch_item(item, self.category_name, category)
            if success:
                self.remove_launch_item(item)
                
                # 最后一步更新"全部"分类
                self.main_window.update_all_category()

    # 拖放事件处理
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-launch-item"):
            event.accept()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-launch-item"):
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-launch-item"):
            event.accept()
            
            # 获取拖动的源控件
            source_item = event.source()
            if not isinstance(source_item, LaunchItem):
                return
                
            # 获取源控件所在的分类标签页
            source_tab = source_item.category_tab
            if source_tab is None:
                return
                
            # 如果是从其他分类拖过来的
            if source_tab != self:
                # 将项目移动到当前分类
                if self.main_window:
                    # 创建新的启动项
                    new_item = self.add_launch_item(source_item.name, source_item.app, source_item.params, source_item.tags)
                    
                    # 从原分类中移除
                    source_tab.remove_launch_item(source_item)
                    
                    # 更新配置
                    self.main_window.update_config()
            else:
                # 同一分类内的拖拽，处理排序
                # 获取鼠标位置
                pos = event.pos()
                
                # 找到最近的项目位置
                target_index = -1
                for i in range(self.content_layout.count()):
                    widget = self.content_layout.itemAt(i).widget()
                    if widget:
                        widget_rect = widget.geometry()
                        if pos.y() < widget_rect.center().y():
                            target_index = i
                            break
                
                if target_index == -1:
                    target_index = self.content_layout.count()
                
                # 移动项目
                current_index = -1
                for i in range(self.content_layout.count()):
                    if self.content_layout.itemAt(i).widget() == source_item:
                        current_index = i
                        break
                
                if current_index != -1 and current_index != target_index:
                    # 从布局中移除
                    self.content_layout.removeWidget(source_item)
                    
                    # 插入到新位置
                    if target_index > current_index:
                        target_index -= 1  # 调整索引，因为移除了一个项目
                    
                    self.content_layout.insertWidget(target_index, source_item)
                    
                    # 更新配置
                    if self.main_window:
                        self.main_window.update_config()
        else:
            event.ignore()

    def run_selected_items(self):
        """运行所有选中的项目"""
        for item in self.selected_items:
            item.launch()

    def duplicate_item(self, item):
        """复制项目并添加到列表中"""
        # 创建新名称，添加" Copy"后缀
        new_name = item.name + " Copy"
        
        # 添加新项目
        new_item = self.add_launch_item(new_name, item.app, item.params.copy() if item.params else [], item.tags.copy() if item.tags else [])
        
        # 更新配置
        if self.main_window:
            self.main_window.update_config()
            
        # 可以添加一个状态栏提示，如果主窗口有状态栏的话
        if self.main_window and hasattr(self.main_window, "statusBar"):
            self.main_window.statusBar().showMessage(f"已创建项目副本: {new_name}", 2000)

    def copy_item_data(self, item, data_type):
        """复制项目数据到剪贴板"""
        clipboard = QApplication.clipboard()
        
        if data_type == "all":
            # 复制整个项目的信息
            data = {
                "name": item.name,
                "app": item.app,
                "params": item.params
            }
            clipboard.setText(json.dumps(data, ensure_ascii=False))
        elif data_type == "name":
            # 复制名称
            clipboard.setText(item.name)
        elif data_type == "path":
            # 复制应用路径
            clipboard.setText(item.app)
        elif data_type == "params":
            # 复制参数
            clipboard.setText(" ".join(item.params) if item.params else "")
        
        # 可以添加一个状态栏提示，如果主窗口有状态栏的话
        if self.main_window and hasattr(self.main_window, "statusBar"):
            self.main_window.statusBar().showMessage(f"已复制到剪贴板", 2000)

    def delete_selected_items(self):
        """删除所有选中的项目"""
        if not self.selected_items:
            return
        
        confirm = QMessageBox.question(self, "确认删除", 
                                     f"确定要删除选中的 {len(self.selected_items)} 个启动项吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            # 创建副本以避免在迭代过程中修改列表
            items_to_delete = self.selected_items.copy()
            
            for item in items_to_delete:
                self.remove_launch_item(item)
            
            # 清空选中项列表
            self.selected_items.clear()
            
            # 更新配置
            if self.main_window:
                self.main_window.update_config()
            
            # 确保检查空列表状态
            self.check_empty_list()

    def move_selected_items_to_category(self, target_category):
        """将所有选中的项目移动到指定分类"""
        if not self.selected_items or not self.main_window:
            return
        
        # 创建副本以避免在迭代过程中修改列表
        items_to_move = self.selected_items.copy()
        
        # 检查是否是"全部"分类
        if self.category_name == "全部":
            # 收集需要更新的原始分类
            original_categories = set()
            
            for item in items_to_move:
                # 找到项目的原始分类
                original_category = self.main_window.find_item_original_category(item)
                if original_category and original_category != "全部":
                    original_categories.add(original_category)
                    # 从原始分类移动到目标分类，但不触发全部更新
                    success = self.main_window.move_launch_item(item, original_category, target_category)
                    if success:
                        # 只从"全部"分类中移除
                        self.remove_launch_item(item)
                else:
                    # 如果找不到原始分类，使用常规移动，但不触发全部更新
                    success = self.main_window.move_launch_item(item, self.category_name, target_category)
                    if success:
                        self.remove_launch_item(item)
        else:
            # 非"全部"分类的常规移动逻辑
            for item in items_to_move:
                # 移动但不触发全部更新
                success = self.main_window.move_launch_item(item, self.category_name, target_category)
                if success:
                    self.remove_launch_item(item)
        
        # 清空选中项列表
        self.selected_items.clear()
        
        # 最后一步更新"全部"分类
        self.main_window.update_all_category()
        
        # 更新配置，但不再触发全部更新
        self.main_window.update_config(skip_all_update=True)
        
        # 检查是否需要显示空列表提示
        self.check_empty_list()
        
        # 如果目标分类在当前标签页中，也检查目标分类的空列表状态
        if target_category in self.main_window.tabs:
            target_tab = self.main_window.tabs[target_category]
            target_tab.check_empty_list()

    def duplicate_selected_items(self):
        """复制所有选中的项目"""
        if not self.selected_items:
            return
        
        # 创建副本以避免在迭代过程中修改列表
        items_to_duplicate = self.selected_items.copy()
        
        for item in items_to_duplicate:
            # 创建新名称，添加" Copy"后缀
            new_name = item.name + " Copy"
            
            # 添加新项目
            self.add_launch_item(new_name, item.app, item.params.copy() if item.params else [], item.tags.copy() if item.tags else [])
        
        # 更新配置
        if self.main_window:
            self.main_window.update_config()
            
        # 可以添加一个状态栏提示
        if self.main_window and hasattr(self.main_window, "statusBar"):
            self.main_window.statusBar().showMessage(f"已创建 {len(items_to_duplicate)} 个项目副本", 2000)

    def check_empty_list(self):
        """检查是否为空列表并显示相应提示"""
        has_items = False
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if widget and isinstance(widget, LaunchItem):
                has_items = True
                break
        if not has_items:
            self.empty_label.show()
        else:
            self.empty_label.hide()

        import sys
        if sys.platform == 'darwin' and self.main_window:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self.main_window.adjustSize)

    def begin_batch_update(self):
        """分页兼容方法，无操作"""
        pass

    def end_batch_update(self, reset_to_first=False):
        """分页兼容方法，无操作"""
        pass

    def reset_to_first_page(self):
        """分页兼容方法，改为滚动到顶部"""
        self.reset_scroll_position()

    def _clear_all_launch_items(self):
        """供主窗口批量清空使用"""
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget and isinstance(widget, LaunchItem):
                self.content_layout.removeWidget(widget)
                widget.setParent(None)
                widget.deleteLater()
        self.check_empty_list()

    def _sort_launch_items(self):
        """按名称排序并重新排列界面上的启动项。"""
        items = []
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if widget and isinstance(widget, LaunchItem):
                items.append(widget)
        if not items:
            return
        items.sort(key=lambda it: (it.name or "").lower())
        for widget in items:
            self.content_layout.removeWidget(widget)
        for widget in items:
            self.content_layout.addWidget(widget)
        self.reset_scroll_position()

    def resizeEvent(self, event):
        """重写调整大小事件，确保内容宽度正确"""
        super().resizeEvent(event)
        # 获取滚动区域的可视区域宽度
        viewport_width = self.scroll_area.viewport().width()
        # 获取内容控件
        content_widget = self.scroll_area.widget()
        if content_widget:
            # 设置内容控件的最小宽度为滚动区域视口宽度
            content_widget.setMinimumWidth(viewport_width - 20)
