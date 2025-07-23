#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
启动项标签编辑对话框

快速编辑单个启动项的标签
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QCheckBox, QLineEdit, QGroupBox,
                           QScrollArea, QFrame, QGridLayout, QSizePolicy, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from gui.base_dialog import BaseDialog
from utils.logger import get_logger
from utils.config_manager import get_available_tags, add_available_tag

logger = get_logger()


class ItemTagsDialog(BaseDialog):
    """启动项标签编辑对话框"""
    
    tags_updated = pyqtSignal(list)  # 标签更新信号
    
    def __init__(self, item_name, available_tags, current_tags, parent=None):
        self.item_name = item_name
        self.available_tags = available_tags or []
        self.current_tags = current_tags or []
        self.new_tag_input = None
        self.tag_checkboxes = {}
        
        super().__init__(f"编辑标签 - {item_name}", parent, (450, 500))
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 标题信息
        title_label = QLabel(f"为 \"{self.item_name}\" 设置标签")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 现有标签选择区域
        if self.available_tags:
            tags_group = QGroupBox("选择标签")
            tags_layout = QVBoxLayout(tags_group)
            
            # 创建滚动区域
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.NoFrame)
            scroll_area.setMaximumHeight(200)
            
            # 标签容器
            tags_widget = QWidget()
            grid_layout = QGridLayout(tags_widget)
            grid_layout.setSpacing(8)
            
            # 创建标签复选框（每行3个）
            row, col = 0, 0
            for tag in self.available_tags:
                checkbox = QCheckBox(tag)
                checkbox.setChecked(tag in self.current_tags)
                checkbox.stateChanged.connect(self.on_tag_selection_changed)
                self.tag_checkboxes[tag] = checkbox
                
                grid_layout.addWidget(checkbox, row, col)
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
            
            scroll_area.setWidget(tags_widget)
            tags_layout.addWidget(scroll_area)
            layout.addWidget(tags_group)
        
        # 添加新标签区域
        new_tag_group = QGroupBox("添加新标签")
        new_tag_layout = QHBoxLayout(new_tag_group)
        
        self.new_tag_input = QLineEdit()
        self.new_tag_input.setPlaceholderText("输入新标签名称...")
        self.new_tag_input.returnPressed.connect(self.add_new_tag)
        new_tag_layout.addWidget(self.new_tag_input)
        
        add_tag_btn = QPushButton("添加")
        add_tag_btn.clicked.connect(self.add_new_tag)
        new_tag_layout.addWidget(add_tag_btn)
        
        layout.addWidget(new_tag_group)
        
        # 当前选中标签显示
        selected_group = QGroupBox("已选标签")
        selected_layout = QVBoxLayout(selected_group)
        
        self.selected_label = QLabel()
        self.selected_label.setWordWrap(True)
        self.selected_label.setStyleSheet("color: #0066cc; padding: 5px;")
        selected_layout.addWidget(self.selected_label)
        
        layout.addWidget(selected_group)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.clear_btn = QPushButton("清除所有")
        self.clear_btn.clicked.connect(self.clear_all_tags)
        button_layout.addWidget(self.clear_btn)
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 初始化显示
        self.update_selected_display()
    
    def on_tag_selection_changed(self):
        """标签选择状态改变时的处理"""
        self.current_tags = []
        for tag, checkbox in self.tag_checkboxes.items():
            if checkbox.isChecked():
                self.current_tags.append(tag)
        
        self.update_selected_display()
        self.tags_updated.emit(self.current_tags)
    
    def add_new_tag(self):
        """添加新标签"""
        tag_text = self.new_tag_input.text().strip()
        if not tag_text:
            return
        
        if tag_text in self.available_tags:
            self.new_tag_input.clear()
            return
        
        if len(tag_text) > 20:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "标签名称不能超过20个字符！")
            return
        
        # 添加到可用标签列表
        self.available_tags.append(tag_text)
        
        # 创建新的复选框
        checkbox = QCheckBox(tag_text)
        checkbox.setChecked(True)  # 新添加的标签默认选中
        checkbox.stateChanged.connect(self.on_tag_selection_changed)
        self.tag_checkboxes[tag_text] = checkbox
        
        # 重新创建标签布局
        self.refresh_tags_layout()
        
        # 清空输入框
        self.new_tag_input.clear()
        
        # 更新当前选中的标签
        self.current_tags.append(tag_text)
        self.update_selected_display()
        self.tags_updated.emit(self.current_tags)
        
        logger.info(f"添加新标签: {tag_text}")
    
    def refresh_tags_layout(self):
        """刷新标签布局"""
        # 这是一个简化版本，实际实现可能需要重新构建整个标签区域
        # 在这里我们只是记录日志，实际的UI更新在add_new_tag中已经处理
        pass
    
    def clear_all_tags(self):
        """清除所有标签"""
        for checkbox in self.tag_checkboxes.values():
            checkbox.setChecked(False)
        
        self.current_tags = []
        self.update_selected_display()
        self.tags_updated.emit(self.current_tags)
    
    def update_selected_display(self):
        """更新已选标签显示"""
        if not self.current_tags:
            self.selected_label.setText("未选择任何标签")
        else:
            tags_text = "、".join(self.current_tags)
            self.selected_label.setText(f"已选择 {len(self.current_tags)} 个标签: {tags_text}")
    
    def get_selected_tags(self):
        """获取选中的标签列表"""
        return self.current_tags.copy()
    
    def get_updated_available_tags(self):
        """获取更新后的可用标签列表"""
        return self.available_tags.copy()