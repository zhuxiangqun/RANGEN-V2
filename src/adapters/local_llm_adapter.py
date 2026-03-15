#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地LLM适配器

支持本地部署的LLM模型，如：
- Llama（通过Ollama、vLLM等）
- Qwen（通过Ollama、vLLM等）
- Phi-3（通过llama.cpp、Ollama等）
- 其他本地部署的模型

设计原则：
1. 统一接口：与BaseLLMAdapter兼容
2. 灵活配置：支持多种本地部署方式
3. 容错处理：处理本地服务不可用情况
4. 性能监控：记录本地模型性能指标

注意：此适配器假设本地LLM服务提供OpenAI兼容的API接口。
"""

import os
import logging
import time
import json
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional, Union
from dataclasses import asdict

from .llm_adapter_base import (
    BaseLLMAdapter,
    LLMProvider,
    AdapterConfig,
    LLMRequest,
    LLMResponse,
    AdapterCapability,
)

logger = logging.getLogger(__name__)


class LocalLLMAdapter(BaseLLMAdapter):
    """本地LLM适配器
    
    支持与本地LLM服务通信，假设这些服务提供OpenAI兼容的API接口。
    典型的本地服务包括：
    - Ollama (http://localhost:11434/v1)
    - vLLM (http://localhost:8000/v1)
    - llama.cpp server (http://localhost:8080/v1)
    - 其他兼容OpenAI API的服务
    """
    
    # 支持的提供商映射到默认配置
    DEFAULT_CONFIGS = {
        LLMProvider.LOCAL_LLAMA: {
            "default_base_url": "http://localhost:11434/v1",  # Ollama默认
            "default_model": "llama2",
            "capabilities": [
                AdapterCapability.CHAT_COMPLETION,
                AdapterCapability.SUMMARIZATION,
                AdapterCapability.TRANSLATION,
            ]
        },
        LLMProvider.LOCAL_QWEN: {
            "default_base_url": "http://localhost:11434/v1",
            "default_model": "qwen2.5",
            "capabilities": [
                AdapterCapability.CHAT_COMPLETION,
                AdapterCapability.CODE_GENERATION,
                AdapterCapability.TRANSLATION,
            ]
        },
        LLMProvider.LOCAL_PHI3: {
            "default_base_url": "http://localhost:11434/v1",
            "default_model": "phi3",
            "capabilities": [
                AdapterCapability.CHAT_COMPLETION,
                AdapterCapability.SUMMARIZATION,
                AdapterCapability.REASONING,
            ]
        }
    }
    
    def __init__(self, config: AdapterConfig):
        """初始化本地LLM适配器
        
        Args:
            config: 适配器配置
        """
        # 确保有默认配置
        if not config.base_url and self.provider in self.DEFAULT_CONFIGS:
            default_config = self.DEFAULT_CONFIGS[self.provider]
            # 创建一个新的配置对象，避免修改原始配置
            config_dict = asdict(config)
            config_dict["base_url"] = default_config["default_base_url"]
            config = AdapterConfig(**config_dict)
            
        # 如果模型名称未指定，使用默认值
        if not config.model_name and self.provider in self.DEFAULT_CONFIGS:
            default_config = self.DEFAULT_CONFIGS[self.provider]
            config_dict = asdict(config)
            config_dict["model_name"] = default_config["default_model"]
            config = AdapterConfig(**config_dict)
            
        # 如果能力列表未指定，使用默认值
        if not config.capabilities and self.provider in self.DEFAULT_CONFIGS:
            default_config = self.DEFAULT_CONFIGS[self.provider]
            config_dict = asdict(config)
            config_dict["capabilities"] = default_config["capabilities"]
            config = AdapterConfig(**config_dict)
        
        # 调用父类初始化
        super().__init__(config)
        
        # HTTP客户端会话
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()
        
        # 本地服务健康状态
        self._is_healthy = True
        self._last_health_check = 0
        self._health_check_interval = 60  # 秒
        
        logger.info(f"初始化本地LLM适配器: {self.provider.value}/{self.model_name}")
        logger.info(f"使用基础URL: {self.base_url}")
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """确保HTTP会话存在"""
        async with self._session_lock:
            if self._session is None or self._session.closed:
                # 创建新会话
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                self._session = aiohttp.ClientSession(timeout=timeout)
                logger.debug(f"创建新的HTTP会话: {self.base_url}")
            
            return self._session
    
    async def _check_health(self) -> bool:
        """检查本地服务是否健康"""
        current_time = time.time()
        if (current_time - self._last_health_check) < self._health_check_interval:
            # 最近已检查过，返回缓存结果
            return self._is_healthy
        
        try:
            session = await self._ensure_session()
            
            # 尝试简单的健康检查端点
            health_url = f"{self.base_url}/health" if self.base_url else None
            if health_url:
                async with session.get(health_url) as response:
                    self._is_healthy = response.status == 200
            else:
                # 如果没有健康检查端点，尝试模型列表端点
                models_url = f"{self.base_url}/models" if self.base_url else None
                if models_url:
                    async with session.get(models_url) as response:
                        self._is_healthy = response.status == 200
                else:
                    # 无法检查健康状态，假设健康
                    self._is_healthy = True
            
            self._last_health_check = current_time
            
            if not self._is_healthy:
                logger.warning(f"本地服务健康检查失败: {self.base_url}")
            else:
                logger.debug(f"本地服务健康检查通过: {self.base_url}")
                
        except Exception as e:
            logger.warning(f"本地服务健康检查异常: {e}")
            self._is_healthy = False
            self._last_health_check = current_time
        
        return self._is_healthy
    
    async def _make_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """向本地服务发送HTTP请求
        
        Args:
            request_data: 请求数据
            
        Returns:
            响应数据字典
        """
        # 检查服务健康状态
        if not await self._check_health():
            raise ConnectionError(f"本地服务不可用: {self.base_url}")
        
        session = await self._ensure_session()
        url = f"{self.base_url}/chat/completions"
        
        # 添加重试逻辑
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                async with session.post(
                    url,
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    latency_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        response_data = await response.json()
                        
                        # 记录性能指标
                        with self._stats_lock:
                            self._stats["total_requests"] += 1
                            self._stats["successful_requests"] += 1
                            self._stats["total_latency_ms"] += latency_ms
                            self._stats["last_request_time"] = time.time()
                        
                        logger.debug(f"本地LLM请求成功: {self.provider.value} "
                                   f"({latency_ms:.0f}ms)")
                        
                        return response_data
                    else:
                        error_text = await response.text()
                        last_error = f"HTTP {response.status}: {error_text}"
                        logger.warning(f"本地LLM请求失败 ({attempt+1}/{self.max_retries+1}): "
                                     f"{last_error}")
                        
                        # 如果不是最后一次尝试，等待后重试
                        if attempt < self.max_retries:
                            await asyncio.sleep(self.retry_delay)
                            
            except aiohttp.ClientError as e:
                last_error = f"网络错误: {str(e)}"
                logger.warning(f"本地LLM网络错误 ({attempt+1}/{self.max_retries+1}): "
                             f"{last_error}")
                
                # 标记服务不健康
                self._is_healthy = False
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
            
            except Exception as e:
                last_error = f"意外错误: {str(e)}"
                logger.error(f"本地LLM请求异常: {e}")
                break
        
        # 所有尝试都失败
        with self._stats_lock:
            self._stats["total_requests"] += 1
            self._stats["failed_requests"] += 1
        
        raise ConnectionError(f"本地LLM请求失败: {last_error}")
    
    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """聊天完成接口实现
        
        Args:
            request: LLM请求对象
            
        Returns:
            LLM响应对象
        """
        start_time = time.time()
        request_id = f"local_{int(start_time * 1000)}_{hash(str(request)) % 10000:04d}"
        
        try:
            # 构建OpenAI兼容的请求格式
            request_data = {
                "model": request.model or self.model_name,
                "messages": request.messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": request.stream,
                "top_p": request.top_p,
                "frequency_penalty": request.frequency_penalty,
                "presence_penalty": request.presence_penalty,
                "stop": request.stop,
                "seed": request.seed,
            }
            
            # 添加系统提示词（如果存在）
            if request.system_prompt:
                # 将系统提示词添加到消息列表开头
                system_message = {"role": "system", "content": request.system_prompt}
                request_data["messages"] = [system_message] + request_data["messages"]
            
            # 发送请求
            response_data = await self._make_request(request_data)
            
            # 解析响应
            if request.stream:
                # 流式响应处理（简化版）
                # 注意：实际实现需要处理流式数据
                content = ""
                usage = {}
                
                # 模拟非流式处理
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    choice = response_data["choices"][0]
                    if "message" in choice:
                        content = choice["message"].get("content", "")
                
                if "usage" in response_data:
                    usage = response_data["usage"]
            else:
                # 非流式响应
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    choice = response_data["choices"][0]
                    content = choice.get("message", {}).get("content", "")
                else:
                    content = ""
                
                usage = response_data.get("usage", {})
            
            latency_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                success=True,
                content=content,
                provider=self.provider.value,
                model=request_data["model"],
                usage=usage,
                latency_ms=latency_ms,
                error_message=None,
                error_code=None,
                request_id=request_id,
                metadata={
                    "local_service": self.base_url,
                    "attempts": 1,  # 实际尝试次数
                    "cached": False,
                }
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"本地LLM适配器请求失败: {e}")
            
            return LLMResponse(
                success=False,
                content=None,
                provider=self.provider.value,
                model=self.model_name,
                usage={},
                latency_ms=latency_ms,
                error_message=str(e),
                error_code="LOCAL_SERVICE_ERROR",
                request_id=request_id,
                metadata={
                    "local_service": self.base_url,
                    "error_type": type(e).__name__,
                }
            )
    
    async def close(self):
        """关闭适配器，释放资源"""
        async with self._session_lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None
                logger.debug("已关闭本地LLM适配器HTTP会话")
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        if self._session and not self._session.closed:
            # 注意：在析构函数中不能使用async，这里只是记录警告
            logger.warning(f"本地LLM适配器 {self.provider.value} 未正确关闭，可能有资源泄漏")


# 适配器注册函数
def register_local_adapters():
    """注册所有本地适配器到工厂"""
    try:
        # 导入工厂
        from .llm_adapter_factory import LLMAdapterFactory
        
        # 注册本地适配器
        LLMAdapterFactory.register_adapter(LLMProvider.LOCAL_LLAMA, LocalLLMAdapter)
        LLMAdapterFactory.register_adapter(LLMProvider.LOCAL_QWEN, LocalLLMAdapter)
        LLMAdapterFactory.register_adapter(LLMProvider.LOCAL_PHI3, LocalLLMAdapter)
        
        logger.info("已注册本地LLM适配器")
        
    except Exception as e:
        logger.error(f"注册本地适配器失败: {e}")


# 模块导入时自动注册适配器
try:
    register_local_adapters()
except Exception as e:
    logger.warning(f"自动注册本地适配器失败: {e}")
    # 不阻止模块加载，适配器可以在需要时手动注册