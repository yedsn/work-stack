#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import os
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from utils.logger import get_logger
from utils.path_utils import (
    get_user_credentials_path,
    get_legacy_credentials_path,
    migrate_legacy_file,
)

logger = get_logger(__name__)
_USER_CREDENTIALS_PATH = get_user_credentials_path()
_LEGACY_CREDENTIALS_PATH = get_legacy_credentials_path()
migrate_legacy_file(_LEGACY_CREDENTIALS_PATH, _USER_CREDENTIALS_PATH)

class CredentialManager:
    """安全凭证管理器 - 加密存储敏感信息"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or str(_USER_CREDENTIALS_PATH)
        self.key = None
        
    def _derive_key(self, password: str, salt: bytes = None) -> bytes:
        """从密码派生加密密钥"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def _get_machine_id(self) -> str:
        """获取机器唯一标识符"""
        try:
            # Windows
            if os.name == 'nt':
                import subprocess
                result = subprocess.run(['wmic', 'csproduct', 'get', 'uuid'], 
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        return lines[1].strip()
            
            # macOS/Linux - 使用机器ID
            machine_id_paths = ['/etc/machine-id', '/var/lib/dbus/machine-id']
            for path in machine_id_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        return f.read().strip()
            
            # 回退到用户目录路径作为标识
            return str(hash(os.path.expanduser('~')))
            
        except Exception as e:
            logger.warning(f"无法获取机器ID: {e}")
            # 使用用户目录路径的哈希值作为回退
            return str(hash(os.path.expanduser('~')))
    
    def _init_encryption(self) -> Fernet:
        """初始化加密器"""
        if self.key is None:
            # 使用机器ID作为密码基础
            machine_id = self._get_machine_id()
            password = f"launcher_{machine_id}_security"
            
            if os.path.exists(self.config_path):
                # 读取现有的盐值
                with open(self.config_path, 'rb') as f:
                    data = json.loads(f.read().decode('utf-8'))
                    salt = base64.b64decode(data.get('salt', ''))
                    self.key, _ = self._derive_key(password, salt)
            else:
                # 生成新的盐值
                self.key, salt = self._derive_key(password)
                # 保存盐值
                with open(self.config_path, 'wb') as f:
                    data = {'salt': base64.b64encode(salt).decode('utf-8'), 'credentials': {}}
                    f.write(json.dumps(data, indent=2).encode('utf-8'))
        
        return Fernet(self.key)
    
    def store_credential(self, service: str, username: str, password: str) -> bool:
        """存储加密的凭证"""
        try:
            fernet = self._init_encryption()
            
            # 加密密码
            encrypted_password = fernet.encrypt(password.encode()).decode()
            
            # 读取现有数据
            credentials = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    credentials = data.get('credentials', {})
                    salt = data.get('salt', '')
            else:
                salt = base64.b64encode(os.urandom(16)).decode('utf-8')
            
            # 存储凭证
            credentials[service] = {
                'username': username,
                'password': encrypted_password
            }
            
            # 写回文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                data = {
                    'salt': salt,
                    'credentials': credentials
                }
                json.dump(data, f, indent=2)
            
            logger.info(f"已安全存储 {service} 的凭证")
            return True
            
        except Exception as e:
            logger.error(f"存储凭证失败: {e}")
            return False
    
    def get_credential(self, service: str) -> tuple:
        """获取解密的凭证"""
        try:
            if not os.path.exists(self.config_path):
                return None, None
            
            fernet = self._init_encryption()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                credentials = data.get('credentials', {})
            
            if service not in credentials:
                return None, None
            
            cred = credentials[service]
            username = cred.get('username')
            encrypted_password = cred.get('password')
            
            if encrypted_password:
                # 解密密码
                password = fernet.decrypt(encrypted_password.encode()).decode()
                return username, password
            
            return username, None
            
        except Exception as e:
            logger.error(f"获取凭证失败: {e}")
            return None, None
    
    def remove_credential(self, service: str) -> bool:
        """删除指定服务的凭证"""
        try:
            if not os.path.exists(self.config_path):
                return True
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            credentials = data.get('credentials', {})
            if service in credentials:
                del credentials[service]
                
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                logger.info(f"已删除 {service} 的凭证")
            
            return True
            
        except Exception as e:
            logger.error(f"删除凭证失败: {e}")
            return False
    
    def list_services(self) -> list:
        """列出所有已存储凭证的服务"""
        try:
            if not os.path.exists(self.config_path):
                return []
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                credentials = data.get('credentials', {})
                return list(credentials.keys())
                
        except Exception as e:
            logger.error(f"列出服务失败: {e}")
            return []
