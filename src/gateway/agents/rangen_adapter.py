"""
RANGEN Agent Adapter - 将现有 RANGEN Agents 集成到 Gateway

ChiefAgent 和 ReActAgent 的适配器
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.services.logging_service import get_logger
from src.gateway.agents.agent_runtime import AgentRuntime, AgentConfig, AgentRequest, AgentResponse, AgentStatus

logger = get_logger(__name__)


class RANGENAgentAdapter:
    """
    RANGEN Agent 适配器
    
    将现有的 ChiefAgent 和 ReActAgent 适配到 Gateway 的 AgentRuntime
    """
    
    def __init__(self):
        self.chief_agent = None
        self.react_agent = None
        self._initialized = False
    
    async def initialize(self):
        """初始化 RANGEN Agents"""
        if self._initialized:
            return
        
        logger.info("Initializing RANGEN Agents...")
        
        # 1. 初始化 ChiefAgent (协调者)，默认注册一名专家以便具备执行能力
        try:
            from src.agents.chief_agent import ChiefAgent
            import os
            register_experts = os.getenv("RANGEN_CHIEF_REGISTER_DEFAULT_EXPERTS", "1").strip().lower() in ("1", "true", "yes")
            self.chief_agent = ChiefAgent(register_default_experts=register_experts)
            logger.info("ChiefAgent initialized (register_default_experts=%s)", register_experts)
        except Exception as e:
            logger.error(f"Failed to initialize ChiefAgent: {e}")
        
        # 2. 初始化 ReActAgent (执行者)
        try:
            from src.agents.react_agent import ReActAgent
            self.react_agent = ReActAgent(agent_name="GatewayReActAgent")
            logger.info("ReActAgent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ReActAgent: {e}")
        
        self._initialized = True
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        处理请求
        
        使用 ChiefAgent 进行任务分解，然后用 ReActAgent 执行
        """
        if not self._initialized:
            await self.initialize()
        
        user_input = request.user_input
        context = request.context or {}
        
        # 根据任务复杂度选择合适的 Agent
        # 简单任务直接用 ReActAgent
        # 复杂任务用 ChiefAgent 分解
        
        try:
            # 首先尝试用 ChiefAgent 分析任务
            if self.chief_agent:
                result = await self._process_with_chief(user_input, context)
            else:
                # 备用：用 ReActAgent
                result = await self._process_with_react(user_input, context)
            
            return AgentResponse(
                content=result["content"],
                status=AgentStatus.COMPLETED,
                tool_calls=result.get("tool_calls", []),
                metadata=result.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return AgentResponse(
                content=f"Error: {str(e)}",
                status=AgentStatus.ERROR,
                tool_calls=[],
                metadata={"error": str(e)}
            )
    
    async def _process_with_chief(self, user_input: str, context: Dict) -> Dict[str, Any]:
        """使用 ChiefAgent 处理"""
        logger.debug(f"Processing with ChiefAgent: {user_input[:50]}...")
        
        # ChiefAgent 是同步的，需要在线程池中运行
        loop = asyncio.get_event_loop()
        
        def sync_process():
            result = self.chief_agent.process_query(
                query=user_input,
                context=context
            )
            return result
        
        result = await loop.run_in_executor(None, sync_process)
        
        # 转换结果
        content = result.answer if hasattr(result, 'answer') else str(result)
        
        return {
            "content": content,
            "tool_calls": [],
            "metadata": {"agent": "chief_agent"}
        }
    
    async def _process_with_react(self, user_input: str, context: Dict) -> Dict[str, Any]:
        """使用 ReActAgent 处理"""
        logger.debug(f"Processing with ReActAgent: {user_input[:50]}...")
        
        # ReActAgent 是同步的
        loop = asyncio.get_event_loop()
        
        def sync_process():
            result = self.react_agent.process_query(
                query=user_input,
                context=context
            )
            return result
        
        result = await loop.run_in_executor(None, sync_process)
        
        # 转换结果
        content = result.answer if hasattr(result, 'answer') else str(result)
        
        return {
            "content": content,
            "tool_calls": [],
            "metadata": {"agent": "react_agent"}
        }
    
    def get_available_agents(self) -> List[str]:
        """获取可用的 Agents"""
        agents = []
        if self.chief_agent:
            agents.append("chief_agent")
        if self.react_agent:
            agents.append("react_agent")
        return agents


class GatewayAgentRuntime(AgentRuntime):
    """
    Gateway Agent 运行时 - 使用 RANGEN 现有的 Agents
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config)
        
        # RANGEN Agent 适配器
        self.rangen_adapter = RANGENAgentAdapter()
    
    async def start(self):
        """启动运行时"""
        await super().start()
        
        # 初始化 RANGEN Agents
        await self.rangen_adapter.initialize()
        
        logger.info("GatewayAgentRuntime started with RANGEN Agents")
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """处理请求 - 使用 RANGEN Agents"""
        
        # 加载记忆
        if self.memory_manager:
            memory = await self.memory_manager.get_memory(request.session_id)
            request.context = request.context or {}
            request.context["memory"] = memory
        
        # 使用 RANGEN Agent 处理
        response = await self.rangen_adapter.process(request)
        
        # 保存记忆
        if self.memory_manager and response.status == AgentStatus.COMPLETED:
            await self.memory_manager.add_interaction(
                session_id=request.session_id,
                user_input=request.user_input,
                agent_response=response.content
            )
        
        return response
