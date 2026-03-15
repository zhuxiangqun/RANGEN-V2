"""
系统性能优化器
专门解决系统卡顿问题
"""

import asyncio
import time
import logging
import threading
from typing import Dict, Any, Optional, Callable, Awaitable

# 智能配置系统导入
from src.utils.smart_config_system import get_smart_config, create_query_context
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_time: float
    async_operations: int
    sync_operations: int
    timeout_count: int
    error_count: int

class SystemPerformanceOptimizer:
    """系统性能优化器 - 专门解决卡顿问题"""

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._metrics = PerformanceMetrics(get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")), 0, 0, 0, 0)
        self._lock = threading.Lock()
        self._timeout_config = {
            'default': config.DEFAULT_SMALL_LIMIT.0,
            'faiss_init': 5.0,
            'knowledge_retrieval': 15.0,
            'reasoning': 20.0,
            'answer_generation': 15.0,
            'citation': config.DEFAULT_SMALL_LIMIT.0
        }
        
        # 🚀 初始化RL系统用于性能优化
        self.rl_system = None
        self._init_rl_system()

    def _init_rl_system(self):
        """初始化RL系统用于性能优化"""
        try:
            from src.utils.deep_reinforcement_learning import DeepReinforcementLearningSystem
            self.rl_system = DeepReinforcementLearningSystem('DQN', 5, config.DEFAULT_SMALL_LIMIT)
            logger.info("✅ RL系统初始化成功，用于系统性能优化")
        except ImportError:
            try:
                from src.utils.deep_reinforcement_learning import DeepReinforcementLearningSystem
                self.rl_system = DeepReinforcementLearningSystem('DQN', 5, config.DEFAULT_SMALL_LIMIT)
                logger.info("✅ RL系统初始化成功，用于系统性能优化")
            except Exception as e:
                logger.warning("⚠️ RL系统初始化失败: %s", str(e))
                self.rl_system = None
        except Exception as e:
            logger.warning("⚠️ RL系统初始化失败: %s", str(e))
            self.rl_system = None

    def _optimize_timeout_with_rl(self, operation: str) -> float:
        """🚀 使用RL智能体优化超时配置"""
        try:
            if not self.rl_system:
                return self._timeout_config.get(operation, self._timeout_config['default'])
            
            # 构建RL状态
            rl_state = self._build_performance_state(operation)
            
            # 使用RL选择超时策略
            try:
                action = self.rl_system.select_action(rl_state)
                # 确保action是整数类型
                if isinstance(action, (list, tuple)):
                    action = action[0] if action else 0
                action = int(action)
                
                # 映射动作到超时配置
                # 使用智能配置系统获取超时映射
                perf_context = create_query_context(query_type="performance_config")
                timeout_mapping = {
                    0: get_smart_config("fast_mode_multiplier", perf_context),   # 快速模式
                    1: get_smart_config("standard_mode_multiplier", perf_context),   # 标准模式
                    2: get_smart_config("relaxed_mode_multiplier", perf_context),   # 宽松模式
                    3: get_smart_config("very_relaxed_mode_multiplier", perf_context),   # 非常宽松模式
                    4: get_smart_config("ultra_relaxed_mode_multiplier", perf_context)    # 超宽松模式
                }

                base_timeout = self._timeout_config.get(operation, self._timeout_config['default'])
                default_multiplier = get_smart_config("default_multiplier", perf_context)
                multiplier = timeout_mapping.get(action, default_multiplier)
                optimized_timeout = base_timeout * multiplier
                
                logger.info(f"🎲 RL优化超时配置: 操作={operation}, 动作={action}, 超时={optimized_timeout:.1f}s")
                
                return optimized_timeout
                
            except Exception as e:
                logger.warning("⚠️ RL超时优化失败: %s，使用默认配置", str(e))
                return self._timeout_config.get(operation, self._timeout_config['default'])
                
        except Exception as e:
            logger.warning("🚨 RL超时优化失败: %s", str(e))
            return self._timeout_config.get(operation, self._timeout_config['default'])

    def _build_performance_state(self, operation: str) -> Any:
        """构建性能RL状态向量"""
        try:
            # 状态向量: [操作类型, 历史超时率, 历史错误率, 系统负载, 历史成功率]
            operation_type = hash(operation) % config.DEFAULT_SMALL_LIMIT / config.DEFAULT_SMALL_LIMIT.0  # 操作类型编码
            timeout_rate = min(get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")), self._metrics.timeout_count / max(1, self._metrics.async_operations + self._metrics.sync_operations))
            error_rate = min(get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")), self._metrics.error_count / max(1, self._metrics.async_operations + self._metrics.sync_operations))
            system_load = get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))  # 默认系统负载
            success_rate = get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")) - timeout_rate - error_rate
            
            # 检查numpy是否可用
            try:
                import numpy as np
                return np.array([operation_type, timeout_rate, error_rate, system_load, success_rate])
            except ImportError:
                return [operation_type, timeout_rate, error_rate, system_load, success_rate]
                
        except Exception as e:
            logger.warning("构建性能RL状态失败: %s", str(e))
            default_state = [get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")), get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")), get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")), get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")), get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))]
            try:
                import numpy as np
                return np.array(default_state)
            except ImportError:
                return default_state

    async def run_with_timeout(self,
                              coro: Awaitable,
                              operation: str = 'default',
                              fallback: Optional[Callable] = None) -> Any:
        """带超时控制的异步执行 - 集成RL智能体优化"""
        # 🚀 使用RL智能体优化超时配置
        if self.rl_system:
            timeout = self._optimize_timeout_with_rl(operation)
        else:
            timeout = self._timeout_config.get(operation, self._timeout_config['default'])

        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            with self._lock:
                self._metrics.async_operations += 1
            return result

        except asyncio.TimeoutError:
            with self._lock:
                self._metrics.timeout_count += 1
            logger.warning("⚠️ 操作超时: %s (超时时间: %.1fs)", operation, timeout)

            if fallback:
                try:
                    return await fallback()
                except Exception as e:
                    logger.error(f"回退操作失败: {e}")

            return None

        except Exception as e:
            with self._lock:
                self._metrics.error_count += 1
            logger.error(f"❌ 操作失败: {operation} - {e}")
            raise

    def run_sync_with_timeout(self,
                             func: Callable,
                             *args,
                             operation: str = 'default',
                             fallback: Optional[Callable] = None,
                             **kwargs) -> Any:
        """带超时控制的同步执行 - 集成RL智能体优化"""
        # 🚀 使用RL智能体优化超时配置
        if self.rl_system:
            timeout = self._optimize_timeout_with_rl(operation)
        else:
            timeout = self._timeout_config.get(operation, self._timeout_config['default'])

        try:
            future = self._executor.submit(func, *args, **kwargs)
            result = future.result(timeout=timeout)
            with self._lock:
                self._metrics.sync_operations += 1
            return result

        except TimeoutError:
            with self._lock:
                self._metrics.timeout_count += 1
            logger.warning("⚠️ 同步操作超时: %s (超时时间: %.1fs)", operation, timeout)

            if fallback:
                try:
                    return fallback()
                except Exception as e:
                    logger.error(f"回退操作失败: {e}")

            return None

        except Exception as e:
            with self._lock:
                self._metrics.error_count += 1
            logger.error(f"❌ 同步操作失败: {operation} - {e}")
            raise

    async def safe_faiss_operation(self,
                                  faiss_memory,
                                  operation: str,
                                  *args,
                                  **kwargs) -> Any:
        """安全的FAISS操作，避免卡顿"""
        if not faiss_memory:
            logger.warning("⚠️ FAISS内存系统未初始化")
            return None

        try:
            if hasattr(faiss_memory, 'ensure_index_ready'):
                await self.run_with_timeout(
                    faiss_memory.ensure_index_ready(),
                    operation='faiss_init'
                )
            elif hasattr(faiss_memory, 'wait_for_initialization'):
                await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    lambda: faiss_memory.wait_for_initialization(timeout=get_smart_config("faiss_init_timeout", create_query_context(query_type="performance_config")))
                )

            if operation == 'search':
                return faiss_memory.search(*args, **kwargs)
            elif operation == 'add':
                return faiss_memory.add(*args, **kwargs)
            elif operation == 'update':
                return faiss_memory.update(*args, **kwargs)
            else:
                logger.warning("⚠️ 未知的FAISS操作: %s", operation)
                return None

        except Exception as e:
            logger.error(f"❌ FAISS操作失败: {operation} - {e}")
            return None

    def get_metrics(self) -> PerformanceMetrics:
        """获取性能指标"""
        with self._lock:
            return PerformanceMetrics(
                execution_time=time.time(),
                async_operations=self._metrics.async_operations,
                sync_operations=self._metrics.sync_operations,
                timeout_count=self._metrics.timeout_count,
                error_count=self._metrics.error_count
            )

_global_optimizer: Optional[SystemPerformanceOptimizer] = None

def get_global_optimizer() -> SystemPerformanceOptimizer:
    """获取全局性能优化器实例"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = SystemPerformanceOptimizer()
    return _global_optimizer

def optimize_async_function(operation: str = 'default'):
    """异步函数优化装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            optimizer = get_global_optimizer()
            return await optimizer.run_with_timeout(
                func(*args, **kwargs),
                operation=operation
            )
        return wrapper
    return decorator
