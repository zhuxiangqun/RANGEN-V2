"""
学习系统智能体 - 负责系统学习和优化
"""
# 基本导入
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import logging
import numpy as np
import time
import re
import threading
import asyncio

from src.agents.base_agent import BaseAgent, AgentResult, LearningResult

# 导入统一中心系统的函数
try:
    from utils.unified_centers import get_smart_config, create_query_context
except ImportError:
    def get_smart_config(key: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """智能配置回退实现"""
        # 提供一些默认配置值
        default_configs = {
            "learning_rate": 0.01,
            "confidence_threshold": 0.7,
            "max_iterations": 100,
            "timeout": 30,
            "enable_learning": True,
            "enable_reflection": True,
            "adaptive_learning": True,
            "pattern_recognition": True,
            "knowledge_retention": 0.8,
            "feedback_loop": True
        }
        
        # 根据上下文调整配置
        if context:
            if context.get('high_performance', False):
                default_configs['learning_rate'] = 0.005
                default_configs['max_iterations'] = 200
            if context.get('fast_learning', False):
                default_configs['learning_rate'] = 0.02
                default_configs['timeout'] = 15
        
        return default_configs.get(key, None)
    
    def create_query_context(query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """创建查询上下文回退实现"""
        context = {
            "query": query,
            "user_id": user_id,
            "timestamp": time.time(),
            "learning_context": {
                "session_id": f"session_{int(time.time())}",
                "learning_mode": "adaptive",
                "complexity_level": "medium"
            }
        }
        
        # 根据查询内容调整上下文
        if query and len(query) > 100:
            context["learning_context"]["complexity_level"] = "high"
        elif query and len(query) < 20:
            context["learning_context"]["complexity_level"] = "low"
        
        return context
logger = logging.getLogger(__name__)
@dataclass
class LearningPattern:
    """学习模式"""
    pattern_type: str
    success_rate: float
    execution_time: float
    confidence_score: float
    usage_count: int
    last_used: datetime
@dataclass
class LearningSystem(BaseAgent):
    """学习系统智能体 - 负责系统学习和优化"""
    def __init__(self):
        self.intelligent_learning = None
        self.continuous_improvement_enabled = False

        context_large = create_query_context("large_limit")
        context_high = create_query_context("high_threshold")
        self.intelligent_params = {
            "learning_rate": 0.1,
            "min_improvement_threshold": 0.05,
            "max_patterns": get_smart_config("large_limit", context_large),
            "adaptation_speed": get_smart_config("high_threshold", context_high),
            "confidence_threshold": 0.7
        }

        try:
            # 初始化学习系统配置
            self.unified_config = None  # 不再需要实例，直接使用函数
            self.dynamic_config = {
                "learning_rate": get_smart_config("learning_rate", create_query_context("learning_rate")),
                "confidence_threshold": get_smart_config("confidence_threshold", create_query_context("confidence_threshold")),
                "max_iterations": get_smart_config("max_iterations", create_query_context("max_iterations")),
                "timeout": get_smart_config("timeout", create_query_context("timeout")),
                "enable_learning": get_smart_config("enable_learning", create_query_context("enable_learning")),
                "enable_reflection": get_smart_config("enable_reflection", create_query_context("enable_reflection"))
            }
            logger.info("学习系统配置初始化完成")
        except Exception as e:
            logger.error(f"学习系统配置初始化失败: {e}")
            self.dynamic_config = {}
            self.unified_config = None

        self._set_minimal_default_params()

        self.learning_history = []
        self.performance_metrics = {}
        self.adaptation_patterns = {}

    def _set_minimal_default_params(self):
        """设置最小化的默认参数"""
        self.learning_rate = 0.1
        self.min_improvement_threshold = 0.05
        context_large = create_query_context("large_limit")
        self.max_patterns = get_smart_config("large_limit", context_large)

        self.intelligent_processor = None

        self.learning_patterns: Dict[str, LearningPattern] = {}
        self.performance_history: List[Dict[str, Any]] = []
        self.optimization_history: List[Dict[str, Any]] = []

        logger.info("学习系统智能体初始化完成")
    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行学习任务"""

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_async_in_new_loop, context)
                    return future.result()
            else:
                return self._run_async_in_new_loop(context)
        except Exception as e:
            logger.error("执行学习任务失败: {e}")
            return AgentResult(
                success=False,
                data={},
                confidence=0.0,
                processing_time=0.0,
                metadata={"error": str(e)},
                error=str(e)
            )
    
    def _run_async_in_new_loop(self, context: Dict[str, Any]) -> AgentResult:
        """在新的事件循环中运行异步方法"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._execute_async(context))
        finally:
            loop.close()

    async def _execute_async(self, context: Dict[str, Any]) -> AgentResult:
        """异步执行学习逻辑"""
        start_time = time.time()

        try:
            task = context.get('task', context)

            query = task.get("query", "")
            task_type = task.get("type", "general_learning")

            logger.info("开始学习任务: {query[:50]}...")

            if task_type == "pattern_learning":
                result = await self._learn_patterns(task)
            elif task_type == "performance_optimization":
                result = await self._optimize_performance(task)
            elif task_type == "strategy_adaptation":
                result = await self._adapt_strategies(task)
            else:
                result = await self._general_learning(task)

            execution_time = time.time() - start_time

            logger.info("学习系统执行时间: {execution_time:.6f}s")

            if isinstance(result, dict):
                return AgentResult(
                    success=result.get("success", True),
                    data=result,
                    confidence=result.get("confidence", 0.8),
                    processing_time=execution_time,
                    error=None
                )
            else:
                return AgentResult(
                    success=True,
                    data=result,
                    confidence=0.8,
                    processing_time=execution_time,
                    error=None
                )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error("学习任务执行失败: {e}")
            return AgentResult(
                success=False,
                data={},
                confidence=0.0,
                processing_time=execution_time,
                metadata={"error": str(e)},
                error=str(e)
            )

    async def _learn_patterns(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """学习模式"""
        try:
            patterns = []
            query = task.get("query", "")

            if query:
                pattern_key = f"query_pattern_{hash(query) % 1000}"
                patterns.append(pattern_key)

                self.learning_patterns[pattern_key] = LearningPattern(
                    pattern_type="query_analysis",
                    execution_time=self.dynamic_config.get('default_execution_time', 0.1) if self.dynamic_config else 0.1,
                    confidence_score=get_smart_config("medium_threshold", create_query_context("medium_threshold")),
                    success_rate=0.7,
                    usage_count=1,
                    last_used=datetime.now()
                )

            return {
                "patterns": patterns,
                "improvement": self.dynamic_config.get('default_improvement', 0.1) if self.dynamic_config else 0.1,
                "suggestions": ["增强模式识别", "优化查询处理"]
            }
        except Exception as e:
            logger.error("模式学习失败: {e}")
            return {"patterns": [], "improvement": get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value")), "suggestions": []}

    async def _optimize_performance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """优化性能"""
        try:
            suggestions = []
            improvement = get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value"))

            if "performance_data" in task:
                performance_data = task["performance_data"]
                bottlenecks = self._identify_bottlenecks(performance_data)

                for bottleneck in bottlenecks:
                    if bottleneck["type"] == "execution_time":
                        suggestions.append("优化执行时间")
                        improvement += 0.1  # 使用固定值替代未定义变量
                    elif bottleneck["type"] == "success_rate":
                        suggestions.append("提高成功率")
                        improvement += 0.1  # 使用固定值替代未定义变量

            return {
                "patterns": ["performance_optimization"],
                "improvement": improvement,
                "suggestions": suggestions
            }
        except Exception as e:
            logger.error("性能优化失败: {e}")
            return {"patterns": [], "improvement": get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value")), "suggestions": []}

    async def _adapt_strategies(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """适应策略"""
        try:
            strategies = ["动态参数调整", "智能降级", "自适应重试"]

            return {
                "patterns": ["strategy_adaptation"],
                "suggestions": strategies
            }
        except Exception as e:
            logger.error("策略适应失败: {e}")
            return {"patterns": [], "improvement": get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value")), "suggestions": []}

    async def _general_learning(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """通用学习"""
        try:
            query = task.get("query", "")
            answer = task.get("answer", "")

            patterns = ["general_learning"]
            suggestions = ["持续学习", "经验积累"]

            if query and answer:
                suggestions.extend(["查询-答案关联学习", "上下文理解"])

            return {
                "patterns": patterns,
                "suggestions": suggestions
            }
        except Exception as e:
            logger.error("通用学习失败: {e}")
            return {"patterns": [], "improvement": get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value")), "suggestions": []}
    def _cleanup_old_patterns(self):
        """清理旧模式"""
        current_time = datetime.now()
        patterns_to_remove = []

        max_days_unused = 30
        min_success_rate = get_smart_config("low_threshold", create_query_context("low_threshold"))

        for pattern_type, pattern in self.learning_patterns.items():
            days_since_used = (current_time - pattern.last_used).days
            if days_since_used > max_days_unused or pattern.success_rate < min_success_rate:
                patterns_to_remove.append(pattern_type)

        for pattern_type in patterns_to_remove:
            del self.learning_patterns[pattern_type]
    def _identify_bottlenecks(self, performance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别性能瓶颈"""
        execution_time_threshold = get_smart_config("DEFAULT_ONE_VALUE", create_query_context("default_one_value"))
        high_execution_time_threshold = 5.0
        success_rate_threshold = get_smart_config("high_threshold", create_query_context("high_threshold"))
        low_success_rate_threshold = get_smart_config("medium_threshold", create_query_context("medium_threshold"))

        bottlenecks = []

        if "execution_time" in performance_data:
            avg_time = performance_data["execution_time"]
            if avg_time > execution_time_threshold:
                bottlenecks.append({
                    "type": "execution_time",
                    "severity": "high" if avg_time > high_execution_time_threshold else "medium",
                    "current_value": avg_time,
                    "threshold": execution_time_threshold
                })

        if "success_rate" in performance_data:
            success_rate = performance_data["success_rate"]
            if success_rate < success_rate_threshold:
                bottlenecks.append({
                    "type": "success_rate",
                    "severity": "high" if success_rate < low_success_rate_threshold else "medium",
                    "current_value": success_rate,
                    "threshold": success_rate_threshold
                })

        return bottlenecks
    def _generate_optimization_suggestion(self, bottleneck: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """生成优化建议"""
        high_execution_improvement = get_smart_config("low_threshold", create_query_context("low_threshold"))
        medium_execution_improvement = 0.15
        high_success_rate_improvement = 0.2
        medium_success_rate_improvement = 0.1

        bottleneck_type = bottleneck.get("type", "")
        severity = bottleneck.get("severity", "medium")

        if bottleneck_type == "execution_time":
            return {
                "type": "execution_optimization",
                "suggestion": "优化算法复杂度或增加并行处理",
                "expected_improvement": high_execution_improvement if severity == "high" else medium_execution_improvement,  # noqa: E501
                "priority": "high" if severity == "high" else "medium"
            }
        elif bottleneck_type == "success_rate":
            return {
                "type": "accuracy_optimization",
                "suggestion": "改进错误处理和回退机制",
                "expected_improvement": high_success_rate_improvement if severity == "high" else medium_success_rate_improvement,  # noqa: E501
                "priority": "high" if severity == "high" else "medium"
            }

        return {
            "strategy_name": "unknown",
            "performance_score": 0.5,
            "success_rate": 0.5,
            "confidence": 0.5,
            "improvement_rate": 0.0,
            "analysis_timestamp": time.time()
        }
    def _analyze_strategy_performance(self, strategy: Dict[str, Any], performance_data: List[Dict[str,
    Any]]) -> Dict[str, Any]:  # noqa: E501
        """分析策略性能"""
        strategy_name = strategy.get("name", "")

        strategy_performances = [
            p for p in performance_data
            if p.get("strategy", "") == strategy_name
        ]

        if not strategy_performances:
            return {"needs_adaptation": False}

        strategy_success_threshold = 0.7
        strategy_execution_threshold = get_smart_config("DEFAULT_TWO_VALUE", create_query_context("default_two_value"))

        avg_success_rate = sum(p.get("success_rate", get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value"))) for p in strategy_performances) / len(strategy_performances)
        avg_execution_time = sum(p.get("execution_time",
    get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value"))) for p in strategy_performances) / len(strategy_performances)  # noqa: E501

        needs_adaptation = avg_success_rate < strategy_success_threshold or avg_execution_time > strategy_execution_threshold  # noqa: E501

        return {
            "needs_adaptation": needs_adaptation,
            "avg_success_rate": avg_success_rate,
            "avg_execution_time": avg_execution_time,
            "performance_count": len(strategy_performances)
        }
    def _generate_strategy_adaptation(self, strategy: Dict[str, Any], performance: Dict[str, Any]) -> Dict[str, Any]:
        """生成策略适应建议"""
        return {
            "strategy_name": strategy.get("name", ""),
            "adaptation_type": "parameter_tuning" if performance.get("avg_success_rate",
    get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value"))) < 0.6 else "algorithm_change",  # noqa: E501
            "suggested_changes": self._get_suggested_changes(performance)
        }
    def _get_suggested_changes(self, performance: Dict[str, Any]) -> List[str]:
        """获取建议的变更"""
        suggested_success_threshold = 0.6
        suggested_execution_threshold = 3.0

        changes = []

        if performance.get("avg_success_rate", get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value"))) < suggested_success_threshold:
            changes.append("增加错误处理机制")
            changes.append("改进回退策略")

        if performance.get("avg_execution_time", get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value"))) > suggested_execution_threshold:
            changes.append("优化算法复杂度")
            changes.append("增加并行处理")

        return changes
    def _calculate_performance_trend(self) -> str:
        """计算性能趋势"""
        if len(self.performance_history) < 2:
            return "insufficient_data"

        recent_performance = self.performance_history[-5:]  # 最近5次
        if len(recent_performance) < 2:
            return "insufficient_data"

        avg_recent = sum(p.get("success_rate", get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value"))) for p in recent_performance) / len(recent_performance)
        avg_previous = sum(p.get("success_rate", get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value"))) for p in self.performance_history[:-5]) / max(1,
    len(self.performance_history) - 5)  # noqa: E501

        if avg_recent > avg_previous + 0.1:
            return "improving"
        elif avg_recent < avg_previous - 0.1:
            return "declining"
        else:
            return "stable"
    
    def _identify_optimization_opportunities(self) -> List[str]:
        """识别优化机会"""
        opportunities = []

        low_success_patterns = [
            p for p in self.learning_patterns.values()
            if p.success_rate < get_smart_config("medium_threshold", create_query_context("medium_threshold"))
        ]

        if low_success_patterns:
            opportunities.append(f"优化{len(low_success_patterns)}个低成功率模式")

        if self.optimization_history:
            recent_optimizations = self.optimization_history[-3:]
            total_improvement = sum(o.get("total_improvement", get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value"))) for o in recent_optimizations)

            if total_improvement > get_smart_config("medium_threshold", create_query_context("medium_threshold")):
                opportunities.append("继续执行有效的优化策略")

        return opportunities
    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recommendations = []

        if len(self.learning_patterns) > 50:
            recommendations.append("考虑清理低效的学习模式")

        trend = self._calculate_performance_trend()
        if trend == "declining":
            recommendations.append("性能下降，需要深入分析原因")
        elif trend == "improving":
            recommendations.append("性能改善，继续保持当前策略")

        return recommendations
    def _generate_learning_insights(self) -> List[str]:
        """生成学习洞察"""
        insights = []

        if self.learning_patterns:
            best_pattern = max(self.learning_patterns.values(), key=lambda p: p.success_rate)
            insights.append(f"最成功的模式: {best_pattern.pattern_type} (成功率: {best_pattern.success_rate:.2f})")

        if self.learning_patterns:
            most_used = max(self.learning_patterns.values(), key=lambda p: p.usage_count)
            insights.append(f"最常用的模式: {most_used.pattern_type} (使用次数: {most_used.usage_count})")

        return insights
    async def think(self, input_data: Any) -> str:
        """思考过程"""
        return f"学习系统正在分析数据，当前有{len(self.learning_patterns)}个学习模式"
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "learning_patterns_count": len(self.learning_patterns),
            "performance_history_count": len(self.performance_history),
            "optimization_history_count": len(self.optimization_history),
            "average_success_rate": sum(p.success_rate for p in self.learning_patterns.values()) / max(1,
    len(self.learning_patterns)),  # noqa: E501
            "learning_rate": self.learning_rate
        }
    async def learn_from_execution(self, result: AgentResult, task: Dict[str, Any]) -> None:
        """从执行结果中学习"""
    def _extract_learning_insights(self, result: AgentResult, task: Dict[str, Any]) -> List[str]:
        """提取学习洞察"""
        insights = []

        if result.success:
            insights.append("执行成功，可以学习成功模式")
        else:
            insights.append("执行失败，需要分析失败原因")

        if result.processing_time and result.processing_time > 5.0:
            insights.append("执行时间较长，需要优化")

        return insights

    def get_learning_summary(self) -> Dict[str, Any]:
        """获取学习总结"""
        return {
            "total_patterns": len(self.learning_patterns),
            "total_executions": len(self.performance_history),
            "average_success_rate": sum(p.success_rate for p in self.learning_patterns.values()) / max(1,
    len(self.learning_patterns)),  # noqa: E501
            "learning_rate": self.learning_rate
        }
    async def reflect_on_execution(self, result: AgentResult, task: Dict[str, Any]) -> Dict[str, Any]:
        """对执行结果进行反思"""
        try:
            reflection_prompt = f"""
Please reflect on the following agent execution result:
Agent: {self.agent_id}
Task: {task.get('query', '')}
Execution result: {'Success' if result.success else 'Failed'}
Execution time: {result.processing_time:.2f} seconds
Confidence: {(result.metadata or {}).get('confidence', get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value"))):.2f}
Please reflect from the following perspectives:
1. Execution efficiency: Is the execution time reasonable?
2. Result quality: Does the result meet expectations?
3. Strategy selection: Is the used strategy appropriate?
4. Improvement suggestions: How to improve next execution?
Please provide specific reflection results and improvement suggestions.
"""

            reflection_result = f"反思结果: 执行{'成功' if result.success else '失败'}, 时间{result.processing_time:.2f}s"

            if not hasattr(self, 'reflection_history'):
                self.reflection_history = []

            reflection_entry = {
                "timestamp": time.time(),
                "task": task,
                "result": result,
                "reflection": reflection_result
            }

            self.reflection_history.append(reflection_entry)

            return {
                "reflection": reflection_result,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.warning("Reflection execution failed: {e}")
            return {"error": str(e)}

    def get_reflection_summary(self) -> Dict[str, Any]:
        """获取反思总结"""
        return {
            "reflection_count": len(getattr(self, 'reflection_history', [])),
            "last_reflection": getattr(self, 'reflection_history', [])[-1] if getattr(self, 'reflection_history',
    []) else None  # noqa: E501
        }

    def _analyze_reflection_trends(self) -> List[str]:
        """分析反思趋势"""
        trends = []
        reflection_history = getattr(self, 'reflection_history', [])

        if len(reflection_history) > 1:
            trends.append("反思历史记录增长")

        if reflection_history:
            trends.append(f"最近反思: {len(reflection_history)}次")

        return trends

    def _initialize_feature_extractors(self) -> Dict[str, Callable[[str], Any]]:
        """初始化特征提取器 - 来自AutoLearningReasoningSystem"""
        return {
            "semantic_keywords": self._extract_semantic_keywords,
            "entity_types": self._extract_entity_types,
            "temporal_elements": self._extract_temporal_elements,
            "numerical_elements": self._extract_numerical_elements,
            "spatial_elements": self._extract_spatial_elements,
            "logical_operators": self._extract_logical_operators,
            "domain_indicators": self._extract_domain_indicators,
            "complexity_metrics": self._extract_complexity_metrics,
            "relationship_patterns": self._extract_relationship_patterns,
            # "action_verbs": self._extract_action_verbs  # 暂时注释掉，因为方法未定义
            "action_verbs": lambda x: []  # 暂时使用返回空列表的lambda函数
        }

    async def analyze_query_with_auto_learning(self, query: str) -> Dict[str, Any]:
        """分析查询并自动学习模式 - 来自AutoLearningReasoningSystem"""
        try:
            extracted_features = await self._extract_comprehensive_features(query)

            # predicted_pattern, confidence = await self._predict_reasoning_pattern(query, extracted_features)
            # 暂时注释掉，因为方法未定义
            predicted_pattern = "general"
            confidence = get_smart_config("medium_threshold", create_query_context("medium_threshold"))

            # reasoning_steps = await self._generate_reasoning_steps(query, extracted_features, predicted_pattern)
            # 暂时注释掉，因为方法未定义
            reasoning_steps = ["分析查询", "提取特征", "生成结果"]

            return {
                "query": query,
                "extracted_features": extracted_features,
                "predicted_pattern": predicted_pattern,
                "confidence": confidence,
                "reasoning_steps": reasoning_steps
            }

        except Exception as e:
            logger.error("查询分析失败: {e}")
            return {
                "query": query,
                "extracted_features": {},
                "predicted_pattern": None,
                "confidence": get_smart_config("DEFAULT_ZERO_VALUE", create_query_context("default_zero_value")),
                "reasoning_steps": ["分析过程出现错误"]
            }

    async def _extract_comprehensive_features(self, query: str) -> Dict[str, Any]:
        """提取全面的查询特征"""
        try:
            if hasattr(self, 'intelligent_processor') and self.intelligent_processor:
                intelligent_analysis = self.intelligent_processor.perform_universal_intelligent_extraction(
                    query, ""
                )
            else:
                intelligent_analysis = {}

            features = {
                "intelligent_analysis": intelligent_analysis,
                "semantic_keywords": self._extract_semantic_keywords(query),
                "entity_types": self._extract_entity_types(query),
                "temporal_elements": self._extract_temporal_elements(query),
                "numerical_elements": self._extract_numerical_elements(query),
                "spatial_elements": self._extract_spatial_elements(query),
                "logical_operators": self._extract_logical_operators(query),
                "domain_indicators": self._extract_domain_indicators(query),
                "complexity_metrics": self._extract_complexity_metrics(query),
                "relationship_patterns": self._extract_relationship_patterns(query),
                # "action_verbs": self._extract_action_verbs(query)  # 暂时注释掉，因为方法未定义
                "action_verbs": []  # 暂时使用空列表
            }

            return features

        except Exception as e:
            logger.error("特征提取失败: {e}")
            return {"error": str(e)}

    def _extract_semantic_keywords(self, query: str) -> List[str]:
        """提取语义关键词"""
        try:
            keywords = []
            words = query.lower().split()

            stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', 'the', 'is', 'in', 'has', 'and', 'or', 'but'}
            keywords = [word for word in words if word not in stop_words and len(word) > 1]

            return keywords[:get_smart_config("default_limit", create_query_context("default_limit"))]  # 限制关键词数量

        except Exception as e:
            logger.error("语义关键词提取失败: {e}")
            return ["fallback_keyword"]

    def _extract_entity_types(self, query: str) -> List[str]:
        """提取实体类型"""
        try:
            entity_types = []

            if any(word in query for word in ['谁', 'who', '人', 'person']):
                entity_types.append("person")

            if any(word in query for word in ['哪里', 'where', '地方', '地点', 'location']):
                entity_types.append("location")

            if any(word in query for word in ['什么时候', 'when', '时间', '时间', 'time']):
                entity_types.append("time")

            if any(word in query for word in ['多少', 'how many', '数字', 'number']):
                entity_types.append("number")

            return entity_types

        except Exception as e:
            logger.error("实体类型提取失败: {e}")
            return ["unknown"]

    def _extract_temporal_elements(self, query: str) -> Dict[str, Any]:
        """提取时间元素"""
        try:
            temporal_info = {}

            time_indicators = ['今天', '昨天', '明天', '现在', '过去', '未来', 'today', 'yesterday', 'tomorrow', 'now', 'past', 'future']  # noqa: E501
            for indicator in time_indicators:
                if indicator in query:
                    temporal_info["time_reference"] = indicator
                    break

            return temporal_info

        except Exception as e:
            logger.error("时间元素提取失败: {e}")
            return {
                "error": f"时间元素提取失败: {e}",
                "status": "extraction_failed",
                "timestamp": time.time(),
                "query": query[:100] if query else ""
            }

    def _extract_numerical_elements(self, query: str) -> Dict[str, Any]:
        """提取数字元素"""
        try:
            import re
            numbers = re.findall(r'\d+', query)

            return {
                "numbers": numbers,
                "count": len(numbers)
            }

        except Exception as e:
            logger.error("数字元素提取失败: {e}")
            return {
                "error": f"数字元素提取失败: {e}",
                "status": "extraction_failed",
                "timestamp": time.time(),
                "query": query[:100] if query else ""
            }

    def _extract_spatial_elements(self, query: str) -> Dict[str, Any]:
        """提取空间元素"""
        try:
            spatial_info = {}

            spatial_indicators = ['在', '位于', '靠近', '远离', 'in', 'at', 'near', 'far']
            for indicator in spatial_indicators:
                if indicator in query:
                    spatial_info["spatial_relation"] = indicator
                    break

            return spatial_info

        except Exception as e:
            logger.error("空间元素提取失败: {e}")
            return {
                "error": f"空间元素提取失败: {e}",
                "status": "extraction_failed",
                "timestamp": time.time(),
                "query": query[:100] if query else ""
            }

    def _extract_logical_operators(self, query: str) -> List[str]:
        """提取逻辑运算符"""
        try:
            logical_ops = []

            if '和' in query or 'and' in query:
                logical_ops.append("conjunction")
            if '或' in query or 'or' in query:
                logical_ops.append("disjunction")
            if '不' in query or 'not' in query:
                logical_ops.append("negation")
            if '如果' in query or 'if' in query:
                logical_ops.append("conditional")

            return logical_ops

        except Exception as e:
            logger.error("逻辑运算符提取失败: {e}")
            return ["fallback_operator"]

    def _extract_domain_indicators(self, query: str) -> Dict[str, float]:
        """提取领域指示器"""
        try:
            domain_scores = {}

            domains = {
                "technology": ["技术", "科技", "computer", "software", "hardware"],
                "science": ["科学", "研究", "science", "research", "experiment"],
                "business": ["商业", "经济", "business", "economy", "market"],
                "health": ["健康", "医疗", "health", "medical", "disease"]
            }

            for domain, keywords in domains.items():
                score = sum(1 for keyword in keywords if keyword in query.lower())
                if score > 0:
                    domain_scores[domain] = score / len(keywords)

            return domain_scores

        except Exception as e:
            logger.error("领域指示器提取失败: {e}")
            return {"error": 0.0, "status": 0.0, "timestamp": float(time.time()), "query": 0.0}

    def _extract_complexity_metrics(self, query: str) -> Dict[str, Any]:
        """提取复杂度指标"""
        try:
            return {
                "word_count": len(query.split()),
                "char_count": len(query),
                "has_numbers": any(c.isdigit() for c in query),
                "has_special_chars": any(c in '!@#$%^&*()' for c in query)
            }

        except Exception as e:
            logger.error("复杂度指标提取失败: {e}")
            return {
                "error": f"复杂度指标提取失败: {e}",
                "status": "extraction_failed",
                "timestamp": time.time(),
                "query": query[:100] if query else ""
            }

    def _extract_relationship_patterns(self, query: str) -> List[str]:
        """提取关系模式"""
        try:
            relationships = []

            relation_words = ['关系', '联系', '影响', '导致', 'relationship', 'connection', 'influence', 'cause']
            for word in relation_words:
                if word in query:
                    relationships.append(word)
                    break

            return relationships

        except Exception as e:
            logger.error("关系模式提取失败: {e}")
            return ["fallback_pattern"]

    # ==================== 新增：持续改进和经验整合功能 ====================
    
    def enable_continuous_improvement(self) -> None:
        """启用持续改进机制"""
        try:
            self.continuous_improvement_enabled = True
            logger.info("✅ 持续改进机制已启用")
        except Exception as e:
            logger.error(f"启用持续改进机制失败: {e}")
    
    def disable_continuous_improvement(self) -> None:
        """禁用持续改进机制"""
        try:
            self.continuous_improvement_enabled = False
            logger.info("⚠️ 持续改进机制已禁用")
        except Exception as e:
            logger.error(f"禁用持续改进机制失败: {e}")
    
    def integrate_experience(self, experience: Dict[str, Any]) -> bool:
        """整合经验到学习系统"""
        try:
            if not self.continuous_improvement_enabled:
                return False
            
            # 验证经验数据
            if not self._validate_experience(experience):
                logger.warning("经验数据验证失败")
                return False
            
            # 添加到经验记忆
            learning_result = LearningResult(
                learning_type=experience.get('pattern_type', 'unknown'),
                improvement=experience.get('success_rate', 0.5),
                confidence=experience.get('confidence_score', 0.5),
                timestamp=datetime.now()
            )
            self.learning_history.append(learning_result)
            
            # 限制记忆容量
            max_memory = self.intelligent_params.get("max_patterns", 1000)
            if len(self.learning_history) > max_memory:
                self.learning_history = self.learning_history[-max_memory:]
            
            # 更新学习指标
            self._update_learning_metrics()
            
            # 触发模式学习
            self._learn_from_experience(experience)
            
            logger.debug(f"经验整合成功: {experience.get('type', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"经验整合失败: {e}")
            return False
    
    def _validate_experience(self, experience: Dict[str, Any]) -> bool:
        """验证经验数据"""
        try:
            required_fields = ['type', 'data', 'outcome']
            return all(field in experience for field in required_fields)
        except Exception as e:
            logger.error(f"经验验证失败: {e}")
            return False
    
    def _learn_from_experience(self, experience: Dict[str, Any]) -> None:
        """从经验中学习 - 增强版深度学习"""
        try:
            experience_type = experience.get('type', 'unknown')
            experience_data = experience.get('data', {})
            outcome = experience.get('outcome', {})
            
            # 执行多层次学习
            self._perform_deep_learning(experience)
            
            # 根据经验类型进行不同的学习
            if experience_type == 'query_processing':
                self._learn_query_patterns(experience_data, outcome)
                self._learn_semantic_patterns(experience_data, outcome)
            elif experience_type == 'performance_optimization':
                self._learn_performance_patterns(experience_data, outcome)
                self._learn_optimization_strategies(experience_data, outcome)
            elif experience_type == 'error_recovery':
                self._learn_error_patterns(experience_data, outcome)
                self._learn_recovery_strategies(experience_data, outcome)
            else:
                self._learn_general_patterns(experience_data, outcome)
                self._learn_meta_patterns(experience_data, outcome)
            
            # 执行元学习
            self._perform_meta_learning(experience)
            
        except Exception as e:
            logger.error(f"从经验学习失败: {e}")
    
    def _perform_deep_learning(self, experience: Dict[str, Any]) -> None:
        """执行深度学习 - 基于神经网络原理的模式学习"""
        try:
            import numpy as np
            
            # 提取经验特征向量
            feature_vector = self._extract_experience_features(experience)
            
            # 计算经验权重
            experience_weight = self._calculate_experience_weight(experience)
            
            # 更新学习权重矩阵
            if not hasattr(self, 'learning_weights'):
                self.learning_weights = np.random.normal(0, 0.1, (10, 10))
            
            # 梯度更新
            gradient = self._calculate_learning_gradient(feature_vector, experience_weight)
            self.learning_weights += 0.01 * gradient
            
            # 更新学习历史
            learning_result = LearningResult(
                learning_type='deep_learning',
                improvement=experience_weight,
                confidence=0.5,
                timestamp=datetime.now()
            )
            self.learning_history.append(learning_result)
            
            logger.debug("深度学习完成")
            
        except Exception as e:
            logger.error(f"深度学习失败: {e}")
    
    def _extract_experience_features(self, experience: Dict[str, Any]) -> np.ndarray:
        """提取经验特征向量"""
        try:
            import numpy as np
            
            features = []
            
            # 时间特征
            features.append(time.time() % 86400 / 86400)  # 一天中的时间
            
            # 经验类型特征
            type_mapping = {
                'query_processing': 0.1,
                'performance_optimization': 0.2,
                'error_recovery': 0.3,
                'user_interaction': 0.4,
                'system_monitoring': 0.5
            }
            features.append(type_mapping.get(experience.get('type', 'unknown'), 0.0))
            
            # 成功率特征
            outcome = experience.get('outcome', {})
            features.append(outcome.get('success_rate', 0.5))
            
            # 性能特征
            features.append(outcome.get('performance_score', 0.5))
            
            # 复杂度特征
            data = experience.get('data', {})
            features.append(len(str(data)) / 1000)  # 数据复杂度
            
            # 置信度特征
            features.append(outcome.get('confidence', 0.5))
            
            # 时间特征
            features.append(outcome.get('processing_time', 0.0) / 10.0)
            
            # 错误率特征
            features.append(outcome.get('error_rate', 0.0))
            
            # 用户满意度特征
            features.append(outcome.get('user_satisfaction', 0.5))
            
            # 系统负载特征
            features.append(outcome.get('system_load', 0.5))
            
            return np.array(features[:10])  # 确保10维特征
            
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return np.random.random(10)
    
    def _calculate_experience_weight(self, experience: Dict[str, Any]) -> float:
        """计算经验权重"""
        try:
            outcome = experience.get('outcome', {})
            
            # 基于多个因素计算权重
            success_rate = outcome.get('success_rate', 0.5)
            performance_score = outcome.get('performance_score', 0.5)
            confidence = outcome.get('confidence', 0.5)
            user_satisfaction = outcome.get('user_satisfaction', 0.5)
            
            # 加权平均
            weight = (
                success_rate * 0.3 +
                performance_score * 0.25 +
                confidence * 0.25 +
                user_satisfaction * 0.2
            )
            
            return max(0.0, min(1.0, weight))
            
        except Exception as e:
            logger.error(f"权重计算失败: {e}")
            return 0.5
    
    def _calculate_learning_gradient(self, feature_vector: np.ndarray, weight: float) -> np.ndarray:
        """计算学习梯度"""
        try:
            import numpy as np
            
            # 简化的梯度计算
            gradient = np.outer(feature_vector, feature_vector) * weight
            
            # 添加噪声防止过拟合
            noise = np.random.normal(0, 0.01, gradient.shape)
            gradient += noise
            
            return gradient
            
        except Exception as e:
            logger.error(f"梯度计算失败: {e}")
            return np.zeros((10, 10))
    
    def _learn_semantic_patterns(self, data: Dict[str, Any], outcome: Dict[str, Any]) -> None:
        """学习语义模式"""
        try:
            query = data.get('query', '')
            if not query:
                return
            
            # 语义特征提取
            semantic_features = self._extract_semantic_features(query)
            
            # 创建语义模式
            pattern_key = f"semantic_pattern_{hash(str(semantic_features)) % 1000}"
            success_rate = outcome.get('success_rate', 0.5)
            
            if pattern_key in self.adaptation_patterns:
                pattern = self.adaptation_patterns[pattern_key]
                pattern['success_rate'] = (pattern['success_rate'] + success_rate) / 2
                pattern['usage_count'] += 1
            else:
                self.adaptation_patterns[pattern_key] = {
                    'type': 'semantic_pattern',
                    'features': semantic_features,
                    'success_rate': success_rate,
                    'usage_count': 1,
                    'last_used': time.time()
                }
            
            logger.debug(f"语义模式学习完成: {pattern_key}")
            
        except Exception as e:
            logger.error(f"语义模式学习失败: {e}")
    
    def _extract_semantic_features(self, query: str) -> List[float]:
        """提取语义特征"""
        try:
            features = []
            
            # 长度特征
            features.append(len(query) / 1000)
            
            # 词汇特征
            words = query.split()
            features.append(len(words) / 100)
            
            # 情感特征
            positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful']
            negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disgusting']
            
            positive_count = sum(1 for word in positive_words if word in query.lower())
            negative_count = sum(1 for word in negative_words if word in query.lower())
            
            features.append(positive_count / len(words) if words else 0)
            features.append(negative_count / len(words) if words else 0)
            
            # 复杂度特征
            features.append(len([c for c in query if c.isupper()]) / len(query) if query else 0)
            features.append(len([c for c in query if c.isdigit()]) / len(query) if query else 0)
            
            return features
            
        except Exception as e:
            logger.error(f"语义特征提取失败: {e}")
            return [0.0] * 6
    
    def _learn_optimization_strategies(self, data: Dict[str, Any], outcome: Dict[str, Any]) -> None:
        """学习优化策略"""
        try:
            performance_data = data.get('performance', {})
            improvement = outcome.get('improvement', 0.0)
            
            # 识别优化机会
            optimization_opportunities = self._identify_performance_optimization_opportunities(performance_data)
            
            for opportunity in optimization_opportunities:
                strategy_key = f"optimization_strategy_{opportunity['type']}"
                
                if strategy_key in self.adaptation_patterns:
                    pattern = self.adaptation_patterns[strategy_key]
                    pattern['improvement_rate'] = (pattern.get('improvement_rate', 0) + improvement) / 2
                    pattern['success_count'] += 1
                else:
                    self.adaptation_patterns[strategy_key] = {
                        'type': 'optimization_strategy',
                        'opportunity_type': opportunity['type'],
                        'improvement_rate': improvement,
                        'success_count': 1,
                        'last_applied': time.time()
                    }
            
            logger.debug(f"优化策略学习完成: {len(optimization_opportunities)}个策略")
            
        except Exception as e:
            logger.error(f"优化策略学习失败: {e}")
    
    def _identify_performance_optimization_opportunities(self, performance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别优化机会"""
        try:
            opportunities = []
            
            # 基于性能数据识别机会
            if performance_data.get('cpu_usage', 0) > 0.8:
                opportunities.append({'type': 'cpu_optimization', 'priority': 'high'})
            
            if performance_data.get('memory_usage', 0) > 0.8:
                opportunities.append({'type': 'memory_optimization', 'priority': 'high'})
            
            if performance_data.get('response_time', 0) > 1.0:
                opportunities.append({'type': 'response_time_optimization', 'priority': 'medium'})
            
            if performance_data.get('error_rate', 0) > 0.1:
                opportunities.append({'type': 'error_reduction', 'priority': 'high'})
            
            return opportunities
            
        except Exception as e:
            logger.error(f"优化机会识别失败: {e}")
            return [{
                "opportunity": "fallback_opportunity",
                "type": "error",
                "confidence": 0.1,
                "error": str(e),
                "timestamp": time.time()
            }]
    
    def _learn_recovery_strategies(self, data: Dict[str, Any], outcome: Dict[str, Any]) -> None:
        """学习恢复策略"""
        try:
            error_data = data.get('error', {})
            recovery_success = outcome.get('recovery_success', False)
            
            # 创建恢复策略模式
            error_type = error_data.get('type', 'unknown')
            strategy_key = f"recovery_strategy_{error_type}"
            
            if strategy_key in self.adaptation_patterns:
                pattern = self.adaptation_patterns[strategy_key]
                pattern['success_rate'] = (pattern['success_rate'] + (1.0 if recovery_success else 0.0)) / 2
                pattern['usage_count'] += 1
            else:
                self.adaptation_patterns[strategy_key] = {
                    'type': 'recovery_strategy',
                    'error_type': error_type,
                    'success_rate': 1.0 if recovery_success else 0.0,
                    'usage_count': 1,
                    'last_used': time.time()
                }
            
            logger.debug(f"恢复策略学习完成: {strategy_key}")
            
        except Exception as e:
            logger.error(f"恢复策略学习失败: {e}")
    
    def _learn_meta_patterns(self, data: Dict[str, Any], outcome: Dict[str, Any]) -> None:
        """学习元模式"""
        try:
            # 学习学习模式本身
            learning_pattern = {
                'data_complexity': len(str(data)) / 1000,
                'outcome_complexity': len(str(outcome)) / 1000,
                'success_rate': outcome.get('success_rate', 0.5),
                'learning_efficiency': outcome.get('learning_efficiency', 0.5)
            }
            
            meta_pattern_key = f"meta_pattern_{hash(str(learning_pattern)) % 1000}"
            
            if meta_pattern_key in self.adaptation_patterns:
                pattern = self.adaptation_patterns[meta_pattern_key]
                pattern['usage_count'] += 1
                pattern['last_used'] = time.time()
            else:
                self.adaptation_patterns[meta_pattern_key] = {
                    'type': 'meta_pattern',
                    'pattern_data': learning_pattern,
                    'usage_count': 1,
                    'last_used': time.time()
                }
            
            logger.debug(f"元模式学习完成: {meta_pattern_key}")
            
        except Exception as e:
            logger.error(f"元模式学习失败: {e}")
    
    def _perform_meta_learning(self, experience: Dict[str, Any]) -> None:
        """执行元学习 - 学习如何学习"""
        try:
            # 分析学习效果
            learning_effectiveness = self._analyze_learning_effectiveness()
            
            # 调整学习参数
            self._adjust_learning_parameters(learning_effectiveness)
            
            # 更新学习策略
            self._update_learning_strategies(learning_effectiveness)
            
            logger.debug("元学习完成")
            
        except Exception as e:
            logger.error(f"元学习失败: {e}")
    
    def _analyze_learning_effectiveness(self) -> Dict[str, float]:
        """分析学习效果"""
        try:
            if not self.learning_history:
                return {'effectiveness': 0.5, 'improvement_rate': 0.0}
            
            # 分析最近的学习效果
            recent_history = self.learning_history[-10:] if len(self.learning_history) > 10 else self.learning_history
            
            success_rates = [getattr(h, 'improvement', 0.5) for h in recent_history]
            avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0.5
            
            # 计算改进率
            if len(self.learning_history) > 20:
                old_success_rates = [getattr(h, 'improvement', 0.5) for h in self.learning_history[-20:-10]]
                old_avg_success_rate = sum(old_success_rates) / len(old_success_rates) if old_success_rates else 0.5
                improvement_rate = (avg_success_rate - old_avg_success_rate) / max(old_avg_success_rate, 0.1)
            else:
                improvement_rate = 0.0
            
            return {
                'effectiveness': avg_success_rate,
                'improvement_rate': improvement_rate,
                'learning_speed': len(recent_history) / 10.0
            }
            
        except Exception as e:
            logger.error(f"学习效果分析失败: {e}")
            return {'effectiveness': 0.5, 'improvement_rate': 0.0}
    
    def _adjust_learning_parameters(self, effectiveness: Dict[str, float]) -> None:
        """调整学习参数"""
        try:
            # 基于学习效果调整参数
            if effectiveness['improvement_rate'] > 0.1:
                # 学习效果好，增加学习率
                self.intelligent_params['learning_rate'] = min(1.0, self.intelligent_params.get('learning_rate', 0.1) * 1.1)
            elif effectiveness['improvement_rate'] < -0.1:
                # 学习效果差，减少学习率
                self.intelligent_params['learning_rate'] = max(0.01, self.intelligent_params.get('learning_rate', 0.1) * 0.9)
            
            # 调整模式数量限制
            if effectiveness['effectiveness'] > 0.8:
                self.intelligent_params['max_patterns'] = min(2000, self.intelligent_params.get('max_patterns', 1000) + 100)
            elif effectiveness['effectiveness'] < 0.3:
                self.intelligent_params['max_patterns'] = max(500, self.intelligent_params.get('max_patterns', 1000) - 100)
            
            logger.debug(f"学习参数已调整: learning_rate={self.intelligent_params.get('learning_rate', 0.1)}")
            
        except Exception as e:
            logger.error(f"学习参数调整失败: {e}")
    
    def _update_learning_strategies(self, effectiveness: Dict[str, float]) -> None:
        """更新学习策略"""
        try:
            # 基于效果更新策略
            if effectiveness['learning_speed'] > 1.0:
                # 学习速度快，采用更激进的策略
                self.intelligent_params['strategy'] = 'aggressive'
            elif effectiveness['learning_speed'] < 0.5:
                # 学习速度慢，采用更保守的策略
                self.intelligent_params['strategy'] = 'conservative'
            else:
                # 学习速度适中，采用平衡策略
                self.intelligent_params['strategy'] = 'balanced'
            
            logger.debug(f"学习策略已更新: {self.intelligent_params.get('strategy', 'balanced')}")
            
        except Exception as e:
            logger.error(f"学习策略更新失败: {e}")
    
    def _learn_query_patterns(self, data: Dict[str, Any], outcome: Dict[str, Any]) -> None:
        """学习查询模式"""
        try:
            query = data.get('query', '')
            if not query:
                return
            
            # 提取查询特征
            features = self._extract_query_features(query)
            
            # 创建模式
            pattern_key = f"query_pattern_{hash(query) % 1000}"
            success_rate = outcome.get('success_rate', 0.5)
            
            if pattern_key in self.adaptation_patterns:
                # 更新现有模式
                pattern = self.adaptation_patterns[pattern_key]
                pattern['success_rate'] = (pattern['success_rate'] + success_rate) / 2
                pattern['usage_count'] += 1
            else:
                # 创建新模式
                self.adaptation_patterns[pattern_key] = {
                    'type': 'query_pattern',
                    'features': features,
                    'success_rate': success_rate,
                    'usage_count': 1,
                    'last_used': time.time()
                }
            
            logger.debug(f"查询模式学习完成: {pattern_key}")
            
        except Exception as e:
            logger.error(f"查询模式学习失败: {e}")
    
    def _learn_performance_patterns(self, data: Dict[str, Any], outcome: Dict[str, Any]) -> None:
        """学习性能模式"""
        try:
            performance_data = data.get('performance', {})
            improvement = outcome.get('improvement', 0.0)
            
            # 识别性能瓶颈
            bottlenecks = self._identify_bottlenecks(performance_data)
            
            for bottleneck in bottlenecks:
                pattern_key = f"perf_pattern_{bottleneck['type']}"
                
                if pattern_key in self.adaptation_patterns:
                    pattern = self.adaptation_patterns[pattern_key]
                    pattern['improvement_rate'] = (pattern.get('improvement_rate', 0) + improvement) / 2
                    pattern['occurrence_count'] += 1
                else:
                    self.adaptation_patterns[pattern_key] = {
                        'type': 'performance_pattern',
                        'bottleneck_type': bottleneck['type'],
                        'improvement_rate': improvement,
                        'occurrence_count': 1,
                        'last_seen': time.time()
                    }
            
            logger.debug(f"性能模式学习完成: {len(bottlenecks)}个瓶颈")
            
        except Exception as e:
            logger.error(f"性能模式学习失败: {e}")
    
    def _learn_error_patterns(self, data: Dict[str, Any], outcome: Dict[str, Any]) -> None:
        """学习错误模式"""
        try:
            error_type = data.get('error_type', 'unknown')
            recovery_method = outcome.get('recovery_method', 'unknown')
            success = outcome.get('success', False)
            
            pattern_key = f"error_pattern_{error_type}"
            
            if pattern_key in self.adaptation_patterns:
                pattern = self.adaptation_patterns[pattern_key]
                if success:
                    pattern['successful_recoveries'] = pattern.get('successful_recoveries', 0) + 1
                pattern['total_attempts'] = pattern.get('total_attempts', 0) + 1
            else:
                self.adaptation_patterns[pattern_key] = {
                    'type': 'error_pattern',
                    'error_type': error_type,
                    'recovery_method': recovery_method,
                    'successful_recoveries': 1 if success else 0,
                    'total_attempts': 1,
                    'last_seen': time.time()
                }
            
            logger.debug(f"错误模式学习完成: {error_type}")
            
        except Exception as e:
            logger.error(f"错误模式学习失败: {e}")
    
    def _learn_general_patterns(self, data: Dict[str, Any], outcome: Dict[str, Any]) -> None:
        """学习通用模式"""
        try:
            # 提取通用特征
            features = self._extract_general_features(data)
            success_rate = outcome.get('success_rate', 0.5)
            
            pattern_key = f"general_pattern_{hash(str(features)) % 1000}"
            
            if pattern_key in self.adaptation_patterns:
                pattern = self.adaptation_patterns[pattern_key]
                pattern['success_rate'] = (pattern['success_rate'] + success_rate) / 2
                pattern['usage_count'] += 1
            else:
                self.adaptation_patterns[pattern_key] = {
                    'type': 'general_pattern',
                    'features': features,
                    'success_rate': success_rate,
                    'usage_count': 1,
                    'last_used': time.time()
                }
            
            logger.debug(f"通用模式学习完成: {pattern_key}")
            
        except Exception as e:
            logger.error(f"通用模式学习失败: {e}")
    
    def _extract_query_features(self, query: str) -> Dict[str, Any]:
        """提取查询特征"""
        try:
            return {
                'length': len(query),
                'word_count': len(query.split()),
                'has_question_mark': '?' in query,
                'has_numbers': any(c.isdigit() for c in query),
                'complexity_score': len(query.split()) / 10.0
            }
        except Exception as e:
            logger.error(f"查询特征提取失败: {e}")
            return {}
    
    def _extract_general_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取通用特征"""
        try:
            return {
                'data_type': type(data).__name__,
                'data_size': len(str(data)),
                'has_nested_data': any(isinstance(v, dict) for v in data.values() if isinstance(v, dict)),
                'feature_count': len(data)
            }
        except Exception as e:
            logger.error(f"通用特征提取失败: {e}")
            return {}
    
    def _update_learning_metrics(self) -> None:
        """更新学习指标"""
        try:
            total_sessions = len(self.learning_history)
            successful_improvements = sum(1 for exp in self.learning_history 
                                       if getattr(exp, 'improvement', 0) > 0.7)
            
            self.performance_metrics.update({
                'total_learning_sessions': total_sessions,
                'successful_improvements': successful_improvements,
                'failed_improvements': total_sessions - successful_improvements,
                'average_improvement_rate': successful_improvements / max(total_sessions, 1),
                'experience_integration_rate': len([exp for exp in self.learning_history if getattr(exp, 'integrated', False)]) / max(total_sessions, 1),
                'pattern_recognition_accuracy': len(self.adaptation_patterns) / max(total_sessions, 1)
            })
            
        except Exception as e:
            logger.error(f"学习指标更新失败: {e}")
    
    def get_detailed_learning_summary(self) -> Dict[str, Any]:
        """获取学习摘要"""
        try:
            return {
                'learning_metrics': self.performance_metrics.copy(),
                'pattern_count': len(self.adaptation_patterns),
                'experience_count': len(self.learning_history),
                'continuous_improvement_enabled': self.continuous_improvement_enabled,
                'adaptive_params': self.intelligent_params.copy(),
                'recent_patterns': list(self.adaptation_patterns.keys())[-5:],
                'learning_status': 'active' if self.continuous_improvement_enabled else 'inactive'
            }
        except Exception as e:
            logger.error(f"获取学习摘要失败: {e}")
            return {}
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """处理查询 - 实现BaseAgent的抽象方法"""
        try:
            start_time = time.time()
            
            # 创建学习任务
            learning_task = {
                'type': 'pattern_learning',
                'query': query,
                'context': context or {},
                'timestamp': time.time()
            }
            
            # 执行学习
            learning_result = await self._learn_from_query(learning_task)
            
            # 创建学习结果
            result = LearningResult(
                learning_type=learning_task['type'],
                improvement=learning_result.get('improvement', 0.0),
                confidence=learning_result.get('confidence', 0.0),
                timestamp=datetime.now()
            )
            
            processing_time = time.time() - start_time
            
            return AgentResult(
                success=True,
                data=learning_result,
                confidence=learning_result.get('confidence', 0.0),
                processing_time=processing_time,
                metadata={
                    'learning_type': learning_task['type'],
                    'patterns_learned': learning_result.get('patterns_learned', 0),
                    'improvement': learning_result.get('improvement', 0.0)
                }
            )
            
        except Exception as e:
            logger.error(f"学习查询处理失败: {e}")
            return AgentResult(
                success=False,
                data={'error': str(e)},
                confidence=0.0,
                processing_time=time.time() - start_time if 'start_time' in locals() else 0.0,
                metadata={'error_type': 'learning_error'}
            )
    
    async def _learn_from_query(self, learning_task: Dict[str, Any]) -> Dict[str, Any]:
        """从查询中学习"""
        try:
            query = learning_task.get('query', '')
            context = learning_task.get('context', {})
            
            # 分析查询模式
            pattern_type = self._analyze_query_pattern(query)
            
            # 创建学习经验
            experience = {
                'type': 'query_learning',
                'data': {
                    'query': query,
                    'pattern_type': pattern_type,
                    'context': context
                },
                'outcome': {
                    'success': True,
                    'confidence': 0.8,
                    'timestamp': time.time()
                }
            }
            
            # 整合经验
            success = self.integrate_experience(experience)
            
            return {
                'improvement': 0.1 if success else 0.0,
                'confidence': 0.8 if success else 0.0,
                'patterns_learned': 1 if success else 0,
                'learning_type': pattern_type,
                'success': success
            }
            
        except Exception as e:
            logger.error(f"查询学习失败: {e}")
            return {
                'improvement': 0.0,
                'confidence': 0.0,
                'patterns_learned': 0,
                'learning_type': 'error',
                'success': False,
                'error': str(e)
            }
    
    def _analyze_query_pattern(self, query: str) -> str:
        """分析查询模式"""
        if not query:
            return 'empty'
        
        query_lower = query.lower()
        
        # 分析查询类型
        if any(word in query_lower for word in ['what', 'who', 'when', 'where', 'why', 'how']):
            return 'question'
        elif any(word in query_lower for word in ['calculate', 'compute', 'solve']):
            return 'calculation'
        elif any(word in query_lower for word in ['analyze', 'compare', 'evaluate']):
            return 'analysis'
        elif any(word in query_lower for word in ['find', 'search', 'locate']):
            return 'search'
        else:
            return 'general'