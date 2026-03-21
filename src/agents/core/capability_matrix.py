"""
智能体能力评估矩阵

基于头条文章启示实现的智能体能力量化评估系统。
提供多维度能力评分和任务智能体匹配功能。
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CapabilityScore:
    """能力评分"""
    knowledge_retrieval: float  # 知识检索能力
    reasoning_depth: float      # 推理深度
    creativity: float           # 创造性
    speed: float               # 执行速度
    reliability: float         # 可靠性
    adaptability: float        # 适应性


class CapabilityAssessmentMatrix:
    """智能体能力评估矩阵"""

    def __init__(self):
        self.capability_weights = {
            'knowledge_retrieval': 0.25,
            'reasoning_depth': 0.20,
            'creativity': 0.15,
            'speed': 0.15,
            'reliability': 0.15,
            'adaptability': 0.10
        }

        # 能力基准数据
        self.baseline_scores = {
            'EnhancedKnowledgeRetrievalAgent': {
                'knowledge_retrieval': 0.95,
                'reasoning_depth': 0.70,
                'creativity': 0.60,
                'speed': 0.85,
                'reliability': 0.90,
                'adaptability': 0.75
            },
            'EnhancedReasoningAgent': {
                'knowledge_retrieval': 0.75,
                'reasoning_depth': 0.95,
                'creativity': 0.85,
                'speed': 0.70,
                'reliability': 0.85,
                'adaptability': 0.80
            },
            'EnhancedAnswerGenerationAgent': {
                'knowledge_retrieval': 0.80,
                'reasoning_depth': 0.85,
                'creativity': 0.90,
                'speed': 0.75,
                'reliability': 0.80,
                'adaptability': 0.85
            },
            'EnhancedCitationAgent': {
                'knowledge_retrieval': 0.85,
                'reasoning_depth': 0.65,
                'creativity': 0.50,
                'speed': 0.90,
                'reliability': 0.95,
                'adaptability': 0.70
            },
            'FactVerificationAgent': {
                'knowledge_retrieval': 0.90,
                'reasoning_depth': 0.80,
                'creativity': 0.55,
                'speed': 0.80,
                'reliability': 0.95,
                'adaptability': 0.75
            }
        }

        # 历史性能数据存储
        self.performance_history = {}
        self.last_updated = datetime.now()

        logger.info("✅ 智能体能力评估矩阵初始化完成")

    def assess_agent_capability(self, agent_type: str, performance_data: Dict[str, Any]) -> CapabilityScore:
        """评估智能体能力"""
        try:
            logger.info(f"🔍 评估智能体能力: {agent_type}")

            # 获取基准评分
            baseline = self.baseline_scores.get(agent_type, self._get_default_baseline())

            # 基于历史性能数据调整评分
            adjusted_scores = self._adjust_scores_based_on_performance(
                agent_type, baseline, performance_data
            )

            capability_score = CapabilityScore(**adjusted_scores)

            # 记录评估结果
            self._record_assessment(agent_type, capability_score, performance_data)

            logger.info(f"✅ {agent_type} 能力评估完成: 综合评分={self._calculate_overall_score(capability_score):.2f}")

            return capability_score

        except Exception as e:
            logger.error(f"❌ 智能体能力评估失败 {agent_type}: {e}")
            # 返回默认评分
            return CapabilityScore(
                knowledge_retrieval=0.5,
                reasoning_depth=0.5,
                creativity=0.5,
                speed=0.5,
                reliability=0.5,
                adaptability=0.5
            )

    def get_optimal_agent_for_task(self, task_features: Dict[str, Any], available_agents: List[str]) -> str:
        """为任务选择最优智能体"""
        try:
            logger.info(f"🎯 为任务选择最优智能体，候选: {available_agents}")

            best_match = None
            best_score = -1

            for agent_type in available_agents:
                # 获取智能体能力
                capability = self.get_agent_capability(agent_type)

                # 计算任务-智能体匹配度
                match_score = self._calculate_task_agent_match(task_features, capability)

                logger.debug(f"📊 {agent_type} 匹配度: {match_score:.3f}")

                if match_score > best_score:
                    best_score = match_score
                    best_match = agent_type

            if best_match:
                logger.info(f"✅ 选择最优智能体: {best_match} (匹配度: {best_score:.3f})")
            else:
                logger.warning("⚠️ 未找到合适的智能体")

            return best_match

        except Exception as e:
            logger.error(f"❌ 智能体选择失败: {e}")
            return available_agents[0] if available_agents else None

    def get_agent_capability(self, agent_type: str) -> CapabilityScore:
        """获取智能体能力评分"""
        # 检查是否有历史评估数据
        if agent_type in self.performance_history:
            # 使用最新的评估结果
            latest_assessment = max(
                self.performance_history[agent_type],
                key=lambda x: x['timestamp']
            )
            return latest_assessment['capability']

        # 使用基准评分
        baseline = self.baseline_scores.get(agent_type, self._get_default_baseline())
        return CapabilityScore(**baseline)

    def update_capability_from_feedback(self, agent_type: str, task_result: Dict[str, Any]) -> None:
        """基于任务结果更新智能体能力评估"""
        try:
            # 分析任务结果
            performance_metrics = self._extract_performance_metrics(task_result)

            # 获取当前能力评分
            current_capability = self.get_agent_capability(agent_type)

            # 基于反馈调整评分
            updated_scores = self._adjust_scores_from_feedback(
                current_capability, performance_metrics
            )

            # 创建新的能力评分
            new_capability = CapabilityScore(**updated_scores)

            # 记录更新
            self._record_assessment(agent_type, new_capability, performance_metrics)

            logger.info(f"🔄 {agent_type} 能力评分已更新")

        except Exception as e:
            logger.error(f"❌ 更新智能体能力失败 {agent_type}: {e}")

    def _calculate_task_agent_match(self, task_features: Dict[str, Any], capability: CapabilityScore) -> float:
        """计算任务-智能体匹配度"""
        try:
            # 任务特征权重
            task_weights = self._analyze_task_requirements(task_features)

            # 计算加权匹配度
            match_score = (
                task_weights['knowledge'] * capability.knowledge_retrieval +
                task_weights['reasoning'] * capability.reasoning_depth +
                task_weights['creativity'] * capability.creativity +
                task_weights['speed'] * capability.speed +
                task_weights['reliability'] * capability.reliability +
                task_weights['adaptability'] * capability.adaptability
            )

            # 应用兼容性因子
            compatibility_factor = self._calculate_compatibility_factor(task_features, capability)
            final_score = match_score * compatibility_factor

            return min(final_score, 1.0)  # 确保不超过1.0

        except Exception as e:
            logger.error(f"❌ 计算匹配度失败: {e}")
            return 0.5  # 默认中等匹配度

    def _analyze_task_requirements(self, task_features: Dict[str, Any]) -> Dict[str, float]:
        """分析任务需求权重"""
        # 基于任务特征确定能力权重
        task_type = task_features.get('type', 'general')
        complexity = task_features.get('complexity', 'medium')
        time_pressure = task_features.get('time_pressure', 'medium')

        base_weights = {
            'knowledge': 0.20,
            'reasoning': 0.25,
            'creativity': 0.15,
            'speed': 0.15,
            'reliability': 0.15,
            'adaptability': 0.10
        }

        # 根据任务类型调整权重
        if task_type == 'research':
            base_weights.update({
                'knowledge': 0.35,
                'reasoning': 0.30,
                'reliability': 0.20
            })
        elif task_type == 'creative':
            base_weights.update({
                'creativity': 0.30,
                'reasoning': 0.25,
                'adaptability': 0.20
            })
        elif task_type == 'analysis':
            base_weights.update({
                'reasoning': 0.35,
                'knowledge': 0.25,
                'reliability': 0.20
            })

        # 根据复杂度调整
        if complexity == 'high':
            base_weights['reasoning'] += 0.10
            base_weights['adaptability'] += 0.05
        elif complexity == 'low':
            base_weights['speed'] += 0.10
            base_weights['reasoning'] -= 0.05

        # 根据时间压力调整
        if time_pressure == 'high':
            base_weights['speed'] += 0.15
            base_weights['reasoning'] -= 0.10

        return base_weights

    def _calculate_compatibility_factor(self, task_features: Dict[str, Any], capability: CapabilityScore) -> float:
        """计算兼容性因子"""
        # 基于任务特殊要求计算兼容性
        compatibility = 1.0

        # 检查特殊技能要求
        required_skills = task_features.get('required_skills', [])
        agent_skills = task_features.get('agent_skills', [])

        if required_skills:
            matched_skills = len(set(required_skills) & set(agent_skills))
            compatibility *= (matched_skills / len(required_skills)) * 0.3 + 0.7

        # 检查经验水平匹配
        required_experience = task_features.get('experience_level', 'intermediate')
        experience_levels = {'beginner': 1, 'intermediate': 2, 'expert': 3}

        # 这里可以根据智能体的历史表现推断经验水平
        # 暂时使用默认兼容性
        compatibility *= 0.9

        return max(compatibility, 0.5)

    def _adjust_scores_based_on_performance(self, agent_type: str, baseline: Dict[str, float],
                                          performance_data: Dict[str, Any]) -> Dict[str, float]:
        """基于性能数据调整评分"""
        adjusted = baseline.copy()

        # 从性能数据中提取调整因子
        success_rate = performance_data.get('success_rate', 0.8)
        quality_score = performance_data.get('quality_score', 0.7)
        response_time = performance_data.get('avg_response_time', 30)

        # 基于成功率调整可靠性
        if success_rate > 0.9:
            adjusted['reliability'] = min(baseline['reliability'] + 0.1, 1.0)
        elif success_rate < 0.7:
            adjusted['reliability'] = max(baseline['reliability'] - 0.1, 0.1)

        # 基于质量评分调整推理深度和创造性
        if quality_score > 0.8:
            adjusted['reasoning_depth'] = min(baseline['reasoning_depth'] + 0.05, 1.0)
            adjusted['creativity'] = min(baseline['creativity'] + 0.05, 1.0)
        elif quality_score < 0.6:
            adjusted['reasoning_depth'] = max(baseline['reasoning_depth'] - 0.05, 0.1)
            adjusted['creativity'] = max(baseline['creativity'] - 0.05, 0.1)

        # 基于响应时间调整速度
        if response_time < 20:
            adjusted['speed'] = min(baseline['speed'] + 0.1, 1.0)
        elif response_time > 60:
            adjusted['speed'] = max(baseline['speed'] - 0.1, 0.1)

        return adjusted

    def _adjust_scores_from_feedback(self, current_capability: CapabilityScore,
                                   performance_metrics: Dict[str, Any]) -> Dict[str, float]:
        """基于反馈调整评分"""
        # 实现更细粒度的评分调整逻辑
        adjusted = {
            'knowledge_retrieval': current_capability.knowledge_retrieval,
            'reasoning_depth': current_capability.reasoning_depth,
            'creativity': current_capability.creativity,
            'speed': current_capability.speed,
            'reliability': current_capability.reliability,
            'adaptability': current_capability.adaptability
        }

        # 基于具体反馈指标调整
        feedback_indicators = performance_metrics.get('feedback_indicators', {})

        for indicator, value in feedback_indicators.items():
            if indicator == 'knowledge_accuracy' and value > 0.8:
                adjusted['knowledge_retrieval'] = min(adjusted['knowledge_retrieval'] + 0.05, 1.0)
            elif indicator == 'reasoning_quality' and value > 0.8:
                adjusted['reasoning_depth'] = min(adjusted['reasoning_depth'] + 0.05, 1.0)
            # 添加更多调整逻辑...

        return adjusted

    def _extract_performance_metrics(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """从任务结果中提取性能指标"""
        return {
            'success': task_result.get('success', False),
            'quality_score': task_result.get('quality_score', 0.7),
            'response_time': task_result.get('response_time', 30),
            'feedback_indicators': task_result.get('feedback_indicators', {})
        }

    def _calculate_overall_score(self, capability: CapabilityScore) -> float:
        """计算综合评分"""
        return (
            capability.knowledge_retrieval * self.capability_weights['knowledge_retrieval'] +
            capability.reasoning_depth * self.capability_weights['reasoning_depth'] +
            capability.creativity * self.capability_weights['creativity'] +
            capability.speed * self.capability_weights['speed'] +
            capability.reliability * self.capability_weights['reliability'] +
            capability.adaptability * self.capability_weights['adaptability']
        )

    def _get_default_baseline(self) -> Dict[str, float]:
        """获取默认基准评分"""
        return {
            'knowledge_retrieval': 0.7,
            'reasoning_depth': 0.7,
            'creativity': 0.6,
            'speed': 0.7,
            'reliability': 0.7,
            'adaptability': 0.6
        }

    def _record_assessment(self, agent_type: str, capability: CapabilityScore,
                          performance_data: Dict[str, Any]) -> None:
        """记录评估结果"""
        if agent_type not in self.performance_history:
            self.performance_history[agent_type] = []

        assessment_record = {
            'timestamp': datetime.now(),
            'capability': capability,
            'performance_data': performance_data,
            'overall_score': self._calculate_overall_score(capability)
        }

        self.performance_history[agent_type].append(assessment_record)

        # 限制历史记录数量
        if len(self.performance_history[agent_type]) > 50:
            self.performance_history[agent_type] = self.performance_history[agent_type][-50:]
