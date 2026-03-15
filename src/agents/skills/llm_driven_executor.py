#!/usr/bin/env python3
"""
LLM 驱动的 Skill 执行器 - 完整版 (含工具调用)

改进版本：
- 即使没有匹配到 skill 也能继续执行
- 基于工具可用性让 LLM 决定是否调用工具
- 更灵活的 Prompt 构建
"""

import json
import re
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from src.agents.skills.enhanced_registry import get_enhanced_skill_registry
from src.agents.skills.skill_trigger import auto_trigger_skills


class ExecutionMode(Enum):
    LLM_DRIVEN = "llm_driven"
    TOOL_BASED = "tool_based"
    HYBRID = "hybrid"


class PromptStyle(Enum):
    SIMPLE = "simple"
    STRUCTURED = "structured"
    AUTO = "auto"


@dataclass
class LLMExecutionResult:
    success: bool
    content: str
    reasoning: str = ""
    tools_used: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    error: Optional[str] = None


class LLMSkillExecutor:
    """LLM 驱动的 Skill 执行器 - 完整版"""
    
    def __init__(self, execution_mode: ExecutionMode = ExecutionMode.LLM_DRIVEN,
                 prompt_style: PromptStyle = PromptStyle.AUTO):
        self.execution_mode = execution_mode
        self.prompt_style = prompt_style
        self.skill_registry = get_enhanced_skill_registry()
        self._llm_client = None
        self._hybrid_executor = None
    
    def _get_llm_client(self):
        if self._llm_client is None:
            try:
                # 加载环境变量
                from dotenv import load_dotenv
                load_dotenv()
                
                import os
                from src.core.llm_integration import LLMIntegration
                
                # 从环境变量获取配置
                provider = os.getenv('LLM_PROVIDER', 'deepseek')
                api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY')
                base_url = os.getenv('DEEPSEEK_BASE_URL') or os.getenv('OPENAI_BASE_URL')
                model = os.getenv('DEEPSEEK_MODEL') or os.getenv('OPENAI_MODEL')
                
                if not api_key:
                    raise ValueError("API key not found. Please set DEEPSEEK_API_KEY in .env")
                
                llm_config = {
                    "provider": provider,
                    "model": model or "deepseek-reasoner",
                    "api_key": api_key,
                    "base_url": base_url,
                }
                self._llm_client = LLMIntegration(llm_config)
            except Exception as e:
                print(f"LLM client init failed: {e}")
                return None
        return self._llm_client
    
    def _get_hybrid_executor(self):
        if self._hybrid_executor is None:
            try:
                from src.agents.skills.hybrid_tool_executor import get_hybrid_executor
                self._hybrid_executor = get_hybrid_executor()
            except Exception as e:
                print(f"Hybrid executor init failed: {e}")
                return None
        return self._hybrid_executor
    
    async def execute(self, user_input: str, skill_name: Optional[str] = None,
                      context: Optional[Dict[str, Any]] = None,
                      prompt_style: PromptStyle = PromptStyle.AUTO) -> LLMExecutionResult:
        """执行 Skill - 完整流程"""
        return await self._execute_with_tools(user_input, skill_name, context, prompt_style)
    
    async def _execute_with_tools(self, user_input: str, skill_name: Optional[str],
                                  context: Optional[Dict[str, Any]] = None,
                                  prompt_style: PromptStyle = PromptStyle.AUTO) -> LLMExecutionResult:
        context = context or {}
        
        # 1. 自动触发 Skill（可选，不强制要求）
        skill_fallback = False
        if skill_name is None:
            triggered = auto_trigger_skills(user_input)
            if triggered:
                skill_name = triggered[0]
            else:
                # 没有匹配到 skill，使用通用模式
                skill_fallback = True
                skill_name = "通用助手"
        
        # 2. 获取工具信息
        tools_info = self._get_tools_info()
        
        # 3. 构建 Prompt
        prompt = self._build_prompt_with_tools(user_input, skill_name, tools_info, context, skill_fallback)
        
        # 4. 获取 LLM
        llm_client = self._get_llm_client()
        if not llm_client:
            return LLMExecutionResult(success=False, content="", error="LLM 不可用")
        
        try:
            # 5. 调用 LLM - call_llm 是同步的
            response = llm_client.call_llm(prompt)
            content = response if isinstance(response, str) else str(response)
            
            # 6. 检测工具调用
            tool_call = self._detect_tool_call(content)
            
            if tool_call:
                # 7. 执行工具
                tool_result = await self._execute_tool(tool_call)
                
                if not tool_result.success:
                    return LLMExecutionResult(
                        success=False, content="",
                        error=tool_result.error or "Tool execution failed",
                        tools_used=[tool_call.get("tool", "")]
                    )
                
                # 8. 生成最终答案
                return await self._generate_final_answer(llm_client, user_input, tool_call, tool_result)
            else:
                # 没有工具调用，直接返回 LLM 回答
                return self._parse_llm_response(content)
            
        except Exception as e:
            return LLMExecutionResult(success=False, content="", error=str(e))
    
    def _get_tools_info(self) -> Dict[str, Any]:
        """获取所有可用工具信息"""
        try:
            executor = self._get_hybrid_executor()
            if executor:
                all_tools = executor.list_all_tools()
                tools_list = []
                for t in all_tools.get("internal", []):
                    tools_list.append({"name": t["name"], "description": t["description"], "source": "internal"})
                for t in all_tools.get("mcp", []):
                    tools_list.append({"name": t["name"], "description": t["description"], "source": "mcp"})
                return {"tools": tools_list, "count": len(tools_list)}
        except Exception:
            pass
        return {"tools": [], "count": 0}
    
    def _build_prompt_with_tools(self, user_input: str, skill_name: str,
                                  tools_info: Dict[str, Any], context: Dict[str, Any],
                                  skill_fallback: bool = False) -> str:
        """构建带工具信息的 Prompt"""
        
        # 如果是 fallback 模式，使用通用描述
        if skill_fallback:
            docs = "你是一个智能助手，可以调用各种工具来帮助用户完成请求。"
        else:
            docs = self.skill_registry.get_skill_documentation(skill_name) or ""
        
        # 构建工具描述
        tools_desc = ""
        if tools_info.get("tools"):
            tools_desc = "\n\n可用工具:\n"
            for tool in tools_info["tools"]:
                desc = tool.get('description', '')
                if len(desc) > 100:
                    desc = desc[:100] + "..."
                source = tool.get('source', 'unknown')
                tools_desc += f"- {tool['name']} [{source}]: {desc}\n"
        
        # 改进的提示词
        return f"""你是 {skill_name} 助手。

{docs}
{tools_desc}

用户请求: {user_input}

请分析请求并决定是否需要调用工具。

如果需要调用工具，请严格按以下JSON格式返回（不要有其他内容）：
{{"tool": "工具名", "parameters": {{工具参数}}, "reasoning": "为什么调用这个工具"}}

如果不需要工具，直接回答用户问题。"""
    
    def _detect_tool_call(self, content: str) -> Optional[Dict]:
        """检测工具调用 - 多种格式"""
        # 尝试标准 JSON 格式
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                if "tool" in data and "parameters" in data:
                    return data
        except Exception:
            pass
        
        # 尝试更灵活的格式
        try:
            # 匹配 "tool": "xxx" 或 "tool":"xxx"
            tool_match = re.search(r'["\']?tool["\']?\s*:\s*["\']?(\w+)["\']?', content)
            if tool_match:
                tool_name = tool_match.group(1)
                # 尝试找 parameters
                params_match = re.search(r'["\']?parameters["\']?\s*:\s*(\{[\s\S]*\})', content)
                if params_match:
                    params = json.loads(params_match.group(1))
                else:
                    params = {}
                return {"tool": tool_name, "parameters": params, "reasoning": "Detected from text"}
        except Exception:
            pass
        
        return None
    
    async def _execute_tool(self, tool_call: Dict) -> Any:
        """执行工具"""
        try:
            executor = self._get_hybrid_executor()
            if not executor:
                raise RuntimeError("Hybrid executor not available")
            
            return await executor.execute(
                tool_name=tool_call.get("tool", ""),
                parameters=tool_call.get("parameters", {}),
                tool_source=None
            )
        except Exception as e:
            from dataclasses import dataclass
            @dataclass
            class ErrorResult:
                success: bool = False
                result: Any = None
                error: str = ""
                source: Any = None
                tool_name: str = ""
                execution_time: float = 0.0
            return ErrorResult(error=str(e))
    
    async def _generate_final_answer(self, llm_client, user_input: str,
                                      tool_call: Dict, tool_result: Any) -> LLMExecutionResult:
        """生成最终答案"""
        tool_name = tool_call.get("tool", "")
        result_str = str(tool_result.result) if tool_result.result else str(tool_result.error)
        
        prompt = f"""用户请求: {user_input}

工具执行结果:
- 工具: {tool_name}
- 结果: {result_str}

请根据工具执行结果，给出最终答案。"""
        
        try:
            response = llm_client.call_llm(prompt)
            content = response if isinstance(response, str) else str(response)
            return LLMExecutionResult(
                success=True, content=content,
                reasoning=tool_call.get("reasoning", "Tool executed"),
                tools_used=[tool_name]
            )
        except Exception as e:
            return LLMExecutionResult(
                success=False, content=result_str,
                error=str(e)
            )
    
    def _parse_llm_response(self, content: str) -> LLMExecutionResult:
        """解析 LLM 响应"""
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result_data = json.loads(json_match.group())
                return LLMExecutionResult(
                    success=result_data.get("success", True),
                    content=result_data.get("content", content),
                    reasoning=result_data.get("reasoning", ""),
                    sources=result_data.get("sources", [])
                )
        except Exception:
            pass
        return LLMExecutionResult(success=True, content=content, reasoning="Direct response")


async def execute_skill(user_input: str, skill_name: Optional[str] = None,
                        mode: ExecutionMode = ExecutionMode.LLM_DRIVEN,
                        style: PromptStyle = PromptStyle.AUTO) -> LLMExecutionResult:
    """便捷执行函数"""
    executor = LLMSkillExecutor(execution_mode=mode, prompt_style=style)
    return await executor.execute(user_input, skill_name)


if __name__ == "__main__":
    import asyncio
    asyncio.run(execute_skill("计算 100 + 200"))
