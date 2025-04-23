#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QApplication, QFrame, QGraphicsDropShadowEffect, QMenu)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag, QPixmap, QFont, QCursor, QColor
from utils.app_launcher import open_app
from gui.flow_layout import FlowLayout

class ParamLabel(QLabel):
    """可点击的参数标签"""
    def __init__(self, param, parent=None):
        super().__init__(param, parent)
        self.param = param
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet("""
            QLabel {
                color: #0066cc;
                text-decoration: underline;
                padding: 2px 5px;
                background-color: #f0f0f0;
                border-radius: 3px;
                margin-right: 5px;
            }
            QLabel:hover {
                background-color: #e0e0e0;
            }
        """)

class LaunchItem(QFrame):
    """启动项组件"""
    def __init__(self, name, app, params=None, source_category=None):
        super().__init__()
        self.name = name
        self.app = app
        self.params = params or []
        self.category_tab = None
        self.source_category = source_category  # 添加所属分类属性
        self.is_selected = False  # 添加选中状态
        
        # 打印调试信息
        print(f"创建启动项: 名称={name}, 应用={app}, 参数={params}")
        
        # 设置为卡片样式
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))  # 半透明黑色
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(8)
        
        # 创建标题布局
        title_layout = QHBoxLayout()
        
        # 创建标题标签
        title_label = QLabel(name)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        
        # 添加到标题布局
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 添加标题布局到主布局
        main_layout.addLayout(title_layout)
        
        # 应用信息
        app_name = os.path.basename(app) if os.path.isabs(app) else app
        app_label = QLabel(f"应用: {app_name}")
        app_label.setStyleSheet("color: gray;")
        main_layout.addWidget(app_label)
        
        # 如果有所属分类且不是在原分类中显示，则显示分类信息
        if source_category:
            category_label = QLabel(f"分类: {source_category}")
            category_label.setStyleSheet("color: #4a86e8; font-style: italic;")
            main_layout.addWidget(category_label)
        
        # 参数信息
        if params:
            params_layout = QVBoxLayout()
            params_layout.setSpacing(5)
            params_layout.setContentsMargins(0, 5, 0, 5)
            
            params_header = QHBoxLayout()
            params_label = QLabel("参数:")
            params_label.setStyleSheet("color: gray;")
            params_header.addWidget(params_label)
            params_header.addStretch()
            params_layout.addLayout(params_header)
            
            # 创建流式布局容器
            flow_layout = FlowLayout()
            flow_layout.setSpacing(5)
            
            # 添加每个参数作为可点击的标签
            for param in params:
                param_label = ParamLabel(str(param))
                param_label.mousePressEvent = lambda event, p=param: self.launch_with_param(p)
                flow_layout.addWidget(param_label)
            
            # 将流式布局添加到参数布局
            params_layout.addLayout(flow_layout)
            main_layout.addLayout(params_layout)
        
        # 设置样式
        self.setStyleSheet("""
            LaunchItem {
                background-color: white;
                border: 1px solid #dddddd;
                border-radius: 5px;
            }
            LaunchItem:hover {
                background-color: #f0f8ff;
                border: 1px solid #4a86e8;
            }
        """)
        
        # 设置固定高度
        self.setMinimumHeight(100)
        
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        # 设置提示
        self.setToolTip("双击启动应用")
        
        # 设置光标
        self.setCursor(QCursor(Qt.PointingHandCursor))
    
    def set_category_tab(self, category_tab):
        """设置所属分类标签页"""
        self.category_tab = category_tab
    
    def update_display(self):
        """更新显示内容"""
        # 更新标题
        title_layout = self.layout().itemAt(0).layout()
        title_label = title_layout.itemAt(0).widget()
        title_label.setText(self.name)
        
        # 更新应用信息
        app_label = self.layout().itemAt(1).widget()
        app_name = os.path.basename(self.app) if os.path.isabs(self.app) else self.app
        app_label.setText(f"应用: {app_name}")
        
        # 更新参数信息 - 需要重建参数布局
        if self.layout().count() > 2:
            # 移除旧的参数布局
            old_params_layout = self.layout().itemAt(2)
            if old_params_layout:
                # 删除旧布局中的所有控件
                self._clear_layout(old_params_layout.layout())
                # 从主布局中移除
                self.layout().removeItem(old_params_layout)
        
        # 如果有参数，创建新的参数布局
        if self.params:
            params_layout = QVBoxLayout()
            params_layout.setSpacing(5)
            params_layout.setContentsMargins(0, 5, 0, 5)
            
            params_header = QHBoxLayout()
            params_label = QLabel("参数:")
            params_label.setStyleSheet("color: gray;")
            params_header.addWidget(params_label)
            params_header.addStretch()
            params_layout.addLayout(params_header)
            
            # 创建流式布局容器
            flow_layout = FlowLayout()
            flow_layout.setSpacing(5)
            
            # 添加每个参数作为可点击的标签
            for param in self.params:
                param_label = ParamLabel(str(param))
                param_label.mousePressEvent = lambda event, p=param: self.launch_with_param(p)
                flow_layout.addWidget(param_label)
            
            # 将流式布局添加到参数布局
            params_layout.addLayout(flow_layout)
            self.layout().addLayout(params_layout)
    
    def _clear_layout(self, layout):
        """清空布局中的所有控件"""
        if layout is None:
            return
        
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            
            if widget:
                widget.deleteLater()
            else:
                # 如果是子布局，递归清空
                self._clear_layout(item.layout())
    
    def launch(self):
        """启动应用"""
        try:
            open_app(self.app, self.params)
            print(f"成功启动应用: {self.app}")
        except Exception as e:
            print(f"启动应用失败: {self.app}, 错误: {str(e)}")
    
    def launch_with_param(self, param):
        """使用单个参数启动应用"""
        try:
            from utils.app_launcher import open_app
            open_app(self.app, [param])
            print(f"成功启动应用(单参数): {self.app} {param}")
        except Exception as e:
            print(f"启动应用失败(单参数): {self.app} {param}, 错误: {str(e)}")
    
    def mouseDoubleClickEvent(self, event):
        """双击启动应用"""
        if event.button() == Qt.LeftButton:
            self.launch()
            event.accept()
    
    # 鼠标事件处理
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            
            # 处理选中状态
            if QApplication.keyboardModifiers() & Qt.ControlModifier:
                # Ctrl+点击，切换选中状态
                self.toggle_selected()
            elif QApplication.keyboardModifiers() & Qt.ShiftModifier:
                # Shift+点击，选择范围
                if self.category_tab:
                    # 找到最后一个选中的项目
                    last_selected = None
                    if self.category_tab.selected_items:
                        last_selected = self.category_tab.selected_items[-1]
                    
                    if last_selected:
                        # 找到当前项目和最后选中项目的索引
                        current_index = -1
                        last_index = -1
                        items = []
                        
                        # 收集所有项目并找到索引
                        for i in range(self.category_tab.content_layout.count()):
                            widget = self.category_tab.content_layout.itemAt(i).widget()
                            if isinstance(widget, LaunchItem):
                                items.append(widget)
                                if widget == self:
                                    current_index = len(items) - 1
                                if widget == last_selected:
                                    last_index = len(items) - 1
                        
                        if current_index != -1 and last_index != -1:
                            # 确定选择范围
                            start_index = min(current_index, last_index)
                            end_index = max(current_index, last_index)
                            
                            # 选择范围内的所有项目
                            for i in range(start_index, end_index + 1):
                                items[i].set_selected(True)
                    else:
                        # 如果没有已选中的项目，只选中当前项目
                        self.set_selected(True)
            else:
                # 普通点击，清除其他选中项，选中当前项
                if self.category_tab:
                    for item in self.category_tab.selected_items:
                        if item != self:
                            item.set_selected(False)
                    self.category_tab.selected_items = []
                self.set_selected(True)
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        
        # 检查是否达到拖动阈值
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        
        # 创建拖放对象
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # 设置MIME类型和数据
        mime_data.setData("application/x-launch-item", b"launch-item")
        drag.setMimeData(mime_data)
        
        # 设置拖动时的图像
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        
        # 执行拖放操作
        result = drag.exec_(Qt.MoveAction)
    
    def toggle_selected(self):
        """切换选中状态"""
        self.set_selected(not self.is_selected)
    
    def set_selected(self, selected):
        """设置选中状态"""
        self.is_selected = selected
        
        if selected:
            self.setStyleSheet("""
                LaunchItem {
                    background-color: #e6f0ff;
                    border: 2px solid #4a86e8;
                    border-radius: 5px;
                }
            """)
            
            # 添加到选中列表
            if self.category_tab and self not in self.category_tab.selected_items:
                self.category_tab.selected_items.append(self)
        else:
            self.setStyleSheet("""
                LaunchItem {
                    background-color: white;
                    border: 1px solid #dddddd;
                    border-radius: 5px;
                }
                LaunchItem:hover {
                    background-color: #f0f8ff;
                    border: 1px solid #4a86e8;
                }
            """)
            
            # 从选中列表中移除
            if self.category_tab and self in self.category_tab.selected_items:
                self.category_tab.selected_items.remove(self)
    
    def contextMenuEvent(self, event):
        """右键菜单事件"""
        # 如果没有选中，先选中当前项
        if not self.is_selected:
            # 清除其他选中项
            if self.category_tab:
                for item in self.category_tab.selected_items:
                    item.set_selected(False)
                self.category_tab.selected_items = []
            
            # 选中当前项
            self.set_selected(True)
        
        # 调用标签页的右键菜单显示方法
        if self.category_tab:
            self.category_tab.show_item_context_menu(event.pos(), self)
        
        menu = QMenu(self)
        menu.exec_(event.globalPos()) 