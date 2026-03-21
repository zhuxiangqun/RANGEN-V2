"""
策略模式基类
定义推理步骤生成的策略接口
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class QueryAnalysis:
    """查询分析结果"""

    def __init__(self,
                 query: str,
                 complexity_score: float = 3.0,
                 query_type: str = "general",
                 estimated_steps: int = 3,
                 requires_reasoning: bool = False,
                 domains: Optional[List[str]] = None,
                 keywords: Optional[List[str]] = None):
        self.query = query
        self.complexity_score = complexity_score
        self.query_type = query_type
        self.estimated_steps = estimated_steps
        self.requires_reasoning = requires_reasoning
        self.domains = domains or []
        self.keywords = keywords or []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'query': self.query,
            'complexity_score': self.complexity_score,
            'query_type': self.query_type,
            'estimated_steps': self.estimated_steps,
            'requires_reasoning': self.requires_reasoning,
            'domains': self.domains,
            'keywords': self.keywords
        }


class BaseStepGenerationStrategy(ABC):
    """推理步骤生成策略基类"""

    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.name}")

        # 策略统计
        self.stats = {
            'calls': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'avg_generation_time': 0.0
        }

    @abstractmethod
    def can_handle(self, analysis: QueryAnalysis) -> bool:
        """判断此策略是否能处理给定的查询分析结果

        Args:
            analysis: 查询分析结果

        Returns:
            bool: 是否能处理
        """
        pass

    @abstractmethod
    def generate_steps(self, query: str, analysis: QueryAnalysis,
                      context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成推理步骤

        Args:
            query: 原始查询
            analysis: 查询分析结果
            context: 额外的上下文信息

        Returns:
            List[Dict[str, Any]]: 生成的推理步骤列表
        """
        pass

    def get_confidence_score(self, analysis: QueryAnalysis) -> float:
        """获取此策略处理给定查询的置信度分数

        Args:
            analysis: 查询分析结果

        Returns:
            float: 置信度分数 (0.0-1.0)
        """
        if self.can_handle(analysis):
            return 0.8  # 默认置信度
        return 0.0

    def get_expected_steps_count(self, analysis: QueryAnalysis) -> int:
        """获取预期生成的步骤数量

        Args:
            analysis: 查询分析结果

        Returns:
            int: 预期步骤数量
        """
        return analysis.estimated_steps

    def validate_generated_steps(self, steps: List[Dict[str, Any]],
                                query: str, analysis: QueryAnalysis) -> bool:
        """验证生成的步骤是否符合策略要求

        Args:
            steps: 生成的步骤
            query: 原始查询
            analysis: 查询分析结果

        Returns:
            bool: 验证是否通过
        """
        if not steps:
            return False

        # 基本验证：步骤数量合理
        expected_count = self.get_expected_steps_count(analysis)
        if abs(len(steps) - expected_count) > 2:  # 允许±2的误差
            self.logger.warning(f"步骤数量不符合预期: 期望{expected_count}, 实际{len(steps)}")
            return False

        # 验证每个步骤的基本结构
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                self.logger.error(f"步骤{i}不是字典格式")
                return False

            required_fields = ['type', 'description']
            for field in required_fields:
                if field not in step or not step[field]:
                    self.logger.error(f"步骤{i}缺少必需字段: {field}")
                    return False

        return True

    def update_stats(self, success: bool, generation_time: float = 0.0):
        """更新策略统计信息"""
        self.stats['calls'] += 1
        if success:
            self.stats['successful_generations'] += 1
        else:
            self.stats['failed_generations'] += 1

        if generation_time > 0:
            # 更新平均生成时间
            total_time = self.stats['avg_generation_time'] * (self.stats['calls'] - 1)
            self.stats['avg_generation_time'] = (total_time + generation_time) / self.stats['calls']

    def get_stats(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        stats = self.stats.copy()
        total_calls = stats['calls']
        if total_calls > 0:
            stats['success_rate'] = stats['successful_generations'] / total_calls * 100
            stats['failure_rate'] = stats['failed_generations'] / total_calls * 100
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0

        return stats

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'calls': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'avg_generation_time': 0.0
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return f"{self.name}(calls={self.stats['calls']}, success_rate={self.get_stats().get('success_rate', 0):.1f}%)"
