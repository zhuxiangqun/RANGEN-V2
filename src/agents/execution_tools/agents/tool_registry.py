"""
Centralized Tool Registry for RANGEN
"""
from typing import Dict, Any, Optional, List, Type
from src.interfaces.tool import ITool
from src.services.logging_service import get_logger

logger = get_logger(__name__)

class ToolRegistry:
    """
    Manages registration and retrieval of tools.
    Acts as a single source of truth for available capabilities.
    """
    
    def __init__(self):
        self._tools: Dict[str, ITool] = {}
        logger.info("ToolRegistry initialized")

    def register_tool(self, tool: Any) -> None:
        """Register a tool instance"""
        # 🚀 Adapter for legacy BaseTool instances
        if not hasattr(tool, 'config') and hasattr(tool, 'tool_name'):
            from src.interfaces.tool import ToolConfig, ToolCategory, ITool, ToolResult as IToolResult
            
            class BaseToolAdapter(ITool):
                def __init__(self, base_tool):
                    self.base_tool = base_tool
                    # Guess category
                    category = ToolCategory.UTILITY
                    if "retrieval" in base_tool.tool_name.lower() or "search" in base_tool.tool_name.lower():
                        category = ToolCategory.RETRIEVAL
                    elif "agent" in base_tool.tool_name.lower():
                        # Map agent tools to UTILITY or create new category if needed
                        category = ToolCategory.UTILITY
                    
                    config = ToolConfig(
                        name=base_tool.tool_name,
                        description=base_tool.description,
                        category=category
                    )
                    super().__init__(config)
                
                def get_parameters_schema(self) -> Dict[str, Any]:
                    return {"type": "object", "properties": {}}
                    
                async def execute(self, *args, **kwargs) -> IToolResult:
                    # 兼容旧调用方式：允许传入单个 dict 作为位置参数
                    call_kwargs = dict(kwargs)
                    if args:
                        if len(args) == 1 and isinstance(args[0], dict):
                            for k, v in args[0].items():
                                # 显式关键字参数优先，不被位置参数覆盖
                                if k not in call_kwargs:
                                    call_kwargs[k] = v
                        else:
                            raise TypeError(
                                f"{self.base_tool.tool_name} adapter.execute expects at most one dict positional argument"
                            )
                    
                    # 统一处理常见参数名称，尽量匹配 BaseTool.call 所需签名
                    base_call = getattr(self.base_tool, "call", None)
                    if not base_call:
                        raise AttributeError(f"Base tool {self.base_tool} has no 'call' method")
                    
                    import inspect
                    sig = inspect.signature(base_call)
                    params = sig.parameters
                    
                    # 为常见工具类型填充必需参数
                    if self.base_tool.tool_name == "answer_generation":
                        if "query" not in call_kwargs:
                            # 优先从原始请求中获取
                            original_query = call_kwargs.get("original_query") or call_kwargs.get("input_query")
                            if not original_query:
                                # 回退到上下文字段
                                context = call_kwargs.get("context") or {}
                                if isinstance(context, dict):
                                    original_query = context.get("query")
                            if original_query:
                                call_kwargs["query"] = original_query
                    elif self.base_tool.tool_name == "knowledge_retrieval":
                        if "query" not in call_kwargs:
                            original_query = call_kwargs.get("original_query") or call_kwargs.get("input_query")
                            if original_query:
                                call_kwargs["query"] = original_query
                    
                    # 过滤掉签名中不存在的参数，避免 TypeError
                    has_var_keyword = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
                    
                    if has_var_keyword:
                        filtered_kwargs = call_kwargs
                    else:
                        filtered_kwargs = {
                            k: v for k, v in call_kwargs.items() if k in params
                        }
                        
                        # 🚀 P0修复：强制确保 query 参数存在（如果 call_kwargs 中有）
                        # 有时候 inspect 可能无法正确获取参数（例如装饰器），或者参数名匹配有问题
                        if "query" in call_kwargs and "query" not in filtered_kwargs and self.base_tool.tool_name == "answer_generation":
                            filtered_kwargs["query"] = call_kwargs["query"]
                            logger.info("🔍 [BaseToolAdapter] Forcibly added query to filtered_kwargs")
                    
                    # Debug logging
                    if self.base_tool.tool_name == "answer_generation":
                        logger.info(f"🔍 [BaseToolAdapter] {self.base_tool.tool_name} params: {list(params.keys())}")
                        logger.info(f"🔍 [BaseToolAdapter] {self.base_tool.tool_name} input kwargs keys: {list(call_kwargs.keys())}")
                        logger.info(f"🔍 [BaseToolAdapter] {self.base_tool.tool_name} filtered kwargs keys: {list(filtered_kwargs.keys())}")
                        if "knowledge_data" in call_kwargs:
                            logger.info(f"🔍 [BaseToolAdapter] knowledge_data found in input kwargs, size: {len(call_kwargs['knowledge_data'])}")
                    
                    result = await self.base_tool.call(**filtered_kwargs)
                    return IToolResult(
                        success=result.success,
                        output=result.data,
                        execution_time=result.execution_time,
                        error=result.error,
                        metadata=result.metadata or {}
                    )
                
                async def call(self, **kwargs) -> IToolResult:
                    return await self.execute(**kwargs)
            
            tool = BaseToolAdapter(tool)

        if tool.config.name in self._tools:
            logger.warning(f"Overwriting existing tool: {tool.config.name}")
        
        self._tools[tool.config.name] = tool
        logger.info(f"Registered tool: {tool.config.name} ({tool.config.category.value})")

    def get_tool(self, name: str) -> Optional[ITool]:
        """Retrieve a tool by name"""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools metadata"""
        return [
            {
                "name": t.config.name,
                "description": t.config.description,
                "category": t.config.category.value,
                "parameters": t.get_parameters_schema()
            }
            for t in self._tools.values()
        ]

    def get_all_tools(self) -> List[ITool]:
        """Get all tool instances"""
        return list(self._tools.values())

# Singleton instance
_tool_registry_instance: Optional[ToolRegistry] = None

def get_tool_registry() -> ToolRegistry:
    """Get the singleton ToolRegistry instance"""
    global _tool_registry_instance
    if _tool_registry_instance is None:
        _tool_registry_instance = ToolRegistry()
    return _tool_registry_instance
