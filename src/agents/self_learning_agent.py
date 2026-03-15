#!/usr/bin/env python3
"""
Self-Learning Integrated Agent
=============================

将自我学习系统集成到Agent中。

功能:
- 自动工具选择学习
- 自动执行策略学习  
- 自动上下文管理学习
- 自动技能触发学习

使用场景:
- 需要持续优化的生产系统
- 复杂任务的自适应处理
- 个性化学习用户习惯

使用方式:
    agent = SelfLearningReActAgent("my_agent")
    result = await agent.execute({"query": "搜索AI新闻"})

注意: EnhancedExecutionCoordinator 也内置了自学习支持，可根据需求选择
"""

import time
"""
Self-Learning Integrated Agent
=============================

⚠️ DEPRECATED: 此模块已不再维护。
请使用 src.core.enhanced_execution_coordinator 代替 (已内置自学习支持)。

将自我学习系统集成到Agent中

功能:
- 自动工具选择学习
- 自动执行策略学习  
- 自动上下文管理学习
- 自动技能触发学习

使用方式:
    agent = SelfLearningReActAgent("my_agent")
    result = await agent.execute({"query": "搜索AI新闻"})
"""

import warnings
warnings.warn(
    "SelfLearningAgent is deprecated. Use EnhancedExecutionCoordinator instead.",
    DeprecationWarning,
    stacklevel=2
)

