"""
高级推理引擎V2
实现多种推理类型的深度协同和智能推理
"""

import logging
import time
import math
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import json


class ReasoningType(Enum):
    """推理类型枚举"""
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    CAUSAL = "causal"
    ANALOGICAL = "analogical"
    SPATIAL = "spatial"
    TEMPORAL = "temporal"
    UNCERTAINTY = "uncertainty"
    MULTI_STEP = "multi_step"
    COUNTERFACTUAL = "counterfactual"
    PROBABILISTIC = "probabilistic"
    META_REASONING = "meta_reasoning"


@dataclass
class ReasoningContext:
    """推理上下文"""
    premises: List[Any]
    constraints: Dict[str, Any]
    background_knowledge: Dict[str, Any]
    reasoning_goals: List[str]
    confidence_threshold: float = 0.5
    max_steps: int = 100
    reasoning_depth: int = 5


@dataclass
class ReasoningResult:
    """推理结果"""
    success: bool
    conclusion: Any
    confidence: float
    reasoning_type: ReasoningType
    steps: List[Dict[str, Any]]
    processing_time: float
    complexity_score: float
    reasoning_chain: List[Dict[str, Any]]
    meta_reasoning: Dict[str, Any]
    error: Optional[str] = None


class ReasoningStrategy(ABC):
    """推理策略基类"""
    
    @abstractmethod
    def execute(self, context: ReasoningContext) -> ReasoningResult:
        """执行推理策略"""
        pass


