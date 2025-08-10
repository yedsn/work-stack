#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import glob
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)

class ConfigHistoryCleanup:
    """配置历史文件清理工具"""
    
    def __init__(self, config_history_dir: str = None):
        if config_history_dir:
            self.config_history_dir = config_history_dir
        else:
            # 默认配置历史目录
            project_root = os.path.dirname(os.path.dirname(__file__))
            self.config_history_dir = os.path.join(project_root, 'config_history')
    
    def cleanup_old_files(self, keep_count: int = 20, max_age_days: int = 30) -> int:
        """
        清理旧的配置历史文件
        
        Args:
            keep_count: 保留的文件数量
            max_age_days: 文件最大保留天数
            
        Returns:
            删除的文件数量
        """
        if not os.path.exists(self.config_history_dir):
            logger.info("配置历史目录不存在")
            return 0
        
        # 获取所有配置历史文件
        pattern = os.path.join(self.config_history_dir, 'config_*.json')
        files = glob.glob(pattern)
        
        if len(files) <= keep_count:
            logger.info(f"配置历史文件数量({len(files)})未超过保留数量({keep_count})")
            return 0
        
        # 按修改时间排序（最新的在前）
        files_with_time = []
        for file_path in files:
            try:
                mtime = os.path.getmtime(file_path)
                files_with_time.append((file_path, mtime))
            except OSError:
                continue
        
        files_with_time.sort(key=lambda x: x[1], reverse=True)
        
        deleted_count = 0
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        # 保留最新的 keep_count 个文件
        files_to_keep = files_with_time[:keep_count]
        files_to_check = files_with_time[keep_count:]
        
        # 删除超出保留数量且超过最大保留天数的文件
        for file_path, mtime in files_to_check:
            file_time = datetime.fromtimestamp(mtime)
            
            # 删除超过最大保留天数的文件
            if file_time < cutoff_time:
                try:
                    os.remove(file_path)
                    logger.debug(f"已删除旧配置文件: {os.path.basename(file_path)}")
                    deleted_count += 1
                except OSError as e:
                    logger.error(f"删除文件 {file_path} 失败: {e}")
            else:
                # 如果文件还未超过最大保留天数，但超出了保留数量，也删除
                # 这种情况通常发生在短时间内产生大量配置文件时
                if len(files_with_time) - deleted_count > keep_count:
                    try:
                        os.remove(file_path)
                        logger.debug(f"已删除多余配置文件: {os.path.basename(file_path)}")
                        deleted_count += 1
                    except OSError as e:
                        logger.error(f"删除文件 {file_path} 失败: {e}")
        
        if deleted_count > 0:
            logger.info(f"配置历史清理完成，删除了 {deleted_count} 个文件")
            remaining_files = len(files) - deleted_count
            logger.info(f"剩余配置历史文件: {remaining_files} 个")
        else:
            logger.info("无需清理配置历史文件")
        
        return deleted_count
    
    def get_history_stats(self) -> dict:
        """获取配置历史统计信息"""
        if not os.path.exists(self.config_history_dir):
            return {"total_files": 0, "total_size": 0, "oldest_file": None, "newest_file": None}
        
        pattern = os.path.join(self.config_history_dir, 'config_*.json')
        files = glob.glob(pattern)
        
        if not files:
            return {"total_files": 0, "total_size": 0, "oldest_file": None, "newest_file": None}
        
        total_size = 0
        oldest_time = float('inf')
        newest_time = 0
        oldest_file = None
        newest_file = None
        
        for file_path in files:
            try:
                stat = os.stat(file_path)
                total_size += stat.st_size
                mtime = stat.st_mtime
                
                if mtime < oldest_time:
                    oldest_time = mtime
                    oldest_file = os.path.basename(file_path)
                
                if mtime > newest_time:
                    newest_time = mtime
                    newest_file = os.path.basename(file_path)
                    
            except OSError:
                continue
        
        return {
            "total_files": len(files),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_file": oldest_file,
            "newest_file": newest_file,
            "oldest_date": datetime.fromtimestamp(oldest_time).strftime("%Y-%m-%d %H:%M:%S") if oldest_time != float('inf') else None,
            "newest_date": datetime.fromtimestamp(newest_time).strftime("%Y-%m-%d %H:%M:%S") if newest_time > 0 else None
        }

def main():
    """独立运行清理工具"""
    cleanup = ConfigHistoryCleanup()
    
    # 显示当前状态
    stats = cleanup.get_history_stats()
    print(f"配置历史统计:")
    print(f"  文件数量: {stats['total_files']}")
    print(f"  总大小: {stats['total_size_mb']} MB")
    print(f"  最旧文件: {stats['oldest_file']} ({stats['oldest_date']})")
    print(f"  最新文件: {stats['newest_file']} ({stats['newest_date']})")
    
    # 执行清理
    deleted = cleanup.cleanup_old_files(keep_count=20, max_age_days=30)
    
    if deleted > 0:
        # 显示清理后状态
        new_stats = cleanup.get_history_stats()
        print(f"\n清理完成:")
        print(f"  删除文件: {deleted} 个")
        print(f"  剩余文件: {new_stats['total_files']} 个")
        print(f"  节省空间: {round((stats['total_size'] - new_stats['total_size']) / (1024 * 1024), 2)} MB")

if __name__ == "__main__":
    main()