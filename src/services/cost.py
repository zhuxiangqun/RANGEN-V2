"""
统一成本控制服务模块

合并以下服务:
- CostController (cost_control.py)
- DeepSeekCostController (deepseek_cost_controller.py)
- TokenCostMonitor (token_cost_monitor.py)
- CostAlertService (cost_alert.py)

使用示例:
```python
from src.services.cost import CostService

cost_service = CostService()
usage = cost_service.track_usage("gpt-4", 1000)
alerts = cost_service.check_budget()
```
"""

import time
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field


# ============== Enums ==============

class LLMProvider(str, Enum):
    """LLM提供商"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class CostAlertLevel(str, Enum):
    """成本告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============== Data Classes ==============

@dataclass
class TokenUsage:
    """Token使用量"""
    provider: LLMProvider
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    timestamp: float


@dataclass
class CostRecord:
    """成本记录"""
    provider: LLMProvider
    model: str
    input_cost: float
    output_cost: float
    total_cost: float
    tokens: int
    timestamp: float


@dataclass
class BudgetLimit:
    """预算限制"""
    daily_limit: float
    monthly_limit: float
    alert_threshold: float  # 百分比 (0.0 - 1.0)


@dataclass
class CostAlert:
    """成本告警"""
    level: CostAlertLevel
    message: str
    current_spend: float
    limit: float
    timestamp: float


# ============== Pricing (per 1M tokens) ==============

PRICING = {
    LLMProvider.DEEPSEEK: {
        "deepseek-chat": {"input": 0.14, "output": 0.28},
        "deepseek-coder": {"input": 0.14, "output": 0.28},
    },
    LLMProvider.OPENAI: {
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    },
    LLMProvider.ANTHROPIC: {
        "claude-3-opus": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    },
}


# ============== Main Class ==============

