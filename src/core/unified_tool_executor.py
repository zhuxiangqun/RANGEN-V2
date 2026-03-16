#!/usr/bin/env python3
"""
Unified Tool Executor - 统一工具执行器

自动根据优先级选择最优工具执行：
1. CLI 工具 (最高优先级 110)
2. 本地工具 (优先级 100)
3. MCP 工具 (优先级 80/50)

与 PriorityRoutingEngine 集成，实现自动工具选择。
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.services.logging_service import get_logger
from src.agents.priority_routing_engine import PriorityRoutingEngine, ToolSource

try:
    from src.core.skill_registry import SkillRegistry
except ImportError:
    SkillRegistry = None

try:
    from src.agents.tools.tool_registry import ToolRegistry
except ImportError:
    ToolRegistry = None

from src.core.cli_executor import get_cli_executor, CLIExecutor

try:
    from src.core.cli_anything_generator import CLIAnythingGenerator, get_cli_anything_generator
except ImportError:
    CLIAnythingGenerator = None
    get_cli_anything_generator = None

logger = get_logger(__name__)


@dataclass
class ToolExecutionResult:
    """工具执行结果"""
    success: bool
    tool_name: str
    tool_source: str  # cli_tool, local, mcp
    output: Any
    execution_time: float
    error: Optional[str] = None


class UnifiedToolExecutor:
    """
    统一工具执行器
    
    根据优先级自动选择最优工具执行：
    - CLI 工具 (最高优先级)
    - 本地工具
    - MCP 工具
    
    使用 PriorityRoutingEngine 进行智能选择。
    """
    
    def __init__(
        self,
        skill_registry,
        tool_registry,
        cli_executor: Optional[CLIExecutor] = None,
        auto_generate: bool = True
    ):
        self.skill_registry = skill_registry
        self.tool_registry = tool_registry
        self.cli_executor = cli_executor or get_cli_executor()
        self.auto_generate = auto_generate
        
        self.priority_router = PriorityRoutingEngine(skill_registry, tool_registry)
        self.priority_router.cli_executor = self.cli_executor
        
        if auto_generate and CLIAnythingGenerator:
            self.cli_generator = get_cli_anything_generator()
            logger.info("UnifiedToolExecutor initialized with CLI-Anything auto-generation")
        else:
            self.cli_generator = None
            logger.info("UnifiedToolExecutor initialized with priority routing")
    
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ToolExecutionResult:
        """
        根据优先级自动选择并执行工具
        
        Args:
            query: 用户查询/请求
            context: 上下文
            
        Returns:
            ToolExecutionResult: 执行结果
        """
        import time
        start_time = time.time()
        
        try:
            # 1. 使用 PriorityRoutingEngine 选择最优工具
            prioritized_tools = self.priority_router.select_tools_with_priority(query, top_k=1)
            
            if not prioritized_tools:
                if self.auto_generate and self.cli_generator:
                    return await self._try_generate_and_execute(query, start_time)
                return ToolExecutionResult(
                    success=False,
                    tool_name="",
                    tool_source="none",
                    output=None,
                    execution_time=time.time() - start_time,
                    error="No suitable tools found"
                )
            
            # 2. 获取最高优先级的工具
            best_tool = prioritized_tools[0]
            tool_name = best_tool.name
            tool_source = best_tool.source
            
            logger.info(f"Selected tool: {tool_name} from {tool_source} (priority: {best_tool.priority_score})")
            
            # 3. 根据工具来源执行
            if tool_source == ToolSource.CLI_TOOL:
                return await self._execute_cli_tool(tool_name, query, start_time)
            elif tool_source == ToolSource.LOCAL:
                return await self._execute_local_tool(tool_name, query, start_time)
            elif tool_source == ToolSource.LOCAL_MCP or tool_source == ToolSource.EXTERNAL_MCP:
                return await self._execute_mcp_tool(tool_name, query, start_time)
            else:
                return await self._execute_local_tool(tool_name, query, start_time)
                
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return ToolExecutionResult(
                success=False,
                tool_name="",
                tool_source="error",
                output=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _execute_cli_tool(
        self,
        tool_name: str,
        query: str,
        start_time: float
    ) -> ToolExecutionResult:
        """执行 CLI 工具"""
        try:
            # 从 CLIExecutor 获取工具
            cli_tool = self.cli_executor.get_tool(tool_name)
            if not cli_tool:
                return ToolExecutionResult(
                    success=False,
                    tool_name=tool_name,
                    tool_source="cli_tool",
                    output=None,
                    execution_time=time.time() - start_time,
                    error=f"CLI tool not found: {tool_name}"
                )
            
            # 解析查询获取参数
            args = self._parse_query_to_args(query, tool_name)
            
            # 执行 CLI 工具
            result = await self.cli_executor.execute(
                command=cli_tool.command,
                args=args
            )
            
            return ToolExecutionResult(
                success=result.success,
                tool_name=tool_name,
                tool_source="cli_tool",
                output=result.stdout or result.json_output,
                execution_time=result.execution_time,
                error=result.stderr if not result.success else None
            )
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                tool_source="cli_tool",
                output=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _execute_local_tool(
        self,
        tool_name: str,
        query: str,
        start_time: float
    ) -> ToolExecutionResult:
        """执行本地工具"""
        try:
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                return ToolExecutionResult(
                    success=False,
                    tool_name=tool_name,
                    tool_source="local",
                    output=None,
                    execution_time=time.time() - start_time,
                    error=f"Local tool not found: {tool_name}"
                )
            
            # 执行工具
            result = await tool.execute(input=query)
            
            return ToolExecutionResult(
                success=True,
                tool_name=tool_name,
                tool_source="local",
                output=result.output if hasattr(result, 'output') else str(result),
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                tool_source="local",
                output=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _execute_mcp_tool(
        self,
        tool_name: str,
        query: str,
        start_time: float
    ) -> ToolExecutionResult:
        """执行 MCP 工具"""
        return ToolExecutionResult(
            success=False,
            tool_name=tool_name,
            tool_source="mcp",
            output=None,
            execution_time=time.time() - start_time,
            error="MCP tool execution not implemented yet"
        )
    
    async def _try_generate_and_execute(
        self,
        query: str,
        start_time: float
    ) -> ToolExecutionResult:
        """
        尝试按需生成 CLI 工具并执行
        
        当没有找到合适工具时，尝试从查询中推断需要什么软件，
        然后调用 CLI-Anything 生成 CLI 工具。
        """
        import time
        
        software_keywords = {
            "gimp": "gimp",
            "blender": "blender", 
            "photoshop": "gimp",
            "image": "gimp",
            "3d": "blender",
            "video": "ffmpeg",
            "audio": "ffmpeg",
            "office": "libreoffice",
            "document": "libreoffice",
        }
        
        query_lower = query.lower()
        detected_software = None
        
        for keyword, software in software_keywords.items():
            if keyword in query_lower:
                detected_software = software
                break
        
        if not detected_software:
            return ToolExecutionResult(
                success=False,
                tool_name="",
                tool_source="none",
                output=None,
                execution_time=time.time() - start_time,
                error="Cannot determine which software to use. Please specify gimp, blender, etc."
            )
        
        logger.info(f"尝试生成 CLI 工具: {detected_software}")
        
        try:
            result = await self.cli_generator.generate(detected_software)
            
            if result.success:
                logger.info(f"CLI 工具生成成功: {result.tool_name}")
                self.cli_executor.discover_tools()
                return await self._execute_cli_tool(result.tool_name, query, start_time)
            else:
                return ToolExecutionResult(
                    success=False,
                    tool_name=detected_software,
                    tool_source="cli_generator",
                    output=None,
                    execution_time=time.time() - start_time,
                    error=f"Failed to generate CLI tool: {result.error}"
                )
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                tool_name="",
                tool_source="cli_generator",
                output=None,
                execution_time=time.time() - start_time,
                error=f"CLI tool generation error: {str(e)}"
            )
    
    def _parse_query_to_args(self, query: str, tool_name: str) -> List[str]:
        """
        简单地将查询解析为 CLI 参数
        
        这是一个简化实现，实际应该用 LLM 来解析
        """
        # 简单实现：直接传递查询作为参数
        return ["--help"]
    
    async def execute_with_intelligent_selection(self, query: str) -> Optional[Dict[str, Any]]:
        """
        使用智能工具选择器执行任务
        
        这是一个高级接口，直接集成 IntelligentToolSelector
        """
        try:
            from src.agents.intelligent_tool_selector import get_intelligent_tool_selector
            
            # 获取智能选择器
            selector = get_intelligent_tool_selector(self.tool_registry, self.cli_executor)
            
            # 获取所有可用工具
            tools = self.tool_registry.get_all_tools()
            
            # 智能分析并选择工具
            needs_new_tool, tool_name, tool_instance, adaptation = await selector.analyze_and_select(query, tools)
            
            if tool_instance and adaptation:
                logger.info(f"Intelligent selection: {tool_name}, params: {adaptation.parameters}")
                
                # 获取 base_tool 并执行
                base_tool = getattr(tool_instance, "base_tool", None) or tool_instance
                
                if hasattr(base_tool, "call"):
                    import time
                    start_time = time.time()
                    
                    result = await base_tool.call(**adaptation.parameters)
                    
                    if result.success:
                        return {
                            "success": True,
                            "tool_name": tool_name,
                            "answer": result.data.get("title", str(result.data)) if result.data else "操作完成",
                            "execution_time": time.time() - start_time,
                            "tool_result": result.data
                        }
            
            return None
            
        except Exception as e:
            logger.warning(f"Intelligent selection error: {e}")
            return None


_unified_executor: Optional[UnifiedToolExecutor] = None


def get_unified_tool_executor() -> UnifiedToolExecutor:
    """获取全局统一工具执行器实例"""
    global _unified_executor
    if _unified_executor is None:
        from src.core.skill_registry import get_skill_registry
        from src.agents.tools.tool_initializer import initialize_tools
        
        skill_registry = get_skill_registry()
        tool_registry = initialize_tools()
        
        _unified_executor = UnifiedToolExecutor(
            skill_registry=skill_registry,
            tool_registry=tool_registry
        )
    return _unified_executor
