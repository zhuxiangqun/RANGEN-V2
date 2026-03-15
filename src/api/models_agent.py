"""
Agent Data Models - Pydantic models for Agent CRUD API
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class AgentCreate(BaseModel):
    """创建Agent请求模型"""
    name: str = Field(..., description="Agent名称")
    description: Optional[str] = Field(None, description="Agent描述")
    type: str = Field(default="agent", description="Agent类型")
    skills: List[str] = Field(default_factory=list, description="关联的Skill ID列表")
    tools: List[str] = Field(default_factory=list, description="关联的Tool ID列表")
    config: Dict[str, Any] = Field(default_factory=dict, description="Agent配置")


class AgentUpdate(BaseModel):
    """更新Agent请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    skills: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent响应模型"""
    id: str
    name: str
    type: str
    description: Optional[str]
    skills: List[str]
    tools: List[str]
    status: str
    created_at: datetime
    updated_at: datetime
    reference_count: int = 0


class AgentListResponse(BaseModel):
    """Agent列表响应模型"""
    agents: List[AgentResponse]
    total: int
