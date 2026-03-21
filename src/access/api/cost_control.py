"""
Cost Control API - Token counting, fee calculation endpoints
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from src.services.cost_control import get_cost_controller, LLMProvider, PRICING_PER_MILLION

router = APIRouter(prefix="/api/v1/cost", tags=["cost-control"])


class TokenRecordRequest(BaseModel):
    """Token记录请求"""
    execution_id: str
    input_tokens: int
    output_tokens: int
    provider: Optional[str] = None
    model: Optional[str] = None


class CostResponse(BaseModel):
    """费用响应"""
    execution_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float


class CostStatsResponse(BaseModel):
    """费用统计响应"""
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost: float
    currency: str


@router.get("/providers")
async def get_providers():
    """获取支持的LLM提供商及定价"""
    providers = []
    
    for provider, pricing in PRICING_PER_MILLION.items():
        providers.append({
            "name": provider.value,
            "pricing": {
                "input_per_million": pricing["input"],
                "output_per_million": pricing["output"]
            }
        })
    
    return {"providers": providers}


@router.get("/current-provider")
async def get_current_provider():
    """获取当前配置的LLM提供商"""
    controller = get_cost_controller()
    
    return {
        "provider": controller._current_provider.value,
        "model": controller._current_model,
        "pricing": controller.get_pricing()
    }


@router.post("/set-provider")
async def set_provider(provider: str, model: str = None):
    """设置LLM提供商"""
    controller = get_cost_controller()
    controller.set_provider(provider, model)
    
    return {
        "provider": provider,
        "model": model,
        "pricing": controller.get_pricing(provider)
    }


@router.post("/record")
async def record_tokens(request: TokenRecordRequest):
    """记录Token使用并计算费用"""
    controller = get_cost_controller()
    
    record = controller.record_tokens(
        execution_id=request.execution_id,
        input_tokens=request.input_tokens,
        output_tokens=request.output_tokens,
        provider=request.provider,
        model=request.model
    )
    
    return CostResponse(
        execution_id=record.execution_id,
        provider=record.provider,
        model=record.model,
        input_tokens=record.input_tokens,
        output_tokens=record.output_tokens,
        input_cost=record.input_cost,
        output_cost=record.output_cost,
        total_cost=record.total_cost
    )


@router.get("/execution/{execution_id}")
async def get_execution_cost(execution_id: str):
    """获取单个执行的费用"""
    controller = get_cost_controller()
    
    record = controller.get_execution_cost(execution_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cost record found for execution: {execution_id}"
        )
    
    return CostResponse(
        execution_id=record.execution_id,
        provider=record.provider,
        model=record.model,
        input_tokens=record.input_tokens,
        output_tokens=record.output_tokens,
        input_cost=record.input_cost,
        output_cost=record.output_cost,
        total_cost=record.total_cost
    )


@router.get("/total")
async def get_total_cost(days: Optional[int] = None):
    """获取总费用统计"""
    controller = get_cost_controller()
    
    since = None
    if days:
        since = datetime.now() - timedelta(days=days)
    
    stats = controller.get_total_cost(since)
    
    return CostStatsResponse(**stats)


@router.get("/period/{days}")
async def get_period_cost(days: int):
    """获取指定时间段内的费用"""
    controller = get_cost_controller()
    
    stats = controller.get_cost_by_period(days)
    
    return stats


@router.get("/breakdown")
async def get_cost_breakdown():
    """获取费用明细"""
    controller = get_cost_controller()
    
    return controller.get_cost_breakdown()


@router.get("/history")
async def get_usage_history(limit: int = 10):
    """获取使用历史"""
    controller = get_cost_controller()
    
    history = controller.get_usage_history(limit)
    
    return {"history": history}


@router.get("/budget")
async def check_budget():
    """检查预算使用情况"""
    controller = get_cost_controller()
    
    return controller.check_budget()


@router.post("/budget/set")
async def set_budget(daily_limit: float, warning_threshold: float = 0.8):
    """设置预算阈值"""
    controller = get_cost_controller()
    
    controller.set_budget_threshold(daily_limit, warning_threshold)
    
    return {
        "daily_limit": daily_limit,
        "warning_threshold": warning_threshold,
        "message": "Budget threshold set successfully"
    }
