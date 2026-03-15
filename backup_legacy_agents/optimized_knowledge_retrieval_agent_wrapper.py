#!/usr/bin/env python3
"""
OptimizedKnowledgeRetrievalAgent包装器 - 使用逐步替换策略

将OptimizedKnowledgeRetrievalAgent的调用包装为使用逐步替换策略，实现平滑迁移到RAGExpert。
注意：OptimizedKnowledgeRetrievalAgent不继承BaseAgent，是一个普通类。
"""

import logging
from typing import Dict, Any, Optional
from .optimized_knowledge_retrieval_agent import OptimizedKnowledgeRetrievalAgent
from .base_agent import BaseAgent
from ..adapters.optimized_knowledge_retrieval_agent_adapter import OptimizedKnowledgeRetrievalAgentAdapter
from ..strategies.gradual_replacement import GradualReplacementStrategy

logger = logging.getLogger(__name__)


class OptimizedKnowledgeRetrievalAgentWrapper(BaseAgent):
    """OptimizedKnowledgeRetrievalAgent包装器 - 使用逐步替换策略
    
    这个包装器实现了与OptimizedKnowledgeRetrievalAgent相同的接口，但内部使用逐步替换策略
    将请求逐步从OptimizedKnowledgeRetrievalAgent迁移到RAGExpert。
    """
    
    def __init__(self, enable_gradual_replacement: bool = True, initial_replacement_rate: float = 1.0):
        """
        初始化OptimizedKnowledgeRetrievalAgent包装器
        
        Args:
            enable_gradual_replacement: 是否启用逐步替换
            initial_replacement_rate: 初始替换比例（默认1%）
        """
        # 初始化BaseAgent（保持兼容性）
        from .base_agent import AgentConfig
        config = AgentConfig(
            agent_id="optimized_knowledge_retrieval_agent",
            agent_type="optimized_knowledge_retrieval_agent_wrapper"
        )
        super().__init__("optimized_knowledge_retrieval_agent", ["knowledge_retrieval", "rag"], config)
        
        # 创建旧Agent实例（OptimizedKnowledgeRetrievalAgent不继承BaseAgent）
        self.old_agent = OptimizedKnowledgeRetrievalAgent()
        
        self.enable_gradual_replacement = enable_gradual_replacement
        self.replacement_strategy: Optional[GradualReplacementStrategy] = None
        
        if enable_gradual_replacement:
            try:
                # 创建适配器
                adapter = OptimizedKnowledgeRetrievalAgentAdapter()
                new_agent = adapter.target_agent
                
                # 创建逐步替换策略
                self.replacement_strategy = GradualReplacementStrategy(
                    old_agent=self.old_agent,
                    new_agent=new_agent,
                    adapter=adapter
                )
                self.replacement_strategy.replacement_rate = 0.100
                
                logger.info(
                    f"✅ OptimizedKnowledgeRetrievalAgent包装器初始化成功，逐步替换已启用 "
                    f"(初始替换比例: {initial_replacement_rate:.0%})"
                )
            except Exception as e:
                logger.warning(f"⚠️ 逐步替换策略初始化失败，将使用旧Agent: {e}")
                self.enable_gradual_replacement = False
                self.replacement_strategy = None
        else:
            logger.info("ℹ️ OptimizedKnowledgeRetrievalAgent包装器初始化成功，逐步替换未启用")
    
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
                return {"success": False, "error": str(e)}
        else:
            # 直接使用旧Agent
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
    
    # 代理其他常用方法到old_agent，保持兼容性
    def process_data(self, data: Any) -> Any:
        """处理数据（代理到old_agent）"""
        return self.old_agent.process_data(data)
    
    def validate(self, data: Any) -> bool:
        """验证数据（代理到old_agent）"""
        return self.old_agent.validate(data)

