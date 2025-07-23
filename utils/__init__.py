#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具函数包

包含应用程序所需的各种工具模块：
- logger: 日志记录
- config_manager: 配置管理
- os_utils: 操作系统工具
- platform_settings: 平台相关设置
- app_launcher: 应用程序启动器
- 同步管理器: gist_manager, webdav_manager等
"""

# 导入常用的工具函数，方便其他模块使用
from .logger import get_logger, set_log_level
from .os_utils import get_os_type, expand_path
from .platform_settings import (
    get_platform_style, 
    get_platform_setting,
    is_windows, 
    is_mac, 
    is_linux
)
from .config_manager import load_config, save_config, get_programs

__all__ = [
    # 日志相关
    'get_logger', 
    'set_log_level',
    
    # 操作系统相关
    'get_os_type',
    'expand_path',
    
    # 平台相关
    'get_platform_style',
    'get_platform_setting', 
    'is_windows',
    'is_mac',
    'is_linux',
    
    # 配置相关
    'load_config',
    'save_config', 
    'get_programs',
] 