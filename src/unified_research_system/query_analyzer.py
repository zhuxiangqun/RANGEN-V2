"""
查询分析器模块

从 UnifiedResearchSystem 拆分出来的查询分析功能
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class QueryAnalysis:
    """查询分析结果"""
    complexity: float  # 0-1 复杂度
    query_type: str   # 查询类型
    features: Dict[str, Any]  # 特征


class QueryAnalyzer:
    """
    查询分析器
    
    分析查询的:
    - 复杂度
    - 类型
    - 特征
    """
    
    def __init__(self):
        # 复杂度阈值
        self._simple_threshold = 0.3
        self._moderate_threshold = 0.6
        
        # 查询类型关键词
        self._query_type_keywords = {
            "research": ["研究", "分析", "调查", "research", "analyze", "investigate"],
            "comparison": ["比较", "对比", "差异", "compare", "difference", "versus"],
            "definition": ["什么是", "定义", "解释", "什么是", "definition", "explain"],
            "howto": ["如何", "怎么办", "怎样", "how to", "how do i", "步骤"],
            "fact": ["谁", "什么", "哪里", "when", "where", "who", "what"],
            "opinion": ["看法", "观点", "认为", "opinion", "think", "believe"],
            "list": ["列出", "列举", "有哪些", "list", "examples", "items"],
        }
    
    def _analyze_query_complexity(self, query: str) -> float:
        """
        分析查询复杂度
        
        基于以下因素:
        - 查询长度
        - 关键词数量
        - 问题结构复杂度
        - 是否包含多个问题
        """
        complexity = 0.0
        
        # 1. 长度因素 (0-0.3)
        query_len = len(query)
        if query_len < 20:
            complexity += 0.0
        elif query_len < 50:
            complexity += 0.1
        elif query_len < 100:
            complexity += 0.2
        else:
            complexity += 0.3
        
        # 2. 关键词复杂度 (0-0.3)
        technical_keywords = [
            "分析", "比较", "评估", "研究", "analyze", "compare", "evaluate",
            "为什么", "如何", "为什么", "why", "how", "原理", "机制",
            "影响", "因素", "原因", "effect", "factor", "cause",
        ]
        keyword_count = sum(1 for kw in technical_keywords if kw.lower() in query.lower())
        complexity += min(0.3, keyword_count * 0.05)
        
        # 3. 问题结构复杂度 (0-0.2)
        # 多个问题标记
        question_markers = query.count("?") + query.count("？")
        if question_markers > 1:
            complexity += 0.2
        elif question_markers == 1:
            complexity += 0.1
        
        # 4. 条件句复杂度 (0-0.2)
        conditional_keywords = ["如果", "则", "但是", "或者", "还是", "if", "then", "but", "or"]
        conditional_count = sum(1 for kw in conditional_keywords if kw.lower() in query.lower())
        complexity += min(0.2, conditional_count * 0.05)
        
        return min(1.0, complexity)
    
    def _extract_context_features(self, request) -> Dict[str, Any]:
        """提取上下文特征"""
        context = getattr(request, "context", {}) or {}
        metadata = getattr(request, "metadata", {}) or {}
        
        features = {
            "has_user_context": bool(context.get("user_id")),
            "has_session_context": bool(context.get("session_id")),
            "has_history": bool(context.get("history")),
            "priority": metadata.get("priority", "normal"),
            "timeout": getattr(request, "timeout", 1800),
        }
        
        return features
    
    def _analyze_agent_suitability(
        self, 
        agent_name: str, 
        request
    ) -> float:
        """
        分析 Agent 适合度
        
        返回 0-1 的分数
        """
        query = request.query
        complexity = self._analyze_query_complexity(query)
        
        # 不同 Agent 的适用场景
        agent_suitability = {
            "knowledge": {
                "simple": 0.9,
                "moderate": 0.7,
                "complex": 0.4,
            },
            "reasoning": {
                "simple": 0.5,
                "moderate": 0.8,
                "complex": 0.9,
            },
            "answer": {
                "simple": 0.9,
                "moderate": 0.8,
                "complex": 0.6,
            },
            "citation": {
                "simple": 0.7,
                "moderate": 0.8,
                "complex": 0.9,
            },
            "chief": {
                "simple": 0.3,
                "moderate": 0.6,
                "complex": 0.9,
            },
        }
        
        # 确定复杂度级别
        if complexity < self._simple_threshold:
            complexity_level = "simple"
        elif complexity < self._moderate_threshold:
            complexity_level = "moderate"
        else:
            complexity_level = "complex"
        
        # 获取适合度
        suitability = agent_suitability.get(agent_name, {}).get(complexity_level, 0.5)
        
        return suitability
    
    def analyze(self, query: str) -> QueryAnalysis:
        """分析查询"""
        # 计算复杂度
        complexity = self._analyze_query_complexity(query)
        
        # 确定查询类型
        query_type = self._classify_query_type(query)
        
        # 构建特征
        features = {
            "length": len(query),
            "word_count": len(query.split()),
            "has_question": "?" in query or "？" in query,
            "complexity_level": "simple" if complexity < self._simple_threshold else "moderate" if complexity < self._moderate_threshold else "complex",
        }
        
        return QueryAnalysis(
            complexity=complexity,
            query_type=query_type,
            features=features,
        )
    
    def _classify_query_type(self, query: str) -> str:
        """分类查询类型"""
        query_lower = query.lower()
        
        # 匹配查询类型
        for query_type, keywords in self._query_type_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return query_type
        
        # 默认类型
        return "general"
    
    def should_use_mas(self, request) -> bool:
        """
        判断是否应该使用多智能体系统 (MAS)
        
        基于查询复杂度和上下文
        """
        complexity = self._analyze_query_complexity(request.query)
        
        # 复杂查询使用 MAS
        if complexity >= self._moderate_threshold:
            return True
        
        # 有历史记录，使用 MAS
        context = getattr(request, "context", {}) or {}
        if context.get("history"):
            return True
        
        # 高优先级查询使用 MAS
        metadata = getattr(request, "metadata", {}) or {}
        if metadata.get("priority") == "high":
            return True
        
        return False
