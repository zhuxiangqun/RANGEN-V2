"""
策略选择器
根据查询分析结果选择最合适的推理策略
"""
import logging
from typing import List, Optional

from .base_strategy import BaseStepGenerationStrategy, QueryAnalysis

logger = logging.getLogger(__name__)


class StepGenerationStrategySelector:
    """推理策略选择器"""

    def __init__(self, strategies: Optional[List[BaseStepGenerationStrategy]] = None):
        self.strategies = strategies or []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 选择统计
        self.stats = {
            'selections': 0,
            'strategy_usage': {},
            'avg_selection_time': 0.0
        }

        if self.strategies:
            self.logger.info(f"✅ 策略选择器初始化完成，支持{len(self.strategies)}个策略")

    def select(self, analysis: QueryAnalysis) -> BaseStepGenerationStrategy:
        """选择最合适的推理策略"""
        import time
        start_time = time.time()

        if not self.strategies:
            raise RuntimeError("没有可用的推理策略")

        try:
            # 找到所有能处理此查询的策略
            candidates = [s for s in self.strategies if s.can_handle(analysis)]

            if not candidates:
                # 如果没有策略能处理，选择默认策略（通常是最后一个）
                selected = self.strategies[-1]
                self.logger.warning(f"没有策略能完美处理查询，使用默认策略: {selected.name}")
            elif len(candidates) == 1:
                # 只有一个候选策略
                selected = candidates[0]
            else:
                # 多个候选策略，选择置信度最高的
                selected = max(candidates, key=lambda s: s.get_confidence_score(analysis))

            # 更新统计
            selection_time = time.time() - start_time
            self._update_stats(selected, selection_time)

            self.logger.info(f"✅ 选择策略: {selected.name} (置信度: {selected.get_confidence_score(analysis):.2f})")
            return selected

        except Exception as e:
            self.logger.error(f"策略选择失败: {e}")
            # 返回第一个策略作为fallback
            return self.strategies[0]

    def add_strategy(self, strategy: BaseStepGenerationStrategy):
        """添加新的推理策略"""
        if strategy not in self.strategies:
            self.strategies.append(strategy)
            self.logger.info(f"✅ 策略已添加: {strategy.name}")
        else:
            self.logger.warning(f"策略已存在: {strategy.name}")

    def remove_strategy(self, strategy_name: str):
        """移除推理策略"""
        original_count = len(self.strategies)
        self.strategies = [s for s in self.strategies if s.name != strategy_name]

        if len(self.strategies) < original_count:
            self.logger.info(f"✅ 策略已移除: {strategy_name}")
        else:
            self.logger.warning(f"策略不存在: {strategy_name}")

    def get_available_strategies(self) -> List[str]:
        """获取所有可用策略的名称"""
        return [s.name for s in self.strategies]

    def get_strategy_stats(self, strategy_name: Optional[str] = None) -> dict:
        """获取策略统计信息"""
        if strategy_name:
            strategy = next((s for s in self.strategies if s.name == strategy_name), None)
            if strategy:
                return strategy.get_stats()
            else:
                return {}
        else:
            # 返回所有策略的统计
            return {
                'selector_stats': self.stats,
                'strategy_stats': {
                    s.name: s.get_stats() for s in self.strategies
                }
            }

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'selections': 0,
            'strategy_usage': {},
            'avg_selection_time': 0.0
        }

        for strategy in self.strategies:
            strategy.reset_stats()

        self.logger.info("✅ 统计信息已重置")

    def _update_stats(self, selected_strategy: BaseStepGenerationStrategy, selection_time: float):
        """更新选择统计"""
        self.stats['selections'] += 1

        # 更新策略使用统计
        strategy_name = selected_strategy.name
        if strategy_name not in self.stats['strategy_usage']:
            self.stats['strategy_usage'][strategy_name] = 0
        self.stats['strategy_usage'][strategy_name] += 1

        # 更新平均选择时间
        total_time = self.stats['avg_selection_time'] * (self.stats['selections'] - 1)
        self.stats['avg_selection_time'] = (total_time + selection_time) / self.stats['selections']

    def create_default_selector() -> 'StepGenerationStrategySelector':
        """创建默认的策略选择器（包含所有内置策略）"""
        try:
            from .simple_strategy import SimpleQueryStrategy
            from .complex_strategy import ComplexQueryStrategy

            strategies = [
                SimpleQueryStrategy(),
                ComplexQueryStrategy()
            ]

            selector = StepGenerationStrategySelector(strategies)
            logger.info("✅ 默认策略选择器创建成功")
            return selector

        except ImportError as e:
            logger.error(f"创建默认策略选择器失败: {e}")
            # 返回空的选择器
            return StepGenerationStrategySelector([])
