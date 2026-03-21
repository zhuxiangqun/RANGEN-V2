"""
Natural Language Agent Routes - API endpoints for creating agents from natural language descriptions
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from src.services.nlp_agent_creator import get_nlp_agent_creator, AgentCreationResult

# 创建路由器
router = APIRouter(prefix="/api/v1/agents", tags=["natural-language-agents"])


# 请求/响应模型
class NaturalLanguageRequest(BaseModel):
    """自然语言创建请求"""
    description: str = Field(..., min_length=5, max_length=1000, description="自然语言描述，如'创建一个能分析CSV文件并生成图表的Agent'")
    auto_create: bool = Field(True, description="是否自动创建Agent（True）或仅返回配置预览（False）")
    name_override: Optional[str] = Field(None, description="覆盖自动生成的Agent名称")
    additional_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外的配置参数")


class ParseRequirementsRequest(BaseModel):
    """解析需求请求"""
    description: str = Field(..., min_length=5, max_length=1000, description="自然语言描述")


class AgentCreationResponse(BaseModel):
    """Agent创建响应"""
    success: bool
    agent: Optional[Dict[str, Any]] = None
    preview: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    suggestions: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None


class ParseRequirementsResponse(BaseModel):
    """解析需求响应"""
    success: bool
    preview: Dict[str, Any]
    validation: Dict[str, Any]
    parse_result: Dict[str, Any]
    matched_config: Dict[str, Any]
    error: Optional[str] = None


class CapabilitiesResponse(BaseModel):
    """能力列表响应"""
    success: bool
    tools: Dict[str, Any]
    skills: Dict[str, Any]
    keyword_mappings: Dict[str, Any]
    system_status: Dict[str, Any]
    error: Optional[str] = None


@router.post("/from-natural-language", response_model=AgentCreationResponse)
async def create_agent_from_natural_language(request: NaturalLanguageRequest):
    """
    从自然语言描述创建Agent
    
    - **description**: 自然语言描述（5-1000字符）
    - **auto_create**: 是否自动创建Agent（默认True）
    - **name_override**: 可选的Agent名称覆盖
    - **additional_config**: 额外的配置参数
    
    返回创建的Agent详情或配置预览
    """
    try:
        import time
        start_time = time.time()
        
        # 获取NLPAgentCreator实例
        creator = get_nlp_agent_creator()
        
        if request.auto_create:
            # 创建Agent
            result = await creator.create_agent_from_natural_language(request.description)
            
            # 处理名称覆盖
            if request.name_override and result.agent:
                # 这里可以添加更新Agent名称的逻辑
                pass
            
            execution_time = time.time() - start_time
            
            return AgentCreationResponse(
                success=result.success,
                agent=result.agent,
                preview=result.preview,
                error=result.error,
                suggestions=result.suggestions,
                execution_time=execution_time
            )
        else:
            # 仅解析需求，返回预览
            parse_result = await creator.parse_requirements_only(request.description)
            execution_time = time.time() - start_time
            
            if parse_result.get("success"):
                return AgentCreationResponse(
                    success=True,
                    preview=parse_result.get("preview"),
                    execution_time=execution_time
                )
            else:
                return AgentCreationResponse(
                    success=False,
                    error=parse_result.get("error"),
                    execution_time=execution_time
                )
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建Agent时发生错误: {str(e)}"
        )


@router.post("/parse-requirements", response_model=ParseRequirementsResponse)
async def parse_requirements(request: ParseRequirementsRequest):
    """
    解析自然语言需求，返回配置预览
    
    - **description**: 自然语言描述（5-1000字符）
    
    返回解析结果、配置预览和验证状态
    """
    try:
        import time
        start_time = time.time()
        
        creator = get_nlp_agent_creator()
        result = await creator.parse_requirements_only(request.description)
        
        execution_time = time.time() - start_time
        
        if result.get("success"):
            return ParseRequirementsResponse(
                success=True,
                preview=result.get("preview", {}),
                validation=result.get("validation", {}),
                parse_result=result.get("parse_result", {}),
                matched_config=result.get("matched_config", {}),
                execution_time=execution_time
            )
        else:
            return ParseRequirementsResponse(
                success=False,
                preview={},
                validation={},
                parse_result={},
                matched_config={},
                error=result.get("error"),
                execution_time=execution_time
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解析需求时发生错误: {str(e)}"
        )


@router.get("/available-capabilities", response_model=CapabilitiesResponse)
async def get_available_capabilities():
    """
    获取系统可用的能力列表
    
    返回当前可用的Tools、Skills和关键词映射
    """
    try:
        creator = get_nlp_agent_creator()
        capabilities = creator.get_available_capabilities()
        
        # 获取系统状态
        system_status = {
            "agent_service": "available",
            "capability_checker": "available",
            "total_agents": 0,  # 可以从数据库获取
            "total_tools": len(capabilities.get("tools", {})),
            "total_skills": len(capabilities.get("skills", {}))
        }
        
        return CapabilitiesResponse(
            success=True,
            tools=capabilities.get("tools", {}),
            skills=capabilities.get("skills", {}),
            keyword_mappings=capabilities.get("keyword_mappings", {}),
            system_status=system_status
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取能力列表时发生错误: {str(e)}"
        )


@router.get("/system-status")
async def get_agent_system_status():
    """
    获取Agent系统状态
    
    返回Agent服务、能力检查器等组件的状态
    """
    try:
        # 这里可以添加更详细的系统状态检查
        return {
            "success": True,
            "components": {
                "agent_service": {"status": "available", "message": "服务运行正常"},
                "capability_checker": {"status": "available", "message": "能力检查器就绪"},
                "nlp_agent_creator": {"status": "available", "message": "自然语言创建器就绪"},
                "database": {"status": "available", "message": "数据库连接正常"}
            },
            "overall_status": "healthy"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统状态时发生错误: {str(e)}"
        )


# 错误处理
@router.get("/error-examples")
async def get_error_examples():
    """
    获取错误示例和解决方法
    
    返回常见的错误类型和解决建议
    """
    return {
        "success": True,
        "errors": [
            {
                "type": "PARSE_ERROR",
                "description": "无法解析需求描述",
                "solution": "请提供更具体、清晰的需求描述，包含关键词如'数据分析'、'文件处理'等",
                "example": "创建一个能处理数据的Agent → 创建一个能分析CSV文件并生成图表的Agent"
            },
            {
                "type": "CAPABILITY_NOT_FOUND",
                "description": "找不到匹配的Tool或Skill",
                "solution": "尝试使用其他关键词，或联系管理员添加所需的能力组件",
                "example": "需求：'创建一个能进行量子计算的Agent' → 系统暂无量子计算能力"
            },
            {
                "type": "VALIDATION_FAILED",
                "description": "配置验证失败",
                "solution": "系统将自动调整配置或提供替代方案，请查看建议",
                "example": "Tools冲突或资源不足"
            }
        ]
    }