"""
Skill Data Models - Pydantic models for Skill CRUD API
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SkillCreate(BaseModel):
    """创建Skill请求模型"""
    name: str = Field(..., description="Skill名称")
    description: Optional[str] = Field(None, description="Skill描述")
    tools: List[str] = Field(default_factory=list, description="包含的Tool ID列表")
    source: Optional[str] = Field(None, description="Skill来源")
    priority: Optional[int] = Field(100, description="Skill优先级")
    config_path: Optional[str] = Field(None, description="配置文件路径")


class SkillResponse(BaseModel):
    """Skill响应模型"""
    id: str
    name: str
    description: Optional[str]
    tools: List[str]
    source: Optional[str] = None
    priority: Optional[int] = 100
    status: str
    created_at: datetime
    reference_count: int = 0


class SkillListResponse(BaseModel):
    """Skill列表响应模型"""
    skills: List[SkillResponse]
    total: int
