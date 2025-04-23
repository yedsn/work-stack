#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "."))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

# 添加调试信息
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"CONFIG_PATH: {CONFIG_PATH}")

def load_config():
    """加载配置文件"""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"categories": ["娱乐", "工作", "文档"], "programs": []}
    except Exception as e:
        print(f"加载配置失败: {e}")
        return {"categories": ["娱乐", "工作", "文档"], "programs": []}

def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False 