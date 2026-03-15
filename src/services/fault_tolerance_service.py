#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故障容忍服务 - 多模型架构的故障转移和降级

提供完整的故障转移、降级链和健康监控功能。
基于断路器模式实现智能故障检测和自动恢复。

主要功能：
1. 多模型断路器管理：为每个模型维护独立的断路器状态
2. 智能降级链：根据成本和性能自动选择备用模型
3. 健康监控：实时监控模型可用性和性能
4. 自动恢复：失败模型在冷却期后自动恢复
5. 统计和报告：提供详细的故障转移统计信息

设计原则：
- 断路器模式：防止级联故障
- 成本感知：优先选择成本更低的备用模型
- 性能优先：在成本相近时选择性能更好的模型
- 渐进恢复：失败模型逐步重新引入
- 透明性：对上层应用透明，自动处理故障

注意：此服务与现有LLMIntegration中的断路器机制兼容。
"""

import os
import time
import json
import logging
import threading
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime

from src.core.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class ModelPriority(str, Enum):
    """模型优先级枚举"""
    PRIMARY = "primary"      # 主模型（高质量，高成本）
    SECONDARY = "secondary"  # 次要模型（中等质量，中等成本）
    FALLBACK = "fallback"    # 备用模型（基本质量，低成本或免费）
    EMERGENCY = "emergency"  # 应急模型（最低质量，本地或模拟）


class FailureType(str, Enum):
    """故障类型枚举"""
    NETWORK = "network"      # 网络故障
    TIMEOUT = "timeout"      # 超时
    RATE_LIMIT = "rate_limit"  # 频率限制
    AUTH_ERROR = "auth_error"  # 认证错误
    MODEL_ERROR = "model_error"  # 模型错误
    UNKNOWN = "unknown"      # 未知错误


@dataclass
class ModelHealth:
    """模型健康状态"""
    model_id: str                    # 模型标识符
    priority: ModelPriority          # 模型优先级
    is_healthy: bool                 # 是否健康
    last_check_time: float           # 最后检查时间
    failure_count: int               # 失败次数
    success_count: int               # 成功次数
    avg_response_time: float         # 平均响应时间（毫秒）
    last_error: Optional[str]        # 最后错误信息
    last_error_time: Optional[float] # 最后错误时间
    circuit_state: str               # 断路器状态
    consecutive_failures: int        # 连续失败次数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    @property
    def uptime_minutes(self) -> float:
        """计算正常运行时间（分钟）"""
        if self.last_error_time:
            return (time.time() - self.last_error_time) / 60
        return float('inf')  # 从未失败


@dataclass
class FallbackChainConfig:
    """降级链配置"""
    chain_id: str                                    # 链标识符
    primary_model: str                               # 主模型
    secondary_models: List[str]                      # 次要模型列表
    fallback_models: List[str]                       # 备用模型列表
    emergency_model: Optional[str] = None            # 应急模型
    cost_weights: Dict[str, float] = None           # 成本权重（越低越好）
    performance_weights: Dict[str, float] = None     # 性能权重（越高越好）
    
    def __post_init__(self):
        """初始化后处理"""
        if self.cost_weights is None:
            self.cost_weights = {}
        if self.performance_weights is None:
            self.performance_weights = {}


@dataclass
class FaultToleranceStats:
    """故障容忍统计"""
    total_requests: int = 0                         # 总请求数
    successful_requests: int = 0                    # 成功请求数
    failed_requests: int = 0                        # 失败请求数
    fallback_triggered: int = 0                     # 降级触发次数
    circuit_breaker_trips: int = 0                  # 断路器跳闸次数
    total_fallback_time_ms: float = 0.0             # 总降级时间（毫秒）
    avg_fallback_latency_ms: float = 0.0            # 平均降级延迟
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        return self.successful_requests / self.total_requests if self.total_requests > 0 else 0.0
    
    @property
    def fallback_rate(self) -> float:
        """计算降级率"""
        return self.fallback_triggered / self.total_requests if self.total_requests > 0 else 0.0


class FaultToleranceService:
    """故障容忍服务"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化故障容忍服务
        
        Args:
            config_file: 配置文件路径（可选）
        """
        self.logger = logging.getLogger(__name__)
        
        # 模型健康状态跟踪
        self.model_health: Dict[str, ModelHealth] = {}
        
        # 断路器实例（每个模型一个）
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # 降级链配置
        self.fallback_chains: Dict[str, FallbackChainConfig] = {}
        
        # 统计信息
        self.stats = FaultToleranceStats()
        self.stats_lock = threading.RLock()
        
        # 配置
        self.config_file = config_file
        self.default_circuit_config = {
            "failure_threshold": 5,     # 失败阈值
            "recovery_timeout": 60,     # 恢复超时（秒）
        }
        
        # 加载配置
        self._load_config()
        
        # 健康检查线程
        self._health_check_interval = 300  # 5分钟
        self._health_check_thread = None
        self._stop_health_check = threading.Event()
        
        self.logger.info("故障容忍服务初始化完成")
    
    def _load_config(self) -> None:
        """加载配置"""
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 加载降级链配置
                if "fallback_chains" in config:
                    for chain_id, chain_config in config["fallback_chains"].items():
                        self.fallback_chains[chain_id] = FallbackChainConfig(
                            chain_id=chain_id,
                            **chain_config
                        )
                        self.logger.info(f"加载降级链配置: {chain_id}")
                
                # 加载断路器配置
                if "circuit_breaker" in config:
                    self.default_circuit_config.update(config["circuit_breaker"])
                
                self.logger.info(f"从 {self.config_file} 加载配置成功")
            except Exception as e:
                self.logger.error(f"加载配置文件失败: {e}")
        
        # 如果没有配置文件，使用默认降级链
        if not self.fallback_chains:
            self._create_default_fallback_chains()
    
    def _create_default_fallback_chains(self) -> None:
        """创建默认降级链"""
        # 默认降级链：DeepSeek → Step-3.5-Flash → 本地模型
        default_chain = FallbackChainConfig(
            chain_id="default",
            primary_model="deepseek-chat",
            secondary_models=["step-3.5-flash"],
            fallback_models=["local-llama", "local-qwen", "local-phi3"],
            emergency_model="mock",
            cost_weights={
                "deepseek-chat": 1.0,
                "step-3.5-flash": 0.3,
                "local-llama": 0.1,
                "local-qwen": 0.1,
                "local-phi3": 0.1,
                "mock": 0.0,
            },
            performance_weights={
                "deepseek-chat": 1.0,
                "step-3.5-flash": 0.8,
                "local-llama": 0.5,
                "local-qwen": 0.5,
                "local-phi3": 0.4,
                "mock": 0.1,
            }
        )
        
        self.fallback_chains["default"] = default_chain
        self.logger.info("创建默认降级链")
    
    def register_model(
        self, 
        model_id: str, 
        priority: ModelPriority = ModelPriority.PRIMARY,
        circuit_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        注册模型
        
        Args:
            model_id: 模型标识符
            priority: 模型优先级
            circuit_config: 断路器配置（可选）
        """
        if model_id in self.model_health:
            self.logger.warning(f"模型已注册: {model_id}")
            return
        
        # 创建断路器
        if circuit_config is None:
            circuit_config = self.default_circuit_config.copy()
        
        circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_config.get("failure_threshold", 5),
            recovery_timeout=circuit_config.get("recovery_timeout", 60),
            name=f"FT-{model_id}"
        )
        
        # 创建健康状态
        health = ModelHealth(
            model_id=model_id,
            priority=priority,
            is_healthy=True,
            last_check_time=time.time(),
            failure_count=0,
            success_count=0,
            avg_response_time=0.0,
            last_error=None,
            last_error_time=None,
            circuit_state=circuit_breaker.state.value,
            consecutive_failures=0
        )
        
        # 保存
        self.model_health[model_id] = health
        self.circuit_breakers[model_id] = circuit_breaker
        
        self.logger.info(f"注册模型: {model_id} (优先级: {priority.value})")
    
    def execute_with_fallback(
        self,
        chain_id: str,
        operation: Callable[[str], Any],
        initial_model: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        使用降级链执行操作
        
        Args:
            chain_id: 降级链标识符
            operation: 要执行的操作（接受模型ID参数）
            initial_model: 初始模型（可选，默认为链的主模型）
            context: 上下文信息（可选）
            
        Returns:
            Any: 操作结果
            
        Raises:
            Exception: 如果所有模型都失败
        """
        start_time = time.time()
        
        # 获取降级链
        chain = self.fallback_chains.get(chain_id)
        if not chain:
            raise ValueError(f"未找到降级链: {chain_id}")
        
        # 确定尝试的模型序列
        models_to_try = self._get_fallback_sequence(chain, initial_model, context)
        
        self.logger.info(f"执行降级链 {chain_id}: {models_to_try}")
        
        last_exception = None
        successful_model = None
        
        for i, model_id in enumerate(models_to_try):
            # 检查模型是否可用
            if not self._is_model_available(model_id):
                self.logger.warning(f"模型不可用，跳过: {model_id}")
                continue
            
            # 检查断路器状态
            circuit_breaker = self.circuit_breakers.get(model_id)
            if circuit_breaker and circuit_breaker.state.value == "OPEN":
                self.logger.debug(f"断路器打开，跳过: {model_id}")
                continue
            
            try:
                # 执行操作
                self.logger.debug(f"尝试模型 {model_id} ({i+1}/{len(models_to_try)})")
                
                if circuit_breaker:
                    # 使用断路器保护
                    result = circuit_breaker.call(operation, model_id)
                else:
                    # 直接执行
                    result = operation(model_id)
                
                # 记录成功
                self._record_success(model_id, start_time)
                successful_model = model_id
                
                # 如果这是降级模型，更新统计
                if i > 0:
                    self._record_fallback(i, start_time)
                
                self.logger.info(f"操作成功，使用模型: {model_id}")
                return result
                
            except CircuitBreakerOpenError as e:
                # 断路器打开，尝试下一个模型
                self.logger.warning(f"断路器打开: {model_id}")
                last_exception = e
                self._record_circuit_trip(model_id)
                
            except Exception as e:
                # 操作失败，记录并尝试下一个模型
                self.logger.warning(f"模型 {model_id} 失败: {str(e)[:100]}")
                last_exception = e
                self._record_failure(model_id, str(e), start_time)
        
        # 所有模型都失败
        self._record_complete_failure(start_time)
        
        if last_exception:
            raise last_exception
        else:
            raise Exception(f"所有模型都失败，降级链: {chain_id}")
    
    def _get_fallback_sequence(
        self, 
        chain: FallbackChainConfig,
        initial_model: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        获取降级序列
        
        Args:
            chain: 降级链配置
            initial_model: 初始模型
            context: 上下文信息
            
        Returns:
            List[str]: 模型尝试序列
        """
        # 构建完整的模型列表
        all_models = []
        
        # 添加初始模型（如果指定）
        if initial_model and initial_model != chain.primary_model:
            all_models.append(initial_model)
        
        # 添加主模型
        if chain.primary_model not in all_models:
            all_models.append(chain.primary_model)
        
        # 添加次要模型
        for model in chain.secondary_models:
            if model not in all_models:
                all_models.append(model)
        
        # 添加备用模型
        for model in chain.fallback_models:
            if model not in all_models:
                all_models.append(model)
        
        # 添加应急模型
        if chain.emergency_model and chain.emergency_model not in all_models:
            all_models.append(chain.emergency_model)
        
        # 根据上下文调整顺序（例如，基于成本或性能）
        if context and ("prefer_cost" in context or "prefer_performance" in context):
            all_models = self._sort_models_by_preference(
                all_models, chain, context
            )
        
        return all_models
    
    def _sort_models_by_preference(
        self,
        models: List[str],
        chain: FallbackChainConfig,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        根据偏好对模型排序
        
        Args:
            models: 模型列表
            chain: 降级链配置
            context: 上下文信息
            
        Returns:
            List[str]: 排序后的模型列表
        """
        # 简单的排序实现
        # 在实际系统中，这里可以根据成本、性能、健康状态等复杂逻辑进行排序
        
        prefer_cost = context.get("prefer_cost", False)
        prefer_performance = context.get("prefer_performance", False)
        
        # 获取模型权重
        cost_weights = chain.cost_weights
        perf_weights = chain.performance_weights
        
        # 计算综合得分
        model_scores = []
        for model in models:
            cost_score = cost_weights.get(model, 1.0)
            perf_score = perf_weights.get(model, 0.5)
            
            if prefer_cost:
                # 成本越低越好
                score = -cost_score  # 负号表示成本越低得分越高
            elif prefer_performance:
                # 性能越高越好
                score = perf_score
            else:
                # 默认：平衡成本和性能
                score = perf_score - 0.5 * cost_score
            
            model_scores.append((model, score))
        
        # 按得分排序（降序）
        model_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [model for model, score in model_scores]
    
    def _is_model_available(self, model_id: str) -> bool:
        """
        检查模型是否可用
        
        Args:
            model_id: 模型标识符
            
        Returns:
            bool: 是否可用
        """
        # 检查模型是否已注册
        if model_id not in self.model_health:
            self.logger.warning(f"模型未注册: {model_id}")
            return False
        
        # 检查健康状态
        health = self.model_health[model_id]
        return health.is_healthy
    
    def _record_success(self, model_id: str, start_time: float) -> None:
        """
        记录成功
        
        Args:
            model_id: 模型标识符
            start_time: 开始时间
        """
        # 更新模型健康状态
        if model_id in self.model_health:
            health = self.model_health[model_id]
            
            # 计算响应时间
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 更新平均响应时间（指数移动平均）
            if health.avg_response_time == 0:
                health.avg_response_time = response_time
            else:
                alpha = 0.1  # 平滑因子
                health.avg_response_time = (1 - alpha) * health.avg_response_time + alpha * response_time
            
            # 更新其他统计
            health.success_count += 1
            health.last_check_time = time.time()
            health.consecutive_failures = 0
            health.circuit_state = self.circuit_breakers[model_id].state.value
        
        # 更新服务统计
        with self.stats_lock:
            self.stats.total_requests += 1
            self.stats.successful_requests += 1
    
    def _record_failure(self, model_id: str, error: str, start_time: float) -> None:
        """
        记录失败
        
        Args:
            model_id: 模型标识符
            error: 错误信息
            start_time: 开始时间
        """
        # 更新模型健康状态
        if model_id in self.model_health:
            health = self.model_health[model_id]
            
            health.failure_count += 1
            health.last_error = error
            health.last_error_time = time.time()
            health.last_check_time = time.time()
            health.consecutive_failures += 1
            
            # 如果连续失败次数过多，标记为不健康
            if health.consecutive_failures >= 3:
                health.is_healthy = False
                self.logger.warning(f"模型标记为不健康: {model_id} (连续失败 {health.consecutive_failures} 次)")
            
            health.circuit_state = self.circuit_breakers[model_id].state.value
        
        # 更新服务统计
        with self.stats_lock:
            self.stats.total_requests += 1
            self.stats.failed_requests += 1
    
    def _record_fallback(self, fallback_level: int, start_time: float) -> None:
        """
        记录降级
        
        Args:
            fallback_level: 降级级别（0=主模型，1=第一次降级，以此类推）
            start_time: 开始时间
        """
        with self.stats_lock:
            self.stats.fallback_triggered += 1
            
            # 计算降级延迟
            fallback_time = (time.time() - start_time) * 1000  # 转换为毫秒
            self.stats.total_fallback_time_ms += fallback_time
            
            # 更新平均降级延迟
            if self.stats.fallback_triggered > 0:
                self.stats.avg_fallback_latency_ms = (
                    self.stats.total_fallback_time_ms / self.stats.fallback_triggered
                )
    
    def _record_circuit_trip(self, model_id: str) -> None:
        """
        记录断路器跳闸
        
        Args:
            model_id: 模型标识符
        """
        with self.stats_lock:
            self.stats.circuit_breaker_trips += 1
    
    def _record_complete_failure(self, start_time: float) -> None:
        """
        记录完全失败（所有模型都失败）
        
        Args:
            start_time: 开始时间
        """
        with self.stats_lock:
            self.stats.total_requests += 1
            self.stats.failed_requests += 1
    
    def get_model_health(self, model_id: str) -> Optional[ModelHealth]:
        """
        获取模型健康状态
        
        Args:
            model_id: 模型标识符
            
        Returns:
            ModelHealth: 健康状态，或None
        """
        return self.model_health.get(model_id)
    
    def get_all_health_status(self) -> Dict[str, ModelHealth]:
        """
        获取所有模型健康状态
        
        Returns:
            Dict[str, ModelHealth]: 健康状态字典
        """
        return self.model_health.copy()
    
    def get_stats(self) -> FaultToleranceStats:
        """
        获取统计信息
        
        Returns:
            FaultToleranceStats: 统计信息
        """
        with self.stats_lock:
            return self.stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        with self.stats_lock:
            self.stats = FaultToleranceStats()
            self.logger.info("统计信息已重置")
    
    def start_health_check(self, interval: int = 300) -> None:
        """
        启动健康检查线程
        
        Args:
            interval: 检查间隔（秒）
        """
        if self._health_check_thread and self._health_check_thread.is_alive():
            self.logger.warning("健康检查线程已在运行")
            return
        
        self._health_check_interval = interval
        self._stop_health_check.clear()
        
        self._health_check_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True,
            name="FaultToleranceHealthCheck"
        )
        
        self._health_check_thread.start()
        self.logger.info(f"健康检查线程已启动，间隔: {interval}秒")
    
    def stop_health_check(self) -> None:
        """停止健康检查线程"""
        if self._health_check_thread:
            self._stop_health_check.set()
            self._health_check_thread.join(timeout=5)
            self.logger.info("健康检查线程已停止")
    
    def _health_check_loop(self) -> None:
        """健康检查循环"""
        while not self._stop_health_check.is_set():
            try:
                self._perform_health_check()
            except Exception as e:
                self.logger.error(f"健康检查失败: {e}")
            
            # 等待下一次检查
            self._stop_health_check.wait(self._health_check_interval)
    
    def _perform_health_check(self) -> None:
        """执行健康检查"""
        self.logger.debug("执行健康检查")
        
        for model_id, health in self.model_health.items():
            try:
                # 这里应该执行实际的健康检查
                # 例如：发送一个简单的测试请求或检查连接
                # 目前仅更新最后检查时间
                health.last_check_time = time.time()
                
                # 如果模型之前标记为不健康，但已经过了一段时间，尝试恢复
                if not health.is_healthy:
                    recovery_time = 300  # 5分钟
                    if time.time() - health.last_error_time > recovery_time:
                        health.is_healthy = True
                        health.consecutive_failures = 0
                        self.logger.info(f"模型恢复健康: {model_id}")
                
            except Exception as e:
                self.logger.warning(f"模型健康检查失败 {model_id}: {e}")
    
    def force_model_healthy(self, model_id: str, healthy: bool) -> None:
        """
        强制设置模型健康状态
        
        Args:
            model_id: 模型标识符
            healthy: 健康状态
        """
        if model_id in self.model_health:
            self.model_health[model_id].is_healthy = healthy
            self.logger.info(f"强制设置模型 {model_id} 健康状态为: {healthy}")
        else:
            self.logger.warning(f"模型未注册: {model_id}")
    
    def reset_circuit_breaker(self, model_id: str) -> None:
        """
        重置模型断路器
        
        Args:
            model_id: 模型标识符
        """
        if model_id in self.circuit_breakers:
            # 重新创建断路器
            circuit_config = self.default_circuit_config.copy()
            self.circuit_breakers[model_id] = CircuitBreaker(
                failure_threshold=circuit_config["failure_threshold"],
                recovery_timeout=circuit_config["recovery_timeout"],
                name=f"FT-{model_id}"
            )
            
            # 更新健康状态
            if model_id in self.model_health:
                self.model_health[model_id].circuit_state = "CLOSED"
                self.model_health[model_id].consecutive_failures = 0
            
            self.logger.info(f"重置模型断路器: {model_id}")
        else:
            self.logger.warning(f"模型未注册: {model_id}")
    
    def export_config(self, file_path: str) -> None:
        """
        导出配置到文件
        
        Args:
            file_path: 文件路径
        """
        config = {
            "fallback_chains": {},
            "circuit_breaker": self.default_circuit_config,
            "model_health": {}
        }
        
        # 导出降级链
        for chain_id, chain in self.fallback_chains.items():
            config["fallback_chains"][chain_id] = asdict(chain)
        
        # 导出模型健康状态
        for model_id, health in self.model_health.items():
            config["model_health"][model_id] = health.to_dict()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"配置已导出到: {file_path}")
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            raise


# 全局实例（单例模式）
_fault_tolerance_service = None
_fault_tolerance_lock = threading.RLock()


def get_fault_tolerance_service(config_file: Optional[str] = None) -> FaultToleranceService:
    """
    获取故障容忍服务实例（单例模式）
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        FaultToleranceService: 服务实例
    """
    global _fault_tolerance_service
    
    with _fault_tolerance_lock:
        if _fault_tolerance_service is None:
            _fault_tolerance_service = FaultToleranceService(config_file)
        
        return _fault_tolerance_service


__all__ = [
    "ModelPriority",
    "FailureType",
    "ModelHealth",
    "FallbackChainConfig",
    "FaultToleranceStats",
    "FaultToleranceService",
    "get_fault_tolerance_service",
]