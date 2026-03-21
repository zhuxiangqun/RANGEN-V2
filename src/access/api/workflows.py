"""
Workflow API Routes - REST API for Workflow operations
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


class WorkflowTestRequest(BaseModel):
    """工作流测试请求"""
    workflow_name: str = Field(..., description="工作流名称")
    test_input: str = Field(..., description="测试输入")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="测试选项")


class WorkflowTestResponse(BaseModel):
    """工作流测试响应"""
    success: bool
    workflow_name: str
    overall_score: float
    quality_level: str
    dimensions: Dict[str, Any]
    component_usage: Dict[str, Any]
    execution_trace: List[Dict[str, Any]]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WorkflowListResponse(BaseModel):
    """工作流列表响应"""
    workflows: List[Dict[str, Any]]
    total: int


class WorkflowResponse(BaseModel):
    """工作流响应"""
    name: str
    type: str
    description: str
    status: str
    source: str


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(status: Optional[str] = None):
    """
    获取Workflow列表
    """
    try:
        from src.ui.discovery_helper import discover_workflows_from_registry
        
        workflows = discover_workflows_from_registry()
        
        if status:
            workflows = [w for w in workflows if w.get('status') == status]
        
        return {
            "workflows": workflows,
            "total": len(workflows)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Workflow列表失败: {str(e)}"
        )


@router.get("/{workflow_name}", response_model=WorkflowResponse)
async def get_workflow(workflow_name: str):
    """
    获取单个Workflow详情
    """
    try:
        from src.ui.discovery_helper import discover_workflows_from_registry
        
        workflows = discover_workflows_from_registry()
        
        for wf in workflows:
            if wf.get('name', '').lower() == workflow_name.lower():
                return wf
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow不存在: {workflow_name}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Workflow详情失败: {str(e)}"
        )


@router.post("/test", response_model=WorkflowTestResponse)
async def test_workflow(request: WorkflowTestRequest):
    """
    测试Workflow执行
    """
    try:
        from src.ui.discovery_helper import test_workflow as _test_workflow
        
        result = _test_workflow(request.workflow_name, request.test_input)
        
        return result
    except Exception as e:
        return {
            "success": False,
            "workflow_name": request.workflow_name,
            "overall_score": 0,
            "quality_level": "error",
            "dimensions": {},
            "component_usage": {},
            "execution_trace": [],
            "error": str(e)
        }


@router.post("/optimize")
async def optimize_workflow(workflow_name: str, test_result: Dict[str, Any]):
    """
    优化Workflow
    """
    try:
        from src.ui.discovery_helper import optimize_workflow as _optimize_workflow
        
        result = _optimize_workflow(workflow_name, test_result)
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"优化失败: {str(e)}"
        }
