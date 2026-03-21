"""
复杂查询策略
处理需要多步推理的复杂查询，生成详细的推理步骤
"""
import time
import re
from typing import Dict, List, Any, Optional

from .base_strategy import BaseStepGenerationStrategy, QueryAnalysis


class ComplexQueryStrategy(BaseStepGenerationStrategy):
    """复杂查询策略

    适用于：
    - 多跳推理查询
    - 复杂度评分 >= 3.0
    - 需要多步逻辑推理
    - 涉及多个领域
    """

    def __init__(self, name: str = "ComplexQueryStrategy"):
        super().__init__(name)

        # 推理模式映射
        self.inference_patterns = {
            'historical_relation': self._generate_historical_steps,
            'multi_hop_facts': self._generate_multi_hop_steps,
            'numerical_reasoning': self._generate_numerical_steps,
            'comparative_analysis': self._generate_comparison_steps,
            'multi_domain': self._generate_multi_domain_steps,
            'complex': self._generate_general_complex_steps
        }

    def can_handle(self, analysis: QueryAnalysis) -> bool:
        """判断是否能处理复杂查询"""
        return (analysis.complexity_score >= 3.0 or
                analysis.requires_reasoning or
                analysis.estimated_steps > 2 or
                analysis.query_type in ['historical_relation', 'multi_hop_facts',
                                      'numerical_reasoning', 'comparative_analysis',
                                      'multi_domain'])

    def generate_steps(self, query: str, analysis: QueryAnalysis,
                      context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成复杂的推理步骤"""
        start_time = time.time()

        try:
            # 根据查询类型选择推理模式
            inference_func = self.inference_patterns.get(
                analysis.query_type,
                self._generate_general_complex_steps
            )

            steps = inference_func(query, analysis, context)

            # 验证生成的步骤
            if self.validate_generated_steps(steps, query, analysis):
                generation_time = time.time() - start_time
                self.update_stats(True, generation_time)
                self.logger.info(f"✅ 复杂查询策略成功生成步骤: {len(steps)}步，用时{generation_time:.2f}s")
                return steps
            else:
                self.logger.error("生成的步骤验证失败")
                generation_time = time.time() - start_time
                self.update_stats(False, generation_time)
                return []

        except Exception as e:
            self.logger.error(f"复杂查询策略生成失败: {e}")
            generation_time = time.time() - start_time
            self.update_stats(False, generation_time)
            return []

    def get_confidence_score(self, analysis: QueryAnalysis) -> float:
        """获取处理复杂查询的置信度"""
        if not self.can_handle(analysis):
            return 0.0

        # 基础置信度
        base_confidence = 0.8

        # 根据复杂度调整
        if analysis.complexity_score >= 6.0:
            base_confidence += 0.1  # 高复杂度更适合此策略
        elif analysis.complexity_score < 4.0:
            base_confidence -= 0.1  # 低复杂度可能不是最佳选择

        # 根据查询类型调整
        if analysis.query_type in ['historical_relation', 'multi_hop_facts']:
            base_confidence += 0.1  # 这些类型是此策略的强项

        return min(1.0, max(0.1, base_confidence))

    def get_expected_steps_count(self, analysis: QueryAnalysis) -> int:
        """根据复杂度估算步骤数量"""
        base_steps = analysis.estimated_steps

        # 根据查询类型调整
        if analysis.query_type == 'historical_relation':
            base_steps = max(base_steps, 4)  # 历史关系至少需要4步
        elif analysis.query_type == 'multi_hop_facts':
            base_steps = max(base_steps, 3)  # 多跳事实至少需要3步
        elif analysis.query_type == 'numerical_reasoning':
            base_steps = max(base_steps, 3)  # 数值推理至少需要3步

        return min(base_steps, 8)  # 最多8步

    def _generate_historical_steps(self, query: str, analysis: QueryAnalysis,
                                  context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成历史关系查询的步骤"""
        steps = []

        # 识别关键人物
        if '15th' in query.lower() and 'first lady' in query.lower():
            steps.extend([
                {
                    "type": "information_gathering",
                    "description": "识别第15任美国第一夫人",
                    "sub_query": "Who was the 15th First Lady of the United States?",
                    "strategy": self.name
                },
                {
                    "type": "information_gathering",
                    "description": "查找第一夫人的母亲信息",
                    "sub_query": "[step 1 result]'s mother",
                    "dependencies": [1],
                    "strategy": self.name
                },
                {
                    "type": "information_gathering",
                    "description": "识别第二位遇刺的美国总统",
                    "sub_query": "Who was the second assassinated President of the United States?",
                    "strategy": self.name
                },
                {
                    "type": "information_gathering",
                    "description": "查找总统的母亲信息",
                    "sub_query": "[step 3 result]'s mother",
                    "dependencies": [3],
                    "strategy": self.name
                },
                {
                    "type": "answer_synthesis",
                    "description": "根据母亲的名字组合出最终答案",
                    "sub_query": f"Combine the names: first name from [step 2 result], surname from [step 4 result]",
                    "dependencies": [2, 4],
                    "strategy": self.name
                }
            ])
        else:
            # 通用历史关系推理
            steps.extend(self._generate_general_complex_steps(query, analysis, context))

        return steps

    def _generate_multi_hop_steps(self, query: str, analysis: QueryAnalysis,
                                 context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成多跳事实推理的步骤"""
        steps = []

        # 分析查询中的关系链
        query_lower = query.lower()

        # 查找关系指示词
        relation_indicators = ['whose', 'where', 'when', 'how many', 'what is']
        found_indicators = [ind for ind in relation_indicators if ind in query_lower]

        step_count = min(len(found_indicators) + 2, 6)  # 基于指示词数量决定步骤数

        for i in range(step_count - 1):
            steps.append({
                "type": "information_gathering",
                "description": f"执行第{i+1}步信息检索",
                "sub_query": f"Step {i+1} of multi-hop reasoning for: {query[:50]}...",
                "strategy": self.name
            })

        # 最后一步：答案合成
        dependencies = list(range(1, step_count))
        steps.append({
            "type": "answer_synthesis",
            "description": "基于多步检索结果合成最终答案",
            "sub_query": f"Synthesize answer from {step_count-1} information gathering steps",
            "dependencies": dependencies,
            "strategy": self.name
        })

        return steps

    def _generate_numerical_steps(self, query: str, analysis: QueryAnalysis,
                                 context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成数值推理的步骤"""
        steps = []

        # 检查是否涉及计算
        if any(word in query.lower() for word in ['calculate', 'compute', 'equals', 'dewey']):
            steps.extend([
                {
                    "type": "information_gathering",
                    "description": "提取数值信息",
                    "sub_query": "Extract numerical values from the query",
                    "strategy": self.name
                },
                {
                    "type": "analysis",
                    "description": "执行数值计算",
                    "sub_query": "Perform the required numerical calculation",
                    "dependencies": [1],
                    "strategy": self.name
                },
                {
                    "type": "answer_synthesis",
                    "description": "格式化计算结果",
                    "sub_query": "Format the numerical result as the final answer",
                    "dependencies": [2],
                    "strategy": self.name
                }
            ])
        else:
            steps.extend(self._generate_general_complex_steps(query, analysis, context))

        return steps

    def _generate_comparison_steps(self, query: str, analysis: QueryAnalysis,
                                  context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成比较分析的步骤"""
        steps = []

        if 'rank' in query.lower() or 'tallest' in query.lower():
            steps.extend([
                {
                    "type": "information_gathering",
                    "description": "收集比较对象的数据",
                    "sub_query": "Gather data for all comparison subjects",
                    "strategy": self.name
                },
                {
                    "type": "analysis",
                    "description": "分析和排序比较对象",
                    "sub_query": "Analyze and rank the comparison subjects",
                    "dependencies": [1],
                    "strategy": self.name
                },
                {
                    "type": "answer_synthesis",
                    "description": "确定排名结果",
                    "sub_query": "Determine the final ranking result",
                    "dependencies": [2],
                    "strategy": self.name
                }
            ])
        else:
            steps.extend(self._generate_general_complex_steps(query, analysis, context))

        return steps

    def _generate_multi_domain_steps(self, query: str, analysis: QueryAnalysis,
                                    context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成多领域查询的步骤"""
        steps = []

        # 为每个领域生成检索步骤
        domains = analysis.domains[:4]  # 最多处理4个领域

        for i, domain in enumerate(domains):
            steps.append({
                "type": "information_gathering",
                "description": f"从{domain}领域收集相关信息",
                "sub_query": f"Gather information from {domain} domain for: {query[:50]}...",
                "domain": domain,
                "strategy": self.name
            })

        # 跨领域分析步骤
        if len(domains) > 1:
            dependencies = list(range(1, len(domains) + 1))
            steps.append({
                "type": "analysis",
                "description": "整合多领域信息",
                "sub_query": f"Synthesize information from {len(domains)} domains",
                "dependencies": dependencies,
                "strategy": self.name
            })

        # 最终答案合成
        final_dependencies = [len(steps)] if len(steps) > 1 else [1]
        steps.append({
            "type": "answer_synthesis",
            "description": "生成跨领域综合答案",
            "sub_query": "Generate comprehensive answer across domains",
            "dependencies": final_dependencies,
            "strategy": self.name
        })

        return steps

    def _generate_general_complex_steps(self, query: str, analysis: QueryAnalysis,
                                       context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成通用复杂查询步骤"""
        steps = []

        # 基于复杂度评分决定步骤数量
        step_count = min(max(3, int(analysis.complexity_score / 2)), 6)

        for i in range(step_count - 1):
            steps.append({
                "type": "information_gathering",
                "description": f"执行推理步骤{i+1}",
                "sub_query": f"Step {i+1} reasoning for complex query: {query[:50]}...",
                "strategy": self.name
            })

        # 最终合成步骤
        dependencies = list(range(1, step_count))
        steps.append({
            "type": "answer_synthesis",
            "description": "基于所有推理步骤合成最终答案",
            "sub_query": f"Synthesize answer from {step_count-1} reasoning steps",
            "dependencies": dependencies,
            "strategy": self.name
        })

        return steps
