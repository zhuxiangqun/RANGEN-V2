"""
Execution Control API - Loop limit, timeout, termination endpoints
"""
import time
from fastapi import APIRouter, HTTPException, status
from typing import Optional
from pydantic import BaseModel, Field
from src.services.execution_control import (
    get_execution_controller,
    ExecutionConfig,
    ExecutionStatus
)

router = APIRouter(prefix="/api/v1/execution", tags=["execution-control"])


class ExecutionConfigRequest(BaseModel):
    """执行配置请求"""
    max_loops: int = Field(default=10, description="最大循环次数")
    step_timeout: int = Field(default=30, description="单步超时(秒)")
    total_timeout: int = Field(default=300, description="总超时(秒)")
    enable_termination: bool = Field(default=True, description="允许手动终止")


class StartExecutionRequest(BaseModel):
    """开始执行请求"""
    execution_id: Optional[str] = Field(None, description="执行ID，为空则自动生成")
    config: Optional[ExecutionConfigRequest] = None


class ExecutionStatusResponse(BaseModel):
    """执行状态响应"""
    execution_id: str
    status: str
    current_loop: int
    max_loops: int
    elapsed_time: float
    total_timeout: int
    termination_reason: Optional[str]
    partial_result: Optional[str]
    error_message: Optional[str]
    can_continue: bool


@router.post("/start")
async def start_execution(request: StartExecutionRequest):
    """
    开始执行（带控制配置）
    """
    controller = get_execution_controller()
    
    # 生成执行ID
    execution_id = request.execution_id or f"exec_{int(time.time() * 1000)}"
    
    # 转换配置
    config = None
    if request.config:
        config = ExecutionConfig(
            max_loops=request.config.max_loops,
            step_timeout=request.config.step_timeout,
            total_timeout=request.config.total_timeout,
            enable_termination=request.config.enable_termination
        )
    
    # 开始执行
    state = controller.start_execution(execution_id, config)
    
    return {
        "execution_id": execution_id,
        "status": state.status.value,
        "message": "Execution started",
        "config": {
            "max_loops": config.max_loops if config else 10,
            "total_timeout": config.total_timeout if config else 300
        }
    }


@router.get("/status/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str):
    """
    获取执行状态
    """
    controller = get_execution_controller()
    
    status_info = controller.get_status(execution_id)
    
    if "error" in status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=status_info["error"]
        )
    
    return ExecutionStatusResponse(**status_info)


@router.post("/check/{execution_id}")
async def check_execution(execution_id: str):
    """
    检查执行是否可继续（用于循环中）
    """
    controller = get_execution_controller()
    
    can_continue = controller.can_continue(execution_id)
    status_info = controller.get_status(execution_id)
    
    if "error" in status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=status_info["error"]
        )
    
    return {
        "execution_id": execution_id,
        "can_continue": can_continue,
        "status": status_info["status"],
        "current_loop": status_info["current_loop"],
        "max_loops": status_info["max_loops"],
        "termination_reason": status_info.get("termination_reason")
    }


@router.post("/terminate/{execution_id}")
async def terminate_execution(
    execution_id: str,
    reason: str = "user_request"
):
    """
    手动终止执行
    """
    controller = get_execution_controller()
    
    success = controller.terminate(execution_id, reason)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot terminate: execution not found or already stopped"
        )
    
    status_info = controller.get_status(execution_id)
    
    return {
        "execution_id": execution_id,
        "status": "terminated",
        "termination_reason": reason,
        "partial_result": status_info.get("partial_result")
    }


@router.post("/complete/{execution_id}")
async def complete_execution(execution_id: str, result: str):
    """
    标记执行完成
    """
    controller = get_execution_controller()
    
    success = controller.complete(execution_id, result)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete: execution not found"
        )
    
    return {
        "execution_id": execution_id,
        "status": "completed",
        "result": result
    }


@router.post("/fail/{execution_id}")
async def fail_execution(execution_id: str, error: str):
    """
    标记执行失败
    """
    controller = get_execution_controller()
    
    success = controller.fail(execution_id, error)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot fail: execution not found"
        )
    
    return {
        "execution_id": execution_id,
        "status": "failed",
        "error": error
    }


@router.delete("/cleanup/{execution_id}")
async def cleanup_execution(execution_id: str):
    """
    清理执行记录
    """
    controller = get_execution_controller()
    
    success = controller.cleanup(execution_id)
    
    return {
        "execution_id": execution_id,
        "cleaned": success
    }
