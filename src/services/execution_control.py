"""
Execution Control Service - Loop limit, timeout, termination management
"""
import uuid
import time
import asyncio
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    TIMEOUT = "timeout"


class TerminationReason(str, Enum):
    """终止原因"""
    USER_REQUEST = "user_request"
    LOOP_LIMIT = "loop_limit"
    TIMEOUT = "timeout"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class ExecutionConfig:
    """执行配置"""
    max_loops: int = 10              # 最大循环次数
    step_timeout: int = 30            # 单步超时(秒)
    total_timeout: int = 300          # 总超时(秒)
    enable_termination: bool = True   # 允许手动终止


@dataclass
class ExecutionState:
    """执行状态"""
    execution_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    current_loop: int = 0
    loops_history: list = field(default_factory=list)
    termination_reason: Optional[TerminationReason] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    partial_result: Optional[str] = None
    error_message: Optional[str] = None


class ExecutionController:
    """执行控制器 - 管理循环限制、超时和终止"""
    
    def __init__(self):
        self._executions: Dict[str, ExecutionState] = {}
        self._configs: Dict[str, ExecutionConfig] = {}
        self._locks: Dict[str, Lock] = {}
    
    def _get_lock(self, execution_id: str) -> Lock:
        """获取执行锁"""
        if execution_id not in self._locks:
            self._locks[execution_id] = Lock()
        return self._locks[execution_id]
    
    def start_execution(
        self,
        execution_id: str,
        config: Optional[ExecutionConfig] = None
    ) -> ExecutionState:
        """开始执行"""
        if execution_id in self._executions:
            logger.warning(f"Execution {execution_id} already exists")
            return self._executions[execution_id]
        
        state = ExecutionState(
            execution_id=execution_id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now()
        )
        
        self._executions[execution_id] = state
        self._configs[execution_id] = config or ExecutionConfig()
        
        logger.info(f"Execution started: {execution_id}")
        
        return state
    
    def check_loop_limit(self, execution_id: str) -> tuple[bool, Optional[str]]:
        """检查循环次数是否超限"""
        if execution_id not in self._executions:
            return False, "Execution not found"
        
        state = self._executions[execution_id]
        config = self._configs.get(execution_id, ExecutionConfig())
        
        state.current_loop += 1
        
        if state.current_loop > config.max_loops:
            state.status = ExecutionStatus.TERMINATED
            state.termination_reason = TerminationReason.LOOP_LIMIT
            state.ended_at = datetime.now()
            state.partial_result = f"已达到最大循环次数 {config.max_loops}"
            
            logger.warning(f"Execution {execution_id} terminated: loop limit exceeded")
            return True, f"Loop limit exceeded: {state.current_loop}/{config.max_loops}"
        
        # 记录循环历史
        state.loops_history.append({
            'loop': state.current_loop,
            'timestamp': datetime.now().isoformat()
        })
        
        return False, None
    
    def check_timeout(self, execution_id: str) -> tuple[bool, Optional[str]]:
        """检查是否超时"""
        if execution_id not in self._executions:
            return False, "Execution not found"
        
        state = self._executions[execution_id]
        config = self._configs.get(execution_id, ExecutionConfig())
        
        if not state.started_at:
            return False, None
        
        # 检查总超时
        elapsed = (datetime.now() - state.started_at).total_seconds()
        
        if elapsed > config.total_timeout:
            state.status = ExecutionStatus.TIMEOUT
            state.termination_reason = TerminationReason.TIMEOUT
            state.ended_at = datetime.now()
            state.partial_result = f"执行超时，已运行 {elapsed:.1f}秒"
            
            logger.warning(f"Execution {execution_id} timeout: {elapsed:.1f}s")
            return True, f"Total timeout: {elapsed:.1f}s > {config.total_timeout}s"
        
        return False, None
    
    def can_continue(self, execution_id: str) -> bool:
        """检查是否可以继续执行"""
        if execution_id not in self._executions:
            return False
        
        state = self._executions[execution_id]
        
        # 检查状态
        if state.status != ExecutionStatus.RUNNING:
            return False
        
        # 检查循环限制
        loop_exceeded, _ = self.check_loop_limit(execution_id)
        if loop_exceeded:
            return False
        
        # 检查超时
        timeout_exceeded, _ = self.check_timeout(execution_id)
        if timeout_exceeded:
            return False
        
        return True
    
    def terminate(self, execution_id: str, reason: str = "user_request") -> bool:
        """手动终止执行"""
        if execution_id not in self._executions:
            logger.warning(f"Execution {execution_id} not found")
            return False
        
        state = self._executions[execution_id]
        
        if state.status != ExecutionStatus.RUNNING:
            logger.warning(f"Execution {execution_id} is not running: {state.status}")
            return False
        
        state.status = ExecutionStatus.TERMINATED
        state.termination_reason = TerminationReason(reason)
        state.ended_at = datetime.now()
        
        logger.info(f"Execution {execution_id} terminated by user")
        
        return True
    
    def complete(self, execution_id: str, result: str) -> bool:
        """标记执行完成"""
        if execution_id not in self._executions:
            return False
        
        state = self._executions[execution_id]
        state.status = ExecutionStatus.COMPLETED
        state.termination_reason = TerminationReason.COMPLETED
        state.ended_at = datetime.now()
        state.partial_result = result
        
        logger.info(f"Execution {execution_id} completed")
        
        return True
    
    def fail(self, execution_id: str, error: str) -> bool:
        """标记执行失败"""
        if execution_id not in self._executions:
            return False
        
        state = self._executions[execution_id]
        state.status = ExecutionStatus.FAILED
        state.termination_reason = TerminationReason.ERROR
        state.ended_at = datetime.now()
        state.error_message = error
        
        logger.error(f"Execution {execution_id} failed: {error}")
        
        return True
    
    def get_state(self, execution_id: str) -> Optional[ExecutionState]:
        """获取执行状态"""
        return self._executions.get(execution_id)
    
    def get_status(self, execution_id: str) -> Dict[str, Any]:
        """获取执行状态摘要"""
        if execution_id not in self._executions:
            return {"error": "Execution not found"}
        
        state = self._executions[execution_id]
        config = self._configs.get(execution_id, ExecutionConfig())
        
        elapsed = 0
        if state.started_at:
            end_time = state.ended_at or datetime.now()
            elapsed = (end_time - state.started_at).total_seconds()
        
        return {
            "execution_id": execution_id,
            "status": state.status.value,
            "current_loop": state.current_loop,
            "max_loops": config.max_loops,
            "elapsed_time": elapsed,
            "total_timeout": config.total_timeout,
            "termination_reason": state.termination_reason.value if state.termination_reason else None,
            "partial_result": state.partial_result,
            "error_message": state.error_message,
            "can_continue": self.can_continue(execution_id)
        }
    
    def cleanup(self, execution_id: str) -> bool:
        """清理执行记录"""
        if execution_id in self._executions:
            del self._executions[execution_id]
        if execution_id in self._configs:
            del self._configs[execution_id]
        if execution_id in self._locks:
            del self._locks[execution_id]
        
        logger.info(f"Execution {execution_id} cleaned up")
        return True


# Global instance
_controller: Optional[ExecutionController] = None


def get_execution_controller() -> ExecutionController:
    """获取执行控制器实例"""
    global _controller
    if _controller is None:
        _controller = ExecutionController()
    return _controller
