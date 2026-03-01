"""
Simplified Tool System - 精简工具集
基于 Anthropic Context Engineering 原则

核心原则：
1. 每个工具功能边界清晰，无重叠
2. 最小可行工具集
3. 工具描述清晰、无歧义
4. Token 高效返回

工具分类（精简后）：
- RETRIEVAL: 信息检索（唯一）
- REASONING: 推理分析（唯一）
- ACTION: 执行操作（唯一）
- UTILITY: 通用工具（唯一）
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass


class ToolCategory(Enum):
    """工具分类 - 清晰的边界"""
    RETRIEVAL = "retrieval"      # 信息检索（搜索、向量检索）
    REASONING = "reasoning"      # 推理分析
    ACTION = "action"            # 执行操作
    UTILITY = "utility"         # 通用工具


@dataclass
class ToolSpec:
    """工具规范"""
    name: str
    category: ToolCategory
    description: str
    parameters: Dict[str, Any]
    examples: List[Dict[str, Any]]
    boundaries: str  # 明确说明这个工具不做什么


# 精简后的核心工具集
CORE_TOOLS: Dict[str, ToolSpec] = {
    # ========== RETRIEVAL 类 ==========
    "search": ToolSpec(
        name="search",
        category=ToolCategory.RETRIEVAL,
        description="Web search for current information, facts, or recent news.",
        parameters={
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "default": 5}
        },
        examples=[
            {"query": "Python 3.12 new features", "max_results": 3}
        ],
        boundaries="DO NOT use for searching code files or internal documents. Use 'retrieve' for that."
    ),
    
    "retrieve": ToolSpec(
        name="retrieve",
        category=ToolCategory.RETRIEVAL,
        description="Retrieve information from internal knowledge base, code files, or documents.",
        parameters={
            "query": {"type": "string", "description": "Retrieval query"},
            "source": {"type": "string", "enum": ["code", "docs", "kb"], "default": "kb"},
            "top_k": {"type": "integer", "default": 5}
        },
        examples=[
            {"query": "authentication flow", "source": "code", "top_k": 3}
        ],
        boundaries="DO NOT use for web search. Use 'search' for current information."
    ),
    
    # ========== REASONING 类 ==========
    "analyze": ToolSpec(
        name="analyze",
        category=ToolCategory.REASONING,
        description="Deep analysis of complex problems, code, or data structures.",
        parameters={
            "target": {"type": "string", "description": "What to analyze"},
            "analysis_type": {"type": "string", "enum": ["code", "data", "logic", "security"]},
            "focus": {"type": "string", "description": "Specific aspects to focus on"}
        },
        examples=[
            {"target": "auth.py", "analysis_type": "code", "focus": "security"}
        ],
        boundaries="DO NOT execute code or perform actions. Use 'execute' for that."
    ),
    
    "plan": ToolSpec(
        name="plan",
        category=ToolCategory.REASONING,
        description="Create a step-by-step plan for complex tasks.",
        parameters={
            "goal": {"type": "string", "description": "Task goal"},
            "constraints": {"type": "array", "description": "Any constraints"},
            "subtasks": {"type": "boolean", "default": False}
        },
        examples=[
            {"goal": "Implement user auth", "subtasks": True}
        ],
        boundaries="DO NOT execute plans. Use 'execute' for that."
    ),
    
    # ========== ACTION 类 ==========
    "execute": ToolSpec(
        name="execute",
        category=ToolCategory.ACTION,
        description="Execute code, run commands, or perform actions.",
        parameters={
            "action": {"type": "string", "enum": ["run_code", "run_command", "create_file", "edit_file"]},
            "code": {"type": "string", "description": "Code to execute"},
            "command": {"type": "string", "description": "Shell command"},
            "path": {"type": "string", "description": "File path"}
        },
        examples=[
            {"action": "run_command", "command": "ls -la"}
        ],
        boundaries="DO NOT analyze or retrieve information. Use appropriate tools for that."
    ),
    
    # ========== UTILITY 类 ==========
    "compute": ToolSpec(
        name="compute",
        category=ToolCategory.UTILITY,
        description="Mathematical computations, calculations, or data transformations.",
        parameters={
            "operation": {"type": "string", "enum": ["calculate", "convert", "format"]},
            "expression": {"type": "string"},
            "input_format": {"type": "string"},
            "output_format": {"type": "string"}
        },
        examples=[
            {"operation": "calculate", "expression": "2**10"}
        ],
        boundaries="DO NOT use for complex analysis or data retrieval."
    ),
    
    "validate": ToolSpec(
        name="validate",
        category=ToolCategory.UTILITY,
        description="Validate data, code, or outputs against rules or patterns.",
        parameters={
            "target": {"type": "string", "description": "What to validate"},
            "rules": {"type": "array", "description": "Validation rules"},
            "strict": {"type": "boolean", "default": True}
        },
        examples=[
            {"target": "user_input", "rules": ["non-empty", "email-format"]}
        ],
        boundaries="DO NOT generate content or perform analysis."
    ),
}


class SimplifiedToolRegistry:
    """
    精简后的工具注册表
    - 每个工具职责单一
    - 清晰的边界
    - 最小功能集
    """
    
    def __init__(self):
        self._tools = CORE_TOOLS.copy()
        self._tool_handlers: Dict[str, Callable] = {}
    
    def register_handler(self, tool_name: str, handler: Callable) -> None:
        """注册工具处理器"""
        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        self._tool_handlers[tool_name] = handler
    
    def get_tool_spec(self, tool_name: str) -> Optional[ToolSpec]:
        """获取工具规范"""
        return self._tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, ToolSpec]:
        """获取所有工具"""
        return self._tools.copy()
    
    def get_tools_by_category(self, category: ToolCategory) -> List[ToolSpec]:
        """按类别获取工具"""
        return [t for t in self._tools.values() if t.category == category]
    
    def get_tool_descriptions(self) -> str:
        """生成工具描述（供 prompt 使用）"""
        lines = ["Available Tools:", "=" * 50]
        
        for category in ToolCategory:
            tools = self.get_tools_by_category(category)
            if tools:
                lines.append(f"\n## {category.value.upper()} Tools:")
                for tool in tools:
                    lines.append(f"\n### {tool.name}")
                    lines.append(f"Description: {tool.description}")
                    lines.append(f"Parameters: {json.dumps(tool.parameters, indent=2)}")
                    lines.append(f"Boundaries: {tool.boundaries}")
        
        return "\n".join(lines)
    
    def can_handle(self, tool_name: str) -> bool:
        """检查工具是否有处理器"""
        return tool_name in self._tool_handlers
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        if tool_name not in self._tool_handlers:
            raise ValueError(f"No handler for tool: {tool_name}")
        
        handler = self._tool_handlers[tool_name]
        return await handler(**kwargs)


# 全局实例
_registry: Optional[SimplifiedToolRegistry] = None


def get_simplified_registry() -> SimplifiedToolRegistry:
    """获取精简工具注册表"""
    global _registry
    if _registry is None:
        _registry = SimplifiedToolRegistry()
    return _registry
