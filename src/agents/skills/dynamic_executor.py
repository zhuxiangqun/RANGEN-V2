"""
动态 Skill 执行器 - 根据 SKILL.md 动态执行任务

原理：
- Skill 的执行逻辑不在硬编码
- AI 根据 SKILL.md 中的示例和说明自行理解如何执行
- 通过 ToolRegistry 调用底层工具
"""

import json
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.agents.skills.enhanced_registry import get_enhanced_skill_registry
from src.agents.tools.tool_registry import get_tool_registry


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    data: Any
    error: Optional[str] = None
    skill_used: str = ""
    tool_used: str = ""


class DynamicSkillExecutor:
    """
    动态 Skill 执行器
    
    根据 SKILL.md 中的说明，让 AI 理解如何执行任务。
    不需要为每个 Skill 编写硬编码。
    """
    
    def __init__(self):
        self.skill_registry = get_enhanced_skill_registry()
        self.tool_registry = get_tool_registry()
    
    def _extract_code_examples(self, skill_doc: str) -> List[str]:
        """从 SKILL.md 中提取代码示例"""
        examples = []
        
        # 匹配 ```python 或 ``` 包裹的代码块
        pattern = r'```(?:python)?\n(.*?)```'
        matches = re.findall(pattern, skill_doc, re.DOTALL)
        
        for match in matches:
            # 清理代码
            code = match.strip()
            if code and not code.startswith('#'):
                examples.append(code)
        
        return examples
    
    def _extract_tool_names(self, skill_doc: str) -> List[str]:
        """从 SKILL.md 中提取工具名称"""
        tools = []
        
        # 匹配 from xxx import yyy 或 import xxx
        import_pattern = r'from\s+(\S+)\s+import\s+(\S+)'
        import_matches = re.findall(import_pattern, skill_doc)
        
        for module, name in import_matches:
            tools.append(name)
        
        # 匹配工具调用 xxxTool() 或 xxx()
        tool_pattern = r'(\w+Tool|\w+Tool\()'
        tool_matches = re.findall(tool_pattern, skill_doc)
        
        tools.extend(tool_matches)
        
        return list(set(tools))
    
    def get_skill_context(self, skill_name: str) -> Dict[str, Any]:
        """获取 Skill 的完整上下文（供 AI 使用）"""
        
        # 获取元数据
        metadata = self.skill_registry.get_metadata(skill_name)
        if not metadata:
            return {"error": f"Skill '{skill_name}' not found"}
        
        # 获取文档
        docs = self.skill_registry.get_skill_documentation(skill_name) or ""
        
        # 提取代码示例
        examples = self._extract_code_examples(docs)
        
        # 提取工具名称
        tool_names = self._extract_tool_names(docs)
        
        # 获取可用工具
        available_tools = []
        for name in tool_names:
            tool = self.tool_registry.get_tool(name)
            if tool:
                available_tools.append({
                    "name": tool.tool_name,
                    "description": tool.description,
                    "schema": tool.get_parameters_schema() if hasattr(tool, 'get_parameters_schema') else {}
                })
        
        return {
            "skill_name": metadata.name,
            "description": metadata.description,
            "triggers": metadata.triggers,
            "tools": available_tools,
            "code_examples": examples[:3],  # 最多3个示例
            "documentation": docs[:2000],   # 截取文档
        }
    
    async def execute(
        self, 
        user_input: str, 
        skill_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        动态执行 Skill
        
        Args:
            user_input: 用户输入
            skill_name: Skill 名称
            params: 执行参数
            
        Returns:
            ExecutionResult: 执行结果
        """
        params = params or {}
        
        # 获取 Skill 上下文
        context = self.get_skill_context(skill_name)
        
        if "error" in context:
            return ExecutionResult(
                success=False,
                data=None,
                error=context["error"]
            )
        
        # 查找可用的 Tool
        tool_name = None
        for tool_info in context.get("tools", []):
            tool = self.tool_registry.get_tool(tool_info["name"])
            if tool:
                tool_name = tool_info["name"]
                break
        
        if not tool_name:
            # 尝试根据 Skill 名推断 Tool
            tool_name = skill_name.replace("-", "_")
            if not self.tool_registry.get_tool(tool_name):
                return ExecutionResult(
                    success=False,
                    data=None,
                    error=f"No available tool found for skill '{skill_name}'"
                )
        
        # 执行 Tool
        tool = self.tool_registry.get_tool(tool_name)
        
        try:
            # 提取查询参数
            query = params.get("query", user_input)
            
            # 调用工具
            result = await tool.call(
                query=query,
                **{k: v for k, v in params.items() if k != "query"}
            )
            
            return ExecutionResult(
                success=result.success,
                data=result.data,
                error=result.error,
                skill_used=skill_name,
                tool_used=tool_name
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                data=None,
                error=str(e),
                skill_used=skill_name,
                tool_used=tool_name
            )
    
    def get_execution_prompt(self, skill_name: str) -> str:
        """
        获取执行提示（供 LLM 使用）
        
        这个 prompt 可以直接发送给 LLM，让它理解如何执行任务
        """
        context = self.get_skill_context(skill_name)
        
        if "error" in context:
            return f"Error: {context['error']}"
        
        prompt = f"""# Skill: {context['skill_name']}

## 描述
{context['description']}

## 触发关键词
{', '.join(context['triggers'])}

## 可用工具
"""
        
        for tool in context.get("tools", []):
            prompt += f"\n### {tool['name']}\n{tool['description']}\n"
        
        if context.get("code_examples"):
            prompt += "\n## 代码示例\n"
            for i, example in enumerate(context["code_examples"], 1):
                prompt += f"\n示例 {i}:\n```python\n{example}\n```\n"
        
        prompt += f"""
## 执行指南
根据以上信息，理解用户请求并执行相应操作。
- 使用合适的工具
- 传入正确的参数
- 处理返回结果
"""
        
        return prompt


# 全局单例
_executor: Optional[DynamicSkillExecutor] = None


def get_dynamic_executor() -> DynamicSkillExecutor:
    """获取动态执行器"""
    global _executor
    if _executor is None:
        _executor = DynamicSkillExecutor()
    return _executor


# 便捷函数
async def execute_skill(
    user_input: str, 
    skill_name: str,
    **params
) -> ExecutionResult:
    """执行 Skill 的便捷函数"""
    executor = get_dynamic_executor()
    return await executor.execute(user_input, skill_name, params)


def get_skill_prompt(skill_name: str) -> str:
    """获取 Skill 执行提示"""
    executor = get_dynamic_executor()
    return executor.get_execution_prompt(skill_name)
