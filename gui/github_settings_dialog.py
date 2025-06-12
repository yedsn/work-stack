#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, 
                           QCheckBox, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt
from utils.gist_manager import GistManager
from utils.logger import get_logger

class GitHubSettingsDialog(QDialog):
    """GitHub 设置对话框 (已过时，保留用于兼容性)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.gist_manager = GistManager()
        
        self.setWindowTitle("GitHub Gist 同步设置 (已过时)")
        self.setMinimumWidth(500)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        
        # 添加过时警告
        warning_label = QLabel(
            """<p style="font-size:14px; color:red; font-weight:bold;">
            此设置页面已过时，请使用新的同步设置！
            </p>
            <p style="font-size:12px; color:#666;">
            该页面仅保留用于兼容性目的，未来版本将删除。
            请从主菜单中选择"同步设置"以使用新的统一设置界面。
            </p>
            """
        )
        warning_label.setTextFormat(Qt.RichText)
        warning_label.setWordWrap(True)
        main_layout.addWidget(warning_label)
        
        # 转到新设置按钮
        goto_new_settings = QPushButton("转到新的同步设置")
        goto_new_settings.clicked.connect(self.goto_sync_settings)
        main_layout.addWidget(goto_new_settings)
        
        # 添加分隔线
        separator = QLabel("<hr>")
        separator.setTextFormat(Qt.RichText)
        main_layout.addWidget(separator)
        
        # 创建表单布局
        form_layout = QFormLayout()
        
        # 启用复选框
        self.enabled_checkbox = QCheckBox("启用 GitHub Gist 同步")
        form_layout.addRow("启用:", self.enabled_checkbox)
        
        # Token 输入框
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)  # 设置为密码模式
        self.token_input.setPlaceholderText("输入GitHub个人访问令牌")
        form_layout.addRow("GitHub Token:", self.token_input)
        
        # Gist ID 输入框
        gist_layout = QHBoxLayout()
        self.gist_id_input = QLineEdit()
        self.gist_id_input.setPlaceholderText("输入已有Gist ID或创建新的Gist")
        gist_layout.addWidget(self.gist_id_input)
        
        # 创建新Gist按钮
        create_gist_button = QPushButton("创建新Gist")
        create_gist_button.clicked.connect(self.create_new_gist)
        gist_layout.addWidget(create_gist_button)
        
        form_layout.addRow("Gist ID:", gist_layout)
        
        # 文件名输入框
        self.filename_input = QLineEdit("launcher_config.json")
        form_layout.addRow("配置文件名:", self.filename_input)
        
        # 自动同步选项
        self.auto_sync_checkbox = QCheckBox("启动时自动同步配置")
        form_layout.addRow("自动同步:", self.auto_sync_checkbox)
        
        # 添加表单到主布局
        main_layout.addLayout(form_layout)
        
        # 测试连接按钮
        test_button = QPushButton("测试连接")
        test_button.clicked.connect(self.test_connection)
        main_layout.addWidget(test_button)
        
        # 同步操作组
        sync_group = QGroupBox("同步操作")
        sync_layout = QHBoxLayout()
        
        # 上传按钮
        upload_button = QPushButton("上传配置到同步服务")
        upload_button.clicked.connect(self.upload_config)
        sync_layout.addWidget(upload_button)
        
        # 下载按钮
        download_button = QPushButton("从同步服务下载配置")
        download_button.clicked.connect(self.download_config)
        sync_layout.addWidget(download_button)
        
        sync_group.setLayout(sync_layout)
        main_layout.addWidget(sync_group)
        
        # 添加确定和取消按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)
    
    def load_settings(self):
        """加载现有设置"""
        try:
            # 从GistManager获取当前设置
            self.enabled_checkbox.setChecked(self.gist_manager.enabled)
            self.token_input.setText(self.gist_manager.token)
            self.gist_id_input.setText(self.gist_manager.gist_id)
            self.filename_input.setText(self.gist_manager.filename)
            self.auto_sync_checkbox.setChecked(self.gist_manager.auto_sync)
        except Exception as e:
            self.logger.error(f"加载GitHub设置时出错: {e}")
    
    def save_settings(self):
        """保存设置"""
        try:
            enabled = self.enabled_checkbox.isChecked()
            token = self.token_input.text().strip()
            gist_id = self.gist_id_input.text().strip()
            filename = self.filename_input.text().strip()
            auto_sync = self.auto_sync_checkbox.isChecked()
            
            # 验证输入
            if enabled:
                if not token:
                    QMessageBox.warning(self, "输入错误", "请输入GitHub Token")
                    return
                
                if not gist_id:
                    QMessageBox.warning(self, "输入错误", "请输入Gist ID或创建新的Gist")
                    return
                
                if not filename:
                    QMessageBox.warning(self, "输入错误", "请输入配置文件名")
                    return
            
            # 保存配置
            self.gist_manager.set_config(enabled, token, gist_id, filename, auto_sync)
            QMessageBox.information(self, "保存成功", "GitHub同步设置已保存")
            self.accept()
        except Exception as e:
            self.logger.error(f"保存GitHub设置时出错: {e}")
            QMessageBox.critical(self, "保存失败", f"保存设置时出错: {e}")
    
    def test_connection(self):
        """测试GitHub连接"""
        try:
            # 使用当前输入的值进行测试
            enabled = self.enabled_checkbox.isChecked()
            token = self.token_input.text().strip()
            gist_id = self.gist_id_input.text().strip()
            
            if not enabled:
                QMessageBox.warning(self, "无法测试", "请先启用 GitHub Gist 同步")
                return
                
            if not token or not gist_id:
                QMessageBox.warning(self, "无法测试", "请先输入Token和Gist ID")
                return
            
            # 创建临时GistManager进行测试
            temp_manager = GistManager()
            temp_manager.enabled = enabled
            temp_manager.token = token
            temp_manager.gist_id = gist_id
            
            # 测试连接
            success, message = temp_manager.test_connection()
            
            if success:
                QMessageBox.information(self, "连接成功", message)
            else:
                QMessageBox.warning(self, "连接失败", message)
        except Exception as e:
            self.logger.error(f"测试GitHub连接时出错: {e}")
            QMessageBox.critical(self, "测试失败", f"测试连接时出错: {e}")
    
    def create_new_gist(self):
        """创建新的Gist"""
        try:
            enabled = self.enabled_checkbox.isChecked()
            token = self.token_input.text().strip()
            
            if not enabled:
                QMessageBox.warning(self, "无法创建", "请先启用 GitHub Gist 同步")
                return
                
            if not token:
                QMessageBox.warning(self, "无法创建", "请先输入GitHub Token")
                return
            
            # 创建临时GistManager
            temp_manager = GistManager()
            temp_manager.enabled = enabled
            temp_manager.token = token
            
            # 获取Gist描述
            description = "应用启动器配置"
            
            # 创建新Gist
            success, message, new_gist_id = temp_manager.create_new_gist(description)
            
            if success and new_gist_id:
                self.gist_id_input.setText(new_gist_id)
                QMessageBox.information(self, "创建成功", f"新的Gist已创建，ID: {new_gist_id}")
            else:
                QMessageBox.warning(self, "创建失败", message)
        except Exception as e:
            self.logger.error(f"创建新Gist时出错: {e}")
            QMessageBox.critical(self, "创建失败", f"创建新Gist时出错: {e}")
    
    def upload_config(self):
        """上传配置到同步服务"""
        try:
            enabled = self.enabled_checkbox.isChecked()
            token = self.token_input.text().strip()
            gist_id = self.gist_id_input.text().strip()
            filename = self.filename_input.text().strip()
            
            if not enabled:
                QMessageBox.warning(self, "无法上传", "请先启用同步服务")
                return
                
            if not token or not gist_id:
                QMessageBox.warning(self, "无法上传", "请先输入Token和Gist ID")
                return
            
            # 创建临时GistManager
            temp_manager = GistManager()
            temp_manager.enabled = enabled
            temp_manager.token = token
            temp_manager.gist_id = gist_id
            temp_manager.filename = filename
            
            # 上传配置
            success, message = temp_manager.upload_config()
            
            if success:
                QMessageBox.information(self, "上传成功", message)
            else:
                QMessageBox.warning(self, "上传失败", message)
        except Exception as e:
            self.logger.error(f"上传配置到同步服务时出错: {e}")
            QMessageBox.critical(self, "上传失败", f"上传配置时出错: {e}")
    
    def download_config(self):
        """从同步服务下载配置"""
        try:
            enabled = self.enabled_checkbox.isChecked()
            token = self.token_input.text().strip()
            gist_id = self.gist_id_input.text().strip()
            filename = self.filename_input.text().strip()
            
            if not enabled:
                QMessageBox.warning(self, "无法下载", "请先启用同步服务")
                return
                
            if not token or not gist_id:
                QMessageBox.warning(self, "无法下载", "请先输入Token和Gist ID")
                return
            
            # 创建临时GistManager
            temp_manager = GistManager()
            temp_manager.enabled = enabled
            temp_manager.token = token
            temp_manager.gist_id = gist_id
            temp_manager.filename = filename
            
            # 确认是否要覆盖本地配置
            confirm = QMessageBox.question(
                self, "确认下载", 
                "从同步服务下载配置将覆盖本地配置，是否继续？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                # 下载配置
                success, message, config_data = temp_manager.download_config()
                
                if success and config_data:
                    # 保存配置
                    from utils.config_manager import save_config
                    save_config(config_data)
                    QMessageBox.information(self, "下载成功", f"{message}\n配置已应用")
                else:
                    QMessageBox.warning(self, "下载失败", message)
        except Exception as e:
            self.logger.error(f"从同步服务下载配置时出错: {e}")
            QMessageBox.critical(self, "下载失败", f"下载配置时出错: {e}")
    
    def goto_sync_settings(self):
        """转到新的同步设置对话框"""
        try:
            # 关闭当前对话框
            self.accept()
            
            # 打开新的同步设置对话框
            from gui.sync_settings_dialog import SyncSettingsDialog
            dialog = SyncSettingsDialog(self.parent())
            dialog.exec_()
        except Exception as e:
            self.logger.error(f"转到同步设置时出错: {e}")
            QMessageBox.critical(self, "错误", f"转到同步设置时出错: {e}") 