#!/usr/bin/env python3
"""
答案格式化工具 - 智能截断和显示优化
"""

import html
import logging
import re
from typing import Optional, Tuple, Dict, Any, List
from src.utils.unified_centers import get_unified_center

logger = logging.getLogger(__name__)

def validate_input_data(data: str) -> bool:
    """验证输入数据"""
    dangerous_chars = ["<", ">", "'", "\"", "&", ";", "|", "`"]
    for char in dangerous_chars:
        if char in data:
            return False
    return True

class AnswerFormatter:
    """答案格式化器 - 提供智能截断和显示优化"""
    
    def __init__(self, max_display_length: int = 100, max_log_length: int = 100):
        self.max_display_length = max_display_length
        self.max_log_length = max_log_length
    
    def format_for_display(self, answer: str, max_length: Optional[int] = None) -> str:
        """格式化答案用于显示 - 智能截断"""
        try:
            # 验证输入
            if not self._validate_answer_input(answer):
                return "无效答案"
            
            if not answer:
                return "无答案"
            
            max_len = max_length or self.max_display_length
            
            # 如果答案长度在合理范围内不截断
            if len(answer) <= max_len:
                return answer
            
            # 智能截断
            return self._smart_truncate(answer, max_len)
            
        except Exception as e:
            logger.error(f"答案格式化失败: {e}")
            return "格式化错误"
    
    def _validate_answer_input(self, answer: str) -> bool:
        """验证答案输入"""
        if not isinstance(answer, str):
            return False
        
        # 检查危险字符
        dangerous_chars = ["<", ">", "'", "\"", "&", ";", "|", "`"]
        for char in dangerous_chars:
            if char in answer:
                return False
        
        return True
    
    def _smart_truncate(self, answer: str, max_length: int) -> str:
        """智能截断"""
        try:
            # 尝试在句号处截断
            if '.' in answer:
                sentences = answer.split('.')
                truncated = ""
                for sentence in sentences:
                    if len(truncated + sentence + '.') <= max_length:
                        truncated += sentence + '.'
                    else:
                        break
                if truncated:
                    return truncated.rstrip('.') + '...'
            
            # 尝试在逗号处截断
            if ',' in answer:
                parts = answer.split(',')
                truncated = ""
                for part in parts:
                    if len(truncated + part + ',') <= max_length:
                        truncated += part + ','
                    else:
                        break
                if truncated:
                    return truncated.rstrip(',') + '...'
            
            # 尝试在空格处截断
            if ' ' in answer:
                words = answer.split(' ')
                truncated = ""
                for word in words:
                    if len(truncated + word + ' ') <= max_length:
                        truncated += word + ' '
                    else:
                        break
                if truncated:
                    return truncated.rstrip() + '...'
            
            # 直接截断
            return answer[:max_length-3] + '...'
            
        except Exception as e:
            logger.warning(f"智能截断失败: {e}")
            return answer[:max_length-3] + '...'
    
    def format_for_log(self, text: str, max_length: Optional[int] = None) -> str:
        """格式化文本用于日志记录"""
        if not text:
            return "无内容"
        
        max_len = max_length or self.max_log_length
        
        if len(text) <= max_len:
            return text
        
        # 在单词边界截断
        truncated = text[:max_len]
        last_space = truncated.rfind(' ')
        
        if last_space > max_len * 0.8:  # 如果空格位置在80%之后
            return truncated[:last_space] + '...'
        else:
            return truncated + '...'
    
    def format_query_for_log(self, query: str) -> str:
        """格式化查询用于日志记录"""
        if not query:
            return "无查询"
        
        # 移除敏感信息
        query = self._remove_sensitive_info(query)
        
        # 限制长度
        if len(query) > self.max_log_length:
            return query[:self.max_log_length] + '...'
        
        return query
    
    def _remove_sensitive_info(self, text: str) -> str:
        """移除敏感信息"""
        # 简单的敏感信息过滤
        sensitive_patterns = [
            r'password\s*[:=]\s*\S+',
            r'token\s*[:=]\s*\S+',
            r'key\s*[:=]\s*\S+',
            r'secret\s*[:=]\s*\S+'
        ]
        
        for pattern in sensitive_patterns:
            text = re.sub(pattern, r'\1***', text, flags=re.IGNORECASE)
        
        return text
    
    def get_answer_summary(self, answer: str, max_length: int = 100) -> Dict[str, Any]:
        """获取答案摘要和是否截断标志"""
        if not answer:
            return {"answer": "无答案", "truncated": False}
        
        if len(answer) <= max_length:
            return {"answer": answer, "truncated": False}
        
        # 智能截断
        truncated = self.format_for_display(answer, max_length)
        is_truncated = len(truncated) < len(answer)
        return {"answer": truncated, "truncated": is_truncated}

# 全局实例
_answer_formatter = AnswerFormatter()

def get_answer_formatter() -> AnswerFormatter:
    """获取答案格式化器实例"""
    return _answer_formatter

