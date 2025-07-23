#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
from utils.logger import get_logger
from utils.config_manager import load_config, save_config, prepare_config_for_sync, merge_synced_config

class GistManager:
    """GitHub Gist 管理器，用于将配置同步到 GitHub Gist"""
    
    def __init__(self):
        self.logger = get_logger()
        self.base_url = "https://api.github.com"
        # 从配置中读取 GitHub 相关设置
        config = load_config()
        self.github_config = config.get("github_sync", {})
        self.enabled = self.github_config.get("enabled", False)
        self.token = self.github_config.get("token", "")
        self.gist_id = self.github_config.get("gist_id", "")
        self.filename = self.github_config.get("filename", "launcher_config.json")
        self.auto_sync = self.github_config.get("auto_sync", False)
    
    def set_config(self, enabled, token, gist_id, filename="launcher_config.json", auto_sync=False):
        """设置 GitHub 配置"""
        self.enabled = enabled
        self.token = token
        self.gist_id = gist_id
        self.filename = filename
        self.auto_sync = auto_sync
        
        # 更新配置文件
        config = load_config()
        config["github_sync"] = {
            "enabled": enabled,
            "token": token,
            "gist_id": gist_id,
            "filename": filename,
            "auto_sync": auto_sync
        }
        save_config(config)
    
    def get_headers(self):
        """获取 API 请求头"""
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def test_connection(self):
        """测试 GitHub 连接是否正常"""
        if not self.enabled:
            return False, "GitHub Gist 同步未启用"
            
        if not self.token or not self.gist_id:
            return False, "Token 或 Gist ID 未设置"
        
        try:
            # 测试 API 连接
            response = requests.get(
                f"{self.base_url}/gists/{self.gist_id}", 
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                return True, "连接成功"
            elif response.status_code == 401:
                return False, "认证失败，请检查 Token"
            elif response.status_code == 404:
                return False, "未找到 Gist，请检查 Gist ID"
            else:
                return False, f"连接错误: {response.status_code}"
        except Exception as e:
            self.logger.error(f"测试 GitHub 连接时出错: {e}")
            return False, f"连接异常: {str(e)}"
    
    def upload_config(self):
        """将配置上传到 GitHub Gist"""
        if not self.enabled:
            return False, "GitHub Gist 同步未启用"
            
        if not self.token or not self.gist_id:
            return False, "Token 或 Gist ID 未设置"
        
        try:
            # 读取本地配置
            config = load_config()
            
            # 准备用于同步的配置（排除本地特定设置）
            sync_config = prepare_config_for_sync(config)
            
            # 检查 Gist 是否存在
            response = requests.get(
                f"{self.base_url}/gists/{self.gist_id}", 
                headers=self.get_headers()
            )
            
            if response.status_code != 200:
                return False, f"获取 Gist 失败: {response.status_code}"
            
            # 准备更新数据
            gist_data = response.json()
            files_data = {}
            files_data[self.filename] = {"content": json.dumps(sync_config, ensure_ascii=False, indent=2)}
            
            # 更新 Gist
            update_data = {"files": files_data}
            update_response = requests.patch(
                f"{self.base_url}/gists/{self.gist_id}",
                headers=self.get_headers(),
                json=update_data
            )
            
            if update_response.status_code == 200:
                return True, "配置已成功上传到 GitHub Gist"
            else:
                return False, f"上传配置失败: {update_response.status_code}"
        except Exception as e:
            self.logger.error(f"上传配置到 GitHub 时出错: {e}")
            return False, f"上传异常: {str(e)}"
    
    def download_config(self):
        """从 GitHub Gist 下载配置"""
        if not self.enabled:
            return False, "GitHub Gist 同步未启用", None
            
        if not self.token or not self.gist_id:
            return False, "Token 或 Gist ID 未设置", None
        
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
                synced_config = json.loads(file_content)
                
                # 读取本地配置以保留本地特定设置
                local_config = load_config()
                
                # 合并配置
                merged_config = merge_synced_config(local_config, synced_config)
                
                return True, "配置已成功从 GitHub Gist 下载", merged_config
            except json.JSONDecodeError:
                return False, "配置文件格式无效", None
        except Exception as e:
            self.logger.error(f"从 GitHub 下载配置时出错: {e}")
            return False, f"下载异常: {str(e)}", None
    
    def create_new_gist(self, description="应用启动器配置"):
        """创建新的 Gist"""
        if not self.enabled:
            return False, "GitHub Gist 同步未启用", None
            
        if not self.token:
            return False, "未设置 Token", None
        
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
                    if "github_sync" not in config:
                        config["github_sync"] = {}
                    config["github_sync"]["gist_id"] = new_gist_id
                    save_config(config)
                    
                    return True, "已成功创建新的 Gist", new_gist_id
                else:
                    return False, "创建 Gist 成功但未获取到 ID", None
            else:
                return False, f"创建 Gist 失败: {response.status_code}", None
        except Exception as e:
            self.logger.error(f"创建新 Gist 时出错: {e}")
            return False, f"创建异常: {str(e)}", None 