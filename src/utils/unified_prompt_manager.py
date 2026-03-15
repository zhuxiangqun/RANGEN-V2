#!/usr/bin/env python3
"""
统一提示词管理器 - 提供统一的提示词管理接口，集成RL/ML优化和动态编排
"""
import logging
from typing import Dict, Any, Optional
from src.utils.prompt_engine import get_prompt_engine
from src.agents.prompt_engineering_agent_wrapper import PromptEngineeringAgentWrapper as PromptEngineeringAgent
from src.utils.prompt_orchestrator import get_prompt_orchestrator
from src.visualization.orchestration_tracker import get_orchestration_tracker

logger = logging.getLogger(__name__)

# 全局单例
_unified_prompt_manager = None


class UnifiedPromptManager:
    """统一提示词管理器 - 集成提示词工程、RL/ML优化和动态编排"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.prompt_engine = get_prompt_engine()
        self.prompt_agent = PromptEngineeringAgent(enable_gradual_replacement=True)
        # 🚀 新增：Prompt 动态编排器
        self.orchestrator = get_prompt_orchestrator()
        self._initialized = True
        self.logger.info("✅ UnifiedPromptManager 初始化完成（已集成动态编排）")
    
    async def get_prompt(
        self,
        prompt_type: str,        # 提示词类型（如 "list_extraction", "answer_generation"）
        query: str,
        context: Optional[Dict[str, Any]] = None,
        use_rl_optimization: bool = True,
        use_orchestration: bool = True  # 🚀 新增：是否使用动态编排（默认True）
    ) -> str:
        """获取优化的提示词（统一接口，支持动态编排）
        
        Args:
            prompt_type: 提示词类型
            query: 查询文本
            context: 上下文信息（可选）
            use_rl_optimization: 是否使用RL优化（默认True）
            use_orchestration: 是否使用动态编排（默认True）
            
        Returns:
            生成的提示词
        """
        try:
            context = context or {}
            
            # 🎯 编排追踪：提示词生成开始
            tracker = getattr(self, '_orchestration_tracker', None) or get_orchestration_tracker()
            prompt_event_id = None
            if tracker:
                prompt_event_id = tracker.track_prompt_generate(
                    prompt_type,
                    query[:200],  # 限制长度
                    context  # 此时 context 已经是 dict 了
                )
            
            # 🚀 新增：如果启用动态编排，优先使用编排器
            if use_orchestration:
                try:
                    # 根据 prompt_type 和 context 选择编排策略
                    orchestration_strategy = self._select_orchestration_strategy(
                        prompt_type, context
                    )
                    
                    # 🎯 编排追踪：传递追踪器到编排器
                    if tracker and hasattr(self.orchestrator, '_orchestration_tracker'):
                        setattr(self.orchestrator, '_orchestration_tracker', tracker)  # type: ignore
                    
                    # 使用编排器生成提示词
                    orchestrated_prompt = await self.orchestrator.orchestrate(
                        query=query,
                        context=context,
                        orchestration_strategy=orchestration_strategy
                    )
                    
                    if orchestrated_prompt:
                        self.logger.debug(f"✅ 使用动态编排生成提示词: 策略={orchestration_strategy}")
                        # 🎯 编排追踪：提示词生成完成
                        if tracker and prompt_event_id:
                            tracker.track_prompt_generate(
                                prompt_type,
                                orchestrated_prompt[:200],
                                context,
                                prompt_event_id
                            )
                        return orchestrated_prompt
                except Exception as e:
                    self.logger.warning(f"⚠️ 动态编排失败: {e}，回退到传统方法")
            
            # 1. 使用提示词工程智能体生成提示词
            # 🎯 编排追踪：传递追踪器到提示词智能体
            if tracker and hasattr(self.prompt_agent, '_orchestration_tracker'):
                setattr(self.prompt_agent, '_orchestration_tracker', tracker)  # type: ignore
            
            result = await self.prompt_agent.execute({
                "task_type": "generate_prompt",
                "template_name": prompt_type,
                "query": query,
                "query_type": context.get("query_type", "general"),
                "evidence": context.get("evidence"),
                "enhanced_context": context.get("enhanced_context", {})
            })
            
            if result.success and result.data:
                prompt = result.data.get("prompt")
                if prompt:
                    # 🎯 编排追踪：提示词生成完成
                    if tracker and prompt_event_id:
                        tracker.track_prompt_generate(
                            prompt_type,
                            prompt[:200],
                            context,
                            prompt_event_id
                        )
                    return prompt
            
            # 2. Fallback: 直接使用提示词引擎
            # 🎯 编排追踪：传递追踪器到提示词引擎
            if tracker and hasattr(self.prompt_engine, '_orchestration_tracker'):
                setattr(self.prompt_engine, '_orchestration_tracker', tracker)  # type: ignore
            
            prompt = self.prompt_engine.generate_prompt(
                template_name=prompt_type,
                query=query,
                **context
            )
            
            if prompt:
                # 🎯 编排追踪：提示词生成完成
                if tracker and prompt_event_id:
                    tracker.track_prompt_generate(
                        prompt_type,
                        prompt[:200],
                        context,
                        prompt_event_id
                    )
                return prompt
            
            # 3. 最后fallback: 使用编排器的简单策略
            try:
                simple_prompt = await self.orchestrator.orchestrate(
                    query=query,
                    context=context,
                    orchestration_strategy="simple"
                )
                if simple_prompt:
                    # 🎯 编排追踪：提示词生成完成
                    if tracker and prompt_event_id:
                        tracker.track_prompt_generate(
                            prompt_type,
                            simple_prompt[:200],
                            context,
                            prompt_event_id
                        )
                    return simple_prompt
            except Exception:
                pass
            
            # 4. 最终fallback: 返回简单提示词
            self.logger.warning(f"⚠️ 提示词模板不存在: {prompt_type}，使用fallback")
            fallback_prompt = f"请回答以下问题：\n\n{query}\n\n请提供准确、详细的答案。"
            # 🎯 编排追踪：提示词生成完成（fallback）
            if tracker and prompt_event_id:
                tracker.track_prompt_generate(
                    prompt_type,
                    fallback_prompt[:200],
                    context,
                    prompt_event_id
                )
            return fallback_prompt
            
        except Exception as e:
            self.logger.error(f"获取提示词失败: {e}", exc_info=True)
            # 返回最简单的fallback
            fallback_prompt = f"请回答以下问题：\n\n{query}\n\n请提供准确、详细的答案。"
            # 🎯 编排追踪：提示词生成失败
            if tracker and prompt_event_id:
                # 确保 context 是字典
                safe_context = context if isinstance(context, dict) else (context or {})
                tracker.track_prompt_generate(
                    prompt_type,
                    fallback_prompt[:200],
                    safe_context,
                    prompt_event_id
                )
            return fallback_prompt
    
    def _select_orchestration_strategy(
        self,
        prompt_type: str,
        context: Dict[str, Any]
    ) -> str:
        """根据提示词类型和上下文选择编排策略
        
        Args:
            prompt_type: 提示词类型
            context: 上下文信息
        
        Returns:
            编排策略名称
        """
        # 根据 prompt_type 选择策略
        strategy_mapping = {
            "reasoning_steps_generation": "reasoning_based",
            "reasoning_with_evidence": "evidence_based",
            "reasoning_without_evidence": "reasoning_based",
            "answer_generation": "default",
            "answer_extraction": "simple",
            "evidence_generation": "evidence_based",
            "query_type_classification": "simple",
        }
        
        # 首先尝试从映射中获取
        strategy = strategy_mapping.get(prompt_type, "default")
        
        # 根据上下文调整策略
        if context.get("evidence") or context.get("knowledge"):
            if strategy == "default":
                strategy = "evidence_based"
        elif context.get("enhanced_context") or context.get("context"):
            if strategy == "default":
                strategy = "context_rich"
        
        # 如果是多步骤推理
        if context.get("is_multi_step") or context.get("reasoning_steps"):
            strategy = "reasoning_based"
        
        # 如果查询类型是复杂的
        query_type = context.get("query_type", "general")
        if query_type in ["multi_hop", "complex"]:
            strategy = "reasoning_based"
        
        return strategy
    
    async def record_performance(
        self,
        prompt_type: str,
        template_name: str,
        query: str,
        answer_quality: float,
        response_time: float,
        cost: Optional[float] = None
    ):
        """记录提示词性能（用于RL学习）
        
        Args:
            prompt_type: 提示词类型
            template_name: 模板名称
            query: 查询文本
            answer_quality: 答案质量（0-1）
            response_time: 响应时间（秒）
            cost: 成本（token数，可选）
        """
        try:
            await self.prompt_agent.record_prompt_performance(
                prompt_type=prompt_type,
                template_name=template_name,
                query=query,
                answer_quality=answer_quality,
                response_time=response_time,
                cost=cost
            )
        except Exception as e:
            self.logger.error(f"记录提示词性能失败: {e}")


def get_unified_prompt_manager() -> UnifiedPromptManager:
    """获取统一提示词管理器实例（单例模式）"""
    global _unified_prompt_manager
    if _unified_prompt_manager is None:
        _unified_prompt_manager = UnifiedPromptManager()
    return _unified_prompt_manager