def format_answer_for_display(answer: str, max_length: int = 100) -> str:
    """格式化答案用于显示"""
    return _answer_formatter.format_for_display(answer, max_length)

def format_text_for_log(text: str, max_length: int = 100) -> str:
    """格式化文本用于日志"""
    return _answer_formatter.format_for_log(text, max_length)

def format_query_for_log(query: str) -> str:
    """格式化查询用于日志"""
    return _answer_formatter.format_query_for_log(query)

def format_answer_for_log(answer: str) -> str:
    """格式化答案用于日志"""
    return _answer_formatter.format_for_log(answer)

# 扩展AnswerFormatter类的方法
def get_formatter_status(self) -> Dict[str, Any]:
    """获取格式化器状态"""
    try:
        return {
            "max_display_length": self.max_display_length,
            "max_log_length": self.max_log_length,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"获取格式化器状态失败: {e}")
        return {"error": str(e)}

def format_for_export(self, answer: str, format_type: str = "text") -> str:
    """格式化答案用于导出"""
    try:
        if not self._validate_answer_input(answer):
            return "无效答案"
        
        if format_type == "html":
            return self._format_as_html(answer)
        elif format_type == "markdown":
            return self._format_as_markdown(answer)
        elif format_type == "json":
            return self._format_as_json(answer)
        else:
            return answer
    except Exception as e:
        logger.error(f"导出格式化失败: {e}")
        return "格式化错误"

def _format_as_html(self, answer: str) -> str:
    """格式化为HTML"""
    try:
        # 转义HTML特殊字符
        escaped = html.escape(answer)
        # 将换行符转换为<br>标签
        formatted = escaped.replace('\n', '<br>')
        return f"<div class='answer'>{formatted}</div>"
    except Exception as e:
        logger.error(f"HTML格式化失败: {e}")
        return answer

def _format_as_markdown(self, answer: str) -> str:
    """格式化为Markdown"""
    try:
        # 将换行符转换为Markdown换行
        formatted = answer.replace('\n', '\n\n')
        return f"## 答案\n\n{formatted}"
    except Exception as e:
        logger.error(f"Markdown格式化失败: {e}")
        return answer

def _format_as_json(self, answer: str) -> str:
    """格式化为JSON"""
    try:
        import json
        data = {
            "answer": answer,
            "timestamp": time.time(),
            "formatted": True
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"JSON格式化失败: {e}")
        return answer

def get_formatting_metrics(self) -> Dict[str, Any]:
    """获取格式化指标"""
    try:
        return {
            "max_display_length": self.max_display_length,
            "max_log_length": self.max_log_length,
            "formatting_types": ["text", "html", "markdown", "json"],
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"获取格式化指标失败: {e}")
        return {"error": str(e)}

def optimize_formatting(self) -> Dict[str, Any]:
    """优化格式化"""
    try:
        optimization_results = {
            "optimization_applied": False,
            "improvements": [],
            "timestamp": time.time()
        }
        
        # 检查是否需要优化
        if self.max_display_length > 1000:
            optimization_results["improvements"].append("建议减少最大显示长度以提高性能")
            optimization_results["optimization_applied"] = True
        
        if self.max_log_length > 500:
            optimization_results["improvements"].append("建议减少最大日志长度以提高性能")
            optimization_results["optimization_applied"] = True
        
        return optimization_results
    except Exception as e:
        logger.error(f"优化格式化失败: {e}")
        return {"error": str(e)}

def health_check(self) -> Dict[str, Any]:
    """健康检查"""
    try:
        # 检查配置是否合理
        if self.max_display_length <= 0 or self.max_log_length <= 0:
            status = "unhealthy"
        elif self.max_display_length > 10000 or self.max_log_length > 10000:
            status = "degraded"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "max_display_length": self.max_display_length,
            "max_log_length": self.max_log_length,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

def get_formatter_info(self) -> Dict[str, Any]:
    """获取格式化器信息"""
    try:
        return {
            "name": "AnswerFormatter",
            "version": "1.0",
            "description": "智能答案格式化器",
            "features": [
                "智能截断",
                "多格式支持",
                "输入验证",
                "日志格式化"
            ],
            "max_display_length": self.max_display_length,
            "max_log_length": self.max_log_length,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"获取格式化器信息失败: {e}")
        return {"error": str(e)}

# 将方法添加到类中
AnswerFormatter.get_formatter_status = get_formatter_status
AnswerFormatter.format_for_export = format_for_export
AnswerFormatter._format_as_html = _format_as_html
AnswerFormatter._format_as_markdown = _format_as_markdown
AnswerFormatter._format_as_json = _format_as_json
AnswerFormatter.get_formatting_metrics = get_formatting_metrics
AnswerFormatter.optimize_formatting = optimize_formatting
AnswerFormatter.health_check = health_check
AnswerFormatter.get_formatter_info = get_formatter_info

# 添加缺失的导入
import time