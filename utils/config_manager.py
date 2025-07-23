#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
import threading
from typing import Dict, Any, Optional
from utils.logger import get_logger

# 获取日志记录器
logger = get_logger("config_manager")

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "."))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

# 项目路径配置完成

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
        logger.error(f"加载配置失败: {e}")
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
        logger.error(f"保存配置失败: {e}")
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

def get_programs(config: Dict[str, Any]) -> list:
    """
    从配置中获取程序列表
    
    Args:
        config: 配置数据
        
    Returns:
        程序列表
    """
    return config.get("programs", [])

def get_available_tags(config: Dict[str, Any]) -> list:
    """
    获取可用标签列表
    
    Args:
        config: 配置数据
        
    Returns:
        可用标签列表
    """
    default_tags = ["通用", "PC", "Mac笔记本", "BK100"]
    return config.get("available_tags", default_tags)

def add_available_tag(config: Dict[str, Any], tag: str) -> Dict[str, Any]:
    """
    添加新的可用标签
    
    Args:
        config: 配置数据
        tag: 要添加的标签
        
    Returns:
        更新后的配置数据
    """
    available_tags = get_available_tags(config)
    if tag not in available_tags:
        available_tags.append(tag)
        config["available_tags"] = available_tags
    return config

def get_tag_filter_state(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取标签过滤状态
    
    Args:
        config: 配置数据
        
    Returns:
        标签过滤状态
    """
    default_state = {
        "selected_tags": [],
        "filter_mode": "OR"  # AND 或 OR
    }
    return config.get("tag_filter_state", default_state)

def update_tag_filter_state(config: Dict[str, Any], selected_tags: list, filter_mode: str = "OR") -> Dict[str, Any]:
    """
    更新标签过滤状态
    
    Args:
        config: 配置数据
        selected_tags: 选中的标签列表
        filter_mode: 过滤模式 ("AND" 或 "OR")
        
    Returns:
        更新后的配置数据
    """
    config["tag_filter_state"] = {
        "selected_tags": selected_tags,
        "filter_mode": filter_mode
    }
    return config

def filter_programs_by_tags(config: Dict[str, Any], programs: list = None) -> list:
    """
    根据标签过滤程序列表
    
    Args:
        config: 配置数据
        programs: 程序列表，如果为None则从config获取
        
    Returns:
        过滤后的程序列表
    """
    if programs is None:
        programs = get_programs(config)
    
    filter_state = get_tag_filter_state(config)
    selected_tags = filter_state.get("selected_tags", [])
    filter_mode = filter_state.get("filter_mode", "OR")
    
    # 如果没有选择标签，返回所有程序
    if not selected_tags:
        return programs
    
    filtered_programs = []
    for program in programs:
        program_tags = program.get("tags", [])
        
        if filter_mode == "AND":
            # AND模式：程序必须包含所有选中的标签
            if all(tag in program_tags for tag in selected_tags):
                filtered_programs.append(program)
        else:
            # OR模式：程序包含任一选中标签即可
            if any(tag in program_tags for tag in selected_tags):
                filtered_programs.append(program)
    
    return filtered_programs