class CostService:
    """
    统一成本控制服务
    
    提供:
    - Token使用跟踪 (Token Tracking)
    - 成本计算 (Cost Calculation)
    - 预算管理 (Budget Management)
    - 告警 (Alerts)
    """
    
    def __init__(self):
        self._usage_history: List[TokenUsage] = []
        self._cost_history: List[CostRecord] = []
        self._alerts: List[CostAlert] = []
        self._budgets: Dict[str, BudgetLimit] = {}
        self._daily_spend: Dict[str, float] = {}
        self._monthly_spend: Dict[str, float] = {}
        
        self._max_history = 10000
        self._day_start = time.time()
        self._month_start = time.time()
    
    # ============== Token Tracking ==============
    
    def track_usage(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> TokenUsage:
        """跟踪Token使用"""
        provider_enum = LLMProvider(provider) if provider in [p.value for p in LLMProvider] else LLMProvider.LOCAL
        
        usage = TokenUsage(
            provider=provider_enum,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            timestamp=time.time()
        )
        
        self._usage_history.append(usage)
        
        # Calculate and record cost
        cost = self._calculate_cost(usage)
        self._cost_history.append(cost)
        
        # Update spending
        self._update_spending(provider, cost.total_cost)
        
        # Check budget
        self._check_budget_alerts(provider)
        
        # Trim history
        self._trim_history()
        
        return usage
    
    def _calculate_cost(self, usage: TokenUsage) -> CostRecord:
        """计算成本"""
        # Get pricing
        provider_pricing = PRICING.get(usage.provider, {})
        model_pricing = provider_pricing.get(usage.model, {"input": 1.0, "output": 1.0})
        
        input_cost = (usage.prompt_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (usage.completion_tokens / 1_000_000) * model_pricing["output"]
        
        return CostRecord(
            provider=usage.provider,
            model=usage.model,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
            tokens=usage.total_tokens,
            timestamp=usage.timestamp
        )
    
    def _update_spending(self, provider: str, cost: float) -> None:
        """更新支出"""
        if provider not in self._daily_spend:
            self._daily_spend[provider] = 0.0
        if provider not in self._monthly_spend:
            self._monthly_spend[provider] = 0.0
        
        self._daily_spend[provider] += cost
        self._monthly_spend[provider] += cost
    
    def _check_budget_alerts(self, provider: str) -> None:
        """检查预算告警"""
        budget = self._budgets.get(provider)
        if not budget:
            return
        
        daily = self._daily_spend.get(provider, 0)
        monthly = self._monthly_spend.get(provider, 0)
        
        # Daily alerts
        if daily >= budget.daily_limit:
            self._alerts.append(CostAlert(
                level=CostAlertLevel.CRITICAL,
                message=f"Daily budget exceeded for {provider}",
                current_spend=daily,
                limit=budget.daily_limit,
                timestamp=time.time()
            ))
        elif daily >= budget.daily_limit * budget.alert_threshold:
            self._alerts.append(CostAlert(
                level=CostAlertLevel.WARNING,
                message=f"Approaching daily budget limit for {provider}",
                current_spend=daily,
                limit=budget.daily_limit,
                timestamp=time.time()
            ))
        
        # Monthly alerts
        if monthly >= budget.monthly_limit:
            self._alerts.append(CostAlert(
                level=CostAlertLevel.CRITICAL,
                message=f"Monthly budget exceeded for {provider}",
                current_spend=monthly,
                limit=budget.monthly_limit,
                timestamp=time.time()
            ))
    
    def _trim_history(self) -> None:
        """修剪历史"""
        if len(self._usage_history) > self._max_history:
            self._usage_history = self._usage_history[-self._max_history:]
        if len(self._cost_history) > self._max_history:
            self._cost_history = self._cost_history[-self._max_history:]
    
    # ============== Budget Management ==============
    
    def set_budget(
        self,
        provider: str,
        daily_limit: float,
        monthly_limit: float,
        alert_threshold: float = 0.8
    ) -> None:
        """设置预算"""
        self._budgets[provider] = BudgetLimit(
            daily_limit=daily_limit,
            monthly_limit=monthly_limit,
            alert_threshold=alert_threshold
        )
    
    def get_budget_status(self, provider: str) -> Dict[str, Any]:
        """获取预算状态"""
        daily = self._daily_spend.get(provider, 0)
        monthly = self._monthly_spend.get(provider, 0)
        budget = self._budgets.get(provider)
        
        if not budget:
            return {
                "provider": provider,
                "budget_set": False,
                "daily": {"spent": daily},
                "monthly": {"spent": monthly}
            }
        
        return {
            "provider": provider,
            "budget_set": True,
            "daily": {
                "spent": daily,
                "limit": budget.daily_limit,
                "percent": (daily / budget.daily_limit) * 100 if budget.daily_limit > 0 else 0
            },
            "monthly": {
                "spent": monthly,
                "limit": budget.monthly_limit,
                "percent": (monthly / budget.monthly_limit) * 100 if budget.monthly_limit > 0 else 0
            }
        }
    
    # ============== Queries ==============
    
    def get_usage_summary(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取使用摘要"""
        usage_list = self._usage_history
        
        if provider:
            usage_list = [u for u in usage_list if u.provider.value == provider]
        if model:
            usage_list = [u for u in usage_list if u.model == model]
        
        if not usage_list:
            return {"count": 0}
        
        total_prompt = sum(u.prompt_tokens for u in usage_list)
        total_completion = sum(u.completion_tokens for u in usage_list)
        
        return {
            "count": len(usage_list),
            "total_tokens": total_prompt + total_completion,
            "prompt_tokens": total_prompt,
            "completion_tokens": total_completion,
            "avg_tokens_per_request": (total_prompt + total_completion) / len(usage_list)
        }
    
    def get_cost_summary(
        self,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取成本摘要"""
        cost_list = self._cost_history
        
        if provider:
            cost_list = [c for c in cost_list if c.provider.value == provider]
        
        if not cost_list:
            return {"total_cost": 0}
        
        total = sum(c.total_cost for c in cost_list)
        
        by_model: Dict[str, float] = {}
        for c in cost_list:
            key = f"{c.provider.value}:{c.model}"
            by_model[key] = by_model.get(key, 0) + c.total_cost
        
        return {
            "total_cost": total,
            "input_cost": sum(c.input_cost for c in cost_list),
            "output_cost": sum(c.output_cost for c in cost_list),
            "by_model": by_model,
            "request_count": len(cost_list)
        }
    
    def get_alerts(self, limit: int = 50) -> List[CostAlert]:
        """获取告警列表"""
        return self._alerts[-limit:]


# ============== Factory ==============

def get_cost_service() -> CostService:
    """获取成本服务实例"""
    return CostService()
