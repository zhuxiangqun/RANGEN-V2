#!/usr/bin/env python3
"""
研究系统日志记录器 - 简化版本
功能已合并到utils模块中
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ResearchLogEntry:
    """研究日志条目 - 标准化格式"""
    timestamp: str
    request_id: str
    query: str
    result: str
    confidence: float
    processing_time: float
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ResearchLogger:
    """研究系统日志记录器 - 简化版本"""
    
    def __init__(self, log_file: str = "research_system.log"):
        self.log_file = log_file
        self.logger = logging.getLogger("research_system")
        self.logger.setLevel(logging.INFO)
        
        # 确保根日志级别也设置为INFO
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # 创建文件处理器 - 使用覆盖模式
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建JSON格式化器
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        
        # 确保没有重复的处理器
        if len(self.logger.handlers) > 1:
            self.logger.handlers = [file_handler]
        
        # 统计信息
        self.log_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0.0
        }
    
    def log_research_request(self, request_id: str, query: str, context: Optional[Dict[str, Any]] = None):
        """记录研究请求"""
        try:
            log_entry = {
                "event_type": "research_request",
                "timestamp": datetime.now().isoformat(),
                "request_id": request_id,
                "query": query,
                "context": context or {}
            }
            
            self.logger.info(json.dumps(log_entry, ensure_ascii=False))
            self.log_stats["total_requests"] += 1
            
        except Exception as e:
            self.logger.error(f"记录研究请求失败: {e}")
    
    def log_research_response(self, request_id: str, query: str, result: str, 
                            confidence: float, processing_time: float, 
                            success: bool = True, error: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None):
        """记录研究响应"""
        try:
            log_entry = ResearchLogEntry(
                timestamp=datetime.now().isoformat(),
                request_id=request_id,
                query=query,
                result=result,
                confidence=confidence,
                processing_time=processing_time,
                success=success,
                error=error,
                metadata=metadata
            )
            
            self.logger.info(json.dumps(asdict(log_entry), ensure_ascii=False))
            
            if success:
                self.log_stats["successful_requests"] += 1
            else:
                self.log_stats["failed_requests"] += 1
            
            self.log_stats["total_processing_time"] += processing_time
            
        except Exception as e:
            self.logger.error(f"记录研究响应失败: {e}")
    
    def log_error(self, request_id: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """记录错误"""
        try:
            log_entry = {
                "event_type": "error",
                "timestamp": datetime.now().isoformat(),
                "request_id": request_id,
                "error": error_message,
                "context": context or {}
            }
            
            self.logger.error(json.dumps(log_entry, ensure_ascii=False))
            
        except Exception as e:
            self.logger.error(f"记录错误失败: {e}")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        stats = self.log_stats.copy()
        if stats["total_requests"] > 0:
            stats["average_processing_time"] = stats["total_processing_time"] / stats["total_requests"]
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
        else:
            stats["average_processing_time"] = 0.0
            stats["success_rate"] = 0.0
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.log_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0.0
        }


# 全局实例
research_logger = ResearchLogger()


def get_research_logger() -> ResearchLogger:
    """获取研究日志记录器实例"""
    return research_logger


# 便捷函数
def log_research_request(request_id: str, query: str, context: Optional[Dict[str, Any]] = None):
    """记录研究请求"""
    research_logger.log_research_request(request_id, query, context)


def log_research_response(request_id: str, query: str, result: str, 
                         confidence: float, processing_time: float, 
                         success: bool = True, error: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None):
    """记录研究响应"""
    research_logger.log_research_response(request_id, query, result, confidence, 
                                        processing_time, success, error, metadata)


def log_error(request_id: str, error_message: str, context: Optional[Dict[str, Any]] = None):
    """记录错误"""
    research_logger.log_error(request_id, error_message, context)


def log_info(message: str, *args, **kwargs):
    """记录信息"""
    if args:
        message = message.format(*args)
    research_logger.logger.info(message)


def log_warning(message: str):
    """记录警告"""
    research_logger.logger.warning(message)


def log_debug(message: str):
    """记录调试信息"""
    research_logger.logger.debug(message)


# 错误处理器
class UnifiedErrorHandler:
    """统一错误处理器"""
    
    @staticmethod
    def handle_error(error: Exception, context: str = "unknown"):
        """处理错误"""
        error_message = f"错误在 {context}: {str(error)}"
        research_logger.logger.error(error_message)