#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理器链模式 - 受Paperclip启发的模块化路由决策

将复杂的路由决策分解为一系列独立的处理器，每个处理器负责一个特定方面：
1. 输入验证处理器
2. 成本优化处理器
3. 性能评估处理器  
4. 质量验证处理器
5. A/B测试处理器
6. 自适应调优处理器
7. 断路器处理器
8. 降级处理器

每个处理器可以：
- 修改路由上下文
- 做出最终决策（提前终止链）
- 添加建议或警告
- 记录指标和日志

设计原则：
1. 单一职责：每个处理器只关注一个方面
2. 可插拔：处理器可以动态添加、移除、重新排序
3. 可组合：处理器链可以嵌套和组合
4. 容错：单个处理器失败不影响整个系统
5. 可观测：每个处理器的决策过程可追踪
"""

import logging
import asyncio
import inspect
import time
from typing import Dict, Any, List, Optional, Union, Callable, Type, Tuple
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import threading

logger = logging.getLogger(__name__)


class ProcessorResult(Enum):
    """处理器执行结果"""
    CONTINUE = "continue"        # 继续执行下一个处理器
    FINAL_DECISION = "final"     # 做出最终决策，终止链
    SKIP_NEXT = "skip_next"      # 跳过下一个处理器
    TERMINATE = "terminate"      # 终止整个处理器链
    ERROR = "error"              # 处理器执行错误


@dataclass
class ProcessingContext:
    """处理器执行上下文"""
    
    # 输入数据
    request: Dict[str, Any]                # 原始请求
    available_models: List[str]            # 可用模型列表
    
    # 中间数据（处理器可修改）
    candidate_models: List[str] = field(default_factory=list)      # 候选模型
    scores: Dict[str, float] = field(default_factory=dict)         # 模型得分
    constraints: Dict[str, Any] = field(default_factory=dict)      # 约束条件
    metadata: Dict[str, Any] = field(default_factory=dict)         # 元数据
    warnings: List[str] = field(default_factory=list)              # 警告信息
    errors: List[str] = field(default_factory=list)                # 错误信息
    
    # 决策数据
    selected_model: Optional[str] = None                           # 选择的模型
    final_decision: bool = False                                   # 是否为最终决策
    decision_reason: Optional[str] = None                          # 决策原因
    processor_trace: List[str] = field(default_factory=list)       # 处理器执行轨迹
    
    # 性能数据
    start_time: float = field(default_factory=time.time)           # 处理开始时间
    processor_times: Dict[str, float] = field(default_factory=dict) # 每个处理器耗时
    
    def add_trace(self, processor_name: str, action: str = "executed"):
        """添加处理器追踪"""
        self.processor_trace.append(f"{processor_name}:{action}")
    
    def add_warning(self, warning: str):
        """添加警告"""
        self.warnings.append(warning)
    
    def add_error(self, error: str):
        """添加错误"""
        self.errors.append(error)
    
    def get_processing_time(self) -> float:
        """获取总处理时间"""
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request": self.request,
            "available_models": self.available_models,
            "candidate_models": self.candidate_models,
            "scores": self.scores,
            "constraints": self.constraints,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
            "selected_model": self.selected_model,
            "final_decision": self.final_decision,
            "decision_reason": self.decision_reason,
            "processor_trace": self.processor_trace,
            "processing_time": self.get_processing_time(),
            "processor_times": self.processor_times
        }


@dataclass
class ProcessorMetrics:
    """处理器性能指标"""
    name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    last_execution_time: float = 0.0
    
    def record_execution(self, success: bool, time_ms: float):
        """记录执行"""
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
        self.total_time_ms += time_ms
        self.avg_time_ms = self.total_time_ms / self.total_executions
        self.last_execution_time = time_ms
    
    def success_rate(self) -> float:
        """成功率"""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions


class BaseProcessor(ABC):
    """处理器基类"""
    
    def __init__(self, name: str, enabled: bool = True, priority: int = 5):
        """
        初始化处理器
        
        Args:
            name: 处理器名称（唯一标识符）
            enabled: 是否启用
            priority: 优先级（1-10，值越小优先级越高）
        """
        self.name = name
        self.enabled = enabled
        self.priority = priority
        self.metrics = ProcessorMetrics(name)
        self._config: Dict[str, Any] = {}
        
        # 事件回调
        self._before_process_callbacks: List[Callable] = []
        self._after_process_callbacks: List[Callable] = []
    
    def configure(self, config: Dict[str, Any]):
        """配置处理器"""
        self._config = config.copy()
        logger.debug(f"配置处理器 {self.name}: {config}")
    
    def add_before_callback(self, callback: Callable):
        """添加处理前回调"""
        self._before_process_callbacks.append(callback)
    
    def add_after_callback(self, callback: Callable):
        """添加处理后回调"""
        self._after_process_callbacks.append(callback)
    
    async def process(self, context: ProcessingContext) -> Tuple[ProcessorResult, ProcessingContext]:
        """
        处理请求（模板方法）
        
        Args:
            context: 处理上下文
            
        Returns:
            (处理结果, 更新后的上下文)
        """
        if not self.enabled:
            context.add_trace(self.name, "skipped_disabled")
            return ProcessorResult.SKIP_NEXT, context
        
        # 执行前置回调
        for callback in self._before_process_callbacks:
            try:
                callback(self.name, context)
            except Exception as e:
                logger.warning(f"处理器 {self.name} 前置回调执行失败: {e}")
        
        start_time = time.time()
        success = False
        
        try:
            # 记录处理器开始
            context.add_trace(self.name, "started")
            
            # 执行实际处理
            result = await self._process(context)
            success = True
            
            # 记录处理器结束
            context.add_trace(self.name, f"completed:{result.value}")
            
        except Exception as e:
            logger.error(f"处理器 {self.name} 执行失败: {e}")
            context.add_error(f"处理器 {self.name} 执行失败: {str(e)}")
            result = ProcessorResult.ERROR
        
        finally:
            # 记录性能指标
            exec_time = (time.time() - start_time) * 1000
            self.metrics.record_execution(success, exec_time)
            context.processor_times[self.name] = exec_time
            
            # 执行后置回调
            for callback in self._after_process_callbacks:
                try:
                    callback(self.name, context, result, exec_time)
                except Exception as e:
                    logger.warning(f"处理器 {self.name} 后置回调执行失败: {e}")
        
        return result, context
    
    @abstractmethod
    async def _process(self, context: ProcessingContext) -> ProcessorResult:
        """
        实际处理逻辑（子类实现）
        
        Args:
            context: 处理上下文
            
        Returns:
            处理结果
        """
        pass
    
    def get_metrics(self) -> ProcessorMetrics:
        """获取性能指标"""
        return self.metrics
    
    def __str__(self) -> str:
        return f"Processor(name={self.name}, enabled={self.enabled}, priority={self.priority})"


class ProcessorChain:
    """处理器链管理器"""
    
    def __init__(self, name: str):
        """
        初始化处理器链
        
        Args:
            name: 处理器链名称
        """
        self.name = name
        self.processors: List[BaseProcessor] = []
        self._processor_map: Dict[str, BaseProcessor] = {}
        self._lock = threading.RLock()
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_processing_time_ms": 0.0,
            "total_processing_time_ms": 0.0
        }
        
        logger.info(f"初始化处理器链: {name}")
    
    def add_processor(self, processor: BaseProcessor, position: Optional[int] = None) -> bool:
        """
        添加处理器
        
        Args:
            processor: 处理器实例
            position: 插入位置，None表示追加到末尾
            
        Returns:
            是否成功添加
        """
        with self._lock:
            if processor.name in self._processor_map:
                logger.warning(f"处理器 {processor.name} 已存在")
                return False
            
            if position is None:
                self.processors.append(processor)
            else:
                self.processors.insert(position, processor)
            
            self._processor_map[processor.name] = processor
            logger.info(f"添加处理器 {processor.name} 到链 {self.name} (优先级: {processor.priority})")
            
            # 按优先级排序
            self._sort_processors()
            return True
    
    def remove_processor(self, processor_name: str) -> bool:
        """
        移除处理器
        
        Args:
            processor_name: 处理器名称
            
        Returns:
            是否成功移除
        """
        with self._lock:
            if processor_name not in self._processor_map:
                return False
            
            # 从列表中移除
            self.processors = [p for p in self.processors if p.name != processor_name]
            # 从映射中移除
            del self._processor_map[processor_name]
            
            logger.info(f"从链 {self.name} 移除处理器 {processor_name}")
            return True
    
    def get_processor(self, processor_name: str) -> Optional[BaseProcessor]:
        """获取处理器"""
        with self._lock:
            return self._processor_map.get(processor_name)
    
    def enable_processor(self, processor_name: str) -> bool:
        """启用处理器"""
        with self._lock:
            processor = self._processor_map.get(processor_name)
            if not processor:
                return False
            
            processor.enabled = True
            logger.info(f"启用处理器 {processor_name}")
            return True
    
    def disable_processor(self, processor_name: str) -> bool:
        """禁用处理器"""
        with self._lock:
            processor = self._processor_map.get(processor_name)
            if not processor:
                return False
            
            processor.enabled = False
            logger.info(f"禁用处理器 {processor_name}")
            return True
    
    def _sort_processors(self):
        """按优先级排序处理器"""
        self.processors.sort(key=lambda p: p.priority)
    
    async def execute(self, context: ProcessingContext) -> ProcessingContext:
        """
        执行处理器链
        
        Args:
            context: 处理上下文
            
        Returns:
            处理后的上下文
        """
        start_time = time.time()
        self._metrics["total_requests"] += 1
        
        try:
            # 按顺序执行处理器
            for i, processor in enumerate(self.processors):
                if context.final_decision:
                    logger.debug(f"提前终止处理器链，已在处理器 {i-1} 做出最终决策")
                    break
                
                # 执行处理器
                result, context = await processor.process(context)
                
                # 根据结果决定下一步
                if result == ProcessorResult.TERMINATE:
                    logger.debug(f"处理器 {processor.name} 请求终止链")
                    break
                elif result == ProcessorResult.SKIP_NEXT:
                    logger.debug(f"处理器 {processor.name} 请求跳过下一个处理器")
                    # 跳过下一个处理器
                    if i + 1 < len(self.processors):
                        context.add_trace(self.processors[i + 1].name, "skipped_by_previous")
                        i += 1
                elif result == ProcessorResult.ERROR:
                    logger.warning(f"处理器 {processor.name} 执行错误")
                    # 继续执行下一个处理器（容错）
                    continue
                elif result == ProcessorResult.FINAL_DECISION:
                    context.final_decision = True
                    logger.debug(f"处理器 {processor.name} 做出最终决策")
            
            # 如果没有处理器做出最终决策，使用默认逻辑
            if not context.final_decision and context.candidate_models:
                context.selected_model = self._select_default_model(context)
                context.decision_reason = "默认选择（无处理器做出最终决策）"
                context.final_decision = True
                context.add_trace("default_selector", "selected")
            
            self._metrics["successful_requests"] += 1
            
        except Exception as e:
            logger.error(f"处理器链执行失败: {e}")
            self._metrics["failed_requests"] += 1
            context.add_error(f"处理器链执行失败: {str(e)}")
            
            # 尝试降级处理
            context = self._fallback_processing(context)
        
        finally:
            # 记录性能指标
            processing_time = (time.time() - start_time) * 1000
            self._metrics["total_processing_time_ms"] += processing_time
            self._metrics["avg_processing_time_ms"] = (
                self._metrics["total_processing_time_ms"] / self._metrics["total_requests"]
            )
            
            context.metadata["chain_processing_time_ms"] = processing_time
            context.metadata["chain_name"] = self.name
        
        return context
    
    def _select_default_model(self, context: ProcessingContext) -> Optional[str]:
        """选择默认模型"""
        if not context.candidate_models:
            return None
        
        # 如果有得分，选择最高分
        if context.scores:
            return max(context.scores.items(), key=lambda x: x[1])[0]
        
        # 否则选择第一个候选模型
        return context.candidate_models[0]
    
    def _fallback_processing(self, context: ProcessingContext) -> ProcessingContext:
        """降级处理"""
        logger.warning("执行降级处理")
        
        # 简单的降级逻辑：选择第一个可用模型
        if context.available_models:
            context.selected_model = context.available_models[0]
            context.decision_reason = "降级处理：选择第一个可用模型"
            context.final_decision = True
            context.add_trace("fallback_handler", "selected")
        
        return context
    
    def get_chain_metrics(self) -> Dict[str, Any]:
        """获取处理器链指标"""
        with self._lock:
            return self._metrics.copy()
    
    def get_all_processor_metrics(self) -> Dict[str, ProcessorMetrics]:
        """获取所有处理器指标"""
        with self._lock:
            return {name: processor.get_metrics() for name, processor in self._processor_map.items()}
    
    def list_processors(self) -> List[Dict[str, Any]]:
        """列出所有处理器信息"""
        with self._lock:
            return [
                {
                    "name": p.name,
                    "enabled": p.enabled,
                    "priority": p.priority,
                    "class": p.__class__.__name__,
                    "metrics": p.get_metrics().__dict__
                }
                for p in self.processors
            ]
    
    def clear(self):
        """清空处理器链"""
        with self._lock:
            self.processors.clear()
            self._processor_map.clear()
            logger.info(f"清空处理器链 {self.name}")


# ============================================================================
# 常用处理器实现
# ============================================================================

class InputValidatorProcessor(BaseProcessor):
    """输入验证处理器"""
    
    def __init__(self, name: str = "input_validator", enabled: bool = True, priority: int = 1):
        super().__init__(name, enabled, priority)
    
    async def _process(self, context: ProcessingContext) -> ProcessorResult:
        """验证输入"""
        request = context.request
        
        # 检查必需字段
        required_fields = ["query", "task_type"]
        missing_fields = [field for field in required_fields if field not in request]
        
        if missing_fields:
            context.add_error(f"缺少必需字段: {missing_fields}")
            return ProcessorResult.TERMINATE
        
        # 验证任务类型
        valid_task_types = ["general", "reasoning", "code_generation", "summarization", 
                           "translation", "creative", "analytical"]
        task_type = request.get("task_type", "general")
        
        if task_type not in valid_task_types:
            context.add_warning(f"未知任务类型: {task_type}，使用默认值 'general'")
            request["task_type"] = "general"
        
        # 验证token限制
        max_tokens = request.get("max_tokens", 4000)
        if max_tokens > 16000:
            context.add_warning(f"max_tokens ({max_tokens}) 超出推荐值，可能被截断")
            request["max_tokens"] = min(max_tokens, 16000)
        
        # 初始化候选模型
        context.candidate_models = context.available_models.copy()
        
        return ProcessorResult.CONTINUE


class CostOptimizerProcessor(BaseProcessor):
    """成本优化处理器"""
    
    def __init__(self, name: str = "cost_optimizer", enabled: bool = True, priority: int = 3):
        super().__init__(name, enabled, priority)
        self.cost_threshold = 0.10  # 默认成本阈值（美元）
    
    async def _process(self, context: ProcessingContext) -> ProcessorResult:
        """成本优化"""
        from src.core.declarative_config import get_config_registry
        
        # 获取模型成本配置
        registry = get_config_registry()
        cost_sensitive = context.request.get("cost_sensitive", False)
        
        # 计算每个模型的成本得分
        model_scores = {}
        for model_name in context.candidate_models:
            config = registry.get_llm_model(model_name)
            if not config:
                context.add_warning(f"模型 {model_name} 无成本配置，跳过成本优化")
                continue
            
            cost_per_token = config.get("cost_per_token", 0.0)
            estimated_tokens = context.request.get("estimated_tokens", 1000)
            estimated_cost = cost_per_token * estimated_tokens
            
            # 成本得分（成本越低得分越高）
            if cost_per_token <= 0:
                cost_score = 1.0  # 免费模型
            else:
                # 归一化处理
                base_cost = 0.000014  # DeepSeek成本作为基准
                normalized_cost = min(estimated_cost / (base_cost * estimated_tokens), 10.0)
                cost_score = max(0.1, 1.0 / (1.0 + normalized_cost))
            
            model_scores[model_name] = cost_score
            
            # 检查是否超过成本阈值
            if cost_sensitive and estimated_cost > self.cost_threshold:
                context.candidate_models.remove(model_name)
                context.add_trace(self.name, f"removed_high_cost:{model_name}")
        
        # 更新总得分
        for model_name, score in model_scores.items():
            context.scores[model_name] = context.scores.get(model_name, 0.0) + score * 0.6
        
        return ProcessorResult.CONTINUE


class PerformanceEvaluatorProcessor(BaseProcessor):
    """性能评估处理器"""
    
    def __init__(self, name: str = "performance_evaluator", enabled: bool = True, priority: int = 4):
        super().__init__(name, enabled, priority)
    
    async def _process(self, context: ProcessingContext) -> ProcessorResult:
        """性能评估"""
        # 这里应该集成性能预测器
        # 暂时使用简单的模拟逻辑
        
        for model_name in context.candidate_models:
            # 模拟性能得分（基于模型类型）
            if "deepseek-reasoner" in model_name:
                perf_score = 0.9
            elif "deepseek-chat" in model_name:
                perf_score = 0.8
            elif "gpt-4" in model_name:
                perf_score = 0.9  # 保留，但应该不会用到
            elif "gpt-3.5" in model_name:
                perf_score = 0.7
            elif "claude" in model_name:
                perf_score = 0.8  # 保留但不再使用
            elif "llama" in model_name:
                perf_score = 0.6
            else:
                perf_score = 0.5
            
            # 考虑任务类型
            task_type = context.request.get("task_type", "general")
            if task_type == "code_generation" and "code" in model_name.lower():
                perf_score *= 1.2
            elif task_type == "reasoning" and "deepseek-reasoner" in model_name:
                perf_score *= 1.3  # DeepSeek推理模型优化
            
            # 更新总得分
            context.scores[model_name] = context.scores.get(model_name, 0.0) + perf_score * 0.4
        
        return ProcessorResult.CONTINUE


class ABTestingProcessor(BaseProcessor):
    """A/B测试处理器"""
    
    def __init__(self, name: str = "ab_testing", enabled: bool = True, priority: int = 6):
        super().__init__(name, enabled, priority)
        self.experiment_traffic_percentage = 10.0  # 实验流量百分比
    
    async def _process(self, context: ProcessingContext) -> ProcessorResult:
        """A/B测试处理"""
        # 检查是否参与实验
        user_id = context.request.get("user_id", "anonymous")
        experiment_id = context.request.get("experiment_id")
        
        if not experiment_id:
            return ProcessorResult.SKIP_NEXT
        
        try:
            from src.services.ab_testing_router import get_ab_testing_router
            
            router = get_ab_testing_router()
            # 这里应该调用路由器的实验路由逻辑
            # 暂时跳过具体实现
            
            context.add_trace(self.name, f"experiment:{experiment_id}")
            return ProcessorResult.CONTINUE
            
        except ImportError:
            context.add_warning("A/B测试服务不可用，跳过实验处理")
            return ProcessorResult.SKIP_NEXT


class CircuitBreakerProcessor(BaseProcessor):
    """断路器处理器"""
    
    def __init__(self, name: str = "circuit_breaker", enabled: bool = True, priority: int = 2):
        super().__init__(name, enabled, priority)
        self.failure_threshold = 5  # 失败阈值
        self.recovery_timeout = 60  # 恢复超时（秒）
        self._failure_counts: Dict[str, int] = {}
        self._circuit_states: Dict[str, Tuple[bool, float]] = {}  # (是否打开, 打开时间)
    
    async def _process(self, context: ProcessingContext) -> ProcessorResult:
        """断路器检查"""
        current_time = time.time()
        
        for model_name in context.candidate_models.copy():
            # 检查断路器状态
            circuit_state = self._circuit_states.get(model_name)
            
            if circuit_state and circuit_state[0]:  # 断路器打开
                open_time = circuit_state[1]
                
                # 检查是否应该恢复
                if current_time - open_time > self.recovery_timeout:
                    # 尝试恢复
                    logger.info(f"尝试恢复模型 {model_name} 的断路器")
                    self._circuit_states[model_name] = (False, 0.0)
                    self._failure_counts[model_name] = 0
                else:
                    # 移除不可用模型
                    context.candidate_models.remove(model_name)
                    context.add_trace(self.name, f"circuit_open:{model_name}")
                    continue
            
            # 检查失败次数
            failure_count = self._failure_counts.get(model_name, 0)
            if failure_count >= self.failure_threshold:
                # 打开断路器
                self._circuit_states[model_name] = (True, current_time)
                context.candidate_models.remove(model_name)
                context.add_trace(self.name, f"circuit_tripped:{model_name}")
                logger.warning(f"模型 {model_name} 断路器打开（失败次数: {failure_count}）")
        
        return ProcessorResult.CONTINUE
    
    def record_failure(self, model_name: str):
        """记录模型失败"""
        current_count = self._failure_counts.get(model_name, 0)
        self._failure_counts[model_name] = current_count + 1
        logger.debug(f"记录模型 {model_name} 失败，当前失败次数: {current_count + 1}")
    
    def record_success(self, model_name: str):
        """记录模型成功（重置失败计数）"""
        if model_name in self._failure_counts:
            self._failure_counts[model_name] = 0
            logger.debug(f"重置模型 {model_name} 失败计数")


class FinalSelectorProcessor(BaseProcessor):
    """最终选择处理器"""
    
    def __init__(self, name: str = "final_selector", enabled: bool = True, priority: int = 10):
        super().__init__(name, enabled, priority)
    
    async def _process(self, context: ProcessingContext) -> ProcessorResult:
        """最终选择"""
        if not context.candidate_models:
            context.add_error("没有可用的候选模型")
            return ProcessorResult.TERMINATE
        
        # 选择得分最高的模型
        scored_models = [(model, context.scores.get(model, 0.0)) 
                        for model in context.candidate_models]
        scored_models.sort(key=lambda x: x[1], reverse=True)
        
        selected_model, score = scored_models[0]
        context.selected_model = selected_model
        context.final_decision = True
        context.decision_reason = f"综合得分最高: {score:.3f}"
        
        # 记录第二名（用于分析）
        if len(scored_models) > 1:
            second_model, second_score = scored_models[1]
            context.metadata["second_choice"] = {
                "model": second_model,
                "score": second_score,
                "score_diff": score - second_score
            }
        
        return ProcessorResult.FINAL_DECISION


# ============================================================================
# 工厂函数和辅助函数
# ============================================================================

def create_default_chain(name: str = "default_routing_chain") -> ProcessorChain:
    """创建默认处理器链"""
    chain = ProcessorChain(name)
    
    # 添加默认处理器
    chain.add_processor(InputValidatorProcessor(priority=1))
    chain.add_processor(CircuitBreakerProcessor(priority=2))
    chain.add_processor(CostOptimizerProcessor(priority=3))
    chain.add_processor(PerformanceEvaluatorProcessor(priority=4))
    chain.add_processor(ABTestingProcessor(priority=6))
    chain.add_processor(FinalSelectorProcessor(priority=10))
    
    logger.info(f"创建默认处理器链 '{name}'，包含 {len(chain.processors)} 个处理器")
    return chain


def create_fallback_chain(name: str = "fallback_chain") -> ProcessorChain:
    """创建降级处理器链"""
    chain = ProcessorChain(name)
    
    # 简化的降级链
    chain.add_processor(InputValidatorProcessor(name="fallback_validator", priority=1))
    chain.add_processor(FinalSelectorProcessor(name="fallback_selector", priority=5))
    
    logger.info(f"创建降级处理器链 '{name}'")
    return chain