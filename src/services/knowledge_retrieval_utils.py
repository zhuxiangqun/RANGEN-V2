#!/usr/bin/env python3
"""
Knowledge Retrieval Utilities - Query Processing Helpers

提取的知识检索辅助函数
"""
import re
import os
from typing import List, Dict, Any, Optional


def normalize_query(query: str) -> str:
    """标准化查询字符串"""
    # 去除首尾空白
    query = query.strip()
    # 转换为小写
    query = query.lower()
    # 移除多余空格
    query = re.sub(r'\s+', ' ', query)
    return query


def is_likely_question(text: str) -> bool:
    """判断文本是否为问题"""
    question_indicators = [
        '?', '什么', '怎么', '如何', '为什么', '哪',
        'who', 'what', 'where', 'when', 'why', 'how',
        '请问', '能否', '是否', '有没有'
    ]
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in question_indicators)


def extract_keywords(query: str, max_keywords: int = 5) -> List[str]:
    """提取查询关键词"""
    # 简单实现：按空格分词，移除停用词
    stop_words = {'的', '了', '是', '在', '和', '与', '或', '及', '等', 'the', 'a', 'an', 'is', 'are', 'in', 'on'}
    
    words = query.split()
    keywords = [w for w in words if w not in stop_words and len(w) > 1]
    
    return keywords[:max_keywords]


def calculate_similarity_threshold(query_type: str, base_threshold: float = 0.7) -> float:
    """根据查询类型计算相似度阈值"""
    threshold_map = {
        'factual': 0.8,
        'conceptual': 0.6,
        'procedural': 0.65,
        'comparison': 0.55,
        'default': base_threshold
    }
    return threshold_map.get(query_type, base_threshold)


def get_dynamic_top_k(query_type: str, base_top_k: int = 10) -> int:
    """根据查询类型动态调整返回数量"""
    top_k_map = {
        'factual': base_top_k,
        'conceptual': base_top_k + 5,
        'procedural': base_top_k + 3,
        'comparison': base_top_k + 8,
        'default': base_top_k
    }
    return top_k_map.get(query_type, base_top_k)


def validate_query_input(query: str) -> bool:
    """验证查询输入是否有效"""
    if not query:
        return False
    if not isinstance(query, str):
        return False
    if len(query.strip()) < 2:
        return False
    return True


def get_retrieval_config() -> Dict[str, Any]:
    """获取检索配置"""
    return {
        'default_limit': int(os.environ.get('RETRIEVAL_DEFAULT_LIMIT', 10)),
        'similarity_threshold': float(os.environ.get('RETRIEVAL_SIMILARITY_THRESHOLD', 0.7)),
        'enable_rerank': os.environ.get('RETRIEVAL_ENABLE_RERANK', 'true').lower() == 'true',
        'enable_cache': os.environ.get('RETRIEVAL_ENABLE_CACHE', 'true').lower() == 'true',
        'cache_ttl': int(os.environ.get('RETRIEVAL_CACHE_TTL', 3600)),
    }


def extract_query_entities(query: str) -> List[str]:
    """从查询中提取实体"""
    # 简单实现：提取连续的大写字母开头的词
    entities = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', query)
    return entities


def classify_query_type(query: str) -> str:
    """分类查询类型"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['多少', '几个', '数量', 'how many', 'number']):
        return 'factual'
    elif any(word in query_lower for word in ['比较', '区别', '差异', 'compare', 'difference']):
        return 'comparison'
    elif any(word in query_lower for word in ['如何', '怎么', '方法', 'how to', 'method']):
        return 'procedural'
    elif any(word in query_lower for word in ['是什么', '什么是', '概念', 'what is', 'concept']):
        return 'conceptual'
    else:
        return 'default'
