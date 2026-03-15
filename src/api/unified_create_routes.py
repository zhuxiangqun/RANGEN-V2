"""
Unified Entity Creation API Routes
=================================

API endpoints for unified natural language entity creation.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.unified_creator import get_unified_creator, CreationResult, EntityType

router = APIRouter(prefix="/api/v1/create", tags=["entity-creation"])


class EntityCreateRequest(BaseModel):
    """Request to create an entity from natural language"""
    description: str = Field(..., min_length=3, max_length=2000, 
                              description="Natural language description of what to create")
    entity_type: Optional[str] = Field(None, description="Explicit entity type: agent/skill/team/tool/workflow")
    name: Optional[str] = Field(None, description="Optional name for the entity")
    auto_register: bool = Field(True, description="Whether to auto-register the entity")


class EntityAnalyzeRequest(BaseModel):
    """Request to analyze entity creation intent"""
    description: str = Field(..., min_length=3, max_length=2000,
                              description="Natural language description to analyze")


class EntityCreateResponse(BaseModel):
    """Response for entity creation"""
    success: bool
    entity_type: str
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    message: str
    details: Optional[dict] = None
    error: Optional[str] = None


class IntentAnalysisResponse(BaseModel):
    """Response for intent analysis"""
    entity_type: str
    confidence: float
    description: str
    suggested_name: Optional[str] = None


@router.post("", response_model=EntityCreateResponse)
async def create_entity(request: EntityCreateRequest):
    """
    Create entity from natural language description
    
    Automatically detects entity type (agent/skill/team/tool/workflow) 
    and dispatches to appropriate creator.
    
    Examples:
    - "帮我创建一个数据分析的agent"
    - "创建一个负责天气查询的skill"
    - "创建一个由3个agent组成的团队"
    """
    try:
        creator = get_unified_creator()
        
        result = await creator.create_from_natural_language(
            description=request.description,
            entity_type=request.entity_type,
            name=request.name,
            auto_register=request.auto_register
        )
        
        return EntityCreateResponse(
            success=result.success,
            entity_type=result.entity_type,
            entity_id=result.entity_id,
            entity_name=result.entity_name,
            message=result.message,
            details=result.details,
            error=result.error
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Entity creation failed: {str(e)}"
        )


@router.post("/analyze", response_model=IntentAnalysisResponse)
async def analyze_intent(request: EntityAnalyzeRequest):
    """
    Analyze natural language description to detect entity creation intent
    
    Returns the detected entity type and confidence score.
    """
    try:
        creator = get_unified_creator()
        
        intent = creator.analyze_intent(request.description)
        
        return IntentAnalysisResponse(
            entity_type=intent.entity_type.value,
            confidence=intent.confidence,
            description=intent.description,
            suggested_name=intent.suggested_name
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intent analysis failed: {str(e)}"
        )


@router.get("/supported-types")
async def get_supported_types():
    """Get list of supported entity types for creation"""
    return {
        "entity_types": [
            {"type": "agent", "name": "Agent", "description": "智能代理/助手"},
            {"type": "skill", "name": "Skill", "description": "技能/能力"},
            {"type": "team", "name": "Team", "description": "团队/协作组"},
            {"type": "tool", "name": "Tool", "description": "工具"},
            {"type": "workflow", "name": "Workflow", "description": "工作流/自动化流程"},
        ],
        "examples": [
            "帮我创建一个数据分析的agent",
            "创建一个负责天气查询的skill", 
            "做一个团队，包含数据分析、报表生成的agent",
            "创建一个可以调用外部API的工具",
        ]
    }
