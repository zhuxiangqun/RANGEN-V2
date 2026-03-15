"""
Cost Control Service - Token counting, fee calculation, cost dashboard
"""
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class LLMProvider(str, Enum):
    """LLM提供商"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


# 定价模型 (每1M token的价格，单位：美元)
PRICING_PER_MILLION = {
    LLMProvider.DEEPSEEK: {
        "input": 0.1,   # $0.1/M
        "output": 0.3,  # $0.3/M
    },
    LLMProvider.OPENAI: {
        "input": 2.5,   # GPT-4 (不再使用，保留作参考)
        "output": 10.0,
        "active": False,  # 标记为不活跃
    },
    LLMProvider.ANTHROPIC: {
        "input": 3.0,   # Claude (不再使用，保留作参考)
        "output": 15.0,
        "active": False,  # 标记为不活跃
    },
    LLMProvider.MOCK: {
        "input": 0.0,
        "output": 0.0,
    },
}


@dataclass
class TokenUsage:
    """Token使用记录"""
    execution_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class CostRecord:
    """费用记录"""
    execution_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    timestamp: datetime = field(default_factory=datetime.now)


class CostController:
    """成本控制器 - Token统计和费用计算"""
    
    def __init__(self):
        self._token_usage: List[TokenUsage] = []
        self._cost_records: List[CostRecord] = []
        self._current_provider = LLMProvider.DEEPSEEK
        self._current_model = "deepseek-chat"
    
    def set_provider(self, provider: str, model: str = None):
        """设置当前LLM提供商"""
        try:
            self._current_provider = LLMProvider(provider.lower())
        except ValueError:
            self._current_provider = LLMProvider.MOCK
        
        self._current_model = model or "default"
        logger.info(f"Provider set to: {self._current_provider.value}")
    
    def get_pricing(self, provider: str = None) -> Dict[str, float]:
        """获取定价信息"""
        p = provider or self._current_provider.value
        try:
            return PRICING_PER_MILLION[LLMProvider(p.lower())]
        except (ValueError, KeyError):
            return {"input": 0.0, "output": 0.0}
    
    def record_tokens(
        self,
        execution_id: str,
        input_tokens: int,
        output_tokens: int,
        provider: str = None,
        model: str = None
    ) -> CostRecord:
        """记录Token使用并计算费用"""
        provider = provider or self._current_provider.value
        model = model or self._current_model
        
        # 记录Token使用
        usage = TokenUsage(
            execution_id=execution_id,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        self._token_usage.append(usage)
        
        # 计算费用
        pricing = self.get_pricing(provider)
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        # 记录费用
        record = CostRecord(
            execution_id=execution_id,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost
        )
        self._cost_records.append(record)
        
        logger.info(f"Token usage recorded: {execution_id}, "
                   f"tokens={usage.total_tokens}, cost=${total_cost:.4f}")
        
        return record
    
    def get_execution_cost(self, execution_id: str) -> Optional[CostRecord]:
        """获取单个执行的费用"""
        for record in self._cost_records:
            if record.execution_id == execution_id:
                return record
        return None
    
    def get_total_cost(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """获取总费用统计"""
        records = self._cost_records
        
        if since:
            records = [r for r in records if r.timestamp >= since]
        
        total_input = sum(r.input_tokens for r in records)
        total_output = sum(r.output_tokens for r in records)
        total_cost = sum(r.total_cost for r in records)
        
        return {
            "total_requests": len(records),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost": total_cost,
            "currency": "USD"
        }
    
    def get_cost_by_period(self, days: int = 7) -> Dict[str, Any]:
        """获取指定时间段内的费用统计"""
        since = datetime.now() - timedelta(days=days)
        
        records = [r for r in self._cost_records if r.timestamp >= since]
        
        # 按天分组
        daily_costs: Dict[str, float] = {}
        for record in records:
            day = record.timestamp.strftime("%Y-%m-%d")
            daily_costs[day] = daily_costs.get(day, 0.0) + record.total_cost
        
        return {
            "period_days": days,
            "total_cost": sum(r.total_cost for r in records),
            "total_requests": len(records),
            "daily_costs": daily_costs,
            "currency": "USD"
        }
    
    def get_cost_breakdown(self) -> Dict[str, Any]:
        """获取费用明细"""
        # 按provider分组
        provider_costs: Dict[str, Dict] = {}
        
        for record in self._cost_records:
            key = f"{record.provider}/{record.model}"
            if key not in provider_costs:
                provider_costs[key] = {
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0
                }
            
            provider_costs[key]["requests"] += 1
            provider_costs[key]["input_tokens"] += record.input_tokens
            provider_costs[key]["output_tokens"] += record.output_tokens
            provider_costs[key]["cost"] += record.total_cost
        
        return {
            "by_provider": provider_costs,
            "total": self.get_total_cost()
        }
    
    def get_usage_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取使用历史"""
        recent = sorted(self._token_usage, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [
            {
                "execution_id": u.execution_id,
                "provider": u.provider,
                "model": u.model,
                "input_tokens": u.input_tokens,
                "output_tokens": u.output_tokens,
                "total_tokens": u.total_tokens,
                "timestamp": u.timestamp.isoformat()
            }
            for u in recent
        ]
    
    def set_budget_threshold(self, daily_limit: float, warning_threshold: float = 0.8):
        """设置预算阈值"""
        self._daily_budget = daily_limit
        self._warning_threshold = warning_threshold
    
    def check_budget(self) -> Dict[str, Any]:
        """检查预算使用情况"""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_cost = self.get_cost_by_period(days=1)
        
        if hasattr(self, '_daily_budget'):
            daily_total = daily_cost.get('total_cost', 0)
            percentage = (daily_total / self._daily_budget) * 100
            
            return {
                "daily_budget": self._daily_budget,
                "daily_spent": daily_total,
                "percentage": percentage,
                "warning": percentage >= (self._warning_threshold * 100),
                "exceeded": daily_total > self._daily_budget
            }
        
        return {"daily_spent": daily_cost.get('total_cost', 0)}


# Global instance
_cost_controller: Optional[CostController] = None


def get_cost_controller() -> CostController:
    """获取成本控制器实例"""
    global _cost_controller
    if _cost_controller is None:
        _cost_controller = CostController()
    return _cost_controller
