#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
import difflib
import shutil
from datetime import datetime
from utils.logger import get_logger
from utils.config_manager import load_config, save_config, CONFIG_PATH

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "."))
HISTORY_DIR = os.path.join(PROJECT_ROOT, "config_history")

class ConfigHistoryManager:
    """配置历史管理器，用于记录和管理配置文件的变更历史"""
    
    def __init__(self):
        self.logger = get_logger()
        self.history_dir = HISTORY_DIR
        
        # 确保历史目录存在
        if not os.path.exists(self.history_dir):
            try:
                os.makedirs(self.history_dir)
                self.logger.info(f"创建历史记录目录: {self.history_dir}")
            except Exception as e:
                self.logger.error(f"创建历史记录目录失败: {e}")
    
    def save_history(self, config=None, description=""):
        """保存当前配置到历史记录"""
        try:
            # 如果没有提供配置，则加载当前配置
            if config is None:
                config = load_config()
            
            # 生成时间戳
            timestamp = int(time.time())
            date_str = datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H%M%S")
            
            # 创建历史记录文件名
            history_file = os.path.join(self.history_dir, f"config_{date_str}.json")
            
            # 添加元数据
            history_config = {
                "timestamp": timestamp,
                "date": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                "description": description,
                "config": config
            }
            
            # 保存历史记录
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"保存配置历史记录: {history_file}")
            
            # 清理旧记录
            self.cleanup_old_histories()
            
            return True, history_file
        except Exception as e:
            self.logger.error(f"保存历史记录失败: {e}")
            return False, str(e)
    
    def get_history_list(self, limit=50):
        """获取历史记录列表"""
        try:
            history_files = []
            
            # 确保目录存在
            if not os.path.exists(self.history_dir):
                return []
            
            # 遍历历史目录获取所有记录文件
            for filename in os.listdir(self.history_dir):
                if filename.startswith("config_") and filename.endswith(".json"):
                    file_path = os.path.join(self.history_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            history_data = json.load(f)
                            history_files.append({
                                "filename": filename,
                                "path": file_path,
                                "timestamp": history_data.get("timestamp", 0),
                                "date": history_data.get("date", "未知"),
                                "description": history_data.get("description", "")
                            })
                    except Exception as e:
                        self.logger.error(f"读取历史记录失败 {filename}: {e}")
            
            # 按时间戳排序（最新的在前）
            history_files.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # 限制返回数量
            return history_files[:limit]
        except Exception as e:
            self.logger.error(f"获取历史记录列表失败: {e}")
            return []
    
    def get_history_content(self, filename):
        """获取指定历史记录的内容"""
        try:
            file_path = os.path.join(self.history_dir, filename)
            
            if not os.path.exists(file_path):
                return None, f"历史记录文件不存在: {filename}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                return history_data, None
        except Exception as e:
            self.logger.error(f"获取历史记录内容失败: {e}")
            return None, f"读取历史记录失败: {str(e)}"
    
    def compare_configs(self, config1, config2):
        """比较两个配置文件的差异"""
        try:
            # 将配置转换为格式化的JSON字符串
            config1_str = json.dumps(config1, ensure_ascii=False, indent=2, sort_keys=True)
            config2_str = json.dumps(config2, ensure_ascii=False, indent=2, sort_keys=True)
            
            # 拆分为行
            config1_lines = config1_str.splitlines()
            config2_lines = config2_str.splitlines()
            
            # 使用difflib比较差异
            differ = difflib.Differ()
            diff = list(differ.compare(config1_lines, config2_lines))
            
            return diff
        except Exception as e:
            self.logger.error(f"比较配置差异失败: {e}")
            return [f"比较配置差异失败: {str(e)}"]
    
    def restore_config(self, filename):
        """恢复到指定的历史配置"""
        try:
            # 获取历史记录内容
            history_data, error = self.get_history_content(filename)
            
            if error or history_data is None:
                return False, error
            
            # 提取配置部分
            config = history_data.get("config")
            
            if not config:
                return False, "历史记录中没有有效的配置数据"
            
            # 保存当前配置作为回滚前的历史记录
            self.save_history(description="恢复前的自动备份")
            
            # 恢复配置
            save_config(config)
            
            return True, f"已恢复到 {history_data.get('date')} 的配置"
        except Exception as e:
            self.logger.error(f"恢复配置失败: {e}")
            return False, f"恢复配置失败: {str(e)}"
    
    def cleanup_old_histories(self, max_files=100):
        """清理旧的历史记录，保留最新的max_files个文件"""
        try:
            # 获取所有历史记录文件
            all_histories = self.get_history_list(limit=9999)
            
            # 如果历史记录数量超过上限，删除最旧的记录
            if len(all_histories) > max_files:
                # 按时间排序，最新的在前面
                all_histories.sort(key=lambda x: x["timestamp"], reverse=True)
                
                # 获取需要删除的记录
                files_to_delete = all_histories[max_files:]
                
                # 删除旧记录
                for file_info in files_to_delete:
                    try:
                        os.remove(file_info["path"])
                        self.logger.info(f"删除旧历史记录: {file_info['filename']}")
                    except Exception as e:
                        self.logger.error(f"删除旧历史记录失败 {file_info['filename']}: {e}")
            
            return True
        except Exception as e:
            self.logger.error(f"清理旧历史记录失败: {e}")
            return False 