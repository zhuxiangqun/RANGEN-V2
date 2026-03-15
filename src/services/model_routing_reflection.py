#!/usr/bin/env python3
"""
模型路由反思模块

基于反思型架构（Reflexion/LATS）实现多模型路由器的自我优化能力。
当路由决策失败或效果不佳时，系统能够：
1. 分析失败原因
2. 生成改进建议  
3. 调整后续路由策略

集成现有的 ReflectionAgent 框架，专门针对模型路由场景优化。
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from src.core.reflection import ReflectionAgent, ReflexionAgent, ReflectionResult, ReflectionType

logger = logging.getLogger(__name__)


class RoutingDecisionType(str, Enum):
    """路由决策类型"""
    INITIAL = "initial"           # 初始选择
    FALLBACK = "fallback"        # 回退选择
    RETRY = "retry"              # 重试选择
    LEARNED = "learned"          # 基于学习的选择


class RoutingQuality(str, Enum):
    """路由质量评估"""
    EXCELLENT = "excellent"      # 优秀：快速成功，高质量
    GOOD = "good"                # 良好：成功但可能有小问题
    ACCEPTABLE = "acceptable"    # 可接受：成功但有明显问题
    POOR = "poor"                # 差：成功但质量低
    FAILED = "failed"            # 失败：模型调用失败


@dataclass
class RoutingDecision:
    """路由决策记录"""
    timestamp: float
    request_id: str
    selected_model: str
    available_models: List[str]
    routing_strategy: str
    decision_type: RoutingDecisionType = RoutingDecisionType.INITIAL
    fallback_original: Optional[str] = None  # 如果是回退，记录原始选择
    request_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 上下文信息
    request_content: str = ""
    content_length: int = 0
    detected_keywords: List[str] = field(default_factory=list)
    estimated_complexity: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "selected_model": self.selected_model,
            "available_models": self.available_models,
            "routing_strategy": self.routing_strategy,
            "decision_type": self.decision_type.value,
            "fallback_original": self.fallback_original,
            "request_metadata": self.request_metadata,
            "content_length": self.content_length,
            "detected_keywords": self.detected_keywords,
            "estimated_complexity": self.estimated_complexity
        }


@dataclass
class RoutingOutcome:
    """路由结果"""
    decision: RoutingDecision
    response: Dict[str, Any]
    latency_ms: float
    success: bool
    error_message: Optional[str] = None
    user_feedback: Optional[float] = None  # 用户评分 0-1
    quality_metrics: Dict[str, float] = field(default_factory=dict)  # 质量指标
    
    @property
    def quality(self) -> RoutingQuality:
        """计算总体质量"""
        if not self.success:
            return RoutingQuality.FAILED
        
        if self.user_feedback is not None:
            if self.user_feedback >= 0.8:
                return RoutingQuality.EXCELLENT
            elif self.user_feedback >= 0.6:
                return RoutingQuality.GOOD
            elif self.user_feedback >= 0.4:
                return RoutingQuality.ACCEPTABLE
            else:
                return RoutingQuality.POOR
        
        # 基于延迟和响应质量估算
        if self.latency_ms < 1000 and self.response.get("confidence", 1.0) > 0.8:
            return RoutingQuality.EXCELLENT
        elif self.latency_ms < 3000 and self.response.get("success", False):
            return RoutingQuality.GOOD
        elif self.success:
            return RoutingQuality.ACCEPTABLE
        else:
            return RoutingQuality.POOR
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "decision": self.decision.to_dict(),
            "success": self.success,
            "latency_ms": self.latency_ms,
            "quality": self.quality.value,
            "error_message": self.error_message,
            "user_feedback": self.user_feedback,
            "quality_metrics": self.quality_metrics
        }


class ModelRoutingReflectionAgent(ReflexionAgent):
    """模型路由反思代理
    
    专门针对多模型路由场景的反思型Agent，基于Reflexion框架实现：
    - 分析路由决策的质量和效果
    - 识别失败模式和优化机会
    - 生成具体的路由策略改进建议
    - 积累经验用于未来决策优化
    """
    
    def __init__(self, llm_provider=None):
        super().__init__(llm_provider)
        
        # 路由特定的数据
        self.routing_decisions: List[RoutingDecision] = []
        self.routing_outcomes: List[RoutingOutcome] = []
        self.learning_patterns: Dict[str, Any] = {}
        
        # 路由性能统计
        self.model_performance: Dict[str, Dict[str, Any]] = {}
        
        logger.info("ModelRoutingReflectionAgent initialized")
    
    def record_decision(self, decision: RoutingDecision) -> str:
        """记录路由决策
        
        Args:
            decision: 路由决策
            
        Returns:
            decision_id: 决策ID
        """
        self.routing_decisions.append(decision)
        
        # 限制历史记录大小
        if len(self.routing_decisions) > 1000:
            self.routing_decisions = self.routing_decisions[-1000:]
        
        # 生成决策ID（简化版）
        decision_id = f"decision_{int(decision.timestamp)}_{len(self.routing_decisions)}"
        
        logger.debug(f"Recorded routing decision: {decision_id} -> {decision.selected_model}")
        return decision_id
    
    def record_outcome(self, outcome: RoutingOutcome) -> str:
        """记录路由结果
        
        Args:
            outcome: 路由结果
            
        Returns:
            outcome_id: 结果ID
        """
        self.routing_outcomes.append(outcome)
        
        # 限制历史记录大小
        if len(self.routing_outcomes) > 1000:
            self.routing_outcomes = self.routing_outcomes[-1000:]
        
        # 更新模型性能统计
        self._update_model_performance(outcome)
        
        # 生成结果ID
        outcome_id = f"outcome_{int(outcome.decision.timestamp)}_{len(self.routing_outcomes)}"
        
        logger.debug(f"Recorded routing outcome: {outcome_id} -> {outcome.quality.value}")
        return outcome_id
    
    def _update_model_performance(self, outcome: RoutingOutcome):
        """更新模型性能统计"""
        model_name = outcome.decision.selected_model
        
        if model_name not in self.model_performance:
            self.model_performance[model_name] = {
                "total_requests": 0,
                "successful_requests": 0,
                "total_latency_ms": 0,
                "failure_reasons": {},
                "by_strategy": {}
            }
        
        stats = self.model_performance[model_name]
        stats["total_requests"] += 1
        
        if outcome.success:
            stats["successful_requests"] += 1
            stats["total_latency_ms"] += outcome.latency_ms
        
        # 记录失败原因
        if not outcome.success and outcome.error_message:
            error_type = outcome.error_message.split(":")[0] if ":" in outcome.error_message else "unknown"
            stats["failure_reasons"][error_type] = stats["failure_reasons"].get(error_type, 0) + 1
        
        # 按策略统计
        strategy = outcome.decision.routing_strategy
        if strategy not in stats["by_strategy"]:
            stats["by_strategy"][strategy] = {"requests": 0, "successes": 0}
        
        stats["by_strategy"][strategy]["requests"] += 1
        if outcome.success:
            stats["by_strategy"][strategy]["successes"] += 1
    
    async def reflect_on_routing(self, outcome: RoutingOutcome) -> ReflectionResult:
        """对路由决策进行反思
        
        Args:
            outcome: 路由结果
            
        Returns:
            反思结果
        """
        decision = outcome.decision
        
        # 准备反思上下文
        context = {
            "decision": decision.to_dict(),
            "outcome": outcome.to_dict(),
            "model_performance": self._get_relevant_performance_stats(decision.selected_model),
            "available_models": decision.available_models
        }
        
        # 定义反思任务
        task = f"""
        分析模型路由决策的质量和效果。
        
        决策详情：
        - 选择的模型：{decision.selected_model}
        - 路由策略：{decision.routing_strategy}
        - 决策类型：{decision.decision_type.value}
        - 请求内容长度：{decision.content_length}字符
        - 检测到的关键词：{decision.detected_keywords}
        
        结果详情：
        - 是否成功：{outcome.success}
        - 延迟：{outcome.latency_ms}ms
        - 质量评估：{outcome.quality.value}
        - 错误信息：{outcome.error_message or '无'}
        - 用户反馈：{outcome.user_feedback or '无'}
        """
        
        # 执行反思
        reflection = await self.reflect_with_trace(
            task=task,
            action=f"model_routing_{decision.selected_model}",
            result=outcome.to_dict(),
            context=context
        )
        
        # 如果是失败或质量差，进行深入分析
        if outcome.quality in [RoutingQuality.FAILED, RoutingQuality.POOR]:
            await self._analyze_failure_pattern(outcome, reflection)
        
        return reflection
    
    def _get_relevant_performance_stats(self, model_name: str) -> Dict[str, Any]:
        """获取相关模型性能统计"""
        if model_name not in self.model_performance:
            return {"total_requests": 0, "success_rate": 0.0}
        
        stats = self.model_performance[model_name]
        success_rate = (stats["successful_requests"] / stats["total_requests"]) if stats["total_requests"] > 0 else 0
        
        return {
            "total_requests": stats["total_requests"],
            "successful_requests": stats["successful_requests"],
            "success_rate": success_rate,
            "avg_latency_ms": (stats["total_latency_ms"] / stats["successful_requests"]) if stats["successful_requests"] > 0 else 0,
            "failure_reasons": stats["failure_reasons"]
        }
    
    async def _analyze_failure_pattern(self, outcome: RoutingOutcome, reflection: ReflectionResult):
        """分析失败模式"""
        decision = outcome.decision
        
        # 识别可能的失败模式
        patterns = []
        
        # 1. 模型能力不匹配
        if "代码" in decision.detected_keywords and decision.selected_model == "step-3.5-flash":
            patterns.append("代码生成任务可能更适合DeepSeek模型")
        
        # 2. 内容长度不匹配
        if decision.content_length > 2000 and decision.selected_model == "step-3.5-flash":
            patterns.append("长文档处理可能更适合DeepSeek模型")
        
        # 3. 策略选择问题
        if decision.routing_strategy == "cost_optimized" and outcome.quality == RoutingQuality.FAILED:
            patterns.append("成本优化策略可能牺牲了质量")
        
        # 记录学习到的模式
        if patterns:
            pattern_key = f"{decision.selected_model}_{decision.routing_strategy}_{'_'.join(decision.detected_keywords[:3])}"
            self.learning_patterns[pattern_key] = {
                "patterns": patterns,
                "timestamp": time.time(),
                "occurrences": self.learning_patterns.get(pattern_key, {}).get("occurrences", 0) + 1
            }
            
            logger.info(f"Identified failure patterns: {patterns}")
    
    def get_routing_suggestions(self, request_content: str, available_models: List[str]) -> Dict[str, Any]:
        """基于学习经验获取路由建议
        
        Args:
            request_content: 请求内容
            available_models: 可用模型列表
            
        Returns:
            路由建议
        """
        suggestions = {
            "recommended_model": None,
            "confidence": 0.0,
            "reasoning": "",
            "learned_patterns": []
        }
        
        if not self.learning_patterns:
            return suggestions
        
        # 提取请求特征
        content_lower = request_content.lower()
        content_length = len(request_content)
        keywords = []
        
        # 检测关键词
        keyword_categories = {
            "代码": ["代码", "编程", "算法", "函数", "class", "def ", "import "],
            "文档": ["文档", "总结", "文章", "报告", "分析"],
            "复杂": ["复杂", "推理", "解释", "为什么", "如何"],
            "简单": ["简单", "快速", "基础", "是什么", "定义"]
        }
        
        detected_keywords = []
        for category, words in keyword_categories.items():
            for word in words:
                if word in content_lower:
                    detected_keywords.append(category)
                    break
        
        # 查找匹配的学习模式
        matched_patterns = []
        for pattern_key, pattern_data in self.learning_patterns.items():
            # 简化匹配逻辑
            if any(keyword in pattern_key for keyword in detected_keywords):
                matched_patterns.append({
                    "pattern": pattern_data["patterns"],
                    "occurrences": pattern_data["occurrences"],
                    "recency": time.time() - pattern_data["timestamp"]
                })
        
        if matched_patterns:
            # 选择最相关和最频繁的模式
            matched_patterns.sort(key=lambda x: (x["occurrences"], -x["recency"]), reverse=True)
            best_pattern = matched_patterns[0]
            
            suggestions["learned_patterns"] = best_pattern["pattern"]
            suggestions["confidence"] = min(0.8, best_pattern["occurrences"] * 0.1)
            suggestions["reasoning"] = f"基于{best_pattern['occurrences']}次历史经验"
            
            # 基于模式推荐模型
            patterns_text = " ".join(best_pattern["pattern"])
            if "DeepSeek" in patterns_text and "deepseek" in available_models:
                suggestions["recommended_model"] = "deepseek"
            elif "step-3.5-flash" in patterns_text and "step-3.5-flash" in available_models:
                suggestions["recommended_model"] = "step-3.5-flash"
        
        return suggestions
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        total_decisions = len(self.routing_decisions)
        total_outcomes = len(self.routing_outcomes)
        
        if total_outcomes == 0:
            return {"total_decisions": total_decisions, "total_outcomes": 0}
        
        # 计算总体成功率
        successful_outcomes = sum(1 for o in self.routing_outcomes if o.success)
        success_rate = successful_outcomes / total_outcomes
        
        # 按模型统计
        model_stats = {}
        for model_name, stats in self.model_performance.items():
            model_stats[model_name] = {
                "total_requests": stats["total_requests"],
                "success_rate": stats["successful_requests"] / stats["total_requests"] if stats["total_requests"] > 0 else 0,
                "avg_latency_ms": stats["total_latency_ms"] / stats["successful_requests"] if stats["successful_requests"] > 0 else 0,
                "failure_reasons": stats["failure_reasons"]
            }
        
        return {
            "total_decisions": total_decisions,
            "total_outcomes": total_outcomes,
            "overall_success_rate": success_rate,
            "model_performance": model_stats,
            "learned_patterns_count": len(self.learning_patterns),
            "reflection_history_count": len(self.reflection_history)
        }


# 单例实例
_model_routing_reflection_agent = None


def get_model_routing_reflection_agent() -> ModelRoutingReflectionAgent:
    """获取模型路由反思代理单例实例"""
    global _model_routing_reflection_agent
    
    if _model_routing_reflection_agent is None:
        _model_routing_reflection_agent = ModelRoutingReflectionAgent()
        logger.info("Created singleton instance of ModelRoutingReflectionAgent")
    
    return _model_routing_reflection_agent