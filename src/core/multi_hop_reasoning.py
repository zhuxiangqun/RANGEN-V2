#!/usr/bin/env python3
"""
多跳推理核心模块 - Multi-Hop Reasoning Core Module
实现复杂的多跳推理、约束满足和知识整合功能
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ReasoningStatus(Enum):
    """推理状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ConstraintType(Enum):
    """约束类型"""
    TEMPORAL = "temporal"  # 时间约束
    LOGICAL = "logical"    # 逻辑约束
    SEMANTIC = "semantic"  # 语义约束
    NUMERICAL = "numerical"  # 数值约束


@dataclass
class ReasoningHop:
    """推理跳步"""
    hop_id: str
    question: str
    reasoning_type: str
    input_facts: List[str]
    output_facts: List[str]
    confidence: float
    intermediate_results: Dict[str, Any]
    timestamp: float


@dataclass
class Constraint:
    """约束条件"""
    constraint_id: str
    constraint_type: ConstraintType
    description: str
    rules: List[Dict[str, Any]]
    priority: float


@dataclass
class KnowledgeItem:
    """知识项"""
    item_id: str
    content: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any]


class MultiHopReasoningEngine:
    """多跳推理引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.reasoning_history: List[ReasoningHop] = []
        self.knowledge_graph: Dict[str, List[str]] = {}
        self.constraints: List[Constraint] = []
        
        # 🚀 优化：初始化提示词工程和LLM集成（用于智能分类）
        self.prompt_engineering = None
        self.llm_integration = None
        self.fast_llm_integration = None
        self._initialize_smart_components()
    
    def _initialize_smart_components(self):
        """初始化智能组件（提示词工程和LLM集成）"""
        try:
            # 初始化提示词工程
            from src.utils.prompt_engine import get_prompt_engine
            self.prompt_engineering = get_prompt_engine()
            self._register_reasoning_type_templates(self.prompt_engineering)
            self.logger.debug("✅ 提示词工程初始化完成")
        except Exception as e:
            self.logger.warning(f"⚠️ 提示词工程初始化失败: {e}")
        
        try:
            # 初始化LLM集成
            import os
            from dotenv import load_dotenv
            from src.core.llm_integration import LLMIntegration
            
            # 🚀 确保从.env文件加载配置
            load_dotenv()
            
            # 快速模型（用于分类）
            fast_llm_config = {
                'llm_provider': 'deepseek',
                'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
                'model': 'deepseek-chat',
                'base_url': os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
            }
            self.fast_llm_integration = LLMIntegration(fast_llm_config)
            self.logger.debug("✅ LLM集成初始化完成")
        except Exception as e:
            self.logger.warning(f"⚠️ LLM集成初始化失败: {e}")
    
    def _register_reasoning_type_templates(self, prompt_engine):
        """注册推理类型分类提示词模板（🚀 修复：完全使用统一提示词工程模块，所有模板从配置文件加载）"""
        try:
            # 🚀 修复：完全依赖PromptEngine的统一配置文件加载机制
            # PromptEngine在初始化时会自动从templates/templates.json加载所有模板
            # 这里只需要验证必需模板是否存在，不再硬编码任何模板内容
            
            required_templates = [
                "multi_hop_reasoning_type_classification"
            ]
            
            missing_templates = [name for name in required_templates if not prompt_engine.get_template(name)]
            
            if not missing_templates:
                self.logger.info(f"✅ 所有多跳推理模板已从配置文件加载: {len(required_templates)} 个")
                return
            
            # 🚀 修复：如果模板缺失，只记录警告，不硬编码注册
            # 所有模板应该从templates/templates.json配置文件加载
            # 如果模板缺失，说明配置文件需要更新，而不是在代码中硬编码
            self.logger.warning(
                f"⚠️ 发现 {len(missing_templates)} 个缺失的多跳推理模板: {missing_templates}\n"
                f"   请确保 templates/templates.json 配置文件中包含这些模板。\n"
                f"   缺少的模板将无法使用，可能影响系统功能。"
            )
            
        except Exception as e:
            self.logger.warning(f"检查多跳推理提示词模板失败: {e}")
    
    def execute_multi_hop_reasoning(
        self,
        query: str,
        knowledge_base: List[KnowledgeItem],
        max_hops: int = 5
    ) -> Dict[str, Any]:
        """
        执行多跳推理
        
        Args:
            query: 查询问题
            knowledge_base: 知识库
            max_hops: 最大跳数
            
        Returns:
            推理结果
        """
        try:
            self.logger.info(f"开始多跳推理: {query}, 最大跳数: {max_hops}")
            
            # 1. 分解查询为子问题
            sub_questions = self._decompose_query(query)
            self.logger.info(f"分解为 {len(sub_questions)} 个子问题")
            
            # 2. 构建推理路径
            reasoning_path = self._build_reasoning_path(sub_questions, knowledge_base)
            self.logger.info(f"构建了 {len(reasoning_path)} 步推理路径")
            
            # 3. 执行多跳推理
            hops = []
            current_facts = []
            
            for hop_idx, sub_question in enumerate(sub_questions[:max_hops]):
                hop_result = self._execute_reasoning_hop(
                    hop_id=f"hop_{hop_idx}",
                    question=sub_question,
                    current_facts=current_facts,
                    knowledge_base=knowledge_base,
                    hop_index=hop_idx
                )
                
                hops.append(hop_result)
                current_facts.extend(hop_result.output_facts)
                
                self.logger.info(f"完成第 {hop_idx + 1} 跳推理")
            
            # 4. 整合推理结果
            final_answer = self._integrate_reasoning_results(hops, query)
            
            # 5. 计算总体置信度
            overall_confidence = self._calculate_overall_confidence(hops)
            
            return {
                "success": True,
                "query": query,
                "sub_questions": sub_questions,
                "reasoning_hops": hops,
                "final_answer": final_answer,
                "confidence": overall_confidence,
                "total_hops": len(hops),
                "reasoning_path": reasoning_path,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"多跳推理失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "confidence": 0.0
            }
    
    def _decompose_query(self, query: str) -> List[str]:
        """分解查询为子问题"""
        try:
            sub_questions = []
            
            # 检测查询类型并分解
            if "和" in query or "以及" in query or "and" in query.lower():
                # 并列查询
                parts = query.replace("和", "###").replace("以及", "###").replace(" and ", "###").split("###")
                sub_questions = [part.strip() for part in parts if part.strip()]
            
            elif "如果" in query or "假设" in query or "if" in query.lower():
                # 条件查询
                sub_questions.append(f"验证条件: {query}")
                sub_questions.append(f"推导结果: {query}")
            
            elif "比较" in query or "差异" in query or "compare" in query.lower():
                # 比较查询
                sub_questions.append(f"分析对象A: {query}")
                sub_questions.append(f"分析对象B: {query}")
                sub_questions.append(f"对比分析: {query}")
            
            elif "为什么" in query or "原因" in query or "why" in query.lower():
                # 因果查询
                sub_questions.append(f"识别现象: {query}")
                sub_questions.append(f"分析原因: {query}")
                sub_questions.append(f"验证因果关系: {query}")
            
            else:
                # 默认分解策略
                sub_questions.append(f"理解问题: {query}")
                sub_questions.append(f"检索相关信息: {query}")
                sub_questions.append(f"推理得出答案: {query}")
            
            return sub_questions
            
        except Exception as e:
            self.logger.error(f"查询分解失败: {e}")
            return [query]  # 失败时返回原查询
    
    def _build_reasoning_path(
        self,
        sub_questions: List[str],
        knowledge_base: List[KnowledgeItem]
    ) -> List[Dict[str, Any]]:
        """构建推理路径"""
        try:
            reasoning_path = []
            
            for idx, sub_question in enumerate(sub_questions):
                # 为每个子问题构建推理步骤
                step = {
                    "step_id": f"step_{idx}",
                    "question": sub_question,
                    "dependencies": [f"step_{i}" for i in range(idx)],  # 依赖前面的所有步骤
                    "required_knowledge": self._identify_required_knowledge(sub_question, knowledge_base),
                    "reasoning_type": self._identify_reasoning_type(sub_question)
                }
                reasoning_path.append(step)
            
            return reasoning_path
            
        except Exception as e:
            self.logger.error(f"构建推理路径失败: {e}")
            return []
    
    def _execute_reasoning_hop(
        self,
        hop_id: str,
        question: str,
        current_facts: List[str],
        knowledge_base: List[KnowledgeItem],
        hop_index: int
    ) -> ReasoningHop:
        """执行单个推理跳步"""
        try:
            # 1. 检索相关知识
            relevant_knowledge = self._retrieve_relevant_knowledge(question, knowledge_base)
            
            # 2. 应用推理规则
            reasoning_type = self._identify_reasoning_type(question)
            
            if reasoning_type == "deductive":
                output_facts = self._apply_deductive_reasoning(question, current_facts, relevant_knowledge)
            elif reasoning_type == "inductive":
                output_facts = self._apply_inductive_reasoning(question, current_facts, relevant_knowledge)
            elif reasoning_type == "abductive":
                output_facts = self._apply_abductive_reasoning(question, current_facts, relevant_knowledge)
            else:
                output_facts = self._apply_default_reasoning(question, current_facts, relevant_knowledge)
            
            # 3. 计算置信度
            confidence = self._calculate_hop_confidence(output_facts, relevant_knowledge)
            
            # 4. 创建推理跳步
            hop = ReasoningHop(
                hop_id=hop_id,
                question=question,
                reasoning_type=reasoning_type,
                input_facts=current_facts.copy(),
                output_facts=output_facts,
                confidence=confidence,
                intermediate_results={
                    "relevant_knowledge": [k.content for k in relevant_knowledge[:3]],
                    "reasoning_type": reasoning_type
                },
                timestamp=time.time()
            )
            
            # 5. 记录推理历史
            self.reasoning_history.append(hop)
            
            return hop
            
        except Exception as e:
            self.logger.error(f"推理跳步执行失败: {e}")
            return ReasoningHop(
                hop_id=hop_id,
                question=question,
                reasoning_type="error",
                input_facts=current_facts,
                output_facts=[],
                confidence=0.0,
                intermediate_results={"error": str(e)},
                timestamp=time.time()
            )
    
    def _integrate_reasoning_results(self, hops: List[ReasoningHop], query: str) -> str:
        """整合推理结果"""
        try:
            # 收集所有输出事实
            all_facts = []
            for hop in hops:
                all_facts.extend(hop.output_facts)
            
            # 去重
            unique_facts = list(set(all_facts))
            
            # 生成最终答案
            if unique_facts:
                answer = f"基于 {len(hops)} 步推理，得出以下结论：\n"
                for i, fact in enumerate(unique_facts[:5], 1):  # 限制为前5个事实
                    answer += f"{i}. {fact}\n"
            else:
                answer = "无法基于当前知识得出明确结论"
            
            return answer
            
        except Exception as e:
            self.logger.error(f"整合推理结果失败: {e}")
            return "推理结果整合失败"
    
    def _calculate_overall_confidence(self, hops: List[ReasoningHop]) -> float:
        """计算总体置信度"""
        try:
            if not hops:
                return 0.0
            
            # 使用最小置信度作为总体置信度（链式推理的弱点）
            confidences = [hop.confidence for hop in hops]
            min_confidence = min(confidences)
            avg_confidence = sum(confidences) / len(confidences)
            
            # 加权平均：70% 最小值 + 30% 平均值
            overall_confidence = min_confidence * 0.7 + avg_confidence * 0.3
            
            return overall_confidence
            
        except Exception as e:
            self.logger.error(f"计算总体置信度失败: {e}")
            return 0.0
    
    def _identify_required_knowledge(
        self,
        sub_question: str,
        knowledge_base: List[KnowledgeItem]
    ) -> List[str]:
        """识别所需知识"""
        try:
            required_knowledge = []
            
            # 简单的关键词匹配
            question_words = set(sub_question.lower().split())
            
            for knowledge in knowledge_base:
                content_words = set(knowledge.content.lower().split())
                overlap = len(question_words & content_words)
                
                if overlap > 0:
                    required_knowledge.append(knowledge.item_id)
            
            return required_knowledge
            
        except Exception as e:
            self.logger.error(f"识别所需知识失败: {e}")
            return []
    
    def _identify_reasoning_type(self, question: str) -> str:
        """识别推理类型（🚀 优化：使用统一分类服务）
        
        策略：
        1. 使用统一分类服务进行智能分类（3-5秒）
        2. 如果LLM不可用或失败，使用改进的规则匹配作为fallback
        """
        try:
            # 🚀 优化：使用统一分类服务
            from src.utils.unified_classification_service import get_unified_classification_service
            
            classification_service = get_unified_classification_service(
                prompt_engineering=self.prompt_engineering,
                llm_integration=self.llm_integration,
                fast_llm_integration=self.fast_llm_integration
            )
            
            valid_types = ['deductive', 'inductive', 'abductive', 'default']
            
            return classification_service.classify(
                query=question,
                classification_type="reasoning_type",
                valid_types=valid_types,
                template_name="multi_hop_reasoning_type_classification",
                default_type="default",
                rules_fallback=self._identify_reasoning_type_with_rules
            )
                
        except Exception as e:
            self.logger.error(f"识别推理类型失败: {e}")
            return "default"
    
    def _identify_reasoning_type_with_rules(self, question: str) -> str:
        """使用规则匹配识别推理类型（Fallback方法 - 🚀 智能方案：使用统一分类服务的语义fallback）"""
        try:
            # 注意：这个方法现在只作为最后的fallback
            # 实际的智能分类由统一分类服务通过LLM和语义相似度完成
            # 这里只返回默认值，实际的fallback由统一分类服务处理
            return "default"
                
        except Exception as e:
            self.logger.error(f"规则匹配失败: {e}")
            return "default"
    
    def _retrieve_relevant_knowledge(
        self,
        question: str,
        knowledge_base: List[KnowledgeItem]
    ) -> List[KnowledgeItem]:
        """检索相关知识"""
        try:
            # 简单的相关性计算
            question_words = set(question.lower().split())
            
            knowledge_with_scores = []
            for knowledge in knowledge_base:
                content_words = set(knowledge.content.lower().split())
                overlap = len(question_words & content_words)
                
                if overlap > 0:
                    relevance_score = overlap / len(question_words)
                    knowledge_with_scores.append((knowledge, relevance_score))
            
            # 按相关性排序
            knowledge_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 返回前5个最相关的知识
            return [k for k, _ in knowledge_with_scores[:5]]
            
        except Exception as e:
            self.logger.error(f"检索相关知识失败: {e}")
            return []
    
    def _apply_deductive_reasoning(
        self,
        question: str,
        current_facts: List[str],
        relevant_knowledge: List[KnowledgeItem]
    ) -> List[str]:
        """应用演绎推理"""
        try:
            output_facts = []
            
            # 基于当前事实和知识进行演绎
            for knowledge in relevant_knowledge:
                # 简单的演绎规则：如果知识中包含"那么"，提取结论
                if "那么" in knowledge.content or "then" in knowledge.content.lower():
                    parts = knowledge.content.replace("那么", "###").replace(" then ", "###").split("###")
                    if len(parts) >= 2:
                        conclusion = parts[1].strip()
                        output_facts.append(conclusion)
            
            return output_facts
            
        except Exception as e:
            self.logger.error(f"演绎推理失败: {e}")
            return []
    
    def _apply_inductive_reasoning(
        self,
        question: str,
        current_facts: List[str],
        relevant_knowledge: List[KnowledgeItem]
    ) -> List[str]:
        """应用归纳推理"""
        try:
            output_facts = []
            
            # 基于知识归纳模式
            if len(relevant_knowledge) >= 3:
                # 提取共同模式
                common_patterns = self._extract_common_patterns([k.content for k in relevant_knowledge])
                output_facts.extend(common_patterns)
            
            return output_facts
            
        except Exception as e:
            self.logger.error(f"归纳推理失败: {e}")
            return []
    
    def _apply_abductive_reasoning(
        self,
        question: str,
        current_facts: List[str],
        relevant_knowledge: List[KnowledgeItem]
    ) -> List[str]:
        """应用溯因推理"""
        try:
            output_facts = []
            
            # 基于观察生成假设
            for knowledge in relevant_knowledge:
                hypothesis = f"可能的原因：{knowledge.content}"
                output_facts.append(hypothesis)
            
            return output_facts
            
        except Exception as e:
            self.logger.error(f"溯因推理失败: {e}")
            return []
    
    def _apply_default_reasoning(
        self,
        question: str,
        current_facts: List[str],
        relevant_knowledge: List[KnowledgeItem]
    ) -> List[str]:
        """应用默认推理"""
        try:
            output_facts = []
            
            # 直接使用相关知识作为事实
            for knowledge in relevant_knowledge:
                output_facts.append(knowledge.content)
            
            return output_facts
            
        except Exception as e:
            self.logger.error(f"默认推理失败: {e}")
            return []
    
    def _calculate_hop_confidence(
        self,
        output_facts: List[str],
        relevant_knowledge: List[KnowledgeItem]
    ) -> float:
        """计算跳步置信度"""
        try:
            if not output_facts:
                return 0.0
            
            # 基于输出事实数量和相关知识数量计算置信度
            fact_score = min(len(output_facts) / 3.0, 1.0)
            knowledge_score = min(len(relevant_knowledge) / 5.0, 1.0)
            
            confidence = (fact_score * 0.6 + knowledge_score * 0.4)
            
            return min(confidence, 1.0)
            
        except Exception as e:
            self.logger.error(f"计算跳步置信度失败: {e}")
            return 0.0
    
    def _extract_common_patterns(self, texts: List[str]) -> List[str]:
        """提取共同模式"""
        try:
            patterns = []
            
            # 提取共同词汇
            all_words = [set(text.lower().split()) for text in texts]
            common_words = all_words[0]
            for words in all_words[1:]:
                common_words &= words
            
            if common_words:
                patterns.append(f"共同特征：{', '.join(list(common_words)[:5])}")
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"提取共同模式失败: {e}")
            return []


class ConstraintSolver:
    """约束求解器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.constraints: List[Constraint] = []
    
    def add_constraint(self, constraint: Constraint):
        """添加约束"""
        self.constraints.append(constraint)
        self.logger.info(f"添加约束: {constraint.constraint_id}")
    
    def solve_constraints(
        self,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        求解约束
        
        Args:
            candidates: 候选解
            
        Returns:
            满足约束的解
        """
        try:
            self.logger.info(f"开始约束求解，候选解数量: {len(candidates)}")
            
            # 按优先级排序约束
            sorted_constraints = sorted(self.constraints, key=lambda c: c.priority, reverse=True)
            
            # 逐个应用约束过滤候选解
            valid_candidates = candidates.copy()
            
            for constraint in sorted_constraints:
                valid_candidates = self._apply_constraint(constraint, valid_candidates)
                self.logger.info(f"应用约束 {constraint.constraint_id} 后，剩余候选解: {len(valid_candidates)}")
            
            return valid_candidates
            
        except Exception as e:
            self.logger.error(f"约束求解失败: {e}")
            return candidates  # 失败时返回原始候选解
    
    def _apply_constraint(
        self,
        constraint: Constraint,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """应用单个约束"""
        try:
            valid_candidates = []
            
            for candidate in candidates:
                if self._check_constraint(constraint, candidate):
                    valid_candidates.append(candidate)
            
            return valid_candidates
            
        except Exception as e:
            self.logger.error(f"应用约束失败: {e}")
            return candidates
    
    def _check_constraint(
        self,
        constraint: Constraint,
        candidate: Dict[str, Any]
    ) -> bool:
        """检查候选解是否满足约束"""
        try:
            if constraint.constraint_type == ConstraintType.TEMPORAL:
                return self._check_temporal_constraint(constraint, candidate)
            elif constraint.constraint_type == ConstraintType.LOGICAL:
                return self._check_logical_constraint(constraint, candidate)
            elif constraint.constraint_type == ConstraintType.SEMANTIC:
                return self._check_semantic_constraint(constraint, candidate)
            elif constraint.constraint_type == ConstraintType.NUMERICAL:
                return self._check_numerical_constraint(constraint, candidate)
            else:
                return True  # 未知类型默认通过
                
        except Exception as e:
            self.logger.error(f"检查约束失败: {e}")
            return True  # 失败时默认通过
    
    def _check_temporal_constraint(
        self,
        constraint: Constraint,
        candidate: Dict[str, Any]
    ) -> bool:
        """检查时间约束"""
        try:
            # 简单的时间约束检查
            for rule in constraint.rules:
                if rule.get('type') == 'before':
                    field_a = rule.get('field_a')
                    field_b = rule.get('field_b')
                    if field_a and field_b and isinstance(field_a, str) and isinstance(field_b, str):
                        time_a = candidate.get(field_a, 0)
                        time_b = candidate.get(field_b, 0)
                        if time_a >= time_b:
                            return False
            
            return True
            
        except Exception:
            return True
    
    def _check_logical_constraint(
        self,
        constraint: Constraint,
        candidate: Dict[str, Any]
    ) -> bool:
        """检查逻辑约束"""
        try:
            # 简单的逻辑约束检查
            for rule in constraint.rules:
                if rule.get('type') == 'and':
                    conditions = rule.get('conditions', [])
                    if not all(candidate.get(cond) for cond in conditions):
                        return False
                elif rule.get('type') == 'or':
                    conditions = rule.get('conditions', [])
                    if not any(candidate.get(cond) for cond in conditions):
                        return False
            
            return True
            
        except Exception:
            return True
    
    def _check_semantic_constraint(
        self,
        constraint: Constraint,
        candidate: Dict[str, Any]
    ) -> bool:
        """检查语义约束"""
        try:
            # 简单的语义约束检查
            for rule in constraint.rules:
                if rule.get('type') == 'must_contain':
                    field = rule.get('field')
                    keywords = rule.get('keywords', [])
                    if field and isinstance(field, str):
                        content = str(candidate.get(field, ''))
                        if not any(keyword in content.lower() for keyword in keywords):
                            return False
            
            return True
            
        except Exception:
            return True
    
    def _check_numerical_constraint(
        self,
        constraint: Constraint,
        candidate: Dict[str, Any]
    ) -> bool:
        """检查数值约束"""
        try:
            # 简单的数值约束检查
            for rule in constraint.rules:
                if rule.get('type') == 'greater_than':
                    field = rule.get('field')
                    threshold = rule.get('threshold', 0)
                    if field and isinstance(field, str):
                        value = candidate.get(field, 0)
                        if value <= threshold:
                            return False
                elif rule.get('type') == 'less_than':
                    field = rule.get('field')
                    threshold = rule.get('threshold', 0)
                    if field and isinstance(field, str):
                        value = candidate.get(field, 0)
                        if value >= threshold:
                            return False
            
            return True
            
        except Exception:
            return True


class KnowledgeIntegrator:
    """知识整合器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.integrated_knowledge: Dict[str, Any] = {}
    
    def integrate_knowledge(
        self,
        knowledge_sources: List[List[KnowledgeItem]],
        integration_strategy: str = "merge"
    ) -> Dict[str, Any]:
        """
        整合多个知识源
        
        Args:
            knowledge_sources: 知识源列表
            integration_strategy: 整合策略 (merge/vote/hierarchical)
            
        Returns:
            整合后的知识
        """
        try:
            self.logger.info(f"开始知识整合，知识源数量: {len(knowledge_sources)}, 策略: {integration_strategy}")
            
            if integration_strategy == "merge":
                result = self._merge_integration(knowledge_sources)
            elif integration_strategy == "vote":
                result = self._vote_integration(knowledge_sources)
            elif integration_strategy == "hierarchical":
                result = self._hierarchical_integration(knowledge_sources)
            else:
                result = self._merge_integration(knowledge_sources)  # 默认策略
            
            self.integrated_knowledge = result
            return result
            
        except Exception as e:
            self.logger.error(f"知识整合失败: {e}")
            return {"error": str(e), "integrated_items": []}
    
    def _merge_integration(
        self,
        knowledge_sources: List[List[KnowledgeItem]]
    ) -> Dict[str, Any]:
        """合并整合策略"""
        try:
            all_items = []
            
            # 收集所有知识项
            for source in knowledge_sources:
                all_items.extend(source)
            
            # 去重
            unique_items = self._deduplicate_knowledge(all_items)
            
            # 排序
            sorted_items = sorted(unique_items, key=lambda x: x.relevance_score, reverse=True)
            
            return {
                "strategy": "merge",
                "total_sources": len(knowledge_sources),
                "total_items": len(all_items),
                "unique_items": len(unique_items),
                "integrated_items": sorted_items,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"合并整合失败: {e}")
            return {"error": str(e), "integrated_items": []}
    
    def _vote_integration(
        self,
        knowledge_sources: List[List[KnowledgeItem]]
    ) -> Dict[str, Any]:
        """投票整合策略"""
        try:
            # 统计每个知识项出现的次数
            item_votes: Dict[str, int] = {}
            item_map: Dict[str, KnowledgeItem] = {}
            
            for source in knowledge_sources:
                for item in source:
                    key = item.content  # 使用内容作为键
                    item_votes[key] = item_votes.get(key, 0) + 1
                    item_map[key] = item
            
            # 按投票数排序
            sorted_items = sorted(
                item_map.values(),
                key=lambda x: item_votes.get(x.content, 0),
                reverse=True
            )
            
            return {
                "strategy": "vote",
                "total_sources": len(knowledge_sources),
                "voted_items": len(sorted_items),
                "integrated_items": sorted_items,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"投票整合失败: {e}")
            return {"error": str(e), "integrated_items": []}
    
    def _hierarchical_integration(
        self,
        knowledge_sources: List[List[KnowledgeItem]]
    ) -> Dict[str, Any]:
        """层次整合策略"""
        try:
            # 按来源优先级整合
            integrated_items = []
            
            for priority, source in enumerate(knowledge_sources):
                for item in source:
                    # 调整相关性分数（优先级越高，分数越高）
                    adjusted_score = item.relevance_score * (1.0 - priority * 0.1)
                    adjusted_item = KnowledgeItem(
                        item_id=item.item_id,
                        content=item.content,
                        source=item.source,
                        relevance_score=adjusted_score,
                        metadata={**item.metadata, "priority": priority}
                    )
                    integrated_items.append(adjusted_item)
            
            # 排序
            sorted_items = sorted(integrated_items, key=lambda x: x.relevance_score, reverse=True)
            
            return {
                "strategy": "hierarchical",
                "total_sources": len(knowledge_sources),
                "integrated_items": sorted_items,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"层次整合失败: {e}")
            return {"error": str(e), "integrated_items": []}
    
    def _deduplicate_knowledge(
        self,
        items: List[KnowledgeItem]
    ) -> List[KnowledgeItem]:
        """知识去重"""
        try:
            seen_contents = set()
            unique_items = []
            
            for item in items:
                if item.content not in seen_contents:
                    seen_contents.add(item.content)
                    unique_items.append(item)
            
            return unique_items
            
        except Exception as e:
            self.logger.error(f"知识去重失败: {e}")
            return items

