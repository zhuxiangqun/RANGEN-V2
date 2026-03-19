#!/usr/bin/env python3
"""
Central Hub API Routes

提供 Central Hub 的 REST API 接口。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter(prefix="/api/v1/hub", tags=["hub"])


class QueryRequest(BaseModel):
    """查询请求"""
    query: str
    context: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """查询响应"""
    success: bool
    intent: Optional[str] = None
    hand: Optional[str] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    alternatives: List[str] = []


class HandsResponse(BaseModel):
    """Hands 列表响应"""
    total: int
    hands: List[Dict[str, str]]


class StatsResponse(BaseModel):
    """统计信息响应"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    hands_loaded: int
    by_intent: Dict[str, Any]
    by_hand: Dict[str, Any]


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    处理用户查询
    
    Args:
        query: 用户查询
        context: 上下文信息
        
    Returns:
        处理结果
    """
    try:
        from src.hands.central_hub import process_query
        
        result = process_query(request.query, request.context)
        
        return QueryResponse(
            success=result.success,
            intent=result.intent,
            hand=result.hand,
            output=result.output,
            error=result.error,
            alternatives=result.alternatives
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hands", response_model=HandsResponse)
async def list_hands():
    """
    列出所有注册的 Hands
    
    Returns:
        Hands 列表
    """
    try:
        from src.hands.central_hub import get_central_hub
        
        hub = get_central_hub()
        hands = hub.list_hands()
        
        return HandsResponse(
            total=len(hands),
            hands=hands
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    获取统计信息
    
    Returns:
        统计信息
    """
    try:
        from src.hands.central_hub import get_central_hub
        
        hub = get_central_hub()
        stats = hub.stats()
        
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload")
async def reload():
    """
    重新加载 Central Hub
    
    Returns:
        重新加载结果
    """
    try:
        from src.hands.central_hub import get_central_hub
        
        hub = get_central_hub()
        hub.reload()
        
        return {"success": True, "message": "重新加载完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
