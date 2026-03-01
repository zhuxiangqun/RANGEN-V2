#!/usr/bin/env python3
"""
知识库管理系统独立日志系统
不依赖其他系统的日志模块
"""

import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

class KnowledgeManagementLogger:
    """知识库管理系统独立日志系统"""
    
    _instance: Optional['KnowledgeManagementLogger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_logger()
        return cls._instance
    
    def _init_logger(self):
        """初始化日志系统"""
        if self._logger is not None:
            return
        
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 创建logger
        self._logger = logging.getLogger("knowledge_management_system")
        self._logger.setLevel(logging.INFO)
        
        # 避免重复添加handler
        if self._logger.handlers:
            # 即使已经有handler，也要确保不传播
            self._logger.propagate = False
            return
        
        # 文件handler
        log_file = log_dir / "knowledge_management.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台handler - 移除，因为root logger已经有控制台handler了
        # console_handler = logging.StreamHandler()
        # console_handler.setLevel(logging.INFO)
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        # console_handler.setFormatter(formatter)
        
        # 添加handler
        self._logger.addHandler(file_handler)
        # self._logger.addHandler(console_handler)
        
        # 🚀 修复：允许日志传播到root logger，由root logger统一输出到控制台
        # 这样既能写入文件（通过上面的file_handler），又能统一控制台输出格式
        self._logger.propagate = True
    
    def get_logger(self) -> logging.Logger:
        """获取logger实例"""
        return self._logger
    
    def info(self, message: str):
        """记录信息日志"""
        self._logger.info(message)
    
    def warning(self, message: str):
        """记录警告日志"""
        self._logger.warning(message)
    
    def error(self, message: str):
        """记录错误日志"""
        self._logger.error(message)
    
    def debug(self, message: str):
        """记录调试日志"""
        self._logger.debug(message)


# 单例访问函数
def get_logger() -> logging.Logger:
    """获取知识库管理系统logger"""
    return KnowledgeManagementLogger().get_logger()

def log_info(message: str):
    """记录信息日志"""
    KnowledgeManagementLogger().info(message)

def log_warning(message: str):
    """记录警告日志"""
    KnowledgeManagementLogger().warning(message)

def log_error(message: str):
    """记录错误日志"""
    KnowledgeManagementLogger().error(message)

def log_debug(message: str):
    """记录调试日志"""
    KnowledgeManagementLogger().debug(message)

