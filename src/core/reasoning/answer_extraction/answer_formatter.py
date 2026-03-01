"""
答案格式化器 - 统一格式化接口
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AnswerFormatter:
    """答案格式化器 - 清理和格式化答案文本"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format(self, answer: str, query: Optional[str] = None) -> str:
        """格式化答案
        
        Args:
            answer: 原始答案
            query: 查询文本（可选，用于上下文感知格式化）
            
        Returns:
            格式化后的答案
        """
        if not answer:
            return ""
        
        # 基础清理
        formatted = self._basic_clean(answer)
        
        # 移除格式标记
        formatted = self._remove_format_markers(formatted)
        
        # 规范化空白字符
        formatted = self._normalize_whitespace(formatted)
        
        # 移除常见前缀
        formatted = self._remove_common_prefixes(formatted)
        
        # 处理列表格式
        if query and self._is_list_format(formatted):
            formatted = self._extract_first_from_list(formatted)
        
        return formatted.strip()
    
    def _basic_clean(self, answer: str) -> str:
        """基础清理"""
        # 移除首尾空白
        cleaned = answer.strip()
        
        # 移除多余的换行符
        cleaned = re.sub(r'\n+', ' ', cleaned)
        
        return cleaned
    
    def _remove_format_markers(self, answer: str) -> str:
        """移除格式标记"""
        # 移除实体类型标签，如 "Person: John Doe" -> "John Doe"
        pattern = r'^[A-Z][^:]*\s*\([^)]+\)\s*:\s*'
        cleaned = re.sub(pattern, '', answer, flags=re.MULTILINE)
        
        # 移除其他格式标记
        cleaned = re.sub(r'\s*\(Entity\)\s*:', ':', cleaned)
        cleaned = re.sub(r'\s*\(Person\)\s*:', ':', cleaned)
        cleaned = re.sub(r'\s*\(Location\)\s*:', ':', cleaned)
        
        return cleaned
    
    def _normalize_whitespace(self, answer: str) -> str:
        """规范化空白字符"""
        # 将多个空白字符替换为单个空格
        cleaned = re.sub(r'\s+', ' ', answer)
        return cleaned.strip()
    
    def _remove_common_prefixes(self, answer: str) -> str:
        """移除常见前缀"""
        # 移除 "The answer is", "Answer:", 等前缀
        patterns = [
            r'^(the\s+answer\s+is|answer\s*[:\s]+|答案\s*[:\s]+)',
            r'^(therefore|so|thus|hence|consequently)\s*[,，]?\s*',
            r'^(based\s+on|according\s+to|from\s+the\s+evidence)\s+',
        ]
        
        for pattern in patterns:
            answer = re.sub(pattern, '', answer, flags=re.IGNORECASE)
        
        # 移除开头的 "the", "a", "an"（如果答案有多个词）
        words = answer.split()
        if len(words) > 1:
            if words[0].lower() in ['the', 'a', 'an']:
                answer = ' '.join(words[1:])
        
        return answer.strip()
    
    def _is_list_format(self, answer: str) -> bool:
        """判断是否是列表格式"""
        # 检查是否是多个连续的大写单词
        pattern = r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){3,}.*$'
        return len(answer) > 100 and bool(re.match(pattern, answer))
    
    def _extract_first_from_list(self, answer: str) -> str:
        """从列表中提取第一个答案"""
        # 尝试提取前两个大写单词（通常是完整的人名）
        match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})', answer)
        if match:
            return match.group(1)
        return answer

