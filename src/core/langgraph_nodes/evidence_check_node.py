#!/usr/bin/env python3
"""
自反思检索节点 - EvidenceCheckNode
根据RAG_OPTIMIZATION_PLAN.md P0阶段实现，在检索后评估证据质量
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional

from src.core.langgraph_unified_workflow import ResearchSystemState
from src.core.reasoning.evidence_processor import EvidenceProcessor
from src.core.reasoning.models import Evidence

logger = logging.getLogger(__name__)


class EvidenceCheckNode:
    """证据检查节点 - 实现自反思检索机制"""
    
    def __init__(self, evidence_processor: Optional[EvidenceProcessor] = None, config: Optional[Dict[str, Any]] = None):
        """
        初始化证据检查节点
        
        Args:
            evidence_processor: 证据处理器实例
            config: 配置参数
        """
        self.evidence_processor = evidence_processor
        self.config = config or {}
        
        # 自反思检索配置
        self.min_evidence_count = self.config.get('min_evidence_count', 3)  # 最少需要3个证据
        self.min_relevance_score = self.config.get('min_relevance_score', 0.6)  # 最低相关性分数
        self.max_irrelevant_ratio = self.config.get('max_irrelevant_ratio', 0.3)  # 最多30%不相关证据
        self.enable_reflection = self.config.get('enable_reflection', True)
        self.reflection_max_tokens = self.config.get('reflection_max_tokens', 200)
        
        # 质量评估权重
        self.relevance_weight = self.config.get('relevance_weight', 0.4)
        self.completeness_weight = self.config.get('completeness_weight', 0.3)
        self.diversity_weight = self.config.get('diversity_weight', 0.2)
        self.freshness_weight = self.config.get('freshness_weight', 0.1)
        
        self.logger = logging.getLogger(f"{__name__}.EvidenceCheckNode")
        self.logger.info("EvidenceCheckNode初始化完成")
    
    async def execute(self, state: ResearchSystemState) -> ResearchSystemState:
        """
        执行证据检查节点
        
        Args:
            state: 当前研究系统状态
            
        Returns:
            ResearchSystemState: 更新后的状态
        """
        start_time = time.time()
        
        try:
            self.logger.info("🔍 [EvidenceCheck] 开始评估证据质量")
            
            # 获取当前步骤的证据
            current_step_index = state.get('current_step_index', 0)
            reasoning_steps = state.get('reasoning_steps', [])
            
            if current_step_index >= len(reasoning_steps):
                self.logger.warning("⚠️ [EvidenceCheck] 无效的步骤索引")
                return state
            
            current_step = reasoning_steps[current_step_index]
            evidence_list = current_step.get('evidence', [])
            
            if not evidence_list:
                self.logger.warning("⚠️ [EvidenceCheck] 当前步骤没有证据")
                return await self._mark_step_completed(state, "no_evidence")
            
            # 1. 证据质量评估
            quality_score = await self._assess_evidence_quality(evidence_list, current_step)
            
            # 2. 决定是否需要重新检索
            needs_retrieval = await self._should_retrieve_again(evidence_list, quality_score)
            
            if needs_retrieval and self.enable_reflection:
                # 3. 自反思 - 生成改进的查询
                improved_query = await self._generate_reflection_query(
                    current_step.get('sub_query', ''),
                    evidence_list,
                    quality_score
                )
                
                if improved_query:
                    self.logger.info(f"🔄 [EvidenceCheck] 触发重新检索: {improved_query[:50]}...")
                    
                    # 标记需要重新检索
                    state['needs_retrieval'] = True
                    state['improved_query'] = improved_query
                    state['reflection_reason'] = self._generate_reflection_reason(
                        evidence_list, quality_score
                    )
                    
                    execution_time = time.time() - start_time
                    state['node_execution_times']['evidence_check'] = execution_time
                    state['node_times']['evidence_check'] = execution_time
                    
                    self.logger.info(f"✅ [EvidenceCheck] 证据检查完成，需要重新检索 (耗时: {execution_time:.2f}s)")
                else:
                    self.logger.warning("⚠️ [EvidenceCheck] 无法生成改进查询")
                    return await self._mark_step_completed(state, "reflection_failed")
            else:
                # 证据质量合格，标记步骤完成
                return await self._mark_step_completed(state, "evidence_passed")
                
        except Exception as e:
            self.logger.error(f"❌ [EvidenceCheck] 证据检查失败: {e}")
            error_msg = f"证据检查失败: {str(e)}"
            
            if 'errors' not in state:
                state['errors'] = []
            state['errors'].append({
                'node': 'evidence_check',
                'error': error_msg,
                'timestamp': time.time(),
                'severity': 'error'
            })
            
            return state
    
    async def _assess_evidence_quality(self, evidence_list: List[Any], step: Dict[str, Any]) -> Dict[str, float]:
        """
        评估证据质量
        
        Args:
            evidence_list: 证据列表
            step: 当前推理步骤
            
        Returns:
            Dict[str, float]: 质量评估分数
        """
        try:
            if not evidence_list:
                return {"overall": 0.0, "details": {}}
            
            quality_metrics = {}
            
            # 1. 相关性评估
            relevance_score = await self._assess_relevance(evidence_list, step)
            quality_metrics['relevance'] = relevance_score
            
            # 2. 完整性评估
            completeness_score = await self._assess_completeness(evidence_list, step)
            quality_metrics['completeness'] = completeness_score
            
            # 3. 多样性评估
            diversity_score = await self._assess_diversity(evidence_list)
            quality_metrics['diversity'] = diversity_score
            
            # 4. 新鲜性评估
            freshness_score = await self._assess_freshness(evidence_list)
            quality_metrics['freshness'] = freshness_score
            
            # 计算加权总分
            overall_score = (
                relevance_score * self.relevance_weight +
                completeness_score * self.completeness_weight +
                diversity_score * self.diversity_weight +
                freshness_score * self.freshness_weight
            )
            
            quality_metrics['overall'] = overall_score
            quality_metrics['evidence_count'] = len(evidence_list)
            
            self.logger.debug(f"🔍 [EvidenceCheck] 质量评估: {overall_score:.3f} (R:{relevance_score:.2f}, C:{completeness_score:.2f}, D:{diversity_score:.2f}, F:{freshness_score:.2f})")
            
            return quality_metrics
            
        except Exception as e:
            self.logger.error(f"❌ [EvidenceCheck] 质量评估失败: {e}")
            return {"overall": 0.0, "details": {"error": str(e)}}
    
    async def _assess_relevance(self, evidence_list: List[Any], step: Dict[str, Any]) -> float:
        """评估证据相关性"""
        try:
            if not evidence_list:
                return 0.0
            
            query = step.get('sub_query', '')
            query_terms = set(query.lower().split())
            
            relevant_count = 0
            total_relevance = 0.0
            
            for evidence in evidence_list:
                if hasattr(evidence, 'content'):
                    content = str(evidence.content).lower()
                    # 计算与查询的重叠度
                    overlap = len(set(content.split()) & query_terms)
                    relevance_score = overlap / max(len(query_terms), 1)
                    
                    relevant_count += 1 if relevance_score > 0.1 else 0
                    total_relevance += relevance_score
            
            # 如果没有相关证据，相关性为0
            if relevant_count == 0:
                return 0.0
                
            # 平均相关性，考虑查询复杂度
            avg_relevance = total_relevance / len(evidence_list)
            complexity_penalty = min(len(query_terms) / 10.0, 0.3)  # 查询越复杂，惩罚越小
            
            return max(0.0, avg_relevance - complexity_penalty)
            
        except Exception as e:
            self.logger.error(f"❌ [EvidenceCheck] 相关性评估失败: {e}")
            return 0.0
    
    async def _assess_completeness(self, evidence_list: List[Any], step: Dict[str, Any]) -> float:
        """评估证据完整性"""
        try:
            if not evidence_list:
                return 0.0
            
            # 检查证据是否有足够的结构化信息
            structured_count = 0
            total_score = 0.0
            
            for evidence in evidence_list:
                if hasattr(evidence, 'metadata'):
                    metadata = evidence.metadata if isinstance(evidence.metadata, dict) else {}
                    
                    # 检查关键元数据字段
                    has_source = bool(metadata.get('source'))
                    has_timestamp = bool(metadata.get('timestamp'))
                    has_confidence = bool(metadata.get('confidence'))
                    has_title = bool(metadata.get('title'))
                    
                    structure_score = sum([
                        1.0 if has_source else 0.0,
                        1.0 if has_timestamp else 0.0,
                        1.0 if has_confidence else 0.0,
                        1.0 if has_title else 0.0
                    ])
                    
                    structured_count += 1 if structure_score >= 2.0 else 0
                    total_score += structure_score
            
            # 完整性分数 = 结构化证据比例
            completeness = total_score / max(len(evidence_list), 1)
            
            self.logger.debug(f"🔍 [EvidenceCheck] 完整性评估: {completeness:.3f} ({structured_count}/{len(evidence_list)} 结构化)")
            
            return completeness
            
        except Exception as e:
            self.logger.error(f"❌ [EvidenceCheck] 完整性评估失败: {e}")
            return 0.0
    
    async def _assess_diversity(self, evidence_list: List[Any]) -> float:
        """评估证据多样性"""
        try:
            if len(evidence_list) <= 1:
                return 1.0  # 单个证据，多样性满分
            
            sources = set()
            content_hashes = set()
            
            for evidence in evidence_list:
                if hasattr(evidence, 'metadata'):
                    metadata = evidence.metadata if isinstance(evidence.metadata, dict) else {}
                    
                    # 来源多样性
                    source = metadata.get('source', 'unknown')
                    sources.add(source)
                    
                    # 内容多样性（使用简单的内容哈希）
                    if hasattr(evidence, 'content'):
                        content = str(evidence.content)
                        content_hash = hash(content[:200])  # 使用前200字符计算哈希
                        content_hashes.add(content_hash)
            
            # 计算多样性分数
            source_diversity = len(sources) / len(evidence_list)
            content_diversity = len(content_hashes) / len(evidence_list)
            
            diversity_score = (source_diversity + content_diversity) / 2.0
            
            self.logger.debug(f"🔍 [EvidenceCheck] 多样性评估: {diversity_score:.3f} (来源:{len(sources)}, 内容:{len(content_hashes)})")
            
            return diversity_score
            
        except Exception as e:
            self.logger.error(f"❌ [EvidenceCheck] 多样性评估失败: {e}")
            return 0.0
    
    async def _assess_freshness(self, evidence_list: List[Any]) -> float:
        """评估证据新鲜性"""
        try:
            if not evidence_list:
                return 0.0
            
            import time
            current_time = time.time()
            freshness_scores = []
            
            for evidence in evidence_list:
                if hasattr(evidence, 'metadata'):
                    metadata = evidence.metadata if isinstance(evidence.metadata, dict) else {}
                    
                    timestamp = metadata.get('timestamp', current_time)
                    if timestamp:
                        # 计算时间衰减（越小越新）
                        age_hours = (current_time - timestamp) / 3600.0
                        freshness = max(0.0, 1.0 - age_hours / (24.0 * 30.0))  # 30天内的认为是新鲜的
                        freshness_scores.append(freshness)
            
            if not freshness_scores:
                return 0.5  # 没有时间信息，给中等分数
            
            avg_freshness = sum(freshness_scores) / len(freshness_scores)
            
            self.logger.debug(f"🔍 [EvidenceCheck] 新鲜性评估: {avg_freshness:.3f}")
            
            return avg_freshness
            
        except Exception as e:
            self.logger.error(f"❌ [EvidenceCheck] 新鲜性评估失败: {e}")
            return 0.0
    
    async def _should_retrieve_again(self, evidence_list: List[Any], quality_score: Dict[str, float]) -> bool:
        """判断是否需要重新检索"""
        try:
            evidence_count = len(evidence_list)
            overall_quality = quality_score.get('overall', 0.0)
            
            # 检查基本条件
            if evidence_count < self.min_evidence_count:
                self.logger.debug(f"🔍 [EvidenceCheck] 证据数量不足: {evidence_count} < {self.min_evidence_count}")
                return True
            
            if overall_quality < self.min_relevance_score:
                self.logger.debug(f"🔍 [EvidenceCheck] 质量分数过低: {overall_quality:.3f} < {self.min_relevance_score}")
                return True
            
            # 检查不相关证据比例
            if hasattr(quality_score, 'relevance'):
                # 简单启发式：如果平均相关性低于阈值，可能需要更多证据
                return False
                
            return False
            
        except Exception as e:
            self.logger.error(f"❌ [EvidenceCheck] 重新检索判断失败: {e}")
            return True  # 安全起见，重新检索
    
    async def _generate_reflection_query(self, original_query: str, evidence_list: List[Any], quality_score: Dict[str, float]) -> Optional[str]:
        """生成自反思查询"""
        try:
            if not self.evidence_processor or not hasattr(self.evidence_processor, 'llm_integration'):
                self.logger.warning("⚠️ [EvidenceCheck] 无法生成反思查询：缺少LLM集成")
                return None
            
            # 分析证据质量不足的原因
            reflection_reason = self._generate_reflection_reason(evidence_list, quality_score)
            
            # 构建反思提示词
            reflection_prompt = f"""
