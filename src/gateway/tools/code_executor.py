"""
Enhanced Code Executor - Enhanced Code Executor

Sandbox-based secure code execution with retry, timeout, error recovery and more
Enhanced v2: Non-blocking execution, syntax validation, execution hooks, cancellation support
"""

import asyncio
import traceback
import ast
import concurrent.futures
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class ExecutionStatus(Enum):
    """Execution status"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    MEMORY_LIMIT = "memory_limit"
    SECURITY_VIOLATION = "security_violation"
    RETRY_EXHAUSTED = "retry_exhausted"
    CANCELLED = "cancelled"
    SYNTAX_ERROR = "syntax_error"


@dataclass
class CodeResult:
    """Code execution result"""
    status: ExecutionStatus
    output: str
    error: str
    execution_time: float
    language: str
    retry_count: int = 0
    memory_used_mb: float = 0
    
    @property
    def success(self) -> bool:
        return self.status == ExecutionStatus.SUCCESS


@dataclass
class ExecutorConfig:
    """Executor configuration"""
    # Timeout
    timeout: int = 30
    max_retries: int = 2
    retry_delay: float = 1.0
    
    # Memory
    max_memory_mb: int = 256
    
    # Security
    sandbox_enabled: bool = True
    
    # Debug
    include_traceback: bool = True
    max_output_length: int = 10000
    
    # Thread pool (new)
    thread_pool_size: int = 4


@dataclass
class ExecutionHooks:
    """Execution hooks - for monitoring and logging"""
    on_start: Optional[Callable[[str, str], None]] = None  # (code, language)
    on_success: Optional[Callable[[str, float], None]] = None  # (output, execution_time)
    on_error: Optional[Callable[[str, str], None]] = None  # (error, execution_time)
    on_complete: Optional[Callable[[ExecutionStatus], None]] = None  # (status)


class CancellationToken:
    """Cancellation token - for cancelling running code"""
    
    def __init__(self):
        self._cancelled = False
    
    def cancel(self):
        """Request cancellation"""
        self._cancelled = True
    
    @property
    def is_cancelled(self) -> bool:
        return self._cancelled


class EnhancedCodeExecutor:
    """
    Enhanced Code Executor
    
    Features:
    - Sandbox isolated execution
    - Auto retry
    - Error recovery
    - Timeout protection
    - Memory limit
    - Multi-language support
    - Non-blocking execution (thread pool)
    - Syntax validation
    - Execution hooks
    - Cancellation support
    """
    
    def __init__(self, config: Optional[ExecutorConfig] = None):
        self.config = config or ExecutorConfig()
        self._sandbox = None
        self._initialized = False
        self._thread_pool: Optional[concurrent.futures.ThreadPoolExecutor] = None
    
    async def initialize(self):
        """Initialize executor"""
        if self._initialized:
            return
        
        # Initialize thread pool
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.thread_pool_size
        )
        
        # Import sandbox
        try:
            from src.gateway.sandbox import Sandbox, SandboxConfig
            
            sandbox_config = SandboxConfig(
                timeout=self.config.timeout,
                max_memory_mb=self.config.max_memory_mb,
                allow_network=False,
                allow_file_read=True,
                allow_file_write=True
            )
            
            if self.config.sandbox_enabled:
                self._sandbox = Sandbox(sandbox_config)
            
            self._initialized = True
            logger.info("EnhancedCodeExecutor initialized")
            
        except ImportError as e:
            logger.warning(f"Sandbox not available, using fallback: {e}")
            self._initialized = True
    
    async def execute(
        self,
        code: str,
        language: str = "python",
        stdin: str = "",
        cancellation_token: Optional[CancellationToken] = None,
        hooks: Optional[ExecutionHooks] = None
    ) -> CodeResult:
        """
        Execute code
        
        Args:
            code: Code to execute
            language: Language (python, javascript, bash)
            stdin: Standard input
            cancellation_token: Cancellation token
            hooks: Execution hooks
            
        Returns:
            CodeResult: Execution result
        """
        if not self._initialized:
            await self.initialize()
        
        # Call start hook
        if hooks and hooks.on_start:
            try:
                hooks.on_start(code, language)
            except Exception as e:
                logger.warning(f"Hook on_start failed: {e}")
        
        # Check cancellation status
        if cancellation_token and cancellation_token.is_cancelled:
            result = CodeResult(
                status=ExecutionStatus.CANCELLED,
                output="",
                error="Execution was cancelled",
                execution_time=0,
                language=language
            )
            if hooks and hooks.on_complete:
                hooks.on_complete(result.status)
            return result
        
        # Determine execution strategy
        if language.lower() == "python":
            result = await self._execute_python(code, stdin, cancellation_token, hooks)
        elif language.lower() in ["javascript", "js", "node"]:
            result = await self._execute_javascript(code, stdin, cancellation_token)
        elif language.lower() in ["bash", "sh", "shell"]:
            result = await self._execute_bash(code, stdin, cancellation_token)
        else:
            result = CodeResult(
                status=ExecutionStatus.ERROR,
                output="",
                error=f"Unsupported language: {language}",
                execution_time=0,
                language=language
            )
        
        # Call complete hook
        if hooks and hooks.on_complete:
            try:
                hooks.on_complete(result.status)
            except Exception as e:
                logger.warning(f"Hook on_complete failed: {e}")
        
        return result
    
    def _validate_python_syntax(self, code: str) -> Optional[str]:
        """
        Validate Python code syntax
        
        Returns:
            None if valid, error message if invalid
        """
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return f"Syntax error at line {e.lineno}: {e.msg}"
    
    async def _execute_python(
        self,
        code: str,
        stdin: str,
        cancellation_token: Optional[CancellationToken] = None,
        hooks: Optional[ExecutionHooks] = None
    ) -> CodeResult:
        """Execute Python code"""
        
        # 1. Preprocess code
        code = self._preprocess_python(code)
        
        # 2. Syntax validation
        syntax_error = self._validate_python_syntax(code)
        if syntax_error:
            return CodeResult(
                status=ExecutionStatus.SYNTAX_ERROR,
                output="",
                error=syntax_error,
                execution_time=0,
                language="python"
            )
        
        # 3. Try execution (with retry)
        last_error = ""
        
        for attempt in range(self.config.max_retries + 1):
            # Check cancellation status
            if cancellation_token and cancellation_token.is_cancelled:
                return CodeResult(
                    status=ExecutionStatus.CANCELLED,
                    output="",
                    error="Execution was cancelled",
                    execution_time=0,
                    language="python",
                    retry_count=attempt
                )
            
            try:
                # Try sandbox execution
                if self._sandbox and self.config.sandbox_enabled:
                    from src.gateway.sandbox import Language
                    
                    result = await asyncio.wait_for(
                        self._sandbox.execute(code, Language.PYTHON, stdin),
                        timeout=self.config.timeout
                    )
                    
                    if result.success:
                        # Call success hook
                        if hooks and hooks.on_success:
                            hooks.on_success(result.output, result.execution_time)
                        
                        return CodeResult(
                            status=ExecutionStatus.SUCCESS,
                            output=self._truncate_output(result.output),
                            error=result.error,
                            execution_time=result.execution_time,
                            language="python",
                            retry_count=attempt,
                            memory_used_mb=result.memory_used_mb
                        )
                    else:
                        last_error = result.error
                        
                else:
                    # Fallback: Direct execution (non-blocking)
                    return await self._execute_python_direct(code, stdin, attempt, cancellation_token, hooks)
                    
            except asyncio.TimeoutError:
                last_error = f"Execution timeout ({self.config.timeout}s)"
                logger.warning(f"Python execution attempt {attempt + 1} timed out")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Python execution attempt {attempt + 1} failed: {e}")
            
            # Wait before retry
            if attempt < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay)
        
        # All retries failed
        result = CodeResult(
            status=ExecutionStatus.RETRY_EXHAUSTED,
            output="",
            error=f"Failed after {self.config.max_retries + 1} attempts: {last_error}",
            execution_time=0,
            language="python",
            retry_count=self.config.max_retries
        )
        
        # Call error hook
        if hooks and hooks.on_error:
            hooks.on_error(result.error, 0)
        
        return result
    
    async def _execute_python_direct(
        self,
        code: str,
        stdin: str,
        attempt: int,
        cancellation_token: Optional[CancellationToken] = None,
        hooks: Optional[ExecutionHooks] = None
    ) -> CodeResult:
        """Direct Python execution (no sandbox) - non-blocking via thread pool"""
        
        start_time = datetime.now()
        
        def _run_code() -> tuple:
            """Run code in thread"""
            output_buffer = []
            error_buffer = []
            
            # Create restricted execution environment
            restricted_globals = {
                "__builtins__": {
                    "print": lambda *args: output_buffer.append(" ".join(str(a) for a in args)),
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "set": set,
                    "tuple": tuple,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "sorted": sorted,
                    "reversed": reversed,
                    "any": any,
                    "all": all,
                    "isinstance": isinstance,
                    "type": type,
                    "Exception": Exception,
                    "ValueError": ValueError,
                    "TypeError": TypeError,
                    "IndexError": IndexError,
                    "KeyError": KeyError,
                    "ZeroDivisionError": ZeroDivisionError,
                    "AttributeError": AttributeError,
                    "NameError": NameError,
                }
            }
            
            try:
                exec(code, restricted_globals, {})
                return "\n".join(output_buffer), "\n".join(error_buffer), None
            except Exception as e:
                return "\n".join(output_buffer), str(e), e
        
        try:
            # Use thread pool for non-blocking execution
            loop = asyncio.get_event_loop()
            
            try:
                output, error, exc = await asyncio.wait_for(
                    loop.run_in_executor(self._thread_pool, _run_code),
                    timeout=self.config.timeout
                )
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Check cancellation status
                if cancellation_token and cancellation_token.is_cancelled:
                    return CodeResult(
                        status=ExecutionStatus.CANCELLED,
                        output=output,
                        error="Execution was cancelled",
                        execution_time=execution_time,
                        language="python",
                        retry_count=attempt
                    )
                
                if exc is None:
                    # Call success hook
                    if hooks and hooks.on_success:
                        hooks.on_success(output, execution_time)
                    
                    return CodeResult(
                        status=ExecutionStatus.SUCCESS,
                        output=self._truncate_output(output),
                        error=error,
                        execution_time=execution_time,
                        language="python",
                        retry_count=attempt
                    )
                else:
                    error_msg = error
                    if self.config.include_traceback:
                        error_msg += "\n" + traceback.format_exc()
                    
                    # Call error hook
                    if hooks and hooks.on_error:
                        hooks.on_error(error_msg, execution_time)
                    
                    return CodeResult(
                        status=ExecutionStatus.ERROR,
                        output=self._truncate_output(output),
                        error=error_msg,
                        execution_time=execution_time,
                        language="python",
                        retry_count=attempt
                    )
                    
            except asyncio.TimeoutError:
                # Call error hook
                if hooks and hooks.on_error:
                    hooks.on_error(f"Execution timeout ({self.config.timeout}s)", self.config.timeout)
                
                return CodeResult(
                    status=ExecutionStatus.TIMEOUT,
                    output="",
                    error=f"Execution timeout ({self.config.timeout}s)",
                    execution_time=self.config.timeout,
                    language="python",
                    retry_count=attempt
                )
                
        except Exception as e:
            error_msg = str(e)
            if self.config.include_traceback:
                error_msg += "\n" + traceback.format_exc()
            
            # Call error hook
            if hooks and hooks.on_error:
                hooks.on_error(error_msg, (datetime.now() - start_time).total_seconds())
            
            return CodeResult(
                status=ExecutionStatus.ERROR,
                output="",
                error=error_msg,
                execution_time=(datetime.now() - start_time).total_seconds(),
                language="python",
                retry_count=attempt
            )
    
    async def _execute_javascript(
        self,
        code: str,
        stdin: str,
        cancellation_token: Optional[CancellationToken] = None
    ) -> CodeResult:
        """Execute JavaScript code"""
        
        start_time = datetime.now()
        
        # Try using Node.js
        try:
            process = await asyncio.create_subprocess_exec(
                "node", "-e", code,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=stdin.encode() if stdin else None),
                    timeout=self.config.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return CodeResult(
                    status=ExecutionStatus.TIMEOUT,
                    output="",
                    error=f"Execution timeout ({self.config.timeout}s)",
                    execution_time=self.config.timeout,
                    language="javascript",
                    retry_count=0
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if process.returncode == 0:
                return CodeResult(
                    status=ExecutionStatus.SUCCESS,
                    output=self._truncate_output(stdout.decode()),
                    error="",
                    execution_time=execution_time,
                    language="javascript",
                    retry_count=0
                )
            else:
                return CodeResult(
                    status=ExecutionStatus.ERROR,
                    output="",
                    error=stderr.decode(),
                    execution_time=execution_time,
                    language="javascript",
                    retry_count=0
                )
                
        except asyncio.TimeoutError:
            return CodeResult(
                status=ExecutionStatus.TIMEOUT,
                output="",
                error=f"Execution timeout ({self.config.timeout}s)",
                execution_time=self.config.timeout,
                language="javascript",
                retry_count=0
            )
        except FileNotFoundError:
            return CodeResult(
                status=ExecutionStatus.ERROR,
                output="",
                error="Node.js not found. Please install Node.js to execute JavaScript.",
                execution_time=0,
                language="javascript",
                retry_count=0
            )
    
    async def _execute_bash(
        self,
        code: str,
        stdin: str,
        cancellation_token: Optional[CancellationToken] = None
    ) -> CodeResult:
        """Execute Bash code"""
        
        # Bash execution uses sandbox
        if self._sandbox and self.config.sandbox_enabled:
            from src.gateway.sandbox import Language
            
            try:
                result = await asyncio.wait_for(
                    self._sandbox.execute(code, Language.BASH, stdin),
                    timeout=self.config.timeout
                )
                
                status = ExecutionStatus.SUCCESS if result.success else ExecutionStatus.ERROR
                
                return CodeResult(
                    status=status,
                    output=self._truncate_output(result.output),
                    error=result.error,
                    execution_time=result.execution_time,
                    language="bash",
                    retry_count=0,
                    memory_used_mb=result.memory_used_mb
                )
            except asyncio.TimeoutError:
                return CodeResult(
                    status=ExecutionStatus.TIMEOUT,
                    output="",
                    error=f"Execution timeout ({self.config.timeout}s)",
                    execution_time=self.config.timeout,
                    language="bash",
                    retry_count=0
                )
        else:
            return CodeResult(
                status=ExecutionStatus.ERROR,
                output="",
                error="Bash execution requires Sandbox mode",
                execution_time=0,
                language="bash",
                retry_count=0
            )
    
    def _preprocess_python(self, code: str) -> str:
        """Preprocess Python code"""
        
        # Remove common problematic patterns
        lines = code.split("\n")
        processed_lines = []
        
        for line in lines:
            # Skip IPython-specific lines
            if line.strip().startswith("%"):
                continue
            if line.strip().startswith("!"):
                continue
                
            processed_lines.append(line)
        
        return "\n".join(processed_lines)
    
    def _truncate_output(self, output: str) -> str:
        """Truncate output"""
        if len(output) > self.config.max_output_length:
            return output[:self.config.max_output_length] + f"\n... (truncated, total {len(output)} chars)"
        return output
    
    async def close(self):
        """Close executor"""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
            self._thread_pool = None
        
        if self._sandbox:
            await self._sandbox.terminate_all()
        
        self._initialized = False


# ==================== Convenience Functions ====================

_executor: Optional[EnhancedCodeExecutor] = None


def get_code_executor(config: Optional[ExecutorConfig] = None) -> EnhancedCodeExecutor:
    """Get code executor"""
    global _executor
    if _executor is None:
        _executor = EnhancedCodeExecutor(config)
    return _executor


async def execute_code(
    code: str,
    language: str = "python",
    **kwargs
) -> CodeResult:
    """Convenience code execution function"""
    executor = get_code_executor()
    return await executor.execute(code, language, **kwargs)
