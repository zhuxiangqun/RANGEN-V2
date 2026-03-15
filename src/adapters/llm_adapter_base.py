#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM适配器基类 - 多模型架构的统一接口

提供所有LLM模型适配器应遵循的标准接口和基础实现。
支持DeepSeek、Step-3.5-Flash、本地开源模型等。

设计原则：
1. 统一接口：所有适配器提供相同的调用方法
2. 错误处理：标准化的错误处理和重试机制
3. 配置管理：一致的配置参数和验证
4. 可扩展性：易于添加新的模型提供商
5. 向后兼容：与现有系统兼容

注意：所有具体适配器应继承自此类并实现抽象方法。
"""

import os
import time
import json
import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM提供商枚举"""
    DEEPSEEK = "deepseek"
    STEPFLASH = "stepflash"
    LOCAL_LLAMA = "local_llama"
    LOCAL_QWEN = "local_qwen"
    LOCAL_PHI3 = "local_phi3"
    OPENAI = "openai"
    CLAUDE = "claude"
    MOCK = "mock"  # 用于测试的模拟提供商


class AdapterCapability(str, Enum):
    """适配器能力枚举"""
    CHAT_COMPLETION = "chat_completion"      # 聊天完成
    EMBEDDING = "embedding"                  # 向量嵌入
    FUNCTION_CALLING = "function_calling"    # 函数调用
    REASONING = "reasoning"                  # 推理能力
    CODE_GENERATION = "code_generation"      # 代码生成
    SUMMARIZATION = "summarization"          # 摘要生成
    TRANSLATION = "translation"              # 翻译


@dataclass
class LLMResponse:
    """统一的LLM响应格式"""
    success: bool                    # 请求是否成功
    content: Optional[str]          # 模型回复内容（成功时）
    provider: str                   # 模型提供商
    model: str                      # 具体模型名称
    usage: Dict[str, Any]          # Token使用情况
    latency_ms: float              # 请求延迟（毫秒）
    error_message: Optional[str]   # 错误信息（失败时）
    error_code: Optional[str]      # 错误代码（失败时）
    request_id: Optional[str]      # 请求ID（用于跟踪）
    metadata: Dict[str, Any]       # 附加元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMResponse':
        """从字典创建响应对象"""
        return cls(**data)


@dataclass
class LLMRequest:
    """统一的LLM请求格式"""
    messages: List[Dict[str, str]]  # 消息列表 [{"role": "user", "content": "..."}]
    model: Optional[str] = None     # 指定模型（可选，使用适配器默认）
    temperature: float = 0.7        # 温度参数
    max_tokens: int = 2000          # 最大生成token数
    stream: bool = False            # 是否流式输出
    system_prompt: Optional[str] = None  # 系统提示词
    functions: Optional[List[Dict]] = None  # 函数定义（函数调用）
    function_call: Optional[Union[str, Dict]] = None  # 函数调用设置
    seed: Optional[int] = None      # 随机种子
    top_p: float = 1.0              # Top-p采样
    frequency_penalty: float = 0.0  # 频率惩罚
    presence_penalty: float = 0.0   # 存在惩罚
    stop: Optional[List[str]] = None  # 停止词
    user: Optional[str] = None      # 用户标识
    metadata: Dict[str, Any] = None  # 附加元数据
    
    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AdapterConfig:
    """适配器配置"""
    provider: LLMProvider            # 提供商类型
    model_name: str                  # 模型名称
    api_key: Optional[str] = None    # API密钥
    base_url: Optional[str] = None   # 基础URL
    timeout: int = 60                # 请求超时时间（秒）
    max_retries: int = 3             # 最大重试次数
    retry_delay: float = 2.0         # 重试延迟（秒）
    max_tokens: int = 4000           # 最大token数
    temperature: float = 0.7         # 温度参数
    enable_cache: bool = False       # 是否启用缓存
    cache_ttl: int = 3600            # 缓存过期时间（秒）
    capabilities: List[AdapterCapability] = None  # 支持的能力
    
    def __post_init__(self):
        """初始化后处理"""
        if self.capabilities is None:
            self.capabilities = [AdapterCapability.CHAT_COMPLETION]


