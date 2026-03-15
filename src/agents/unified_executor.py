#!/usr/bin/env python3
"""
统一执行器 - 兼容新旧系统

提供统一API，同时支持:
- 新系统: Skill-based + MCP协议
- 旧系统: Tool-based (deprecated)
"""

import asyncio
import warnings
from typing import Any, Dict, Optional
from typing import Any, Dict, Optional
from dataclasses import dataclass

from src.agents.skills.hybrid_tool_executor import HybridToolExecutor
from src.agents.tools.tool_registry import get_tool_registry
from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0


class UnifiedExecutor:
    """
    统一执行器
    
    用法:
        executor = UnifiedExecutor()
        
        # 使用新系统 (Skill-based + MCP)
        result = await executor.execute("calculator", {"expression": "10 + 20"})
        
        # 强制使用旧系统 (Tool-based)
        result = await executor.execute("calculator", {"expression": "10 + 20"}, mode="legacy")
    """
    
    def __init__(self, default_mode: str = "skill"):
        self._default_mode = default_mode
        self._skill_executor = None
        self._tool_registry = None
        logger.info(f"UnifiedExecutor initialized with mode: {default_mode}")
    
    @property
    def skill_executor(self) -> HybridToolExecutor:
        if self._skill_executor is None:
            self._skill_executor = HybridToolExecutor(internal_mode="mcp")
        return self._skill_executor
    
    @property
    def tool_registry(self):
        if self._tool_registry is None:
            self._tool_registry = get_tool_registry()
        return self._tool_registry
    
    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        mode: Optional[str] = None
    ) -> ExecutionResult:
        import time
        start_time = time.time()
        
        exec_mode = mode or self._default_mode
        
        try:
            if exec_mode == "skill":
                result = await self._execute_skill(tool_name, parameters)
            else:
                result = await self._execute_legacy(tool_name, parameters)
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Execution failed: {e}")
            
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _execute_skill(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        result = await self.skill_executor.execute(
            tool_name=tool_name,
            parameters=parameters,
            tool_source=None
        )
        return result.result if hasattr(result, 'result') else result
    
    async def _execute_legacy(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        warnings.warn(
            f"Using legacy execution for {tool_name}. Please migrate to Skill-based execution.",
            DeprecationWarning,
            stacklevel=3
        )
        
        logger.warning(f"Legacy execution called for: {tool_name}")
        
        tool = self.tool_registry.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool not found: {tool_name}")
        
        result = await tool.execute(**parameters)
        return result.output if hasattr(result, 'output') else result
    
    def list_tools(self) -> Dict[str, list]:
        tools = self.tool_registry.list_tools()
        return {
            "available_tools": [t["name"] for t in tools],
            "count": len(tools)
        }


_unified_executor: Optional[UnifiedExecutor] = None


def get_unified_executor(default_mode: str = "skill") -> UnifiedExecutor:
    global _unified_executor
    if _unified_executor is None:
        _unified_executor = UnifiedExecutor(default_mode)
    return _unified_executor


async def execute_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    use_mcp: bool = True
) -> ExecutionResult:
    executor = get_unified_executor()
    mode = "skill" if use_mcp else "legacy"
    return await executor.execute(tool_name, parameters, mode)
