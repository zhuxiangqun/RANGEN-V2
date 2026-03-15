#!/usr/bin/env python3
"""
上下文工程智能体 - 管理长期记忆和上下文
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from .expert_agent import ExpertAgent
from .base_agent import AgentResult

logger = logging.getLogger(__name__)


class ContextEngineeringAgent(ExpertAgent):
    """上下文工程智能体 - 管理长期记忆和上下文
    
    核心能力：
    1. 上下文管理：短期/长期上下文、压缩和优化
    2. 记忆管理：智能存储和检索、重要性评估、遗忘和更新
    3. 上下文关联：智能检索、关联分析、上下文推荐
    """
    
    def __init__(self):
        super().__init__(
            agent_id="context_engineering_expert",
            domain_expertise="上下文工程和长期记忆管理",
            capability_level=0.95,
            collaboration_style="supportive"
        )
        
        # 上下文工程中心
        self.context_center = None
        
        # 记忆管理数据
        self.memory_importance_scores: Dict[str, float] = {}
        self.memory_access_patterns: Dict[str, List[float]] = {}
        self.context_associations: Dict[str, List[str]] = {}
        
        # 学习配置
        self.learning_config = {
            "enable_importance_learning": True,
            "enable_association_learning": True,
            "min_access_count_for_importance": 3,
            "association_threshold": 0.7,
        }
        
        logger.info("✅ ContextEngineeringAgent 初始化完成")
    
    def _get_service(self):
        """获取上下文工程中心服务"""
        if self.context_center is None:
            from src.utils.unified_context_engineering_center import UnifiedContextEngineeringCenter
            self.context_center = UnifiedContextEngineeringCenter()
        return self.context_center
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行上下文工程任务
        
        Args:
            context: 任务上下文，包含：
                - task_type: 任务类型（add_context, get_context, compress_context, manage_memory, associate_context）
                - session_id: 会话ID
                - content: 上下文内容（用于add_context）
                - category: 上下文类别
                - scope: 上下文范围（short_term/long_term）
                - source: 上下文来源
                - metadata: 元数据
                - max_fragments: 最大片段数（用于get_context）
                - fragment_id: 片段ID（用于管理）
        
        Returns:
            AgentResult: 执行结果
        """
        import time
        start_time = time.time()
        
        if not self.context_center:
            self.context_center = self._get_service()
        
        task_type = context.get("task_type", "get_context")
        
        try:
            if task_type == "add_context":
                return await self._add_context(context, start_time)
            elif task_type == "get_context":
                return await self._get_context(context, start_time)
            elif task_type == "compress_context":
                return await self._compress_context(context, start_time)
            elif task_type == "manage_memory":
                return await self._manage_memory(context, start_time)
            elif task_type == "associate_context":
                return await self._associate_context(context, start_time)
            elif task_type == "evaluate_importance":
                return await self._evaluate_importance(context, start_time)
            else:
                return AgentResult(
                    success=False,
                    data=None,
                    error=f"未知的任务类型: {task_type}",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
        except Exception as e:
            logger.error(f"上下文工程任务执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _add_context(
        self, 
        context: Dict[str, Any], 
        start_time: float
    ) -> AgentResult:
        """添加上下文"""
        try:
            session_id = context.get("session_id", "default")
            content = context.get("content", "")
            category_str = context.get("category", "informational")
            scope_str = context.get("scope", "short_term")
            source_str = context.get("source", "user_input")
            metadata = context.get("metadata", {})
            
            # 转换字符串为枚举类型
            from src.utils.unified_context_engineering_center import (
                ContextCategory, ContextScope, ContextSource
            )
            
            category_map = {
                "guiding": ContextCategory.GUIDING,
                "informational": ContextCategory.INFORMATIONAL,
                "actionable": ContextCategory.ACTIONABLE
            }
            scope_map = {
                "short_term": ContextScope.SHORT_TERM,
                "long_term": ContextScope.LONG_TERM,
                "implicit": ContextScope.IMPLICIT
            }
            source_map = {
                "user_input": ContextSource.USER_INPUT,
                "system_log": ContextSource.SYSTEM_LOG,
                "knowledge_base": ContextSource.KNOWLEDGE_BASE,
                "tool_definition": ContextSource.TOOL_DEFINITION,
                "tool_call": ContextSource.TOOL_CALL,
                "tool_result": ContextSource.TOOL_RESULT,
                "environment": ContextSource.ENVIRONMENT
            }
            
            category = category_map.get(category_str, ContextCategory.INFORMATIONAL)
            scope = scope_map.get(scope_str, ContextScope.SHORT_TERM)
            source = source_map.get(source_str, ContextSource.USER_INPUT)
            
            # 评估上下文重要性（如果启用学习）
            importance_score = 0.5  # 默认重要性
            if self.learning_config.get("enable_importance_learning"):
                importance_score = await self._evaluate_context_importance(
                    content, category, scope, source, metadata
                )
                metadata["importance_score"] = importance_score
            
            # 调用上下文中心添加上下文
            import asyncio
            loop = asyncio.get_event_loop()
            
            fragment_id = await loop.run_in_executor(
                None,
                lambda: self.context_center.add_context_fragment(
                    session_id=session_id,
                    content=content,
                    category=category,
                    scope=scope,
                    source=source,
                    metadata=metadata
                )
            )
            
            # 记录访问模式（用于学习）
            self._record_access(fragment_id, time.time())
            
            return AgentResult(
                success=True,
                data={
                    "fragment_id": fragment_id,
                    "session_id": session_id,
                    "importance_score": importance_score
                },
                confidence=0.9,
                processing_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"添加上下文失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _get_context(
        self, 
        context: Dict[str, Any], 
        start_time: float
    ) -> AgentResult:
        """获取上下文"""
        try:
            session_id = context.get("session_id", "default")
            max_fragments = context.get("max_fragments", 20)
            query = context.get("query", "")  # 可选：用于语义检索
            
            import asyncio
            loop = asyncio.get_event_loop()
            
            # 获取增强上下文
            enhanced_context = await loop.run_in_executor(
                None,
                lambda: self.context_center.get_enhanced_context(
                    session_id=session_id,
                    max_fragments=max_fragments
                )
            )
            
            # 如果提供了查询，进行智能排序和过滤
            if query and self.learning_config.get("enable_association_learning"):
                enhanced_context = await self._intelligent_context_ranking(
                    enhanced_context, query
                )
            
            # 提取fragments
            fragments = enhanced_context.get("fragments", [])
            
            # 记录访问模式（用于学习）
            for fragment in fragments:
                fragment_id = fragment.get("id") or fragment.get("fragment_id")
                if fragment_id:
                    self._record_access(fragment_id, time.time())
            
            return AgentResult(
                success=True,
                data={
                    "fragments": fragments,
                    "count": len(fragments),
                    "session_id": session_id,
                    "enhanced_context": enhanced_context
                },
                confidence=0.9,
                processing_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"获取上下文失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _compress_context(
        self, 
        context: Dict[str, Any], 
        start_time: float
    ) -> AgentResult:
        """压缩上下文"""
        try:
            session_id = context.get("session_id", "default")
            target_size = context.get("target_size", 0.7)  # 压缩到70%
            
            import asyncio
            loop = asyncio.get_event_loop()
            
            # 获取当前上下文
            current_context = await loop.run_in_executor(
                None,
                lambda: self.context_center.get_enhanced_context(
                    session_id=session_id,
                    max_fragments=1000  # 获取所有片段
                )
            )
            
            fragments = current_context.get("fragments", [])
            
            # 根据重要性排序
            sorted_fragments = await self._sort_by_importance(fragments)
            
            # 选择最重要的片段
            target_count = int(len(sorted_fragments) * target_size)
            compressed_fragments = sorted_fragments[:target_count]
            
            return AgentResult(
                success=True,
                data={
                    "original_count": len(fragments),
                    "compressed_count": len(compressed_fragments),
                    "compression_ratio": target_size,
                    "fragments": compressed_fragments
                },
                confidence=0.85,
                processing_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"压缩上下文失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _manage_memory(
        self, 
        context: Dict[str, Any], 
        start_time: float
    ) -> AgentResult:
        """管理记忆"""
        try:
            session_id = context.get("session_id", "default")
            action = context.get("action", "evaluate")  # evaluate, forget, update
            
            if action == "evaluate":
                # 评估记忆重要性
                importance_scores = await self._evaluate_all_memories(session_id)
                
                return AgentResult(
                    success=True,
                    data={
                        "session_id": session_id,
                        "importance_scores": importance_scores,
                        "recommendations": self._generate_memory_recommendations(importance_scores)
                    },
                    confidence=0.9,
                    processing_time=time.time() - start_time
                )
            elif action == "forget":
                # 遗忘低重要性记忆
                threshold = context.get("threshold", 0.3)
                forgotten_count = await self._forget_low_importance_memories(session_id, threshold)
                
                return AgentResult(
                    success=True,
                    data={
                        "session_id": session_id,
                        "forgotten_count": forgotten_count,
                        "threshold": threshold
                    },
                    confidence=0.8,
                    processing_time=time.time() - start_time
                )
            else:
                return AgentResult(
                    success=False,
                    data=None,
                    error=f"未知的记忆管理操作: {action}",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
        except Exception as e:
            logger.error(f"管理记忆失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _associate_context(
        self, 
        context: Dict[str, Any], 
        start_time: float
    ) -> AgentResult:
        """关联上下文"""
        try:
            fragment_id = context.get("fragment_id")
            session_id = context.get("session_id", "default")
            
            if not fragment_id:
                return AgentResult(
                    success=False,
                    data=None,
                    error="缺少fragment_id",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
            
            # 查找关联的上下文
            associations = await self._find_context_associations(fragment_id, session_id)
            
            return AgentResult(
                success=True,
                data={
                    "fragment_id": fragment_id,
                    "associations": associations,
                    "count": len(associations)
                },
                confidence=0.85,
                processing_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"关联上下文失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _evaluate_importance(
        self, 
        context: Dict[str, Any], 
        start_time: float
    ) -> AgentResult:
        """评估上下文重要性"""
        try:
            fragment_id = context.get("fragment_id")
            content = context.get("content", "")
            category = context.get("category", "informational")
            scope = context.get("scope", "short_term")
            
            importance_score = await self._evaluate_context_importance(
                content, category, scope, None, {}
            )
            
            return AgentResult(
                success=True,
                data={
                    "fragment_id": fragment_id,
                    "importance_score": importance_score
                },
                confidence=0.9,
                processing_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"评估重要性失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    def _record_access(self, fragment_id: str, timestamp: float) -> None:
        """记录访问模式"""
        if fragment_id not in self.memory_access_patterns:
            self.memory_access_patterns[fragment_id] = []
        
        self.memory_access_patterns[fragment_id].append(timestamp)
        
        # 限制历史记录数量（保留最近100次访问）
        if len(self.memory_access_patterns[fragment_id]) > 100:
            self.memory_access_patterns[fragment_id] = self.memory_access_patterns[fragment_id][-100:]
    
    async def _evaluate_context_importance(
        self,
        content: str,
        category: Any,
        scope: Any,
        source: Any,
        metadata: Dict[str, Any]
    ) -> float:
        """评估上下文重要性"""
        # 基础重要性评分
        importance = 0.5
        
        # 根据类别调整
        if category and hasattr(category, 'value'):
            if category.value == "guiding":
                importance += 0.3
            elif category.value == "actionable":
                importance += 0.2
        
        # 根据范围调整
        if scope and hasattr(scope, 'value'):
            if scope.value == "long_term":
                importance += 0.2
        
        # 根据元数据调整
        if metadata.get("is_key_clue"):
            importance += 0.2
        if metadata.get("priority", 0) > 0.7:
            importance += 0.1
        
        # 如果启用了学习，使用访问模式调整
        if self.learning_config.get("enable_importance_learning"):
            # 这里可以根据历史访问模式调整重要性
            # 例如：频繁访问的上下文重要性更高
            pass
        
        # 使用LLM评估（如果可用）
        if self.llm_client and len(content) < 500:  # 只对短内容使用LLM
            try:
                llm_score = await self._llm_evaluate_importance(content)
                if llm_score is not None:
                    importance = (importance + llm_score) / 2  # 平均
            except Exception as e:
                logger.debug(f"LLM评估重要性失败: {e}")
        
        return min(max(importance, 0.0), 1.0)  # 限制在0-1之间
    
    async def _llm_evaluate_importance(self, content: str) -> Optional[float]:
        """使用LLM评估重要性"""
        if not self.llm_client:
            return None
        
        try:
            prompt = f"""评估以下上下文内容的重要性（0-1之间，1表示非常重要）。

上下文内容: {content[:300]}

请只返回一个0-1之间的数字，表示重要性评分。

重要性评分："""
            
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm_client._call_llm(prompt) if hasattr(self.llm_client, '_call_llm') else ""
            )
            
            # 解析数字
            try:
                score = float(response.strip())
                return min(max(score, 0.0), 1.0)
            except ValueError:
                return None
        except Exception as e:
            logger.debug(f"LLM评估重要性失败: {e}")
            return None
    
    async def _sort_by_importance(self, fragments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """根据重要性排序片段"""
        # 计算每个片段的重要性
        fragment_scores = []
        for fragment in fragments:
            fragment_id = fragment.get("id") or fragment.get("fragment_id", "")
            importance = fragment.get("metadata", {}).get("importance_score", 0.5)
            
            # 根据访问模式调整
            if fragment_id in self.memory_access_patterns:
                access_count = len(self.memory_access_patterns[fragment_id])
                if access_count > 0:
                    importance += min(access_count * 0.05, 0.3)  # 最多增加0.3
            
            fragment_scores.append((fragment, importance))
        
        # 按重要性排序
        fragment_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [fragment for fragment, _ in fragment_scores]
    
    async def _intelligent_context_ranking(
        self, 
        enhanced_context: Dict[str, Any], 
        query: str
    ) -> Dict[str, Any]:
        """智能上下文排序（基于查询相关性）"""
        fragments = enhanced_context.get("fragments", [])
        
        # 简单的关键词匹配排序（可以改进为语义相似度）
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        fragment_scores = []
        for fragment in fragments:
            content = fragment.get("content", "").lower()
            content_words = set(content.split())
            
            # 计算词重叠度
            overlap = len(query_words & content_words)
            relevance = overlap / len(query_words) if query_words else 0.0
            
            fragment_scores.append((fragment, relevance))
        
        # 按相关性排序
        fragment_scores.sort(key=lambda x: x[1], reverse=True)
        
        enhanced_context["fragments"] = [fragment for fragment, _ in fragment_scores]
        
        return enhanced_context
    
    async def _evaluate_all_memories(self, session_id: str) -> Dict[str, float]:
        """评估所有记忆的重要性"""
        import asyncio
        loop = asyncio.get_event_loop()
        
        enhanced_context = await loop.run_in_executor(
            None,
            lambda: self.context_center.get_enhanced_context(
                session_id=session_id,
                max_fragments=1000
            )
        )
        
        fragments = enhanced_context.get("fragments", [])
        importance_scores = {}
        
        for fragment in fragments:
            fragment_id = fragment.get("id") or fragment.get("fragment_id", "")
            if fragment_id:
                importance = fragment.get("metadata", {}).get("importance_score", 0.5)
                importance_scores[fragment_id] = importance
        
        return importance_scores
    
    def _generate_memory_recommendations(
        self, 
        importance_scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """生成记忆管理建议"""
        recommendations = []
        
        low_importance = [fid for fid, score in importance_scores.items() if score < 0.3]
        if low_importance:
            recommendations.append({
                "action": "forget",
                "fragment_ids": low_importance,
                "reason": "重要性低于0.3，建议遗忘"
            })
        
        high_importance = [fid for fid, score in importance_scores.items() if score > 0.8]
        if high_importance:
            recommendations.append({
                "action": "preserve",
                "fragment_ids": high_importance,
                "reason": "重要性高于0.8，建议长期保存"
            })
        
        return recommendations
    
    async def _forget_low_importance_memories(
        self, 
        session_id: str, 
        threshold: float
    ) -> int:
        """遗忘低重要性记忆"""
        # 这里可以实现实际的遗忘逻辑
        # 目前只是标记，不实际删除
        importance_scores = await self._evaluate_all_memories(session_id)
        forgotten = [fid for fid, score in importance_scores.items() if score < threshold]
        
        return len(forgotten)
    
    async def _find_context_associations(
        self, 
        fragment_id: str, 
        session_id: str
    ) -> List[Dict[str, Any]]:
        """查找上下文关联"""
        # 如果已有关联记录，直接返回
        if fragment_id in self.context_associations:
            associated_ids = self.context_associations[fragment_id]
            
            # 获取关联的片段
            import asyncio
            loop = asyncio.get_event_loop()
            enhanced_context = await loop.run_in_executor(
                None,
                lambda: self.context_center.get_enhanced_context(
                    session_id=session_id,
                    max_fragments=1000
                )
            )
            
            fragments = enhanced_context.get("fragments", [])
            associated_fragments = [
                f for f in fragments 
                if (f.get("id") or f.get("fragment_id", "")) in associated_ids
            ]
            
            return associated_fragments
        
        # 如果没有关联记录，使用语义相似度查找
        # 这里可以实现更复杂的关联逻辑
        return []

