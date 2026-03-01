#!/usr/bin/env python3
"""
日志辅助工具
提供统一的日志格式化，包含模块标识（Agent、Tool等）
"""

import logging
import sys
from typing import Optional, Dict, Any


class ModuleLoggerAdapter(logging.LoggerAdapter):
    """模块日志适配器 - 在日志消息中添加模块标识"""
    
    def __init__(self, logger: logging.Logger, module_type: str, module_name: str, extra: Optional[Dict[str, Any]] = None):
        """
        初始化模块日志适配器
        
        Args:
            logger: 基础logger
            module_type: 模块类型（如 'Agent', 'Tool', 'Engine'等）
            module_name: 模块名称（如 'ReActAgent', 'RAGTool'等）
            extra: 额外的上下文信息
        """
        super().__init__(logger, extra or {})
        self.module_type = module_type
        self.module_name = module_name
    
    def process(self, msg, kwargs):
        """处理日志消息，添加模块标识"""
        # 格式化模块标识
        module_tag = f"[{self.module_type}:{self.module_name}]"
        
        # 在消息前添加模块标识
        formatted_msg = f"{module_tag} {msg}"
        
        return formatted_msg, kwargs


def get_module_logger(module_type: str, module_name: str, logger_name: Optional[str] = None) -> ModuleLoggerAdapter:
    """
    获取模块日志器 - 使用核心系统的统一日志模块
    
    Args:
        module_type: 模块类型（如 'Agent', 'Tool', 'Engine'等）
        module_name: 模块名称（如 'ReActAgent', 'RAGTool'等）
        logger_name: 基础logger名称（可选，默认使用模块名称）
        
    Returns:
        ModuleLoggerAdapter: 配置好的模块日志适配器，使用统一日志系统的文件处理器
    """
    if logger_name is None:
        logger_name = f"{module_type.lower()}.{module_name}"
    
    base_logger = logging.getLogger(logger_name)
    base_logger.setLevel(logging.INFO)
    
    # 使用核心系统的统一日志模块（research_logger）
    # 获取统一日志系统的logger，它已经有文件处理器
    try:
        from src.utils.research_logger import get_research_logger
        research_logger_instance = get_research_logger()
        research_logger_base = research_logger_instance.logger
        
        # 让模块logger成为research_logger的子logger，这样会自动继承文件处理器
        # 或者直接复用research_logger的文件处理器
        if not base_logger.handlers:
            # 复用统一日志系统的文件处理器
            for handler in research_logger_base.handlers:
                if isinstance(handler, logging.FileHandler):
                    # 创建新的handler实例，避免共享handler导致的问题
                    file_handler = logging.FileHandler(handler.baseFilename, mode='a', encoding='utf-8')
                    file_handler.setLevel(logging.INFO)
                    file_handler.setFormatter(handler.formatter)
                    base_logger.addHandler(file_handler)
                    break
    except Exception:
        # 如果导入失败，至少确保有控制台输出
        if not any(isinstance(h, logging.StreamHandler) for h in base_logger.handlers):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(message)s')
            console_handler.setFormatter(formatter)
            base_logger.addHandler(console_handler)
            
    # 🚀 修复：防止日志传播到root logger，导致重复输出
    base_logger.propagate = False
    
    return ModuleLoggerAdapter(base_logger, module_type, module_name)


def setup_console_logging_format():
    """设置控制台日志格式，包含模块标识"""
    # 获取根logger
    root_logger = logging.getLogger()
    
    # 创建格式器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 检查是否已有控制台处理器
    console_handler = None
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            console_handler = handler
            break
    
    # 如果没有，创建一个
    if console_handler is None:
        console_handler = logging.StreamHandler(sys.stdout)
        root_logger.addHandler(console_handler)
    
    # 设置格式
    console_handler.setFormatter(formatter)
    
    # 设置日志级别
    root_logger.setLevel(logging.INFO)


# 模块类型常量
class ModuleType:
    """模块类型常量"""
    AGENT = "Agent"
    TOOL = "Tool"
    ENGINE = "Engine"
    SYSTEM = "System"
    SERVICE = "Service"
    MANAGER = "Manager"
    INTEGRATION = "Integration"

