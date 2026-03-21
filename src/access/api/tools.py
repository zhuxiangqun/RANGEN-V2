"""
Tool API Routes - REST API for Tool operations
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from src.services.database import get_database
from src.services.logging_service import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


class ToolResponse(BaseModel):
    """Tool响应模型"""
    id: str
    name: str
    description: Optional[str]
    type: Optional[str]
    source: Optional[str] = None
    priority: Optional[int] = 100
    status: str
    created_at: datetime


class ToolListResponse(BaseModel):
    """Tool列表响应模型"""
    tools: List[ToolResponse]
    total: int


@router.get("", response_model=ToolListResponse)
async def list_tools(status: Optional[str] = None):
    """
    获取Tool列表
    """
    db = get_database()
    
    try:
        tools = db.get_all_tools(status)
        return {
            "tools": tools,
            "total": len(tools)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Tool列表失败: {str(e)}"
        )


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(tool_id: str):
    """
    获取单个Tool详情
    """
    db = get_database()
    
    tool = db.get_tool(tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool不存在: {tool_id}"
        )
    
    return tool


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    name: str,
    description: Optional[str] = None,
    tool_type: Optional[str] = None,
    source: Optional[str] = None,
    priority: Optional[int] = 100
):
    """
    创建新Tool
    """
    import uuid
    db = get_database()
    
    tool_id = f"tool_{uuid.uuid4().hex[:12]}"
    
    try:
        tool = db.create_tool({
            'id': tool_id,
            'name': name,
            'description': description,
            'type': tool_type,
            'source': source,
            'priority': priority,
            'status': 'active'
        })
        return tool
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建Tool失败: {str(e)}"
        )


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(tool_id: str):
    """
    删除Tool
    """
    db = get_database()
    
    if not db.get_tool(tool_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool不存在: {tool_id}"
        )
    
    try:
        db.delete_tool(tool_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除Tool失败: {str(e)}"
        )
