"""
答案提取策略基类
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ExtractionStrategy(ABC):
    """答案提取策略基类
    
    使用策略模式，支持不同类型的答案提取方法：
    - LLM提取
    - 模式匹配提取
    - 语义理解提取
    - 认知增强提取
    """
    
    @abstractmethod
    def extract(
        self,
        query: str,
        evidence: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """提取答案
        
        Args:
            query: 查询文本
            evidence: 证据列表
            context: 上下文信息
            
        Returns:
            提取的答案，如果无法提取则返回None
        """
        pass
    
    @abstractmethod
    def can_handle(self, query: str, query_type: Optional[str] = None) -> bool:
        """判断是否可以处理该查询
        
        Args:
            query: 查询文本
            query_type: 查询类型
            
        Returns:
            如果可以处理返回True，否则返回False
        """
        pass

