#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
import threading
from typing import Dict, Any, Optional

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "."))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

# 添加调试信息
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"CONFIG_PATH: {CONFIG_PATH}")

# 全局变量
_config_cache: Optional[Dict[str, Any]] = None
_last_save_time = 0
_save_timer = None
_save_lock = threading.Lock()
SAVE_DELAY = 1.0  # 延迟保存时间（秒）

def load_config() -> Dict[str, Any]:
    """加载配置文件（使用缓存）"""
    global _config_cache
    
    # 如果有缓存且文件未变更，返回缓存
    if _config_cache is not None:
        try:
            if os.path.exists(CONFIG_PATH):
                file_mtime = os.path.getmtime(CONFIG_PATH)
                cache_mtime = _config_cache.get('_cache_time', 0)
                if file_mtime <= cache_mtime:
                    # 返回不包含缓存元数据的配置
                    return {k: v for k, v in _config_cache.items() if not k.startswith('_cache')}
        except OSError:
            pass
    
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 添加缓存时间戳
            _config_cache = config.copy()
            _config_cache['_cache_time'] = time.time()
            return config
        else:
            default_config = {"categories": ["娱乐", "工作", "文档"], "programs": []}
            _config_cache = default_config.copy()
            _config_cache['_cache_time'] = time.time()
            return default_config
    except Exception as e:
        print(f"加载配置失败: {e}")
        default_config = {"categories": ["娱乐", "工作", "文档"], "programs": []}
        _config_cache = default_config.copy()
        _config_cache['_cache_time'] = time.time()
        return default_config

def _do_save_config(config: Dict[str, Any]) -> bool:
    """实际执行保存操作"""
    try:
        # 原子写入，先写临时文件再重命名
        temp_path = CONFIG_PATH + '.tmp'
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 重命名为正式文件
        if os.path.exists(CONFIG_PATH):
            os.remove(CONFIG_PATH)
        os.rename(temp_path, CONFIG_PATH)
        
        # 更新缓存
        global _config_cache
        _config_cache = config.copy()
        _config_cache['_cache_time'] = time.time()
        
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        # 清理临时文件
        temp_path = CONFIG_PATH + '.tmp'
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return False

def save_config(config: Dict[str, Any], immediate: bool = False) -> bool:
    """保存配置文件（支持延迟保存）"""
    global _save_timer, _last_save_time
    
    if immediate:
        # 立即保存
        with _save_lock:
            if _save_timer:
                _save_timer.cancel()
                _save_timer = None
            return _do_save_config(config)
    else:
        # 延迟保存
        with _save_lock:
            # 取消之前的定时器
            if _save_timer:
                _save_timer.cancel()
            
            # 更新缓存中的配置
            global _config_cache
            _config_cache = config.copy()
            _config_cache['_cache_time'] = time.time()
            
            # 设置新的定时器
            _save_timer = threading.Timer(SAVE_DELAY, lambda: _do_save_config(config))
            _save_timer.start()
            
        return True

def flush_config():
    """强制刷新所有待保存的配置"""
    global _save_timer
    with _save_lock:
        if _save_timer:
            _save_timer.cancel()
            _save_timer = None
            if _config_cache:
                config_to_save = {k: v for k, v in _config_cache.items() if not k.startswith('_cache')}
                return _do_save_config(config_to_save)
    return True

def clear_config_cache():
    """清空配置缓存"""
    global _config_cache
    _config_cache = None