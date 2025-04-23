#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from typing import Dict, Any, List

from utils.ui_utils import print_colored

def load_config(config_file: str) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置数据字典
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print_colored(f"错误: 配置文件 '{config_file}' 格式不正确", "red")
        raise
    except Exception as e:
        print_colored(f"读取配置文件时出错: {e}", "red")
        raise

def get_programs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从配置中获取程序列表
    
    Args:
        config: 配置数据
        
    Returns:
        程序列表
    """
    programs = config.get("programs", [])
    if not programs:
        print_colored("配置文件中没有定义程序", "red")
    return programs 