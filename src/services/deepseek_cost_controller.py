#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek成本精细化控制器 - 专为DeepSeek-only策略设计

核心功能：
1. 预算控制：月度预算、单次调用预算、预算警告阈值
2. 使用分析：按模型、时间段、用户等维度分析DeepSeek使用情况
3. 成本优化：智能路由到最具成本效益的DeepSeek模型
4. 实时监控：与状态管理器集成，实时更新成本状态
5. 预算强制执行：确保外部LLM只使用DeepSeek，并控制在预算内

设计原则：
- 主动防御：在调用前检查预算，防止超支
- 精细控制：按模型、用户、项目等多维度控制
- 实时反馈：实时更新成本状态，支持决策优化
- 向后兼容：与现有CostController API兼容
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import threading

from src.services.cost_control import (
    CostController, 
    LLMProvider, 
    CostRecord, 
    TokenUsage
)
from src.core.rangen_state import (
    get_global_state_manager,
    StateUpdate,
    StateUpdateStrategy
)

logger = logging.getLogger(__name__)


class BudgetType(Enum):
    """预算类型"""
    MONTHLY = "monthly"          # 月度预算
    PER_PROJECT = "per_project"  # 按项目预算
    PER_USER = "per_user"        # 按用户预算
    PER_MODEL = "per_model"      # 按模型预算
    CUSTOM = "custom"            # 自定义预算


@dataclass
class BudgetLimit:
    """预算限制"""
    budget_type: BudgetType
    limit_amount: float               # 限制金额（美元）
    warning_threshold: float = 0.8    # 警告阈值（百分比）
    period_days: int = 30             # 周期天数（用于月度预算）
    start_date: datetime = field(default_factory=datetime.now)
    
    @property
    def warning_amount(self) -> float:
        """警告金额"""
        return self.limit_amount * self.warning_threshold
    
    def is_within_period(self, date: datetime) -> bool:
        """检查日期是否在预算周期内"""
        if self.budget_type == BudgetType.MONTHLY:
            end_date = self.start_date + timedelta(days=self.period_days)
            return self.start_date <= date <= end_date
        return True  # 其他类型假设始终在周期内


@dataclass
class DeepSeekModelCost:
    """DeepSeek模型成本配置"""
    model_name: str
    input_cost_per_million: float    # 输入token成本（美元/百万token）
    output_cost_per_million: float   # 输出token成本（美元/百万token）
    reasoning_tokens_multiplier: float = 1.0  # 推理token乘数（用于reasoner模型）
    max_tokens_per_call: int = 128000         # 单次调用最大token数
    recommended_for: List[str] = field(default_factory=list)  # 推荐使用场景
    
    @property
    def is_reasoner_model(self) -> bool:
        """是否为推理模型"""
        return "reasoner" in self.model_name.lower()


# DeepSeek模型成本配置（2025年定价）
DEEPSEEK_MODEL_COSTS = {
    "deepseek-reasoner": DeepSeekModelCost(
        model_name="deepseek-reasoner",
        input_cost_per_million=2.5,    # $2.5 / 1M tokens (输入)
        output_cost_per_million=10.0,  # $10.0 / 1M tokens (输出)
        reasoning_tokens_multiplier=2.0,  # 推理token消耗更高
        max_tokens_per_call=128000,
        recommended_for=["complex_reasoning", "planning", "analysis"]
    ),
    "deepseek-chat": DeepSeekModelCost(
        model_name="deepseek-chat",
        input_cost_per_million=0.8,    # $0.8 / 1M tokens (输入)
        output_cost_per_million=3.2,   # $3.2 / 1M tokens (输出)
        max_tokens_per_call=128000,
        recommended_for=["general_chat", "code_generation", "summarization"]
    ),
    "deepseek-coder": DeepSeekModelCost(
        model_name="deepseek-coder",
        input_cost_per_million=1.2,    # $1.2 / 1M tokens (输入)
        output_cost_per_million=4.8,   # $4.8 / 1M tokens (输出)
        max_tokens_per_call=128000,
        recommended_for=["code_completion", "code_review", "refactoring"]
    ),
}


