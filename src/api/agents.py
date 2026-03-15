"""
Agent API Routes - REST API for Agent CRUD operations
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from src.api.models_agent import (
    AgentCreate, 
    AgentUpdate, 
    AgentResponse, 
    AgentListResponse
)
from src.services.agent_service import get_agent_service

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(agent: AgentCreate):
    """
    创建新Agent
    """
    service = get_agent_service()
    
    try:
        result = service.create_agent(agent.model_dump())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建Agent失败: {str(e)}"
        )


@router.get("", response_model=AgentListResponse)
async def list_agents(status: Optional[str] = None):
    """
    获取Agent列表
    """
    service = get_agent_service()
    
    try:
        agents = service.list_agents(status)
        return {
            "agents": agents,
            "total": len(agents)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Agent列表失败: {str(e)}"
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """
    获取单个Agent详情
    """
    service = get_agent_service()
    
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent不存在: {agent_id}"
        )
    
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, agent: AgentUpdate):
    """
    更新Agent
    """
    service = get_agent_service()
    
    if not service.check_agent_exists(agent_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent不存在: {agent_id}"
        )
    
    try:
        result = service.update_agent(agent_id, agent.model_dump(exclude_unset=True))
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新Agent失败: {str(e)}"
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str):
    """
    删除Agent
    """
    service = get_agent_service()
    
    if not service.check_agent_exists(agent_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent不存在: {agent_id}"
        )
    
    try:
        service.delete_agent(agent_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除Agent失败: {str(e)}"
        )
