#!/usr/bin/env python3
"""
执行控制器 - Agent实时性保障
Execution Controller - Agent Real-time Support

参考文章核心观点：
"流式输出、打字态、取消、中断恢复——请求-响应式架构撑不住"

核心功能：
1. 任务取消
2. 任务暂停/恢复
3. Checkpoint保存
4. 执行状态追踪
5. 超时控制
"""

import logging
import asyncio
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


class PauseType(Enum):
    """暂停类型"""
    USER = "user"           # 用户主动暂停
    SYSTEM = "system"       # 系统自动暂停（如资源不足）
    TIMEOUT = "timeout"    # 超时暂停


@dataclass
class ExecutionCheckpoint:
    """执行检查点"""
    checkpoint_id: str
    execution_id: str
    step_index: int
    state: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionState:
    """执行状态"""
    execution_id: str
    status: ExecutionStatus
    user_id: str
    tool_name: str
    parameters: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime] = None
    current_step: int = 0
    checkpoints: List[ExecutionCheckpoint] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    progress: float = 0.0  # 0-100
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 暂停相关
    pause_type: Optional[PauseType] = None
    pause_reason: Optional[str] = None
    # 流式相关
    streaming_output: List[str] = field(default_factory=list)
    is_streaming: bool = False


class ExecutionController:
    """
    执行控制器
    
    提供生产级任务执行控制：
    1. 任务取消
    2. 任务暂停/恢复
    3. Checkpoint保存与恢复
    4. 执行状态追踪
    5. 超时控制
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 执行超时时间（秒）
        self.default_timeout = self.config.get("default_timeout", 600)
        
        # Checkpoint保留数量
        self.max_checkpoints = self.config.get("max_checkpoints", 10)
        
        # 执行状态存储
        self.executions: Dict[str, ExecutionState] = {}
        
        # 回调函数
        self.on_cancel_callbacks: List[Callable] = []
        self.on_pause_callbacks: List[Callable] = []
        self.on_resume_callbacks: List[Callable] = []
        
        # 清理任务
        self._cleanup_task: Optional[ asyncio.Task] = None
        
        logger.info("执行控制器初始化完成")
    
    async def start(
        self,
        user_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> str:
        """
        启动执行任务
        
        Args:
            user_id: 用户ID
            tool_name: 工具名称
            parameters: 调用参数
            metadata: 元数据
            timeout: 超时时间（秒）
            
        Returns:
            execution_id: 执行ID
        """
        execution_id = str(uuid.uuid4())
        
        state = ExecutionState(
            execution_id=execution_id,
            status=ExecutionStatus.RUNNING,
            user_id=user_id,
            tool_name=tool_name,
            parameters=parameters,
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        
        self.executions[execution_id] = state
        
        # 设置超时
        if timeout is None:
            timeout = self.default_timeout
        
        # 调度超时任务
        asyncio.create_task(self._timeout_task(execution_id, timeout))
        
        logger.info(f"启动执行任务: {execution_id}")
        
        return execution_id
    
    async def cancel(
        self,
        execution_id: str,
        reason: str = "用户取消"
    ) -> Dict[str, Any]:
        """
        取消执行任务
        
        Args:
            execution_id: 执行ID
            reason: 取消原因
            
        Returns:
            结果
        """
        if execution_id not in self.executions:
            return {"success": False, "error": "任务不存在"}
        
        state = self.executions[execution_id]
        
        if state.status not in [ExecutionStatus.RUNNING, ExecutionStatus.PAUSED]:
            return {"success": False, "error": f"任务状态不支持取消: {state.status.value}"}
        
        # 更新状态
        state.status = ExecutionStatus.CANCELLED
        state.end_time = datetime.now()
        
        # 记录原因
        state.metadata["cancel_reason"] = reason
        state.metadata["cancelled_at"] = datetime.now().isoformat()
        
        # 执行回调
        for callback in self.on_cancel_callbacks:
            try:
                await callback(execution_id, reason)
            except Exception as e:
                logger.error(f"取消回调执行失败: {e}")
        
        logger.info(f"取消执行任务: {execution_id}, 原因: {reason}")
        
        return {
            "success": True,
            "execution_id": execution_id,
            "status": state.status.value,
            "elapsed_time": (state.end_time - state.start_time).total_seconds()
        }
    
    async def pause(
        self,
        execution_id: str,
        pause_type: PauseType = PauseType.USER,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        暂停执行任务
        
        Args:
            execution_id: 执行ID
            pause_type: 暂停类型
            reason: 暂停原因
            
        Returns:
            结果
        """
        if execution_id not in self.executions:
            return {"success": False, "error": "任务不存在"}
        
        state = self.executions[execution_id]
        
        if state.status != ExecutionStatus.RUNNING:
            return {"success": False, "error": f"只有运行中的任务可以暂停: {state.status.value}"}
        
        # 保存checkpoint
        checkpoint = await self._create_checkpoint(execution_id, state)
        state.checkpoints.append(checkpoint)
        
        # 限制checkpoint数量
        if len(state.checkpoints) > self.max_checkpoints:
            state.checkpoints = state.checkpoints[-self.max_checkpoints:]
        
        # 更新状态
        state.status = ExecutionStatus.PAUSED
        state.pause_type = pause_type
        state.pause_reason = reason
        state.end_time = datetime.now()
        
        # 执行回调
        for callback in self.on_pause_callbacks:
            try:
                await callback(execution_id, pause_type, reason)
            except Exception as e:
                logger.error(f"暂停回调执行失败: {e}")
        
        logger.info(f"暂停执行任务: {execution_id}, 类型: {pause_type.value}")
        
        return {
            "success": True,
            "execution_id": execution_id,
            "checkpoint_id": checkpoint.checkpoint_id,
            "status": state.status.value
        }
    
    async def resume(
        self,
        execution_id: str,
        from_checkpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        恢复执行任务
        
        Args:
            execution_id: 执行ID
            from_checkpoint: 从指定checkpoint恢复
            
        Returns:
            结果
        """
        if execution_id not in self.executions:
            return {"success": False, "error": "任务不存在"}
        
        state = self.executions[execution_id]
        
        if state.status != ExecutionStatus.PAUSED:
            return {"success": False, "error": f"只有暂停的任务可以恢复: {state.status.value}"}
        
        # 恢复状态
        if from_checkpoint:
            checkpoint = next(
                (c for c in state.checkpoints if c.checkpoint_id == from_checkpoint),
                None
            )
            if checkpoint:
                state.current_step = checkpoint.step_index
                # 可以选择恢复state
        
        state.status = ExecutionStatus.RUNNING
        state.pause_type = None
        state.pause_reason = None
        state.end_time = None
        
        # 执行回调
        for callback in self.on_resume_callbacks:
            try:
                await callback(execution_id, from_checkpoint)
            except Exception as e:
                logger.error(f"恢复回调执行失败: {e}")
        
        logger.info(f"恢复执行任务: {execution_id}")
        
        return {
            "success": True,
            "execution_id": execution_id,
            "status": state.status.value,
            "resume_from_step": state.current_step
        }
    
    async def update_progress(
        self,
        execution_id: str,
        progress: float,
        step: Optional[int] = None,
        streaming_output: Optional[str] = None
    ):
        """更新执行进度"""
        if execution_id not in self.executions:
            return
        
        state = self.executions[execution_id]
        
        if state.status != ExecutionStatus.RUNNING:
            return
        
        # 更新进度
        state.progress = max(0.0, min(100.0, progress))
        
        # 更新步骤
        if step is not None:
            state.current_step = step
        
        # 流式输出
        if streaming_output:
            state.is_streaming = True
            state.streaming_output.append(streaming_output)
            
            # 保留最近100条
            if len(state.streaming_output) > 100:
                state.streaming_output = state.streaming_output[-100:]
    
    async def complete(
        self,
        execution_id: str,
        result: Any = None,
        error: Optional[str] = None
    ):
        """完成任务"""
        if execution_id not in self.executions:
            return
        
        state = self.executions[execution_id]
        
        state.status = ExecutionStatus.COMPLETED if not error else ExecutionStatus.FAILED
        state.end_time = datetime.now()
        state.result = result
        state.error = error
        
        if error:
            state.metadata["error_at"] = datetime.now().isoformat()
        
        logger.info(f"任务完成: {execution_id}, 状态: {state.status.value}")
    
    def get_state(self, execution_id: str) -> Optional[ExecutionState]:
        """获取执行状态"""
        return self.executions.get(execution_id)
    
    def get_all_states(
        self,
        user_id: Optional[str] = None,
        status: Optional[ExecutionStatus] = None
    ) -> List[ExecutionState]:
        """获取所有执行状态"""
        states = list(self.executions.values())
        
        if user_id:
            states = [s for s in states if s.user_id == user_id]
        
        if status:
            states = [s for s in states if s.status == status]
        
        return states
    
    def get_streaming_output(self, execution_id: str) -> List[str]:
        """获取流式输出"""
        state = self.executions.get(execution_id)
        if state:
            return state.streaming_output
        return []
    
    async def _create_checkpoint(
        self,
        execution_id: str,
        state: ExecutionState
    ) -> ExecutionCheckpoint:
        """创建检查点"""
        checkpoint = ExecutionCheckpoint(
            checkpoint_id=str(uuid.uuid4()),
            execution_id=execution_id,
            step_index=state.current_step,
            state={
                "progress": state.progress,
                "streaming_output": state.streaming_output[-10:]  # 保留最近10条
            },
            timestamp=datetime.now(),
            metadata=state.metadata
        )
        
        return checkpoint
    
    async def _timeout_task(self, execution_id: str, timeout: int):
        """超时检测任务"""
        try:
            await asyncio.sleep(timeout)
            
            if execution_id in self.executions:
                state = self.executions[execution_id]
                
                if state.status == ExecutionStatus.RUNNING:
                    # 超时暂停
                    await self.pause(
                        execution_id,
                        pause_type=PauseType.TIMEOUT,
                        reason=f"执行超时 ({timeout}秒)"
                    )
                    
                    logger.warning(f"执行任务超时已暂停: {execution_id}")
        
        except asyncio.CancelledError:
            pass  # 任务被取消，正常退出
    
    def on_cancel(self, callback: Callable):
        """注册取消回调"""
        self.on_cancel_callbacks.append(callback)
    
    def on_pause(self, callback: Callable):
        """注册暂停回调"""
        self.on_pause_callbacks.append(callback)
    
    def on_resume(self, callback: Callable):
        """注册恢复回调"""
        self.on_resume_callbacks.append(callback)
    
    def cleanup_completed(self, older_than_hours: int = 24):
        """清理已完成的执行记录"""
        cutoff = datetime.now() - timedelta(hours=older_than_hours)
        
        to_remove = []
        for execution_id, state in self.executions.items():
            if state.status in [ExecutionStatus.COMPLETED, ExecutionStatus.CANCELLED, ExecutionStatus.FAILED]:
                if state.end_time and state.end_time < cutoff:
                    to_remove.append(execution_id)
        
        for execution_id in to_remove:
            del self.executions[execution_id]
        
        logger.info(f"清理完成执行记录: {len(to_remove)}条")
        
        return len(to_remove)


# 全局单例
_execution_controller: Optional[ExecutionController] = None


def get_execution_controller(
    config: Optional[Dict[str, Any]] = None
) -> ExecutionController:
    """获取执行控制器单例"""
    global _execution_controller
    
    if _execution_controller is None:
        _execution_controller = ExecutionController(config)
    
    return _execution_controller