class DeepSeekCostController(CostController):
    """DeepSeek成本精细化控制器"""
    
    def __init__(self, default_monthly_budget: float = 1000.0):
        """
        初始化DeepSeek成本控制器
        
        Args:
            default_monthly_budget: 默认月度预算（美元）
        """
        super().__init__()
        
        # 强制使用DeepSeek作为提供商
        self._current_provider = LLMProvider.DEEPSEEK
        self._current_model = "deepseek-reasoner"
        
        # 预算配置
        self.default_monthly_budget = default_monthly_budget
        self.budget_limits: List[BudgetLimit] = [
            BudgetLimit(
                budget_type=BudgetType.MONTHLY,
                limit_amount=default_monthly_budget,
                warning_threshold=0.8,
                period_days=30
            )
        ]
        
        # 使用记录（增强版）
        self.deepseek_usage_records: List[Dict[str, Any]] = []
        
        # 状态管理器集成
        self.state_manager = get_global_state_manager()
        
        # 线程安全
        self._lock = threading.RLock()
        
        logger.info(f"DeepSeek成本控制器初始化，默认月度预算：${default_monthly_budget}")
    
    def set_provider(self, provider: str, model: str = None):
        """
        设置LLM提供商（强制为DeepSeek）
        
        注意：根据系统策略，外部LLM只使用DeepSeek
        """
        provider_lower = provider.lower()
        
        # 检查是否为本地模型（允许本地模型）
        is_local_model = "local" in provider_lower
        
        if provider_lower != "deepseek" and not is_local_model:
            logger.warning(f"⚠️ 尝试设置非DeepSeek提供商 '{provider}'，强制重定向到DeepSeek")
            provider = "deepseek"
        
        if provider == "deepseek":
            # 验证DeepSeek模型
            if model and model not in DEEPSEEK_MODEL_COSTS:
                logger.warning(f"未知DeepSeek模型 '{model}'，使用默认 'deepseek-reasoner'")
                model = "deepseek-reasoner"
            
            super().set_provider("deepseek", model)
            
            # 更新状态管理器
            self.state_manager.update_state({
                "llm_provider": "deepseek",
                "llm_model": model or "deepseek-reasoner"
            })
        else:
            # 本地模型
            super().set_provider(provider, model)
            
            # 更新状态管理器（标记为本地模型）
            self.state_manager.update_state({
                "llm_provider": provider,
                "llm_model": model or "local",
                "warnings": [f"使用本地模型: {provider}/{model}"]
            })
    
    def record_tokens(
        self,
        execution_id: str,
        input_tokens: int,
        output_tokens: int,
        provider: str = None,
        model: str = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> CostRecord:
        """
        记录Token使用并计算费用（增强版）
        
        Args:
            execution_id: 执行ID
            input_tokens: 输入token数
            output_tokens: 输出token数
            provider: 提供商（强制为DeepSeek）
            model: 模型名称
            user_id: 用户ID（用于按用户预算）
            project_id: 项目ID（用于按项目预算）
            task_type: 任务类型
            
        Returns:
            费用记录
        """
        with self._lock:
            # 强制使用DeepSeek（除非是本地模型）
            if provider and provider.lower() != "deepseek" and "local" not in provider.lower():
                logger.warning(f"⚠️ 非DeepSeek提供商 '{provider}'，强制重定向到DeepSeek")
                provider = "deepseek"
            
            # 获取实际使用的模型
            actual_model = model or self._current_model
            actual_provider = provider or "deepseek"
            
            # 检查预算
            estimated_cost = self._estimate_cost(
                actual_provider, actual_model, input_tokens, output_tokens
            )
            
            budget_check = self.check_budget(
                estimated_cost, 
                user_id=user_id, 
                project_id=project_id
            )
            
            if not budget_check["allowed"]:
                raise BudgetExceededError(
                    f"预算超支：{budget_check['message']} "
                    f"（预估成本：${estimated_cost:.4f}）"
                )
            
            # 调用父类方法记录token
            record = super().record_tokens(
                execution_id=execution_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                provider=actual_provider,
                model=actual_model
            )
            
            # 记录增强的使用信息
            usage_record = {
                "execution_id": execution_id,
                "provider": actual_provider,
                "model": actual_model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_cost": record.total_cost,
                "user_id": user_id,
                "project_id": project_id,
                "task_type": task_type,
                "timestamp": datetime.now(),
                "budget_check": budget_check
            }
            self.deepseek_usage_records.append(usage_record)
            
            # 更新状态管理器
            self._update_state_with_cost(record, usage_record)
            
            # 记录详细日志
            logger.info(
                f"DeepSeek使用记录：{execution_id}, "
                f"模型={actual_model}, "
                f"tokens={input_tokens}+{output_tokens}, "
                f"成本=${record.total_cost:.4f}, "
                f"用户={user_id or 'N/A'}, "
                f"项目={project_id or 'N/A'}"
            )
            
            return record
    
    def check_budget(
        self, 
        estimated_cost: float,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        检查预算是否允许调用
        
        Args:
            estimated_cost: 预估成本（美元）
            user_id: 用户ID（用于按用户预算）
            project_id: 项目ID（用于按项目预算）
            
        Returns:
            检查结果
        """
        with self._lock:
            # 获取相关预算限制
            relevant_budgets = self._get_relevant_budgets(user_id, project_id)
            
            # 获取当前周期内的总成本
            current_total = self.get_total_cost_since_period_start()
            total_with_estimate = current_total["total_cost"] + estimated_cost
            
            # 检查每个相关预算
            for budget in relevant_budgets:
                if total_with_estimate > budget.limit_amount:
                    return {
                        "allowed": False,
                        "message": f"总成本 ${total_with_estimate:.2f} 超过预算限制 ${budget.limit_amount:.2f}",
                        "budget_type": budget.budget_type.value,
                        "current_cost": current_total["total_cost"],
                        "estimated_cost": estimated_cost
                    }
                
                # 检查警告阈值
                if total_with_estimate > budget.warning_amount:
                    logger.warning(
                        f"⚠️ 成本接近预算限制：${total_with_estimate:.2f} / "
                        f"${budget.limit_amount:.2f} ({budget.budget_type.value})"
                    )
            
            return {
                "allowed": True,
                "message": "预算检查通过",
                "current_cost": current_total["total_cost"],
                "estimated_cost": estimated_cost
            }
    
    def get_total_cost_since_period_start(self) -> Dict[str, Any]:
        """获取当前预算周期内的总成本"""
        with self._lock:
            # 获取当前活跃的月度预算
            monthly_budgets = [
                b for b in self.budget_limits 
                if b.budget_type == BudgetType.MONTHLY and b.is_within_period(datetime.now())
            ]
            
            if not monthly_budgets:
                # 如果没有活跃的月度预算，使用默认30天周期
                since = datetime.now() - timedelta(days=30)
            else:
                # 使用最新的月度预算开始日期
                since = max(b.start_date for b in monthly_budgets)
            
            # 获取该时间段内的记录
            records = [r for r in self._cost_records if r.timestamp >= since]
            
            # 按提供商和模型分组
            cost_by_provider = {}
            cost_by_model = {}
            
            for record in records:
                # 按提供商
                provider = record.provider
                cost_by_provider[provider] = cost_by_provider.get(provider, 0.0) + record.total_cost
                
                # 按模型（仅DeepSeek）
                if provider == "deepseek":
                    model = record.model
                    cost_by_model[model] = cost_by_model.get(model, 0.0) + record.total_cost
            
            total_input = sum(r.input_tokens for r in records)
            total_output = sum(r.output_tokens for r in records)
            total_cost = sum(r.total_cost for r in records)
            
            return {
                "period_start": since,
                "total_requests": len(records),
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_tokens": total_input + total_output,
                "total_cost": total_cost,
                "cost_by_provider": cost_by_provider,
                "cost_by_model": cost_by_model,
                "currency": "USD"
            }
    
    def get_deepseek_usage_analysis(
        self, 
        days: int = 30,
        group_by: str = "model"  # model, user, project, task_type
    ) -> Dict[str, Any]:
        """
        获取DeepSeek使用分析
        
        Args:
            days: 分析天数
            group_by: 分组维度
            
        Returns:
            使用分析报告
        """
        with self._lock:
            since = datetime.now() - timedelta(days=days)
            
            # 过滤DeepSeek使用记录
            deepseek_records = [
                r for r in self.deepseek_usage_records 
                if r.get("provider") == "deepseek" and r["timestamp"] >= since
            ]
            
            if not deepseek_records:
                return {
                    "period_days": days,
                    "total_requests": 0,
                    "total_cost": 0.0,
                    "grouped_data": {},
                    "recommendations": []
                }
            
            # 按指定维度分组
            grouped = {}
            for record in deepseek_records:
                key = record.get(group_by, "unknown")
                if key not in grouped:
                    grouped[key] = {
                        "requests": 0,
                        "total_tokens": 0,
                        "total_cost": 0.0,
                        "avg_cost_per_request": 0.0
                    }
                
                grouped[key]["requests"] += 1
                grouped[key]["total_tokens"] += record["input_tokens"] + record["output_tokens"]
                grouped[key]["total_cost"] += record["total_cost"]
            
            # 计算平均值
            for key in grouped:
                if grouped[key]["requests"] > 0:
                    grouped[key]["avg_cost_per_request"] = (
                        grouped[key]["total_cost"] / grouped[key]["requests"]
                    )
            
            # 生成优化建议
            recommendations = self._generate_cost_optimization_recommendations(deepseek_records)
            
            total_cost = sum(record["total_cost"] for record in deepseek_records)
            total_requests = len(deepseek_records)
            
            return {
                "period_days": days,
                "total_requests": total_requests,
                "total_cost": total_cost,
                "avg_cost_per_request": total_cost / total_requests if total_requests > 0 else 0.0,
                "grouped_data": grouped,
                "recommendations": recommendations
            }
    
    def recommend_model_for_task(
        self, 
        task_type: str, 
        estimated_input_tokens: int,
        estimated_output_tokens: int,
        budget_constraint: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        为任务推荐最合适的DeepSeek模型
        
        Args:
            task_type: 任务类型
            estimated_input_tokens: 预估输入token数
            estimated_output_tokens: 预估输出token数
            budget_constraint: 预算约束（美元）
            
        Returns:
            模型推荐
        """
        recommendations = []
        
        for model_name, model_config in DEEPSEEK_MODEL_COSTS.items():
            # 计算预估成本
            estimated_cost = self._estimate_cost(
                "deepseek", model_name, estimated_input_tokens, estimated_output_tokens
            )
            
            # 检查预算约束
            if budget_constraint is not None and estimated_cost > budget_constraint:
                continue
            
            # 计算适用性分数
            suitability_score = self._calculate_model_suitability(
                model_config, task_type, estimated_input_tokens, estimated_output_tokens
            )
            
            recommendations.append({
                "model": model_name,
                "estimated_cost": estimated_cost,
                "suitability_score": suitability_score,
                "recommended_for": model_config.recommended_for,
                "cost_per_million_input": model_config.input_cost_per_million,
                "cost_per_million_output": model_config.output_cost_per_million,
                "max_tokens": model_config.max_tokens_per_call
            })
        
        # 按适用性分数排序
        recommendations.sort(key=lambda x: x["suitability_score"], reverse=True)
        
        if not recommendations:
            # 如果没有符合预算的模型，返回成本最低的模型
            cheapest = min(
                DEEPSEEK_MODEL_COSTS.items(),
                key=lambda x: x[1].input_cost_per_million + x[1].output_cost_per_million
            )
            estimated_cost = self._estimate_cost(
                "deepseek", cheapest[0], estimated_input_tokens, estimated_output_tokens
            )
            
            return {
                "model": cheapest[0],
                "estimated_cost": estimated_cost,
                "suitability_score": 0.5,
                "warning": f"没有符合预算约束的模型，使用成本最低的模型",
                "budget_constraint": budget_constraint
            }
        
        return {
            "recommendations": recommendations,
            "best_model": recommendations[0]["model"],
            "best_model_cost": recommendations[0]["estimated_cost"],
            "best_model_score": recommendations[0]["suitability_score"]
        }
    
    def add_budget_limit(self, budget_limit: BudgetLimit):
        """添加预算限制"""
        with self._lock:
            self.budget_limits.append(budget_limit)
            logger.info(f"添加预算限制：{budget_limit.budget_type.value} ${budget_limit.limit_amount}")
    
    def _estimate_cost(
        self, 
        provider: str, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> float:
        """预估成本"""
        if provider != "deepseek":
            return 0.0  # 本地模型成本为0
        
        if model not in DEEPSEEK_MODEL_COSTS:
            model = "deepseek-reasoner"  # 默认模型
        
        model_config = DEEPSEEK_MODEL_COSTS[model]
        
        # 计算成本
        input_cost = (input_tokens / 1_000_000) * model_config.input_cost_per_million
        output_cost = (output_tokens / 1_000_000) * model_config.output_cost_per_million
        
        # 如果是推理模型，应用乘数
        if model_config.is_reasoner_model:
            output_cost *= model_config.reasoning_tokens_multiplier
        
        return input_cost + output_cost
    
    def _get_relevant_budgets(
        self, 
        user_id: Optional[str] = None, 
        project_id: Optional[str] = None
    ) -> List[BudgetLimit]:
        """获取相关预算限制"""
        relevant = []
        
        for budget in self.budget_limits:
            # 检查预算是否在周期内
            if not budget.is_within_period(datetime.now()):
                continue
            
            # 通用预算（月度、自定义）
            if budget.budget_type in [BudgetType.MONTHLY, BudgetType.CUSTOM]:
                relevant.append(budget)
            
            # 按用户预算
            elif budget.budget_type == BudgetType.PER_USER and user_id:
                # 这里需要实现用户关联逻辑
                relevant.append(budget)
            
            # 按项目预算
            elif budget.budget_type == BudgetType.PER_PROJECT and project_id:
                # 这里需要实现项目关联逻辑
                relevant.append(budget)
        
        return relevant
    
    def _update_state_with_cost(self, cost_record: CostRecord, usage_record: Dict[str, Any]):
        """更新状态管理器中的成本信息"""
        updates = {
            "total_cost": cost_record.total_cost,
            "deepseek_usage": [usage_record]
        }
        
        # 更新成本细分
        cost_breakdown = self.state_manager.get_state().get("cost_breakdown", {})
        model_key = f"deepseek:{cost_record.model}"
        cost_breakdown[model_key] = cost_breakdown.get(model_key, 0.0) + cost_record.total_cost
        
        updates["cost_breakdown"] = cost_breakdown
        
        # 更新预算剩余
        budget_remaining = self.default_monthly_budget - self.get_total_cost_since_period_start()["total_cost"]
        updates["budget_remaining"] = max(0.0, budget_remaining)
        
        self.state_manager.update_state(updates)
    
    def _calculate_model_suitability(
        self, 
        model_config: DeepSeekModelCost, 
        task_type: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算模型适用性分数"""
        score = 0.5  # 基础分数
        
        # 任务类型匹配度
        if task_type in model_config.recommended_for:
            score += 0.3
        
        # Token限制检查
        total_tokens = input_tokens + output_tokens
        if total_tokens <= model_config.max_tokens_per_call:
            score += 0.1
        else:
            score -= 0.2
        
        # 成本效率（成本越低分数越高）
        avg_cost = (model_config.input_cost_per_million + model_config.output_cost_per_million) / 2
        if avg_cost < 2.0:  # 低成本模型
            score += 0.1
        elif avg_cost > 5.0:  # 高成本模型
            score -= 0.1
        
        return min(1.0, max(0.0, score))  # 限制在0-1之间
    
    def _generate_cost_optimization_recommendations(
        self, 
        usage_records: List[Dict[str, Any]]
    ) -> List[str]:
        """生成成本优化建议"""
        recommendations = []
        
        # 按模型分析
        model_usage = {}
        for record in usage_records:
            model = record.get("model", "unknown")
            if model not in model_usage:
                model_usage[model] = {"cost": 0.0, "count": 0}
            model_usage[model]["cost"] += record["total_cost"]
            model_usage[model]["count"] += 1
        
        # 检查是否有高成本模型使用
        for model, usage in model_usage.items():
            if usage["cost"] > 100.0:  # 单模型花费超过$100
                # 检查是否有更经济的替代模型
                if model == "deepseek-reasoner":
                    recommendations.append(
                        f"考虑对非推理任务使用 deepseek-chat 替代 deepseek-reasoner，"
                        f"可节省约70%成本（当前花费：${usage['cost']:.2f}）"
                    )
        
        # 检查大token使用
        high_token_records = [
            r for r in usage_records 
            if (r["input_tokens"] + r["output_tokens"]) > 100000
        ]
        if high_token_records:
            recommendations.append(
                f"检测到 {len(high_token_records)} 次大token使用（>100k tokens），"
                f"考虑优化上下文长度或使用上下文压缩"
            )
        
        return recommendations


class BudgetExceededError(Exception):
    """预算超支异常"""
    pass


# 全局DeepSeek成本控制器实例
_global_deepseek_cost_controller: Optional[DeepSeekCostController] = None


def get_global_deepseek_cost_controller() -> DeepSeekCostController:
    """获取全局DeepSeek成本控制器（单例）"""
    global _global_deepseek_cost_controller
    if _global_deepseek_cost_controller is None:
        _global_deepseek_cost_controller = DeepSeekCostController()
    return _global_deepseek_cost_controller


# 集成到现有LLM集成模块的辅助函数
def integrate_with_llm_integration():
    """
    将DeepSeek成本控制器集成到现有LLM集成模块
    
    使用示例：
    1. 在llm_integration.py中导入：from src.services.deepseek_cost_controller import get_global_deepseek_cost_controller
    2. 在调用DeepSeek前检查预算
    3. 记录实际使用的token
    """
    controller = get_global_deepseek_cost_controller()
    
    # 示例：检查预算
    estimated_tokens = 1000  # 预估token数
    estimated_cost = controller._estimate_cost("deepseek", "deepseek-reasoner", estimated_tokens, 500)
    
    budget_check = controller.check_budget(estimated_cost)
    if not budget_check["allowed"]:
        raise BudgetExceededError(budget_check["message"])
    
    return controller


if __name__ == "__main__":
    # 示例用法
    controller = DeepSeekCostController(default_monthly_budget=500.0)
    
    # 记录使用
    try:
        record = controller.record_tokens(
            execution_id="test_123",
            input_tokens=1500,
            output_tokens=500,
            provider="deepseek",
            model="deepseek-reasoner",
            user_id="user_001",
            project_id="project_alpha",
            task_type="complex_reasoning"
        )
        print(f"记录成本：${record.total_cost:.4f}")
        
        # 获取分析报告
        analysis = controller.get_deepseek_usage_analysis(days=7, group_by="model")
        print(f"7天使用分析：{analysis}")
        
        # 获取模型推荐
        recommendation = controller.recommend_model_for_task(
            task_type="code_generation",
            estimated_input_tokens=2000,
            estimated_output_tokens=1000,
            budget_constraint=0.05  # $0.05预算限制
        )
        print(f"模型推荐：{recommendation}")
        
    except BudgetExceededError as e:
        print(f"预算超支：{e}")