基于以下查询和证据，生成一个改进的检索查询：

原始查询: {original_query}

证据质量评估:
{self._format_quality_assessment(quality_score)}

证据总结:
{self._format_evidence_summary(evidence_list)}

请分析证据的不足之处，并生成一个能够获得更好结果的改进查询。
改进查询应该：
1. 更具体和明确
2. 包含相关关键词的同义词
3. 扩展查询范围以涵盖更多相关信息
4. 使用更精确的技术术语

改进查询（直接回答）:
"""
            
            # 生成改进查询
            improved_query = await self.evidence_processor.llm_integration.generate(
                prompt=reflection_prompt,
                temperature=0.3,  # 较低温度，保持查询的严肃性
                max_tokens=self.reflection_max_tokens
            )
            
            if improved_query and len(improved_query.strip()) > 5:
                self.logger.info(f"💡 [EvidenceCheck] 生成改进查询: {improved_query.strip()[:100]}...")
                return improved_query.strip()
            else:
                self.logger.warning("⚠️ [EvidenceCheck] 反思查询生成失败或无效")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ [EvidenceCheck] 反思查询生成失败: {e}")
            return None
    
    def _generate_reflection_reason(self, evidence_list: List[Any], quality_score: Dict[str, float]) -> str:
        """生成反思原因"""
        try:
            reasons = []
            
            # 分析质量分数低的原因
            overall = quality_score.get('overall', 0.0)
            evidence_count = quality_score.get('evidence_count', 0)
            
            if evidence_count < self.min_evidence_count:
                reasons.append(f"证据数量不足({evidence_count} < {self.min_evidence_count})")
            
            if overall < self.min_relevance_score:
                reasons.append("整体相关性过低")
            
            if quality_score.get('relevance', 0.0) < 0.3:
                reasons.append("证据与查询匹配度低")
            
            if quality_score.get('completeness', 0.0) < 0.3:
                reasons.append("证据结构化程度不足")
            
            if quality_score.get('diversity', 0.0) < 0.3:
                reasons.append("证据来源单一")
            
            return "; ".join(reasons) if reasons else "证据质量需要改进"
            
        except Exception as e:
            return f"反思原因分析失败: {str(e)}"
    
    def _format_quality_assessment(self, quality_score: Dict[str, float]) -> str:
        """格式化质量评估结果"""
        try:
            return f"""
