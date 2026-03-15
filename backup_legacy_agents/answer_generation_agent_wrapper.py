#!/usr/bin/env python3
"""
AnswerGenerationAgent包装器 - 使用逐步替换策略

将AnswerGenerationAgent的调用包装为使用逐步替换策略，实现平滑迁移到RAGExpert。
注意：RAGExpert包含知识检索和答案生成功能，而AnswerGenerationAgent只做答案生成。
适配器将只使用RAGExpert的答案生成部分。
"""

import logging
from typing import Dict, Any, Optional
from backup_legacy_agents.expert_agents import AnswerGenerationAgent
from backup_legacy_agents.base_agent import BaseAgent
from src.adapters.answer_generation_agent_adapter import AnswerGenerationAgentAdapter
from src.strategies.gradual_replacement import GradualReplacementStrategy

logger = logging.getLogger(__name__)


class AnswerGenerationAgentWrapper(BaseAgent):
    """AnswerGenerationAgent包装器 - 使用逐步替换策略
    
    这个包装器实现了与AnswerGenerationAgent相同的接口，但内部使用逐步替换策略
    将请求逐步从AnswerGenerationAgent迁移到RAGExpert（答案生成部分）。
    """
    
    def __init__(self, enable_gradual_replacement: bool = True, initial_replacement_rate: float = 1.0):
        """
        初始化AnswerGenerationAgent包装器
        
        Args:
            enable_gradual_replacement: 是否启用逐步替换
            initial_replacement_rate: 初始替换比例（默认1%）
        """
        # 初始化BaseAgent（保持兼容性）
        from backup_legacy_agents.base_agent import AgentConfig
        config = AgentConfig(
            agent_id="answer_generation_expert",
            agent_type="answer_generation_agent_wrapper"
        )
        super().__init__("answer_generation_expert", ["answer_generation", "rag"], config)
        
        # 创建旧Agent实例
        self.old_agent = AnswerGenerationAgent()
        
        self.enable_gradual_replacement = enable_gradual_replacement
        self.replacement_strategy: Optional[GradualReplacementStrategy] = None
        
        if enable_gradual_replacement:
            try:
                # 创建适配器
                adapter = AnswerGenerationAgentAdapter()
                new_agent = adapter.target_agent
                
                # 创建逐步替换策略
                self.replacement_strategy = GradualReplacementStrategy(
                    old_agent=self.old_agent,
                    new_agent=new_agent,
                    adapter=adapter
                )
                self.replacement_strategy.replacement_rate = max(initial_replacement_rate, 0.100)  # 确保至少3.5%
                
                logger.info(
                    f"✅ AnswerGenerationAgent包装器初始化成功，逐步替换已启用 "
                    f"(初始替换比例: {initial_replacement_rate:.0%})"
                )
            except Exception as e:
                logger.warning(f"⚠️ 逐步替换策略初始化失败，将使用旧Agent: {e}")
                self.enable_gradual_replacement = False
                self.replacement_strategy = None
        else:
            logger.info("ℹ️ AnswerGenerationAgent包装器初始化成功，逐步替换未启用")
    
    async def execute(self, context: Dict[str, Any]) -> Any:
        from src.agents.base_agent import AgentResult
        result: Any
        if self.enable_gradual_replacement and self.replacement_strategy:
            try:
                result = await self.replacement_strategy.execute_with_gradual_replacement(context)
            except Exception as e:
                logger.error(f"❌ 逐步替换执行失败，回退到旧Agent: {e}")
                result = await self.old_agent.execute(context)
        else:
            result = await self.old_agent.execute(context)
        if isinstance(result, AgentResult):
            return result
        if isinstance(result, dict):
            return AgentResult(
                success=result.get("success", False),
                data=result.get("data"),
                confidence=result.get("confidence", 0.0),
                processing_time=result.get("processing_time", 0.0),
                metadata=result.get("metadata"),
                error=result.get("error"),
            )
        return AgentResult(
            success=True,
            data=result,
            confidence=0.0,
            processing_time=0.0,
            metadata=None,
            error=None,
        )
    
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
    @property
    def service(self):
        """服务（代理到old_agent）"""
        return self.old_agent.service
    
    def _get_service(self):
        """获取服务（代理到old_agent）"""
        return self.old_agent._get_service()
