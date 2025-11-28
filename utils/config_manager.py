#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
import threading
from typing import Dict, Any, Optional, List
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
DEFAULT_ICON_CACHE_CAPACITY = 128

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

def get_ui_preferences(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取界面偏好设置
    """
    prefs = config.get("ui_preferences")
    return prefs if isinstance(prefs, dict) else {}

def is_launch_icon_enabled(config: Dict[str, Any]) -> bool:
    """
    返回是否启用启动项图标渲染
    """
    prefs = get_ui_preferences(config)
    return prefs.get("launch_icons_enabled", True)

def set_launch_icon_enabled(config: Dict[str, Any], enabled: bool) -> Dict[str, Any]:
    """
    更新启动项图标开关
    """
    prefs = get_ui_preferences(config).copy()
    prefs["launch_icons_enabled"] = bool(enabled)
    config["ui_preferences"] = prefs
    return config

def get_icon_cache_capacity(config: Dict[str, Any]) -> int:
    """
    获取图标缓存容量
    """
    prefs = get_ui_preferences(config)
    value = prefs.get("icon_cache_capacity", DEFAULT_ICON_CACHE_CAPACITY)
    try:
        capacity = int(value)
        return capacity if capacity > 0 else DEFAULT_ICON_CACHE_CAPACITY
    except (TypeError, ValueError):
        return DEFAULT_ICON_CACHE_CAPACITY

def set_icon_cache_capacity(config: Dict[str, Any], capacity: int) -> Dict[str, Any]:
    """
    设置图标缓存容量
    """
    prefs = get_ui_preferences(config).copy()
    try:
        normalized = max(16, int(capacity))
    except (TypeError, ValueError):
        normalized = DEFAULT_ICON_CACHE_CAPACITY
    prefs["icon_cache_capacity"] = normalized
    config["ui_preferences"] = prefs
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

def prepare_config_for_sync(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    准备用于同步的配置数据（排除本地特定的设置）
    
    Args:
        config: 完整的配置数据
        
    Returns:
        用于同步的配置数据（排除了本地特定设置）
    """
    # 创建配置副本
    sync_config = config.copy()
    
    # 从配置中读取本地专用键列表，如果没有则使用默认值
    sync_settings = config.get("sync_settings", {})
    local_only_keys = sync_settings.get("local_only_keys", [
        "tag_filter_state",  # 标签过滤状态保持本地
        "window_size",       # 窗口大小本地化
        "device_window_sizes",  # 设备特定窗口大小
        "sync_settings"      # 同步设置本身也不同步
    ])
    
    # 排除本地专用设置
    for key in local_only_keys:
        if key in sync_config:
            del sync_config[key]
    
    return sync_config

def merge_synced_config(local_config: Dict[str, Any], synced_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并同步的配置与本地配置
    
    Args:
        local_config: 本地配置数据
        synced_config: 从远程同步的配置数据
        
    Returns:
        合并后的配置数据
    """
    # 以同步配置为基础
    merged_config = synced_config.copy()
    
    # 从本地配置中读取本地专用键列表
    sync_settings = local_config.get("sync_settings", {})
    local_only_keys = sync_settings.get("local_only_keys", [
        "tag_filter_state",  # 保持本地的标签过滤状态
        "window_size",       # 保持本地的窗口大小
        "device_window_sizes",  # 保持设备特定窗口大小
        "sync_settings"      # 同步设置本身也保持本地
    ])
    
    # 保留本地特定的设置
    for key in local_only_keys:
        if key in local_config:
            merged_config[key] = local_config[key]
    
    return merged_config

def get_local_only_keys(config: Dict[str, Any]) -> list:
    """
    获取本地专用键列表
    
    Args:
        config: 配置数据
        
    Returns:
        本地专用键列表
    """
    sync_settings = config.get("sync_settings", {})
    return sync_settings.get("local_only_keys", [
        "tag_filter_state",
        "window_size", 
        "device_window_sizes",
        "sync_settings"
    ])

def set_local_only_keys(config: Dict[str, Any], keys: list) -> Dict[str, Any]:
    """
    设置本地专用键列表
    
    Args:
        config: 配置数据
        keys: 本地专用键列表
        
    Returns:
        更新后的配置数据
    """
    if "sync_settings" not in config:
        config["sync_settings"] = {}
    
    config["sync_settings"]["local_only_keys"] = keys
    return config

def add_local_only_key(config: Dict[str, Any], key: str) -> Dict[str, Any]:
    """
    添加本地专用键
    
    Args:
        config: 配置数据
        key: 要添加的键名
        
    Returns:
        更新后的配置数据
    """
    local_only_keys = get_local_only_keys(config)
    if key not in local_only_keys:
        local_only_keys.append(key)
        config = set_local_only_keys(config, local_only_keys)
    return config

def remove_local_only_key(config: Dict[str, Any], key: str) -> Dict[str, Any]:
    """
    移除本地专用键
    
    Args:
        config: 配置数据
        key: 要移除的键名
        
    Returns:
        更新后的配置数据
    """
    local_only_keys = get_local_only_keys(config)
    if key in local_only_keys:
        local_only_keys.remove(key)
        config = set_local_only_keys(config, local_only_keys)
    return config

def print_sync_config_info(config: Dict[str, Any] = None):
    """
    打印同步配置信息（调试和管理用途）
    
    Args:
        config: 配置数据，如果为None则自动加载
    """
    if config is None:
        config = load_config()
    
    print("🔧 同步配置信息")
    print("=" * 50)
    
    # 显示当前的本地专用键
    local_only_keys = get_local_only_keys(config)
    print(f"📋 本地专用键 ({len(local_only_keys)} 个):")
    for i, key in enumerate(local_only_keys, 1):
        print(f"   {i}. {key}")
    
    print("\n" + "=" * 50)
    
    # 显示将要同步的配置项
    sync_config = prepare_config_for_sync(config)
    print(f"☁️  将要同步的配置项 ({len(sync_config)} 个):")
    for i, key in enumerate(sync_config.keys(), 1):
        print(f"   {i}. {key}")
    
    print("\n" + "=" * 50)
    
    # 显示本地保留的配置项
    local_keys = set(config.keys()) - set(sync_config.keys())
    print(f"🏠 本地保留的配置项 ({len(local_keys)} 个):")
    for i, key in enumerate(sorted(local_keys), 1):
        print(f"   {i}. {key}")
    
    print("\n✅ 配置信息显示完成！")

# 命令行调用支持
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "sync-info":
        print_sync_config_info()
