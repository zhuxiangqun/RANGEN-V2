"""
基础分析器类
定义所有分析器的通用接口和基础功能
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseAnalyzer(ABC):
    """基础分析器抽象类"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def analyze(self, log_content: str) -> Dict[str, Any]:
        """分析日志内容，返回分析结果"""
        pass
    
    def _extract_pattern_matches(self, log_content: str, patterns: List[str], 
                                case_sensitive: bool = False, multiline: bool = False) -> List[str]:
        """提取正则表达式匹配的内容"""
        matches = []
        flags = 0 if case_sensitive else re.IGNORECASE
        if multiline:
            flags |= re.MULTILINE | re.DOTALL
        
        for pattern in patterns:
            try:
                pattern_matches = re.findall(pattern, log_content, flags)
                matches.extend(pattern_matches)
            except re.error as e:
                self.logger.warning(f"正则表达式错误: {pattern}, {e}")
                continue
        
        return matches
    
    def _extract_numeric_values(self, log_content: str, patterns: List[str]) -> List[float]:
        """提取数值"""
        values = []
        matches = self._extract_pattern_matches(log_content, patterns)
        
        for match in matches:
            try:
                # 如果match是元组，取第一个元素
                if isinstance(match, tuple):
                    match = match[0]
                values.append(float(match))
            except (ValueError, TypeError) as e:
                self.logger.warning(f"无法转换数值: {match}, 错误: {e}")
                continue
        
        return values
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度 - Jaccard相似度"""
        if not s1 or not s2:
            return 0.0
        
        set1 = set(s1.lower().split())
        set2 = set(s2.lower().split())
        
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _safe_divide(self, numerator: float, denominator: float, default: float = 0.0) -> float:
        """安全除法，避免除零错误"""
        return numerator / denominator if denominator != 0 else default
    
    def _calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """计算基础统计信息"""
        if not values:
            return {
                "average": 0.0,
                "max": 0.0,
                "min": 0.0,
                "count": 0,
                "sum": 0.0
            }
        
        return {
            "average": sum(values) / len(values),
            "max": max(values),
            "min": min(values),
            "count": len(values),
            "sum": sum(values)
        }
