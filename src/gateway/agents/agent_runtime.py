"""
Agent Runtime - Agent 运行时

实现完整的 Agent Loop: Reason → Act → Observe
参考 OpenClaw 的 Agent 架构
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.services.logging_service import get_logger
from src.gateway.events.event_bus import EventBus, Event, EventType
from src.gateway.memory.session_memory import SessionMemory
from src.gateway.agents.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent 运行状态"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Agent 运行时配置"""
    # 模型配置
    model_provider: str = "deepseek"
    model_name: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # 工具配置
    max_tool_calls: int = 10
    tool_timeout: int = 30
    
    # 循环配置
    max_iterations: int = 10
    enable_thinking: bool = True
    
    # 记忆配置
    memory_enabled: bool = True
    context_window: int = 10  # 保留最近 N 轮对话


@dataclass
class AgentRequest:
    """Agent 请求"""
    user_input: str
    user_id: str
    session_id: str
    channel: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Agent 响应"""
    content: str
    status: AgentStatus
    tool_calls: List[Dict] = field(default_factory=list)
    thinking: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentRuntime:
    """
    Agent 运行时
    
    实现完整的 Agent Loop:
    1. 准备上下文 (Prepare Context)
    2. 思考 (Reason) - LLM 生成 Thought
    3. 行动 (Act) - 执行工具或回复
    4. 观察 (Observe) - 获取工具结果/用户反馈
    5. 循环回到步骤 2
    6. 返回最终响应
    """
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        event_bus: Optional[EventBus] = None
    ):
        self.config = config or AgentConfig()
        self.event_bus = event_bus or EventBus()
        
        # 状态
        self.status = AgentStatus.IDLE
        self._running = False
        
        # 核心组件
        self.llm_service = None  # 将在 start 中初始化
        self.tool_registry = {}  # 工具注册表
        self.memory_manager: Optional[SessionMemory] = None
        
        # Prompt 构建器
        self.prompt_builder = PromptBuilder()
        
        # 当前会话状态
        self._current_session: Dict[str, Any] = {}
        
        logger.info("AgentRuntime instance created")
    
    async def start(self):
        """启动 Agent 运行时"""
        if self._running:
            return
        
        logger.info("Starting AgentRuntime...")
        
        # 1. 初始化 LLM 服务
        await self._init_llm()
        
        # 2. 初始化记忆管理
        if self.config.memory_enabled:
            self.memory_manager = SessionMemory(
                context_window=self.config.context_window
            )
        
        # 3. 初始化工具
        await self._init_tools()
        
        self._running = True
        
        await self.event_bus.emit(Event(
            type=EventType.AGENT_STARTED,
            data={"config": self.config.__dict__}
        ))
        
        logger.info("AgentRuntime started")
    
    async def stop(self):
        """停止 Agent 运行时"""
        if not self._running:
            return
        
        self._running = False
        
        # 保存所有会话记忆
        if self.memory_manager:
            await self.memory_manager.save_all()
        
        logger.info("AgentRuntime stopped")
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        处理用户请求
        
        实现完整的 Agent Loop
        """
        if not self._running:
            raise RuntimeError("AgentRuntime not started")
        
        logger.info(f"Processing request for user {request.user_id}, session {request.session_id}")
        
        # 1. 准备上下文
        context = await self._prepare_context(request)
        
        # 2. Agent Loop
        iteration = 0
        thought_history = []
        
        while iteration < self.config.max_iterations:
            iteration += 1
            
            # 2.1 Reason (思考)
            thought = await self._reason(context, thought_history)
            thought_history.append(thought)
            
            # 检查是否需要行动
            if thought.get("action"):
                # 2.2 Act (行动)
                result = await self._act(thought, context)
                
                # 2.3 Observe (观察)
                await self._observe(thought, result, context)
                
                # 将结果加入上下文
                context["observation"] = result
            else:
                # 没有行动，直接完成
                break
        
        # 3. 生成最终响应
        response = await self._generate_response(context, thought_history)
        
        # 4. 保存记忆
        if self.memory_manager:
            await self.memory_manager.add_interaction(
                session_id=request.session_id,
                user_input=request.user_input,
                agent_response=response.content
            )
        
        return response
    
    async def _init_llm(self):
        """初始化 LLM 服务"""
        try:
            from src.core.llm_integration import LLMIntegration
            self.llm_service = LLMIntegration(config={})
            logger.info("LLM service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise
    
    async def _init_tools(self):
        """初始化工具"""
        # 从现有的 ToolRegistry 获取工具
        try:
            from src.agents.tools.tool_registry import ToolRegistry
            registry = ToolRegistry()
            self.tool_registry = registry.get_all_tools()
            logger.info(f"Initialized {len(self.tool_registry)} tools")
        except Exception as e:
            logger.warning(f"Failed to initialize tools: {e}")
    
    async def _prepare_context(self, request: AgentRequest) -> Dict[str, Any]:
        """准备上下文"""
        context = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "channel": request.channel,
            "user_input": request.user_input,
            "timestamp": datetime.now().isoformat(),
            **request.context
        }
        
        # 加载会话记忆
        if self.memory_manager:
            memory = await self.memory_manager.get_memory(request.session_id)
            context["memory"] = memory
        
        # 添加系统信息
        context["system"] = {
            "model": self.config.model_name,
            "max_iterations": self.config.max_iterations,
            "tools_available": list(self.tool_registry.keys())
        }
        
        return context
    
    async def _reason(
        self,
        context: Dict[str, Any],
        history: List[Dict]
    ) -> Dict[str, Any]:
        """Reason - LLM 生成思考"""
        self.status = AgentStatus.THINKING
        
        await self.event_bus.emit(Event(
            type=EventType.AGENT_THINKING,
            data={"session_id": context.get("session_id")}
        ))
        
        # 构建 prompt
        prompt = self.prompt_builder.build_reasoning_prompt(
            user_input=context.get("user_input", ""),
            memory=context.get("memory", []),
            tools=context.get("system", {}).get("tools_available", []),
            history=history,
            enable_thinking=self.config.enable_thinking
        )
        
        try:
            # 调用 LLM
            response = await asyncio.wait_for(
                self.llm_service._call_llm(prompt, max_tokens=self.config.max_tokens),
                timeout=self.config.tool_timeout
            )
            
            # 解析响应
            thought = self._parse_thought(response)
            
            logger.debug(f"Thought: {thought.get('thought', '')[:100]}...")
            
            return thought
            
        except asyncio.TimeoutError:
            return {"error": "LLM timeout", "action": None}
        except Exception as e:
            logger.error(f"Error in reasoning: {e}")
            return {"error": str(e), "action": None}
    
    async def _act(
        self,
        thought: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Act - 执行工具"""
        self.status = AgentStatus.ACTING
        
        action = thought.get("action")
        if not action:
            return {"type": "response", "content": thought.get("thought", "")}
        
        tool_name = action.get("tool")
        tool_args = action.get("args", {})
        
        await self.event_bus.emit(Event(
            type=EventType.AGENT_ACTING,
            data={
                "tool": tool_name,
                "args": tool_args,
                "session_id": context.get("session_id")
            }
        ))
        
        # 执行工具
        if tool_name in self.tool_registry:
            tool = self.tool_registry[tool_name]
            try:
                result = await asyncio.wait_for(
                    tool.execute(**tool_args),
                    timeout=self.config.tool_timeout
                )
                
                await self.event_bus.emit(Event(
                    type=EventType.TOOL_COMPLETED,
                    data={"tool": tool_name, "result_length": len(str(result))}
                ))
                
                return {"type": "tool", "tool": tool_name, "result": result}
                
            except asyncio.TimeoutError:
                return {"type": "tool", "tool": tool_name, "error": "Tool timeout"}
            except Exception as e:
                return {"type": "tool", "tool": tool_name, "error": str(e)}
        else:
            return {"type": "error", "error": f"Unknown tool: {tool_name}"}
    
    async def _observe(
        self,
        thought: Dict[str, Any],
        result: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """Observe - 观察结果"""
        self.status = AgentStatus.OBSERVING
        
        await self.event_bus.emit(Event(
            type=EventType.AGENT_OBSERVING,
            data={
                "result_type": result.get("type"),
                "session_id": context.get("session_id")
            }
        ))
    
    async def _generate_response(
        self,
        context: Dict[str, Any],
        history: List[Dict]
    ) -> AgentResponse:
        """生成最终响应"""
        self.status = AgentStatus.COMPLETED
        
        # 从历史中获取最后的思考
        last_thought = history[-1] if history else {}
        
        content = last_thought.get("thought", "")
        
        # 如果有观察结果，添加到响应中
        observation = context.get("observation", {})
        if observation.get("type") == "tool":
            content += f"\n\n[Tool: {observation.get('tool')}]\n{observation.get('result', '')}"
        
        # 收集所有工具调用
        tool_calls = [
            {"tool": h.get("action", {}).get("tool"), "args": h.get("action", {}).get("args")}
            for h in history
            if h.get("action")
        ]
        
        await self.event_bus.emit(Event(
            type=EventType.AGENT_COMPLETED,
            data={"response_length": len(content), "iterations": len(history)}
        ))
        
        return AgentResponse(
            content=content,
            status=self.status,
            tool_calls=tool_calls,
            thinking=last_thought.get("thinking", ""),
            metadata={"iterations": len(history)}
        )
    
    def _parse_thought(self, response: str) -> Dict[str, Any]:
        """
        解析 LLM 响应
        
        简化版本 - 实际应该用更复杂的解析
        """
        # 检查是否包含工具调用
        if "{" in response and "tool" in response.lower():
            # 尝试解析 JSON
            try:
                import json
                # 找到 JSON 块
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    action = json.loads(response[start:end])
                    return {
                        "thought": response[:start],
                        "action": action
                    }
            except:
                pass
        
        # 默认返回文本响应
        return {
            "thought": response,
            "action": None
        }
    
    # ==================== 工具管理 ====================
    
    def register_tool(self, name: str, tool: Any):
        """注册工具"""
        self.tool_registry[name] = tool
        logger.info(f"Tool registered: {name}")
    
    def unregister_tool(self, name: str):
        """注销工具"""
        if name in self.tool_registry:
            del self.tool_registry[name]
            logger.info(f"Tool unregistered: {name}")
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self.tool_registry.keys())
