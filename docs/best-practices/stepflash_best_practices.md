# Step-3.5-Flash 最佳实践指南

## 概述

Step-3.5-Flash 是 StepFun 开发的开源稀疏 MoE 大语言模型，具有 196B 总参数和 11B 活跃参数。本指南提供在 RANGEN 系统中使用 Step-3.5-Flash 的最佳实践。

## 目录

1. [部署策略](#部署策略)
2. [性能优化](#性能优化)
3. [错误处理与重试](#错误处理与重试)
4. [监控与指标](#监控与指标)
5. [安全配置](#安全配置)
6. [成本优化](#成本优化)
7. [故障排除](#故障排除)
8. [实际案例](#实际案例)

## 部署策略

### 1. 选择适合的部署方式

Step-3.5-Flash 支持三种部署方式，根据您的需求选择：

#### OpenRouter API (推荐用于开发和生产)
- **优点**: 无需自行部署，API 稳定，有免费额度
- **适用场景**: 快速原型开发、中小规模生产应用
- **配置示例**:
  ```bash
  # .env 配置
  LLM_PROVIDER=stepflash
  STEPSFLASH_API_KEY=sk-or-xxx-xxx
  STEPFLASH_DEPLOYMENT_TYPE=openrouter
  ```

#### NVIDIA NIM API (推荐企业用户)
- **优点**: 高性能，企业级 SLA，支持私有部署
- **适用场景**: 企业应用、高并发生产环境
- **配置示例**:
  ```bash
  # .env 配置
  LLM_PROVIDER=stepflash
  STEPSFLASH_API_KEY=your-nvidia-nim-api-key
  STEPFLASH_DEPLOYMENT_TYPE=nvidia_nim
  STEPFLASH_BASE_URL=https://api.nvidia.com/nim/v1
  ```

#### vLLM 本地部署 (推荐技术团队)
- **优点**: 完全控制，数据隐私，可定制化
- **适用场景**: 数据敏感应用、大规模自部署
- **配置示例**:
  ```bash
  # .env 配置
  LLM_PROVIDER=stepflash
  STEPFLASH_DEPLOYMENT_TYPE=vllm_local
  STEPFLASH_BASE_URL=http://localhost:8000/v1
  ```

### 2. 部署决策矩阵

| 需求 | 推荐部署 | 理由 |
|------|----------|------|
| 快速启动 | OpenRouter | 无需配置，5分钟即可使用 |
| 数据安全 | vLLM 本地 | 数据不离开本地网络 |
| 高并发 | NVIDIA NIM | 企业级性能和扩展性 |
| 成本敏感 | OpenRouter | 有免费额度，按需付费 |
| 定制需求 | vLLM 本地 | 完全控制模型和参数 |

## 性能优化

### 1. 适配器参数调优

StepFlashAdapter 提供多个可调参数，根据使用场景优化：

#### 开发环境配置
```python
from src.services.stepflash_adapter import StepFlashAdapter

# 开发环境 - 快速响应
dev_adapter = StepFlashAdapter(
    deployment_type="openrouter",
    timeout=15,           # 短超时，快速失败
    max_tokens=2048,      # 适中输出长度
    temperature=0.7,      # 标准创造性
    max_retries=2,        # 少量重试
    retry_delay=1.0       # 短重试间隔
)
```

#### 生产环境配置
```python
# 生产环境 - 稳定可靠
prod_adapter = StepFlashAdapter(
    deployment_type="openrouter",
    timeout=45,           # 长超时，避免中断长任务
    max_tokens=8192,      # 支持长文本生成
    temperature=0.3,      # 低温度，更确定输出
    max_retries=5,        # 多次重试保证可用性
    retry_delay=2.0,      # 指数退避起始延迟
)
```

#### 批处理任务配置
```python
# 批处理任务 - 高吞吐量
batch_adapter = StepFlashAdapter(
    deployment_type="nvidia_nim",  # 高并发支持
    timeout=60,           # 长超时适应批处理
    max_tokens=4096,      # 适中输出
    temperature=0.5,      # 平衡创造性和一致性
    max_retries=3,        # 适中重试
    retry_delay=1.5       # 适中重试间隔
)
```

### 2. 消息处理优化

#### 批量消息处理
```python
from src.services.stepflash_adapter import StepFlashAdapter

adapter = StepFlashAdapter()

# 批量处理消息，减少API调用
batch_messages = [
    [{"role": "user", "content": "问题1"}],
    [{"role": "user", "content": "问题2"}],
    [{"role": "user", "content": "问题3"}]
]

# 使用异步处理提高吞吐量
import asyncio

async def process_batch(messages_batch):
    tasks = []
    for messages in messages_batch:
        task = asyncio.create_task(
            adapter.chat_completion(messages)
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# 或者使用线程池
from concurrent.futures import ThreadPoolExecutor

def process_batch_sync(messages_batch, max_workers=3):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(adapter.chat_completion, messages)
            for messages in messages_batch
        ]
        
        results = []
        for future in futures:
            try:
                results.append(future.result(timeout=30))
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        
        return results
```

#### 消息压缩和优化
```python
def optimize_messages(messages, max_tokens=8000):
    """
    优化消息以减少token消耗
    
    策略:
    1. 合并连续的用户消息
    2. 截断过长消息
    3. 移除不必要的元数据
    """
    optimized = []
    current_user_content = []
    
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("role", "user")
            content = msg.get("content", "")
        else:
            # 支持ChatMessage对象
            role = getattr(msg, "role", "user")
            content = getattr(msg, "content", "")
        
        if role == "user":
            current_user_content.append(content)
        else:
            # 如果有累积的用户消息，先合并
            if current_user_content:
                optimized.append({
                    "role": "user",
                    "content": " ".join(current_user_content)[:max_tokens]
                })
                current_user_content = []
            
            # 添加助手消息
            optimized.append({
                "role": role,
                "content": content[:max_tokens]
            })
    
    # 处理最后累积的用户消息
    if current_user_content:
        optimized.append({
            "role": "user",
            "content": " ".join(current_user_content)[:max_tokens]
        })
    
    return optimized
```

### 3. 缓存策略

#### 响应缓存
```python
import hashlib
import json
import time
from functools import lru_cache

class StepFlashResponseCache:
    """Step-3.5-Flash 响应缓存"""
    
    def __init__(self, ttl_seconds=3600, max_size=1000):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.cache = {}
        self.access_time = {}
    
    def _get_cache_key(self, messages, params):
        """生成缓存键"""
        # 序列化消息和参数
        messages_str = json.dumps(messages, sort_keys=True)
        params_str = json.dumps(params, sort_keys=True)
        
        # 生成哈希
        combined = f"{messages_str}||{params_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, messages, params):
        """获取缓存的响应"""
        cache_key = self._get_cache_key(messages, params)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # 检查是否过期
            if time.time() - entry["timestamp"] < self.ttl:
                # 更新访问时间
                self.access_time[cache_key] = time.time()
                return entry["response"]
            else:
                # 过期删除
                del self.cache[cache_key]
                del self.access_time[cache_key]
        
        return None
    
    def put(self, messages, params, response):
        """缓存响应"""
        cache_key = self._get_cache_key(messages, params)
        
        # 如果缓存已满，删除最久未使用的
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_time.items(), key=lambda x: x[1])[0]
            del self.cache[oldest_key]
            del self.access_time[oldest_key]
        
        # 添加新缓存
        self.cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        self.access_time[cache_key] = time.time()
    
    def clear_expired(self):
        """清理过期的缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if current_time - entry["timestamp"] >= self.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_time:
                del self.access_time[key]
```

#### 使用缓存的适配器包装器
```python
from src.services.stepflash_adapter import StepFlashAdapter

class CachedStepFlashAdapter(StepFlashAdapter):
    """带缓存的 StepFlashAdapter"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = StepFlashResponseCache()
        
        # 可缓存的方法
        self.cacheable_methods = {"chat_completion"}
    
    def chat_completion(self, messages, **kwargs):
        # 检查是否应该跳过缓存
        skip_cache = kwargs.pop("skip_cache", False)
        
        if not skip_cache:
            # 尝试从缓存获取
            params = {
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "model": self.model
            }
            
            cached_response = self.cache.get(messages, params)
            if cached_response:
                return cached_response
        
        # 调用原始方法
        response = super().chat_completion(messages, **kwargs)
        
        if not skip_cache and response.get("success"):
            # 缓存成功响应
            params = {
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "model": self.model
            }
            self.cache.put(messages, params, response)
        
        return response
```

## 错误处理与重试

### 1. 智能重试策略

StepFlashAdapter 内置了智能重试机制，但您可以根据需要自定义：

#### 自定义重试策略
```python
from src.services.stepflash_adapter import StepFlashAdapter
import time

class SmartRetryStepFlashAdapter(StepFlashAdapter):
    """智能重试策略的适配器"""
    
    def __init__(self, *args, **kwargs):
        # 自定义重试配置
        self.retry_config = {
            "transient_errors": [429, 500, 502, 503, 504, 408],  # 可重试错误码
            "permanent_errors": [400, 401, 403, 404, 422],      # 不可重试错误码
            "jitter_factor": 0.1,  # 抖动因子，避免重试风暴
            "backoff_multiplier": 2.0,  # 退避乘数
        }
        super().__init__(*args, **kwargs)
    
    def chat_completion(self, messages, **kwargs):
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 包括第一次尝试
            try:
                # 如果有抖动，添加随机延迟
                if attempt > 0:
                    jitter = 1 + (random.random() * 2 - 1) * self.retry_config["jitter_factor"]
                    sleep_time = self.retry_delay * (self.retry_config["backoff_multiplier"] ** (attempt - 1)) * jitter
                    time.sleep(sleep_time)
                
                # 调用父类方法
                response = super().chat_completion(messages, **kwargs)
                
                # 检查响应中的错误
                if not response.get("success"):
                    error_msg = response.get("error", "")
                    
                    # 根据错误类型决定是否重试
                    if self._should_retry(error_msg, attempt):
                        continue
                    else:
                        return response
                
                return response
                
            except Exception as e:
                last_exception = e
                
                # 检查异常类型决定是否重试
                if self._should_retry_exception(e, attempt):
                    continue
                else:
                    break
        
        # 所有重试都失败
        return {
            "success": False,
            "error": f"所有重试失败: {last_exception}" if last_exception else "未知错误",
            "attempts": self.max_retries + 1
        }
    
    def _should_retry(self, error_msg, attempt):
        """根据错误消息决定是否重试"""
        # 检查是否为可重试错误
        for code in self.retry_config["transient_errors"]:
            if f"错误: {code}" in error_msg or f"status: {code}" in error_msg.lower():
                return attempt < self.max_retries
        
        # 检查是否为不可重试错误
        for code in self.retry_config["permanent_errors"]:
            if f"错误: {code}" in error_msg or f"status: {code}" in error_msg.lower():
                return False
        
        # 默认重试策略
        return attempt < self.max_retries
    
    def _should_retry_exception(self, exception, attempt):
        """根据异常类型决定是否重试"""
        import requests
        
        if isinstance(exception, requests.exceptions.Timeout):
            return attempt < self.max_retries
        
        if isinstance(exception, requests.exceptions.ConnectionError):
            return attempt < self.max_retries
        
        if isinstance(exception, requests.exceptions.HTTPError):
            # 检查HTTP错误码
            if hasattr(exception, 'response') and exception.response is not None:
                status_code = exception.response.status_code
                if status_code in self.retry_config["transient_errors"]:
                    return attempt < self.max_retries
        
        return False
```

### 2. 优雅降级策略

当 Step-3.5-Flash 不可用时，提供备用方案：

```python
class ResilientLLMService:
    """弹性的LLM服务，支持优雅降级"""
    
    def __init__(self, primary_adapter, fallback_adapter=None):
        self.primary_adapter = primary_adapter
        self.fallback_adapter = fallback_adapter
        self.primary_failures = 0
        self.max_failures_before_fallback = 3
        
    def chat_completion(self, messages, **kwargs):
        # 如果主适配器连续失败多次，切换到备用
        if self.primary_failures >= self.max_failures_before_fallback and self.fallback_adapter:
            return self._call_with_fallback(messages, **kwargs)
        
        try:
            # 尝试主适配器
            response = self.primary_adapter.chat_completion(messages, **kwargs)
            
            if response.get("success"):
                # 重置失败计数
                if self.primary_failures > 0:
                    self.primary_failures = 0
                return response
            else:
                # 主适配器失败
                self.primary_failures += 1
                
                # 如果设置了备用适配器，尝试备用
                if self.fallback_adapter:
                    return self._call_with_fallback(messages, **kwargs)
                else:
                    return response
                    
        except Exception as e:
            # 主适配器异常
            self.primary_failures += 1
            logger.error(f"主适配器异常: {e}")
            
            if self.fallback_adapter:
                return self._call_with_fallback(messages, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"主适配器异常: {e}"
                }
    
    def _call_with_fallback(self, messages, **kwargs):
        """使用备用适配器调用"""
        try:
            response = self.fallback_adapter.chat_completion(messages, **kwargs)
            
            if response.get("success"):
                logger.info("成功使用备用适配器")
            else:
                logger.warning(f"备用适配器也失败: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"备用适配器异常: {e}")
            return {
                "success": False,
                "error": f"所有适配器都失败: {e}"
            }
```

### 3. 断路器模式

防止级联故障的断路器实现：

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # 正常状态，请求通过
    OPEN = "open"          # 打开状态，请求被拒绝
    HALF_OPEN = "half_open" # 半开状态，尝试恢复

class CircuitBreaker:
    """断路器模式实现"""
    
    def __init__(self, failure_threshold=5, reset_timeout=60, half_open_max_attempts=3):
        self.failure_threshold = failure_threshold  # 失败阈值
        self.reset_timeout = reset_timeout          # 重置超时（秒）
        self.half_open_max_attempts = half_open_max_attempts  # 半开状态最大尝试次数
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_attempts = 0
        
    def call(self, func, *args, **kwargs):
        """通过断路器调用函数"""
        # 检查断路器状态
        if self.state == CircuitState.OPEN:
            # 检查是否应该进入半开状态
            if self._should_try_half_open():
                self.state = CircuitState.HALF_OPEN
                self.half_open_attempts = 0
            else:
                raise CircuitBreakerOpenError("断路器打开，请求被拒绝")
        
        try:
            # 执行函数
            result = func(*args, **kwargs)
            
            # 调用成功
            self._on_success()
            return result
            
        except Exception as e:
            # 调用失败
            self._on_failure()
            raise
    
    def _should_try_half_open(self):
        """检查是否应该尝试进入半开状态"""
        if self.state != CircuitState.OPEN or self.last_failure_time is None:
            return False
        
        # 检查是否过了重置超时时间
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.reset_timeout
    
    def _on_success(self):
        """调用成功时的处理"""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_attempts += 1
            
            # 如果半开状态成功次数达到阈值，关闭断路器
            if self.half_open_attempts >= self.half_open_max_attempts:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_attempts = 0
        else:
            # 关闭状态下的成功，重置失败计数
            self.failure_count = 0
    
    def _on_failure(self):
        """调用失败时的处理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # 半开状态失败，重新打开断路器
            self.state = CircuitState.OPEN
            self.half_open_attempts = 0
        elif self.failure_count >= self.failure_threshold:
            # 达到失败阈值，打开断路器
            self.state = CircuitState.OPEN

class CircuitBreakerOpenError(Exception):
    """断路器打开异常"""
    pass

# 使用断路器的适配器
class CircuitBreakerStepFlashAdapter(StepFlashAdapter):
    """带断路器的 StepFlashAdapter"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            reset_timeout=30,
            half_open_max_attempts=2
        )
    
    def chat_completion(self, messages, **kwargs):
        try:
            return self.circuit_breaker.call(
                super().chat_completion,
                messages,
                **kwargs
            )
        except CircuitBreakerOpenError as e:
            return {
                "success": False,
                "error": str(e),
                "circuit_state": "open"
            }
```

## 监控与指标

### 1. 性能指标收集

```python
import time
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    request_id: str
    timestamp: datetime
    duration_ms: float
    success: bool
    token_count: int = 0
    error_type: str = None
    model: str = None
    deployment_type: str = None

class StepFlashMonitor:
    """Step-3.5-Flash 监控器"""
    
    def __init__(self, window_size=1000):
        self.metrics_history = []
        self.window_size = window_size
        
        # 实时指标
        self.realtime_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_duration_ms": 0,
            "total_tokens": 0,
            "error_counts": {},
            "last_error_time": None,
            "concurrent_requests": 0,
        }
    
    def record_request(self, request_id, duration_ms, success, 
                      token_count=0, error_type=None, model=None, deployment_type=None):
        """记录请求指标"""
        metrics = PerformanceMetrics(
            request_id=request_id,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            success=success,
            token_count=token_count,
            error_type=error_type,
            model=model,
            deployment_type=deployment_type
        )
        
        # 添加到历史记录
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.window_size:
            self.metrics_history.pop(0)
        
        # 更新实时指标
        self.realtime_metrics["total_requests"] += 1
        self.realtime_metrics["total_duration_ms"] += duration_ms
        
        if success:
            self.realtime_metrics["successful_requests"] += 1
            self.realtime_metrics["total_tokens"] += token_count
        else:
            self.realtime_metrics["failed_requests"] += 1
            self.realtime_metrics["last_error_time"] = datetime.now()
            
            if error_type:
                self.realtime_metrics["error_counts"][error_type] = \
                    self.realtime_metrics["error_counts"].get(error_type, 0) + 1
    
    def get_performance_summary(self, window_minutes=5):
        """获取性能摘要"""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        
        # 过滤时间窗口内的指标
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return None
        
        successful = [m for m in recent_metrics if m.success]
        failed = [m for m in recent_metrics if not m.success]
        
        # 计算性能指标
        avg_duration = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)
        success_rate = len(successful) / len(recent_metrics) if recent_metrics else 0
        
        # 计算百分位数
        durations = sorted([m.duration_ms for m in recent_metrics])
        p50 = durations[int(len(durations) * 0.5)] if durations else 0
        p95 = durations[int(len(durations) * 0.95)] if durations else 0
        p99 = durations[int(len(durations) * 0.99)] if durations else 0
        
        # 错误分析
        error_analysis = {}
        for metric in failed:
            if metric.error_type:
                error_analysis[metric.error_type] = \
                    error_analysis.get(metric.error_type, 0) + 1
        
        return {
            "time_window_minutes": window_minutes,
            "total_requests": len(recent_metrics),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "success_rate": success_rate,
            "avg_duration_ms": avg_duration,
            "p50_duration_ms": p50,
            "p95_duration_ms": p95,
            "p99_duration_ms": p99,
            "total_tokens": sum(m.token_count for m in successful),
            "avg_tokens_per_request": sum(m.token_count for m in successful) / len(successful) if successful else 0,
            "error_analysis": error_analysis,
            "deployment_distribution": self._get_deployment_distribution(recent_metrics),
            "model_distribution": self._get_model_distribution(recent_metrics),
        }
    
    def _get_deployment_distribution(self, metrics):
        """获取部署类型分布"""
        distribution = {}
        for metric in metrics:
            if metric.deployment_type:
                distribution[metric.deployment_type] = \
                    distribution.get(metric.deployment_type, 0) + 1
        return distribution
    
    def _get_model_distribution(self, metrics):
        """获取模型分布"""
        distribution = {}
        for metric in metrics:
            if metric.model:
                distribution[metric.model] = \
                    distribution.get(metric.model, 0) + 1
        return distribution
    
    def get_alerts(self):
        """获取告警"""
        alerts = []
        
        # 成功率告警
        recent_summary = self.get_performance_summary(window_minutes=1)
        if recent_summary and recent_summary["success_rate"] < 0.9:
            alerts.append({
                "type": "low_success_rate",
                "severity": "warning",
                "message": f"成功率低于90%: {recent_summary['success_rate']:.2%}",
                "timestamp": datetime.now()
            })
        
        # 响应时间告警
        if recent_summary and recent_summary["p95_duration_ms"] > 10000:  # 10秒
            alerts.append({
                "type": "high_response_time",
                "severity": "warning",
                "message": f"P95响应时间超过10秒: {recent_summary['p95_duration_ms']:.0f}ms",
                "timestamp": datetime.now()
            })
        
        # 连续错误告警
        if self.realtime_metrics["failed_requests"] > 10:
            alerts.append({
                "type": "consecutive_failures",
                "severity": "critical",
                "message": f"连续失败请求: {self.realtime_metrics['failed_requests']}",
                "timestamp": datetime.now()
            })
        
        return alerts
```

### 2. 与系统监控集成

```python
from src.core.monitoring_system import MonitoringSystem

class IntegratedStepFlashMonitor(StepFlashMonitor):
    """与系统监控集成的监控器"""
    
    def __init__(self, monitoring_system=None):
        super().__init__()
        self.monitoring_system = monitoring_system or MonitoringSystem()
        
    def record_request(self, *args, **kwargs):
        """记录请求并发送到监控系统"""
        super().record_request(*args, **kwargs)
        
        # 发送指标到监控系统
        if self.monitoring_system:
            metrics = args[1] if len(args) > 1 else kwargs.get('duration_ms', 0)
            success = args[2] if len(args) > 2 else kwargs.get('success', False)
            
            # 发送基本指标
            self.monitoring_system.record_metric(
                "stepflash.request.duration_ms",
                metrics,
                tags={
                    "success": str(success).lower(),
                    "model": kwargs.get('model', 'unknown'),
                    "deployment": kwargs.get('deployment_type', 'unknown')
                }
            )
            
            # 发送成功率指标
            self.monitoring_system.record_metric(
                "stepflash.request.success",
                1 if success else 0
            )
            
            # 发送token计数
            if kwargs.get('token_count', 0) > 0:
                self.monitoring_system.record_metric(
                    "stepflash.request.tokens",
                    kwargs.get('token_count')
                )
            
            # 检查并发送告警
            alerts = self.get_alerts()
            for alert in alerts:
                self.monitoring_system.send_alert(
                    alert["type"],
                    alert["message"],
                    severity=alert["severity"]
                )
```

## 安全配置

### 1. API密钥安全管理

```python
import os
from cryptography.fernet import Fernet
import base64

class SecureAPIKeyManager:
    """安全的API密钥管理器"""
    
    def __init__(self, encryption_key=None):
        # 使用环境变量中的加密密钥或生成新密钥
        env_key = os.getenv("STEPFLASH_ENCRYPTION_KEY")
        if env_key:
            self.cipher = Fernet(base64.b64decode(env_key))
        elif encryption_key:
            self.cipher = Fernet(encryption_key)
        else:
            # 生成新密钥（仅用于开发）
            key = Fernet.generate_key()
            self.cipher = Fernet(key)
            print(f"警告: 生成了新的加密密钥，请保存到环境变量: {base64.b64encode(key).decode()}")
        
    def encrypt_api_key(self, api_key):
        """加密API密钥"""
        encrypted = self.cipher.encrypt(api_key.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_api_key(self, encrypted_key):
        """解密API密钥"""
        encrypted = base64.b64decode(encrypted_key)
        return self.cipher.decrypt(encrypted).decode()
    
    def get_api_key_from_env(self, env_var="STEPSFLASH_API_KEY"):
        """从环境变量获取并解密API密钥"""
        encrypted_key = os.getenv(env_var)
        if not encrypted_key:
            return None
        
        try:
            return self.decrypt_api_key(encrypted_key)
        except Exception as e:
            logger.error(f"API密钥解密失败: {e}")
            return None
    
    def rotate_key(self, new_key):
        """轮换加密密钥"""
        old_cipher = self.cipher
        self.cipher = Fernet(new_key)
        
        # 重新加密所有存储的API密钥
        # 这里需要根据实际存储方式实现
        pass
```

### 2. 请求验证和限流

```python
import time
from collections import defaultdict

class RequestValidator:
    """请求验证和限流器"""
    
    def __init__(self, rate_limit_per_minute=60, max_tokens_per_request=10000):
        self.rate_limit = rate_limit_per_minute
        self.max_tokens = max_tokens_per_request
        
        # 限流跟踪
        self.request_counts = defaultdict(list)
        self.blocked_ips = set()
        
    def validate_request(self, messages, ip_address=None, user_id=None):
        """验证请求"""
        violations = []
        
        # 1. 检查消息格式
        if not self._validate_message_format(messages):
            violations.append("invalid_message_format")
        
        # 2. 检查token限制
        estimated_tokens = self._estimate_tokens(messages)
        if estimated_tokens > self.max_tokens:
            violations.append(f"token_limit_exceed