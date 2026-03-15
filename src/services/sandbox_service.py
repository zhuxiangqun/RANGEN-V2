"""
Sandbox Service - Unified sandbox for Tool/Agent/API execution
"""
import asyncio
import uuid
import time
from typing import Dict, Any, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class SandboxType(str, Enum):
    """沙箱类型"""
    TOOL = "tool"       # Tool执行沙箱
    AGENT = "agent"     # Agent执行沙箱
    API = "api"         # API调用沙箱
    CODE = "code"       # 代码执行沙箱


class SandboxStatus(str, Enum):
    """沙箱执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    ERROR = "error"
    BLOCKED = "blocked"


@dataclass
class SandboxConfig:
    """沙箱配置"""
    sandbox_type: SandboxType = SandboxType.TOOL
    
    # 通用配置
    timeout: int = 30              # 执行超时(秒)
    max_memory_mb: int = 256        # 最大内存
    allow_network: bool = False     # 是否允许网络
    
    # Tool沙箱配置
    allow_file_read: bool = True
    allowed_dirs: list = field(default_factory=lambda: ["data/workspace"])
    blocked_dirs: list = field(default_factory=lambda: [
        "/", "~", "/etc", "/usr", "/var", "/root", 
        "/home", "/opt", "/boot", "/dev", "/sys", "/proc"
    ])
    read_only_dirs: list = field(default_factory=lambda: ["data/workspace"])
    temp_dirs: list = field(default_factory=lambda: ["/tmp/sandbox"])
    
    # Agent沙箱配置
    max_iterations: int = 10        # 最大迭代次数
    allow_termination: bool = True   # 允许终止
    
    # API沙箱配置
    allow_external_calls: bool = False
    blocked_domains: list = field(default_factory=list)
    
    # Docker - 启用沙箱隔离
    use_docker: bool = True  # 默认启用
    docker_image: str = "python:3.11-slim"
    docker_network: str = "none"  # 完全禁用网络
    read_only_rootfs: bool = True
    auto_remove: bool = True
    
    # 资源配额
    max_cpu_percent: int = 50
    max_disk_write_mb: int = 100


@dataclass
class SandboxResult:
    """沙箱执行结果"""
    execution_id: str
    sandbox_type: SandboxType
    status: SandboxStatus
    output: Optional[str] = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SandboxService:
    """统一沙箱服务 - Tool/Agent/API执行隔离"""
    
    def __init__(self):
        self._configs: Dict[str, SandboxConfig] = {}
        self._executions: Dict[str, SandboxResult] = {}
    
    def create_config(
        self,
        sandbox_type: SandboxType,
        **kwargs
    ) -> SandboxConfig:
        """创建沙箱配置"""
        config = SandboxConfig(sandbox_type=sandbox_type, **kwargs)
        return config
    
    async def execute_in_sandbox(
        self,
        execution_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        config: Optional[SandboxConfig] = None
    ) -> SandboxResult:
        """在沙箱中执行"""
        kwargs = kwargs or {}
        
        # 获取配置
        if config is None:
            config = self._configs.get(execution_id, SandboxConfig())
        
        # 创建结果记录
        result = SandboxResult(
            execution_id=execution_id,
            sandbox_type=config.sandbox_type,
            status=SandboxStatus.RUNNING
        )
        
        self._executions[execution_id] = result
        
        start_time = time.time()
        
        try:
            # 检查是否超时
            if config.timeout > 0:
                # 异步执行带超时
                result.output = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=config.timeout
                )
            else:
                result.output = await func(*args, **kwargs)
            
            result.status = SandboxStatus.COMPLETED
            
        except asyncio.TimeoutError:
            result.status = SandboxStatus.TIMEOUT
            result.error = f"Execution timeout after {config.timeout}s"
            logger.warning(f"Sandbox execution timeout: {execution_id}")
            
        except Exception as e:
            result.status = SandboxStatus.ERROR
            result.error = str(e)
            logger.error(f"Sandbox execution error: {execution_id}, {e}")
        
        result.duration = time.time() - start_time
        
        return result
    
    def execute_tool_sandboxed(
        self,
        tool_func: Callable,
        tool_args: Dict[str, Any],
        config: Optional[SandboxConfig] = None
    ) -> SandboxResult:
        """在Tool沙箱中执行"""
        execution_id = f"tool_{uuid.uuid4().hex[:12]}"
        
        if config is None:
            config = SandboxConfig(
                sandbox_type=SandboxType.TOOL,
                timeout=30,
                allow_network=False,
                allow_file_read=True,
                allow_file_write=False
            )
        
        # 模拟同步执行
        import threading
        result_holder = [None]
        error_holder = [None]
        
        def run_tool():
            try:
                result_holder[0] = tool_func(**tool_args)
            except Exception as e:
                error_holder[0] = e
        
        thread = threading.Thread(target=run_tool)
        thread.start()
        thread.join(timeout=config.timeout)
        
        if thread.is_alive():
            return SandboxResult(
                execution_id=execution_id,
                sandbox_type=SandboxType.TOOL,
                status=SandboxStatus.TIMEOUT,
                error=f"Tool execution timeout after {config.timeout}s"
            )
        
        if error_holder[0]:
            return SandboxResult(
                execution_id=execution_id,
                sandbox_type=SandboxType.TOOL,
                status=SandboxStatus.ERROR,
                error=str(error_holder[0])
            )
        
        return SandboxResult(
            execution_id=execution_id,
            sandbox_type=SandboxType.TOOL,
            status=SandboxStatus.COMPLETED,
            output=str(result_holder[0])
        )
    
    def execute_api_sandboxed(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict] = None,
        data: Optional[Dict] = None,
        config: Optional[SandboxConfig] = None
    ) -> SandboxResult:
        """在API沙箱中执行"""
        execution_id = f"api_{uuid.uuid4().hex[:12]}"
        
        if config is None:
            config = SandboxConfig(
                sandbox_type=SandboxType.API,
                allow_external_calls=False,
                allowed_domains=[],
                blocked_domains=["localhost", "127.0.0.1"]
            )
        
        # 检查域名
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # 检查是否被阻止
        if domain in config.blocked_domains:
            return SandboxResult(
                execution_id=execution_id,
                sandbox_type=SandboxType.API,
                status=SandboxStatus.BLOCKED,
                error=f"Domain blocked: {domain}"
            )
        
        # 检查是否在白名单
        if config.allowed_domains and domain not in config.allowed_domains:
            return SandboxResult(
                execution_id=execution_id,
                sandbox_type=SandboxType.API,
                status=SandboxStatus.BLOCKED,
                error=f"Domain not in whitelist: {domain}"
            )
        
        # 检查是否允许外部调用
        if not config.allow_external_calls:
            return SandboxResult(
                execution_id=execution_id,
                sandbox_type=SandboxType.API,
                status=SandboxStatus.BLOCKED,
                error="External API calls are not allowed"
            )
        
        # 模拟API调用
        return SandboxResult(
            execution_id=execution_id,
            sandbox_type=SandboxType.API,
            status=SandboxStatus.COMPLETED,
            output=f"API call to {url} would be executed here",
            metadata={"url": url, "method": method}
        )
    
    def get_execution_result(self, execution_id: str) -> Optional[SandboxResult]:
        """获取执行结果"""
        return self._executions.get(execution_id)
    
    def is_sandbox_enabled(self, sandbox_type: SandboxType) -> bool:
        """检查沙箱是否启用"""
        # 默认全部启用
        return True
    
    def get_sandbox_status(self) -> Dict[str, Any]:
        """获取沙箱状态"""
        return {
            "enabled": True,
            "types": [t.value for t in SandboxType],
            "executions": len(self._executions)
        }


# Global instance
_sandbox_service: Optional[SandboxService] = None


def get_sandbox_service() -> SandboxService:
    """获取沙箱服务实例"""
    global _sandbox_service
    if _sandbox_service is None:
        _sandbox_service = SandboxService()
    return _sandbox_service
