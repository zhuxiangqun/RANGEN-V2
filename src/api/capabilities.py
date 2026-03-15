"""
Capability Check API - Check existing capabilities
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from src.services.capability_checker import get_capability_checker

router = APIRouter(prefix="/api/v1/capabilities", tags=["capabilities"])


class CapabilityCheckRequest(BaseModel):
    """能力检查请求"""
    tools: Optional[List[str]] = Field(default_factory=list)
    skills: Optional[List[str]] = Field(default_factory=list)
    agents: Optional[List[str]] = Field(default_factory=list)


class CheckResultResponse(BaseModel):
    """检查结果响应"""
    satisfied: bool
    missing: List[str]
    available: List[str]
    message: str


class SuggestionResponse(BaseModel):
    """建议响应"""
    agents: List[Dict]
    skills: List[Dict]
    tools: List[Dict]
    message: str


@router.post("/check")
async def check_capabilities(request: CapabilityCheckRequest):
    """
    检查能力是否满足需求
    """
    checker = get_capability_checker()
    
    requirements = {}
    if request.tools:
        requirements['tools'] = request.tools
    if request.skills:
        requirements['skills'] = request.skills
    if request.agents:
        requirements['agents'] = request.agents
    
    if not requirements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请至少提供一种能力类型进行检查"
        )
    
    try:
        results = checker.check_all(requirements)
        
        # 汇总结果
        all_satisfied = all(r.satisfied for r in results.values())
        
        return {
            "overall_satisfied": all_satisfied,
            "details": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"能力检查失败: {str(e)}"
        )


@router.get("/suggest")
async def suggest_capabilities(
    tools: Optional[str] = None,
    skills: Optional[str] = None,
    agents: Optional[str] = None
):
    """
    获取能力组合建议
    """
    checker = get_capability_checker()
    
    requirements = {}
    if tools:
        requirements['tools'] = tools.split(',')
    if skills:
        requirements['skills'] = skills.split(',')
    if agents:
        requirements['agents'] = agents.split(',')
    
    try:
        suggestion = checker.suggest_combination(requirements)
        return suggestion
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取建议失败: {str(e)}"
        )


@router.post("/can-create")
async def can_create_agent(request: CapabilityCheckRequest):
    """
    判断是否可以创建Agent
    """
    checker = get_capability_checker()
    
    try:
        can_create, message = checker.can_create_agent(
            request.tools or [],
            request.skills or []
        )
        
        return {
            "can_create": can_create,
            "message": message
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查失败: {str(e)}"
        )
