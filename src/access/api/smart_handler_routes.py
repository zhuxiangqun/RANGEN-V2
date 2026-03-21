"""
Smart Requirement Handler API Routes
==================================

统一的智能需求处理接口：
1. 分析需求 - 判断是否已有能力
2. 如需创建 - 调用UnifiedCreator
3. 如需执行 - 调用相应Agent
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from src.agents.requirement_analyzer_agent import (
    get_requirement_analyzer,
    RequirementAnalyzerAgent,
    CapabilityMatch
)
from src.agents.ops_diagnosis_agent import get_ops_diagnosis_agent
from src.services.unified_creator import get_unified_creator, EntityType
from src.api.auth import require_read, require_write

router = APIRouter(prefix="/api/v1/smart", tags=["smart-handler"])


class SmartRequest(BaseModel):
    requirement: str
    auto_match: bool = True
    auto_create: bool = False
    execute_after_create: bool = True


class CapabilityInfo(BaseModel):
    type: str
    name: str
    description: str
    id: str
    match_score: float


class AnalysisResult(BaseModel):
    requirement: str
    understood_requirement: str
    capabilities_needed: List[str]
    existing_capabilities: List[CapabilityInfo]
    match_result: str  # exact_match, partial_match, no_match, need_creation
    confidence: float
    recommended_action: str  # execute, create, enhance_or_create
    requires_confirmation: bool
    confirmation_message: str
    suggested_creation: Optional[Dict[str, Any]] = None


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_requirement(
    request: SmartRequest,
    auth_data: dict = Depends(require_read)
):
    """
    智能需求分析接口
    
    输入：
    - requirement: 用户需求描述
    - auto_match: 是否自动匹配现有能力（默认True）
    
    输出：
    - 需求理解结果
    - 现有能力匹配情况
    - 推荐动作（执行/创建）
    - 是否需要确认
    """
    try:
        analyzer = get_requirement_analyzer()
        result = await analyzer.analyze_requirement(
            requirement=request.requirement,
            auto_match=request.auto_match,
            require_confirmation=not request.auto_create
        )
        
        return AnalysisResult(
            requirement=result.requirement,
            understood_requirement=result.understood_requirement,
            capabilities_needed=result.capabilities_needed,
            existing_capabilities=[
                CapabilityInfo(
                    type=c.type,
                    name=c.name,
                    description=c.description,
                    id=c.id,
                    match_score=c.match_score
                ) for c in result.existing_capabilities
            ],
            match_result=result.match_result.value,
            confidence=result.confidence,
            recommended_action=result.recommended_action,
            requires_confirmation=result.requires_confirmation,
            confirmation_message=result.confirmation_message,
            suggested_creation=result.suggested_creation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"需求分析失败: {str(e)}")


class CreateConfirmRequest(BaseModel):
    requirement: str
    entity_type: str  # agent, skill, tool, workflow
    entity_name: Optional[str] = None
    execute_after_create: bool = True


@router.post("/create")
async def create_entity(
    request: CreateConfirmRequest,
    auth_data: dict = Depends(require_write)
):
    """
    根据确认创建实体
    
    输入：
    - requirement: 原始需求
    - entity_type: 要创建的实体类型
    - entity_name: 实体名称
    - execute_after_create: 创建后是否执行
    """
    try:
        creator = get_unified_creator()
        
        entity_type_map = {
            "agent": "agent",
            "skill": "skill",
            "tool": "tool",
            "workflow": "workflow"
        }
        
        mapped_type = entity_type_map.get(request.entity_type, "agent")
        
        result = await creator.create_from_natural_language(
            description=request.requirement,
            entity_type=mapped_type,
            name=request.entity_name
        )
        
        response = {
            "success": result.success,
            "entity_type": result.entity_type,
            "entity_id": result.entity_id,
            "entity_name": result.entity_name,
            "message": result.message,
            "details": result.details,
            "error": result.error
        }
        
        if result.success and request.execute_after_create:
            response["execution_triggered"] = True
            response["execution_message"] = f"实体已创建，现在可以使用了"
        else:
            response["execution_triggered"] = False
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.post("/execute")
async def execute_with_requirement(
    request: SmartRequest,
    auth_data: dict = Depends(require_write)
):
    """
    智能执行接口 - 分析需求并执行
    
    流程：
    1. 分析需求
    2. 如果有匹配能力 → 直接执行
    3. 如果需要创建 → 返回创建建议
    4. 如果 auto_create=True → 自动创建并执行
    """
    try:
        # 1. 分析需求
        analyzer = get_requirement_analyzer()
        analysis = await analyzer.analyze_requirement(
            requirement=request.requirement,
            auto_match=request.auto_match,
            require_confirmation=not request.auto_create
        )
        
        result = {
            "analysis": {
                "requirement": analysis.requirement,
                "understood_requirement": analysis.understood_requirement,
                "match_result": analysis.match_result.value,
                "confidence": analysis.confidence,
                "recommended_action": analysis.recommended_action
            },
            "execution": None,
            "creation": None
        }
        
        # 2. 根据分析结果执行
        if analysis.match_result == CapabilityMatch.EXACT_MATCH:
            # 精确匹配 → 执行运维诊断
            ops = get_ops_diagnosis_agent()
            exec_result = await ops.execute(
                inputs={"query": analysis.requirement},
                context={"auto_fix": True}
            )
            
            result["execution"] = {
                "success": exec_result.status.value == "success",
                "agent": exec_result.agent_name,
                "output": exec_result.output,
                "error": exec_result.error
            }
            
        elif analysis.match_result == CapabilityMatch.PARTIAL_MATCH:
            # 部分匹配 → 返回建议
            result["suggestion"] = {
                "message": analysis.confirmation_message,
                "matched_capabilities": [
                    {"name": c.name, "type": c.type, "score": c.match_score}
                    for c in analysis.existing_capabilities[:3]
                ]
            }
            
        else:  # NO_MATCH or NEED_CREATION
            # 需要创建
            if request.auto_create and analysis.suggested_creation:
                # 自动创建
                creator = get_unified_creator()
                entity_type = analysis.suggested_creation.get("type", "agent")
                
                create_result = await creator.create_from_natural_language(
                    description=request.requirement,
                    entity_type=entity_type,
                    name=request.entity_name or analysis.suggested_creation.get("name")
                )
                
                result["creation"] = {
                    "success": create_result.success,
                    "entity_type": create_result.entity_type,
                    "entity_id": create_result.entity_id,
                    "entity_name": create_result.entity_name,
                    "error": create_result.error
                }
                
                if create_result.success:
                    result["execution"] = {
                        "success": True,
                        "message": f"已创建并可以使用 {entity_type}: {create_result.entity_name}"
                    }
            else:
                # 需要确认
                result["confirmation_required"] = True
                result["suggestion"] = {
                    "message": analysis.confirmation_message,
                    "suggested_creation": analysis.suggested_creation
                }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能执行失败: {str(e)}")


@router.get("/capabilities")
async def list_capabilities(
    auth_data: dict = Depends(require_read)
):
    """
    列出所有可用能力（Agent/Skill/Tool）
    """
    try:
        analyzer = get_requirement_analyzer()
        caps = await analyzer._get_all_capabilities()
        
        return {
            "capabilities": [
                {
                    "type": c.type,
                    "name": c.name,
                    "description": c.description,
                    "id": c.id
                }
                for c in caps
            ],
            "total": len(caps)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
