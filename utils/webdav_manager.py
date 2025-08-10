#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import requests
from requests.auth import HTTPBasicAuth
import base64
from urllib.parse import urlparse, urljoin
from utils.logger import get_logger
from utils.config_manager import load_config, save_config, prepare_config_for_sync, merge_synced_config
from utils.credential_manager import CredentialManager

class WebDAVManager:
    """WebDAV 管理器，用于将配置同步到 WebDAV 服务"""
    
    def __init__(self):
        self.logger = get_logger()
        self.credential_manager = CredentialManager()
        
        # 从配置中读取 WebDAV 相关设置
        config = load_config()
        self.webdav_config = config.get("webdav_sync", {})
        self.enabled = self.webdav_config.get("enabled", False)
        self.server_url = self.webdav_config.get("server_url", "")
        self.username = self.webdav_config.get("username", "")
        
        # 从安全存储获取密码，如果不存在则尝试从配置迁移
        stored_username, stored_password = self.credential_manager.get_credential("webdav")
        if stored_password:
            self.password = stored_password
        else:
            # 迁移旧的明文密码到安全存储
            old_password = self.webdav_config.get("password", "")
            if old_password:
                self.credential_manager.store_credential("webdav", self.username, old_password)
                self.password = old_password
                self.logger.info("已将WebDAV密码迁移到安全存储")
            else:
                self.password = ""
        
        self.remote_path = self.webdav_config.get("remote_path", "/")
        self.filename = self.webdav_config.get("filename", "launcher_config.json")
        self.auto_sync = self.webdav_config.get("auto_sync", False)
        
        # 确保远程路径以/开头且以/结尾
        if self.remote_path and not self.remote_path.startswith('/'):
            self.remote_path = '/' + self.remote_path
        if self.remote_path and not self.remote_path.endswith('/'):
            self.remote_path = self.remote_path + '/'
    
    def set_config(self, enabled, server_url, username, password, remote_path="/", filename="launcher_config.json", auto_sync=False):
        """设置 WebDAV 配置"""
        self.enabled = enabled
        self.server_url = server_url
        self.username = username
        self.password = password
        
        # 安全存储密码
        if password:
            self.credential_manager.store_credential("webdav", username, password)
        
        # 确保远程路径以/开头且以/结尾
        if remote_path and not remote_path.startswith('/'):
            remote_path = '/' + remote_path
        if remote_path and not remote_path.endswith('/'):
            remote_path = remote_path + '/'
            
        self.remote_path = remote_path
        self.filename = filename
        self.auto_sync = auto_sync
        
        # 更新配置文件 - 不再保存密码明文
        config = load_config()
        config["webdav_sync"] = {
            "enabled": enabled,
            "server_url": server_url,
            "username": username,
            # 密码已安全存储，配置文件中不再包含
            "remote_path": remote_path,
            "filename": filename,
            "auto_sync": auto_sync
        }
        save_config(config)
    
    def get_auth(self):
        """获取基本认证"""
        return HTTPBasicAuth(self.username, self.password)
    
    def get_full_url(self, path=""):
        """获取完整的URL路径"""
        base_url = self.server_url
        if not base_url.endswith('/'):
            base_url += '/'
            
        # 如果提供了路径，确保它不以/开头
        if path.startswith('/'):
            path = path[1:]
            
        return urljoin(base_url, path)
    
    def get_file_url(self):
        """获取配置文件的URL"""
        path = os.path.join(self.remote_path, self.filename)
        if path.startswith('/'):
            path = path[1:]
        return self.get_full_url(path)
    
    def test_connection(self):
        """测试 WebDAV 连接是否正常"""
        if not self.enabled:
            return False, "WebDAV 同步未启用"
            
        if not self.server_url or not self.username or not self.password:
            return False, "服务器URL、用户名或密码未设置"
        
        try:
            # 尝试OPTIONS请求测试服务器连接
            response = requests.options(
                self.get_full_url(),
                auth=self.get_auth(),
                timeout=10
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                # 检查DAV头，确认是WebDAV服务器
                dav_header = response.headers.get('DAV') or ""
                if "1" in dav_header.split(",") or "2" in dav_header.split(","):
                    # 尝试PROPFIND请求确认WebDAV功能可用
                    propfind_response = requests.request(
                        "PROPFIND", 
                        self.get_full_url(),
                        auth=self.get_auth(),
                        headers={"Depth": "0"},
                        timeout=10
                    )
                    
                    if propfind_response.status_code == 207:  # 207是WebDAV成功响应
                        return True, "连接成功"
                    else:
                        return False, f"WebDAV功能测试失败: {propfind_response.status_code}"
                else:
                    return False, "服务器不支持WebDAV"
            elif response.status_code == 401:
                return False, "认证失败，请检查用户名和密码"
            else:
                return False, f"连接错误: {response.status_code}"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"测试 WebDAV 连接时出错: {e}")
            return False, f"连接异常: {str(e)}"
    
    def create_directory(self, path):
        """创建远程目录"""
        try:
            dir_url = self.get_full_url(path)
            response = requests.request(
                "MKCOL",
                dir_url,
                auth=self.get_auth(),
                timeout=10
            )
            
            # 201表示创建成功，405表示已存在
            return response.status_code in [201, 405]
        except Exception as e:
            self.logger.error(f"创建WebDAV目录时出错: {e}")
            return False
    
    def ensure_directory_exists(self):
        """确保远程目录存在"""
        if not self.remote_path or self.remote_path == '/':
            return True
        
        # 分解路径并逐级创建
        parts = self.remote_path.strip('/').split('/')
        current_path = ""
        
        for part in parts:
            if not part:
                continue
            current_path += "/" + part
            if not self.create_directory(current_path):
                return False
        
        return True
    
    def upload_config(self):
        """将配置上传到 WebDAV"""
        if not self.enabled:
            return False, "WebDAV 同步未启用"
            
        if not self.server_url or not self.username or not self.password:
            return False, "服务器URL、用户名或密码未设置"
        
        try:
            # 确保远程目录存在
            if not self.ensure_directory_exists():
                return False, "创建远程目录失败"
            
            # 读取本地配置
            config = load_config()
            
            # 准备用于同步的配置（排除本地特定设置）
            sync_config = prepare_config_for_sync(config)
            config_json = json.dumps(sync_config, ensure_ascii=False, indent=2)
            
            # 上传到WebDAV
            file_url = self.get_file_url()
            response = requests.put(
                file_url,
                auth=self.get_auth(),
                data=config_json,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                return True, "配置已成功上传到 WebDAV"
            else:
                return False, f"上传配置失败: {response.status_code}"
        except Exception as e:
            self.logger.error(f"上传配置到 WebDAV 时出错: {e}")
            return False, f"上传异常: {str(e)}"
    
    def download_config(self):
        """从 WebDAV 下载配置"""
        if not self.enabled:
            return False, "WebDAV 同步未启用", None
            
        if not self.server_url or not self.username or not self.password:
            return False, "服务器URL、用户名或密码未设置", None
        
        try:
            # 获取WebDAV文件
            file_url = self.get_file_url()
            response = requests.get(
                file_url,
                auth=self.get_auth(),
                timeout=30
            )
            
            if response.status_code == 200:
                # 解析JSON内容
                try:
                    synced_config = json.loads(response.text)
                    
                    # 读取本地配置以保留本地特定设置
                    local_config = load_config()
                    
                    # 合并配置
                    merged_config = merge_synced_config(local_config, synced_config)
                    
                    return True, "配置已成功从 WebDAV 下载", merged_config
                except json.JSONDecodeError:
                    return False, "下载的配置文件格式无效", None
            elif response.status_code == 404:
                return False, "WebDAV上未找到配置文件", None
            else:
                return False, f"下载配置失败: {response.status_code}", None
        except Exception as e:
            self.logger.error(f"从 WebDAV 下载配置时出错: {e}")
            return False, f"下载异常: {str(e)}", None 