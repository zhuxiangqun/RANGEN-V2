"""
Team 执行 API 路由

允许用户使用自动创建的 Team 来执行任务
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio


router = APIRouter(prefix="/api/v1/team", tags=["team"])


class TeamExecuteRequest(BaseModel):
    team_id: str
    task: str
    context: Optional[Dict[str, Any]] = None


class TeamExecuteResponse(BaseModel):
    success: bool
    team_id: str
    team_name: str
    task: str
    result: Any
    steps: List[Dict[str, Any]]
    error: Optional[str] = None


@router.post("/execute", response_model=TeamExecuteResponse)
async def execute_team(request: TeamExecuteRequest):
    """
    使用 Team 执行任务
    
    用户提供:
    - team_id: Team ID
    - task: 任务描述
    - context: 可选的上下文
    
    返回:
    - 执行结果
    - 执行步骤
    """
    from src.core.team_executor import TeamExecutor, TeamExecutionRequest, get_team_executor
    
    executor = get_team_executor()
    
    team = executor.get_team(request.team_id)
    if not team:
        raise HTTPException(status_code=404, detail=f"Team not found: {request.team_id}")
    
    exec_request = TeamExecutionRequest(
        team_id=request.team_id,
        task=request.task,
        context=request.context or {}
    )
    
    result = await executor.execute(exec_request)
    
    return TeamExecuteResponse(
        success=result.success,
        team_id=result.team_id,
        team_name=team.get("name", ""),
        task=result.task,
        result=result.result,
        steps=result.steps,
        error=result.error
    )


@router.get("/list")
async def list_teams():
    """
    列出所有可用的 Team
    """
    from src.core.team_executor import get_team_executor
    
    executor = get_team_executor()
    teams = executor.list_teams()
    
    return {
        "teams": teams,
        "count": len(teams)
    }


@router.get("/{team_id}")
async def get_team(team_id: str):
    """
    获取指定 Team 的详细信息
    """
    from src.core.team_executor import get_team_executor
    
    executor = get_team_executor()
    team = executor.get_team(team_id)
    
    if not team:
        raise HTTPException(status_code=404, detail=f"Team not found: {team_id}")
    
    return team
