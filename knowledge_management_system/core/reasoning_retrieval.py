#!/usr/bin/env python3
"""
推理式检索智能体 (Reasoning Retrieval Agent)
参考 PageIndex 框架 - 使用LLM推理进行类人检索

核心功能:
1. 基于树结构进行推理式检索
2. 模拟人类专家浏览文档的方式
3. 提供可解释的检索结果
4. 支持多轮推理和回溯

参考: https://github.com/VectifyAI/PageIndex
"""

import os
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from .tree_index_builder import TreeIndexBuilder, DocumentIndex, TreeNode
from ..utils.logger import get_logger

logger = get_logger()


class RetrievalStrategy(Enum):
    """检索策略"""
    REASONING = "reasoning"  # 推理式检索
    VECTOR = "vector"  # 向量检索
    HYBRID = "hybrid"  # 混合检索


@dataclass
class RetrievalResult:
    """检索结果"""
    content: str
    node_id: str
    section_path: str  # 章节路径
    page_number: Optional[int] = None
    relevance_score: float = 0.0
    reasoning: str = ""  # 推理过程
    summary: str = ""  # 内容摘要
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "node_id": self.node_id,
            "section_path": self.section_path,
            "page_number": self.page_number,
            "relevance_score": self.relevance_score,
            "reasoning": self.reasoning,
            "summary": self.summary,
            "metadata": self.metadata
        }


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_number: int
    action: str  # 采取的行动
    thought: str  # 思考过程
    node_visited: str  # 访问的节点
    relevance_assessment: str  # 相关性评估
    continue_search: bool  # 是否继续搜索


