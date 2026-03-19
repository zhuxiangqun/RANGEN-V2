"""
Ops Diagnosis Agent API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from src.agents.ops_diagnosis_agent import get_ops_diagnosis_agent, OpsDiagnosisAgent
from src.api.auth import require_read

router = APIRouter(prefix="/api/v1/ops-diagnosis", tags=["ops-diagnosis"])


class DiagnosisRequest(BaseModel):
    query: str
    auto_fix: bool = True


class DiagnosisResponse(BaseModel):
    status: str
    agent_name: str
    result: Dict[str, Any]


@router.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose(
    request: DiagnosisRequest,
    auth_data: dict = Depends(require_read)
):
    """
    运维诊断接口 - 诊断系统问题并自动修复
    
    输入：
    - query: 问题描述（如"根路径404"、"MCP服务离线"）
    - auto_fix: 是否自动修复（默认True）
    
    输出：
    - status: 执行状态
    - result: 诊断结果和修复信息
    """
    try:
        agent = get_ops_diagnosis_agent()
        result = await agent.execute(
            inputs={"query": request.query},
            context={"auto_fix": request.auto_fix, "api_key": auth_data.get("key", "")}
        )
        
        if result.status.value == "success":
            return DiagnosisResponse(
                status="success",
                agent_name=result.agent_name,
                result=result.output or {}
            )
        else:
            raise HTTPException(status_code=500, detail=result.error or "诊断失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"诊断服务异常: {str(e)}")


@router.get("/health-check")
async def health_check(auth_data: dict = Depends(require_read)):
    """
    健康检查 - 检查系统各组件状态
    """
    try:
        agent = get_ops_diagnosis_agent()
        result = await agent.execute(
            inputs={"query": "健康检查"},
            context={"api_key": auth_data.get("key", "")}
        )
        
        if result.status.value == "success":
            return {
                "status": "success",
                "health": result.output
            }
        else:
            return {
                "status": "error",
                "error": result.error
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/fix/{issue_type}")
async def fix_issue(
    issue_type: str,
    auth_data: dict = Depends(require_read)
):
    """
    直接修复指定类型的问题
    
    issue_type: root_path_404, mcp_offline, cache_clear, etc.
    """
    query_map = {
        "root_path_404": "根路径返回404",
        "mcp_offline": "MCP服务离线",
        "cache_clear": "清理缓存",
        "api_restart": "重启API服务",
    }
    
    query = query_map.get(issue_type, issue_type)
    
    try:
        agent = get_ops_diagnosis_agent()
        result = await agent.execute(
            inputs={"query": query},
            context={"auto_fix": True, "api_key": auth_data.get("key", "")}
        )
        
        return {
            "status": "success" if result.status.value == "success" else "error",
            "result": result.output or {},
            "error": result.error
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