class MetaReasoningStrategy(ReasoningStrategy):
    """元推理策略"""
    
    def __init__(self):
        self.name = "meta_reasoning"
        self.logger = logging.getLogger(f"ReasoningStrategy.{self.name}")
        self.reasoning_history = []
        self.meta_knowledge = {}
    
    def execute(self, context: ReasoningContext) -> ReasoningResult:
        """执行元推理"""
        start_time = time.time()
        
        try:
            # 1. 分析推理任务
            task_analysis = self._analyze_reasoning_task(context)
            
            # 2. 选择推理策略
            selected_strategy = self._select_reasoning_strategy(task_analysis, context)
            
            # 3. 执行推理过程
            reasoning_steps = self._execute_reasoning_process(context, selected_strategy)
            
            # 4. 生成推理链
            reasoning_chain = self._generate_reasoning_chain(reasoning_steps)
            
            # 5. 元推理分析
            meta_reasoning = self._perform_meta_reasoning(reasoning_steps, context)
            
            # 6. 生成结论
            conclusion = self._generate_conclusion(reasoning_chain, meta_reasoning)
            
            # 7. 计算置信度
            confidence = self._calculate_confidence(reasoning_chain, meta_reasoning, context)
            
            processing_time = time.time() - start_time
            
            return ReasoningResult(
                success=True,
                conclusion=conclusion,
                confidence=confidence,
                reasoning_type=ReasoningType.META_REASONING,
                steps=reasoning_steps,
                processing_time=processing_time,
                complexity_score=self._calculate_complexity_score(reasoning_steps),
                reasoning_chain=reasoning_chain,
                meta_reasoning=meta_reasoning
            )
            
        except Exception as e:
            self.logger.error(f"元推理执行失败: {e}")
            return ReasoningResult(
                success=False,
                conclusion=None,
                confidence=0.0,
                reasoning_type=ReasoningType.META_REASONING,
                steps=[],
                processing_time=time.time() - start_time,
                complexity_score=0.0,
                reasoning_chain=[],
                meta_reasoning={},
                error=str(e)
            )
    
    def _analyze_reasoning_task(self, context: ReasoningContext) -> Dict[str, Any]:
        """分析推理任务"""
        analysis = {
            'task_complexity': self._assess_task_complexity(context),
            'reasoning_difficulty': self._assess_reasoning_difficulty(context),
            'knowledge_requirements': self._assess_knowledge_requirements(context),
            'constraint_impact': self._assess_constraint_impact(context),
            'goal_priority': self._assess_goal_priority(context),
            'reasoning_opportunities': self._identify_reasoning_opportunities(context)
        }
        
        return analysis
    
    def _assess_task_complexity(self, context: ReasoningContext) -> float:
        """评估任务复杂度"""
        complexity = 0.5  # 基础复杂度
        
        # 基于前提数量调整
        premise_count = len(context.premises)
        complexity += min(0.3, premise_count / 20.0)
        
        # 基于约束数量调整
        constraint_count = len(context.constraints)
        complexity += min(0.2, constraint_count / 10.0)
        
        # 基于目标数量调整
        goal_count = len(context.reasoning_goals)
        complexity += min(0.2, goal_count / 10.0)
        
        # 基于背景知识复杂度调整
        knowledge_complexity = self._assess_knowledge_complexity(context.background_knowledge)
        complexity += knowledge_complexity * 0.3
        
        return min(1.0, complexity)
    
    def _assess_knowledge_complexity(self, knowledge: Dict[str, Any]) -> float:
        """评估知识复杂度"""
        if not knowledge:
            return 0.0
        
        # 基于知识项数量
        knowledge_count = len(knowledge)
        complexity = min(0.5, knowledge_count / 50.0)
        
        # 基于知识深度
        for key, value in knowledge.items():
            if isinstance(value, dict):
                complexity += 0.1
            elif isinstance(value, list):
                complexity += 0.05
        
        return min(1.0, complexity)
    
    def _assess_reasoning_difficulty(self, context: ReasoningContext) -> float:
        """评估推理难度"""
        difficulty = 0.5  # 基础难度
        
        # 基于推理深度调整
        depth = context.reasoning_depth
        difficulty += min(0.3, depth / 20.0)
        
        # 基于最大步数调整
        max_steps = context.max_steps
        difficulty += min(0.2, max_steps / 200.0)
        
        # 基于置信度阈值调整
        threshold = context.confidence_threshold
        if threshold > 0.8:
            difficulty += 0.2
        elif threshold > 0.6:
            difficulty += 0.1
        
        return min(1.0, difficulty)
    
    def _assess_knowledge_requirements(self, context: ReasoningContext) -> Dict[str, Any]:
        """评估知识需求"""
        requirements = {
            'domain_knowledge': 0.0,
            'logical_knowledge': 0.0,
            'procedural_knowledge': 0.0,
            'factual_knowledge': 0.0
        }
        
        # 基于前提分析知识需求
        for premise in context.premises:
            if isinstance(premise, str):
                if any(word in premise.lower() for word in ['如果', '那么', '因为', '所以', 'if', 'then', 'because', 'therefore']):
                    requirements['logical_knowledge'] += 0.1
                elif any(word in premise.lower() for word in ['如何', '怎样', 'how', 'what', 'when', 'where']):
                    requirements['procedural_knowledge'] += 0.1
                elif any(word in premise.lower() for word in ['是', '有', '存在', 'is', 'has', 'exists']):
                    requirements['factual_knowledge'] += 0.1
                else:
                    requirements['domain_knowledge'] += 0.1
        
        # 标准化到0-1范围
        for key in requirements:
            requirements[key] = min(1.0, requirements[key])
        
        return requirements
    
    def _assess_constraint_impact(self, context: ReasoningContext) -> float:
        """评估约束影响"""
        if not context.constraints:
            return 0.0
        
        impact = 0.0
        
        for key, value in context.constraints.items():
            if isinstance(value, (int, float)):
                # 数值约束
                impact += 0.2
            elif isinstance(value, str):
                # 字符串约束
                impact += 0.1
            elif isinstance(value, list):
                # 列表约束
                impact += 0.15
            elif isinstance(value, dict):
                # 字典约束
                impact += 0.25
        
        return min(1.0, impact)
    
    def _assess_goal_priority(self, context: ReasoningContext) -> float:
        """评估目标优先级"""
        if not context.reasoning_goals:
            return 0.5
        
        priority = 0.0
        
        for goal in context.reasoning_goals:
            if isinstance(goal, str):
                goal_lower = goal.lower()
                if any(word in goal_lower for word in ['重要', '关键', '紧急', 'important', 'critical', 'urgent']):
                    priority += 0.3
                elif any(word in goal_lower for word in ['需要', '必须', 'should', 'must', 'need']):
                    priority += 0.2
                else:
                    priority += 0.1
        
        return min(1.0, priority / len(context.reasoning_goals))
    
    def _identify_reasoning_opportunities(self, context: ReasoningContext) -> List[str]:
        """识别推理机会"""
        opportunities = []
        
        # 基于前提识别机会
        for premise in context.premises:
            if isinstance(premise, str):
                if any(word in premise.lower() for word in ['因果', 'cause', 'effect']):
                    opportunities.append('causal_reasoning')
                elif any(word in premise.lower() for word in ['类比', 'similar', 'like']):
                    opportunities.append('analogical_reasoning')
                elif any(word in premise.lower() for word in ['时间', 'time', 'before', 'after']):
                    opportunities.append('temporal_reasoning')
                elif any(word in premise.lower() for word in ['空间', 'space', 'location', 'where']):
                    opportunities.append('spatial_reasoning')
                elif any(word in premise.lower() for word in ['可能', '概率', 'probability', 'chance']):
                    opportunities.append('probabilistic_reasoning')
        
        # 基于目标识别机会
        for goal in context.reasoning_goals:
            if isinstance(goal, str):
                goal_lower = goal.lower()
                if any(word in goal_lower for word in ['证明', 'prove', 'demonstrate']):
                    opportunities.append('deductive_reasoning')
                elif any(word in goal_lower for word in ['归纳', 'generalize', 'induce']):
                    opportunities.append('inductive_reasoning')
                elif any(word in goal_lower for word in ['解释', 'explain', 'why']):
                    opportunities.append('abductive_reasoning')
        
        return list(set(opportunities))
    
    def _select_reasoning_strategy(self, analysis: Dict[str, Any], context: ReasoningContext) -> Dict[str, Any]:
        """选择推理策略"""
        strategy = {
            'primary_type': 'general',
            'secondary_types': [],
            'reasoning_depth': context.reasoning_depth,
            'confidence_threshold': context.confidence_threshold,
            'max_steps': context.max_steps
        }
        
        # 基于任务复杂度选择策略
        task_complexity = analysis['task_complexity']
        if task_complexity > 0.8:
            strategy['primary_type'] = 'multi_step'
            strategy['secondary_types'] = ['meta_reasoning', 'probabilistic']
        elif task_complexity > 0.6:
            strategy['primary_type'] = 'causal'
            strategy['secondary_types'] = ['analogical', 'temporal']
        elif task_complexity > 0.4:
            strategy['primary_type'] = 'deductive'
            strategy['secondary_types'] = ['inductive']
        else:
            strategy['primary_type'] = 'simple'
            strategy['secondary_types'] = []
        
        # 基于推理机会调整策略
        opportunities = analysis['reasoning_opportunities']
        if opportunities:
            strategy['secondary_types'].extend(opportunities[:3])  # 最多3个次要类型
        
        return strategy
    
    def _execute_reasoning_process(self, context: ReasoningContext, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行推理过程"""
        steps = []
        
        # 步骤1：初始化推理
        steps.append({
            'step': 1,
            'action': 'initialize_reasoning',
            'description': '初始化推理过程',
            'reasoning_type': strategy['primary_type'],
            'confidence': 0.9
        })
        
        # 步骤2：分析前提
        steps.append({
            'step': 2,
            'action': 'analyze_premises',
            'description': '分析推理前提',
            'premise_count': len(context.premises),
            'confidence': 0.8
        })
        
        # 步骤3：应用约束
        steps.append({
            'step': 3,
            'action': 'apply_constraints',
            'description': '应用推理约束',
            'constraint_count': len(context.constraints),
            'confidence': 0.7
        })
        
        # 步骤4：执行主要推理
        primary_reasoning = self._execute_primary_reasoning(context, strategy)
        steps.append(primary_reasoning)
        
        # 步骤5：执行次要推理
        for i, secondary_type in enumerate(strategy['secondary_types']):
            secondary_reasoning = self._execute_secondary_reasoning(context, secondary_type, i + 5)
            steps.append(secondary_reasoning)
        
        # 步骤6：整合推理结果
        steps.append({
            'step': len(steps) + 1,
            'action': 'integrate_reasoning',
            'description': '整合推理结果',
            'confidence': 0.8
        })
        
        return steps
    
    def _execute_primary_reasoning(self, context: ReasoningContext, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """执行主要推理"""
        primary_type = strategy['primary_type']
        
        if primary_type == 'multi_step':
            return self._execute_multi_step_reasoning(context)
        elif primary_type == 'causal':
            return self._execute_causal_reasoning(context)
        elif primary_type == 'deductive':
            return self._execute_deductive_reasoning(context)
        else:
            return self._execute_simple_reasoning(context)
    
    def _execute_secondary_reasoning(self, context: ReasoningContext, reasoning_type: str, step_number: int) -> Dict[str, Any]:
        """执行次要推理"""
        if reasoning_type == 'meta_reasoning':
            return self._execute_meta_reasoning_step(context, step_number)
        elif reasoning_type == 'probabilistic':
            return self._execute_probabilistic_reasoning(context, step_number)
        elif reasoning_type == 'analogical':
            return self._execute_analogical_reasoning(context, step_number)
        elif reasoning_type == 'temporal':
            return self._execute_temporal_reasoning(context, step_number)
        elif reasoning_type == 'spatial':
            return self._execute_spatial_reasoning(context, step_number)
        else:
            return self._execute_general_reasoning(context, step_number)
    
    def _execute_multi_step_reasoning(self, context: ReasoningContext) -> Dict[str, Any]:
        """执行多步推理"""
        return {
            'step': 4,
            'action': 'multi_step_reasoning',
            'description': '执行多步推理',
            'reasoning_type': 'multi_step',
            'steps_count': context.reasoning_depth,
            'confidence': 0.8
        }
    
    def _execute_causal_reasoning(self, context: ReasoningContext) -> Dict[str, Any]:
        """执行因果推理"""
        return {
            'step': 4,
            'action': 'causal_reasoning',
            'description': '执行因果推理',
            'reasoning_type': 'causal',
            'causal_relations': self._identify_causal_relations(context.premises),
            'confidence': 0.75
        }
    
    def _execute_deductive_reasoning(self, context: ReasoningContext) -> Dict[str, Any]:
        """执行演绎推理"""
        return {
            'step': 4,
            'action': 'deductive_reasoning',
            'description': '执行演绎推理',
            'reasoning_type': 'deductive',
            'logical_rules': self._identify_logical_rules(context.premises),
            'confidence': 0.85
        }
    
    def _execute_simple_reasoning(self, context: ReasoningContext) -> Dict[str, Any]:
        """执行简单推理"""
        return {
            'step': 4,
            'action': 'simple_reasoning',
            'description': '执行简单推理',
            'reasoning_type': 'simple',
            'confidence': 0.7
        }
    
    def _execute_meta_reasoning_step(self, context: ReasoningContext, step_number: int) -> Dict[str, Any]:
        """执行元推理步骤"""
        return {
            'step': step_number,
            'action': 'meta_reasoning',
            'description': '执行元推理分析',
            'reasoning_type': 'meta_reasoning',
            'meta_analysis': '分析推理过程本身',
            'confidence': 0.8
        }
    
    def _execute_probabilistic_reasoning(self, context: ReasoningContext, step_number: int) -> Dict[str, Any]:
        """执行概率推理"""
        return {
            'step': step_number,
            'action': 'probabilistic_reasoning',
            'description': '执行概率推理',
            'reasoning_type': 'probabilistic',
            'probability_analysis': '计算事件概率',
            'confidence': 0.75
        }
    
    def _execute_analogical_reasoning(self, context: ReasoningContext, step_number: int) -> Dict[str, Any]:
        """执行类比推理"""
        return {
            'step': step_number,
            'action': 'analogical_reasoning',
            'description': '执行类比推理',
            'reasoning_type': 'analogical',
            'analogies': self._identify_analogies(context.premises),
            'confidence': 0.7
        }
    
    def _execute_temporal_reasoning(self, context: ReasoningContext, step_number: int) -> Dict[str, Any]:
        """执行时间推理"""
        return {
            'step': step_number,
            'action': 'temporal_reasoning',
            'description': '执行时间推理',
            'reasoning_type': 'temporal',
            'temporal_relations': self._identify_temporal_relations(context.premises),
            'confidence': 0.8
        }
    
    def _execute_spatial_reasoning(self, context: ReasoningContext, step_number: int) -> Dict[str, Any]:
        """执行空间推理"""
        return {
            'step': step_number,
            'action': 'spatial_reasoning',
            'description': '执行空间推理',
            'reasoning_type': 'spatial',
            'spatial_relations': self._identify_spatial_relations(context.premises),
            'confidence': 0.75
        }
    
    def _execute_general_reasoning(self, context: ReasoningContext, step_number: int) -> Dict[str, Any]:
        """执行通用推理"""
        return {
            'step': step_number,
            'action': 'general_reasoning',
            'description': '执行通用推理',
            'reasoning_type': 'general',
            'confidence': 0.6
        }
    
    def _identify_causal_relations(self, premises: List[Any]) -> List[str]:
        """识别因果关系"""
        relations = []
        for premise in premises:
            if isinstance(premise, str):
                if any(word in premise.lower() for word in ['导致', '引起', '因为', '所以', 'cause', 'lead to', 'result in']):
                    relations.append(premise)
        return relations
    
    def _identify_logical_rules(self, premises: List[Any]) -> List[str]:
        """识别逻辑规则"""
        rules = []
        for premise in premises:
            if isinstance(premise, str):
                if any(word in premise.lower() for word in ['如果', '那么', 'if', 'then', '当', 'when']):
                    rules.append(premise)
        return rules
    
    def _identify_analogies(self, premises: List[Any]) -> List[str]:
        """识别类比关系"""
        analogies = []
        for premise in premises:
            if isinstance(premise, str):
                if any(word in premise.lower() for word in ['像', '类似', '如同', 'like', 'similar to', 'analogous']):
                    analogies.append(premise)
        return analogies
    
    def _identify_temporal_relations(self, premises: List[Any]) -> List[str]:
        """识别时间关系"""
        relations = []
        for premise in premises:
            if isinstance(premise, str):
                if any(word in premise.lower() for word in ['时间', 'time', '之前', '之后', 'before', 'after', 'during']):
                    relations.append(premise)
        return relations
    
    def _identify_spatial_relations(self, premises: List[Any]) -> List[str]:
        """识别空间关系"""
        relations = []
        for premise in premises:
            if isinstance(premise, str):
                if any(word in premise.lower() for word in ['位置', 'location', '地方', 'place', '空间', 'space', 'where']):
                    relations.append(premise)
        return relations
    
    def _generate_reasoning_chain(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成推理链"""
        chain = []
        
        for step in steps:
            chain.append({
                'step': step['step'],
                'action': step['action'],
                'description': step['description'],
                'reasoning_type': step.get('reasoning_type', 'general'),
                'confidence': step.get('confidence', 0.5),
                'details': step.get('details', {})
            })
        
        return chain
    
    def _perform_meta_reasoning(self, steps: List[Dict[str, Any]], context: ReasoningContext) -> Dict[str, Any]:
        """执行元推理"""
        meta_analysis = {
            'reasoning_quality': self._assess_reasoning_quality(steps),
            'reasoning_efficiency': self._assess_reasoning_efficiency(steps),
            'reasoning_consistency': self._assess_reasoning_consistency(steps),
            'reasoning_completeness': self._assess_reasoning_completeness(steps, context),
            'reasoning_insights': self._generate_reasoning_insights(steps)
        }
        
        return meta_analysis
    
    def _assess_reasoning_quality(self, steps: List[Dict[str, Any]]) -> float:
        """评估推理质量"""
        if not steps:
            return 0.0
        
        # 基于步骤置信度计算质量
        confidences = [step.get('confidence', 0.5) for step in steps]
        avg_confidence = sum(confidences) / len(confidences)
        
        # 基于步骤数量调整
        step_count = len(steps)
        step_bonus = min(0.2, step_count / 20.0)
        
        return min(1.0, avg_confidence + step_bonus)
    
    def _assess_reasoning_efficiency(self, steps: List[Dict[str, Any]]) -> float:
        """评估推理效率"""
        if not steps:
            return 0.0
        
        # 基于步骤类型多样性计算效率
        reasoning_types = set(step.get('reasoning_type', 'general') for step in steps)
        type_diversity = len(reasoning_types) / 10.0  # 假设最多10种类型
        
        # 基于步骤逻辑性计算效率
        logical_steps = sum(1 for step in steps if step.get('reasoning_type') in ['deductive', 'causal', 'logical'])
        logical_ratio = logical_steps / len(steps)
        
        return min(1.0, (type_diversity + logical_ratio) / 2.0)
    
    def _assess_reasoning_consistency(self, steps: List[Dict[str, Any]]) -> float:
        """评估推理一致性"""
        if not steps:
            return 0.0
        
        # 基于步骤间的逻辑一致性
        consistency_score = 0.0
        
        for i in range(len(steps) - 1):
            current_step = steps[i]
            next_step = steps[i + 1]
            
            # 检查步骤间的逻辑关系
            if self._are_steps_logically_consistent(current_step, next_step):
                consistency_score += 1.0
        
        return consistency_score / max(1, len(steps) - 1)
    
    def _are_steps_logically_consistent(self, step1: Dict[str, Any], step2: Dict[str, Any]) -> bool:
        """检查步骤间的逻辑一致性"""
        # 简化的一致性检查
        type1 = step1.get('reasoning_type', 'general')
        type2 = step2.get('reasoning_type', 'general')
        
        # 某些推理类型组合是不一致的
        inconsistent_pairs = [
            ('deductive', 'inductive'),
            ('causal', 'probabilistic'),
            ('analogical', 'logical')
        ]
        
        return (type1, type2) not in inconsistent_pairs and (type2, type1) not in inconsistent_pairs
    
    def _assess_reasoning_completeness(self, steps: List[Dict[str, Any]], context: ReasoningContext) -> float:
        """评估推理完整性"""
        if not steps:
            return 0.0
        
        # 基于目标覆盖度计算完整性
        goal_coverage = 0.0
        for goal in context.reasoning_goals:
            if self._is_goal_addressed(goal, steps):
                goal_coverage += 1.0
        
        goal_completeness = goal_coverage / max(1, len(context.reasoning_goals))
        
        # 基于前提使用度计算完整性
        premise_usage = self._calculate_premise_usage(context.premises, steps)
        
        return (goal_completeness + premise_usage) / 2.0
    
    def _is_goal_addressed(self, goal: str, steps: List[Dict[str, Any]]) -> bool:
        """检查目标是否被处理"""
        goal_lower = goal.lower()
        
        for step in steps:
            description = step.get('description', '').lower()
            if any(word in description for word in goal_lower.split()):
                return True
        
        return False
    
    def _calculate_premise_usage(self, premises: List[Any], steps: List[Dict[str, Any]]) -> float:
        """计算前提使用度"""
        if not premises:
            return 1.0
        
        used_premises = 0
        for premise in premises:
            if isinstance(premise, str):
                for step in steps:
                    description = step.get('description', '').lower()
                    if any(word in description for word in premise.lower().split()):
                        used_premises += 1
                        break
        
        return used_premises / len(premises)
    
    def _generate_reasoning_insights(self, steps: List[Dict[str, Any]]) -> List[str]:
        """生成推理洞察"""
        insights = []
        
        # 基于推理类型生成洞察
        reasoning_types = set(step.get('reasoning_type', 'general') for step in steps)
        
        if 'multi_step' in reasoning_types:
            insights.append("使用了多步推理，提高了推理的深度和准确性")
        
        if 'causal' in reasoning_types:
            insights.append("识别了因果关系，增强了推理的逻辑性")
        
        if 'analogical' in reasoning_types:
            insights.append("运用了类比推理，提高了推理的创造性")
        
        if 'probabilistic' in reasoning_types:
            insights.append("考虑了概率因素，增强了推理的可靠性")
        
        # 基于推理质量生成洞察
        quality = self._assess_reasoning_quality(steps)
        if quality > 0.8:
            insights.append("推理质量很高，结论可信度强")
        elif quality > 0.6:
            insights.append("推理质量良好，结论基本可信")
        else:
            insights.append("推理质量需要改进，结论可信度有限")
        
        return insights
    
    def _generate_conclusion(self, reasoning_chain: List[Dict[str, Any]], meta_reasoning: Dict[str, Any]) -> str:
        """生成结论"""
        if not reasoning_chain:
            return "无法生成结论"
        
        conclusion = "基于元推理分析：\n\n"
        
        # 添加推理过程总结
        conclusion += "推理过程：\n"
        for step in reasoning_chain:
            conclusion += f"{step['step']}. {step['description']}\n"
        
        # 添加元推理分析
        conclusion += "\n元推理分析：\n"
        conclusion += f"- 推理质量: {meta_reasoning['reasoning_quality']:.2f}\n"
        conclusion += f"- 推理效率: {meta_reasoning['reasoning_efficiency']:.2f}\n"
        conclusion += f"- 推理一致性: {meta_reasoning['reasoning_consistency']:.2f}\n"
        conclusion += f"- 推理完整性: {meta_reasoning['reasoning_completeness']:.2f}\n"
        
        # 添加推理洞察
        if meta_reasoning['reasoning_insights']:
            conclusion += "\n推理洞察：\n"
            for insight in meta_reasoning['reasoning_insights']:
                conclusion += f"- {insight}\n"
        
        conclusion += "\n结论: 通过元推理分析，我们得出了综合性的结论。"
        
        return conclusion
    
    def _calculate_confidence(self, reasoning_chain: List[Dict[str, Any]], meta_reasoning: Dict[str, Any], context: ReasoningContext) -> float:
        """计算置信度"""
        if not reasoning_chain:
            return 0.0
        
        # 基于推理链的置信度
        chain_confidences = [step.get('confidence', 0.5) for step in reasoning_chain]
        avg_chain_confidence = sum(chain_confidences) / len(chain_confidences)
        
        # 基于元推理质量
        meta_quality = meta_reasoning['reasoning_quality']
        
        # 基于推理完整性
        completeness = meta_reasoning['reasoning_completeness']
        
        # 综合置信度
        confidence = (avg_chain_confidence + meta_quality + completeness) / 3.0
        
        # 基于约束调整
        if context.confidence_threshold > 0.8:
            confidence *= 0.9  # 高阈值降低置信度
        elif context.confidence_threshold < 0.3:
            confidence *= 1.1  # 低阈值提高置信度
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_complexity_score(self, steps: List[Dict[str, Any]]) -> float:
        """计算复杂度分数"""
        if not steps:
            return 0.0
        
        # 基于步骤数量
        step_count = len(steps)
        step_complexity = min(1.0, step_count / 20.0)
        
        # 基于推理类型多样性
        reasoning_types = set(step.get('reasoning_type', 'general') for step in steps)
        type_complexity = min(1.0, len(reasoning_types) / 10.0)
        
        # 基于步骤置信度
        confidences = [step.get('confidence', 0.5) for step in steps]
        avg_confidence = sum(confidences) / len(confidences)
        confidence_complexity = avg_confidence
        
        return (step_complexity + type_complexity + confidence_complexity) / 3.0


class AdvancedReasoningEngineV2:
    """高级推理引擎V2"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.strategies = {
            ReasoningType.META_REASONING: MetaReasoningStrategy()
        }
        self.metrics = {
            'total_reasoning_sessions': 0,
            'successful_sessions': 0,
            'failed_sessions': 0,
            'average_confidence': 0.0,
            'average_complexity': 0.0
        }
    
    def execute_reasoning(self, context: ReasoningContext, reasoning_type: ReasoningType = ReasoningType.META_REASONING) -> ReasoningResult:
        """执行推理"""
        if reasoning_type not in self.strategies:
            reasoning_type = ReasoningType.META_REASONING
        
        self.metrics['total_reasoning_sessions'] += 1
        
        try:
            result = self.strategies[reasoning_type].execute(context)
            
            if result.success:
                self.metrics['successful_sessions'] += 1
            else:
                self.metrics['failed_sessions'] += 1
            
            # 更新指标
            self._update_metrics(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"推理执行失败: {e}")
            self.metrics['failed_sessions'] += 1
            
            return ReasoningResult(
                success=False,
                conclusion=None,
                confidence=0.0,
                reasoning_type=reasoning_type,
                steps=[],
                processing_time=0.0,
                complexity_score=0.0,
                reasoning_chain=[],
                meta_reasoning={},
                error=str(e)
            )
    
    def _update_metrics(self, result: ReasoningResult):
        """更新指标"""
        total = self.metrics['total_reasoning_sessions']
        
        # 更新平均置信度
        current_avg_conf = self.metrics['average_confidence']
        self.metrics['average_confidence'] = (current_avg_conf * (total - 1) + result.confidence) / total
        
        # 更新平均复杂度
        current_avg_comp = self.metrics['average_complexity']
        self.metrics['average_complexity'] = (current_avg_comp * (total - 1) + result.complexity_score) / total
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.metrics.copy()
    
    def get_available_reasoning_types(self) -> List[ReasoningType]:
        """获取可用推理类型"""
        return list(self.strategies.keys())
