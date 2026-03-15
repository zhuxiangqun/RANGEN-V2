#!/usr/bin/env python3
"""
StrategicChiefAgent包装器 - 使用逐步替换策略

将StrategicChiefAgent的调用包装为使用逐步替换策略，实现平滑迁移到AgentCoordinator。
注意：StrategicChiefAgent不继承BaseAgent，是一个普通类。
"""

import logging
from typing import Dict, Any, Optional
from .strategic_chief_agent import StrategicChiefAgent
from .base_agent import BaseAgent
from ..adapters.strategic_chief_agent_adapter import StrategicChiefAgentAdapter
from ..strategies.gradual_replacement import GradualReplacementStrategy

logger = logging.getLogger(__name__)


class StrategicChiefAgentWrapper(BaseAgent):
    """StrategicChiefAgent包装器 - 使用逐步替换策略
    
    这个包装器实现了与StrategicChiefAgent相同的接口，但内部使用逐步替换策略
    将请求逐步从StrategicChiefAgent迁移到AgentCoordinator。
    """
    
    def __init__(self, enable_gradual_replacement: bool = True, initial_replacement_rate: float = 1.0):
        """
        初始化StrategicChiefAgent包装器
        
        Args:
            enable_gradual_replacement: 是否启用逐步替换
            initial_replacement_rate: 初始替换比例（默认1%）
        """
        # 初始化BaseAgent（保持兼容性）
        from .base_agent import AgentConfig
        config = AgentConfig(
            agent_id="strategic_chief_agent",
            agent_type="strategic_chief_agent_wrapper"
        )
        super().__init__(
            "strategic_chief_agent",
            ["coordination", "strategic_planning", "task_decomposition"],
            config
        )
        
        # 创建旧Agent实例（StrategicChiefAgent不继承BaseAgent）
        self.old_agent = StrategicChiefAgent()
        
        self.enable_gradual_replacement = enable_gradual_replacement
        self.replacement_strategy: Optional[GradualReplacementStrategy] = None
        
        if enable_gradual_replacement:
            try:
                # 创建适配器
                adapter = StrategicChiefAgentAdapter()
                new_agent = adapter.target_agent
                
                # 创建逐步替换策略
                self.replacement_strategy = GradualReplacementStrategy(
                    old_agent=self.old_agent,
                    new_agent=new_agent,
                    adapter=adapter
                )
                self.replacement_strategy.replacement_rate = 0.100
                
                logger.info(
                    f"✅ StrategicChiefAgent包装器初始化成功，逐步替换已启用 "
                    f"(初始替换比例: {initial_replacement_rate:.0%})"
                )
            except Exception as e:
                logger.warning(f"⚠️ 逐步替换策略初始化失败，将使用旧Agent: {e}")
                self.enable_gradual_replacement = False
                self.replacement_strategy = None
        else:
            logger.info("ℹ️ StrategicChiefAgent包装器初始化成功，逐步替换未启用")
    
    async def execute(self, context: Dict[str, Any]) -> Any:
        """
        执行任务 - 使用逐步替换策略
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        if self.enable_gradual_replacement and self.replacement_strategy:
            # 使用逐步替换策略
            try:
                result = await self.replacement_strategy.execute_with_gradual_replacement(context)
                return result
            except Exception as e:
                logger.error(f"❌ 逐步替换执行失败，回退到旧Agent: {e}")
                # 回退到旧Agent
                if hasattr(self.old_agent, 'decide_strategy'):
                    # StrategicChiefAgent使用decide_strategy方法
                    query_analysis = context.get('query_analysis')
                    system_state = context.get('system_state')
                    return await self.old_agent.decide_strategy(query_analysis, system_state)
                return {"success": False, "error": str(e)}
        else:
            # 直接使用旧Agent
            if hasattr(self.old_agent, 'decide_strategy'):
                query_analysis = context.get('query_analysis')
                system_state = context.get('system_state')
                return await self.old_agent.decide_strategy(query_analysis, system_state)
            return {"success": True, "data": None}
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        处理查询 - 实现BaseAgent的抽象方法
        
        Args:
            query: 查询文本
            context: 上下文信息（可选）
            
        Returns:
            AgentResult: 处理结果
        """
        # 准备上下文
        exec_context = {"query": query}
        if context:
            exec_context.update(context)
        
        # 使用同步包装异步execute方法
        import asyncio
        
        try:
            # 如果已有事件循环，使用它
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果循环正在运行，使用线程池执行
                import concurrent.futures
                def run_in_thread():
                    return asyncio.run(self.execute(exec_context))
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result()
            else:
                return loop.run_until_complete(self.execute(exec_context))
        except RuntimeError:
            # 没有事件循环，创建新的
            return asyncio.run(self.execute(exec_context))
    
    async def decide_strategy(self, query_analysis, system_state=None):
        """代理decide_strategy方法到old_agent"""
        return await self.old_agent.decide_strategy(query_analysis, system_state)
    
    def get_replacement_stats(self) -> Optional[Dict[str, Any]]:
        """获取替换统计信息"""
        if self.replacement_strategy:
            return self.replacement_strategy.get_replacement_stats()
        return None
    
    def increase_replacement_rate(self, step: float = 0.1) -> Optional[float]:
        """增加替换比例"""
        if self.replacement_strategy:
            return self.replacement_strategy.increase_replacement_rate(step)
        return None
    
    def should_increase_rate(self) -> bool:
        """判断是否应该增加替换比例"""
        if self.replacement_strategy:
            return self.replacement_strategy.should_increase_rate()
        return False

