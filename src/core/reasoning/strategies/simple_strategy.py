"""
简单查询策略
处理简单的事实检索查询，生成最少的推理步骤
"""
import time
from typing import Dict, List, Any, Optional

from .base_strategy import BaseStepGenerationStrategy, QueryAnalysis


class SimpleQueryStrategy(BaseStepGenerationStrategy):
    """简单查询策略

    适用于：
    - 事实检索查询
    - 复杂度评分 < 3.0
    - 预计只需要1-2步推理
    """

    def __init__(self, name: str = "SimpleQueryStrategy"):
        super().__init__(name)

    def can_handle(self, analysis: QueryAnalysis) -> bool:
        """判断是否能处理简单查询"""
        # 简单查询的标准：
        # 1. 复杂度评分低
        # 2. 不是复杂推理类型
        # 3. 查询长度适中
        return (analysis.complexity_score < 3.0 and
                analysis.query_type in ['fact_retrieval', 'general'] and
                len(analysis.query) < 200)

    def generate_steps(self, query: str, analysis: QueryAnalysis,
                      context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成简单的推理步骤"""
        start_time = time.time()

        try:
            # 对于简单查询，通常只需要一步：直接检索答案
            steps = [
                {
                    "type": "answer_synthesis",
                    "description": f"检索关于'{query[:50]}...'的答案",
                    "sub_query": query,
                    "strategy": self.name,
                    "confidence": 0.9
                }
            ]

            # 验证生成的步骤
            if self.validate_generated_steps(steps, query, analysis):
                generation_time = time.time() - start_time
                self.update_stats(True, generation_time)
                self.logger.info(f"✅ 简单查询策略成功生成步骤: {len(steps)}步，用时{generation_time:.2f}s")
                return steps
            else:
                self.logger.error("生成的步骤验证失败")
                generation_time = time.time() - start_time
                self.update_stats(False, generation_time)
                return []

        except Exception as e:
            self.logger.error(f"简单查询策略生成失败: {e}")
            generation_time = time.time() - start_time
            self.update_stats(False, generation_time)
            return []

    def get_confidence_score(self, analysis: QueryAnalysis) -> float:
        """获取处理简单查询的置信度"""
        if not self.can_handle(analysis):
            return 0.0

        # 根据复杂度评分计算置信度
        # 复杂度越低，置信度越高
        base_confidence = 0.9
        complexity_penalty = analysis.complexity_score / 10.0  # 复杂度越高，惩罚越大

        return max(0.1, base_confidence - complexity_penalty)

    def get_expected_steps_count(self, analysis: QueryAnalysis) -> int:
        """简单查询通常只需要1步"""
        return 1

    def validate_generated_steps(self, steps: List[Dict[str, Any]],
                                query: str, analysis: QueryAnalysis) -> bool:
        """验证简单查询生成的步骤"""
        # 调用父类验证
        if not super().validate_generated_steps(steps, query, analysis):
            return False

        # 简单查询特有的验证
        if len(steps) != 1:
            self.logger.warning(f"简单查询应该只有1步，但生成了{len(steps)}步")
            return False

        # 检查步骤类型是否合适
        step = steps[0]
        if step.get('type') not in ['answer_synthesis', 'information_gathering']:
            self.logger.warning(f"简单查询的步骤类型不合适: {step.get('type')}")
            return False

        return True
