"""
Team API Routes - REST API for Team collaboration
"""
import asyncio
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from src.services.team_service import get_team_service, CollaborationMode

router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


class TeamMemberRequest(BaseModel):
    """团队成员请求"""
    agent_id: str
    role: str
    input_from: Optional[List[str]] = None


class TeamCreateRequest(BaseModel):
    """创建团队请求"""
    name: str = Field(..., description="团队名称")
    description: str = Field(..., description="团队描述")
    agent_ids: List[str] = Field(..., description="成员Agent ID列表")
    mode: str = Field(default="sequential", description="协作模式: sequential/parallel/hierarchical")
    role_assignments: Optional[dict] = Field(default=None, description="角色分配")


class TeamResponse(BaseModel):
    """团队响应"""
    id: str
    name: str
    description: str
    mode: str
    members: List[dict]
    status: str
    created_at: datetime


class TeamListResponse(BaseModel):
    """团队列表响应"""
    teams: List[TeamResponse]
    total: int


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(request: TeamCreateRequest):
    """
    创建新团队
    """
    service = get_team_service()
    
    try:
        team = service.create_team(
            name=request.name,
            description=request.description,
            agent_ids=request.agent_ids,
            mode=request.mode,
            role_assignments=request.role_assignments
        )
        return team
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建团队失败: {str(e)}"
        )


@router.get("", response_model=TeamListResponse)
async def list_teams(status: Optional[str] = None):
    """
    获取团队列表
    """
    service = get_team_service()
    
    try:
        teams = service.list_teams(status)
        return {
            "teams": teams,
            "total": len(teams)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取团队列表失败: {str(e)}"
        )


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(team_id: str):
    """
    获取团队详情
    """
    service = get_team_service()
    
    team = service.get_team(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"团队不存在: {team_id}"
        )
    
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(team_id: str):
    """
    删除团队
    """
    service = get_team_service()
    
    if not service.get_team(team_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"团队不存在: {team_id}"
        )
    
    try:
        service.delete_team(team_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除团队失败: {str(e)}"
        )


@router.get("/suggest")
async def suggest_team(requirement: str):
    """
    根据需求建议团队配置
    """
    service = get_team_service()
    
    try:
        suggestion = service.suggest_team_from_requirement(requirement)
        return suggestion
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取建议失败: {str(e)}"
        )


@router.post("/execute/{team_id}")
async def execute_team_task(team_id: str, query: str):
    """
    执行团队任务
    """
    service = get_team_service()
    
    team = service.get_team(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"团队不存在: {team_id}"
        )
    
    # 模拟团队执行
    results = []
    
    for i, member in enumerate(team['members']):
        # 模拟每个Agent的执行
        result = {
            'member': member,
            'output': f"Agent [{member['agent_id']}] 处理结果 {i+1}",
            'status': 'completed'
        }
        results.append(result)
        
        # 模拟执行延迟
        await asyncio.sleep(0.1)
    
    return {
        'team_id': team_id,
        'query': query,
        'status': 'completed',
        'members_count': len(team['members']),
        'results': results
    }
