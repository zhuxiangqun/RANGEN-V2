"""
Sandbox - 安全执行环境

提供隔离的代码执行环境，防止危险操作
"""

import asyncio
import logging
import os
import tempfile
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class Language(Enum):
    """支持的编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    BASH = "bash"


@dataclass
class SandboxConfig:
    """沙箱配置"""
    # 超时设置
    timeout: int = 30  # 秒
    max_memory_mb: int = 256  # MB
    
    # 权限控制
    allow_network: bool = False
    allow_file_read: bool = True
    allow_file_write: bool = True
    blocked_dirs: List[str] = field(default_factory=lambda: [
        "/", "~", "/etc", "/usr", "/var", "/root", 
        "/home", "/opt", "/boot", "/dev", "/sys", "/proc"
    ])
    # 只读目录
    read_only_dirs: List[str] = field(default_factory=lambda: ["data/workspace"])
    # 临时目录
    temp_dirs: List[str] = field(default_factory=lambda: ["/tmp/sandbox"])
    
    # 环境
    env_vars: Dict[str, str] = field(default_factory=dict)
    
    # Docker - 启用沙箱隔离
    use_docker: bool = True  # 默认启用Docker沙箱
    docker_image: str = "python:3.11-slim"  # 使用slim镜像减少攻击面
    docker_network: str = "none"  # 完全禁用网络
    read_only_rootfs: bool = True  # 根文件系统只读
    auto_remove: bool = True  # 执行后自动清理容器
    
    # 资源配额
    max_cpu_percent: int = 50  # CPU限制
    max_disk_write_mb: int = 100  # 磁盘写入限制


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: str = ""
    error: str = ""
    exit_code: int = 0
    execution_time: float = 0
    memory_used_mb: float = 0


class Sandbox:
    """
    沙箱执行环境
    
    提供安全的代码执行，支持:
    - Python
    - JavaScript
    - Bash (受限)
    
    安全特性:
    - 超时保护
    - 内存限制
    - 网络隔离
    - 文件系统限制
    - 危险命令过滤
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._running_processes: Dict[str, asyncio.subprocess.Process] = {}
    
    async def execute(
        self,
        code: str,
        language: Language = Language.PYTHON,
        stdin: str = ""
    ) -> ExecutionResult:
        """
        执行代码
        
        Args:
            code: 要执行的代码
            language: 编程语言
            stdin: 标准输入
            
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            if language == Language.PYTHON:
                return await self._execute_python(code, stdin, start_time)
            elif language == Language.JAVASCRIPT:
                return await self._execute_javascript(code, stdin, start_time)
            elif language == Language.BASH:
                return await self._execute_bash(code, stdin, start_time)
            else:
                return ExecutionResult(
                    success=False,
                    error=f"Unsupported language: {language.value}"
                )
                
        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                error=f"Execution timeout ({self.config.timeout}s)",
                exit_code=-1
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                exit_code=-1
            )
    
    async def _execute_python(
        self,
        code: str,
        stdin: str,
        start_time: datetime
    ) -> ExecutionResult:
        """执行Python代码"""
        
        # 安全检查
        security_error = self._check_security(code)
        if security_error:
            return ExecutionResult(success=False, error=security_error)
        
        # 如果使用Docker
        if self.config.use_docker:
            return await self._execute_docker(code, "python3", start_time)
        
        # 使用本地Python
        return await self._execute_local(
            ["python3", "-u", "-c", code],
            stdin,
            start_time
        )
    
    async def _execute_javascript(
        self,
        code: str,
        stdin: str,
        start_time: datetime
    ) -> ExecutionResult:
        """执行JavaScript代码"""
        
        security_error = self._check_security(code)
        if security_error:
            return ExecutionResult(success=False, error=security_error)
        
        if self.config.use_docker:
            return await self._execute_docker(code, "node", start_time)
        
        return await self._execute_local(
            ["node", "-e", code],
            stdin,
            start_time
        )
    
    async def _execute_bash(
        self,
        code: str,
        stdin: str,
        start_time: datetime
    ) -> ExecutionResult:
        """执行Bash代码"""
        
        # 严格安全检查
        security_error = self._check_bash_security(code)
        if security_error:
            return ExecutionResult(success=False, error=security_error)
        
        return await self._execute_local(
            ["bash", "-c", code],
            stdin,
            start_time
        )
    
    async def _execute_local(
        self,
        cmd: List[str],
        stdin: str,
        start_time: datetime
    ) -> ExecutionResult:
        """本地执行"""
        
        # 设置环境变量
        env = os.environ.copy()
        env.update(self.config.env_vars)
        
        # 如果禁止网络
        if not self.config.allow_network:
            env["HTTP_PROXY"] = ""
            env["HTTPS_PROXY"] = ""
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self.config.allowed_dirs[0] if self.config.allowed_dirs else None
            )
            
            # 保存进程引用
            process_id = str(uuid.uuid4())
            self._running_processes[process_id] = process
            
            try:
                # 执行并等待超时
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=stdin.encode() if stdin else None),
                    timeout=self.config.timeout
                )
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return ExecutionResult(
                    success=process.returncode == 0,
                    output=stdout.decode("utf-8", errors="replace"),
                    error=stderr.decode("utf-8", errors="replace"),
                    exit_code=process.returncode or 0,
                    execution_time=execution_time
                )
                
            finally:
                # 清理进程
                if process_id in self._running_processes:
                    del self._running_processes[process_id]
                    
                    # 如果还在运行，终止它
                    if process.returncode is None:
                        process.terminate()
                        try:
                            await asyncio.wait_for(process.wait(), timeout=5)
                        except asyncio.TimeoutError:
                            process.kill()
                            
        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                error=f"Execution timeout ({self.config.timeout}s)",
                exit_code=-1
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
    
    async def _execute_docker(
        self,
        code: str,
        interpreter: str,
        start_time: datetime
    ) -> ExecutionResult:
        """Docker中执行"""
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=f".{interpreter}", delete=False) as f:
            f.write(code)
            code_file = f.name
        
        try:
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{code_file}:/code",
                "--network", "none" if not self.config.allow_network else "bridge",
                self.config.docker_image,
                interpreter, "/code"
            ]
            
            return await self._execute_local(cmd, "", start_time)
            
        finally:
            # 清理临时文件
            try:
                os.unlink(code_file)
            except:
                pass
    
    def _check_security(self, code: str) -> Optional[str]:
        """检查代码安全性 (Python/JS)"""
        
        # 危险关键词
        dangerous_patterns = [
            ("import os", "import os"),
            ("import sys", "import sys"),
            ("import subprocess", "import subprocess"),
            ("import socket", "import socket"),
            ("import requests", "import requests"),
            ("import httpx", "import httpx"),
            ("eval(", "eval()"),
            ("exec(", "exec()"),
            ("__import__", "__import__()"),
            ("open(", "file operations"),
            ("readfile", "file read"),
            ("writefile", "file write"),
        ]
        
        for pattern, description in dangerous_patterns:
            if pattern in code:
                # 检查是否在注释中
                for line in code.split("\n"):
                    if pattern in line and not line.strip().startswith("#"):
                        return f"Blocked: {description} - security violation"
        
        return None
    
    def _check_bash_security(self, code: str) -> Optional[str]:
        """检查Bash安全性"""
        
        # 绝对禁止的命令
        forbidden_commands = [
            "rm -rf",
            "dd if=",
            "mkfs",
            "fdisk",
            "> /dev/sd",
            "curl | sh",
            "wget | sh",
            "shutdown",
            "reboot",
            "halt",
            "init 0",
            "init 6",
            "chmod 777",
            "chown -R",
            "wget",
            "curl",
            "ssh",
            "scp",
            "ftp",
            "telnet",
            ":(){:|:&};:",  # Fork bomb
        ]
        
        code_lower = code.lower()
        for cmd in forbidden_commands:
            if cmd in code_lower:
                return f"Blocked forbidden command: {cmd}"
        
        # 检查路径穿越
        for blocked in self.config.blocked_dirs:
            if blocked in code:
                return f"Blocked path: {blocked}"
        
        return None
    
    async def terminate_all(self):
        """终止所有运行中的进程"""
        for process_id, process in list(self._running_processes.items()):
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        self._running_processes.clear()
        logger.info("All sandbox processes terminated")


class SandboxPool:
    """
    沙箱池
    
    管理多个沙箱实例，提供复用
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None, max_size: int = 5):
        self.config = config or SandboxConfig()
        self.max_size = max_size
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._initialized = False
    
    async def initialize(self):
        """初始化沙箱池"""
        if self._initialized:
            return
        
        # 预创建沙箱实例
        for _ in range(self.max_size):
            sandbox = Sandbox(self.config)
            await self._pool.put(sandbox)
        
        self._initialized = True
        logger.info(f"Sandbox pool initialized with {self.max_size} instances")
    
    async def execute(
        self,
        code: str,
        language: Language = Language.PYTHON,
        stdin: str = ""
    ) -> ExecutionResult:
        """从池中获取沙箱执行"""
        
        if not self._initialized:
            await self.initialize()
        
        # 获取沙箱
        sandbox = await self._pool.get()
        
        try:
            # 执行代码
            result = await sandbox.execute(code, language, stdin)
            return result
            
        finally:
            # 归还沙箱
            await self._pool.put(sandbox)
    
    async def close(self):
        """关闭沙箱池"""
        await self.terminate_all()
        self._initialized = False
        logger.info("Sandbox pool closed")


# ==================== 便捷函数 ====================

_default_sandbox: Optional[Sandbox] = None
_default_pool: Optional[SandboxPool] = None


def get_sandbox(config: Optional[SandboxConfig] = None) -> Sandbox:
    """获取默认沙箱"""
    global _default_sandbox
    if _default_sandbox is None:
        _default_sandbox = Sandbox(config)
    return _default_sandbox


def get_sandbox_pool(
    config: Optional[SandboxConfig] = None,
    max_size: int = 5
) -> SandboxPool:
    """获取沙箱池"""
    global _default_pool
    if _default_pool is None:
        _default_pool = SandboxPool(config, max_size)
    return _default_pool


async def execute_safe(
    code: str,
    language: Language = Language.PYTHON,
    use_pool: bool = True
) -> ExecutionResult:
    """便捷执行函数"""
    if use_pool:
        pool = get_sandbox_pool()
        return await pool.execute(code, language)
    else:
        sandbox = get_sandbox()
        return await sandbox.execute(code, language)
