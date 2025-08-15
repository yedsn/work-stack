#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import threading
from logging.handlers import RotatingFileHandler

# 单例日志记录器
_logger = None
_logger_lock = threading.Lock()

def get_logger(name="launcher"):
    """
    获取应用程序日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    global _logger
    
    # 双重检查锁定模式
    if _logger is not None:
        return _logger
    
    with _logger_lock:
        # 再次检查，防止其他线程已经创建了logger
        if _logger is not None:
            return _logger
        
        # 创建日志目录
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, "app.log")
        
        # 日志格式
        log_format = "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        
        # 创建日志记录器
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)  # 改为DEBUG级别以便查看性能日志
        
        # 防止重复添加处理器
        if not logger.handlers:
            # 文件处理器 - 使用循环日志文件，最大5MB，保留3个备份
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3,
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(log_format, date_format))
            logger.addHandler(file_handler)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(log_format, date_format))
            logger.addHandler(console_handler)
        
        _logger = logger
        return logger

def set_log_level(level):
    """
    设置日志级别
    
    Args:
        level: 日志级别 (logging.DEBUG, logging.INFO, 等)
    """
    logger = get_logger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level) 