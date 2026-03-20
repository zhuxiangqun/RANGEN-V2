"""
设计工作流 API 路由
===================

提供设计优先工作流的 API 接口。

端点:
- POST /api/v1/design/check - 检查是否需要设计
- POST /api/v1/design/generate - 生成设计
- POST /api/v1/design/approve - 批准设计
- POST /api/v1/design/reject - 拒绝设计
- GET /api/v1/design/status - 获取设计状态
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

router = APIRouter(prefix="/api/v1/design", tags=["design"])


# ============ 请求模型 ============

class DesignCheckRequest(BaseModel):
    """检查是否需要设计"""
    description: str = Field(..., description="实体描述")
    entity_type: str = Field(..., description="实体类型: agent/skill/tool")


class DesignGenerateRequest(BaseModel):
    """生成设计请求"""
    description: str = Field(..., description="实体描述")
    entity_type: str = Field(..., description="实体类型: agent/skill/tool")
    requirements: Optional[Dict[str, Any]] = Field(None, description="额外需求")


class DesignApproveRequest(BaseModel):
    """批准设计请求"""
    design_id: str = Field(..., description="设计ID")
    approved_by: str = Field("api", description="批准者")


class DesignRejectRequest(BaseModel):
    """拒绝设计请求"""
    design_id: str = Field(..., description="设计ID")
    reason: str = Field(..., description="拒绝原因")


# ============ 响应模型 ============

class DesignCheckResponse(BaseModel):
    """设计检查响应"""
    success: bool
    design_required: str  # not_required, required, existing_ok
    entity_type: str
    message: str
    details: Optional[Dict[str, Any]] = None


class DesignGenerateResponse(BaseModel):
    """设计生成响应"""
    success: bool
    design_id: Optional[str] = None
    message: str
    status: str  # pending_approval, approved, rejected
    design_summary: Optional[Dict[str, Any]] = None
    review_result: Optional[Dict[str, Any]] = None
    requirements: Optional[str] = None


class DesignApproveResponse(BaseModel):
    """设计批准响应"""
    success: bool
    design_id: str
    message: str
    can_create: bool = True


class DesignStatusResponse(BaseModel):
    """设计状态响应"""
    success: bool
    status: str  # idle, brainstorming, design_review, design_approved, implementing, completed
    can_write_code: bool
    message: str
    design: Optional[Dict[str, Any]] = None


# ============ API 端点 ============

@router.post("/check", response_model=DesignCheckResponse)
async def check_design_required(request: DesignCheckRequest):
    """
    检查是否需要设计
    
    在创建实体前调用此接口，检查是否需要先完成设计。
    """
    try:
        from src.services.hard_gate_integration import get_hard_gate_integration
        
        integration = get_hard_gate_integration()
        result = await integration.check_design_required(
            description=request.description,
            entity_type=request.entity_type
        )
        
        return DesignCheckResponse(
            success=True,
            design_required=result.design_required.value,
            entity_type=result.entity_type or request.entity_type,
            message=result.message,
            details=result.details
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")


@router.post("/generate", response_model=DesignGenerateResponse)
async def generate_design(request: DesignGenerateRequest):
    """
    生成设计
    
    执行完整的设计工作流：
    1. 需求发现
    2. AI 设计生成
    3. 提交到 HARD-GATE
    4. 组件设计审查
    """
    try:
        from src.services.hard_gate_integration import get_hard_gate_integration
        
        integration = get_hard_gate_integration()
        
        # 检查是否需要设计
        design_check = await integration.check_design_required(
            description=request.description,
            entity_type=request.entity_type
        )
        
        if design_check.design_required.value == "not_required":
            return DesignGenerateResponse(
                success=True,
                design_id=None,
                message="此类型不需要设计，可直接创建",
                status="skipped"
            )
        
        # 执行设计工作流
        result = await integration.execute_design_workflow(
            description=request.description,
            entity_type=request.entity_type,
            requirements=request.requirements
        )
        
        if not result.get("success"):
            return DesignGenerateResponse(
                success=False,
                message=result.get("message", "设计生成失败"),
                status="failed"
            )
        
        # 提取设计摘要
        design = result.get("design")
        design_summary = None
        if design:
            design_summary = {
                "title": getattr(design, 'title', 'Untitled'),
                "overview": getattr(design, 'overview', ''),
                "components": [
                    {
                        "name": c.name,
                        "description": c.description
                    }
                    for c in getattr(design, 'components', [])
                ],
                "file_structure": getattr(design, 'file_structure', [])
            }
        
        return DesignGenerateResponse(
            success=True,
            design_id=result.get("design_id"),
            message=result.get("message", "设计已生成"),
            status=result.get("status", "pending_approval"),
            design_summary=design_summary,
            review_result=_format_review_result(result.get("review_result")),
            requirements=result.get("requirements")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设计生成失败: {str(e)}")


@router.post("/approve", response_model=DesignApproveResponse)
async def approve_design(request: DesignApproveRequest):
    """
    批准设计
    
    批准后可以开始实现。
    """
    try:
        from src.services.hard_gate_integration import get_hard_gate_integration
        
        integration = get_hard_gate_integration()
        result = await integration.approve_design(
            design_id=request.design_id,
            approved_by=request.approved_by
        )
        
        return DesignApproveResponse(
            success=result.get("success", False),
            design_id=request.design_id,
            message=result.get("message", "批准操作完成"),
            can_create=result.get("success", False)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批准失败: {str(e)}")


@router.post("/reject", response_model=Dict[str, Any])
async def reject_design(request: DesignRejectRequest):
    """
    拒绝设计
    
    拒绝后需要重新生成或修改需求。
    """
    try:
        from src.agents.hard_gate import HARD_GATE
        
        gate = HARD_GATE()
        success = gate.reject_design(reason=request.reason)
        
        return {
            "success": success,
            "design_id": request.design_id,
            "message": "设计已拒绝" if success else "拒绝失败"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"拒绝失败: {str(e)}")


@router.get("/status", response_model=DesignStatusResponse)
async def get_design_status():
    """
    获取设计状态
    
    返回当前 HARD-GATE 状态和是否可以编写代码。
    """
    try:
        from src.services.hard_gate_integration import get_hard_gate_integration
        
        integration = get_hard_gate_integration()
        can_write, reason = integration.can_write_code()
        
        from src.agents.hard_gate import HARD_GATE
        gate = HARD_GATE()
        status = gate.get_status()
        
        design_data = status.get("design")
        design_dict = None
        if design_data:
            design_dict = {
                "title": getattr(design_data, 'title', 'Untitled'),
                "approved": getattr(design_data, 'approved', False),
                "created_at": getattr(design_data, 'created_at', None)
            }
        
        return DesignStatusResponse(
            success=True,
            status=status.get("phase", "unknown"),
            can_write_code=can_write,
            message=reason,
            design=design_dict
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"状态查询失败: {str(e)}")


@router.post("/reset", response_model=Dict[str, Any])
async def reset_hard_gate():
    """
    重置 HARD-GATE
    
    将 HARD-GATE 重置到初始状态。
    """
    try:
        from src.agents.hard_gate import HARD_GATE
        
        gate = HARD_GATE()
        gate.reset()
        
        return {
            "success": True,
            "message": "HARD-GATE 已重置"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")


def _format_review_result(review_result) -> Optional[Dict[str, Any]]:
    """格式化审查结果"""
    if not review_result:
        return None
    
    return {
        "is_approved": getattr(review_result, 'is_approved', None),
        "component_type": getattr(review_result, 'component_type', None),
        "dimension_scores": getattr(review_result, 'dimension_scores', {}),
        "issue_count": len(getattr(review_result, 'issues', [])),
        "blocker_count": len(getattr(review_result, 'blockers', []))
    }
