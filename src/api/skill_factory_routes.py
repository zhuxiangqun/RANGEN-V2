"""
Skill Factory API Routes - REST API for Skill Factory operations

提供 Skill Factory 的功能接口：
1. 创建新技能（通过工厂）
2. 分析需求并分类原型
3. 运行质量检查
4. 获取工厂统计信息
5. 获取可用原型列表
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.api.auth import require_admin
from src.agents.skills.skill_factory_integration import (
    get_factory_integration, 
    is_skill_factory_available,
    SkillFactoryIntegration
)

router = APIRouter(prefix="/api/v1/skill-factory", tags=["skill-factory"])


# 数据模型
class SkillRequirements(BaseModel):
    """技能需求模型"""
    name: str = Field(..., description="技能名称")
    description: str = Field(..., description="技能详细描述")
    use_cases: List[str] = Field(default_factory=list, description="使用场景")
    target_users: List[str] = Field(default_factory=list, description="目标用户")
    complexity: str = Field("medium", description="复杂度: low/medium/high")
    tools_needed: List[str] = Field(default_factory=list, description="需要的工具")
    integration_points: List[str] = Field(default_factory=list, description="集成点")


class RequirementsAnalysisRequest(BaseModel):
    """需求分析请求模型"""
    requirements_text: str = Field(..., description="需求描述文本")
    detailed: bool = Field(False, description="是否返回详细分析")


class SkillCreateRequest(BaseModel):
    """技能创建请求模型"""
    requirements: SkillRequirements = Field(..., description="技能需求")
    prototype_type: Optional[str] = Field(None, description="指定原型类型（可选）")
    skip_quality_check: bool = Field(False, description="跳过质量检查")


class QualityCheckRequest(BaseModel):
    """质量检查请求模型"""
    skill_dir: str = Field(..., description="技能目录路径")


class SkillCreationResponse(BaseModel):
    """技能创建响应模型"""
    success: bool
    skill_name: str
    prototype_type: Optional[str] = None
    skill_dir: Optional[str] = None
    error: Optional[str] = None
    quality_report: Optional[Dict[str, Any]] = None
    factory_result: Optional[Dict[str, Any]] = None


class RequirementsAnalysisResponse(BaseModel):
    """需求分析响应模型"""
    success: bool
    recommended_prototype: Optional[str] = None
    confidence: Optional[float] = None
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class PrototypeInfo(BaseModel):
    """原型信息模型"""
    id: str
    name: str
    description: str
    use_cases: List[str]


class PrototypesResponse(BaseModel):
    """原型列表响应模型"""
    success: bool
    prototypes: List[PrototypeInfo]
    error: Optional[str] = None


class QualityCheckResponse(BaseModel):
    """质量检查响应模型"""
    success: bool
    passed: Optional[bool] = None
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FactoryStatistics(BaseModel):
    """工厂统计信息模型"""
    total_generated: int
    generated_skills: List[str]
    total_registered: int
    registered_skills: List[str]
    factory_available: bool


class StatisticsResponse(BaseModel):
    """统计信息响应模型"""
    success: bool
    statistics: Optional[FactoryStatistics] = None
    error: Optional[str] = None


class FactoryStatusResponse(BaseModel):
    """工厂状态响应模型"""
    available: bool
    message: str


# 依赖项
def get_factory() -> SkillFactoryIntegration:
    """获取 Skill Factory 集成服务"""
    if not is_skill_factory_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Skill Factory is not available. Please check installation."
        )
    
    try:
        return get_factory_integration()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize Skill Factory: {str(e)}"
        )


# API 路由
@router.get("/status", response_model=FactoryStatusResponse)
async def get_factory_status():
    """
    获取 Skill Factory 状态
    
    检查 Skill Factory 是否可用
    """
    available = is_skill_factory_available()
    
    return FactoryStatusResponse(
        available=available,
        message="Skill Factory is available" if available else "Skill Factory is not available"
    )


@router.get("/prototypes", response_model=PrototypesResponse)
async def get_prototypes(factory: SkillFactoryIntegration = Depends(get_factory)):
    """
    获取可用技能原型列表
    
    返回所有可用的技能原型及其描述
    """
    try:
        prototypes = factory.get_available_prototypes()
        
        return PrototypesResponse(
            success=True,
            prototypes=[
                PrototypeInfo(
                    id=proto["id"],
                    name=proto["name"],
                    description=proto["description"],
                    use_cases=proto["use_cases"]
                )
                for proto in prototypes
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prototypes: {str(e)}"
        )


@router.post("/analyze", response_model=RequirementsAnalysisResponse)
async def analyze_requirements(
    request: RequirementsAnalysisRequest,
    factory: SkillFactoryIntegration = Depends(get_factory)
):
    """
    分析技能需求并推荐原型
    
    根据需求描述文本分析并推荐最适合的技能原型
    """
    try:
        result = factory.analyze_and_classify_requirements(request.requirements_text)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Analysis failed")
            )
        
        return RequirementsAnalysisResponse(
            success=True,
            recommended_prototype=result.get("recommended_prototype"),
            confidence=result.get("confidence"),
            analysis=result.get("analysis")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze requirements: {str(e)}"
        )


@router.post("/create", response_model=SkillCreationResponse)
async def create_skill(
    request: SkillCreateRequest,
    factory: SkillFactoryIntegration = Depends(get_factory)
):
    """
    创建新技能
    
    使用 Skill Factory 创建新技能并自动注册到系统
    需要管理员权限
    """
    try:
        # 准备需求数据
        requirements_dict = {
            "name": request.requirements.name,
            "description": request.requirements.description,
            "use_cases": request.requirements.use_cases,
            "target_users": request.requirements.target_users,
            "complexity": request.requirements.complexity,
            "tools_needed": request.requirements.tools_needed,
            "integration_points": request.requirements.integration_points
        }
        
        # 如果指定了原型类型，添加到需求中
        if request.prototype_type:
            requirements_dict["preferred_prototype"] = request.prototype_type
        
        # 创建技能
        result = factory.create_and_register_skill(
            requirements_dict,
            request.requirements.name
        )
        
        # 如果请求跳过质量检查，移除质量报告
        if request.skip_quality_check and "quality_report" in result:
            result["quality_report"] = None
        
        return SkillCreationResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill: {str(e)}"
        )


@router.post("/quality-check", response_model=QualityCheckResponse)
async def run_quality_check(
    request: QualityCheckRequest,
    factory: SkillFactoryIntegration = Depends(get_factory)
):
    """
    运行技能质量检查
    
    对指定技能目录运行质量检查
    """
    try:
        result = factory.run_quality_check(request.skill_dir)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Quality check failed")
            )
        
        return QualityCheckResponse(
            success=True,
            passed=result.get("passed"),
            report=result.get("report")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run quality check: {str(e)}"
        )


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(factory: SkillFactoryIntegration = Depends(get_factory)):
    """
    获取工厂统计信息
    
    返回 Skill Factory 的统计数据
    """
    try:
        result = factory.get_statistics()
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to get statistics")
            )
        
        stats = result.get("statistics", {})
        
        return StatisticsResponse(
            success=True,
            statistics=FactoryStatistics(
                total_generated=stats.get("total_generated", 0),
                generated_skills=stats.get("generated_skills", []),
                total_registered=stats.get("total_registered", 0),
                registered_skills=stats.get("registered_skills", []),
                factory_available=stats.get("factory_available", False)
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/quick-create", response_model=SkillCreationResponse)
async def quick_create_skill(
    name: str,
    description: str,
    factory: SkillFactoryIntegration = Depends(get_factory)
):
    """
    快速创建技能（简化接口）
    
    使用简化的参数快速创建技能
    需要管理员权限
    """
    try:
        requirements = {
            "name": name,
            "description": description,
            "use_cases": ["general"],
            "target_users": ["all"],
            "complexity": "medium",
            "tools_needed": [],
            "integration_points": []
        }
        
        result = factory.create_and_register_skill(requirements, name)
        
        return SkillCreationResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to quick create skill: {str(e)}"
        )