#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
标签管理对话框

管理全局可用标签，支持添加、删除、重命名标签
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QListWidget, QListWidgetItem, QLineEdit, 
                           QMessageBox, QInputDialog, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from gui.base_dialog import BaseDialog
from utils.logger import get_logger
from utils.config_manager import get_available_tags, add_available_tag

logger = get_logger()


class TagManagerDialog(BaseDialog):
    """标签管理对话框"""
    
    tags_updated = pyqtSignal(list)  # 标签更新信号
    
    def __init__(self, available_tags, parent=None):
        self.available_tags = available_tags.copy() if available_tags else []
        self.default_tags = ["通用", "PC", "Mac笔记本", "BK100"]
        
        super().__init__("标签管理", parent, (400, 500))
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("管理全局标签")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 标签列表组
        tags_group = QGroupBox("可用标签")
        tags_layout = QVBoxLayout(tags_group)
        
        # 标签列表
        self.tags_list = QListWidget()
        self.tags_list.setMaximumHeight(250)
        self.refresh_tags_list()
        tags_layout.addWidget(self.tags_list)
        
        # 标签操作按钮
        tag_buttons_layout = QHBoxLayout()
        
        self.add_tag_btn = QPushButton("添加标签")
        self.add_tag_btn.clicked.connect(self.add_tag)
        tag_buttons_layout.addWidget(self.add_tag_btn)
        
        self.rename_tag_btn = QPushButton("重命名")
        self.rename_tag_btn.clicked.connect(self.rename_tag)
        tag_buttons_layout.addWidget(self.rename_tag_btn)
        
        self.delete_tag_btn = QPushButton("删除标签")
        self.delete_tag_btn.clicked.connect(self.delete_tag)
        tag_buttons_layout.addWidget(self.delete_tag_btn)
        
        tags_layout.addLayout(tag_buttons_layout)
        layout.addWidget(tags_group)
        
        # 预设标签组
        preset_group = QGroupBox("预设标签")
        preset_layout = QVBoxLayout(preset_group)
        
        preset_info = QLabel("以下是系统预设标签，建议保留：")
        preset_info.setStyleSheet("color: #666666; font-size: 11px;")
        preset_layout.addWidget(preset_info)
        
        preset_tags_text = "、".join(self.default_tags)
        preset_tags_label = QLabel(preset_tags_text)
        preset_tags_label.setWordWrap(True)
        preset_tags_label.setStyleSheet("color: #0066cc; font-weight: bold; padding: 5px;")
        preset_layout.addWidget(preset_tags_label)
        
        layout.addWidget(preset_group)
        
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
        
        # 连接选择信号
        self.tags_list.itemSelectionChanged.connect(self.update_button_states)
        self.update_button_states()
    
    def refresh_tags_list(self):
        """刷新标签列表"""
        self.tags_list.clear()
        for tag in self.available_tags:
            item = QListWidgetItem(tag)
            if tag in self.default_tags:
                item.setToolTip("系统预设标签")
                # 预设标签用不同颜色显示
                item.setData(Qt.ForegroundRole, Qt.blue)
            self.tags_list.addItem(item)
    
    def update_button_states(self):
        """更新按钮状态"""
        has_selection = bool(self.tags_list.currentItem())
        self.rename_tag_btn.setEnabled(has_selection)
        self.delete_tag_btn.setEnabled(has_selection)
    
    def add_tag(self):
        """添加新标签"""
        text, ok = QInputDialog.getText(self, "添加标签", "请输入新标签名称：")
        if ok and text.strip():
            tag_name = text.strip()
            if tag_name in self.available_tags:
                QMessageBox.warning(self, "警告", f"标签 '{tag_name}' 已存在！")
                return
            
            if len(tag_name) > 20:
                QMessageBox.warning(self, "警告", "标签名称不能超过20个字符！")
                return
            
            self.available_tags.append(tag_name)
            self.refresh_tags_list()
            self.tags_updated.emit(self.available_tags)
            logger.info(f"添加标签: {tag_name}")
    
    def rename_tag(self):
        """重命名标签"""
        current_item = self.tags_list.currentItem()
        if not current_item:
            return
        
        old_name = current_item.text()
        text, ok = QInputDialog.getText(
            self, "重命名标签", f"请输入新名称：", text=old_name
        )
        
        if ok and text.strip() and text.strip() != old_name:
            new_name = text.strip()
            if new_name in self.available_tags:
                QMessageBox.warning(self, "警告", f"标签 '{new_name}' 已存在！")
                return
            
            if len(new_name) > 20:
                QMessageBox.warning(self, "警告", "标签名称不能超过20个字符！")
                return
            
            # 更新标签列表
            index = self.available_tags.index(old_name)
            self.available_tags[index] = new_name
            self.refresh_tags_list()
            self.tags_updated.emit(self.available_tags)
            logger.info(f"重命名标签: {old_name} -> {new_name}")
    
    def delete_tag(self):
        """删除标签"""
        current_item = self.tags_list.currentItem()
        if not current_item:
            return
        
        tag_name = current_item.text()
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除标签 '{tag_name}' 吗？\n\n"
            "注意：删除后，所有使用此标签的启动项将失去该标签。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.available_tags.remove(tag_name)
            self.refresh_tags_list()
            self.tags_updated.emit(self.available_tags)
            logger.info(f"删除标签: {tag_name}")
    
    def get_updated_tags(self):
        """获取更新后的标签列表"""
        return self.available_tags