整体质量: {quality_score.get('overall', 0.0):.3f}
- 相关性: {quality_score.get('relevance', 0.0):.3f}
- 完整性: {quality_score.get('completeness', 0.0):.3f}
- 多样性: {quality_score.get('diversity', 0.0):.3f}
- 新鲜性: {quality_score.get('freshness', 0.0):.3f}
- 证据数量: {quality_score.get('evidence_count', 0)}
"""
        except Exception:
            return f"质量评估格式化失败: {quality_score}"
    
    def _format_evidence_summary(self, evidence_list: List[Any]) -> str:
        """格式化证据总结"""
        try:
            if not evidence_list:
                return "无证据"
            
            summary_lines = []
            for i, evidence in enumerate(evidence_list[:5]):  # 只显示前5个证据
                if hasattr(evidence, 'content'):
                    content_preview = str(evidence.content)[:100]
                    source = getattr(evidence, 'source', 'unknown')
                    summary_lines.append(f"{i+1}. [{source}] {content_preview}...")
            
            if len(evidence_list) > 5:
                summary_lines.append(f"... (还有{len(evidence_list)-5}个证据)")
            
            return "\n".join(summary_lines)
            
        except Exception:
            return "证据总结格式化失败"
    
    async def _mark_step_completed(self, state: ResearchSystemState, reason: str) -> ResearchSystemState:
        """标记步骤完成"""
        try:
            # 更新步骤答案
            reasoning_steps = state.get('reasoning_steps', [])
            current_step_index = state.get('current_step_index', 0)
            
            if current_step_index < len(reasoning_steps):
                current_step = reasoning_steps[current_step_index]
                
                # 根据完成原因生成答案
                if reason == "evidence_passed":
                    answer = f"✅ 证据检查通过，质量评估得分: {reason}. 继续下一步推理。"
                elif reason == "no_evidence":
                    answer = "⚠️ 当前步骤没有收集到证据，跳过质量检查，继续下一步。"
                elif reason == "reflection_failed":
                    answer = "❌ 自反思查询生成失败，使用原查询继续。"
                else:
                    answer = f"📝 步骤完成，原因: {reason}."
                
                current_step['answer'] = answer
                current_step['completed'] = True
                current_step['completion_reason'] = reason
            
            # 更新状态
            state['reasoning_steps'] = reasoning_steps
            
            self.logger.info(f"✅ [EvidenceCheck] 步骤标记完成: {reason}")
            
            return state
            
        except Exception as e:
            self.logger.error(f"❌ [EvidenceCheck] 步骤标记失败: {e}")
            return state


# 便捷函数
def create_evidence_check_node(evidence_processor: Optional[EvidenceProcessor] = None, config: Optional[Dict[str, Any]] = None) -> EvidenceCheckNode:
    """
    创建证据检查节点实例
    
    Args:
        evidence_processor: 证据处理器实例
        config: 配置参数
        
    Returns:
        EvidenceCheckNode: 证据检查节点实例
    """
    return EvidenceCheckNode(evidence_processor, config)


# 向后兼容性别名
SelfReflectiveRetrievalNode = EvidenceCheckNode