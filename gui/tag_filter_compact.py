#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
紧凑型标签过滤器组件

单行显示的标签过滤器，点击打开设置对话框
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                           QDialog, QVBoxLayout, QCheckBox, QButtonGroup, 
                           QRadioButton, QScrollArea, QFrame, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from utils.logger import get_logger
from gui.base_dialog import BaseDialog

logger = get_logger()


class TagFilterSettingsDialog(BaseDialog):
    """标签过滤设置对话框"""
    
    settings_changed = pyqtSignal(list, str)  # 选中标签列表，过滤模式
    
    def __init__(self, available_tags, selected_tags, filter_mode, parent=None):
        self.available_tags = available_tags or []
        self.selected_tags = selected_tags or []
        self.filter_mode = filter_mode
        self.tag_checkboxes = {}
        
        super().__init__("标签过滤设置", parent, (400, 450))
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 过滤模式选择
        mode_group = QGroupBox("过滤模式")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_group = QButtonGroup()
        
        self.or_radio = QRadioButton("或 (OR) - 显示包含任一选中标签的项目")
        self.or_radio.setChecked(self.filter_mode == "OR")
        self.mode_group.addButton(self.or_radio)
        mode_layout.addWidget(self.or_radio)
        
        self.and_radio = QRadioButton("且 (AND) - 只显示包含所有选中标签的项目")
        self.and_radio.setChecked(self.filter_mode == "AND")
        self.mode_group.addButton(self.and_radio)
        mode_layout.addWidget(self.and_radio)
        
        layout.addWidget(mode_group)
        
        # 标签选择区域
        tags_group = QGroupBox("选择标签")
        tags_layout = QVBoxLayout(tags_group)
        
        # 快捷操作按钮
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all_tags)
        button_layout.addWidget(select_all_btn)
        
        clear_btn = QPushButton("清除")
        clear_btn.clicked.connect(self.clear_all_tags)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        tags_layout.addLayout(button_layout)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setMaximumHeight(200)
        
        # 标签容器
        tags_widget = QWidget()
        tags_widget_layout = QVBoxLayout(tags_widget)
        tags_widget_layout.setSpacing(5)
        
        # 创建标签复选框
        for tag in self.available_tags:
            checkbox = QCheckBox(tag)
            checkbox.setChecked(tag in self.selected_tags)
            self.tag_checkboxes[tag] = checkbox
            tags_widget_layout.addWidget(checkbox)
        
        scroll_area.setWidget(tags_widget)
        tags_layout.addWidget(scroll_area)
        
        layout.addWidget(tags_group)
        
        # 状态显示
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #666666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 更新状态显示
        self.update_status()
    
    def get_selected_tags(self):
        """获取选中的标签"""
        selected = []
        for tag, checkbox in self.tag_checkboxes.items():
            if checkbox.isChecked():
                selected.append(tag)
        return selected
    
    def get_filter_mode(self):
        """获取过滤模式"""
        return "AND" if self.and_radio.isChecked() else "OR"
    
    def select_all_tags(self):
        """全选标签"""
        for checkbox in self.tag_checkboxes.values():
            checkbox.setChecked(True)
        self.update_status()
    
    def clear_all_tags(self):
        """清除所有标签"""
        for checkbox in self.tag_checkboxes.values():
            checkbox.setChecked(False)
        self.update_status()
    
    def update_status(self):
        """更新状态显示"""
        selected_tags = self.get_selected_tags()
        if not selected_tags:
            self.status_label.setText("未选择标签 - 将显示所有项目")
        else:
            mode_text = "且" if self.get_filter_mode() == "AND" else "或"
            tags_text = "、".join(selected_tags)
            self.status_label.setText(f"已选择 {len(selected_tags)} 个标签 ({mode_text}): {tags_text}")
    
    def accept(self):
        """确定按钮处理"""
        selected_tags = self.get_selected_tags()
        filter_mode = self.get_filter_mode()
        self.settings_changed.emit(selected_tags, filter_mode)
        super().accept()


class TagFilterCompact(QWidget):
    """紧凑型标签过滤器组件"""
    
    filter_changed = pyqtSignal(list, str)  # 选中标签列表，过滤模式
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.available_tags = []
        self.selected_tags = []
        self.filter_mode = "OR"
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(10)
        
        # 标签过滤标题
        filter_icon = QLabel("🏷")
        filter_icon.setStyleSheet("font-size: 14px;")
        layout.addWidget(filter_icon)
        
        filter_label = QLabel("标签过滤:")
        filter_font = QFont()
        filter_font.setBold(True)
        filter_label.setFont(filter_font)
        layout.addWidget(filter_label)
        
        # 状态显示标签
        self.status_label = QLabel("未设置")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666666;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # 设置按钮
        self.settings_btn = QPushButton("设置")
        self.settings_btn.setMaximumHeight(24)
        self.settings_btn.setMaximumWidth(50)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        layout.addWidget(self.settings_btn)
        
        # 快速清除按钮
        self.clear_btn = QPushButton("清除")
        self.clear_btn.setMaximumHeight(24)
        self.clear_btn.setMaximumWidth(50)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c1170a;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_filters)
        layout.addWidget(self.clear_btn)
        
        layout.addStretch()
        
        # 初始化状态
        self.update_status_display()
    
    def set_available_tags(self, tags):
        """设置可用标签列表"""
        self.available_tags = tags.copy() if tags else []
        self.update_status_display()
    
    def set_filter_state(self, selected_tags, filter_mode):
        """设置过滤状态"""
        self.selected_tags = selected_tags.copy() if selected_tags else []
        self.filter_mode = filter_mode
        self.update_status_display()
    
    def get_filter_state(self):
        """获取当前过滤状态"""
        return self.selected_tags.copy(), self.filter_mode
    
    def show_settings_dialog(self):
        """显示设置对话框"""
        try:
            dialog = TagFilterSettingsDialog(
                self.available_tags, 
                self.selected_tags, 
                self.filter_mode, 
                self
            )
            
            dialog.settings_changed.connect(self.on_settings_changed)
            
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"显示标签过滤设置对话框时出错: {e}")
    
    def on_settings_changed(self, selected_tags, filter_mode):
        """设置更改时的处理"""
        self.selected_tags = selected_tags
        self.filter_mode = filter_mode
        self.update_status_display()
        self.filter_changed.emit(self.selected_tags, self.filter_mode)
    
    def clear_filters(self):
        """清除所有过滤器"""
        self.selected_tags = []
        self.update_status_display()
        self.filter_changed.emit(self.selected_tags, self.filter_mode)
    
    def update_status_display(self):
        """更新状态显示"""
        if not self.selected_tags:
            self.status_label.setText("未设置过滤")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #999999;
                    background-color: #f9f9f9;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
            """)
        else:
            mode_text = "且" if self.filter_mode == "AND" else "或"
            if len(self.selected_tags) == 1:
                status_text = f"{self.selected_tags[0]}"
            elif len(self.selected_tags) <= 3:
                status_text = f"{len(self.selected_tags)}个标签 ({mode_text}): {'、'.join(self.selected_tags)}"
            else:
                preview_tags = self.selected_tags[:2]
                status_text = f"{len(self.selected_tags)}个标签 ({mode_text}): {'、'.join(preview_tags)}..."
            
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #1976d2;
                    background-color: #e3f2fd;
                    border: 1px solid #bbdefb;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
    
    def get_selected_tag_count(self):
        """获取选中标签数量"""
        return len(self.selected_tags)