#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
from utils.logger import get_logger
from utils.config_manager import load_config, save_config

class OpenGistManager:
    """Open Gist 管理器，用于将配置同步到 Open Gist 服务"""
    
    def __init__(self):
        self.logger = get_logger()
        self.base_url = ""  # Open Gist的API地址
        # 从配置中读取 Open Gist 相关设置
        config = load_config()
        self.open_gist_config = config.get("open_gist_sync", {})
        self.enabled = self.open_gist_config.get("enabled", False)
        self.api_url = self.open_gist_config.get("api_url", "")
        self.api_key = self.open_gist_config.get("api_key", "")
        self.gist_id = self.open_gist_config.get("gist_id", "")
        self.filename = self.open_gist_config.get("filename", "launcher_config.json")
        self.auto_sync = self.open_gist_config.get("auto_sync", False)
        
        # 如果设置了API URL，则更新base_url
        if self.api_url:
            self.base_url = self.api_url
    
    def set_config(self, enabled, api_url, api_key, gist_id, filename="launcher_config.json", auto_sync=False):
        """设置 Open Gist 配置"""
        self.enabled = enabled
        self.api_url = api_url
        self.base_url = api_url
        self.api_key = api_key
        self.gist_id = gist_id
        self.filename = filename
        self.auto_sync = auto_sync
        
        # 更新配置文件
        config = load_config()
        config["open_gist_sync"] = {
            "enabled": enabled,
            "api_url": api_url,
            "api_key": api_key,
            "gist_id": gist_id,
            "filename": filename,
            "auto_sync": auto_sync
        }
        save_config(config)
    
    def get_headers(self):
        """获取 API 请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def test_connection(self):
        """测试 Open Gist 连接是否正常"""
        if not self.enabled:
            return False, "Open Gist 同步未启用"
            
        if not self.api_url or not self.api_key or not self.gist_id:
            return False, "API URL、API Key 或 Gist ID 未设置"
        
        try:
            # 测试 API 连接
            response = requests.get(
                f"{self.base_url}/gists/{self.gist_id}", 
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                return True, "连接成功"
            elif response.status_code == 401:
                return False, "认证失败，请检查 API Key"
            elif response.status_code == 404:
                return False, "未找到 Gist，请检查 Gist ID"
            else:
                return False, f"连接错误: {response.status_code}"
        except Exception as e:
            self.logger.error(f"测试 Open Gist 连接时出错: {e}")
            return False, f"连接异常: {str(e)}"
    
    def upload_config(self):
        """将配置上传到 Open Gist"""
        if not self.enabled:
            return False, "Open Gist 同步未启用"
            
        if not self.api_url or not self.api_key or not self.gist_id:
            return False, "API URL、API Key 或 Gist ID 未设置"
        
        try:
            # 读取本地配置
            config = load_config()
            
            # 检查 Gist 是否存在
            response = requests.get(
                f"{self.base_url}/gists/{self.gist_id}", 
                headers=self.get_headers()
            )
            
            if response.status_code != 200:
                return False, f"获取 Gist 失败: {response.status_code}"
            
            # 准备更新数据
            files_data = {}
            files_data[self.filename] = {"content": json.dumps(config, ensure_ascii=False, indent=2)}
            
            # 更新 Gist
            update_data = {"files": files_data}
            update_response = requests.patch(
                f"{self.base_url}/gists/{self.gist_id}",
                headers=self.get_headers(),
                json=update_data
            )
            
            if update_response.status_code == 200:
                return True, "配置已成功上传到 Open Gist"
            else:
                return False, f"上传配置失败: {update_response.status_code}"
        except Exception as e:
            self.logger.error(f"上传配置到 Open Gist 时出错: {e}")
            return False, f"上传异常: {str(e)}"
    
    def download_config(self):
        """从 Open Gist 下载配置"""
        if not self.enabled:
            return False, "Open Gist 同步未启用", None
            
        if not self.api_url or not self.api_key or not self.gist_id:
            return False, "API URL、API Key 或 Gist ID 未设置", None
        
        try:
            # 获取 Gist 内容
            response = requests.get(
                f"{self.base_url}/gists/{self.gist_id}", 
                headers=self.get_headers()
            )
            
            if response.status_code != 200:
                return False, f"获取 Gist 失败: {response.status_code}", None
            
            # 解析响应
            gist_data = response.json()
            files = gist_data.get("files", {})
            
            if self.filename not in files:
                return False, f"Gist 中未找到文件: {self.filename}", None
            
            # 获取文件内容
            file_content = files[self.filename].get("content", "{}")
            try:
                config_data = json.loads(file_content)
                return True, "配置已成功从 Open Gist 下载", config_data
            except json.JSONDecodeError:
                return False, "配置文件格式无效", None
        except Exception as e:
            self.logger.error(f"从 Open Gist 下载配置时出错: {e}")
            return False, f"下载异常: {str(e)}", None
    
    def create_new_gist(self, description="应用启动器配置"):
        """创建新的 Gist"""
        if not self.enabled:
            return False, "Open Gist 同步未启用", None
            
        if not self.api_url or not self.api_key:
            return False, "API URL 或 API Key 未设置", None
        
        try:
            # 读取本地配置
            config = load_config()
            
            # 准备创建 Gist 的数据
            files_data = {}
            files_data[self.filename] = {"content": json.dumps(config, ensure_ascii=False, indent=2)}
            
            create_data = {
                "description": description,
                "public": False,  # 私有 Gist
                "files": files_data
            }
            
            # 创建 Gist
            response = requests.post(
                f"{self.base_url}/gists",
                headers=self.get_headers(),
                json=create_data
            )
            
            if response.status_code == 201:
                # 获取新创建的 Gist ID
                new_gist = response.json()
                new_gist_id = new_gist.get("id")
                
                if new_gist_id:
                    # 更新本地配置中的 Gist ID
                    self.gist_id = new_gist_id
                    config = load_config()
                    if "open_gist_sync" not in config:
                        config["open_gist_sync"] = {}
                    config["open_gist_sync"]["gist_id"] = new_gist_id
                    save_config(config)
                    
                    return True, "已成功创建新的 Gist", new_gist_id
                else:
                    return False, "创建 Gist 成功但未获取到 ID", None
            else:
                return False, f"创建 Gist 失败: {response.status_code}", None
        except Exception as e:
            self.logger.error(f"创建新 Gist 时出错: {e}")
            return False, f"创建异常: {str(e)}", None 