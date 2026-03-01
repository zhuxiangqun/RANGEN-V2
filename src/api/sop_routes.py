#!/usr/bin/env python3
"""
SOP管理API模块
提供SOP的RESTful管理接口
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from src.core.sop_learning import get_sop_learning_system, SOPLevel, SOPCategory

# 创建路由
router = APIRouter(prefix="/sops", tags=["SOP Management"])


# ===== 请求/响应模型 =====
class SOPCreateRequest(BaseModel):
    """创建SOP请求"""
    name: str
    description: str
    category: str
    level: str = "l3_task"
    steps: List[Dict[str, Any]]
    tags: List[str] = []


class SOPUpdateRequest(BaseModel):
    """更新SOP请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class SOPRecallRequest(BaseModel):
    """SOP召回请求"""
    task_description: str
    context: Optional[Dict[str, Any]] = None
    max_results: int = 5


# ===== API端点 =====
@router.get("")
async def list_sops(
    level: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """列出所有SOP
    
    Args:
        level: 按层级过滤 (l0_meta, l2_global, l3_task)
        category: 按类别过滤
        limit: 返回数量限制
        
    Returns:
        SOP列表和统计信息
    """
    sop_system = get_sop_learning_system()
    
    # 解析过滤条件
    sop_level = SOPLevel(level) if level else None
    sop_category = SOPCategory(category) if category else None
    
    # 获取SOP
    sops = sop_system.get_all_sops(level=sop_level, category=sop_category)
    
    # 限制返回数量
    sops = sops[:limit]
    
    # 获取统计信息
    stats = sop_system.get_statistics()
    
    return {
        "success": True,
        "count": len(sops),
        "sops": [sop["summary"] for sop in sops],
        "statistics": stats
    }


@router.get("/{sop_id}")
async def get_sop(sop_id: str) -> Dict[str, Any]:
    """获取指定SOP详情
    
    Args:
        sop_id: SOP ID
        
    Returns:
        SOP详细信息
    """
    sop_system = get_sop_learning_system()
    sop = sop_system.get_sop(sop_id)
    
    if not sop:
        raise HTTPException(status_code=404, detail=f"SOP not found: {sop_id}")
    
    # 获取质量分析
    quality = sop_system.analyze_sop_quality(sop_id)
    
    return {
        "success": True,
        "sop": sop.to_dict(),
        "quality": quality
    }


@router.post("")
async def create_sop(request: SOPCreateRequest) -> Dict[str, Any]:
    """创建新SOP
    
    Args:
        request: 创建请求
        
    Returns:
        创建的SOP信息
    """
    from src.core.sop_learning import StandardOperatingProcedure, SOPStep
    
    sop_system = get_sop_learning_system()
    
    try:
        # 解析层级和类别
        level = SOPLevel(request.level)
        category = SOPCategory(request.category)
        
        # 创建步骤
        steps = []
        for i, step_data in enumerate(request.steps):
            step = SOPStep(
                step_id=step_data.get("step_id", f"step_{i+1}"),
                hand_name=step_data.get("hand_name", ""),
                parameters=step_data.get("parameters", {}),
                description=step_data.get("description", f"Step {i+1}")
            )
            steps.append(step)
        
        # 创建SOP
        import time
        sop = StandardOperatingProcedure(
            sop_id="",
            name=request.name,
            description=request.description,
            category=category,
            level=level,
            steps=steps,
            tags=request.tags,
            metadata={"source": "api_create", "auto_generated": False}
        )
        
        # 验证
        is_valid, errors = sop.validate()
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Validation errors: {errors}")
        
        # 保存
        sop_system.sops[sop.sop_id] = sop
        sop_system._index_sop(sop)
        sop_system._save_sops()
        
        return {
            "success": True,
            "sop_id": sop.sop_id,
            "message": "SOP created successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create SOP: {str(e)}")


@router.put("/{sop_id}")
async def update_sop(sop_id: str, request: SOPUpdateRequest) -> Dict[str, Any]:
    """更新SOP
    
    Args:
        sop_id: SOP ID
        request: 更新请求
        
    Returns:
        更新结果
    """
    sop_system = get_sop_learning_system()
    sop = sop_system.get_sop(sop_id)
    
    if not sop:
        raise HTTPException(status_code=404, detail=f"SOP not found: {sop_id}")
    
    # 更新字段
    if request.name is not None:
        sop.name = request.name
    if request.description is not None:
        sop.description = request.description
    if request.tags is not None:
        sop.tags = request.tags
    
    import time
    sop.updated_at = time.time()
    
    # 保存
    sop_system._save_sops()
    
    return {
        "success": True,
        "sop_id": sop_id,
        "message": "SOP updated successfully"
    }


@router.delete("/{sop_id}")
async def delete_sop(sop_id: str) -> Dict[str, Any]:
    """删除SOP
    
    Args:
        sop_id: SOP ID
        
    Returns:
        删除结果
    """
    sop_system = get_sop_learning_system()
    
    success = sop_system.delete_sop(sop_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"SOP not found: {sop_id}")
    
    return {
        "success": True,
        "sop_id": sop_id,
        "message": "SOP deleted successfully"
    }


@router.post("/recall")
async def recall_sops(request: SOPRecallRequest) -> Dict[str, Any]:
    """召回相关SOP
    
    Args:
        request: 召回请求
        
    Returns:
        相关SOP列表
    """
    sop_system = get_sop_learning_system()
    
    recalled = sop_system.recall_sop(
        task_description=request.task_description,
        context=request.context
    )
    
    results = []
    for sop_data in recalled[:request.max_results]:
        results.append({
            "sop_id": sop_data["sop"].sop_id,
            "name": sop_data["sop"].name,
            "description": sop_data["sop"].description,
            "relevance": sop_data["relevance"],
            "success_rate": sop_data["sop"].success_rate,
            "step_count": len(sop_data["sop"].steps)
        })
    
    return {
        "success": True,
        "count": len(results),
        "results": results
    }


@router.get("/statistics/stats")
async def get_statistics() -> Dict[str, Any]:
    """获取SOP系统统计信息
    
    Returns:
        统计信息
    """
    sop_system = get_sop_learning_system()
    stats = sop_system.get_statistics()
    
    return {
        "success": True,
        "statistics": stats
    }


@router.post("/export")
async def export_sops(format: str = "json", sop_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """导出SOP
    
    Args:
        format: 导出格式 (json, pickle)
        sop_ids: 要导出的SOP ID列表
        
    Returns:
        导出的SOP数据
    """
    sop_system = get_sop_learning_system()
    
    try:
        export_data = sop_system.export_sops(format=format, sop_ids=sop_ids)
        
        return {
            "success": True,
            "format": format,
            "count": len(sop_ids) if sop_ids else sop_system.get_statistics()["total_sops"],
            "data": export_data if format == "json" else "Binary data"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/import")
async def import_sops(data: str, format: str = "json") -> Dict[str, Any]:
    """导入SOP
    
    Args:
        data: 导入的SOP数据
        format: 数据格式 (json, pickle)
        
    Returns:
        导入结果
    """
    sop_system = get_sop_learning_system()
    
    try:
        result = sop_system.import_sops(data, format=format)
        
        return {
            "success": result.get("success", False),
            "imported_count": result.get("imported_count", 0),
            "skipped_count": result.get("skipped_count", 0),
            "failed_count": result.get("failed_count", 0),
            "total_sops": result.get("total_sops", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
