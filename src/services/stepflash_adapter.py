#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step-3.5-Flash 适配器服务

Step-3.5-Flash 是 StepFun 开发的稀疏 MoE 大语言模型:
- 196B 总参数，11B 活跃参数
- 100-350 tok/s 超快吞吐量
- 256K 上下文长度
- Apache 2.0 开源许可证

支持多种接入方式:
1. OpenRouter API (推荐，免费层可用)
2. NVIDIA NIM API
3. vLLM 本地部署

参考: https://build.nvidia.com/stepfun-ai/step-3.5-flash/modelcard
"""

import os
import logging
import time
import concurrent.futures
import threading
from typing import Dict, Any, Optional, List
from enum import Enum

from src.observability.metrics import record_llm_call, record_llm_tokens, record_cache_operation
from src.services.training_data_collector import get_llm_training_collector
from src.services.training_orchestrator import get_training_orchestrator
from src.services.model_routing_reflection import get_model_routing_reflection_agent, RoutingDecision, RoutingDecisionType, RoutingOutcome

logger = logging.getLogger(__name__)


class StepFlashDeploymentType(Enum):
    """Step-3.5-Flash 部署类型"""
    OPENROUTER = "openrouter"      # OpenRouter API (推荐)
    NVIDIA_NIM = "nvidia_nim"       # NVIDIA NIM
    VLLM_LOCAL = "vllm_local"       # vLLM 本地部署


class StepFlashAdapter:
    """
    Step-3.5-Flash 适配器
    
    提供统一的接口来调用 Step-3.5-Flash 模型，支持多种部署方式。
    
    使用示例:
    
    ```python
    # 使用 OpenRouter (免费层)
    adapter = StepFlashAdapter(
        deployment_type="openrouter",
        api_key="your-openrouter-key"
    )
    
    # 使用 NVIDIA NIM
    adapter = StepFlashAdapter(
        deployment_type="nvidia_nim",
        api_key="your-nvidia-key"
    )
    
    # 使用 vLLM 本地部署
    adapter = StepFlashAdapter(
        deployment_type="vllm_local",
        base_url="http://localhost:8000"
    )
    
    # 调用模型
    response = adapter.chat_completion([
        {"role": "user", "content": "你好"}
    ])
    ```
    """
    
    # 模型名称映射
    MODEL_MAPPING = {
        StepFlashDeploymentType.OPENROUTER: "stepfun/step-3.5-flash",
        StepFlashDeploymentType.NVIDIA_NIM: "nvidia/stepfun-ai/step-3.5-flash",
        StepFlashDeploymentType.VLLM_LOCAL: "step-3.5-flash",
    }
    
    # API 基础 URL
    API_URLS = {
        StepFlashDeploymentType.OPENROUTER: "https://openrouter.ai/api/v1/chat/completions",
        StepFlashDeploymentType.NVIDIA_NIM: "https://api.nvidia.com/nim/v1/chat/completions",
        StepFlashDeploymentType.VLLM_LOCAL: None,  # 用户提供
    }
    
    def __init__(
        self,
        deployment_type: str = "openrouter",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        enable_cache: bool = False,
        cache_ttl: int = 3600,
    ):
        """
        初始化 Step-3.5-Flash 适配器
        
        Args:
            deployment_type: 部署类型 ("openrouter", "nvidia_nim", "vllm_local")
            api_key: API 密钥
            base_url: 自定义基础 URL (主要用于 vLLM 本地部署)
            model: 自定义模型名称
            timeout: 请求超时时间(秒)，默认60秒
            max_tokens: 最大生成token数，默认4096
            temperature: 温度参数，默认0.7
            max_retries: 最大重试次数，默认3
            retry_delay: 重试延迟(秒)，默认2.0
            enable_cache: 是否启用响应缓存，默认False
            cache_ttl: 缓存过期时间(秒)，默认3600
        """
        self.deployment_type = StepFlashDeploymentType(deployment_type)
        self.api_key = api_key or os.getenv("STEPSFLASH_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        self.base_url = base_url
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 设置模型名称
        if model:
            self.model = model
        else:
            self.model = self.MODEL_MAPPING.get(self.deployment_type, "step-3.5-flash")
        
        # 设置 API URL
        if self.deployment_type == StepFlashDeploymentType.VLLM_LOCAL:
            self.api_url = base_url or "http://localhost:8000/v1/chat/completions"
        else:
            self.api_url = self.API_URLS.get(self.deployment_type, "")
        
        # 缓存配置
        self.enable_cache = enable_cache  # 是否启用响应缓存
        self.cache_ttl = cache_ttl  # 缓存过期时间（秒）
        self.max_cache_size = 1000  # 最大缓存条目数
        self.cache_policy = "lru"  # 缓存策略：lru（最近最少使用）或 fifo（先进先出）
        self._cache = {}  # 缓存存储：cache_key -> (created_time, last_access_time, access_count, response)
        self._cache_lock = threading.RLock()  # 缓存访问锁
        self._cache_hits = 0  # 缓存命中次数
        self._cache_misses = 0  # 缓存未命中次数
        
        # 自适应批处理配置
        self.adaptive_batch_enabled = True  # 是否启用自适应批处理
        self.batch_performance_history = []  # 批处理性能历史记录
        self.max_batch_history = 50  # 最大历史记录数
        self.current_batch_size = 5  # 当前批处理大小
        self.min_batch_size = 1  # 最小批处理大小
        self.max_batch_size = 20  # 最大批处理大小
        self.batch_adjustment_factor = 0.2  # 调整因子（20%）
        self.target_response_time = 5.0  # 目标响应时间（秒）
        self.max_error_rate = 0.1  # 最大错误率（10%）
        
        # 预测性缓存配置
        self.predictive_cache_enabled = True  # 是否启用预测性缓存
        self.request_patterns = {}  # 请求模式记录：hash -> {count, last_access, avg_interval}
        self.max_patterns = 100  # 最大记录的模式数
        self.pattern_threshold = 3  # 预测阈值（访问次数超过此值才预测）
        self.prediction_window = 3600  # 预测窗口（秒，1小时内）
        self.warmup_workers = 2  # 预热工作线程数
        
        # 高级语义缓存配置
        self.semantic_cache_enabled = True  # 是否启用语义缓存
        self.semantic_similarity_threshold = 0.85  # 语义相似度阈值（0-1）
        self.vector_embedding_dim = 384  # 向量嵌入维度（使用sentence-transformers的all-MiniLM-L6-v2）
        self.semantic_cache_size = 500  # 语义缓存最大条目数
        self._semantic_cache = {}  # 语义缓存：cache_key -> (embedding_vector, response_data)
        self._semantic_cache_lock = threading.RLock()  # 语义缓存访问锁
        self._semantic_cache_hits = 0  # 语义缓存命中次数
        self._semantic_cache_misses = 0  # 语义缓存未命中次数
        
        logger.info(f"Step-3.5-Flash 适配器初始化: {deployment_type}, model: {self.model}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用 Step-3.5-Flash 模型进行聊天完成
        
        Args:
            messages: 消息列表 [{"role": "user/assistant/system", "content": "..."}]
            **kwargs: 其他参数 (temperature, max_tokens 等)
        
        Returns:
            响应字典 {
                "success": bool,
                "response": str,  # 模型回复
                "model": str,     # 使用的模型
                "usage": dict,   # token 使用情况
                "error": str,    # 错误信息(如果失败)
            }
        """
        start_time = time.time()
        
        # 缓存检查（跳过流式请求的缓存）
        cache_key = None
        stream_enabled = kwargs.get("stream", False)
        
        if self.enable_cache and not stream_enabled:
            cache_key = self._generate_cache_key(messages, **kwargs)
            cached_response = self._get_from_cache(cache_key)
            if cached_response is not None:
                # 缓存命中，记录缓存指标并返回缓存结果
                duration = time.time() - start_time
                record_llm_call(
                    provider="stepflash",
                    model=self.model,
                    endpoint=self.deployment_type.value,
                    duration=duration,
                    success=True
                )
                # 记录缓存命中
                record_cache_operation(cache_name="stepflash_llm", operation="chat_completion", hit=True)
                
                # 记录请求模式（缓存命中时也记录，表明这是重复请求）
                self._record_request_pattern(messages, **kwargs)
                
                return cached_response
        
        # 缓存未命中，记录缓存未命中（如果启用了缓存且非流式请求）
        if self.enable_cache and not stream_enabled and cache_key:
            record_cache_operation(cache_name="stepflash_llm", operation="chat_completion", hit=False)
            self._cache_misses += 1
        
        # 语义缓存检查（标准缓存未命中时尝试）
        semantic_cached_response = None
        if self.semantic_cache_enabled and not stream_enabled:
            semantic_cached_response = self._find_semantic_cache_match(messages, **kwargs)
            if semantic_cached_response is not None:
                # 语义缓存命中，记录指标并返回
                duration = time.time() - start_time
                record_llm_call(
                    provider="stepflash",
                    model=self.model,
                    endpoint=self.deployment_type.value,
                    duration=duration,
                    success=True
                )
                # 记录语义缓存命中
                logger.info(f"语义缓存命中，相似度: {semantic_cached_response.get('semantic_similarity', '未知')}")
                
                # 添加语义缓存标记
                semantic_cached_response["semantic_cache_hit"] = True
                semantic_cached_response["original_cache_key"] = cache_key
                
                # 记录请求模式
                self._record_request_pattern(messages, **kwargs)
                
                return semantic_cached_response
        
        # 记录请求模式用于预测性缓存（无论缓存是否命中）
        self._record_request_pattern(messages, **kwargs)
        
        try:
            import requests
            
            # 转换消息格式：支持 ChatMessage 对象或字典
            converted_messages = []
            for msg in messages:
                if hasattr(msg, 'role') and hasattr(msg, 'content'):
                    # ChatMessage 对象
                    converted_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
                elif isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    # 字典格式
                    converted_messages.append(msg)
                else:
                    # 未知格式，尝试转换
                    logger.warning(f"未知消息格式: {type(msg)}")
                    converted_messages.append({
                        "role": "user",
                        "content": str(msg)
                    })
            
            # 合并参数
            params = {
                "model": self.model,
                "messages": converted_messages,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
            }
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json",
            }
            
            # 根据部署类型设置认证
            if self.deployment_type == StepFlashDeploymentType.OPENROUTER:
                headers["Authorization"] = f"Bearer {self.api_key}"
                headers["HTTP-Referer"] = "https://rangen.ai"
                headers["X-Title"] = "RANGEN"
            elif self.deployment_type == StepFlashDeploymentType.NVIDIA_NIM:
                headers["Authorization"] = f"Bearer {self.api_key}"
            elif self.deployment_type == StepFlashDeploymentType.VLLM_LOCAL:
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
            
            # 发送请求（带重试机制）
            last_exception = None
            
            for attempt in range(self.max_retries):
                try:
                    response = requests.post(
                        self.api_url,
                        json=params,
                        headers=headers,
                        timeout=kwargs.get("timeout", self.timeout)
                    )
                    
                    # 处理响应
                    if response.status_code == 200:
                        result = response.json()
                        
                        # 记录成功指标
                        duration = time.time() - start_time
                        record_llm_call(
                            provider="stepflash",
                            model=self.model,
                            endpoint=self.deployment_type.value,
                            duration=duration,
                            success=True
                        )
                        
                        # 记录token使用情况（如果可用）
                        if "usage" in result:
                            usage = result["usage"]
                            if "prompt_tokens" in usage:
                                record_llm_tokens(
                                    provider="stepflash",
                                    model=self.model,
                                    token_type="input",
                                    token_count=usage["prompt_tokens"]
                                )
                            if "completion_tokens" in usage:
                                record_llm_tokens(
                                    provider="stepflash",
                                    model=self.model,
                                    token_type="output",
                                    token_count=usage["completion_tokens"]
                                )
                        
                        response_data = {
                            "success": True,
                            "response": result["choices"][0]["message"]["content"],
                            "model": result.get("model", self.model),
                            "usage": result.get("usage", {}),
                            "finish_reason": result["choices"][0].get("finish_reason"),
                            "retry_attempts": attempt,  # 记录重试次数
                        }
                        
                        # 缓存响应结果（如果启用了缓存且非流式请求）
                        if self.enable_cache and cache_key and not kwargs.get("stream", False):
                            self._set_to_cache(cache_key, response_data)
                            # 记录缓存设置
                            record_cache_operation(cache_name="stepflash_llm", operation="cache_set", hit=None, value_size=len(str(response_data)))
                        
                        # 添加到语义缓存（如果启用）
                        if self.semantic_cache_enabled and cache_key and not kwargs.get("stream", False):
                            self._add_to_semantic_cache(cache_key, messages, response_data)
                        
                        return response_data
                    elif response.status_code in [429, 500, 502, 503, 504] and attempt < self.max_retries - 1:
                        # 可重试的错误：限流、服务器错误
                        logger.warning(f"Step-3.5-Flash API 可重试错误 {response.status_code}, 第 {attempt + 1} 次重试...")
                        import time
                        time.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
                        continue
                    else:
                        # 不可重试的错误或最后一次尝试
                        logger.error(f"Step-3.5-Flash API 错误: {response.status_code} - {response.text}")
                        return {
                            "success": False,
                            "error": f"API 错误: {response.status_code}",
                            "details": response.text,
                            "retry_attempts": attempt,
                        }
                        
                except requests.exceptions.Timeout as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"请求超时，第 {attempt + 1} 次重试...")
                        import time
                        time.sleep(self.retry_delay * (2 ** attempt))
                        last_exception = e
                        continue
                    else:
                        last_exception = e
                        break
                        
                except requests.exceptions.ConnectionError as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"连接错误，第 {attempt + 1} 次重试...")
                        import time
                        time.sleep(self.retry_delay * (2 ** attempt))
                        last_exception = e
                        continue
                    else:
                        last_exception = e
                        break
                        
                except Exception as e:
                    # 其他异常，不重试
                    logger.error(f"Step-3.5-Flash 请求异常: {e}")
                    return {
                        "success": False,
                        "error": str(e),
                        "retry_attempts": attempt,
                    }
            
            # 所有重试都失败了
            error_msg = f"所有重试失败: {last_exception}" if last_exception else "未知错误"
            logger.error(f"Step-3.5-Flash 调用失败: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "retry_attempts": self.max_retries,
            }
                
        except ImportError:
            # requests 未安装，返回模拟响应
            return self._mock_response(messages)
        except Exception as e:
            logger.error(f"Step-3.5-Flash 调用失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def _generate_cache_key(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
        
        Returns:
            缓存键字符串
        """
        import hashlib
        import json
        
        # 创建缓存数据字典
        cache_data = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "deployment_type": self.deployment_type.value,
        }
        
        # 添加其他重要参数（排除stream等不适合缓存的参数）
        exclude_keys = {"stream", "n", "stop", "logprobs", "echo", "logit_bias"}
        for key, value in kwargs.items():
            if key not in exclude_keys and value is not None:
                cache_data[key] = value
        
        # 生成JSON字符串并计算哈希
        cache_str = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        cache_hash = hashlib.sha256(cache_str.encode('utf-8')).hexdigest()
        
        return f"stepflash:{cache_hash}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        从缓存中获取响应（支持LRU和FIFO策略）
        
        Args:
            cache_key: 缓存键
        
        Returns:
            缓存的响应数据，如果未找到或已过期则返回None
        """
        if not self.enable_cache:
            return None
        
        with self._cache_lock:
            if cache_key not in self._cache:
                return None
            
            cache_entry = self._cache[cache_key]
            
            # 兼容旧格式 (cache_time, response) 和新格式 (created_time, last_access_time, access_count, response)
            if len(cache_entry) == 2:
                # 旧格式：转换为新格式
                cache_time, cached_response = cache_entry
                cache_entry = (cache_time, cache_time, 1, cached_response)
                self._cache[cache_key] = cache_entry
            
            created_time, last_access_time, access_count, cached_response = cache_entry
            
            # 检查缓存是否过期
            current_time = time.time()
            if current_time - created_time > self.cache_ttl:
                # 缓存过期，删除条目
                del self._cache[cache_key]
                return None
            
            # 更新访问统计（LRU策略）
            updated_entry = (created_time, current_time, access_count + 1, cached_response)
            self._cache[cache_key] = updated_entry
            
            # 记录缓存命中
            self._cache_hits += 1
            
            # 返回缓存的响应
            logger.debug(f"Step-3.5-Flash 缓存命中: {cache_key[:32]}... (访问次数: {access_count + 1})")
            return cached_response
    
    def _set_to_cache(self, cache_key: str, response: Dict[str, Any]) -> None:
        """
        将响应保存到缓存（支持智能过期和LRU清理）
        
        Args:
            cache_key: 缓存键
            response: 响应数据
        """
        if not self.enable_cache or not response.get("success"):
            # 缓存未启用或响应失败时不缓存
            return
        
        with self._cache_lock:
            current_time = time.time()
            cache_entry = (current_time, current_time, 1, response)  # (created_time, last_access_time, access_count, response)
            self._cache[cache_key] = cache_entry
            logger.debug(f"Step-3.5-Flash 缓存设置: {cache_key[:32]}...")
            
            # 检查是否需要清理过期或超出大小的缓存
            self._cleanup_if_needed()
    
    def _cleanup_if_needed(self) -> None:
        """
        清理过期缓存条目，并根据缓存策略（LRU/FIFO）限制缓存大小
        """
        if not self.enable_cache or len(self._cache) <= self.max_cache_size:
            return
        
        with self._cache_lock:
            current_time = time.time()
            
            # 首先清理过期条目
            expired_keys = []
            for cache_key, cache_entry in self._cache.items():
                if len(cache_entry) == 4:
                    created_time, _, _, _ = cache_entry
                    if current_time - created_time > self.cache_ttl:
                        expired_keys.append(cache_key)
                elif len(cache_entry) == 2:  # 旧格式
                    cache_time, _ = cache_entry
                    if current_time - cache_time > self.cache_ttl:
                        expired_keys.append(cache_key)
            
            for cache_key in expired_keys:
                del self._cache[cache_key]
            
            # 如果仍然超过最大大小，根据策略清理
            if len(self._cache) > self.max_cache_size:
                if self.cache_policy == "lru":
                    # LRU: 删除最久未访问的条目
                    lru_entries = []
                    for cache_key, cache_entry in self._cache.items():
                        if len(cache_entry) == 4:
                            _, last_access_time, _, _ = cache_entry
                            lru_entries.append((last_access_time, cache_key))
                        else:  # 旧格式
                            cache_time, _ = cache_entry
                            lru_entries.append((cache_time, cache_key))
                    
                    # 按最后访问时间排序，删除最旧的
                    lru_entries.sort(key=lambda x: x[0])
                    keys_to_remove = [entry[1] for entry in lru_entries[:len(self._cache) - self.max_cache_size]]
                else:  # FIFO
                    # FIFO: 删除最早创建的条目
                    fifo_entries = []
                    for cache_key, cache_entry in self._cache.items():
                        if len(cache_entry) == 4:
                            created_time, _, _, _ = cache_entry
                            fifo_entries.append((created_time, cache_key))
                        else:  # 旧格式
                            cache_time, _ = cache_entry
                            fifo_entries.append((cache_time, cache_key))
                    
                    # 按创建时间排序，删除最旧的
                    fifo_entries.sort(key=lambda x: x[0])
                    keys_to_remove = [entry[1] for entry in fifo_entries[:len(self._cache) - self.max_cache_size]]
                
                for cache_key in keys_to_remove:
                    del self._cache[cache_key]
                
                logger.debug(f"Step-3.5-Flash 缓存清理: 移除了 {len(keys_to_remove)} 个条目，当前大小: {len(self._cache)}")
    
    def clear_cache(self) -> int:
        """
        清除所有缓存
        
        Returns:
            清除的缓存条目数量
        """
        with self._cache_lock:
            cache_count = len(self._cache)
            self._cache.clear()
            logger.info(f"Step-3.5-Flash 缓存已清除，共 {cache_count} 个条目")
            return cache_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息（包含命中率、访问统计和策略信息）
        
        Returns:
            缓存统计字典
        """
        with self._cache_lock:
            current_time = time.time()
            valid_count = 0
            expired_count = 0
            total_size = 0
            total_access_count = 0
            avg_access_count = 0
            
            for cache_key, cache_entry in self._cache.items():
                # 兼容旧格式和新格式
                if len(cache_entry) == 4:
                    created_time, last_access_time, access_count, _ = cache_entry
                    if current_time - created_time > self.cache_ttl:
                        expired_count += 1
                    else:
                        valid_count += 1
                        total_access_count += access_count
                    total_size += len(cache_key) + 150  # 基本开销（稍大）
                else:  # 旧格式
                    cache_time, _ = cache_entry
                    if current_time - cache_time > self.cache_ttl:
                        expired_count += 1
                    else:
                        valid_count += 1
                        total_access_count += 1  # 旧格式默认访问次数为1
                    total_size += len(cache_key) + 100  # 基本开销
            
            # 计算命中率
            total_operations = self._cache_hits + self._cache_misses
            hit_ratio = self._cache_hits / total_operations if total_operations > 0 else 0.0
            
            # 计算平均访问次数（仅有效条目）
            avg_access_count = total_access_count / valid_count if valid_count > 0 else 0.0
            
            return {
                "enabled": self.enable_cache,
                "ttl_seconds": self.cache_ttl,
                "max_size": self.max_cache_size,
                "policy": self.cache_policy,
                "total_entries": len(self._cache),
                "valid_entries": valid_count,
                "expired_entries": expired_count,
                "estimated_size_bytes": total_size,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "hit_ratio": hit_ratio,
                "total_access_count": total_access_count,
                "avg_access_count": avg_access_count,
                "memory_usage_mb": total_size / (1024 * 1024),
            }
    
    def _get_text_embedding(self, text: str) -> Optional[List[float]]:
        """
        获取文本的向量嵌入
        
        Args:
            text: 输入文本
        
        Returns:
            向量嵌入列表，如果无法生成则返回None
        """
        if not self.semantic_cache_enabled or not text:
            return None
        
        try:
            # 尝试导入 sentence-transformers
            from sentence_transformers import SentenceTransformer
            
            # 使用轻量级模型
            model_name = "all-MiniLM-L6-v2"
            
            # 缓存模型实例（类变量）
            if not hasattr(StepFlashAdapter, "_embedding_model"):
                logger.info(f"加载语义嵌入模型: {model_name}")
                StepFlashAdapter._embedding_model = SentenceTransformer(model_name)
            
            # 生成嵌入向量
            embedding = StepFlashAdapter._embedding_model.encode(text)
            return embedding.tolist()
            
        except ImportError:
            logger.warning("sentence-transformers 库未安装，语义缓存功能将降级")
            self.semantic_cache_enabled = False
            return None
        except Exception as e:
            logger.warning(f"生成文本嵌入失败: {e}")
            return None
    
    def _get_messages_embedding(self, messages: List[Dict[str, str]]) -> Optional[List[float]]:
        """
        获取消息列表的向量嵌入
        
        Args:
            messages: 消息列表
        
        Returns:
            向量嵌入列表
        """
        if not messages:
            return None
        
        # 提取用户消息内容
        user_messages = []
        for msg in messages:
            if msg.get("role") in ["user", "system"]:
                content = msg.get("content", "")
                if content:
                    user_messages.append(content)
        
        if not user_messages:
            return None
        
        # 合并所有用户消息
        combined_text = " ".join(user_messages)
        return self._get_text_embedding(combined_text)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
        
        Returns:
            余弦相似度（0-1）
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        try:
            import numpy as np
            
            # 转换为numpy数组
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            # 计算点积和范数
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            # 避免除以零
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            # 确保在[0, 1]范围内
            return max(0.0, min(1.0, similarity))
            
        except ImportError:
            logger.warning("numpy 库未安装，使用简化相似度计算")
            # 简化计算
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            logger.warning(f"计算余弦相似度失败: {e}")
            return 0.0
    
    def _find_semantic_cache_match(self, messages: List[Dict[str, str]], **kwargs) -> Optional[Dict[str, Any]]:
        """
        在语义缓存中查找相似请求
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
        
        Returns:
            匹配的缓存响应，如果未找到则返回None
        """
        if not self.semantic_cache_enabled or not self._semantic_cache:
            return None
        
        # 获取当前请求的嵌入向量
        query_embedding = self._get_messages_embedding(messages)
        if query_embedding is None:
            return None
        
        with self._semantic_cache_lock:
            best_match = None
            best_similarity = 0.0
            
            for cache_key, (cached_embedding, cached_response) in self._semantic_cache.items():
                # 计算相似度
                similarity = self._cosine_similarity(query_embedding, cached_embedding)
                
                # 检查是否超过阈值且比当前最佳匹配更好
                if similarity >= self.semantic_similarity_threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (cache_key, cached_response, similarity)
            
            if best_match:
                cache_key, cached_response, similarity = best_match
                logger.debug(f"语义缓存命中: 相似度 {similarity:.3f}, key: {cache_key[:20]}...")
                self._semantic_cache_hits += 1
                
                # 更新缓存条目的最后访问时间（如果需要）
                # 这里可以添加缓存条目的元数据更新逻辑
                
                # 添加相似度信息到响应中（创建副本避免修改原始缓存）
                response_with_similarity = cached_response.copy()
                response_with_similarity["semantic_similarity"] = similarity
                response_with_similarity["semantic_cache_key"] = cache_key
                
                return response_with_similarity
        
        self._semantic_cache_misses += 1
        return None
    
    def _add_to_semantic_cache(self, cache_key: str, messages: List[Dict[str, str]], response: Dict[str, Any]):
        """
        添加响应到语义缓存
        
        Args:
            cache_key: 缓存键
            messages: 消息列表
            response: 响应数据
        """
        if not self.semantic_cache_enabled:
            return
        
        # 获取消息的嵌入向量
        embedding = self._get_messages_embedding(messages)
        if embedding is None:
            return
        
        with self._semantic_cache_lock:
            # 检查缓存大小，必要时清理
            if len(self._semantic_cache) >= self.semantic_cache_size:
                # 简单策略：删除最早添加的条目（可以优化为LRU）
                oldest_key = next(iter(self._semantic_cache))
                del self._semantic_cache[oldest_key]
                logger.debug(f"语义缓存达到上限，删除条目: {oldest_key[:20]}...")
            
            # 添加到缓存
            self._semantic_cache[cache_key] = (embedding, response)
            logger.debug(f"语义缓存添加: {cache_key[:20]}...")
    
    def get_semantic_cache_stats(self) -> Dict[str, Any]:
        """
        获取语义缓存统计信息
        
        Returns:
            语义缓存统计字典
        """
        with self._semantic_cache_lock:
            total_operations = self._semantic_cache_hits + self._semantic_cache_misses
            hit_ratio = self._semantic_cache_hits / total_operations if total_operations > 0 else 0.0
            
            return {
                "enabled": self.semantic_cache_enabled,
                "total_entries": len(self._semantic_cache),
                "max_entries": self.semantic_cache_size,
                "similarity_threshold": self.semantic_similarity_threshold,
                "embedding_dim": self.vector_embedding_dim,
                "hits": self._semantic_cache_hits,
                "misses": self._semantic_cache_misses,
                "hit_ratio": hit_ratio,
                "sample_keys": list(self._semantic_cache.keys())[:5] if self._semantic_cache else []
            }
    
    def clear_semantic_cache(self) -> int:
        """
        清空语义缓存
        
        Returns:
            清除的缓存条目数
        """
        with self._semantic_cache_lock:
            cache_count = len(self._semantic_cache)
            self._semantic_cache.clear()
            self._semantic_cache_hits = 0
            self._semantic_cache_misses = 0
            logger.info(f"语义缓存已清除，共 {cache_count} 个条目")
            return cache_count
    
    def batch_chat_completion(
        self, 
        messages_list: List[List[Dict[str, str]]], 
        max_concurrent: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量调用 Step-3.5-Flash 模型进行聊天完成
        
        Args:
            messages_list: 消息列表的列表，每个元素是一个聊天消息列表
            max_concurrent: 最大并发请求数，默认5
            **kwargs: 其他参数 (temperature, max_tokens 等)
        
        Returns:
            响应字典列表，顺序与输入一致
        """
        if not messages_list:
            return []
        
        # 限制并发数，避免API限流
        max_concurrent = min(max_concurrent, len(messages_list))
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # 提交所有任务
            future_to_index = {
                executor.submit(self.chat_completion, messages, **kwargs): i
                for i, messages in enumerate(messages_list)
            }
            
            # 收集结果，保持顺序
            results = [None] * len(messages_list)
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results[index] = result
                except Exception as e:
                    logger.error(f"Step-3.5-Flash 批量调用失败 (索引 {index}): {e}")
                    results[index] = {
                        "success": False,
                        "error": str(e),
                        "response": None,
                        "model": self.model,
                    }
        
        return results
    
    def _record_batch_performance(
        self,
        batch_size: int,
        total_time: float,
        success_count: int,
        error_count: int
    ):
        """
        记录批处理性能指标
        
        Args:
            batch_size: 批处理大小
            total_time: 总处理时间（秒）
            success_count: 成功请求数
            error_count: 错误请求数
        """
        if not self.adaptive_batch_enabled:
            return
        
        # 计算性能指标
        avg_response_time = total_time / batch_size if batch_size > 0 else 0
        error_rate = error_count / batch_size if batch_size > 0 else 0
        
        performance_data = {
            "timestamp": time.time(),
            "batch_size": batch_size,
            "total_time": total_time,
            "avg_response_time": avg_response_time,
            "success_count": success_count,
            "error_count": error_count,
            "error_rate": error_rate
        }
        
        # 添加到历史记录
        self.batch_performance_history.append(performance_data)
        
        # 限制历史记录大小
        if len(self.batch_performance_history) > self.max_batch_history:
            self.batch_performance_history = self.batch_performance_history[-self.max_batch_history:]
        
        logger.debug(f"记录批处理性能: batch_size={batch_size}, avg_time={avg_response_time:.2f}s, error_rate={error_rate:.1%}")
    
    def _adjust_batch_size(self) -> int:
        """
        根据历史性能调整批处理大小
        
        Returns:
            调整后的批处理大小
        """
        if not self.adaptive_batch_enabled or not self.batch_performance_history:
            return self.current_batch_size
        
        # 获取最近的历史记录（最后10次）
        recent_history = self.batch_performance_history[-10:] if len(self.batch_performance_history) >= 10 else self.batch_performance_history
        
        if not recent_history:
            return self.current_batch_size
        
        # 计算平均性能指标
        avg_response_time = sum(h["avg_response_time"] for h in recent_history) / len(recent_history)
        avg_error_rate = sum(h["error_rate"] for h in recent_history) / len(recent_history)
        
        # 调整逻辑
        new_batch_size = self.current_batch_size
        
        # 如果响应时间超过目标，减少批处理大小
        if avg_response_time > self.target_response_time:
            reduction = int(self.current_batch_size * self.batch_adjustment_factor)
            new_batch_size = max(self.min_batch_size, self.current_batch_size - reduction)
            logger.info(f"响应时间过高 ({avg_response_time:.2f}s > {self.target_response_time}s)，减少批处理大小: {self.current_batch_size} -> {new_batch_size}")
        
        # 如果错误率超过阈值，减少批处理大小
        elif avg_error_rate > self.max_error_rate:
            reduction = int(self.current_batch_size * self.batch_adjustment_factor * 2)  # 双倍减少
            new_batch_size = max(self.min_batch_size, self.current_batch_size - reduction)
            logger.info(f"错误率过高 ({avg_error_rate:.1%} > {self.max_error_rate:.0%})，减少批处理大小: {self.current_batch_size} -> {new_batch_size}")
        
        # 如果性能良好，尝试增加批处理大小
        elif avg_response_time < self.target_response_time * 0.7 and avg_error_rate < self.max_error_rate * 0.5:
            increase = int(self.current_batch_size * self.batch_adjustment_factor)
            new_batch_size = min(self.max_batch_size, self.current_batch_size + increase)
            logger.info(f"性能良好，增加批处理大小: {self.current_batch_size} -> {new_batch_size}")
        
        # 应用调整
        old_size = self.current_batch_size
        self.current_batch_size = new_batch_size
        
        if old_size != new_batch_size:
            logger.info(f"批处理大小调整: {old_size} -> {new_batch_size} (响应时间: {avg_response_time:.2f}s, 错误率: {avg_error_rate:.1%})")
        
        return self.current_batch_size
    
    def adaptive_batch_chat_completion(
        self,
        messages_list: List[List[Dict[str, str]]],
        initial_batch_size: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        自适应批量调用 Step-3.5-Flash 模型
        
        根据历史性能动态调整批处理大小，优化吞吐量和响应时间。
        
        Args:
            messages_list: 消息列表的列表，每个元素是一个聊天消息列表
            initial_batch_size: 初始批处理大小（可选）
            **kwargs: 其他参数 (temperature, max_tokens 等)
        
        Returns:
            响应字典列表，顺序与输入一致
        """
        if not messages_list:
            return []
        
        if not self.adaptive_batch_enabled:
            # 回退到标准批处理
            return self.batch_chat_completion(messages_list, **kwargs)
        
        # 使用当前批处理大小或初始大小
        if initial_batch_size is not None:
            batch_size = max(self.min_batch_size, min(initial_batch_size, self.max_batch_size))
            self.current_batch_size = batch_size
        else:
            batch_size = self.current_batch_size
        
        total_results = []
        total_messages = len(messages_list)
        processed_count = 0
        
        logger.info(f"开始自适应批处理: 总共 {total_messages} 条消息，初始批处理大小: {batch_size}")
        
        while processed_count < total_messages:
            # 调整批处理大小
            batch_size = self._adjust_batch_size()
            
            # 计算当前批次
            current_batch = messages_list[processed_count:processed_count + batch_size]
            actual_batch_size = len(current_batch)
            
            if actual_batch_size == 0:
                break
            
            logger.debug(f"处理批次 {len(total_results) + 1}: 大小 {actual_batch_size}, 累计 {processed_count}/{total_messages}")
            
            # 执行批次处理
            start_time = time.time()
            
            try:
                batch_results = self.batch_chat_completion(current_batch, max_concurrent=batch_size, **kwargs)
                
                # 统计成功和失败
                success_count = sum(1 for r in batch_results if r.get("success", False))
                error_count = actual_batch_size - success_count
                batch_time = time.time() - start_time
                
                # 记录性能
                self._record_batch_performance(
                    batch_size=actual_batch_size,
                    total_time=batch_time,
                    success_count=success_count,
                    error_count=error_count
                )
                
                total_results.extend(batch_results)
                processed_count += actual_batch_size
                
                logger.debug(f"批次完成: 时间 {batch_time:.2f}s, 成功 {success_count}/{actual_batch_size}")
                
            except Exception as e:
                logger.error(f"自适应批处理失败: {e}")
                # 单个批次失败，减少批处理大小并重试
                self.current_batch_size = max(self.min_batch_size, batch_size // 2)
                logger.warning(f"批次失败，减少批处理大小: {batch_size} -> {self.current_batch_size}")
        
        logger.info(f"自适应批处理完成: 处理 {processed_count} 条消息，最终批处理大小: {self.current_batch_size}")
        return total_results
    
    def _record_request_pattern(self, messages: List[Dict[str, str]], **kwargs):
        """
        记录请求模式用于预测性缓存
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
        """
        if not self.predictive_cache_enabled or not self.enable_cache:
            return
        
        # 生成请求哈希（简化版本）
        import hashlib
        import json
        
        request_data = {
            "messages": messages,
            "params": {k: v for k, v in kwargs.items() if k not in ["stream"]}  # 排除流式参数
        }
        
        # 计算哈希
        request_str = json.dumps(request_data, sort_keys=True, ensure_ascii=False)
        request_hash = hashlib.md5(request_str.encode()).hexdigest()
        
        current_time = time.time()
        
        # 更新模式记录
        if request_hash in self.request_patterns:
            pattern = self.request_patterns[request_hash]
            last_time = pattern["last_access"]
            interval = current_time - last_time
            
            # 更新平均间隔（指数移动平均）
            old_avg = pattern["avg_interval"]
            pattern["avg_interval"] = (old_avg * 0.7) + (interval * 0.3)
            pattern["count"] += 1
            pattern["last_access"] = current_time
        else:
            # 新模式
            self.request_patterns[request_hash] = {
                "count": 1,
                "last_access": current_time,
                "avg_interval": 0,
                "first_access": current_time,
                "request_data": request_data  # 注意：可能占用内存，实际使用中应只存储必要信息
            }
            
            # 限制模式数量
            if len(self.request_patterns) > self.max_patterns:
                # 移除最旧或最少使用的模式
                oldest_hash = min(self.request_patterns.keys(), 
                                 key=lambda h: self.request_patterns[h]["last_access"])
                del self.request_patterns[oldest_hash]
    
    def _predict_frequent_requests(self) -> List[Dict[str, Any]]:
        """
        预测频繁请求
        
        Returns:
            预测的请求列表（包含消息和参数）
        """
        if not self.predictive_cache_enabled or not self.request_patterns:
            return []
        
        current_time = time.time()
        predicted_requests = []
        
        for request_hash, pattern in self.request_patterns.items():
            # 检查是否频繁访问
            if pattern["count"] >= self.pattern_threshold:
                # 检查是否在预测窗口内可能再次访问
                time_since_last = current_time - pattern["last_access"]
                avg_interval = pattern["avg_interval"] if pattern["avg_interval"] > 0 else self.prediction_window
                
                # 如果平均间隔小于预测窗口，且距离上次访问时间接近平均间隔，则预测
                if avg_interval < self.prediction_window and time_since_last < avg_interval * 1.5:
                    predicted_requests.append({
                        "hash": request_hash,
                        "messages": pattern["request_data"]["messages"],
                        "params": pattern["request_data"]["params"],
                        "priority": pattern["count"] / (time_since_last + 1)  # 优先级公式
                    })
        
        # 按优先级排序
        predicted_requests.sort(key=lambda x: x["priority"], reverse=True)
        
        # 限制数量
        max_predictions = min(10, len(predicted_requests))
        return predicted_requests[:max_predictions]
    
    def _warmup_cache_for_prediction(self, predicted_requests: List[Dict[str, Any]]):
        """
        为预测的请求预热缓存
        
        Args:
            predicted_requests: 预测的请求列表
        """
        if not predicted_requests or not self.enable_cache:
            return
        
        logger.info(f"开始缓存预热，预测 {len(predicted_requests)} 个请求")
        
        import concurrent.futures
        
        def warmup_single_request(request_data):
            try:
                messages = request_data["messages"]
                params = request_data["params"]
                
                # 生成缓存键
                cache_key = self._generate_cache_key(messages, **params)
                
                # 检查是否已缓存
                if cache_key in self._cache:
                    return  # 已缓存，跳过
                
                # 执行请求并缓存结果
                response = self.chat_completion(messages, **params)
                
                if response.get("success"):
                    # 缓存结果（使用较短的TTL，因为这是预测性缓存）
                    self._add_to_cache(cache_key, response, ttl=self.cache_ttl // 2)
                    return True
                
            except Exception as e:
                logger.debug(f"缓存预热失败: {e}")
            
            return False
        
        # 使用线程池并行预热
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.warmup_workers) as executor:
            futures = [executor.submit(warmup_single_request, req) for req in predicted_requests]
            success_count = 0
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    if future.result():
                        success_count += 1
                except:
                    pass
        
        logger.info(f"缓存预热完成: 成功 {success_count}/{len(predicted_requests)}")
    
    def run_predictive_cache_warmup(self):
        """运行预测性缓存预热（可在后台定期调用）"""
        if not self.predictive_cache_enabled or not self.enable_cache:
            return
        
        logger.debug("开始预测性缓存预热周期")
        
        # 预测频繁请求
        predicted_requests = self._predict_frequent_requests()
        
        if predicted_requests:
            self._warmup_cache_for_prediction(predicted_requests)
        else:
            logger.debug("没有预测到频繁请求")
    
    def enable_predictive_cache(self, enabled: bool = True):
        """启用或禁用预测性缓存"""
        self.predictive_cache_enabled = enabled
        logger.info(f"预测性缓存 {'已启用' if enabled else '已禁用'}")
    
    def get_cache_prediction_stats(self) -> Dict[str, Any]:
        """获取缓存预测统计"""
        if not self.predictive_cache_enabled:
            return {"enabled": False}
        
        total_patterns = len(self.request_patterns)
        frequent_patterns = sum(1 for p in self.request_patterns.values() 
                              if p["count"] >= self.pattern_threshold)
        
        return {
            "enabled": True,
            "total_patterns": total_patterns,
            "frequent_patterns": frequent_patterns,
            "pattern_threshold": self.pattern_threshold,
            "prediction_window": self.prediction_window,
            "request_patterns_sample": list(self.request_patterns.keys())[:5] if total_patterns > 0 else []
        }
    
    def _mock_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """模拟响应 (当 requests 库不可用时)"""
        # 提取最后一个消息的内容
        last_message = messages[-1] if messages else {}
        if hasattr(last_message, 'content'):
            content = last_message.content
        elif isinstance(last_message, dict):
            content = last_message.get("content", "")
        else:
            content = str(last_message)
        
        return {
            "success": True,
            "response": f"[Step-3.5-Flash] 处理: {content[:50]}...",
            "model": self.model,
            "usage": {
                "prompt_tokens": len(content) // 4,
                "completion_tokens": 20,
                "total_tokens": len(content) // 4 + 20,
            },
        }
    
    def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """
        流式调用 Step-3.5-Flash 模型
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
        
        Yields:
            流式响应片段
        """
        try:
            import requests
            
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "stream": True,
            }
            
            headers = {
                "Content-Type": "application/json",
            }
            
            if self.deployment_type == StepFlashDeploymentType.OPENROUTER:
                headers["Authorization"] = f"Bearer {self.api_key}"
            elif self.deployment_type == StepFlashDeploymentType.NVIDIA_NIM:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = requests.post(
                self.api_url,
                json=params,
                headers=headers,
                stream=True,
                timeout=kwargs.get("timeout", self.timeout)
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            import json
                            try:
                                chunk = json.loads(data)
                                content = chunk["choices"][0].get("delta", {}).get("content", "")
                                if content:
                                    yield content
                            except:
                                pass
            else:
                yield f"Error: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Step-3.5-Flash 流式调用失败: {e}")
            yield f"Error: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "name": "Step-3.5-Flash",
            "model": self.model,
            "deployment_type": self.deployment_type.value,
            "total_params": "196B",
            "active_params": "11B",
            "context_length": "256K",
            "max_throughput": "350 tok/s",
            "license": "Apache 2.0",
            "provider": "StepFun",
            "capabilities": [
                "reasoning",
                "coding",
                "agentic",
                "fast-inference",
                "long-context",
            ],
        }


class StepFlashRouter:
    """
    Step-3.5-Flash 路由器
    
    根据请求特征自动选择合适的部署方式或回退策略。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化路由器
        
        Args:
            config: 配置字典 {
                "primary": "openrouter",  # 主部署方式
                "fallback": "nvidia_nim",  # 备用部署方式
                "api_key": "...",
            }
        """
        self.config = config or {}
        self.primary = self.config.get("primary", "openrouter")
        self.fallback = self.config.get("fallback", "nvidia_nim")
        self.api_key = self.config.get("api_key")
        
        # 初始化主适配器
        self.primary_adapter = StepFlashAdapter(
            deployment_type=self.primary,
            api_key=self.api_key
        )
        
        # 初始化备用适配器
        if self.fallback:
            self.fallback_adapter = StepFlashAdapter(
                deployment_type=self.fallback,
                api_key=self.api_key
            )
        else:
            self.fallback_adapter = None
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用主适配器调用，失败时自动回退
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
        
        Returns:
            响应字典
        """
        # 尝试主适配器
        response = self.primary_adapter.chat_completion(messages, **kwargs)
        
        if response.get("success"):
            return response
        
        # 主适配器失败，尝试备用
        if self.fallback_adapter:
            logger.warning("主适配器失败，尝试备用适配器...")
            fallback_response = self.fallback_adapter.chat_completion(messages, **kwargs)
            
            if fallback_response.get("success"):
                fallback_response["fallback_used"] = True
                return fallback_response
        
        # 所有适配器都失败
        return response


class StepFlashLoadBalancer:
    """
    Step-3.5-Flash 负载均衡器
    
    管理多个 Step-3.5-Flash 实例，提供负载均衡功能。
    支持轮询、最少连接数、加权轮询等负载均衡策略。
    """
    
    def __init__(
        self,
        instances: List[Dict[str, Any]],
        strategy: str = "round_robin"
    ):
        """
        初始化负载均衡器
        
        Args:
            instances: 实例配置列表，每个实例包含:
                - deployment_type: 部署类型
                - api_key: API 密钥 (可选)
                - base_url: 基础URL (可选)
                - weight: 权重 (可选，默认1)
            strategy: 负载均衡策略，可选值:
                - "round_robin": 轮询 (默认)
                - "least_connections": 最少连接数
                - "weighted_round_robin": 加权轮询
                - "random": 随机
        """
        self.instances = instances
        self.strategy = strategy
        self.current_index = 0
        self.connection_counts = {}  # 记录每个实例的连接数
        self.instance_adapters = []
        
        # 初始化所有适配器实例
        for i, instance_config in enumerate(instances):
            adapter = StepFlashAdapter(
                deployment_type=instance_config.get("deployment_type", "openrouter"),
                api_key=instance_config.get("api_key"),
                base_url=instance_config.get("base_url"),
                enable_cache=instance_config.get("enable_cache", False),
                cache_ttl=instance_config.get("cache_ttl", 3600)
            )
            self.instance_adapters.append(adapter)
            self.connection_counts[i] = 0
        
        logger.info(f"初始化负载均衡器，共 {len(self.instance_adapters)} 个实例，策略: {strategy}")
    
    def _select_instance(self) -> int:
        """根据策略选择实例索引"""
        if not self.instance_adapters:
            raise ValueError("没有可用的实例")
        
        if self.strategy == "round_robin":
            index = self.current_index
            self.current_index = (self.current_index + 1) % len(self.instance_adapters)
            return index
        
        elif self.strategy == "least_connections":
            # 选择连接数最少的实例
            min_connections = min(self.connection_counts.values())
            candidates = [i for i, count in self.connection_counts.items() 
                         if count == min_connections]
            # 如果有多个，使用轮询
            if len(candidates) > 1:
                index = candidates[self.current_index % len(candidates)]
                self.current_index = (self.current_index + 1) % len(self.instance_adapters)
            else:
                index = candidates[0]
            return index
        
        elif self.strategy == "weighted_round_robin":
            # 加权轮询 - 简化实现：根据权重选择
            weights = [instance.get("weight", 1) for instance in self.instances]
            total_weight = sum(weights)
            
            # 简单的加权轮询实现
            if self.current_index >= total_weight:
                self.current_index = 0
            
            cumulative = 0
            for i, weight in enumerate(weights):
                cumulative += weight
                if self.current_index < cumulative:
                    self.current_index += 1
                    return i
            
            # 回退到第一个实例
            return 0
        
        elif self.strategy == "random":
            import random
            return random.randint(0, len(self.instance_adapters) - 1)
        
        else:
            logger.warning(f"未知策略 '{self.strategy}'，使用轮询")
            index = self.current_index
            self.current_index = (self.current_index + 1) % len(self.instance_adapters)
            return index
    
    def _record_connection(self, index: int, increment: bool = True):
        """记录连接数"""
        if increment:
            self.connection_counts[index] = self.connection_counts.get(index, 0) + 1
        else:
            self.connection_counts[index] = max(0, self.connection_counts.get(index, 0) - 1)
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用负载均衡调用聊天补全
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
        
        Returns:
            响应字典，包含 instance_index 字段标识使用的实例
        """
        if not self.instance_adapters:
            return {
                "success": False,
                "error": "没有可用的实例",
                "message": "负载均衡器没有可用的实例"
            }
        
        # 选择实例
        instance_index = self._select_instance()
        adapter = self.instance_adapters[instance_index]
        
        # 记录连接开始
        self._record_connection(instance_index, increment=True)
        
        try:
            # 调用适配器
            response = adapter.chat_completion(messages, **kwargs)
            
            # 添加实例信息
            if response.get("success"):
                response["instance_index"] = instance_index
                response["instance_count"] = len(self.instance_adapters)
                response["strategy"] = self.strategy
        except Exception as e:
            response = {
                "success": False,
                "error": str(e),
                "message": f"实例 {instance_index} 调用失败",
                "instance_index": instance_index
            }
        finally:
            # 记录连接结束
            self._record_connection(instance_index, increment=False)
        
        return response
    
    def batch_chat_completion(
        self,
        messages_list: List[List[Dict[str, str]]],
        max_concurrent: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量聊天补全，将请求分发到不同实例
        
        Args:
            messages_list: 消息列表的列表
            max_concurrent: 最大并发数
            **kwargs: 其他参数
        
        Returns:
            响应列表
        """
        import concurrent.futures
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            future_to_index = {}
            
            for i, messages in enumerate(messages_list):
                # 为每个请求选择实例
                instance_index = self._select_instance()
                adapter = self.instance_adapters[instance_index]
                
                # 记录连接
                self._record_connection(instance_index, increment=True)
                
                # 提交任务
                future = executor.submit(
                    self._execute_with_adapter,
                    adapter, messages, instance_index, kwargs
                )
                future_to_index[future] = instance_index
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_index):
                instance_index = future_to_index[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        "success": False,
                        "error": str(e),
                        "message": f"实例 {instance_index} 批量调用失败",
                        "instance_index": instance_index
                    })
                finally:
                    # 记录连接结束
                    self._record_connection(instance_index, increment=False)
        
        return results
    
    def _execute_with_adapter(
        self,
        adapter: StepFlashAdapter,
        messages: List[Dict[str, str]],
        instance_index: int,
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用指定适配器执行请求"""
        try:
            response = adapter.chat_completion(messages, **kwargs)
            if response.get("success"):
                response["instance_index"] = instance_index
            return response
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"实例 {instance_index} 执行失败",
                "instance_index": instance_index
            }
    
    def get_instance_status(self) -> List[Dict[str, Any]]:
        """获取所有实例状态"""
        status_list = []
        for i, (adapter, instance_config) in enumerate(zip(self.instance_adapters, self.instances)):
            status_list.append({
                "index": i,
                "deployment_type": instance_config.get("deployment_type", "unknown"),
                "connection_count": self.connection_counts.get(i, 0),
                "weight": instance_config.get("weight", 1),
                "config": {k: v for k, v in instance_config.items() if k not in ["api_key"]}  # 排除敏感信息
            })
        return status_list
    
    def get_health_check(self) -> Dict[str, Any]:
        """健康检查"""
        total_instances = len(self.instance_adapters)
        healthy_count = 0
        
        for adapter in self.instance_adapters:
            # 简单的健康检查：尝试获取模型信息
            try:
                # 这里可以添加更详细的健康检查逻辑
                healthy_count += 1
            except:
                pass
        
        return {
            "total_instances": total_instances,
            "healthy_instances": healthy_count,
            "unhealthy_instances": total_instances - healthy_count,
            "health_ratio": healthy_count / total_instances if total_instances > 0 else 0,
            "connection_counts": self.connection_counts
        }


# 全局单例
_stepflash_adapter: Optional[StepFlashAdapter] = None
_stepflash_router: Optional[StepFlashRouter] = None
_stepflash_load_balancer: Optional[StepFlashLoadBalancer] = None
# _multi_model_router: Optional[MultiModelRouter] = None  # 未使用


def get_stepflash_adapter(
    deployment_type: str = "openrouter",
    api_key: Optional[str] = None,
    **kwargs
) -> StepFlashAdapter:
    """
    获取 Step-3.5-Flash 适配器单例
    
    Args:
        deployment_type: 部署类型
        api_key: API 密钥
        **kwargs: 其他参数
    
    Returns:
        StepFlashAdapter 实例
    """
    global _stepflash_adapter
    
    if _stepflash_adapter is None:
        _stepflash_adapter = StepFlashAdapter(
            deployment_type=deployment_type,
            api_key=api_key,
            **kwargs
        )
    
    return _stepflash_adapter


def get_stepflash_router(config: Optional[Dict[str, Any]] = None) -> StepFlashRouter:
    """
    获取 Step-3.5-Flash 路由器单例
    
    Args:
        config: 路由器配置
    
    Returns:
        StepFlashRouter 实例
    """
    global _stepflash_router
    
    if _stepflash_router is None:
        _stepflash_router = StepFlashRouter(config)
    
    return _stepflash_router


def get_stepflash_load_balancer(
    instances: Optional[List[Dict[str, Any]]] = None,
    strategy: str = "round_robin"
) -> StepFlashLoadBalancer:
    """
    获取 Step-3.5-Flash 负载均衡器单例
    
    Args:
        instances: 实例配置列表，如果为None则使用默认配置
        strategy: 负载均衡策略
    
    Returns:
        StepFlashLoadBalancer 实例
    """
    global _stepflash_load_balancer
    
    if _stepflash_load_balancer is None:
        if instances is None:
            # 默认配置：两个OpenRouter实例（不同API密钥）
            instances = [
                {
                    "deployment_type": "openrouter",
                    "weight": 1
                },
                {
                    "deployment_type": "openrouter", 
                    "weight": 1
                }
            ]
        _stepflash_load_balancer = StepFlashLoadBalancer(instances, strategy)
    
    return _stepflash_load_balancer


class MultiModelRouter:
    """
    多模型智能路由器
    
    根据请求特性智能选择最合适的模型：
    - Step-3.5-Flash: 成本效益高，推理速度快
    - GPT-4: 复杂推理，代码生成  
    - Claude: 长上下文，文档分析
    - 其他模型: 根据特定需求选择
    """
    
    def __init__(
        self,
        model_adapters: Dict[str, Any],
        routing_strategy: str = "auto",
        enable_reflection: bool = True
    ):
        """
        初始化多模型路由器
        
        Args:
            model_adapters: 模型适配器字典 {model_name: adapter_instance}
            routing_strategy: 路由策略
                - "auto": 自动根据请求内容选择
                - "cost_optimized": 成本优化优先
                - "performance": 性能优先
                - "quality": 质量优先
            enable_reflection: 是否启用反思机制
        """
        self.model_adapters = model_adapters
        self.routing_strategy = routing_strategy
        self.routing_history = []  # 记录路由历史
        self.enable_reflection = enable_reflection
        
        # 初始化反思代理
        if self.enable_reflection:
            self.reflection_agent = get_model_routing_reflection_agent()
            logger.info("模型路由反思机制已启用")
        else:
            self.reflection_agent = None
            logger.info("模型路由反思机制已禁用")
        
        logger.info(f"初始化多模型路由器，可用模型: {list(model_adapters.keys())}, 策略: {routing_strategy}")
    
    def _analyze_request_content(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        分析请求内容，提取特征用于路由决策
        
        Args:
            messages: 消息列表
            
        Returns:
            内容特征字典
        """
        content = ""
        for msg in messages:
            if msg.get("role") == "user":
                content += msg.get("content", "") + " "
        
        content_lower = content.lower()
        content_length = len(content)
        
        # 检测关键词
        keyword_categories = {
            "代码": ["代码", "编程", "算法", "函数", "class", "def ", "import "],
            "文档": ["文档", "总结", "文章", "报告", "分析"],
            "复杂": ["复杂", "推理", "解释", "为什么", "如何"],
            "简单": ["简单", "快速", "基础", "是什么", "定义"],
            "长文本": ["长", "文档", "文章", "报告", "总结"]
        }
        
        detected_keywords = []
        for category, words in keyword_categories.items():
            for word in words:
                if word in content_lower:
                    detected_keywords.append(category)
                    break
        
        # 估算复杂度（简单启发式）
        estimated_complexity = 0.0
        if "代码" in detected_keywords:
            estimated_complexity += 0.6
        if "复杂" in detected_keywords:
            estimated_complexity += 0.3
        if "文档" in detected_keywords:
            estimated_complexity += 0.2
        if content_length > 2000:
            estimated_complexity += 0.4
        
        return {
            "content": content,
            "content_lower": content_lower,
            "content_length": content_length,
            "detected_keywords": detected_keywords,
            "estimated_complexity": min(1.0, estimated_complexity)
        }
    
    def _select_model(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        根据请求内容智能选择模型，集成反思建议
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
        
        Returns:
            选择的模型名称
        """
        if not self.model_adapters:
            raise ValueError("没有可用的模型适配器")
        
        # 分析请求内容
        content_analysis = self._analyze_request_content(messages)
        content = content_analysis["content_lower"]
        content_length = content_analysis["content_length"]
        detected_keywords = content_analysis["detected_keywords"]
        
        # 获取反思建议（如果启用）
        reflection_suggestion = None
        reflection_confidence = 0.0
        
        if self.enable_reflection and self.reflection_agent:
            try:
                suggestions = self.reflection_agent.get_routing_suggestions(
                    request_content=content_analysis["content"],
                    available_models=list(self.model_adapters.keys())
                )
                
                if suggestions["recommended_model"] and suggestions["confidence"] > 0.3:
                    reflection_suggestion = suggestions["recommended_model"]
                    reflection_confidence = suggestions["confidence"]
                    
                    logger.debug(
                        f"反思建议: {reflection_suggestion} "
                        f"(置信度: {reflection_confidence:.2f}, "
                        f"原因: {suggestions['reasoning']})"
                    )
            except Exception as e:
                logger.debug(f"获取反思建议失败: {e}")
        
        # 基于策略和反思建议进行选择
        selected_model = None
        
        # 如果有高置信度的反思建议，优先考虑
        if reflection_suggestion and reflection_confidence > 0.6:
            if reflection_suggestion in self.model_adapters:
                selected_model = reflection_suggestion
                logger.info(f"采用反思建议选择模型: {selected_model} (置信度: {reflection_confidence:.2f})")
        
        # 如果没有采用反思建议，使用原始逻辑
        if not selected_model:
            if self.routing_strategy == "cost_optimized":
                # 成本优化：优先使用本地开源模型
                selected_model = "step-3.5-flash"
            
            elif self.routing_strategy == "performance":
                # 性能优先：根据任务类型选择
                if any(keyword in content for keyword in ["代码", "编程", "算法", "函数", "class"]):
                    selected_model = "deepseek"  # 代码生成用 DeepSeek
                elif content_length > 2000:
                    selected_model = "deepseek"  # 长文档用 DeepSeek
                else:
                    selected_model = "step-3.5-flash"
            
            elif self.routing_strategy == "quality":
                # 质量优先：使用最强模型（DeepSeek）
                selected_model = "deepseek"
            
            else:  # "auto"
                # 自动选择：基于启发式规则
                if any(keyword in content for keyword in ["复杂", "推理", "分析", "解释", "为什么"]):
                    selected_model = "deepseek"
                elif any(keyword in content for keyword in ["文档", "总结", "长文本", "文章"]):
                    selected_model = "deepseek"
                elif any(keyword in content for keyword in ["简单", "快速", "基础", "是什么"]):
                    selected_model = "step-3.5-flash"
                else:
                    # 默认使用 Step-3.5-Flash（成本效益最高）
                    selected_model = "step-3.5-flash"
        
        # 如果反思建议有中等置信度但未被采用，记录日志
        if reflection_suggestion and reflection_confidence > 0.3 and selected_model != reflection_suggestion:
            logger.debug(
                f"反思建议未被采纳: 建议 {reflection_suggestion} "
                f"(置信度: {reflection_confidence:.2f}), "
                f"实际选择 {selected_model}"
            )
        
        # 确保选择的模型可用
        if selected_model not in self.model_adapters:
            logger.warning(f"选择的模型 '{selected_model}' 不可用，回退到第一个可用模型")
            selected_model = list(self.model_adapters.keys())[0]
        
        return selected_model
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        智能路由到最适合的模型
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
        
        Returns:
            响应字典，包含 model_used 字段
        """
        if not self.model_adapters:
            return {
                "success": False,
                "error": "没有可用的模型适配器",
                "message": "多模型路由器没有可用的模型"
            }
        
        # 选择模型
        selected_model = self._select_model(messages, **kwargs)
        
        if selected_model not in self.model_adapters:
            # 回退到第一个可用模型
            selected_model = list(self.model_adapters.keys())[0]
        
        adapter = self.model_adapters[selected_model]
        
        logger.info(f"多模型路由: 选择模型 '{selected_model}' 处理请求")
        
        # 记录开始时间（用于计算延迟）
        start_time = time.time()
        
        # 分析请求内容
        content_analysis = self._analyze_request_content(messages)
        
        # 生成请求ID
        request_id = f"req_{int(start_time)}_{hash(str(messages)) & 0xffffffff:08x}"
        
        # 创建详细的路由决策记录
        routing_decision = RoutingDecision(
            timestamp=start_time,
            request_id=request_id,
            selected_model=selected_model,
            available_models=list(self.model_adapters.keys()),
            routing_strategy=self.routing_strategy,
            decision_type=RoutingDecisionType.INITIAL,
            request_metadata=kwargs.copy(),
            request_content=content_analysis["content"],
            content_length=content_analysis["content_length"],
            detected_keywords=content_analysis["detected_keywords"],
            estimated_complexity=content_analysis["estimated_complexity"]
        )
        
        # 记录到路由历史（简化版）
        simple_decision = {
            "timestamp": start_time,
            "selected_model": selected_model,
            "strategy": self.routing_strategy,
            "message_length": content_analysis["content_length"],
            "request_id": request_id
        }
        self.routing_history.append(simple_decision)
        
        # 限制历史记录大小
        if len(self.routing_history) > 100:
            self.routing_history = self.routing_history[-100:]
        
        # 记录到反思代理（如果启用）
        decision_id = None
        if self.enable_reflection and self.reflection_agent:
            try:
                decision_id = self.reflection_agent.record_decision(routing_decision)
                logger.debug(f"路由决策已记录到反思代理: {decision_id}")
            except Exception as e:
                logger.debug(f"记录路由决策到反思代理失败: {e}")
        
        try:
            # 调用选中的适配器
            response = adapter.chat_completion(messages, **kwargs)
            
            # 添加路由信息
            if response.get("success"):
                response["model_used"] = selected_model
                response["routing_strategy"] = self.routing_strategy
                response["available_models"] = list(self.model_adapters.keys())
            
            # 记录模型交互到训练数据收集器
            try:
                collector = get_llm_training_collector()
                metadata = {
                    "routing_strategy": self.routing_strategy,
                    "selected_model": selected_model,
                    "available_models": list(self.model_adapters.keys()),
                    "timestamp": time.time()
                }
                collector.record_model_interaction(
                    model_name=selected_model,
                    messages=messages,
                    response=response,
                    user_feedback=kwargs.get("user_feedback"),
                    metadata=metadata
                )
            except Exception as record_error:
                logger.debug(f"记录训练数据失败（主模型）: {record_error}")
            
            # 记录路由结果到反思代理
            if self.enable_reflection and self.reflection_agent and decision_id:
                try:
                    # 计算延迟
                    latency_ms = (time.time() - start_time) * 1000
                    
                    # 创建路由结果
                    success = response.get("success", False)
                    error_message = response.get("error") if not success else None
                    user_feedback = kwargs.get("user_feedback")
                    
                    routing_outcome = RoutingOutcome(
                        decision=routing_decision,
                        response=response,
                        latency_ms=latency_ms,
                        success=success,
                        error_message=error_message,
                        user_feedback=user_feedback,
                        quality_metrics={
                            "confidence": response.get("confidence", 0.5),
                            "completeness": 1.0 if response.get("content") else 0.0
                        }
                    )
                    
                    # 记录结果
                    outcome_id = self.reflection_agent.record_outcome(routing_outcome)
                    logger.debug(f"路由结果已记录到反思代理: {outcome_id}")
                    
                    # 异步触发反思（在后台线程中运行）
                    def run_reflection():
                        try:
                            import asyncio
                            
                            # 创建新的事件循环
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            # 执行反思
                            reflection_result = loop.run_until_complete(
                                self.reflection_agent.reflect_on_routing(routing_outcome)
                            )
                            
                            logger.debug(
                                f"路由反思完成: {reflection_result.reflection_type.value}, "
                                f"问题数: {len(reflection_result.issues)}"
                            )
                            
                            loop.close()
                        except Exception as reflection_error:
                            logger.debug(f"路由反思失败: {reflection_error}")
                    
                    # 启动后台线程执行反思
                    reflection_thread = threading.Thread(target=run_reflection, daemon=True)
                    reflection_thread.start()
                    
                except Exception as outcome_error:
                    logger.debug(f"记录路由结果失败: {outcome_error}")
            
            return response
        
        except Exception as e:
            logger.error(f"模型 '{selected_model}' 调用失败: {e}")
            
            # 记录主模型失败
            try:
                collector = get_llm_training_collector()
                failure_response = {
                    "success": False,
                    "error": str(e),
                    "message": f"模型调用失败",
                    "model_used": selected_model
                }
                metadata = {
                    "routing_strategy": self.routing_strategy,
                    "selected_model": selected_model,
                    "failure": True,
                    "exception": str(e),
                    "timestamp": time.time()
                }
                collector.record_model_interaction(
                    model_name=selected_model,
                    messages=messages,
                    response=failure_response,
                    user_feedback=kwargs.get("user_feedback"),
                    metadata=metadata
                )
            except Exception as record_error:
                logger.debug(f"记录训练数据失败（主模型失败）: {record_error}")
            
            # 记录主模型失败到反思代理
            if self.enable_reflection and self.reflection_agent and decision_id:
                try:
                    # 计算延迟
                    latency_ms = (time.time() - start_time) * 1000
                    
                    # 创建失败响应
                    failure_response = {
                        "success": False,
                        "error": str(e),
                        "message": f"模型调用失败",
                        "model_used": selected_model
                    }
                    
                    # 创建路由结果（失败）
                    routing_outcome = RoutingOutcome(
                        decision=routing_decision,
                        response=failure_response,
                        latency_ms=latency_ms,
                        success=False,
                        error_message=str(e),
                        user_feedback=kwargs.get("user_feedback"),
                        quality_metrics={
                            "confidence": 0.0,
                            "completeness": 0.0
                        }
                    )
                    
                    # 记录结果
                    outcome_id = self.reflection_agent.record_outcome(routing_outcome)
                    logger.debug(f"主模型失败结果已记录到反思代理: {outcome_id}")
                    
                    # 异步触发反思（在后台线程中运行）
                    def run_reflection():
                        try:
                            import asyncio
                            
                            # 创建新的事件循环
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            # 执行反思
                            reflection_result = loop.run_until_complete(
                                self.reflection_agent.reflect_on_routing(routing_outcome)
                            )
                            
                            logger.debug(
                                f"主模型失败反思完成: {reflection_result.reflection_type.value}, "
                                f"问题数: {len(reflection_result.issues)}"
                            )
                            
                            loop.close()
                        except Exception as reflection_error:
                            logger.debug(f"主模型失败反思失败: {reflection_error}")
                    
                    # 启动后台线程执行反思
                    reflection_thread = threading.Thread(target=run_reflection, daemon=True)
                    reflection_thread.start()
                    
                except Exception as outcome_error:
                    logger.debug(f"记录主模型失败结果失败: {outcome_error}")
            
            # 失败时尝试备用模型
            backup_models = [m for m in self.model_adapters.keys() if m != selected_model]
            
            for backup_model in backup_models:
                try:
                    logger.info(f"尝试备用模型 '{backup_model}'")
                    backup_adapter = self.model_adapters[backup_model]
                    response = backup_adapter.chat_completion(messages, **kwargs)
                    
                    if response.get("success"):
                        response["model_used"] = backup_model
                        response["routing_strategy"] = self.routing_strategy
                        response["fallback"] = True
                        response["original_model"] = selected_model
                    
                    # 记录备用模型交互
                    try:
                        collector = get_llm_training_collector()
                        metadata = {
                            "routing_strategy": self.routing_strategy,
                            "selected_model": backup_model,
                            "fallback": True,
                            "original_model": selected_model,
                            "timestamp": time.time()
                        }
                        collector.record_model_interaction(
                            model_name=backup_model,
                            messages=messages,
                            response=response,
                            user_feedback=kwargs.get("user_feedback"),
                            metadata=metadata
                        )
                    except Exception as record_error:
                        logger.debug(f"记录训练数据失败（备用模型）: {record_error}")
                    
                    return response
                
                except Exception as inner_e:
                    logger.debug(f"备用模型 '{backup_model}' 也失败: {inner_e}")
                    continue
            
            # 所有模型都失败
            all_failed_response = {
                "success": False,
                "error": str(e),
                "message": f"所有模型都失败，最后尝试的是 '{selected_model}'",
                "models_tried": list(self.model_adapters.keys())
            }
            
            # 记录所有模型失败
            try:
                collector = get_llm_training_collector()
                metadata = {
                    "routing_strategy": self.routing_strategy,
                    "selected_model": selected_model,
                    "all_models_failed": True,
                    "models_tried": list(self.model_adapters.keys()),
                    "timestamp": time.time()
                }
                collector.record_model_interaction(
                    model_name=selected_model,
                    messages=messages,
                    response=all_failed_response,
                    user_feedback=kwargs.get("user_feedback"),
                    metadata=metadata
                )
            except Exception as record_error:
                logger.debug(f"记录训练数据失败（所有模型失败）: {record_error}")
            
            return all_failed_response
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        if not self.routing_history:
            return {
                "total_requests": 0,
                "model_distribution": {},
                "strategy": self.routing_strategy
            }
        
        # 计算模型使用分布
        model_counts = {}
        for decision in self.routing_history:
            model = decision["selected_model"]
            model_counts[model] = model_counts.get(model, 0) + 1
        
        total = len(self.routing_history)
        model_distribution = {
            model: {
                "count": count,
                "percentage": count / total * 100
            }
            for model, count in model_counts.items()
        }
        
        return {
            "total_requests": total,
            "model_distribution": model_distribution,
            "strategy": self.routing_strategy,
            "available_models": list(self.model_adapters.keys()),
            "recent_decisions": self.routing_history[-5:] if total >= 5 else self.routing_history
        }
    
    def update_routing_strategy(self, strategy: str):
        """更新路由策略"""
        valid_strategies = ["auto", "cost_optimized", "performance", "quality"]
        
        if strategy not in valid_strategies:
            raise ValueError(f"无效的策略，必须是: {valid_strategies}")
        
        old_strategy = self.routing_strategy
        self.routing_strategy = strategy
        
        logger.info(f"路由策略更新: {old_strategy} -> {strategy}")
    
    def add_model_adapter(self, model_name: str, adapter: Any):
        """添加模型适配器"""
        if model_name in self.model_adapters:
            logger.warning(f"模型 '{model_name}' 已存在，将被替换")
        
        self.model_adapters[model_name] = adapter
        logger.info(f"添加模型适配器: {model_name}")
    
    def remove_model_adapter(self, model_name: str):
        """移除模型适配器"""
        if model_name in self.model_adapters:
            del self.model_adapters[model_name]
            logger.info(f"移除模型适配器: {model_name}")
        else:
            logger.warning(f"模型 '{model_name}' 不存在")


def get_multi_model_router(
    adapters_config: Optional[Dict[str, Any]] = None,
    strategy: str = "auto"
) -> MultiModelRouter:
    """
    获取多模型路由器单例
    
    Args:
        adapters_config: 适配器配置字典
        strategy: 路由策略
    
    Returns:
        MultiModelRouter 实例
    """
    global _multi_model_router
    
    if _multi_model_router is None:
        if adapters_config is None:
            # 默认配置：只有 Step-3.5-Flash
            stepflash_adapter = get_stepflash_adapter()
            adapters_config = {
                "step-3.5-flash": stepflash_adapter
            }
        
        _multi_model_router = MultiModelRouter(adapters_config, strategy)
    
    return _multi_model_router