import time
"""
Self-Learning Integrated Agent
=============================

将自我学习系统集成到Agent中

功能:
- 自动工具选择学习
- 自动执行策略学习  
- 自动上下文管理学习
- 自动技能触发学习

使用方式:
    agent = SelfLearningReActAgent("my_agent")
    result = await agent.execute({"query": "搜索AI新闻"})
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..agents.react_agent import ReActAgent
from ..agents.base_agent import AgentResult, AgentConfig
from ..agents.tools.tool_registry import get_tool_registry

from src.core.self_learning import (
    get_tool_selection_learner,
    get_execution_strategy_learner,
    get_context_management_learner,
    get_skill_trigger_learner,
    TaskContext,
    TaskCategory,
    TaskComplexity,
    TaskFeatures,
    StrategyType,
    StrategyOutcome,
    UsageOutcome
)
from src.core.events import (
    create_event_stream,
    EventType
)

logger = logging.getLogger(__name__)


class SelfLearningReActAgent(ReActAgent):
    """
    自我学习ReAct Agent
    
    在执行过程中自动学习并优化:
    - 工具选择
    - 执行策略
    - 上下文管理
    - 技能触发
    """
    
    def __init__(
        self,
        agent_name: str = "SelfLearningAgent",
        use_intelligent_config: bool = True,
        enable_learning: bool = True
    ):
        """
        初始化自我学习Agent
        
        Args:
            agent_name: Agent名称
            use_intelligent_config: 使用智能配置
            enable_learning: 启用学习功能
        """
        super().__init__(agent_name, use_intelligent_config)
        
        # 学习功能开关
        self.enable_learning = enable_learning
        
        if not enable_learning:
            logger.info(f"{agent_name}: Learning disabled")
            return
        
        # 初始化学习器
        self._init_learning_components()
        
        # 事件流
        self._event_stream = None
        
        # 统计
        self._learning_stats = {
            "tools_learned": 0,
            "strategies_learned": 0,
            "context_items_learned": 0,
            "skill_triggers_learned": 0
        }
        
        logger.info(f"✅ SelfLearningReActAgent initialized: {agent_name}")
    
    def _init_learning_components(self):
        """初始化学习组件"""
        try:
            # 工具选择学习器
            self.tool_learner = get_tool_selection_learner()
            
            # 执行策略学习器
            self.strategy_learner = get_execution_strategy_learner()
            
            # 上下文管理学习器
            self.context_learner = get_context_management_learner()
            
            # 技能触发学习器
            self.skill_learner = get_skill_trigger_learner()
            
            logger.info("✅ Learning components initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize learning: {e}")
            self.enable_learning = False
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        执行任务（带学习功能）
        
        Args:
            context: 上下文，包含query字段
            
        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()
        query = context.get('query', '')
        
        # 发送开始事件
        await self._emit_learning_event(
            EventType.AGENT_START,
            f"开始执行: {query[:50]}..."
        )
        
        if not self.enable_learning:
            # 不启用学习，直接调用父类方法
            return await super().execute(context)
        
        try:
            # ===== 第一步：学习预测最佳工具 =====
            task_context = TaskContext.from_query(query, context)
            
            # 获取可用工具
            available_tools = self.tool_registry.list_tools()
            tool_names = [t['name'] for t in available_tools]
            
            # 预测最佳工具
            predicted_tool, tool_scores = self.tool_learner.predict_best_tool(
                task_context=task_context,
                available_tools=tool_names
            )
            
            await self._emit_learning_event(
                EventType.AGENT_THINKING,
                f"预测工具: {predicted_tool}, 分数: {tool_scores}"
            )
            
            # ===== 第二步：学习预测最佳策略 =====
            task_features = TaskFeatures.from_query(query, context)
            
            predicted_strategy, strategy_scores = self.strategy_learner.predict_best_strategy(
                task_features=task_features
            )
            
            await self._emit_learning_event(
                EventType.AGENT_THINKING,
                f"预测策略: {predicted_strategy}, 分数: {strategy_scores}"
            )
            
            # ===== 第三步：获取重要上下文 =====
            context_keywords = self._extract_keywords(query)
            important_context = self.context_learner.get_important_context(
                context_keywords=context_keywords
            )
            
            # 将重要上下文添加到执行上下文
            if important_context:
                context['learned_context'] = [
                    item.content for item in important_context[:5]
                ]
            
            # ===== 第四步：执行任务 (调用父类) =====
            result = await super().execute(context)
            
            # ===== 第五步：从结果学习 =====
            await self._learn_from_result(
                query=query,
                context=context,
                task_context=task_context,
                task_features=task_features,
                result=result,
                execution_time=time.time() - start_time,
                tool_used=context.get('tool_used', None),
                strategy_used=predicted_strategy
            )
            
            # 添加学习统计到结果
            if result.metadata:
                result.metadata['learning_stats'] = self._learning_stats
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Execution failed: {e}", exc_info=True)
            
            await self._emit_learning_event(
                EventType.AGENT_ERROR,
                f"执行失败: {str(e)}"
            )
            
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _learn_from_result(
        self,
        query: str,
        context: Dict[str, Any],
        task_context: TaskContext,
        task_features: TaskFeatures,
        result: AgentResult,
        execution_time: float,
        tool_used: Optional[str],
        strategy_used: Optional[StrategyType]
    ):
        """从执行结果学习"""
        
        # 判断成功与否
        success = result.success
        quality_score = result.confidence
        
        # ===== 1. 学习工具选择 =====
        if tool_used:
            self.tool_learner.record_usage(
                tool_name=tool_used,
                task_context=task_context,
                success=success,
                quality_score=quality_score,
                execution_time=execution_time
            )
            self._learning_stats['tools_learned'] += 1
        
        # ===== 2. 学习执行策略 =====
        if strategy_used:
            outcome = StrategyOutcome(
                success=success,
                quality_score=quality_score,
                execution_time=execution_time,
                iterations=result.metadata.get('react_iterations', 0) if result.metadata else 0,
                tool_calls=len(result.metadata.get('tools_used', [])) if result.metadata else 0
            )
            
            self.strategy_learner.record_execution(
                task_features=task_features,
                strategy=strategy_used,
                outcome=outcome
            )
            self._learning_stats['strategies_learned'] += 1
        
        # ===== 3. 学习上下文管理 =====
        # 记录哪些上下文被使用
        learned_context = context.get('learned_context', [])
        for ctx_content in learned_context:
            # 记录使用结果
            usage_outcome = UsageOutcome(
                item_used=True,
                useful=success,
                quality_improvement=quality_score * 0.2
            )
            
            # 创建上下文项ID
            ctx_id = f"ctx_{hash(ctx_content) % 100000}"
            
            # 添加上下文项（如果不存在）
            self.context_learner.add_context_item(
                item_id=ctx_id,
                content=ctx_content,
                base_importance=0.6,
                keywords=self._extract_keywords(ctx_content)
            )
            
            self._learning_stats['context_items_learned'] += 1
        
        # ===== 4. 学习技能触发 =====
        # 如果使用了技能，记录触发结果
        skill_used = context.get('skill_used')
        if skill_used:
            # 注册并记录技能触发
            if not hasattr(self.skill_learner, '_skill_performance') or \
               skill_used not in self.skill_learner._skill_performance:
                self.skill_learner.register_skill(skill_used)
            
            self.skill_learner.record_trigger(
                skill_name=skill_used,
                trigger_condition=type('TriggerCondition', (), {
                    'keywords': self._extract_keywords(query)
                })(),
                query=query,
                context=context,
                success=success,
                quality_score=quality_score,
                execution_time=execution_time
            )
            self._learning_stats['skill_triggers_learned'] += 1
        
        await self._emit_learning_event(
            EventType.AGENT_COMPLETE,
            f"学习完成: tools={self._learning_stats['tools_learned']}, "
            f"strategies={self._learning_stats['strategies_learned']}"
        )
        
        logger.info(f"✅ Learned from result: {self._learning_stats}")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单关键词提取
        import re
        
        # 中文分词（简单实现）
        chinese_words = re.findall(r'[\u4e00-\u9fa5]+', text)
        
        # 英文单词
        english_words = re.findall(r'[a-zA-Z]+', text)
        
        # 合并并去重
        keywords = list(set(chinese_words + english_words))
        
        # 过滤太短的词
        keywords = [k for k in keywords if len(k) >= 2]
        
        return keywords[:10]  # 最多10个
    
    async def _emit_learning_event(self, event_type: EventType, content: str):
        """发送学习事件"""
        if self._event_stream:
            await self._event_stream.emit_simple(
                event_type=event_type,
                content=content,
                agent_id=self.agent_id
            )
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        stats = {
            "learning_enabled": self.enable_learning,
            "learning_stats": self._learning_stats
        }
        
        if self.enable_learning:
            stats["tool_learner"] = self.tool_learner.get_statistics()
            stats["strategy_learner"] = self.strategy_learner.get_statistics()
            stats["context_learner"] = self.context_learner.get_statistics()
            stats["skill_learner"] = self.skill_learner.get_statistics()
        
        return stats
    
    def export_learning_knowledge(self, directory: str = "data/learning"):
        """导出学习到的知识"""
        import os
        os.makedirs(directory, exist_ok=True)
        
        if self.enable_learning:
            self.tool_learner.export_knowledge(f"{directory}/tool_selection.json")
            self.strategy_learner.export_knowledge(f"{directory}/execution_strategy.json")
            self.context_learner.export_knowledge(f"{directory}/context_management.json")
            self.skill_learner.export_knowledge(f"{directory}/skill_trigger.json")
            
            logger.info(f"✅ Exported learning knowledge to {directory}")
    
    def import_learning_knowledge(self, directory: str = "data/learning"):
        """导入学习到的知识"""
        import os
        path_exists = os.path.exists(directory)
        
        if path_exists and self.enable_learning:
            try:
                self.tool_learner.import_knowledge(f"{directory}/tool_selection.json")
                self.strategy_learner.import_knowledge(f"{directory}/execution_strategy.json")
                self.context_learner.import_knowledge(f"{directory}/context_management.json")
                self.skill_learner.import_knowledge(f"{directory}/skill_trigger.json")
                
                logger.info(f"✅ Imported learning knowledge from {directory}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to import knowledge: {e}")


def create_self_learning_agent(
    agent_name: str = "SelfLearningAgent",
    enable_learning: bool = True
) -> SelfLearningReActAgent:
    """
    创建自我学习Agent的便捷函数
    
    Args:
        agent_name: Agent名称
        enable_learning: 启用学习
        
    Returns:
        SelfLearningReActAgent实例
    """
    return SelfLearningReActAgent(
        agent_name=agent_name,
        enable_learning=enable_learning
    )
