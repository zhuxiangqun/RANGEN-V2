#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
声明式配置系统 - 受Paperclip启发的配置管理

提供声明式装饰器来配置LLM模型、路由策略和处理器链。
设计原则：
1. 约定优于配置：提供合理的默认值
2. 声明式语法：使用装饰器简化配置
3. 类型安全：充分利用Python类型提示
4. 运行时注册：支持动态配置更新

示例用法：

@register_llm_model(
    name="deepseek-reasoner",
    provider=LLMProvider.DEEPSEEK,
    cost_per_token=0.00002,
    capabilities=[AdapterCapability.CHAT_COMPLETION, AdapterCapability.REASONING]
)
class DeepSeekReasonerModel(BaseLLMAdapter):
    pass

@register_routing_strategy(
    name="cost_optimized",
    description="成本优先路由策略",
    processors=["cost_calculator", "quality_validator", "fallback_handler"]
)
class CostOptimizedStrategy(RoutingStrategy):
    pass
"""

import functools
import inspect
import logging
from typing import Dict, Any, List, Optional, Union, Type, Callable, Set
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
import threading
import asyncio

logger = logging.getLogger(__name__)


class ConfigRegistry:
    """配置注册中心 - 全局配置存储"""
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        """初始化注册表"""
        self.llm_models: Dict[str, Dict[str, Any]] = {}
        self.routing_strategies: Dict[str, Dict[str, Any]] = {}
        self.processors: Dict[str, Dict[str, Any]] = {}
        self.storage_backends: Dict[str, Dict[str, Any]] = {}
        self.validators: Dict[str, Dict[str, Any]] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # 存储支持
        self._storage = None
        self._storage_namespace = "config_registry"
        self._auto_save = True
        
        # 默认配置
        self._defaults = {
            "llm_model": {
                "enabled": True,
                "timeout": 60,
                "max_retries": 3,
                "retry_delay": 1.0,
                "max_tokens": 4000,
                "temperature": 0.7,
                "stream": False,
            },
            "routing_strategy": {
                "enabled": True,
                "priority": 5,  # 1-10, 10最高
                "requires_auth": False,
                "supports_streaming": True,
            },
            "processor": {
                "enabled": True,
                "async_execution": False,
                "timeout": 10.0,
                "retryable": True,
            }
        }
        
        logger.info("声明式配置注册中心已初始化")
    
    def register_llm_model(self, config: Dict[str, Any], model_class: Type) -> str:
        """注册LLM模型"""
        from datetime import datetime as dt
        model_name = config["name"]
        
        with self._lock:
            # 合并默认配置
            full_config = self._defaults["llm_model"].copy()
            full_config.update(config)
            full_config["class"] = model_class
            full_config["registered_at"] = dt.now().isoformat()
            
            self.llm_models[model_name] = full_config
            
            logger.info(f"已注册LLM模型: {model_name} ({model_class.__name__})")
        
        # 触发配置注册事件
        try:
            from .event_system import ConfigRegisteredEvent, EventMetadata
            from datetime import datetime
            metadata = EventMetadata(
                event_id="dummy",
                event_type="config.registered",
                timestamp=datetime.now(),
                source="config_registry"
            )
            event = ConfigRegisteredEvent(
                metadata=metadata,
                config_type="llm_model",
                config_name=model_name,
                config_data=full_config.copy(),
                source_class=model_class.__name__
            )
            self.emit_event("registered", event_data=event)
        except ImportError:
            # 事件系统不可用，静默跳过
            pass
        
        # 异步保存到存储（不等待）
        if self._storage and self._auto_save:
            asyncio.create_task(self._save_to_storage("llm_model", model_name, full_config))
        
        return model_name
    
    def register_routing_strategy(self, config: Dict[str, Any], strategy_class: Type) -> str:
        """注册路由策略"""
        from datetime import datetime as dt
        strategy_name = config["name"]
        
        with self._lock:
            # 合并默认配置
            full_config = self._defaults["routing_strategy"].copy()
            full_config.update(config)
            full_config["class"] = strategy_class
            full_config["registered_at"] = dt.now().isoformat()
            
            self.routing_strategies[strategy_name] = full_config
            
            logger.info(f"已注册路由策略: {strategy_name} ({strategy_class.__name__})")
        
        # 触发配置注册事件
        try:
            from .event_system import ConfigRegisteredEvent, EventMetadata
            from datetime import datetime
            metadata = EventMetadata(
                event_id="dummy",
                event_type="config.registered",
                timestamp=datetime.now(),
                source="config_registry"
            )
            event = ConfigRegisteredEvent(
                metadata=metadata,
                config_type="routing_strategy",
                config_name=strategy_name,
                config_data=full_config.copy(),
                source_class=strategy_class.__name__
            )
            self.emit_event("registered", event_data=event)
        except ImportError:
            # 事件系统不可用，静默跳过
            pass
        
        # 异步保存到存储（不等待）
        if self._storage and self._auto_save:
            asyncio.create_task(self._save_to_storage("routing_strategy", strategy_name, full_config))
        
        return strategy_name
    
    def register_processor(self, config: Dict[str, Any], processor_class: Type) -> str:
        """注册处理器"""
        from datetime import datetime as dt
        processor_name = config["name"]
        
        with self._lock:
            # 合并默认配置
            full_config = self._defaults["processor"].copy()
            full_config.update(config)
            full_config["class"] = processor_class
            full_config["registered_at"] = dt.now().isoformat()
            
            self.processors[processor_name] = full_config
            
            logger.info(f"已注册处理器: {processor_name} ({processor_class.__name__})")
        
        # 触发配置注册事件
        try:
            from .event_system import ConfigRegisteredEvent, EventMetadata
            from datetime import datetime
            metadata = EventMetadata(
                event_id="dummy",
                event_type="config.registered",
                timestamp=datetime.now(),
                source="config_registry"
            )
            event = ConfigRegisteredEvent(
                metadata=metadata,
                config_type="processor",
                config_name=processor_name,
                config_data=full_config.copy(),
                source_class=processor_class.__name__
            )
            self.emit_event("registered", event_data=event)
        except ImportError:
            # 事件系统不可用，静默跳过
            pass
        
        # 异步保存到存储（不等待）
        if self._storage and self._auto_save:
            asyncio.create_task(self._save_to_storage("processor", processor_name, full_config))
        
        return processor_name
    
    def get_llm_model(self, name: str) -> Optional[Dict[str, Any]]:
        """获取LLM模型配置"""
        with self._lock:
            return self.llm_models.get(name)
    
    def get_routing_strategy(self, name: str) -> Optional[Dict[str, Any]]:
        """获取路由策略配置"""
        with self._lock:
            return self.routing_strategies.get(name)
    
    def get_processor(self, name: str) -> Optional[Dict[str, Any]]:
        """获取处理器配置"""
        with self._lock:
            return self.processors.get(name)
    
    def list_llm_models(self) -> List[str]:
        """列出所有注册的LLM模型"""
        with self._lock:
            return list(self.llm_models.keys())
    
    def list_routing_strategies(self) -> List[str]:
        """列出所有注册的路由策略"""
        with self._lock:
            return list(self.routing_strategies.keys())
    
    def list_processors(self) -> List[str]:
        """列出所有注册的处理器"""
        with self._lock:
            return list(self.processors.keys())
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """添加事件处理器"""
        with self._lock:
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(handler)
            logger.debug(f"已添加事件处理器: {event_type} -> {handler.__name__}")
    
    def emit_event(self, event_type: str, **kwargs):
        """触发事件"""
        with self._lock:
            handlers = self.event_handlers.get(event_type, [])
            for handler in handlers:
                try:
                    handler(**kwargs)
                except Exception as e:
                    logger.error(f"事件处理器执行失败 {event_type}/{handler.__name__}: {e}")
    
    # ============================================================================
    # 存储支持方法
    # ============================================================================
    
    def set_storage(self, storage, namespace: str = "config_registry", auto_save: bool = True):
        """设置存储后端
        
        参数:
            storage: 存储实例（从storage_abstraction导入）
            namespace: 存储命名空间
            auto_save: 是否自动保存配置到存储
        """
        with self._lock:
            self._storage = storage
            self._storage_namespace = namespace
            self._auto_save = auto_save
            logger.info(f"已设置存储后端: {namespace}, 自动保存: {auto_save}")
    
    def get_storage(self):
        """获取存储后端"""
        return self._storage
    
    def _get_storage_key(self, category: str, name: str) -> str:
        """获取存储键"""
        return f"{self._storage_namespace}:{category}:{name}"
    
    async def _save_to_storage(self, category: str, name: str, data: Dict[str, Any]):
        """保存数据到存储"""
        if not self._storage or not self._auto_save:
            return
        
        try:
            storage_key = self._get_storage_key(category, name)
            success = await self._storage.save(storage_key, data, immediate=False)
            if success:
                logger.debug(f"配置已保存到存储: {storage_key}")
            else:
                logger.warning(f"配置保存到存储失败: {storage_key}")
        except Exception as e:
            logger.error(f"保存到存储失败 {category}/{name}: {e}")
    
    async def _load_from_storage(self, category: str, name: str) -> Optional[Dict[str, Any]]:
        """从存储加载数据"""
        if not self._storage:
            return None
        
        try:
            storage_key = self._get_storage_key(category, name)
            data = await self._storage.load(storage_key, use_cache=True)
            if data:
                logger.debug(f"配置从存储加载: {storage_key}")
            return data
        except Exception as e:
            logger.error(f"从存储加载失败 {category}/{name}: {e}")
            return None
    
    async def load_all_from_storage(self):
        """从存储加载所有配置（简化实现）"""
        if not self._storage:
            logger.warning("未设置存储后端，无法加载配置")
            return False
        
        try:
            # 注意：实际实现需要扫描存储中的所有键
            # 这里简化实现，仅记录日志
            logger.info("从存储加载所有配置（简化实现）")
            return True
        except Exception as e:
            logger.error(f"从存储加载所有配置失败: {e}")
            return False
    
    async def save_all_to_storage(self):
        """保存所有配置到存储"""
        if not self._storage:
            logger.warning("未设置存储后端，无法保存配置")
            return False
        
        try:
            with self._lock:
                # 保存LLM模型
                for name, config in self.llm_models.items():
                    storage_key = self._get_storage_key("llm_model", name)
                    await self._storage.save(storage_key, config, immediate=True)
                
                # 保存路由策略
                for name, config in self.routing_strategies.items():
                    storage_key = self._get_storage_key("routing_strategy", name)
                    await self._storage.save(storage_key, config, immediate=True)
                
                # 保存处理器
                for name, config in self.processors.items():
                    storage_key = self._get_storage_key("processor", name)
                    await self._storage.save(storage_key, config, immediate=True)
            
            logger.info(f"所有配置已保存到存储: {len(self.llm_models)} 模型, "
                       f"{len(self.routing_strategies)} 策略, {len(self.processors)} 处理器")
            return True
        except Exception as e:
            logger.error(f"保存所有配置到存储失败: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        if not self._storage:
            return {"storage_enabled": False}
        
        try:
            stats = self._storage.get_stats()
            stats["storage_enabled"] = True
            stats["storage_namespace"] = self._storage_namespace
            stats["auto_save"] = self._auto_save
            stats["cached_items"] = {
                "llm_models": len(self.llm_models),
                "routing_strategies": len(self.routing_strategies),
                "processors": len(self.processors),
            }
            return stats
        except Exception as e:
            logger.error(f"获取存储统计信息失败: {e}")
            return {"storage_enabled": False, "error": str(e)}


# 全局注册中心实例
_registry = ConfigRegistry()


def get_config_registry() -> ConfigRegistry:
    """获取配置注册中心实例"""
    return _registry


# ============================================================================
# 声明式装饰器
# ============================================================================

def register_llm_model(
    name: str,
    provider: Union[str, Enum],
    model: Optional[str] = None,
    cost_per_token: float = 0.0,
    capabilities: Optional[List[Union[str, Enum]]] = None,
    base_url: Optional[str] = None,
    api_key_env: Optional[str] = None,
    timeout: int = 60,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    stream: bool = False,
    enabled: bool = True,
    **kwargs
):
    """
    注册LLM模型的装饰器
    
    参数：
    - name: 模型名称（唯一标识符）
    - provider: 提供商（字符串或枚举）
    - model: 实际模型标识符（如"deepseek-reasoner"）
    - cost_per_token: 每token成本（美元）
    - capabilities: 能力列表
    - base_url: API基础URL
    - api_key_env: API密钥环境变量名
    - timeout: 超时时间（秒）
    - max_retries: 最大重试次数
    - retry_delay: 重试延迟（秒）
    - max_tokens: 最大token数
    - temperature: 温度参数
    - stream: 是否支持流式响应
    - enabled: 是否启用
    - **kwargs: 其他配置参数
    """
    def decorator(cls):
        # 准备配置
        config = {
            "name": name,
            "provider": provider.value if isinstance(provider, Enum) else provider,
            "model": model or name,
            "cost_per_token": cost_per_token,
            "capabilities": [
                cap.value if isinstance(cap, Enum) else cap 
                for cap in (capabilities or [])
            ],
            "base_url": base_url,
            "api_key_env": api_key_env,
            "timeout": timeout,
            "max_retries": max_retries,
            "retry_delay": retry_delay,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
            "enabled": enabled,
        }
        config.update(kwargs)
        
        # 注册模型
        _registry.register_llm_model(config, cls)
        
        # 添加类属性
        cls.config_name = name
        cls.config_provider = config["provider"]
        cls.config_model = config["model"]
        cls.config_enabled = enabled
        
        # 确保类有必要的属性
        if not hasattr(cls, 'name'):
            cls.name = name
        
        return cls
    
    return decorator


def register_routing_strategy(
    name: str,
    description: str = "",
    processors: Optional[List[str]] = None,
    default_model: Optional[str] = None,
    fallback_chain: Optional[List[str]] = None,
    cost_weight: float = 0.6,
    performance_weight: float = 0.4,
    quality_weight: float = 0.0,
    enable_circuit_breaker: bool = True,
    circuit_failure_threshold: int = 5,
    circuit_recovery_timeout: int = 60,
    enabled: bool = True,
    priority: int = 5,
    requires_auth: bool = False,
    supports_streaming: bool = True,
    **kwargs
):
    """
    注册路由策略的装饰器
    
    参数：
    - name: 策略名称（唯一标识符）
    - description: 策略描述
    - processors: 处理器链（按顺序执行）
    - default_model: 默认模型
    - fallback_chain: 降级链（模型列表）
    - cost_weight: 成本权重（0-1）
    - performance_weight: 性能权重（0-1）
    - quality_weight: 质量权重（0-1）
    - enable_circuit_breaker: 是否启用断路器
    - circuit_failure_threshold: 断路器失败阈值
    - circuit_recovery_timeout: 断路器恢复超时（秒）
    - enabled: 是否启用
    - priority: 优先级（1-10）
    - requires_auth: 是否需要认证
    - supports_streaming: 是否支持流式响应
    - **kwargs: 其他配置参数
    """
    def decorator(cls):
        # 准备配置
        config = {
            "name": name,
            "description": description,
            "processors": processors or [],
            "default_model": default_model,
            "fallback_chain": fallback_chain or [],
            "cost_weight": cost_weight,
            "performance_weight": performance_weight,
            "quality_weight": quality_weight,
            "enable_circuit_breaker": enable_circuit_breaker,
            "circuit_failure_threshold": circuit_failure_threshold,
            "circuit_recovery_timeout": circuit_recovery_timeout,
            "enabled": enabled,
            "priority": priority,
            "requires_auth": requires_auth,
            "supports_streaming": supports_streaming,
        }
        config.update(kwargs)
        
        # 注册策略
        _registry.register_routing_strategy(config, cls)
        
        # 添加类属性
        cls.config_name = name
        cls.config_processors = processors or []
        cls.config_enabled = enabled
        
        # 确保类有必要的属性
        if not hasattr(cls, 'name'):
            cls.name = name
        
        return cls
    
    return decorator


def register_processor(
    name: str,
    description: str = "",
    input_type: Optional[Type] = None,
    output_type: Optional[Type] = None,
    async_execution: bool = False,
    timeout: float = 10.0,
    retryable: bool = True,
    max_retries: int = 3,
    requires_config: bool = False,
    enabled: bool = True,
    **kwargs
):
    """
    注册处理器的装饰器
    
    参数：
    - name: 处理器名称（唯一标识符）
    - description: 处理器描述
    - input_type: 输入类型（用于类型检查）
    - output_type: 输出类型（用于类型检查）
    - async_execution: 是否异步执行
    - timeout: 超时时间（秒）
    - retryable: 是否可重试
    - max_retries: 最大重试次数
    - requires_config: 是否需要配置
    - enabled: 是否启用
    - **kwargs: 其他配置参数
    """
    def decorator(cls):
        # 准备配置
        config = {
            "name": name,
            "description": description,
            "input_type": input_type,
            "output_type": output_type,
            "async_execution": async_execution,
            "timeout": timeout,
            "retryable": retryable,
            "max_retries": max_retries,
            "requires_config": requires_config,
            "enabled": enabled,
        }
        config.update(kwargs)
        
        # 注册处理器
        _registry.register_processor(config, cls)
        
        # 添加类属性
        cls.config_name = name
        cls.config_enabled = enabled
        
        # 确保类有process方法
        if not hasattr(cls, 'process'):
            if async_execution:
                raise TypeError(f"异步处理器 {name} 必须实现 async process 方法")
            else:
                raise TypeError(f"处理器 {name} 必须实现 process 方法")
        
        return cls
    
    return decorator


def on_event(event_type: str):
    """
    事件处理器装饰器
    
    参数：
    - event_type: 事件类型
    """
    def decorator(func):
        _registry.add_event_handler(event_type, func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ============================================================================
# 辅助函数
# ============================================================================

def emit_config_event(event_type: str, **kwargs):
    """触发配置事件"""
    _registry.emit_event(event_type, **kwargs)


def get_llm_model_config(name: str) -> Optional[Dict[str, Any]]:
    """获取LLM模型配置"""
    return _registry.get_llm_model(name)


def get_routing_strategy_config(name: str) -> Optional[Dict[str, Any]]:
    """获取路由策略配置"""
    return _registry.get_routing_strategy(name)


def get_processor_config(name: str) -> Optional[Dict[str, Any]]:
    """获取处理器配置"""
    return _registry.get_processor(name)


def list_available_models() -> List[str]:
    """列出可用模型"""
    return _registry.list_llm_models()


def list_available_strategies() -> List[str]:
    """列出可用策略"""
    return _registry.list_routing_strategies()


def list_available_processors() -> List[str]:
    """列出可用处理器"""
    return _registry.list_processors()