class ReasoningRetrievalAgent:
    """推理式检索智能体"""
    
    def __init__(
        self,
        tree_index_builder: Optional[TreeIndexBuilder] = None,
        vector_retriever: Optional[Callable] = None,  # 向量检索回调
        max_reasoning_steps: int = 5,
        max_results: int = 5,
    ):
        """
        初始化推理式检索智能体
        
        Args:
            tree_index_builder: 树索引构建器
            vector_retriever: 向量检索回调函数 (可选)
            max_reasoning_steps: 最大推理步数
            max_results: 最大返回结果数
        """
        self.logger = logger
        self.tree_index_builder = tree_index_builder or TreeIndexBuilder()
        self.vector_retriever = vector_retriever
        self.max_reasoning_steps = max_reasoning_steps
        self.max_results = max_results
        
        # LLM服务 (用于推理)
        self.llm_service = None
        
        # 检索历史
        self.retrieval_history: List[List[RetrievalResult]] = []
    
    def set_llm_service(self, llm_service):
        """设置LLM服务"""
        self.llm_service = llm_service
        self.tree_index_builder.set_llm_service(llm_service)
    
    def set_vector_retriever(self, retriever: Callable):
        """设置向量检索回调"""
        self.vector_retriever = retriever
    
    def retrieve(
        self,
        query: str,
        document_id: Optional[str] = None,
        strategy: RetrievalStrategy = RetrievalStrategy.REASONING,
        **kwargs
    ) -> List[RetrievalResult]:
        """
        检索相关文档内容
        
        Args:
            query: 查询文本
            document_id: 文档ID (可选)
            strategy: 检索策略
            **kwargs: 其他参数
            
        Returns:
            检索结果列表
        """
        self.logger.info(f"推理式检索: query={query[:50]}..., strategy={strategy.value}")
        
        if strategy == RetrievalStrategy.REASONING:
            return self._reasoning_retrieve(query, document_id)
        elif strategy == RetrievalStrategy.VECTOR:
            return self._vector_retrieve(query, document_id)
        elif strategy == RetrievalStrategy.HYBRID:
            return self._hybrid_retrieve(query, document_id)
        else:
            return self._reasoning_retrieve(query, document_id)
    
    def _reasoning_retrieve(
        self,
        query: str,
        document_id: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        推理式检索 - 使用LLM遍历树结构
        
        核心算法:
        1. 从根节点开始
        2. 让LLM评估当前节点是否相关
        3. 基于推理决定下一步方向
        4. 重复直到找到足够相关的内容
        """
        # 获取文档索引
        if document_id:
            doc_index = self.tree_index_builder.get_index(document_id)
            if not doc_index:
                self.logger.warning(f"未找到文档索引: {document_id}")
                return self._fallback_to_vector(query)
        else:
            # 如果没有指定文档，尝试从所有文档检索
            return self._reasoning_retrieve_multi_doc(query)
        
        if not doc_index or not doc_index.root:
            return self._fallback_to_vector(query)
        
        # 开始检索
        results推理式 = []
        reasoning_steps = []
        
        # 第一步：评估根节点
        current_node = doc_index.root
        visited_nodes = set()
        
        for step in range(self.max_reasoning_steps):
            if not current_node:
                break
            
            visited_nodes.add(current_node.node_id)
            
            # 评估当前节点与查询的相关性
            relevance, thought = self._evaluate_node_relevance(
                query, current_node, step
            )
            
            reasoning_step = ReasoningStep(
                step_number=step + 1,
                action="evaluate",
                thought=thought,
                node_visited=current_node.node_id,
                relevance_assessment=relevance,
                continue_search=True
            )
            reasoning_steps.append(reasoning_step)
            
            if relevance > 0.7:
                # 高相关性，添加到结果
                result = self._create_result_from_node(
                    query, current_node, doc_index, relevance, thought
                )
                results.append(result)
                
                # 继续搜索子节点
                if current_node.nodes:
                    # 选择最相关的子节点继续
                    current_node = self._select_best_child(
                        query, current_node.nodes
                    )
                else:
                    break
            elif relevance > 0.3:
                # 中等相关，搜索子节点
                if current_node.nodes:
                    current_node = self._select_best_child(
                        query, current_node.nodes
                    )
                else:
                    break
            else:
                # 低相关性，尝试其他路径
                break
            
            # 限制结果数量
            if len(results) >= self.max_results:
                break
        
        # 如果没有找到足够的结果，使用向量检索补充
        if len(results) < self.max_results:
            vector_results = self._fallback_to_vector(query, document_id)
            results.extend(vector_results[:self.max_results - len(results)])
        
        self.retrieval_history.append(results)
        self.logger.info(f"推理式检索完成: 找到 {len(results)} 个结果")
        
        return results[:self.max_results]
    
    def _reasoning_retrieve_multi_doc(
        self,
        query: str
    ) -> List[RetrievalResult]:
        """从多个文档进行推理式检索"""
        all_results = []
        
        # 获取所有索引的文档
        indices = self.tree_index_builder.get_all_indices()
        
        for doc_id, doc_index in indices.items():
            if not doc_index.root:
                continue
            
            # 对每个文档进行推理式检索
            results = self._reasoning_retrieve(query, doc_id)
            all_results.extend(results)
        
        # 按相关性排序
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return all_results[:self.max_results]
    
    def _evaluate_node_relevance(
        self,
        query: str,
        node: TreeNode,
        step: int
    ) -> tuple:
        """
        评估节点与查询的相关性
        
        Returns:
            (相关性分数, 推理说明)
        """
        # 如果有LLM服务，使用LLM评估
        if self.llm_service:
            try:
                # 构建上下文
                context = f"""
查询: {query}

节点标题: {node.title}
节点摘要: {node.summary}
节点层级: {node.level}
节点ID: {node.node_id}

请评估这个节点与查询的相关性 (0-1分)，并解释你的推理过程。
格式: 分数|推理说明
"""
                response = self.llm_service.generate(context)
                
                if response:
                    # 解析响应
                    lines = response.strip().split('\n')
                    for line in lines:
                        if '|' in line:
                            parts = line.split('|', 1)
                            try:
                                score = float(parts[0].strip())
                                reasoning = parts[1].strip() if len(parts) > 1 else ""
                                return score, reasoning
                            except ValueError:
                                continue
            except Exception as e:
                self.logger.warning(f"LLM评估失败: {e}")
        
        # 回退：使用简单的关键词匹配
        return self._simple_relevance评估(query, node)
    
    def _simple_relevance评估(self, query: str, node: TreeNode) -> tuple:
        """简单的相关性评估 (关键词匹配)"""
        query_lower = query.lower()
        
        # 合并节点信息
        node_text = f"{node.title} {node.summary} {node.content}".lower()
        
        # 计算查询词在节点中的出现次数
        query_words = set(query_lower.split())
        matches = sum(1 for word in query_words if word in node_text)
        
        # 计算相关性分数
        score = min(1.0, matches / max(1, len(query_words)))
        
        # 标题匹配权重更高
        if any(word in node.title.lower() for word in query_words):
            score = min(1.0, score + 0.3)
        
        reasoning = f"关键词匹配: {matches}/{len(query_words)}"
        
        return score, reasoning
    
    def _select_best_child(
        self,
        query: str,
        children: List[TreeNode]
    ) -> Optional[TreeNode]:
        """选择最相关的子节点"""
        if not children:
            return None
        
        # 评估所有子节点
        best_node = None
        best_score = -1
        
        for child in children:
            score, _ = self._evaluate_node_relevance(query, child, 0)
            if score > best_score:
                best_score = score
                best_node = child
        
        return best_node
    
    def _create_result_from_node(
        self,
        query: str,
        node: TreeNode,
        doc_index: DocumentIndex,
        relevance: float,
        reasoning: str
    ) -> RetrievalResult:
        """从节点创建检索结果"""
        # 构建章节路径
        section_path = self._build_section_path(node, doc_index)
        
        # 截取内容
        content = node.content[:5000] if node.content else ""
        
        return RetrievalResult(
            content=content,
            node_id=node.node_id,
            section_path=section_path,
            page_number=node.start_index,  # 使用start_index作为页码
            relevance_score=relevance,
            reasoning=reasoning,
            summary=node.summary,
            metadata={
                "document_id": doc_index.document_id,
                "document_title": doc_index.title,
                "node_level": node.level,
                "start_index": node.start_index,
                "end_index": node.end_index
            }
        )
    
    def _build_section_path(self, node: TreeNode, doc_index: DocumentIndex) -> str:
        """构建章节路径"""
        path_parts = [doc_index.title]
        
        # 找到从根到当前节点的路径
        if doc_index.root:
            path = self._find_path(doc_index.root, node.node_id)
            if path:
                path_parts.extend([n.title for n in path])
        
        return " > ".join(path_parts)
    
    def _find_path(
        self,
        node: TreeNode,
        target_id: str,
        path: Optional[List[TreeNode]] = None
    ) -> Optional[List[TreeNode]]:
        """查找从根到目标节点的路径"""
        if path is None:
            path = []
        
        path.append(node)
        
        if node.node_id == target_id:
            return path
        
        for child in node.nodes:
            result = self._find_path(child, target_id, path.copy())
            if result:
                return result
        
        return None
    
    def _vector_retrieve(
        self,
        query: str,
        document_id: Optional[str] = None
    ) -> List[RetrievalResult]:
        """使用向量检索"""
        if not self.vector_retriever:
            return []
        
        try:
            # 调用向量检索回调
            vector_results = self.vector_retriever(query, top_k=self.max_results)
            
            # 转换为检索结果格式
            results = []
            for i, vr in enumerate(vector_results):
                result = RetrievalResult(
                    content=vr.get("content", ""),
                    node_id=vr.get("knowledge_id", ""),
                    section_path="",
                    relevance_score=vr.get("similarity_score", 0.0),
                    reasoning="向量相似度检索",
                    metadata=vr
                )
                results.append(result)
            
            return results
        except Exception as e:
            self.logger.error(f"向量检索失败: {e}")
            return []
    
    def _hybrid_retrieve(
        self,
        query: str,
        document_id: Optional[str] = None
    ) -> List[RetrievalResult]:
        """混合检索 - 结合推理式和向量检索"""
        # 并行执行两种检索
        reasoning_results = self._reasoning_retrieve(query, document_id)
        vector_results = self._vector_retrieve(query, document_id)
        
        # 合并结果
        all_results = {}
        
        for result in reasoning_results:
            key = f"reasoning_{result.node_id}"
            all_results[key] = result
        
        for result in vector_results:
            key = f"vector_{result.node_id}"
            if key not in all_results:
                all_results[key] = result
            else:
                # 合并分数
                existing = all_results[key]
                existing.relevance_score = max(
                    existing.relevance_score,
                    result.relevance_score
                )
                existing.reasoning += f"\n向量检索补充: {result.relevance_score}"
        
        # 按相关性排序
        results = list(all_results.values())
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results[:self.max_results]
    
    def _fallback_to_vector(
        self,
        query: str,
        document_id: Optional[str] = None
    ) -> List[RetrievalResult]:
        """回退到向量检索"""
        if self.vector_retriever:
            return self._vector_retrieve(query, document_id)
        
        # 没有向量检索，返回空结果
        return []
    
    def get_retrieval_history(self) -> List[List[RetrievalResult]]:
        """获取检索历史"""
        return self.retrieval_history
    
    def clear_history(self):
        """清空检索历史"""
        self.retrieval_history = []


# 单例模式
_reasoning_agent_instance: Optional['ReasoningRetrievalAgent'] = None


def get_reasoning_retrieval_agent(
    tree_index_builder: Optional[TreeIndexBuilder] = None
) -> ReasoningRetrievalAgent:
    """获取ReasoningRetrievalAgent单例"""
    global _reasoning_agent_instance
    if _reasoning_agent_instance is None:
        _reasoning_agent_instance = ReasoningRetrievalAgent(
            tree_index_builder=tree_index_builder
        )
    return _reasoning_agent_instance
