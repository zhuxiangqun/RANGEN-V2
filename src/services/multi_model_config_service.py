#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模型配置服务 - 扩展基础配置服务以支持多模型架构

提供针对多模型架构的专用配置管理功能：
1. 模型提供商配置管理
2. 路由策略配置
3. 成本优化配置
4. 故障转移配置
5. 性能基准配置

设计原则：
- 扩展性：在基础配置服务之上构建，不破坏现有功能
- 模块化：配置按功能模块组织
- 验证：所有配置都经过严格验证
- 热更新：支持运行时配置更新
- 向后兼容：与现有配置格式兼容
"""

import os
import json
import logging
import threading
from typing import Dict, Any, List, Optional, Union, Set
from enum import Enum
from dataclasses import dataclass, asdict, field
from datetime import datetime

from .config_service import ConfigService

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """模型提供商枚举"""
    DEEPSEEK = "deepseek"
    STEPFLASH = "stepflash"
    LOCAL_LLAMA = "local_llama"
    LOCAL_QWEN = "local_qwen"
    LOCAL_PHI3 = "local_phi3"
    OPENAI = "openai"
    CLAUDE = "claude"
    MOCK = "mock"


class RoutingStrategy(str, Enum):
    """路由策略枚举"""
    COST_FIRST = "cost_first"          # 成本优先
    PERFORMANCE_FIRST = "performance_first"  # 性能优先
    BALANCED = "balanced"              # 平衡策略
    MANUAL = "manual"                  # 手动指定
    AUTO = "auto"                      # 自动选择
    FALLBACK_CHAIN = "fallback_chain"  # 降级链


@dataclass
class ModelConfig:
    """单个模型配置"""
    provider: ModelProvider            # 提供商
    model_id: str                      # 模型标识符
    display_name: str                  # 显示名称
    api_key_env: Optional[str] = None  # API密钥环境变量名
    base_url: Optional[str] = None     # 基础URL
    timeout: int = 60                  # 超时时间（秒）
    max_tokens: int = 4000             # 最大token数
    temperature: float = 0.7           # 温度参数
    enabled: bool = True               # 是否启用
    cost_per_token: float = 0.0        # 每token成本（美元）
    max_requests_per_minute: int = 60  # 每分钟最大请求数
    capabilities: List[str] = field(default_factory=list)  # 能力列表
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """从字典创建配置对象"""
        # 处理provider字段
        if isinstance(data.get('provider'), str):
            try:
                data['provider'] = ModelProvider(data['provider'])
            except ValueError:
                logger.warning(f"无效的提供商: {data['provider']}")
                data['provider'] = ModelProvider.MOCK
        
        return cls(**data)


@dataclass
class RoutingConfig:
    """路由配置"""
    strategy: RoutingStrategy          # 路由策略
    primary_model: Optional[str] = None  # 主模型（手动策略时使用）
    fallback_chain: List[str] = field(default_factory=list)  # 降级链
    cost_weight: float = 0.6          # 成本权重（0-1）
    performance_weight: float = 0.4   # 性能权重（0-1）
    enable_circuit_breaker: bool = True  # 是否启用断路器
    circuit_failure_threshold: int = 5  # 断路器失败阈值
    circuit_recovery_timeout: int = 60  # 断路器恢复超时（秒）
    enable_cache: bool = False        # 是否启用缓存
    cache_ttl: int = 3600             # 缓存过期时间（秒）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['strategy'] = self.strategy.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoutingConfig':
        """从字典创建配置对象"""
        # 处理strategy字段
        if isinstance(data.get('strategy'), str):
            try:
                data['strategy'] = RoutingStrategy(data['strategy'])
            except ValueError:
                logger.warning(f"无效的路由策略: {data['strategy']}")
                data['strategy'] = RoutingStrategy.BALANCED
        
        return cls(**data)


@dataclass
class CostOptimizationConfig:
    """成本优化配置"""
    enable_cost_tracking: bool = True     # 是否启用成本跟踪
    monthly_budget: float = 100.0         # 月度预算（美元）
    daily_spending_limit: float = 5.0     # 每日支出限制（美元）
    alert_threshold_percent: float = 80.0 # 告警阈值百分比
    enable_token_optimization: bool = True  # 是否启用token优化
    max_context_length: int = 8000        # 最大上下文长度
    enable_compression: bool = False      # 是否启用上下文压缩
    compression_ratio: float = 0.5        # 压缩比例
    enable_caching: bool = True           # 是否启用缓存
    cache_hit_ratio_target: float = 0.7   # 缓存命中率目标
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class PerformanceBenchmarkConfig:
    """性能基准配置"""
    enable_benchmarking: bool = True      # 是否启用基准测试
    benchmark_interval_hours: int = 24    # 基准测试间隔（小时）
    test_prompts: List[str] = field(default_factory=list)  # 测试提示词
    expected_response_time_ms: float = 3000.0  # 期望响应时间（毫秒）
    min_success_rate: float = 0.95        # 最低成功率
    enable_auto_tuning: bool = False      # 是否启用自动调优
    tuning_interval_hours: int = 168      # 调优间隔（小时，一周）
    performance_metrics: List[str] = field(default_factory=list)  # 性能指标
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.test_prompts:
            self.test_prompts = [
                "Hello, how are you?",
                "What is the capital of France?",
                "Explain quantum computing in simple terms.",
                "Write a Python function to calculate factorial.",
                "Translate 'good morning' to Chinese."
            ]
        
        if not self.performance_metrics:
            self.performance_metrics = [
                "response_time_ms",
                "success_rate",
                "token_usage",
                "cost_per_request"
            ]


class MultiModelConfigService:
    """多模型配置服务"""
    
    _instance = None
    _lock = threading.RLock()
    
    # 默认配置
    _default_config = {
        "models": {},
        "routing": {
            "strategy": "balanced",
            "enable_circuit_breaker": True,
            "circuit_failure_threshold": 5,
            "circuit_recovery_timeout": 60
        },
        "cost_optimization": {
            "enable_cost_tracking": True,
            "monthly_budget": 100.0,
            "daily_spending_limit": 5.0
        },
        "performance_benchmark": {
            "enable_benchmarking": True,
            "benchmark_interval_hours": 24
        }
    }
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MultiModelConfigService, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化服务"""
        self.logger = logging.getLogger(__name__)
        self.base_config_service = ConfigService()
        
        # 配置缓存
        self._config_cache = {}
        self._config_timestamp = {}
        
        # 监听配置变化
        self._config_listeners = []
        
        self.logger.info("多模型配置服务初始化完成")
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """
        获取模型配置
        
        Args:
            model_id: 模型标识符
            
        Returns:
            ModelConfig: 模型配置，或None
        """
        cache_key = f"model_{model_id}"
        
        # 检查缓存
        if cache_key in self._config_cache:
            cached_config, timestamp = self._config_cache[cache_key]
            # 如果缓存未过期（5分钟），返回缓存
            if time.time() - timestamp < 300:
                return cached_config
        
        # 从基础配置服务加载
        config_path = f"multi_model.models.{model_id}"
        raw_config = self.base_config_service.get(config_path)
        
        if not raw_config:
            # 尝试从默认配置加载
            default_models = self._get_default_models()
            if model_id in default_models:
                raw_config = default_models[model_id]
            else:
                self.logger.warning(f"未找到模型配置: {model_id}")
                return None
        
        # 创建配置对象
        try:
            config_dict = raw_config.copy()
            config_dict["model_id"] = model_id
            
            # 确保有display_name
            if "display_name" not in config_dict:
                config_dict["display_name"] = model_id.replace("_", " ").title()
            
            model_config = ModelConfig.from_dict(config_dict)
            
            # 缓存配置
            self._config_cache[cache_key] = (model_config, time.time())
            
            return model_config
        except Exception as e:
            self.logger.error(f"解析模型配置失败 {model_id}: {e}")
            return None
    
    def get_all_model_configs(self) -> Dict[str, ModelConfig]:
        """
        获取所有模型配置
        
        Returns:
            Dict[str, ModelConfig]: 模型配置字典
        """
        # 从基础配置服务加载
        models_config = self.base_config_service.get("multi_model.models", {})
        
        result = {}
        
        # 处理显式配置的模型
        for model_id, raw_config in models_config.items():
            try:
                config_dict = raw_config.copy()
                config_dict["model_id"] = model_id
                
                if "display_name" not in config_dict:
                    config_dict["display_name"] = model_id.replace("_", " ").title()
                
                model_config = ModelConfig.from_dict(config_dict)
                result[model_id] = model_config
            except Exception as e:
                self.logger.error(f"解析模型配置失败 {model_id}: {e}")
        
        # 添加默认模型（如果未在配置中定义）
        default_models = self._get_default_models()
        for model_id, default_config in default_models.items():
            if model_id not in result:
                try:
                    config_dict = default_config.copy()
                    config_dict["model_id"] = model_id
                    config_dict["display_name"] = model_id.replace("_", " ").title()
                    
                    model_config = ModelConfig.from_dict(config_dict)
                    result[model_id] = model_config
                except Exception as e:
                    self.logger.error(f"创建默认模型配置失败 {model_id}: {e}")
        
        return result
    
    def get_enabled_model_configs(self) -> Dict[str, ModelConfig]:
        """
        获取启用的模型配置
        
        Returns:
            Dict[str, ModelConfig]: 启用的模型配置字典
        """
        all_configs = self.get_all_model_configs()
        return {model_id: config for model_id, config in all_configs.items() 
                if config.enabled}
    
    def get_routing_config(self) -> RoutingConfig:
        """
        获取路由配置
        
        Returns:
            RoutingConfig: 路由配置
        """
        cache_key = "routing_config"
        
        # 检查缓存
        if cache_key in self._config_cache:
            cached_config, timestamp = self._config_cache[cache_key]
            if time.time() - timestamp < 300:
                return cached_config
        
        # 从基础配置服务加载
        raw_config = self.base_config_service.get("multi_model.routing", {})
        
        # 合并默认配置
        default_routing = self._default_config["routing"].copy()
        default_routing.update(raw_config)
        
        # 创建配置对象
        try:
            routing_config = RoutingConfig.from_dict(default_routing)
            
            # 缓存配置
            self._config_cache[cache_key] = (routing_config, time.time())
            
            return routing_config
        except Exception as e:
            self.logger.error(f"解析路由配置失败: {e}")
            return RoutingConfig(strategy=RoutingStrategy.BALANCED)
    
    def get_cost_optimization_config(self) -> CostOptimizationConfig:
        """
        获取成本优化配置
        
        Returns:
            CostOptimizationConfig: 成本优化配置
        """
        cache_key = "cost_optimization_config"
        
        # 检查缓存
        if cache_key in self._config_cache:
            cached_config, timestamp = self._config_cache[cache_key]
            if time.time() - timestamp < 300:
                return cached_config
        
        # 从基础配置服务加载
        raw_config = self.base_config_service.get("multi_model.cost_optimization", {})
        
        # 合并默认配置
        default_cost = self._default_config["cost_optimization"].copy()
        default_cost.update(raw_config)
        
        # 创建配置对象
        try:
            cost_config = CostOptimizationConfig(**default_cost)
            
            # 缓存配置
            self._config_cache[cache_key] = (cost_config, time.time())
            
            return cost_config
        except Exception as e:
            self.logger.error(f"解析成本优化配置失败: {e}")
            return CostOptimizationConfig()
    
    def get_performance_benchmark_config(self) -> PerformanceBenchmarkConfig:
        """
        获取性能基准配置
        
        Returns:
            PerformanceBenchmarkConfig: 性能基准配置
        """
        cache_key = "performance_benchmark_config"
        
        # 检查缓存
        if cache_key in self._config_cache[cache_key]:
            cached_config, timestamp = self._config_cache[cache_key]
            if time.time() - timestamp < 300:
                return cached_config
        
        # 从基础配置服务加载
        raw_config = self.base_config_service.get("multi_model.performance_benchmark", {})
        
        # 合并默认配置
        default_benchmark = self._default_config["performance_benchmark"].copy()
        default_benchmark.update(raw_config)
        
        # 创建配置对象
        try:
            benchmark_config = PerformanceBenchmarkConfig(**default_benchmark)
            
            # 缓存配置
            self._config_cache[cache_key] = (benchmark_config, time.time())
            
            return benchmark_config
        except Exception as e:
            self.logger.error(f"解析性能基准配置失败: {e}")
            return PerformanceBenchmarkConfig()
    
    def save_model_config(self, model_config: ModelConfig) -> bool:
        """
        保存模型配置
        
        Args:
            model_config: 模型配置
            
        Returns:
            bool: 是否成功
        """
        try:
            # 转换为字典
            config_dict = model_config.to_dict()
            
            # 准备保存的数据
            save_dict = config_dict.copy()
            # 移除model_id字段（作为键使用）
            model_id = save_dict.pop("model_id")
            
            # 设置配置路径
            config_path = f"multi_model.models.{model_id}"
            
            # 保存到基础配置服务（如果支持）
            # 注意：这取决于基础配置服务是否支持动态更新
            # 这里我们只是记录日志，实际实现可能需要调用特定的API
            self.logger.info(f"保存模型配置: {model_id}")
            
            # 更新缓存
            cache_key = f"model_{model_id}"
            self._config_cache[cache_key] = (model_config, time.time())
            
            # 通知监听器
            self._notify_config_change("model", model_id)
            
            return True
        except Exception as e:
            self.logger.error(f"保存模型配置失败: {e}")
            return False
    
    def update_routing_config(self, updates: Dict[str, Any]) -> bool:
        """
        更新路由配置
        
        Args:
            updates: 更新字典
            
        Returns:
            bool: 是否成功
        """
        try:
            # 获取当前配置
            current_config = self.get_routing_config()
            current_dict = current_config.to_dict()
            
            # 应用更新
            current_dict.update(updates)
            
            # 创建新的配置对象
            new_config = RoutingConfig.from_dict(current_dict)
            
            # 更新缓存
            cache_key = "routing_config"
            self._config_cache[cache_key] = (new_config, time.time())
            
            # 通知监听器
            self._notify_config_change("routing", "routing")
            
            self.logger.info("路由配置已更新")
            return True
        except Exception as e:
            self.logger.error(f"更新路由配置失败: {e}")
            return False
    
    def validate_config(self, config_type: str, config_data: Dict[str, Any]) -> List[str]:
        """
        验证配置
        
        Args:
            config_type: 配置类型（model, routing, cost, benchmark）
            config_data: 配置数据
            
        Returns:
            List[str]: 错误消息列表（空列表表示验证通过）
        """
        errors = []
        
        if config_type == "model":
            # 验证模型配置
            required_fields = ["provider", "model_id"]
            for field in required_fields:
                if field not in config_data:
                    errors.append(f"缺少必填字段: {field}")
            
            # 验证提供商
            if "provider" in config_data:
                try:
                    ModelProvider(config_data["provider"])
                except ValueError:
                    errors.append(f"无效的提供商: {config_data['provider']}")
            
            # 验证成本
            if "cost_per_token" in config_data:
                cost = config_data["cost_per_token"]
                if not isinstance(cost, (int, float)) or cost < 0:
                    errors.append(f"无效的成本: {cost}")
        
        elif config_type == "routing":
            # 验证路由配置
            if "strategy" in config_data:
                try:
                    RoutingStrategy(config_data["strategy"])
                except ValueError:
                    errors.append(f"无效的路由策略: {config_data['strategy']}")
            
            # 验证权重
            if "cost_weight" in config_data:
                weight = config_data["cost_weight"]
                if not isinstance(weight, (int, float)) or weight < 0 or weight > 1:
                    errors.append(f"无效的成本权重: {weight}")
            
            if "performance_weight" in config_data:
                weight = config_data["performance_weight"]
                if not isinstance(weight, (int, float)) or weight < 0 or weight > 1:
                    errors.append(f"无效的性能权重: {weight}")
        
        return errors
    
    def export_config(self, file_path: str) -> bool:
        """
        导出配置到文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            config_data = {
                "models": {},
                "routing": self.get_routing_config().to_dict(),
                "cost_optimization": self.get_cost_optimization_config().to_dict(),
                "performance_benchmark": self.get_performance_benchmark_config().to_dict(),
                "export_timestamp": datetime.now().isoformat()
            }
            
            # 导出模型配置
            model_configs = self.get_all_model_configs()
            for model_id, config in model_configs.items():
                config_data["models"][model_id] = config.to_dict()
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"配置已导出到: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            return False
    
    def register_config_listener(self, listener: callable) -> None:
        """
        注册配置变化监听器
        
        Args:
            listener: 监听器函数（接受两个参数：config_type, config_id）
        """
        with self._lock:
            if listener not in self._config_listeners:
                self._config_listeners.append(listener)
                self.logger.debug(f"注册配置监听器: {listener.__name__}")
    
    def unregister_config_listener(self, listener: callable) -> None:
        """注销配置变化监听器"""
        with self._lock:
            if listener in self._config_listeners:
                self._config_listeners.remove(listener)
                self.logger.debug(f"注销配置监听器: {listener.__name__}")
    
    def _notify_config_change(self, config_type: str, config_id: str) -> None:
        """通知配置变化"""
        with self._lock:
            for listener in self._config_listeners:
                try:
                    listener(config_type, config_id)
                except Exception as e:
                    self.logger.error(f"配置监听器调用失败: {e}")
    
    def _get_default_models(self) -> Dict[str, Dict[str, Any]]:
        """获取默认模型配置"""
        return {
            "deepseek-chat": {
                "provider": "deepseek",
                "api_key_env": "DEEPSEEK_API_KEY",
                "base_url": "https://api.deepseek.com/v1",
                "cost_per_token": 0.000002,
                "max_requests_per_minute": 60,
                "capabilities": ["chat_completion", "reasoning", "code_generation"]
            },
            "step-3.5-flash": {
                "provider": "stepflash",
                "api_key_env": "STEPSFLASH_API_KEY",
                "base_url": None,  # 自动检测
                "cost_per_token": 0.0000005,
                "max_requests_per_minute": 100,
                "capabilities": ["chat_completion", "summarization", "translation"]
            },
            "local-llama": {
                "provider": "local_llama",
                "api_key_env": None,
                "base_url": "http://localhost:8000/v1",
                "cost_per_token": 0.0,
                "max_requests_per_minute": 30,
                "capabilities": ["chat_completion", "summarization"]
            },
            "local-qwen": {
                "provider": "local_qwen",
                "api_key_env": None,
                "base_url": "http://localhost:8001/v1",
                "cost_per_token": 0.0,
                "max_requests_per_minute": 30,
                "capabilities": ["chat_completion", "translation"]
            },
            "local-phi3": {
                "provider": "local_phi3",
                "api_key_env": None,
                "base_url": "http://localhost:8002/v1",
                "cost_per_token": 0.0,
                "max_requests_per_minute": 40,
                "capabilities": ["chat_completion"]
            },
            "mock": {
                "provider": "mock",
                "api_key_env": None,
                "base_url": None,
                "cost_per_token": 0.0,
                "max_requests_per_minute": 1000,
                "capabilities": ["chat_completion"]
            }
        }
    
    def clear_cache(self) -> None:
        """清空配置缓存"""
        with self._lock:
            self._config_cache.clear()
            self.logger.info("配置缓存已清空")


# 导入time模块（用于缓存时间戳）
import time


# 全局实例（单例模式）
_multi_model_config_service = None


def get_multi_model_config_service() -> MultiModelConfigService:
    """
    获取多模型配置服务实例（单例模式）
    
    Returns:
        MultiModelConfigService: 配置服务实例
    """
    global _multi_model_config_service
    
    if _multi_model_config_service is None:
        _multi_model_config_service = MultiModelConfigService()
    
    return _multi_model_config_service


__all__ = [
    "ModelProvider",
    "RoutingStrategy",
    "ModelConfig",
    "RoutingConfig",
    "CostOptimizationConfig",
    "PerformanceBenchmarkConfig",
    "MultiModelConfigService",
    "get_multi_model_config_service",
]