#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强智能模型路由器 - 集成Paperclip优化组件

这个路由器集成了以下优化组件：
1. 声明式配置系统 - 通过装饰器注册模型和策略
2. 处理器链模式 - 模块化的路由决策流程
3. 统一存储抽象 - 配置持久化
4. 增强事件系统 - 路由决策监控
5. 增强验证系统 - 配置验证

设计原则：
- 向后兼容：保持原有API不变
- 渐进式增强：新功能可选择性启用
- 可观察性：完整的事件追踪和指标收集
"""

import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading

# 导入优化组件
from src.core.declarative_config import (
    register_llm_model, register_routing_strategy, register_processor,
    get_config_registry, on_event
)
from src.core.processor_chain import (
    ProcessorChain, BaseProcessor, ProcessingContext,
    ProcessorResult, InputValidatorProcessor,
    CostOptimizerProcessor, PerformanceEvaluatorProcessor,
    ABTestingProcessor, CircuitBreakerProcessor, FinalSelectorProcessor
)
from src.core.storage_abstraction import (
    StorageFactory, get_default_storage
)
from src.core.event_system import (
    get_event_bus, EventTypes, EventMetadata,
    ConfigRegisteredEvent, ModelSelectedEvent, RoutingDecisionEvent,
    event_subscriber, on_routing_decision
)
from src.core.validation_system import (
    get_llm_model_validator, ValidationResult
)

logger = logging.getLogger(__name__)


# ============================================================================
# 原有类型的重新导出（保持兼容性）
# ============================================================================

class TaskType(str, Enum):
    """任务类型（保持兼容）"""
    GENERAL = "general"
    REASONING = "reasoning"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    CODE_GENERATION = "code_generation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    EMBEDDING = "embedding"


@dataclass
class TaskContext:
    """任务上下文（保持兼容）"""
    task_type: TaskType
    estimated_tokens: int
    priority: int = 5
    deadline_ms: Optional[int] = None
    user_preference: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """路由决策（保持兼容）"""
    selected_model: str
    alternative_models: List[str]
    predicted_performance: Any  # 简化，原为ModelPerformancePrediction
    reasoning: List[str]
    timestamp: float = field(default_factory=time.time)


# ============================================================================
# 声明式配置注册
# ============================================================================

# 注册DeepSeek模型（符合用户要求）
@register_llm_model(
    name="deepseek-reasoner",
    provider="deepseek",
    cost_per_token=0.000014,  # DeepSeek定价
    max_tokens=128000,
    temperature=0.7,
    timeout=60,
    max_retries=3,
    description="DeepSeek Reasoning模型，擅长复杂推理任务"
)
class DeepSeekReasonerModel:
    """DeepSeek Reasoning模型"""
    def __init__(self, config):
        self.config = config
    
    async def generate(self, prompt, **kwargs):
        # 实际实现会调用DeepSeek API
        return {"content": f"DeepSeek Reasoner响应: {prompt[:50]}..."}


@register_llm_model(
    name="deepseek-chat",
    provider="deepseek",
    cost_per_token=0.00001,  # DeepSeek定价
    max_tokens=128000,
    temperature=0.7,
    timeout=60,
    max_retries=3,
    description="DeepSeek Chat模型，通用对话任务"
)
class DeepSeekChatModel:
    """DeepSeek Chat模型"""
    def __init__(self, config):
        self.config = config
    
    async def generate(self, prompt, **kwargs):
        # 实际实现会调用DeepSeek API
        return {"content": f"DeepSeek Chat响应: {prompt[:50]}..."}


# 注册路由策略
@register_routing_strategy(
    name="deepseek-optimized",
    description="DeepSeek优化路由策略",
    processors=["input_validator", "cost_optimizer", "performance_evaluator", "final_selector"],
    cost_weight=0.4,
    performance_weight=0.4,
    quality_weight=0.2,
    priority=8
)
class DeepSeekOptimizedStrategy:
    """DeepSeek优化策略"""
    pass


@register_routing_strategy(
    name="cost-first",
    description="成本优先策略",
    processors=["input_validator", "cost_optimizer", "final_selector"],
    cost_weight=0.8,
    performance_weight=0.2,
    quality_weight=0.0,
    priority=5
)
class CostFirstStrategy:
    """成本优先策略"""
    pass


@register_routing_strategy(
    name="performance-first",
    description="性能优先策略",
    processors=["input_validator", "performance_evaluator", "final_selector"],
    cost_weight=0.2,
    performance_weight=0.8,
    quality_weight=0.0,
    priority=5
)
class PerformanceFirstStrategy:
    """性能优先策略"""
    pass


# ============================================================================
# 自定义处理器（针对DeepSeek优化）
# ============================================================================

@register_processor(
    name="deepseek_validator",
    description="DeepSeek专用验证器",
    async_execution=True,
    timeout=5.0,
    max_retries=2
)
class DeepSeekValidatorProcessor(BaseProcessor):
    """DeepSeek验证器 - 验证请求是否适合DeepSeek模型"""
    
    def __init__(self, name="deepseek_validator", priority=15):
        super().__init__(name=name, priority=priority)
    
    async def _process(self, context: ProcessingContext) -> ProcessorResult:
        request = context.request
        available_models = context.available_models
        
        # 检查是否有DeepSeek模型可用
        deepseek_models = [m for m in available_models if 'deepseek' in m.lower()]
        if not deepseek_models:
            logger.warning("没有可用的DeepSeek模型")
            context.metadata["deepseek_available"] = False
            context.metadata["deepseek_models"] = []
            return ProcessorResult.CONTINUE
        
        context.metadata["deepseek_available"] = True
        context.metadata["deepseek_models"] = deepseek_models
        
        # 验证任务类型
        task_type = request.get("task_type", "general")
        if task_type in ["reasoning", "analytical", "code_generation"]:
            context.metadata["recommended_model"] = "deepseek-reasoner"
        else:
            context.metadata["recommended_model"] = "deepseek-chat"
        
        logger.debug(f"DeepSeek验证通过: 推荐 {context.metadata['recommended_model']}")
        return ProcessorResult.CONTINUE


@register_processor(
    name="deepseek_cost_optimizer",
    description="DeepSeek成本优化器",
    async_execution=True,
    timeout=3.0,
    max_retries=1
)
class DeepSeekCostOptimizerProcessor(BaseProcessor):
    """DeepSeek成本优化器 - 基于DeepSeek定价优化成本"""
    
    def __init__(self, name="deepseek_cost_optimizer", priority=25):
        super().__init__(name=name, priority=priority)
        # DeepSeek定价（每1000 token）
        self.pricing = {
            "deepseek-reasoner": 0.014,  # $0.014 per 1K tokens
            "deepseek-chat": 0.01,       # $0.01 per 1K tokens
        }
    
    async def _process(self, context: ProcessingContext) -> ProcessorResult:
        request = context.request
        available_models = context.available_models
        
        if not available_models:
            return ProcessorResult.CONTINUE
        
        # 计算每个模型的成本
        estimated_tokens = request.get("estimated_tokens", 1000)
        cost_estimates = {}
        
        for model in available_models:
            if model in self.pricing:
                cost = (estimated_tokens / 1000) * self.pricing[model]
                cost_estimates[model] = cost
        
        # 选择成本最低的模型
        if cost_estimates:
            cheapest_model = min(cost_estimates.items(), key=lambda x: x[1])
            context.metadata["cost_estimates"] = cost_estimates
            context.metadata["cheapest_model"] = cheapest_model[0]
            context.metadata["cheapest_cost"] = cheapest_model[1]
            
            logger.debug(f"成本优化: {cheapest_model[0]} 成本 ${cheapest_model[1]:.6f}")
        
        return ProcessorResult.CONTINUE


# ============================================================================
# 增强智能模型路由器
# ============================================================================

class EnhancedIntelligentRouter:
    """增强智能模型路由器"""
    
    def __init__(
        self,
        strategy_name: str = "deepseek-optimized",
        enable_processor_chain: bool = True,
        enable_events: bool = True,
        enable_storage: bool = True
    ):
        self.strategy_name = strategy_name
        self.enable_processor_chain = enable_processor_chain
        self.enable_events = enable_events
        self.enable_storage = enable_storage
        
        # 获取组件
        self.config_registry = get_config_registry()
        self.event_bus = get_event_bus() if enable_events else None
        self.storage = get_default_storage() if enable_storage else None
        
        # 初始化处理器链
        self.processor_chain = None
        if enable_processor_chain:
            self._init_processor_chain()
        
        # 事件订阅
        if enable_events:
            self._subscribe_events()
        
        # 存储集成
        if enable_storage:
            self._init_storage()
        
        logger.info(f"增强智能路由器已初始化，策略: {strategy_name}")
    
    def _init_processor_chain(self):
        """初始化处理器链"""
        self.processor_chain = ProcessorChain(name="enhanced-router-chain")
        
        # 添加处理器（按优先级顺序）
        self.processor_chain.add_processor(
            InputValidatorProcessor(name="input_validator", priority=10)
        )
        self.processor_chain.add_processor(
            DeepSeekValidatorProcessor(name="deepseek_validator", priority=15)
        )
        self.processor_chain.add_processor(
            DeepSeekCostOptimizerProcessor(name="deepseek_cost_optimizer", priority=25)
        )
        self.processor_chain.add_processor(
            PerformanceEvaluatorProcessor(name="performance_evaluator", priority=30)
        )
        self.processor_chain.add_processor(
            CircuitBreakerProcessor(name="circuit_breaker", priority=45)
        )
        self.processor_chain.add_processor(
            FinalSelectorProcessor(name="final_selector", priority=50)
        )
        
        logger.info("处理器链已初始化")
    
    def _subscribe_events(self):
        """订阅事件"""
        @event_subscriber(EventTypes.ROUTING_STARTED)
        async def on_routing_started(event):
            logger.info(f"路由开始: {event.metadata.event_id}")
        
        @event_subscriber(EventTypes.ROUTING_DECISION)
        async def on_routing_decision(event):
            logger.info(f"路由决策: {event.selected_model} (原因: {event.decision_factors})")
        
        @event_subscriber(EventTypes.MODEL_SELECTED)
        async def on_model_selected(event):
            logger.info(f"模型选择: {event.model_name} 成本: ${event.cost_estimate:.6f}")
        
        logger.info("事件订阅已设置")
    
    def _init_storage(self):
        """初始化存储"""
        if self.storage:
            # 保存路由器配置
            router_config = {
                "strategy_name": self.strategy_name,
                "enable_processor_chain": self.enable_processor_chain,
                "enable_events": self.enable_events,
                "enable_storage": self.enable_storage,
                "initialized_at": datetime.now().isoformat()
            }
            
            # 异步保存（不等待）
            asyncio.create_task(
                self.storage.save("router_config", router_config, immediate=False)
            )
            
            logger.info("存储集成已初始化")
    
    async def select_model(
        self,
        task_context: TaskContext,
        available_models: List[str],
        user_constraints: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """选择最优模型"""
        
        # 发布路由开始事件
        request_id = f"req_{int(time.time()*1000)}"
        if self.event_bus:
            await self.event_bus.publish(
                EventTypes.ROUTING_STARTED,
                {
                    "request_id": request_id,
                    "task_type": task_context.task_type.value,
                    "available_models": available_models
                },
                source="EnhancedIntelligentRouter"
            )
        
        start_time = time.time()
        
        try:
            # 准备处理上下文
            context_data = {
                "request_id": request_id,
                "task_type": task_context.task_type.value,
                "estimated_tokens": task_context.estimated_tokens,
                "priority": task_context.priority,
                "deadline_ms": task_context.deadline_ms,
                "user_preference": task_context.user_preference,
                "metadata": task_context.metadata,
                "user_constraints": user_constraints or {},
                "available_models": available_models
            }
            
            context = ProcessingContext(
                request=context_data,
                available_models=available_models
            )
            
            # 使用处理器链或简单逻辑
            if self.enable_processor_chain and self.processor_chain:
                result_context = await self.processor_chain.execute(context)
                selected_model = result_context.selected_model
                decision_reason = result_context.decision_reason or "处理器链决策"
                processing_metrics = {
                    "processor_times": result_context.processor_times,
                    "processing_time_ms": result_context.metadata.get("chain_processing_time_ms", 0),
                    "chain_name": result_context.metadata.get("chain_name", "")
                }
            else:
                # 回退到简单逻辑
                selected_model = self._simple_model_selection(
                    task_context, available_models, user_constraints
                )
                decision_reason = "简单选择逻辑"
                processing_metrics = {}
            
            processing_time = time.time() - start_time
            
            # 创建路由决策
            decision = RoutingDecision(
                selected_model=selected_model,
                alternative_models=[m for m in available_models if m != selected_model],
                predicted_performance={
                    "model": selected_model,
                    "estimated_latency_ms": processing_time * 1000,
                    "confidence": 0.8
                },
                reasoning=[decision_reason],
                timestamp=time.time()
            )
            
            # 发布路由决策事件
            if self.event_bus:
                await self.event_bus.publish(
                    EventTypes.ROUTING_DECISION,
                    {
                        "request_id": request_id,
                        "selected_model": selected_model,
                        "decision_factors": decision_reason,
                        "processing_time_ms": processing_time * 1000,
                        "success": True
                    },
                    source="EnhancedIntelligentRouter",
                    wait_for_processing=False
                )
            
            # 发布模型选择事件
            if self.event_bus:
                await self.event_bus.publish(
                    EventTypes.MODEL_SELECTED,
                    {
                        "request_id": request_id,
                        "model_name": selected_model,
                        "model_provider": "deepseek",
                        "selection_reason": decision_reason,
                        "cost_estimate": 0.0,  # 实际应从上下文获取
                        "latency_estimate": processing_time * 1000,
                        "alternatives": [m for m in available_models if m != selected_model]
                    },
                    source="EnhancedIntelligentRouter",
                    wait_for_processing=False
                )
            
            logger.info(f"路由决策完成: {selected_model}, 耗时: {processing_time:.3f}s")
            return decision
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"路由决策失败: {e}")
            
            # 发布失败事件
            if self.event_bus:
                await self.event_bus.publish(
                    EventTypes.ROUTING_FAILED,
                    {
                        "request_id": request_id,
                        "processing_time_ms": processing_time * 1000,
                        "error": str(e),
                        "success": False
                    },
                    source="EnhancedIntelligentRouter",
                    wait_for_processing=False
                )
            
            # 返回降级决策
            return RoutingDecision(
                selected_model=available_models[0] if available_models else "deepseek-chat",
                alternative_models=[],
                predicted_performance={
                    "model": available_models[0] if available_models else "deepseek-chat",
                    "estimated_latency_ms": processing_time * 1000,
                    "confidence": 0.3
                },
                reasoning=[f"降级决策: {str(e)}"],
                timestamp=time.time()
            )
    
    def _simple_model_selection(
        self,
        task_context: TaskContext,
        available_models: List[str],
        user_constraints: Optional[Dict[str, Any]] = None
    ) -> str:
        """简单模型选择逻辑（回退）"""
        if not available_models:
            return "deepseek-chat"
        
        # 优先选择DeepSeek模型
        deepseek_models = [m for m in available_models if 'deepseek' in m.lower()]
        if deepseek_models:
            # 根据任务类型选择
            if task_context.task_type in [TaskType.REASONING, TaskType.ANALYTICAL, TaskType.CODE_GENERATION]:
                # 优先选择reasoner
                for model in deepseek_models:
                    if 'reasoner' in model.lower():
                        return model
            # 默认返回第一个DeepSeek模型
            return deepseek_models[0]
        
        # 没有DeepSeek模型，返回第一个可用模型
        return available_models[0]
    
    async def validate_configuration(self) -> ValidationResult:
        """验证路由器配置"""
        validator = get_llm_model_validator()
        
        # 获取所有注册的LLM模型配置
        configs = []
        registry = get_config_registry()
        for model_name, model_config in registry.llm_models.items():
            configs.append(model_config)
        
        # 验证每个配置
        all_valid = True
        errors = []
        
        for config in configs:
            result = await validator.validate(config)
            if not result.valid:
                all_valid = False
                errors.extend(result.errors)
        
        validation_result = ValidationResult(valid=all_valid)
        if not all_valid:
            validation_result.errors = errors
        
        return validation_result
    
    def get_stats(self) -> Dict[str, Any]:
        """获取路由器统计信息"""
        stats = {
            "strategy_name": self.strategy_name,
            "enable_processor_chain": self.enable_processor_chain,
            "enable_events": self.enable_events,
            "enable_storage": self.enable_storage,
            "processor_chain_initialized": self.processor_chain is not None
        }
        
        # 添加存储统计
        if self.storage:
            storage_stats = self.storage.get_stats()
            stats["storage"] = storage_stats
        
        # 添加事件总线统计
        if self.event_bus:
            event_stats = self.event_bus.get_bus_stats()
            stats["events"] = event_stats
        
        return stats
    
    async def close(self):
        """关闭路由器资源"""
        if self.storage:
            await self.storage.close()
        
        logger.info("增强智能路由器已关闭")


# ============================================================================
# 使用示例
# ============================================================================

async def example_usage():
    """使用示例"""
    print("增强智能模型路由器使用示例")
    print("=" * 60)
    
    # 创建路由器
    router = EnhancedIntelligentRouter(
        strategy_name="deepseek-optimized",
        enable_processor_chain=True,
        enable_events=True,
        enable_storage=True
    )
    
    # 验证配置
    validation_result = await router.validate_configuration()
    if validation_result.valid:
        print("✓ 配置验证通过")
    else:
        print(f"⚠️ 配置验证失败: {validation_result.errors}")
    
    # 创建任务上下文
    task_context = TaskContext(
        task_type=TaskType.REASONING,
        estimated_tokens=500,
        priority=8,
        metadata={"complexity": "high"}
    )
    
    # 可用模型
    available_models = ["deepseek-reasoner", "deepseek-chat"]
    
    # 选择模型
    decision = await router.select_model(
        task_context=task_context,
        available_models=available_models,
        user_constraints={"max_cost": 0.01}
    )
    
    print(f"✓ 选择的模型: {decision.selected_model}")
    print(f"✓ 决策原因: {decision.reasoning}")
    print(f"✓ 备选模型: {decision.alternative_models}")
    
    # 获取统计信息
    stats = router.get_stats()
    print(f"✓ 路由器统计: {stats}")
    
    # 关闭路由器
    await router.close()
    
    print("=" * 60)
    print("示例完成")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())