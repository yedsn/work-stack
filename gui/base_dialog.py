#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
对话框基类

提供所有对话框的通用功能和统一接口
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QDialogButtonBox
from PyQt5.QtCore import Qt
from utils.logger import get_logger


class BaseDialog(QDialog):
    """
    对话框基类
    
    提供统一的对话框创建、设置加载/保存接口
    """
    
    def __init__(self, title: str, parent=None, size=None):
        """
        初始化对话框
        
        Args:
            title: 对话框标题
            parent: 父窗口
            size: 对话框尺寸 (width, height)
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.logger = get_logger()
        
        # 设置窗口属性
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        if size:
            self.resize(*size)
        
        # 初始化UI
        self.init_ui()
        
        # 加载设置
        self.load_settings()
    
    def init_ui(self):
        """
        初始化用户界面
        
        子类必须重写此方法来创建具体的UI元素
        """
        raise NotImplementedError("子类必须实现 init_ui 方法")
    
    def create_button_box(self, buttons=None):
        """
        创建标准的按钮框
        
        Args:
            buttons: 按钮类型，默认为确定和取消
            
        Returns:
            QDialogButtonBox: 按钮框控件
        """
        if buttons is None:
            buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            
        button_box = QDialogButtonBox(buttons)
        button_box.accepted.connect(self.accept_dialog)
        button_box.rejected.connect(self.reject)
        
        return button_box
    
    def accept_dialog(self):
        """
        接受对话框
        
        保存设置并关闭对话框
        """
        try:
            if self.validate_input():
                self.save_settings()
                self.accept()
        except Exception as e:
            self.logger.error(f"保存设置时出错: {e}")
            self.show_error("保存设置失败", str(e))
    
    def load_settings(self):
        """
        加载设置
        
        子类可以重写此方法来加载特定的设置
        """
        pass
    
    def save_settings(self):
        """
        保存设置
        
        子类可以重写此方法来保存特定的设置
        """
        pass
    
    def validate_input(self) -> bool:
        """
        验证输入数据
        
        子类可以重写此方法来验证用户输入
        
        Returns:
            bool: 输入是否有效
        """
        return True
    
    def show_error(self, title: str, message: str):
        """
        显示错误消息
        
        Args:
            title: 错误标题
            message: 错误消息
        """
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, title, message)
    
    def show_info(self, title: str, message: str):
        """
        显示信息消息
        
        Args:
            title: 信息标题
            message: 信息消息
        """
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, title, message)
    
    def show_warning(self, title: str, message: str):
        """
        显示警告消息
        
        Args:
            title: 警告标题
            message: 警告消息
        """
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(self, title, message)