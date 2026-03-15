#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM适配器工厂 - 多模型架构的适配器创建

提供统一的适配器创建接口，支持所有LLM提供商。
基于配置文件或代码参数动态创建适配器实例。

设计原则：
1. 统一创建接口：所有适配器通过相同方式创建
2. 配置驱动：适配器配置统一管理
3. 懒加载：按需创建适配器实例
4. 单例模式：相同配置返回相同实例
5. 类型安全：提供完整的类型提示

注意：此工厂与现有LLMAdapterFactory共存以保持向后兼容。
"""

import os
import logging
import threading
from typing import Dict, Any, Optional, Type, Union
from dataclasses import asdict

from .llm_adapter_base import (
    BaseLLMAdapter,
    LLMProvider,
    AdapterConfig,
    LLMResponse,
    LLMRequest,
)

logger = logging.getLogger(__name__)


class LLMAdapterFactory:
    """LLM适配器工厂（新版本）"""
    
    _instances = {}  # 适配器实例缓存（单例模式）
    _instance_lock = threading.RLock()
    
    # 适配器类映射
    _adapter_classes = {}
    
    @classmethod
    def register_adapter(
        cls, 
        provider: Union[LLMProvider, str], 
        adapter_class: Type[BaseLLMAdapter]
    ) -> None:
        """
        注册适配器类
        
        Args:
            provider: 提供商类型
            adapter_class: 适配器类（必须继承BaseLLMAdapter）
        """
        if isinstance(provider, str):
            try:
                provider = LLMProvider(provider)
            except ValueError:
                raise ValueError(f"无效的提供商: {provider}")
        
        # 验证适配器类
        if not issubclass(adapter_class, BaseLLMAdapter):
            raise TypeError(f"适配器类必须继承BaseLLMAdapter: {adapter_class}")
        
        with cls._instance_lock:
            cls._adapter_classes[provider] = adapter_class
            logger.info(f"已注册适配器: {provider.value} -> {adapter_class.__name__}")
    
    @classmethod
    def create_adapter(
        cls, 
        config: Union[AdapterConfig, Dict[str, Any], str],
        **kwargs
    ) -> BaseLLMAdapter:
        """
        创建适配器实例
        
        Args:
            config: 适配器配置（AdapterConfig对象、字典或提供商字符串）
            **kwargs: 额外的配置参数（当config为字符串时使用）
            
        Returns:
            BaseLLMAdapter: 适配器实例
            
        Raises:
            ValueError: 如果提供商不支持或配置无效
            TypeError: 如果适配器类无效
        """
        # 解析配置参数
        adapter_config = cls._parse_config(config, **kwargs)
        
        # 生成缓存键（基于配置哈希）
        cache_key = cls._generate_cache_key(adapter_config)
        
        with cls._instance_lock:
            # 检查是否已有实例
            if cache_key in cls._instances:
                logger.debug(f"返回缓存的适配器实例: {cache_key}")
                return cls._instances[cache_key]
            
            # 获取适配器类
            adapter_class = cls._get_adapter_class(adapter_config.provider)
            if adapter_class is None:
                raise ValueError(f"未注册的提供商: {adapter_config.provider.value}")
            
            # 创建新实例
            logger.info(f"创建新的适配器实例: {adapter_config.provider.value}")
            instance = adapter_class(adapter_config)
            
            # 缓存实例
            cls._instances[cache_key] = instance
            
            return instance
    
    @classmethod
    def create_adapter_simple(
        cls,
        provider: Union[LLMProvider, str],
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ) -> BaseLLMAdapter:
        """
        简化版适配器创建
        
        Args:
            provider: 提供商类型
            model_name: 模型名称
            api_key: API密钥
            base_url: 基础URL
            **kwargs: 其他配置参数
            
        Returns:
            BaseLLMAdapter: 适配器实例
        """
        # 解析提供商
        if isinstance(provider, str):
            try:
                provider = LLMProvider(provider)
            except ValueError:
                raise ValueError(f"无效的提供商: {provider}")
        
        # 构建配置
        config_dict = {
            "provider": provider,
            "model_name": model_name,
            "api_key": api_key,
            "base_url": base_url,
        }
        
        # 添加其他参数
        for key, value in kwargs.items():
            if hasattr(AdapterConfig, key):
                config_dict[key] = value
        
        # 创建配置对象
        config = AdapterConfig(**config_dict)
        
        return cls.create_adapter(config)
    
    @classmethod
    def _parse_config(
        cls, 
        config: Union[AdapterConfig, Dict[str, Any], str],
        **kwargs
    ) -> AdapterConfig:
        """
        解析配置参数
        
        Args:
            config: 配置参数
            **kwargs: 额外参数
            
        Returns:
            AdapterConfig: 配置对象
        """
        if isinstance(config, AdapterConfig):
            # 已经是配置对象
            return config
        
        elif isinstance(config, dict):
            # 字典配置
            config_dict = config.copy()
            
            # 从kwargs更新
            config_dict.update(kwargs)
            
            # 解析提供商
            provider = config_dict.get("provider")
            if isinstance(provider, str):
                try:
                    config_dict["provider"] = LLMProvider(provider)
                except ValueError:
                    raise ValueError(f"无效的提供商: {provider}")
            
            return AdapterConfig(**config_dict)
        
        elif isinstance(config, str):
            # 提供商字符串
            try:
                provider = LLMProvider(config)
            except ValueError:
                raise ValueError(f"无效的提供商: {config}")
            
            # 构建配置字典
            config_dict = {
                "provider": provider,
                "model_name": kwargs.get("model_name", f"{provider.value}_default"),
                "api_key": kwargs.get("api_key"),
                "base_url": kwargs.get("base_url"),
            }
            
            # 添加其他参数
            for key in ["timeout", "max_retries", "retry_delay", "max_tokens", 
                       "temperature", "enable_cache", "cache_ttl", "capabilities"]:
                if key in kwargs:
                    config_dict[key] = kwargs[key]
            
            return AdapterConfig(**config_dict)
        
        else:
            raise TypeError(f"不支持的配置类型: {type(config)}")
    
    @classmethod
    def _generate_cache_key(cls, config: AdapterConfig) -> str:
        """
        生成缓存键
        
        Args:
            config: 适配器配置
            
        Returns:
            str: 缓存键
        """
        import hashlib
        
        # 创建配置字典（排除敏感信息）
        config_dict = asdict(config)
        
        # 移除API密钥（避免在缓存键中包含敏感信息）
        if "api_key" in config_dict:
            config_dict["api_key"] = "***" if config_dict["api_key"] else None
        
        # 序列化并哈希
        config_json = json.dumps(config_dict, sort_keys=True)
        config_hash = hashlib.md5(config_json.encode()).hexdigest()
        
        return f"{config.provider.value}:{config.model_name}:{config_hash}"
    
    @classmethod
    def _get_adapter_class(cls, provider: LLMProvider) -> Optional[Type[BaseLLMAdapter]]:
        """
        获取适配器类
        
        Args:
            provider: 提供商
            
        Returns:
            Type[BaseLLMAdapter]: 适配器类，或None
        """
        return cls._adapter_classes.get(provider)
    
    @classmethod
    def get_registered_providers(cls) -> list:
        """
        获取已注册的提供商列表
        
        Returns:
            list: 已注册的提供商列表
        """
        with cls._instance_lock:
            return list(cls._adapter_classes.keys())
    
    @classmethod
    def get_available_adapters(cls) -> Dict[str, Any]:
        """
        获取可用适配器信息
        
        Returns:
            Dict[str, Any]: 适配器信息字典
        """
        result = {
            "providers": [],
            "instances": len(cls._instances),
            "registered_adapters": {}
        }
        
        with cls._instance_lock:
            for provider, adapter_class in cls._adapter_classes.items():
                result["providers"].append(provider.value)
                result["registered_adapters"][provider.value] = {
                    "class": adapter_class.__name__,
                    "module": adapter_class.__module__
                }
        
        return result
    
    @classmethod
    def clear_instance_cache(cls) -> None:
        """清空实例缓存"""
        with cls._instance_lock:
            instance_count = len(cls._instances)
            cls._instances.clear()
            logger.info(f"已清空适配器实例缓存，释放 {instance_count} 个实例")
    
    @classmethod
    def get_instance_stats(cls) -> Dict[str, Any]:
        """
        获取实例统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with cls._instance_lock:
            provider_stats = {}
            for cache_key, instance in cls._instances.items():
                provider = instance.provider.value
                if provider not in provider_stats:
                    provider_stats[provider] = 0
                provider_stats[provider] += 1
            
            return {
                "total_instances": len(cls._instances),
                "provider_distribution": provider_stats,
                "cache_keys": list(cls._instances.keys())
            }


# 导入json模块（用于缓存键生成）
import json


# 默认适配器注册（在模块导入时注册）
def _register_default_adapters():
    """注册默认适配器"""
    try:
        # 尝试导入并注册StepFlash适配器
        from .stepflash_adapter import StepFlashAdapter
        LLMAdapterFactory.register_adapter(LLMProvider.STEPFLASH, StepFlashAdapter)
        logger.info("已注册默认适配器: StepFlashAdapter")
    except ImportError:
        logger.warning("无法导入StepFlashAdapter，将跳过注册")
    
    # 注意：其他适配器（DeepSeek、LocalLLM等）需要在创建具体实现后手动注册


# 执行默认注册
_register_default_adapters()


__all__ = [
    "LLMAdapterFactory",
]