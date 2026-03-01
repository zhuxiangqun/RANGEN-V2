#!/usr/bin/env python3
"""
混合检索系统 (Hybrid Retrieval System)
结合向量检索和推理式检索，提供更准确的检索结果

功能:
1. 统一检索接口
2. 多策略检索
3. 结果融合与重排序
4. 可解释性输出
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from .tree_index_builder import TreeIndexBuilder
from .reasoning_retrieval import ReasoningRetrievalAgent, RetrievalResult, RetrievalStrategy
from ..utils.logger import get_logger

logger = get_logger()


class RetrievalMode(Enum):
    """检索模式"""
    VECTOR_ONLY = "vector_only"  # 仅向量检索
    REASONING_ONLY = "reasoning_only"  # 仅推理式检索
    HYBRID = "hybrid"  # 混合检索
    ADAPTIVE = "adaptive"  # 自适应选择


@dataclass
class HybridRetrievalConfig:
    """混合检索配置"""
    mode: RetrievalMode = RetrievalMode.HYBRID
    vector_weight: float = 0.5  # 向量检索权重
    reasoning_weight: float = 0.5  # 推理式检索权重
    top_k: int = 5  # 返回结果数
    enable_rerank: bool = True  # 是否重排序
    min_relevance_score: float = 0.3  # 最低相关性阈值


@dataclass 
class ExplainableResult:
    """可解释检索结果"""
    content: str
    relevance_score: float
    source: str  # 检索来源 (vector/reasoning)
    section_path: str  # 章节路径
    page_number: Optional[int] = None
    reasoning: str = ""  # 推理说明
    citations: List[str] = field(default_factory=list)  # 引用
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "relevance_score": self.relevance_score,
            "source": self.source,
            "section_path": self.section_path,
            "page_number": self.page_number,
            "reasoning": self.reasoning,
            "citations": self.citations,
            "metadata": self.metadata
        }


class HybridRetrievalSystem:
    """混合检索系统"""
    
    def __init__(
        self,
        config: Optional[HybridRetrievalConfig] = None,
        vector_retriever: Optional[Callable] = None,
        tree_index_builder: Optional[TreeIndexBuilder] = None,
    ):
        """
        初始化混合检索系统
        
        Args:
            config: 混合检索配置
            vector_retriever: 向量检索回调
            tree_index_builder: 树索引构建器
        """
        self.logger = logger
        self.config = config or HybridRetrievalConfig()
        self.vector_retriever = vector_retriever
        
        # 初始化推理式检索智能体
        self.reasoning_agent = ReasoningRetrievalAgent(
            tree_index_builder=tree_index_builder,
            vector_retriever=vector_retriever
        )
        
        # 检索统计
        self.stats = {
            "total_queries": 0,
            "vector_only_count": 0,
            "reasoning_only_count": 0,
            "hybrid_count": 0,
            "adaptive_count": 0
        }
    
    def set_llm_service(self, llm_service):
        """设置LLM服务"""
        self.reasoning_agent.set_llm_service(llm_service)
    
    def set_vector_retriever(self, retriever: Callable):
        """设置向量检索回调"""
        self.vector_retriever = retriever
        self.reasoning_agent.set_vector_retriever(retriever)
    
    def retrieve(
        self,
        query: str,
        document_id: Optional[str] = None,
        mode: Optional[RetrievalMode] = None,
        **kwargs
    ) -> List[ExplainableResult]:
        """
        执行检索
        
        Args:
            query: 查询文本
            document_id: 文档ID (可选)
            mode: 检索模式 (可选)
            **kwargs: 其他参数
            
        Returns:
            可解释检索结果列表
        """
        self.stats["total_queries"] += 1
        
        # 确定检索模式
        if mode is None:
            mode = self.config.mode
        
        if mode == RetrievalMode.ADAPTIVE:
            mode = self._adaptive_select_mode(query)
        
        # 记录统计
        if mode == RetrievalMode.VECTOR_ONLY:
            self.stats["vector_only_count"] += 1
        elif mode == RetrievalMode.REASONING_ONLY:
            self.stats["reasoning_only_count"] += 1
        elif mode == RetrievalMode.HYBRID:
            self.stats["hybrid_count"] += 1
        
        # 执行检索
        self.logger.info(f"混合检索: query={query[:50]}..., mode={mode.value}")
        
        if mode == RetrievalMode.VECTOR_ONLY:
            results = self._vector_only_retrieve(query, document_id)
        elif mode == RetrievalMode.REASONING_ONLY:
            results = self._reasoning_only_retrieve(query, document_id)
        elif mode == RetrievalMode.HYBRID:
            results = self._hybrid_retrieve(query, document_id)
        else:
            results = self._hybrid_retrieve(query, document_id)
        
        # 重排序 (如果启用)
        if self.config.enable_rerank and len(results) > 1:
            results = self._rerank_results(query, results)
        
        # 限制结果数量
        results = results[:self.config.top_k]
        
        self.logger.info(f"混合检索完成: 返回 {len(results)} 个结果")
        return results
    
    def _adaptive_select_mode(self, query: str) -> RetrievalMode:
        """
        自适应选择检索模式
        
        根据查询特征选择合适的检索策略:
        - 简单事实查询 -> 向量检索
        - 复杂推理查询 -> 推理式检索
        - 混合查询 -> 混合检索
        """
        self.stats["adaptive_count"] += 1
        
        # 简单启发式规则
        query_length = len(query)
        has_numbers = any(c.isdigit() for c in query)
        has_comparison = any(word in query.lower() for word in [
            "比较", "vs", "versus", "difference", "哪个更好", "推荐"
        ])
        has_reasoning = any(word in query.lower() for word in [
            "为什么", "如何", "原因", "解释", "分析", "推理"
        ])
        
        # 复杂推理查询
        if has_reasoning or query_length > 50:
            return RetrievalMode.REASONING_ONLY
        
        # 比较查询
        if has_comparison:
            return RetrievalMode.HYBRID
        
        # 默认使用混合检索
        return RetrievalMode.HYBRID
    
    def _vector_only_retrieve(
        self,
        query: str,
        document_id: Optional[str]
    ) -> List[ExplainableResult]:
        """仅向量检索"""
        if not self.vector_retriever:
            return []
        
        try:
            vector_results = self.vector_retriever(
                query,
                top_k=self.config.top_k * 2  # 获取更多结果用于筛选
            )
            
            results = []
            for vr in vector_results:
                score = vr.get("similarity_score", 0.0)
                if score >= self.config.min_relevance_score:
                    result = ExplainableResult(
                        content=vr.get("content", ""),
                        relevance_score=score,
                        source="vector",
                        section_path=vr.get("section_path", ""),
                        page_number=vr.get("page_number"),
                        reasoning=f"向量相似度: {score:.3f}",
                        metadata=vr
                    )
                    results.append(result)
            
            return results
        except Exception as e:
            self.logger.error(f"向量检索失败: {e}")
            return []
    
    def _reasoning_only_retrieve(
        self,
        query: str,
        document_id: Optional[str]
    ) -> List[ExplainableResult]:
        """仅推理式检索"""
        reasoning_results = self.reasoning_agent.retrieve(
            query=query,
            document_id=document_id,
            strategy=RetrievalStrategy.REASONING
        )
        
        results = []
        for rr in reasoning_results:
            if rr.relevance_score >= self.config.min_relevance_score:
                result = ExplainableResult(
                    content=rr.content,
                    relevance_score=rr.relevance_score,
                    source="reasoning",
                    section_path=rr.section_path,
                    page_number=rr.page_number,
                    reasoning=rr.reasoning,
                    metadata=rr.metadata
                )
                results.append(result)
        
        return results
    
    def _hybrid_retrieve(
        self,
        query: str,
        document_id: Optional[str]
    ) -> List[ExplainableResult]:
        """混合检索"""
        # 并行执行两种检索
        vector_results = self._vector_only_retrieve(query, document_id)
        reasoning_results = self._reasoning_only_retrieve(query, document_id)
        
        # 合并结果
        merged_results = {}
        
        for result in vector_results:
            key = f"vector_{result.metadata.get('node_id', '')}"
            merged_results[key] = result
        
        for result in reasoning_results:
            key = f"reasoning_{result.metadata.get('node_id', '')}"
            if key in merged_results:
                # 合并分数 (加权平均)
                existing = merged_results[key]
                existing.relevance_score = (
                    existing.relevance_score * self.config.vector_weight +
                    result.relevance_score * self.config.reasoning_weight
                )
                existing.source = "hybrid"
                existing.reasoning += f"\n{result.reasoning}"
            else:
                merged_results[key] = result
        
        # 转换为列表并排序
        results = list(merged_results.values())
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results
    
    def _rerank_results(
        self,
        query: str,
        results: List[ExplainableResult]
    ) -> List[ExplainableResult]:
        """重排序结果"""
        if not results:
            return results
        
        # 如果有LLM服务，使用LLM重排序
        if hasattr(self, 'llm_service') and self.llm_service:
            try:
                # 构建重排序上下文
                context = f"查询: {query}\n\n"
                for i, result in enumerate(results[:5]):
                    context += f"{i+1}. {result.content[:500]}...\n\n"
                
                context += "请根据与查询的相关性重新排序以上结果，返回索引列表 (如: 3,1,5,2,4)"
                
                response = self.llm_service.generate(context)
                
                if response:
                    # 解析响应
                    # 尝试提取数字列表
                    import re
                    numbers = re.findall(r'\d+', response)
                    if numbers:
                        new_order = [int(n) - 1 for n in numbers[:len(results)]]
                        if all(0 <= i < len(results) for i in new_order):
                            results = [results[i] for i in new_order]
                            return results
            except Exception as e:
                self.logger.warning(f"LLM重排序失败: {e}")
        
        # 默认保持原顺序
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取检索统计"""
        return {
            **self.stats,
            "mode_distribution": {
                "vector_only": self.stats["vector_only_count"],
                "reasoning_only": self.stats["reasoning_only_count"],
                "hybrid": self.stats["hybrid_count"],
                "adaptive": self.stats["adaptive_count"]
            }
        }
    
    def reset_stats(self):
        """重置统计"""
        for key in self.stats:
            self.stats[key] = 0


# 单例模式
_hybrid_retrieval_instance: Optional['HybridRetrievalSystem'] = None


def get_hybrid_retrieval_system(
    config: Optional[HybridRetrievalConfig] = None,
    vector_retriever: Optional[Callable] = None,
    tree_index_builder: Optional[TreeIndexBuilder] = None
) -> HybridRetrievalSystem:
    """获取HybridRetrievalSystem单例"""
    global _hybrid_retrieval_instance
    if _hybrid_retrieval_instance is None:
        _hybrid_retrieval_instance = HybridRetrievalSystem(
            config=config,
            vector_retriever=vector_retriever,
            tree_index_builder=tree_index_builder
        )
    return _hybrid_retrieval_instance