class BaseLLMAdapter(ABC):
    """LLM适配器基类
    
    所有具体适配器必须继承此类并实现抽象方法。
    """
    
    def __init__(self, config: AdapterConfig):
        """
        初始化适配器
        
        Args:
            config: 适配器配置
        """
        self.config = config
        self.provider = config.provider
        self.model_name = config.model_name
        self.api_key = config.api_key
        self.base_url = config.base_url
        self.timeout = config.timeout
        self.max_retries = config.max_retries
        self.retry_delay = config.retry_delay
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
        self.enable_cache = config.enable_cache
        self.cache_ttl = config.cache_ttl
        self.capabilities = config.capabilities
        
        # 缓存相关（如果启用）
        self._cache = {}
        self._cache_lock = threading.RLock()
        self._cache_stats = {"hits": 0, "misses": 0, "size": 0}
        
        # 性能统计
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency_ms": 0.0,
            "last_request_time": None
        }
        self._stats_lock = threading.RLock()
        
        # 验证配置
        self._validate_config()
        
        logger.info(f"初始化 {self.provider.value} 适配器: {self.model_name}")
    
    def _validate_config(self) -> None:
        """验证配置"""
        if not self.model_name:
            raise ValueError("模型名称不能为空")
        
        # 验证API密钥（如果提供商需要）
        if self.provider not in [LLMProvider.MOCK, LLMProvider.LOCAL_PHI3, 
                                LLMProvider.LOCAL_LLAMA, LLMProvider.LOCAL_QWEN]:
            if not self.api_key:
                logger.warning(f"{self.provider.value} 适配器未提供API密钥，"
                             f"将尝试从环境变量获取")
    
    @abstractmethod
    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """
        聊天完成 - 核心抽象方法
        
        所有具体适配器必须实现此方法。
        
        Args:
            request: LLM请求对象
            
        Returns:
            LLM响应对象
        """
        pass
    
    def sync_chat_completion(self, request: LLMRequest) -> LLMResponse:
        """
        同步版本的聊天完成
        
        默认实现将异步方法转换为同步调用。
        适配器可以覆盖此方法以提供更高效的同步实现。
        
        Args:
            request: LLM请求对象
            
        Returns:
            LLM响应对象
        """
        import asyncio
        try:
            # 如果已有事件循环，使用它
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在运行的事件循环中，需要创建新任务
                # 这里使用简单的同步桥接
                return self._sync_chat_completion_fallback(request)
            else:
                # 没有运行的事件循环，直接运行
                return loop.run_until_complete(self.chat_completion(request))
        except RuntimeError:
            # 没有事件循环，创建新的
            return asyncio.run(self.chat_completion(request))
    
    def _sync_chat_completion_fallback(self, request: LLMRequest) -> LLMResponse:
        """同步聊天完成的回退实现"""
        # 简单实现：记录警告并返回错误
        logger.warning(f"{self.provider.value} 适配器未实现同步方法，"
                      f"使用异步方法可能造成阻塞")
        
        # 尝试导入asyncio并运行
        try:
            import asyncio
            return asyncio.run(self.chat_completion(request))
        except Exception as e:
            logger.error(f"同步调用失败: {e}")
            return LLMResponse(
                success=False,
                content=None,
                provider=self.provider.value,
                model=self.model_name,
                usage={},
                latency_ms=0.0,
                error_message=f"同步调用失败: {str(e)}",
                error_code="SYNC_CALL_FAILED",
                request_id=None,
                metadata={"async_fallback_used": True}
            )
    
    async def chat_completion_simple(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> LLMResponse:
        """
        简化版的聊天完成
        
        为了方便使用，提供此简化方法。
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            **kwargs: 其他参数，将传递给LLMRequest
            
        Returns:
            LLM响应对象
        """
        # 从kwargs构建LLMRequest
        request_kwargs = {
            "messages": messages,
            "model": kwargs.get("model"),
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": kwargs.get("stream", False),
            "system_prompt": kwargs.get("system_prompt"),
            "functions": kwargs.get("functions"),
            "function_call": kwargs.get("function_call"),
            "seed": kwargs.get("seed"),
            "top_p": kwargs.get("top_p", 1.0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
            "stop": kwargs.get("stop"),
            "user": kwargs.get("user"),
            "metadata": kwargs.get("metadata", {})
        }
        
        # 创建请求对象
        request = LLMRequest(**request_kwargs)
        
        # 调用核心方法
        return await self.chat_completion(request)
    
    def sync_chat_completion_simple(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> LLMResponse:
        """
        同步简化版的聊天完成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            LLM响应对象
        """
        request_kwargs = {
            "messages": messages,
            "model": kwargs.get("model"),
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": kwargs.get("stream", False),
            "system_prompt": kwargs.get("system_prompt"),
            "functions": kwargs.get("functions"),
            "function_call": kwargs.get("function_call"),
            "seed": kwargs.get("seed"),
            "top_p": kwargs.get("top_p", 1.0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
            "stop": kwargs.get("stop"),
            "user": kwargs.get("user"),
            "metadata": kwargs.get("metadata", {})
        }
        
        request = LLMRequest(**request_kwargs)
        return self.sync_chat_completion(request)
    
    def has_capability(self, capability: AdapterCapability) -> bool:
        """
        检查适配器是否支持特定能力
        
        Args:
            capability: 要检查的能力
            
        Returns:
            是否支持
        """
        return capability in self.capabilities
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取适配器统计信息
        
        Returns:
            统计信息字典
        """
        with self._stats_lock:
            stats = self._stats.copy()
            
            # 计算平均延迟
            if stats["total_requests"] > 0:
                stats["avg_latency_ms"] = (
                    stats["total_latency_ms"] / stats["total_requests"]
                )
            else:
                stats["avg_latency_ms"] = 0.0
            
            # 计算成功率
            if stats["total_requests"] > 0:
                stats["success_rate"] = (
                    stats["successful_requests"] / stats["total_requests"]
                )
            else:
                stats["success_rate"] = 0.0
            
            # 添加缓存统计
            stats["cache"] = self._cache_stats.copy()
            
            return stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        with self._stats_lock:
            self._stats = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_latency_ms": 0.0,
                "last_request_time": None
            }
    
    def _update_stats(self, success: bool, latency_ms: float) -> None:
        """更新统计信息"""
        with self._stats_lock:
            self._stats["total_requests"] += 1
            if success:
                self._stats["successful_requests"] += 1
            else:
                self._stats["failed_requests"] += 1
            
            self._stats["total_latency_ms"] += latency_ms
            self._stats["last_request_time"] = datetime.now().isoformat()
    
    # 缓存相关方法
    def _generate_cache_key(self, request: LLMRequest) -> str:
        """
        生成缓存键
        
        Args:
            request: LLM请求
            
        Returns:
            缓存键字符串
        """
        import hashlib
        
        # 序列化请求的关键部分
        cache_data = {
            "messages": request.messages,
            "model": request.model or self.model_name,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "system_prompt": request.system_prompt,
        }
        
        # 添加函数调用相关数据（如果存在）
        if request.functions:
            cache_data["functions"] = request.functions
        
        # 生成哈希
        cache_json = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_json.encode()).hexdigest()
        
        return f"{self.provider.value}:{self.model_name}:{cache_hash}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[LLMResponse]:
        """
        从缓存获取响应
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存的响应，或None
        """
        if not self.enable_cache:
            return None
        
        with self._cache_lock:
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                created_time, response = entry
                
                # 检查是否过期
                current_time = time.time()
                if current_time - created_time <= self.cache_ttl:
                    # 缓存命中，更新统计
                    self._cache_stats["hits"] += 1
                    
                    # 更新缓存访问时间（可选，用于LRU）
                    self._cache[cache_key] = (created_time, response)
                    
                    logger.debug(f"缓存命中: {cache_key}")
                    return response
                else:
                    # 缓存过期，删除
                    del self._cache[cache_key]
                    self._cache_stats["size"] -= 1
            
            # 缓存未命中
            self._cache_stats["misses"] += 1
            return None
    
    def _save_to_cache(self, cache_key: str, response: LLMResponse) -> None:
        """
        保存响应到缓存
        
        Args:
            cache_key: 缓存键
            response: 要缓存的响应
        """
        if not self.enable_cache:
            return
        
        with self._cache_lock:
            # 检查缓存大小，如果超过限制则清理（简单LRU实现）
            max_cache_size = getattr(self, 'max_cache_size', 1000)
            if len(self._cache) >= max_cache_size:
                # 删除最旧的条目（这里简化处理，删除第一个）
                if self._cache:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    self._cache_stats["size"] -= 1
            
            # 保存新条目
            self._cache[cache_key] = (time.time(), response)
            self._cache_stats["size"] += 1
    
    def clear_cache(self) -> None:
        """清空缓存"""
        with self._cache_lock:
            self._cache.clear()
            self._cache_stats["size"] = 0
            logger.info(f"已清空 {self.provider.value} 适配器缓存")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息
        
        Returns:
            缓存信息字典
        """
        with self._cache_lock:
            return {
                "enabled": self.enable_cache,
                "size": self._cache_stats["size"],
                "hits": self._cache_stats["hits"],
                "misses": self._cache_stats["misses"],
                "ttl_seconds": self.cache_ttl,
                "hit_rate": (
                    self._cache_stats["hits"] / 
                    (self._cache_stats["hits"] + self._cache_stats["misses"])
                    if (self._cache_stats["hits"] + self._cache_stats["misses"]) > 0
                    else 0.0
                )
            }
    
    # 辅助方法
    def _create_error_response(
        self, 
        error_message: str, 
        error_code: str = "UNKNOWN_ERROR",
        request_id: Optional[str] = None
    ) -> LLMResponse:
        """
        创建错误响应
        
        Args:
            error_message: 错误信息
            error_code: 错误代码
            request_id: 请求ID
            
        Returns:
            错误响应对象
        """
        return LLMResponse(
            success=False,
            content=None,
            provider=self.provider.value,
            model=self.model_name,
            usage={},
            latency_ms=0.0,
            error_message=error_message,
            error_code=error_code,
            request_id=request_id,
            metadata={"error_timestamp": datetime.now().isoformat()}
        )
    
    def _create_success_response(
        self,
        content: str,
        usage: Dict[str, Any],
        latency_ms: float,
        request_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        创建成功响应
        
        Args:
            content: 回复内容
            usage: Token使用情况
            latency_ms: 请求延迟（毫秒）
            request_id: 请求ID
            **kwargs: 其他元数据
            
        Returns:
            成功响应对象
        """
        metadata = {
            "response_timestamp": datetime.now().isoformat(),
            **kwargs
        }
        
        return LLMResponse(
            success=True,
            content=content,
            provider=self.provider.value,
            model=self.model_name,
            usage=usage,
            latency_ms=latency_ms,
            error_message=None,
            error_code=None,
            request_id=request_id,
            metadata=metadata
        )
    
    # 兼容性方法（用于与现有系统集成）
    async def call_llm(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        **kwargs
    ) -> Optional[str]:
        """
        兼容现有系统的LLM调用接口
        
        实现UnifiedLLMInterface协议。
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 其他参数
            
        Returns:
            模型回复内容，或None（失败时）
        """
        # 构建消息列表
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        # 构建请求
        request_kwargs = {
            "messages": messages,
            "system_prompt": system_prompt,
        }
        
        # 传递其他参数
        for key in ["temperature", "max_tokens", "stream", "functions", 
                   "function_call", "seed", "top_p", "frequency_penalty",
                   "presence_penalty", "stop", "user"]:
            if key in kwargs:
                request_kwargs[key] = kwargs[key]
        
        request = LLMRequest(**request_kwargs)
        
        # 调用适配器
        response = await self.chat_completion(request)
        
        if response.success:
            return response.content
        else:
            logger.error(f"LLM调用失败: {response.error_message}")
            return None
    
    def _call_llm(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        **kwargs
    ) -> Optional[str]:
        """
        同步版本的call_llm方法
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 其他参数
            
        Returns:
            模型回复内容，或None
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        request_kwargs = {
            "messages": messages,
            "system_prompt": system_prompt,
        }
        
        for key in ["temperature", "max_tokens", "stream", "functions", 
                   "function_call", "seed", "top_p", "frequency_penalty",
                   "presence_penalty", "stop", "user"]:
            if key in kwargs:
                request_kwargs[key] = kwargs[key]
        
        request = LLMRequest(**request_kwargs)
        response = self.sync_chat_completion(request)
        
        if response.success:
            return response.content
        else:
            logger.error(f"LLM调用失败: {response.error_message}")
            return None