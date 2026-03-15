#!/usr/bin/env python3
"""
LangGraph ReAct Agent Wrapper

为 LangGraph 工作流提供 ReAct Agent 接口。

使用场景:
- 需要与现有 LangGraph 工作流集成
- 自定义 LangGraph 节点开发
- 复杂状态管理需求

与 ExecutionCoordinator 的区别:
- ExecutionCoordinator: 完整封装，内部管理状态
- LangGraphReActAgent: 提供底层接口，更灵活
"""

import logging
"""
LangGraph ReAct Agent Wrapper

⚠️ DEPRECATED: 此模块已不再维护。
LangGraph 集成已移至 src/core/ExecutionCoordinator。

为 LangGraph 工作流提供 ReAct Agent 接口
"""

import warnings
warnings.warn(
    "LangGraphReActAgent is deprecated. Use src.core.ExecutionCoordinator instead.",
    DeprecationWarning,
    stacklevel=2
)

import logging
"""
LangGraph ReAct Agent Wrapper
为 LangGraph 工作流提供 ReAct Agent 接口
"""

import logging
from typing import Dict, Any, Optional

from src.agents.react_agent import ReActAgent

logger = logging.getLogger(__name__)


class LangGraphReActAgent:
    """
    LangGraph ReAct Agent - 使用 LangGraph 封装的 ReAct Agent
    提供与 LangGraph 工作流兼容的接口
    """
    
    def __init__(self, agent_name: str = "LangGraphReActAgent", **kwargs):
        """
        初始化 LangGraph ReAct Agent
        
        Args:
            agent_name: Agent 名称
            **kwargs: 其他配置参数
        """
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
        
        # 内部使用 ReAct Agent
        self._react_agent = ReActAgent(
            agent_name=agent_name,
            use_intelligent_config=True
        )
        
        # LangGraph 工作流属性
        self._react_agent = ReActAgent(
            agent_name=agent_name,
            use_intelligent_config=True
        )
        self._react_agent = ReActAgent(
            agent_id=agent_name,
            agent_type="react",
            capabilities_dict=kwargs.get('capabilities', {})
        )
        
        # LangGraph 工作流属性
        self.workflow = None
        
        self.logger.info(f"✅ LangGraphReActAgent 初始化完成: {agent_name}")
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 Agent 推理
        
        Args:
            context: 包含查询和状态的上下文
            
        Returns:
            执行结果
        """
        query = context.get("query", "")
        
        try:
            # 使用内部 ReAct Agent 执行
            result = await self._react_agent.execute(query)
            
            if result.success:
                return {
                    "success": True,
                    "result": result.data,
                    "agent_name": self.agent_name
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "agent_name": self.agent_name
                }
        except Exception as e:
            self.logger.error(f"❌ LangGraphReActAgent 执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_name": self.agent_name
            }
    
    def get_state(self) -> Dict[str, Any]:
        """获取 Agent 状态"""
        return {
            "agent_name": self.agent_name,
            "status": "ready"
        }
