"""
Sandbox API - Unified sandbox for Tool/Agent/API execution
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from src.services.sandbox_service import (
    get_sandbox_service,
    SandboxType,
    SandboxConfig,
    SandboxStatus
)

router = APIRouter(prefix="/api/v1/sandbox", tags=["sandbox"])


class SandboxExecuteRequest(BaseModel):
    """沙箱执行请求"""
    sandbox_type: str = Field(..., description="沙箱类型: tool/agent/api/code")
    timeout: int = Field(default=30, description="超时时间(秒)")
    max_memory_mb: int = Field(default=256, description="最大内存(MB)")
    allow_network: bool = Field(default=False, description="允许网络")
    
    # Tool沙箱参数
    allow_file_read: Optional[bool] = None
    allow_file_write: Optional[bool] = None
    
    # API沙箱参数
    allow_external_calls: Optional[bool] = None
    allowed_domains: Optional[list] = None
    blocked_domains: Optional[list] = None
    
    # Agent沙箱参数
    max_iterations: Optional[int] = None


class SandboxResultResponse(BaseModel):
    """沙箱执行结果"""
    execution_id: str
    sandbox_type: str
    status: str
    output: Optional[str]
    error: Optional[str]
    duration: float
    metadata: Dict[str, Any]


@router.get("/status")
async def get_sandbox_status():
    """获取沙箱状态"""
    service = get_sandbox_service()
    
    return service.get_sandbox_status()


@router.get("/types")
async def get_sandbox_types():
    """获取支持的沙箱类型"""
    return {
        "types": [
            {
                "name": t.value,
                "description": desc
            }
            for t, desc in [
                (SandboxType.TOOL, "Tool execution sandbox"),
                (SandboxType.AGENT, "Agent execution sandbox"),
                (SandboxType.API, "API call sandbox"),
                (SandboxType.CODE, "Code execution sandbox")
            ]
        ]
    }


@router.get("/result/{execution_id}")
async def get_execution_result(execution_id: str):
    """获取沙箱执行结果"""
    service = get_sandbox_service()
    
    result = service.get_execution_result(execution_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution not found: {execution_id}"
        )
    
    return SandboxResultResponse(
        execution_id=result.execution_id,
        sandbox_type=result.sandbox_type.value,
        status=result.status.value,
        output=result.output,
        error=result.error,
        duration=result.duration,
        metadata=result.metadata
    )


@router.post("/execute/tool")
async def execute_tool_sandboxed(
    tool_name: str,
    tool_args: Dict[str, Any] = {}
):
    """在Tool沙箱中执行"""
    service = get_sandbox_service()
    
    # 创建配置
    config = SandboxConfig(
        sandbox_type=SandboxType.TOOL,
        timeout=30,
        allow_network=False,
        allow_file_read=True,
        allow_file_write=False
    )
    
    # 模拟Tool执行
    def mock_tool_func(**kwargs):
        return f"Tool {tool_name} executed with args: {kwargs}"
    
    result = service.execute_tool_sandboxed(
        tool_func=mock_tool_func,
        tool_args=tool_args,
        config=config
    )
    
    return SandboxResultResponse(
        execution_id=result.execution_id,
        sandbox_type=result.sandbox_type.value,
        status=result.status.value,
        output=result.output,
        error=result.error,
        duration=result.duration,
        metadata=result.metadata
    )


@router.post("/execute/api")
async def execute_api_sandboxed(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    allow_external_calls: bool = False
):
    """在API沙箱中执行"""
    service = get_sandbox_service()
    
    # 创建配置
    config = SandboxConfig(
        sandbox_type=SandboxType.API,
        allow_external_calls=allow_external_calls,
        blocked_domains=["localhost", "127.0.0.1", "0.0.0.0"]
    )
    
    result = service.execute_api_sandboxed(
        url=url,
        method=method,
        headers=headers,
        data=data,
        config=config
    )
    
    return SandboxResultResponse(
        execution_id=result.execution_id,
        sandbox_type=result.sandbox_type.value,
        status=result.status.value,
        output=result.output,
        error=result.error,
        duration=result.duration,
        metadata=result.metadata
    )


@router.post("/check-domain")
async def check_domain(domain: str):
    """检查域名是否允许"""
    service = get_sandbox_service()
    
    config = SandboxConfig(
        sandbox_type=SandboxType.API,
        allow_external_calls=True,
        allowed_domains=["*.openai.com", "*.deepseek.com"],
        blocked_domains=["localhost", "127.0.0.1"]
    )
    
    # 检查是否被阻止
    if domain in config.blocked_domains:
        return {
            "domain": domain,
            "allowed": False,
            "reason": "Domain is blocked"
        }
    
    # 检查是否在白名单
    import fnmatch
    for allowed in config.allowed_domains:
        if fnmatch.fnmatch(domain, allowed):
            return {
                "domain": domain,
                "allowed": True,
                "reason": "Domain is in whitelist"
            }
    
    return {
        "domain": domain,
        "allowed": False,
        "reason": "Domain is not in whitelist"
    }
