#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, 
                           QMenu, QAction, QInputDialog, QMessageBox, QApplication, QDialog, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFileDialog, QFrame, QAbstractItemView)
from PyQt5.QtCore import Qt, QPoint
from gui.launch_item import LaunchItem

class CategoryTab(QWidget):
    """分类标签页"""
    def __init__(self, category_name):
        super().__init__()
        self.category_name = category_name
        self.main_window = None
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # 创建内容控件
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(10)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # 存储选中的项目
        self.selected_items = []
    
    def set_main_window(self, main_window):
        """设置主窗口引用"""
        self.main_window = main_window
    
    def add_launch_item(self, name, app, params):
        """添加启动项"""
        item = LaunchItem(name, app, params)
        item.set_category_tab(self)
        
        # 设置右键菜单
        item.setContextMenuPolicy(Qt.CustomContextMenu)
        item.customContextMenuRequested.connect(lambda pos, i=item: self.show_item_context_menu(pos, i))
        
        self.content_layout.addWidget(item)
        return item
    
    def remove_launch_item(self, item):
        """移除启动项"""
        self.content_layout.removeWidget(item)
        item.deleteLater()
    
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
            elif action == delete_action:
                self.delete_launch_item(item)
    
    def edit_launch_item(self, item):
        """编辑启动项"""
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
            item.name = name_input.text()
            item.app = app_input.text()
            item.params = params_input.text().split() if params_input.text() else []
            item.update_display()
            
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
                    new_item = self.add_launch_item(source_item.name, source_item.app, source_item.params)
                    
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
        new_item = self.add_launch_item(new_name, item.app, item.params.copy() if item.params else [])
        
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
            self.add_launch_item(new_name, item.app, item.params.copy() if item.params else [])
        
        # 更新配置
        if self.main_window:
            self.main_window.update_config()
            
        # 可以添加一个状态栏提示
        if self.main_window and hasattr(self.main_window, "statusBar"):
            self.main_window.statusBar().showMessage(f"已创建 {len(items_to_duplicate)} 个项目副本", 2000)