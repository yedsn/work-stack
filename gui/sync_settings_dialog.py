#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, 
                           QCheckBox, QGroupBox, QFormLayout,
                           QTabWidget, QWidget)
from PyQt5.QtCore import Qt
from utils.gist_manager import GistManager
from utils.open_gist_manager import OpenGistManager
from utils.webdav_manager import WebDAVManager
from utils.logger import get_logger

class SyncSettingsDialog(QDialog):
    """同步设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.github_manager = GistManager()
        self.open_gist_manager = OpenGistManager()
        self.webdav_manager = WebDAVManager()
        
        self.setWindowTitle("同步设置")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        
        # 创建标签页控件
        tab_widget = QTabWidget()
        
        # GitHub Gist 标签页
        github_tab = QWidget()
        github_layout = QVBoxLayout(github_tab)
        
        # GitHub Gist 启用复选框
        self.github_enabled_checkbox = QCheckBox("启用 GitHub Gist 同步")
        github_layout.addWidget(self.github_enabled_checkbox)
        
        # GitHub Gist 设置组
        github_group = QGroupBox("GitHub Gist 设置")
        github_form = QFormLayout(github_group)
        
        # Token 输入框
        self.github_token_input = QLineEdit()
        self.github_token_input.setEchoMode(QLineEdit.Password)  # 设置为密码模式
        self.github_token_input.setPlaceholderText("输入GitHub个人访问令牌")
        github_form.addRow("GitHub Token:", self.github_token_input)
        
        # Gist ID 输入框
        github_gist_layout = QHBoxLayout()
        self.github_gist_id_input = QLineEdit()
        self.github_gist_id_input.setPlaceholderText("输入已有Gist ID或创建新的Gist")
        github_gist_layout.addWidget(self.github_gist_id_input)
        
        # 创建新Gist按钮
        create_github_gist_button = QPushButton("创建新Gist")
        create_github_gist_button.clicked.connect(self.create_new_github_gist)
        github_gist_layout.addWidget(create_github_gist_button)
        
        github_form.addRow("Gist ID:", github_gist_layout)
        
        # 文件名输入框
        self.github_filename_input = QLineEdit("launcher_config.json")
        github_form.addRow("配置文件名:", self.github_filename_input)
        
        # 自动同步选项
        self.github_auto_sync_checkbox = QCheckBox("启动时自动同步配置")
        github_form.addRow("自动同步:", self.github_auto_sync_checkbox)
        
        github_layout.addWidget(github_group)
        
        # 测试连接按钮
        test_github_button = QPushButton("测试 GitHub Gist 连接")
        test_github_button.clicked.connect(self.test_github_connection)
        github_layout.addWidget(test_github_button)
        
        # 添加帮助信息
        github_help_text = """
        <p style="font-size:12px; color:#666;">
        <b>GitHub Gist 使用说明:</b><br>
        1. 在GitHub获取个人访问令牌(需要gist权限)<br>
        2. 输入已有Gist ID或创建新的Gist<br>
        3. 测试连接确保一切正常<br>
        4. 选择是否启用自动同步<br>
        </p>
        """
        github_help_label = QLabel(github_help_text)
        github_help_label.setTextFormat(Qt.RichText)
        github_layout.addWidget(github_help_label)
        
        # 添加弹性空间
        github_layout.addStretch()
        
        # Open Gist 标签页
        open_gist_tab = QWidget()
        open_gist_layout = QVBoxLayout(open_gist_tab)
        
        # Open Gist 启用复选框
        self.open_gist_enabled_checkbox = QCheckBox("启用 Open Gist 同步")
        open_gist_layout.addWidget(self.open_gist_enabled_checkbox)
        
        # Open Gist 设置组
        open_gist_group = QGroupBox("Open Gist 设置")
        open_gist_form = QFormLayout(open_gist_group)
        
        # API URL 输入框
        self.open_gist_api_url_input = QLineEdit()
        self.open_gist_api_url_input.setPlaceholderText("输入Open Gist API URL")
        open_gist_form.addRow("API URL:", self.open_gist_api_url_input)
        
        # API Key 输入框
        self.open_gist_api_key_input = QLineEdit()
        self.open_gist_api_key_input.setEchoMode(QLineEdit.Password)  # 设置为密码模式
        self.open_gist_api_key_input.setPlaceholderText("输入Open Gist API Key")
        open_gist_form.addRow("API Key:", self.open_gist_api_key_input)
        
        # Gist ID 输入框
        open_gist_id_layout = QHBoxLayout()
        self.open_gist_id_input = QLineEdit()
        self.open_gist_id_input.setPlaceholderText("输入已有Gist ID或创建新的Gist")
        open_gist_id_layout.addWidget(self.open_gist_id_input)
        
        # 创建新Gist按钮
        create_open_gist_button = QPushButton("创建新Gist")
        create_open_gist_button.clicked.connect(self.create_new_open_gist)
        open_gist_id_layout.addWidget(create_open_gist_button)
        
        open_gist_form.addRow("Gist ID:", open_gist_id_layout)
        
        # 文件名输入框
        self.open_gist_filename_input = QLineEdit("launcher_config.json")
        open_gist_form.addRow("配置文件名:", self.open_gist_filename_input)
        
        # 自动同步选项
        self.open_gist_auto_sync_checkbox = QCheckBox("启动时自动同步配置")
        open_gist_form.addRow("自动同步:", self.open_gist_auto_sync_checkbox)
        
        open_gist_layout.addWidget(open_gist_group)
        
        # 测试连接按钮
        test_open_gist_button = QPushButton("测试 Open Gist 连接")
        test_open_gist_button.clicked.connect(self.test_open_gist_connection)
        open_gist_layout.addWidget(test_open_gist_button)
        
        # 添加帮助信息
        open_gist_help_text = """
        <p style="font-size:12px; color:#666;">
        <b>Open Gist 使用说明:</b><br>
        1. 输入Open Gist服务的API URL和API Key<br>
        2. 输入已有Gist ID或创建新的Gist<br>
        3. 测试连接确保一切正常<br>
        4. 选择是否启用自动同步<br>
        </p>
        """
        open_gist_help_label = QLabel(open_gist_help_text)
        open_gist_help_label.setTextFormat(Qt.RichText)
        open_gist_layout.addWidget(open_gist_help_label)
        
        # 添加弹性空间
        open_gist_layout.addStretch()
        
        # WebDAV 标签页
        webdav_tab = QWidget()
        webdav_layout = QVBoxLayout(webdav_tab)
        
        # WebDAV 启用复选框
        self.webdav_enabled_checkbox = QCheckBox("启用 WebDAV 同步")
        webdav_layout.addWidget(self.webdav_enabled_checkbox)
        
        # WebDAV 设置组
        webdav_group = QGroupBox("WebDAV 设置")
        webdav_form = QFormLayout(webdav_group)
        
        # 服务器URL输入框
        self.webdav_server_url_input = QLineEdit()
        self.webdav_server_url_input.setPlaceholderText("输入WebDAV服务器URL（例如：https://example.com/webdav/）")
        webdav_form.addRow("服务器URL:", self.webdav_server_url_input)
        
        # 用户名输入框
        self.webdav_username_input = QLineEdit()
        self.webdav_username_input.setPlaceholderText("输入WebDAV用户名")
        webdav_form.addRow("用户名:", self.webdav_username_input)
        
        # 密码输入框
        self.webdav_password_input = QLineEdit()
        self.webdav_password_input.setEchoMode(QLineEdit.Password)  # 设置为密码模式
        self.webdav_password_input.setPlaceholderText("输入WebDAV密码")
        webdav_form.addRow("密码:", self.webdav_password_input)
        
        # 远程路径输入框
        self.webdav_remote_path_input = QLineEdit("/")
        self.webdav_remote_path_input.setPlaceholderText("输入远程保存路径（例如：/backup/configs/）")
        webdav_form.addRow("远程路径:", self.webdav_remote_path_input)
        
        # 文件名输入框
        self.webdav_filename_input = QLineEdit("launcher_config.json")
        webdav_form.addRow("配置文件名:", self.webdav_filename_input)
        
        # 自动同步选项
        self.webdav_auto_sync_checkbox = QCheckBox("启动时自动同步配置")
        webdav_form.addRow("自动同步:", self.webdav_auto_sync_checkbox)
        
        webdav_layout.addWidget(webdav_group)
        
        # 测试连接按钮
        test_webdav_button = QPushButton("测试 WebDAV 连接")
        test_webdav_button.clicked.connect(self.test_webdav_connection)
        webdav_layout.addWidget(test_webdav_button)
        
        # 添加帮助信息
        webdav_help_text = """
        <p style="font-size:12px; color:#666;">
        <b>WebDAV 使用说明:</b><br>
        1. 输入WebDAV服务器的URL、用户名和密码<br>
        2. 指定远程保存路径和文件名<br>
        3. 测试连接确保一切正常<br>
        4. 选择是否启用自动同步<br>
        <br>
        常见WebDAV服务：<br>
        - NextCloud/ownCloud: https://your-server.com/remote.php/webdav/<br>
        - Seafile: https://your-server.com/seafdav/<br>
        - Box: https://dav.box.com/dav/<br>
        </p>
        """
        webdav_help_label = QLabel(webdav_help_text)
        webdav_help_label.setTextFormat(Qt.RichText)
        webdav_layout.addWidget(webdav_help_label)
        
        # 添加弹性空间
        webdav_layout.addStretch()
        
        # 添加标签页
        tab_widget.addTab(github_tab, "GitHub Gist")
        tab_widget.addTab(open_gist_tab, "Open Gist")
        tab_widget.addTab(webdav_tab, "WebDAV")
        
        main_layout.addWidget(tab_widget)
        
        # 同步操作组
        sync_group = QGroupBox("同步操作")
        sync_layout = QHBoxLayout(sync_group)
        
        # 上传按钮
        upload_button = QPushButton("上传配置到所有启用的服务")
        upload_button.clicked.connect(self.upload_config)
        sync_layout.addWidget(upload_button)
        
        # 下载按钮
        download_button = QPushButton("从所有启用的服务下载配置")
        download_button.clicked.connect(self.download_config)
        sync_layout.addWidget(download_button)
        
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
            self.github_enabled_checkbox.setChecked(self.github_manager.enabled)
            self.github_token_input.setText(self.github_manager.token)
            self.github_gist_id_input.setText(self.github_manager.gist_id)
            self.github_filename_input.setText(self.github_manager.filename)
            self.github_auto_sync_checkbox.setChecked(self.github_manager.auto_sync)
            
            # 从OpenGistManager获取当前设置
            self.open_gist_enabled_checkbox.setChecked(self.open_gist_manager.enabled)
            self.open_gist_api_url_input.setText(self.open_gist_manager.api_url)
            self.open_gist_api_key_input.setText(self.open_gist_manager.api_key)
            self.open_gist_id_input.setText(self.open_gist_manager.gist_id)
            self.open_gist_filename_input.setText(self.open_gist_manager.filename)
            self.open_gist_auto_sync_checkbox.setChecked(self.open_gist_manager.auto_sync)
            
            # 从WebDAVManager获取当前设置
            self.webdav_enabled_checkbox.setChecked(self.webdav_manager.enabled)
            self.webdav_server_url_input.setText(self.webdav_manager.server_url)
            self.webdav_username_input.setText(self.webdav_manager.username)
            self.webdav_password_input.setText(self.webdav_manager.password)
            self.webdav_remote_path_input.setText(self.webdav_manager.remote_path)
            self.webdav_filename_input.setText(self.webdav_manager.filename)
            self.webdav_auto_sync_checkbox.setChecked(self.webdav_manager.auto_sync)
        except Exception as e:
            self.logger.error(f"加载同步设置时出错: {e}")
    
    def save_settings(self):
        """保存设置"""
        try:
            # GitHub Gist 设置
            github_enabled = self.github_enabled_checkbox.isChecked()
            github_token = self.github_token_input.text().strip()
            github_gist_id = self.github_gist_id_input.text().strip()
            github_filename = self.github_filename_input.text().strip()
            github_auto_sync = self.github_auto_sync_checkbox.isChecked()
            
            # Open Gist 设置
            open_gist_enabled = self.open_gist_enabled_checkbox.isChecked()
            open_gist_api_url = self.open_gist_api_url_input.text().strip()
            open_gist_api_key = self.open_gist_api_key_input.text().strip()
            open_gist_id = self.open_gist_id_input.text().strip()
            open_gist_filename = self.open_gist_filename_input.text().strip()
            open_gist_auto_sync = self.open_gist_auto_sync_checkbox.isChecked()
            
            # WebDAV 设置
            webdav_enabled = self.webdav_enabled_checkbox.isChecked()
            webdav_server_url = self.webdav_server_url_input.text().strip()
            webdav_username = self.webdav_username_input.text().strip()
            webdav_password = self.webdav_password_input.text().strip()
            webdav_remote_path = self.webdav_remote_path_input.text().strip()
            webdav_filename = self.webdav_filename_input.text().strip()
            webdav_auto_sync = self.webdav_auto_sync_checkbox.isChecked()
            
            # 验证 GitHub Gist 输入
            if github_enabled:
                if not github_token:
                    QMessageBox.warning(self, "输入错误", "请输入GitHub Token")
                    return
                
                if not github_gist_id:
                    QMessageBox.warning(self, "输入错误", "请输入GitHub Gist ID或创建新的Gist")
                    return
                
                if not github_filename:
                    QMessageBox.warning(self, "输入错误", "请输入GitHub配置文件名")
                    return
            
            # 验证 Open Gist 输入
            if open_gist_enabled:
                if not open_gist_api_url:
                    QMessageBox.warning(self, "输入错误", "请输入Open Gist API URL")
                    return
                
                if not open_gist_api_key:
                    QMessageBox.warning(self, "输入错误", "请输入Open Gist API Key")
                    return
                
                if not open_gist_id:
                    QMessageBox.warning(self, "输入错误", "请输入Open Gist ID或创建新的Gist")
                    return
                
                if not open_gist_filename:
                    QMessageBox.warning(self, "输入错误", "请输入Open Gist配置文件名")
                    return
            
            # 验证 WebDAV 输入
            if webdav_enabled:
                if not webdav_server_url:
                    QMessageBox.warning(self, "输入错误", "请输入WebDAV服务器URL")
                    return
                
                if not webdav_username:
                    QMessageBox.warning(self, "输入错误", "请输入WebDAV用户名")
                    return
                
                if not webdav_password:
                    QMessageBox.warning(self, "输入错误", "请输入WebDAV密码")
                    return
                
                if not webdav_filename:
                    QMessageBox.warning(self, "输入错误", "请输入WebDAV配置文件名")
                    return
            
            # 保存 GitHub Gist 配置
            self.github_manager.set_config(
                github_enabled, 
                github_token, 
                github_gist_id, 
                github_filename, 
                github_auto_sync
            )
            
            # 保存 Open Gist 配置
            self.open_gist_manager.set_config(
                open_gist_enabled,
                open_gist_api_url,
                open_gist_api_key,
                open_gist_id,
                open_gist_filename,
                open_gist_auto_sync
            )
            
            # 保存 WebDAV 配置
            self.webdav_manager.set_config(
                webdav_enabled,
                webdav_server_url,
                webdav_username,
                webdav_password,
                webdav_remote_path,
                webdav_filename,
                webdav_auto_sync
            )
            
            QMessageBox.information(self, "保存成功", "同步设置已保存")
            self.accept()
        except Exception as e:
            self.logger.error(f"保存同步设置时出错: {e}")
            QMessageBox.critical(self, "保存失败", f"保存设置时出错: {e}")
    
    def test_github_connection(self):
        """测试GitHub连接"""
        try:
            # 使用当前输入的值进行测试
            enabled = self.github_enabled_checkbox.isChecked()
            token = self.github_token_input.text().strip()
            gist_id = self.github_gist_id_input.text().strip()
            
            if not enabled:
                QMessageBox.warning(self, "无法测试", "GitHub Gist 同步未启用")
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
    
    def test_open_gist_connection(self):
        """测试Open Gist连接"""
        try:
            # 使用当前输入的值进行测试
            enabled = self.open_gist_enabled_checkbox.isChecked()
            api_url = self.open_gist_api_url_input.text().strip()
            api_key = self.open_gist_api_key_input.text().strip()
            gist_id = self.open_gist_id_input.text().strip()
            
            if not enabled:
                QMessageBox.warning(self, "无法测试", "Open Gist 同步未启用")
                return
                
            if not api_url or not api_key or not gist_id:
                QMessageBox.warning(self, "无法测试", "请先输入API URL、API Key和Gist ID")
                return
            
            # 创建临时OpenGistManager进行测试
            temp_manager = OpenGistManager()
            temp_manager.enabled = enabled
            temp_manager.api_url = api_url
            temp_manager.base_url = api_url
            temp_manager.api_key = api_key
            temp_manager.gist_id = gist_id
            
            # 测试连接
            success, message = temp_manager.test_connection()
            
            if success:
                QMessageBox.information(self, "连接成功", message)
            else:
                QMessageBox.warning(self, "连接失败", message)
        except Exception as e:
            self.logger.error(f"测试Open Gist连接时出错: {e}")
            QMessageBox.critical(self, "测试失败", f"测试连接时出错: {e}")
    
    def test_webdav_connection(self):
        """测试WebDAV连接"""
        try:
            # 使用当前输入的值进行测试
            enabled = self.webdav_enabled_checkbox.isChecked()
            server_url = self.webdav_server_url_input.text().strip()
            username = self.webdav_username_input.text().strip()
            password = self.webdav_password_input.text().strip()
            
            if not enabled:
                QMessageBox.warning(self, "无法测试", "WebDAV 同步未启用")
                return
                
            if not server_url or not username or not password:
                QMessageBox.warning(self, "无法测试", "请先输入服务器URL、用户名和密码")
                return
            
            # 创建临时WebDAVManager进行测试
            temp_manager = WebDAVManager()
            temp_manager.enabled = enabled
            temp_manager.server_url = server_url
            temp_manager.username = username
            temp_manager.password = password
            
            # 测试连接
            success, message = temp_manager.test_connection()
            
            if success:
                QMessageBox.information(self, "连接成功", message)
            else:
                QMessageBox.warning(self, "连接失败", message)
        except Exception as e:
            self.logger.error(f"测试WebDAV连接时出错: {e}")
            QMessageBox.critical(self, "测试失败", f"测试连接时出错: {e}")
    
    def create_new_github_gist(self):
        """创建新的GitHub Gist"""
        try:
            enabled = self.github_enabled_checkbox.isChecked()
            token = self.github_token_input.text().strip()
            
            if not enabled:
                QMessageBox.warning(self, "无法创建", "GitHub Gist 同步未启用")
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
                self.github_gist_id_input.setText(new_gist_id)
                QMessageBox.information(self, "创建成功", f"新的GitHub Gist已创建，ID: {new_gist_id}")
            else:
                QMessageBox.warning(self, "创建失败", message)
        except Exception as e:
            self.logger.error(f"创建新GitHub Gist时出错: {e}")
            QMessageBox.critical(self, "创建失败", f"创建新GitHub Gist时出错: {e}")
    
    def create_new_open_gist(self):
        """创建新的Open Gist"""
        try:
            enabled = self.open_gist_enabled_checkbox.isChecked()
            api_url = self.open_gist_api_url_input.text().strip()
            api_key = self.open_gist_api_key_input.text().strip()
            
            if not enabled:
                QMessageBox.warning(self, "无法创建", "Open Gist 同步未启用")
                return
                
            if not api_url or not api_key:
                QMessageBox.warning(self, "无法创建", "请先输入API URL和API Key")
                return
            
            # 创建临时OpenGistManager
            temp_manager = OpenGistManager()
            temp_manager.enabled = enabled
            temp_manager.api_url = api_url
            temp_manager.base_url = api_url
            temp_manager.api_key = api_key
            
            # 获取Gist描述
            description = "应用启动器配置"
            
            # 创建新Gist
            success, message, new_gist_id = temp_manager.create_new_gist(description)
            
            if success and new_gist_id:
                self.open_gist_id_input.setText(new_gist_id)
                QMessageBox.information(self, "创建成功", f"新的Open Gist已创建，ID: {new_gist_id}")
            else:
                QMessageBox.warning(self, "创建失败", message)
        except Exception as e:
            self.logger.error(f"创建新Open Gist时出错: {e}")
            QMessageBox.critical(self, "创建失败", f"创建新Open Gist时出错: {e}")
    
    def upload_config(self):
        """上传配置到所有启用的服务"""
        try:
            # 获取所有启用的同步服务
            enabled_services = []
            
            # 检查GitHub Gist
            github_enabled = self.github_enabled_checkbox.isChecked()
            github_token = self.github_token_input.text().strip()
            github_gist_id = self.github_gist_id_input.text().strip()
            github_filename = self.github_filename_input.text().strip()
            
            if github_enabled and github_token and github_gist_id and github_filename:
                # 创建临时GistManager
                github_manager = GistManager()
                github_manager.enabled = github_enabled
                github_manager.token = github_token
                github_manager.gist_id = github_gist_id
                github_manager.filename = github_filename
                enabled_services.append(("GitHub Gist", github_manager))
            
            # 检查Open Gist
            open_gist_enabled = self.open_gist_enabled_checkbox.isChecked()
            open_gist_api_url = self.open_gist_api_url_input.text().strip()
            open_gist_api_key = self.open_gist_api_key_input.text().strip()
            open_gist_id = self.open_gist_id_input.text().strip()
            open_gist_filename = self.open_gist_filename_input.text().strip()
            
            if open_gist_enabled and open_gist_api_url and open_gist_api_key and open_gist_id and open_gist_filename:
                # 创建临时OpenGistManager
                open_gist_manager = OpenGistManager()
                open_gist_manager.enabled = open_gist_enabled
                open_gist_manager.api_url = open_gist_api_url
                open_gist_manager.base_url = open_gist_api_url
                open_gist_manager.api_key = open_gist_api_key
                open_gist_manager.gist_id = open_gist_id
                open_gist_manager.filename = open_gist_filename
                enabled_services.append(("Open Gist", open_gist_manager))
            
            # 检查WebDAV
            webdav_enabled = self.webdav_enabled_checkbox.isChecked()
            webdav_server_url = self.webdav_server_url_input.text().strip()
            webdav_username = self.webdav_username_input.text().strip()
            webdav_password = self.webdav_password_input.text().strip()
            webdav_remote_path = self.webdav_remote_path_input.text().strip()
            webdav_filename = self.webdav_filename_input.text().strip()
            
            if webdav_enabled and webdav_server_url and webdav_username and webdav_password and webdav_filename:
                # 创建临时WebDAVManager
                webdav_manager = WebDAVManager()
                webdav_manager.enabled = webdav_enabled
                webdav_manager.server_url = webdav_server_url
                webdav_manager.username = webdav_username
                webdav_manager.password = webdav_password
                webdav_manager.remote_path = webdav_remote_path
                webdav_manager.filename = webdav_filename
                enabled_services.append(("WebDAV", webdav_manager))
            
            # 如果没有启用的服务，显示提示
            if not enabled_services:
                QMessageBox.warning(self, "无法上传", "没有启用的同步服务")
                return
            
            # 上传到所有启用的服务
            results = []
            for service_name, manager in enabled_services:
                success, message = manager.upload_config()
                results.append((service_name, success, message))
            
            # 显示上传结果
            result_message = "上传结果:\n\n"
            for service_name, success, message in results:
                status = "成功" if success else "失败"
                result_message += f"{service_name}: {status} - {message}\n"
            
            QMessageBox.information(self, "上传完成", result_message)
        except Exception as e:
            self.logger.error(f"上传配置时出错: {e}")
            QMessageBox.critical(self, "上传失败", f"上传配置时出错: {e}")
    
    def download_config(self):
        """从所有启用的服务下载配置"""
        try:
            # 获取所有启用的同步服务
            enabled_services = []
            
            # 检查GitHub Gist
            github_enabled = self.github_enabled_checkbox.isChecked()
            github_token = self.github_token_input.text().strip()
            github_gist_id = self.github_gist_id_input.text().strip()
            github_filename = self.github_filename_input.text().strip()
            
            if github_enabled and github_token and github_gist_id and github_filename:
                # 创建临时GistManager
                github_manager = GistManager()
                github_manager.enabled = github_enabled
                github_manager.token = github_token
                github_manager.gist_id = github_gist_id
                github_manager.filename = github_filename
                enabled_services.append(("GitHub Gist", github_manager))
            
            # 检查Open Gist
            open_gist_enabled = self.open_gist_enabled_checkbox.isChecked()
            open_gist_api_url = self.open_gist_api_url_input.text().strip()
            open_gist_api_key = self.open_gist_api_key_input.text().strip()
            open_gist_id = self.open_gist_id_input.text().strip()
            open_gist_filename = self.open_gist_filename_input.text().strip()
            
            if open_gist_enabled and open_gist_api_url and open_gist_api_key and open_gist_id and open_gist_filename:
                # 创建临时OpenGistManager
                open_gist_manager = OpenGistManager()
                open_gist_manager.enabled = open_gist_enabled
                open_gist_manager.api_url = open_gist_api_url
                open_gist_manager.base_url = open_gist_api_url
                open_gist_manager.api_key = open_gist_api_key
                open_gist_manager.gist_id = open_gist_id
                open_gist_manager.filename = open_gist_filename
                enabled_services.append(("Open Gist", open_gist_manager))
            
            # 检查WebDAV
            webdav_enabled = self.webdav_enabled_checkbox.isChecked()
            webdav_server_url = self.webdav_server_url_input.text().strip()
            webdav_username = self.webdav_username_input.text().strip()
            webdav_password = self.webdav_password_input.text().strip()
            webdav_remote_path = self.webdav_remote_path_input.text().strip()
            webdav_filename = self.webdav_filename_input.text().strip()
            
            if webdav_enabled and webdav_server_url and webdav_username and webdav_password and webdav_filename:
                # 创建临时WebDAVManager
                webdav_manager = WebDAVManager()
                webdav_manager.enabled = webdav_enabled
                webdav_manager.server_url = webdav_server_url
                webdav_manager.username = webdav_username
                webdav_manager.password = webdav_password
                webdav_manager.remote_path = webdav_remote_path
                webdav_manager.filename = webdav_filename
                enabled_services.append(("WebDAV", webdav_manager))
            
            # 如果没有启用的服务，显示提示
            if not enabled_services:
                QMessageBox.warning(self, "无法下载", "没有启用的同步服务")
                return
            
            # 确认是否要覆盖本地配置
            confirm = QMessageBox.question(
                self, "确认下载", 
                "从同步服务下载配置将覆盖本地配置，是否继续？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm != QMessageBox.Yes:
                return
            
            # 下载结果列表
            results = []
            downloaded_configs = []
            
            # 下载所有配置
            for service_name, manager in enabled_services:
                success, message, config_data = manager.download_config()
                results.append((service_name, success, message))
                if success and config_data:
                    downloaded_configs.append((service_name, config_data))
            
            # 如果有成功下载的配置，选择使用最新的一个
            if downloaded_configs:
                # 如果只有一个配置，直接使用
                if len(downloaded_configs) == 1:
                    from utils.config_manager import save_config
                    save_config(downloaded_configs[0][1])
                    
                    # 显示下载结果
                    result_message = "下载结果:\n\n"
                    for service_name, success, message in results:
                        status = "成功" if success else "失败"
                        result_message += f"{service_name}: {status} - {message}\n"
                    
                    QMessageBox.information(self, "下载完成", result_message + "\n\n配置已应用")
                else:
                    # 多个配置，询问用户选择
                    options = [f"{service_name}" for service_name, _ in downloaded_configs]
                    option_descriptions = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
                    
                    # 显示下载结果
                    result_message = "下载结果:\n\n"
                    for service_name, success, message in results:
                        status = "成功" if success else "失败"
                        result_message += f"{service_name}: {status} - {message}\n"
                    
                    # 询问用户选择配置
                    from PyQt5.QtWidgets import QInputDialog
                    selected_index, ok = QInputDialog.getItem(
                        self, "选择配置", 
                        result_message + "\n\n多个服务下载成功，请选择要使用的配置:",
                        options, 0, False
                    )
                    
                    if ok and selected_index:
                        # 查找选中的配置
                        selected_name = selected_index
                        for service_name, config_data in downloaded_configs:
                            if service_name == selected_name:
                                from utils.config_manager import save_config
                                save_config(config_data)
                                QMessageBox.information(self, "下载完成", f"已应用来自 {service_name} 的配置")
                                break
            else:
                # 没有成功下载的配置，显示结果
                result_message = "下载结果:\n\n"
                for service_name, success, message in results:
                    status = "成功" if success else "失败"
                    result_message += f"{service_name}: {status} - {message}\n"
                
                QMessageBox.warning(self, "下载失败", result_message)
        except Exception as e:
            self.logger.error(f"下载配置时出错: {e}")
            QMessageBox.critical(self, "下载失败", f"下载配置时出错: {e}") 