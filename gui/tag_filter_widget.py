#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
标签过滤器组件

在主窗口中提供标签过滤功能，支持多选和过滤模式切换
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                           QPushButton, QCheckBox, QButtonGroup, QRadioButton,
                           QScrollArea, QFrame, QGroupBox, QToolButton, QMenu)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from utils.logger import get_logger

logger = get_logger()


class TagFilterWidget(QWidget):
    """标签过滤器组件"""
    
    filter_changed = pyqtSignal(list, str)  # 选中标签列表，过滤模式
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.available_tags = []
        self.selected_tags = []
        self.filter_mode = "OR"
        self.tag_checkboxes = {}
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # 标签过滤标题
        header_layout = QHBoxLayout()
        
        filter_label = QLabel("标签过滤:")
        filter_font = QFont()
        filter_font.setBold(True)
        filter_label.setFont(filter_font)
        header_layout.addWidget(filter_label)
        
        header_layout.addStretch()
        
        # 清除过滤按钮
        self.clear_btn = QPushButton("清除")
        self.clear_btn.setMaximumHeight(24)
        self.clear_btn.setMaximumWidth(50)
        self.clear_btn.clicked.connect(self.clear_filters)
        header_layout.addWidget(self.clear_btn)
        
        # 全选按钮
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setMaximumHeight(24)
        self.select_all_btn.setMaximumWidth(50)
        self.select_all_btn.clicked.connect(self.select_all_tags)
        header_layout.addWidget(self.select_all_btn)
        
        layout.addLayout(header_layout)
        
        # 过滤模式选择
        mode_layout = QHBoxLayout()
        mode_label = QLabel("过滤模式:")
        mode_layout.addWidget(mode_label)
        
        self.mode_group = QButtonGroup()
        
        self.or_radio = QRadioButton("或 (OR)")
        self.or_radio.setToolTip("显示包含任一选中标签的项目")
        self.or_radio.setChecked(True)
        self.or_radio.toggled.connect(self.on_mode_changed)
        self.mode_group.addButton(self.or_radio)
        mode_layout.addWidget(self.or_radio)
        
        self.and_radio = QRadioButton("且 (AND)")
        self.and_radio.setToolTip("只显示包含所有选中标签的项目")
        self.and_radio.toggled.connect(self.on_mode_changed)
        self.mode_group.addButton(self.and_radio)
        mode_layout.addWidget(self.and_radio)
        
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # 标签选择区域
        self.tags_group = QGroupBox("可用标签")
        tags_layout = QVBoxLayout(self.tags_group)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setMaximumHeight(120)
        
        # 标签容器
        self.tags_widget = QWidget()
        self.tags_layout = QVBoxLayout(self.tags_widget)
        self.tags_layout.setContentsMargins(5, 5, 5, 5)
        self.tags_layout.setSpacing(3)
        
        scroll_area.setWidget(self.tags_widget)
        tags_layout.addWidget(scroll_area)
        
        layout.addWidget(self.tags_group)
        
        # 状态信息
        self.status_label = QLabel("未选择标签")
        self.status_label.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        # 初始化状态
        self.update_status()
    
    def set_available_tags(self, tags):
        """设置可用标签列表"""
        self.available_tags = tags.copy() if tags else []
        self.refresh_tag_checkboxes()
    
    def refresh_tag_checkboxes(self):
        """刷新标签复选框"""
        # 清除现有复选框
        for checkbox in self.tag_checkboxes.values():
            checkbox.setParent(None)
        self.tag_checkboxes.clear()
        
        # 创建新的复选框
        for tag in self.available_tags:
            checkbox = QCheckBox(tag)
            checkbox.setChecked(tag in self.selected_tags)
            checkbox.stateChanged.connect(self.on_tag_selection_changed)
            self.tag_checkboxes[tag] = checkbox
            self.tags_layout.addWidget(checkbox)
        
        # 添加弹性空间
        self.tags_layout.addStretch()
        
        self.update_status()
    
    def set_filter_state(self, selected_tags, filter_mode):
        """设置过滤状态"""
        self.selected_tags = selected_tags.copy() if selected_tags else []
        self.filter_mode = filter_mode
        
        # 更新UI状态
        if filter_mode == "AND":
            self.and_radio.setChecked(True)
        else:
            self.or_radio.setChecked(True)
        
        # 更新复选框状态
        for tag, checkbox in self.tag_checkboxes.items():
            checkbox.setChecked(tag in self.selected_tags)
        
        self.update_status()
    
    def get_filter_state(self):
        """获取当前过滤状态"""
        return self.selected_tags.copy(), self.filter_mode
    
    def on_tag_selection_changed(self):
        """标签选择状态改变时的处理"""
        self.selected_tags = []
        for tag, checkbox in self.tag_checkboxes.items():
            if checkbox.isChecked():
                self.selected_tags.append(tag)
        
        self.update_status()
        self.filter_changed.emit(self.selected_tags, self.filter_mode)
    
    def on_mode_changed(self):
        """过滤模式改变时的处理"""
        if self.or_radio.isChecked():
            self.filter_mode = "OR"
        else:
            self.filter_mode = "AND"
        
        self.update_status()
        if self.selected_tags:  # 只有在有选中标签时才发射信号
            self.filter_changed.emit(self.selected_tags, self.filter_mode)
    
    def clear_filters(self):
        """清除所有过滤器"""
        self.selected_tags = []
        for checkbox in self.tag_checkboxes.values():
            checkbox.setChecked(False)
        
        self.update_status()
        self.filter_changed.emit(self.selected_tags, self.filter_mode)
    
    def select_all_tags(self):
        """选择所有标签"""
        self.selected_tags = self.available_tags.copy()
        for checkbox in self.tag_checkboxes.values():
            checkbox.setChecked(True)
        
        self.update_status()
        self.filter_changed.emit(self.selected_tags, self.filter_mode)
    
    def update_status(self):
        """更新状态信息"""
        if not self.selected_tags:
            self.status_label.setText("未选择标签 - 显示所有项目")
        else:
            mode_text = "且" if self.filter_mode == "AND" else "或"
            tags_text = "、".join(self.selected_tags)
            self.status_label.setText(f"已选择 {len(self.selected_tags)} 个标签 ({mode_text}): {tags_text}")
    
    def get_selected_tag_count(self):
        """获取选中标签数量"""
        return len(self.selected_tags)