"""
知识检索工具模块
包含枚举类和通用工具函数
"""

from enum import Enum
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """查询类型枚举"""
    QUESTION = "question"
    EXPLANATION = "explanation"
    COMPARISON = "comparison"
    ANALYSIS = "analysis"
    GENERAL = "general"


class KnowledgeSource(Enum):
    """知识源枚举"""
    WIKI = "wiki"
    FAISS = "faiss"
    FALLBACK = "fallback"
    CACHE = "cache"

