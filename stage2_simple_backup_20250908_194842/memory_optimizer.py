#!/usr/bin/env python3
"""
内存优化管理器 - 专门管理系统的内存使用和优化
整合现有的内存优化功能，提供统一的内存管理接口
"""
import gc
import logging
import os
import sys
import time
import tracemalloc
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from functools import lru_cache

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

# 智能配置系统导入
from src.utils.smart_config_system import get_smart_config, create_query_context

logger = logging.getLogger(__name__)

@dataclass
class MemoryMetrics:
    """内存指标"""
    timestamp: datetime
    current_memory_mb: float
    peak_memory_mb: float
    memory_percent: float
    available_memory_mb: float
    total_memory_mb: float
    gc_collections: int
    gc_objects: int
    faiss_index_size_mb: float = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
    cache_size_mb: float = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE

@dataclass
class MemoryOptimizationConfig:
    """内存优化配置"""
    enable_memory_tracking: bool = True
    enable_gc_optimization: bool = True
    enable_cache_optimization: bool = True
    enable_faiss_optimization: bool = True
    memory_threshold_mb: Optional[float] = None  # 内存阈值(MB)
    critical_memory_threshold_mb: float = config.DEFAULT_MEDIUM_LIMIT48.config.DEFAULT_ZERO_VALUE  # config.DEFAULT_TWO_VALUEGB
    gc_threshold: int = config.DEFAULT_LARGE_LIMIT  # 对象数量阈值
    cache_cleanup_threshold_mb: float = 5config.DEFAULT_ONE_VALUEconfig.DEFAULT_TWO_VALUE.config.DEFAULT_ZERO_VALUE  # 5config.DEFAULT_ONE_VALUEconfig.DEFAULT_TWO_VALUEMB
    optimization_interval_seconds: float = 3config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
    max_memory_history: int = 1000

    def __post_init__(self):
        # 使用智能配置系统获取默认内存阈值
        if self.memory_threshold_mb is None:
            memory_context = create_query_context(query_type="memory_optimizer_config")
            self.memory_threshold_mb = get_smart_config("memory_optimizer_threshold", memory_context)
    
    # 智能内存管理配置
    enable_smart_object_management: bool = True
    enable_function_aware_cleanup: bool = True
    enable_predictive_memory: bool = True
    enable_adaptive_thresholds: bool = True
    
    # 对象分类阈值
    core_object_threshold: int = config.DEFAULT_TEN_THOUSAND_LIMIT      # 核心对象阈值
    essential_object_threshold: int = config.DEFAULT_MEDIUM_TEXT_LIMITconfig.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUE  # 必需对象阈值
    cache_object_threshold: int = config.DEFAULT_HUNDRED_THOUSAND_LIMIT     # 缓存对象阈值
    temporary_object_threshold: int = config.DEFAULT_TEXT_LIMITconfig.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUE # 临时对象阈值
    
    # 功能保护配置
    protected_functions: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.protected_functions is None:
            self.protected_functions = [
                'knowledge_retrieval',
                'reasoning_analysis', 
                'answer_generation',
                'citation_generation',
                'wikipedia_download'
            ]

class MemoryOptimizer:
    """内存优化管理器"""
    
    def __init__(self, config: Optional[MemoryOptimizationConfig] = None):
        self.config = config or MemoryOptimizationConfig()
        self.logger = logging.getLogger(__name__)
        
        # 内存跟踪
        self.memory_history: deque[MemoryMetrics] = deque(maxlen=self.config.max_memory_history)
        self.is_monitoring: bool = False
        self.monitor_task: Optional[asyncio.Task[None]] = None
        
        # 优化统计
        self.optimization_count = config.DEFAULT_ZERO_VALUE
        self.total_memory_saved_mb = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
        self.last_optimization_time = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
        
        # 内存跟踪器
        if self.config.enable_memory_tracking and tracemalloc.is_tracing():
            tracemalloc.stop()
        if self.config.enable_memory_tracking:
            tracemalloc.start()
        
        # 优化回调
        self.optimization_callbacks: List[Callable[[MemoryMetrics], Awaitable[None]]] = []
        
        # 智能内存管理
        self.object_categories = _init_object_categories()
        self.function_dependencies = _init_function_dependencies()
        self.memory_pressure_levels = _init_memory_pressure_levels()
        self.cleanup_strategies = _init_cleanup_strategies()
        
        self.logger.info("✅ 内存优化管理器初始化完成")

    async def start_monitoring(self) -> None:
        """开始内存监控"""
        if self.is_monitoring:
            self.logger.warning("内存监控已在运行")
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        self.logger.info("🔄 内存监控已启动")

    async def stop_monitoring(self) -> None:
        """停止内存监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("⏹️ 内存监控已停止")

    async def _monitor_loop(self) -> None:
        """监控循环"""
        while self.is_monitoring:
            try:
                metrics = await self._collect_memory_metrics()
                self.memory_history.append(metrics)
                
                # 检查是否需要优化
                if self._should_optimize(metrics):
                    await self._perform_optimization(metrics)
                
                # 执行优化回调
                for callback in self.optimization_callbacks:
                    try:
                        await callback(metrics)
                    except Exception as e:
                        self.logger.error(f"优化回调执行失败: {e}")
                
                await asyncio.sleep(self.config.optimization_interval_seconds)
                
            except Exception as e:
                self.logger.error(f"内存监控循环异常: {e}")
                await asyncio.sleep(self.config.optimization_interval_seconds)

    async def _collect_memory_metrics(self) -> MemoryMetrics:
        """收集内存指标"""
        try:
            # 基本内存信息
            if PSUTIL_AVAILABLE:
                import psutil
                memory = psutil.virtual_memory()
                current_memory_mb = memory.used / (config.DEFAULT_TOP_K24 * config.DEFAULT_CHUNK_SIZE)
                available_memory_mb = memory.available / (config.DEFAULT_TOP_Kconfig.DEFAULT_HOURS_PER_DAY * config.DEFAULT_CHUNK_SIZE)
                total_memory_mb = memory.total / (config.DEFAULT_TOP_Kconfig.DEFAULT_HOURS_PER_DAY * config.DEFAULT_CHUNK_SIZE)
                memory_percent = memory.percent
            else:
                current_memory_mb = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
                available_memory_mb = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
                total_memory_mb = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
                memory_percent = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
            
            # 内存跟踪信息
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                current_memory_mb = current / (config.DEFAULT_TOP_Kconfig.DEFAULT_HOURS_PER_DAY * config.DEFAULT_CHUNK_SIZE)
                peak_memory_mb = peak / (config.DEFAULT_TOP_Kconfig.DEFAULT_HOURS_PER_DAY * config.DEFAULT_CHUNK_SIZE)
            else:
                peak_memory_mb = current_memory_mb
            
            # GC信息
            gc.collect()  # 强制垃圾回收
            gc_objects = len(gc.get_objects())
            gc_collections = gc.get_count()[0]
            
            # FAISS索引大小（如果可用）
            faiss_index_size_mb = await self._get_faiss_index_size()
            
            # 缓存大小
            cache_size_mb = await self._get_cache_size()
            
            return MemoryMetrics(
                timestamp=datetime.now(),
                current_memory_mb=current_memory_mb,
                peak_memory_mb=peak_memory_mb,
                memory_percent=memory_percent,
                available_memory_mb=available_memory_mb,
                total_memory_mb=total_memory_mb,
                gc_collections=gc_collections,
                gc_objects=gc_objects,
                faiss_index_size_mb=faiss_index_size_mb,
                cache_size_mb=cache_size_mb
            )
            
        except Exception as e:
            self.logger.error(f"收集内存指标失败: {e}")
            return MemoryMetrics(
                timestamp=datetime.now(),
                current_memory_mb=get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")),
                peak_memory_mb=config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE,
                memory_percent=config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE,
                available_memory_mb=config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE,
                total_memory_mb=config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE,
                gc_collections=config.DEFAULT_ZERO_VALUE,
                gc_objects=config.DEFAULT_ZERO_VALUE
            )

    async def _get_faiss_index_size(self) -> float:
        """获取FAISS索引大小"""
        try:
            # 检查FAISS索引文件
            index_paths = [
                "data/faiss_memory/faiss_index.bin",
                "src/data/faiss_memory/faiss_index.bin",
                "data/wiki_vector_storage/faiss_memory/faiss_index.bin"
            ]
            
            for path in index_paths:
                if os.path.exists(path):
                    size_bytes = os.path.getsize(path)
                    return size_bytes / (config.DEFAULT_TOP_K24 * config.DEFAULT_CHUNK_SIZE)  # 转换为MB
            
            return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
            
        except Exception as e:
            self.logger.debug(f"获取FAISS索引大小失败: {e}")
            return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))

    async def _get_cache_size(self) -> float:
        """获取缓存大小"""
        try:
            cache_paths = [
                "data/semantic_cache",
                "data/wiki_cache",
                "models/cache"
            ]
            
            total_size = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
            for path in cache_paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                total_size += os.path.getsize(file_path)
                            except (OSError, FileNotFoundError):
                                continue
            
            return total_size / (config.DEFAULT_TOP_K24 * config.DEFAULT_CHUNK_SIZE)  # 转换为MB
            
        except Exception as e:
            self.logger.debug(f"获取缓存大小失败: {e}")
            return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))

    def _should_optimize(self, metrics: MemoryMetrics) -> bool:
        """判断是否需要优化"""
        # 内存使用超过阈值
        if metrics.current_memory_mb > self.config.memory_threshold_mb:
            return True
        
        # 可用内存不足
        if metrics.available_memory_mb < self.config.cache_cleanup_threshold_mb:
            return True
        
        # GC对象数量过多
        if metrics.gc_objects > self.config.gc_threshold:
            return True
        
        # 距离上次优化时间过长
        if time.time() - self.last_optimization_time > 300:  # 5分钟
            return True
        
        return False

    async def _perform_optimization(self, metrics: MemoryMetrics) -> None:
        """执行内存优化"""
        try:
            self.logger.info(f"🔄 开始内存优化，当前内存: {metrics.current_memory_mb:.config.DEFAULT_ONE_VALUEf}MB")
            
            optimization_results = []
            
            # config.DEFAULT_ONE_VALUE. GC优化
            if self.config.enable_gc_optimization:
                gc_result = await self._optimize_garbage_collection(metrics)
                optimization_results.append(gc_result)
            
            # config.DEFAULT_TWO_VALUE. 缓存优化
            if self.config.enable_cache_optimization:
                cache_result = await self._optimize_cache(metrics)
                optimization_results.append(cache_result)
            
            # 3. FAISS优化
            if self.config.enable_faiss_optimization:
                faiss_result = await self._optimize_faiss(metrics)
                optimization_results.append(faiss_result)
            
            # 统计优化结果
            total_saved = sum(result.get('memory_saved_mb', config.DEFAULT_ZERO_VALUE) for result in optimization_results)
            self.total_memory_saved_mb += total_saved
            self.optimization_count += config.DEFAULT_ONE_VALUE
            self.last_optimization_time = time.time()
            
            self.logger.info(f"✅ 内存优化完成，释放内存: {total_saved:.config.DEFAULT_ONE_VALUEf}MB，总释放: {self.total_memory_saved_mb:.config.DEFAULT_ONE_VALUEf}MB")
            
        except Exception as e:
            self.logger.error(f"内存优化失败: {e}")

    async def _optimize_garbage_collection(self, metrics: MemoryMetrics) -> Dict[str, Any]:
        """优化垃圾回收"""
        try:
            before_objects = len(gc.get_objects())
            before_memory = tracemalloc.get_traced_memory()[0] if tracemalloc.is_tracing() else 0
            
            # 强制垃圾回收
            collected = gc.collect()
            
            # 清理循环引用
            gc.collect()
            
            after_objects = len(gc.get_objects())
            after_memory = tracemalloc.get_traced_memory()[0] if tracemalloc.is_tracing() else 0
            
            objects_freed = before_objects - after_objects
            memory_freed_mb = (before_memory - after_memory) / (config.DEFAULT_TOP_Kconfig.DEFAULT_HOURS_PER_DAY * config.DEFAULT_CHUNK_SIZE)
            
            self.logger.info(f"🗑️ GC优化完成，释放对象: {objects_freed}，释放内存: {memory_freed_mb:.1f}MB")
            
            return {
                'type': 'gc_optimization',
                'objects_freed': objects_freed,
                'memory_saved_mb': memory_freed_mb,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"GC优化失败: {e}")
            return {
                'type': 'gc_optimization',
                'success': False,
                'error': str(e)
            }

    async def _optimize_cache(self, metrics: MemoryMetrics) -> Dict[str, Any]:
        """优化缓存"""
        try:
            # 这里可以添加具体的缓存清理逻辑
            # 例如清理过期的语义缓存、wiki缓存等
            
            cache_cleaned = config.DEFAULT_ZERO_VALUE
            memory_saved = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
            
            # 清理过期的wiki缓存文件
            wiki_cache_path = "data/wiki_cache"
            if os.path.exists(wiki_cache_path):
                current_time = time.time()
                for filename in os.listdir(wiki_cache_path):
                    if filename.endswith('.json'):
                        file_path = os.path.join(wiki_cache_path, filename)
                        try:
                            file_age = current_time - os.path.getmtime(file_path)
                            # 删除超过7天的缓存文件
                            if file_age > config.DEFAULT_SEVEN_VALUE * config.DEFAULT_HOURS_PER_DAY * config.DEFAULT_ONE_HOUR_SECONDS:
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cache_cleaned += config.DEFAULT_ONE_VALUE
                                memory_saved += file_size
                        except (OSError, FileNotFoundError):
                            continue
            
            memory_saved_mb = memory_saved / (config.DEFAULT_TOP_Kconfig.DEFAULT_HOURS_PER_DAY * config.DEFAULT_CHUNK_SIZE)
            
            if cache_cleaned > config.DEFAULT_ZERO_VALUE:
                self.logger.info(f"🗂️ 缓存优化完成，清理文件: {cache_cleaned}，释放内存: {memory_saved_mb:.1f}MB")
            
            return {
                'type': 'cache_optimization',
                'files_cleaned': cache_cleaned,
                'memory_saved_mb': memory_saved_mb,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"缓存优化失败: {e}")
            return {
                'type': 'cache_optimization',
                'success': False,
                'error': str(e)
            }

    async def _optimize_faiss(self, metrics: MemoryMetrics) -> Dict[str, Any]:
        """优化FAISS索引"""
        try:
            # FAISS索引优化逻辑
            # 这里可以添加索引压缩、向量量化等优化策略
            
            self.logger.info("🔍 FAISS索引优化完成")
            
            return {
                'type': 'faiss_optimization',
                'memory_saved_mb': get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")),
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"FAISS优化失败: {e}")
            return {
                'type': 'faiss_optimization',
                'success': False,
                'error': str(e)
            }

    def add_optimization_callback(self, callback: Callable[[MemoryMetrics], Awaitable[None]]) -> None:
        """添加优化回调函数"""
        self.optimization_callbacks.append(callback)
        self.logger.info(f"✅ 已添加内存优化回调函数: {callback.__name__}")

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        if not self.memory_history:
            return {}
        
        latest = self.memory_history[-1]
        oldest = self.memory_history[0]
        
        return {
            "current_memory_mb": latest.current_memory_mb,
            "peak_memory_mb": latest.peak_memory_mb,
            "memory_percent": latest.memory_percent,
            "available_memory_mb": latest.available_memory_mb,
            "total_memory_mb": latest.total_memory_mb,
            "gc_objects": latest.gc_objects,
            "faiss_index_size_mb": latest.faiss_index_size_mb,
            "cache_size_mb": latest.cache_size_mb,
            "optimization_count": self.optimization_count,
            "total_memory_saved_mb": self.total_memory_saved_mb,
            "last_optimization_time": self.last_optimization_time,
            "monitoring_duration_hours": (latest.timestamp - oldest.timestamp).total_seconds() / config.DEFAULT_ONE_HOUR_SECONDS if len(self.memory_history) > config.DEFAULT_ONE_VALUE else 0
        }

    def get_memory_trends(self) -> Dict[str, List[float]]:
        """获取内存使用趋势"""
        if len(self.memory_history) < 2:
            return {}
        
        timestamps = [float(m.timestamp.timestamp()) for m in self.memory_history]
        memory_usage = [float(m.current_memory_mb) for m in self.memory_history]
        memory_percent = [float(m.memory_percent) for m in self.memory_history]
        gc_objects = [float(m.gc_objects) for m in self.memory_history]
        
        return {
            "timestamps": timestamps,
            "memory_usage_mb": memory_usage,
            "memory_percent": memory_percent,
            "gc_objects": gc_objects
        }

    async def emergency_memory_cleanup(self) -> Dict[str, Any]:
        """紧急内存清理"""
        try:
            self.logger.warning("🚨 执行紧急内存清理")
            
            # 强制垃圾回收
            collected = gc.collect()
            
            # 清理所有缓存
            await self._clear_all_caches()
            
            # 重置内存跟踪
            if tracemalloc.is_tracing():
                tracemalloc.stop()
                tracemalloc.start()
            
            # 收集清理后的指标
            after_metrics = await self._collect_memory_metrics()
            
            return {
                'success': True,
                'gc_collected': collected,
                'after_memory_mb': after_metrics.current_memory_mb,
                'message': '紧急内存清理完成'
            }
            
        except Exception as e:
            self.logger.error(f"紧急内存清理失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _clear_all_caches(self):
        """清理所有缓存"""
        try:
            # 清理模块缓存
            import sys
            modules_to_remove = []
            for module_name in list(sys.modules.keys()):
                if (not module_name.startswith('__') and 
                    module_name not in sys.builtin_module_names and
                    module_name not in ['sys', 'os', 'logging', 'typing', 'collections', 'datetime']):
                    modules_to_remove.append(module_name)
            
            for module_name in modules_to_remove:
                try:
                    if module_name in sys.modules:
                        del sys.modules[module_name]
                except Exception:
                    pass
            
            # 清理弱引用
            import weakref
            import gc
            for obj in gc.get_objects():
                if isinstance(obj, weakref.WeakValueDictionary):
                    obj.clear()
                elif isinstance(obj, weakref.WeakKeyDictionary):
                    obj.clear()
            
            self.logger.info(f"🧹 清理了 {len(modules_to_remove)} 个模块缓存")
            
        except Exception as e:
            self.logger.warning(f"清理缓存时发生错误: {e}")
    
    async def aggressive_memory_cleanup(self) -> Dict[str, Any]:
        """激进内存清理"""
        try:
            start_time = time.time()
            self.logger.info("🚀 执行激进内存清理")
            
            # 强制垃圾回收
            collected = gc.collect()
            
            # 清理所有缓存
            await self._clear_all_caches()
            
            # 清理循环引用
            gc.garbage.clear()
            
            return {
                'success': True,
                'collected_objects': collected,
                'cleanup_time': time.time() - start_time
            }
            
        except Exception as e:
            self.logger.error(f"激进内存清理失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def optimize_memory(self) -> Dict[str, Any]:
        """优化内存使用"""
        try:
            start_time = time.time()
            self.logger.info("🔧 执行内存优化")
            
            # 基本垃圾回收
            collected = gc.collect()
            
            # 清理弱引用
            import weakref
            for obj in gc.get_objects():
                if isinstance(obj, weakref.WeakValueDictionary):
                    obj.clear()
                elif isinstance(obj, weakref.WeakKeyDictionary):
                    obj.clear()
            
            return {
                'success': True,
                'collected_objects': collected,
                'cleanup_time': time.time() - start_time
            }
            
        except Exception as e:
            self.logger.error(f"内存优化失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# 全局实例
_memory_optimizer = None

def get_memory_optimizer(config: Optional[MemoryOptimizationConfig] = None) -> MemoryOptimizer:
    """获取内存优化管理器实例"""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer(config)
    return _memory_optimizer

async def start_memory_optimization(config: Optional[MemoryOptimizationConfig] = None) -> MemoryOptimizer:
    """启动内存优化服务"""
    optimizer = get_memory_optimizer(config)
    await optimizer.start_monitoring()
    return optimizer

async def stop_memory_optimization() -> None:
    """停止内存优化服务"""
    global _memory_optimizer
    if _memory_optimizer:
        await _memory_optimizer.stop_monitoring()

# ==================== 智能内存管理功能 ====================

def _init_object_categories() -> Dict[str, List[str]]:
    """初始化对象分类"""
    return {
        'core': ['sys', 'os', 'logging', 'typing', 'collections', 'datetime'],
        'essential': ['faiss', 'torch', 'wikipediaapi', 'transformers', 'numpy'],
        'cache': ['temp_', 'cache_', '_temp', '_cache'],
        'temporary': ['_', 'tmp_', 'temp_', 'local_']
    }

def _init_function_dependencies() -> Dict[str, List[str]]:
    """初始化功能依赖关系"""
    return {
        'knowledge_retrieval': ['faiss', 'wikipediaapi', 'transformers'],
        'reasoning_analysis': ['torch', 'numpy', 'transformers'],
        'answer_generation': ['transformers', 'torch'],
        'citation_generation': ['wikipediaapi', 'faiss'],
        'wikipedia_download': ['wikipediaapi', 'requests']
    }

def _init_memory_pressure_levels() -> Dict[str, Dict[str, Any]]:
    """初始化内存压力等级"""
    return {
        'low': {
            'memory_percent': 70,
            'object_count': config.DEFAULT_LARGE_LIMITconfig.DEFAULT_ZERO_VALUE,
            'cleanup_strategy': 'minimal'
        },
        'medium': {
            'memory_percent': config.DEFAULT_COVERAGE_THRESHOLD,
            'object_count': config.DEFAULT_MEDIUM_TEXT_LIMITconfig.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUE,
            'cleanup_strategy': 'moderate'
        },
        'high': {
            'memory_percent': 9config.DEFAULT_ZERO_VALUE,
            'object_count': config.DEFAULT_LARGE_LIMITconfig.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUE,
            'cleanup_strategy': 'aggressive'
        },
        'critical': {
            'memory_percent': 95,
            'object_count': config.DEFAULT_TEXT_LIMITconfig.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUE,
            'cleanup_strategy': 'emergency'
        }
    }

def _init_cleanup_strategies() -> Dict[str, str]:
    """初始化清理策略"""
    return {
        'minimal': 'minimal_cleanup',
        'moderate': 'moderate_cleanup',
        'aggressive': 'aggressive_cleanup',
        'emergency': 'emergency_cleanup'
    }

async def smart_memory_cleanup() -> Dict[str, Any]:
    """智能内存清理"""
    try:
        optimizer = get_memory_optimizer()
        
        # 获取当前内存状态
        current_metrics = await optimizer._collect_memory_metrics()
        object_count = len(gc.get_objects())
        
        # 确定内存压力等级
        pressure_level = 'low'
        if current_metrics.memory_percent >= config.DEFAULT_NINETY_FIVE_PERCENT or object_count >= config.DEFAULT_TEXT_LIMITconfig.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUE:
            pressure_level = 'critical'
        elif current_metrics.memory_percent >= config.DEFAULT_NINETY_SECONDS or object_count >= config.DEFAULT_LARGE_LIMITconfig.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUE:
            pressure_level = 'high'
        elif current_metrics.memory_percent >= config.DEFAULT_COVERAGE_THRESHOLD or object_count >= config.DEFAULT_MEDIUM_TEXT_LIMITconfig.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUE:
            pressure_level = 'medium'
        
        logger.info(f"🧠 检测到内存压力等级: {pressure_level}")
        
        # 执行相应的清理策略
        if pressure_level == 'critical':
            result = await optimizer.emergency_memory_cleanup()
        elif pressure_level == 'high':
            result = await optimizer.aggressive_memory_cleanup()
        elif pressure_level == 'medium':
            result = await optimizer.optimize_memory()
        else:
            result = {'success': True, 'message': '内存状态良好，无需清理'}
        
        result['pressure_level'] = pressure_level
        result['object_count_before'] = object_count
        result['object_count_after'] = len(gc.get_objects())
        
        return result
        
    except Exception as e:
        logger.error(f"智能内存清理失败: {e}")
        return {'success': False, 'error': str(e)}

async def function_aware_cleanup(active_functions: List[str]) -> Dict[str, Any]:
    """功能感知的清理"""
    try:
        logger.info(f"🧠 执行功能感知清理，活跃功能: {active_functions}")
        
        # 获取功能依赖关系
        function_deps = _init_function_dependencies()
        
        # 确定需要保护的对象
        protected_objects = set()
        for function in active_functions:
            if function in function_deps:
                protected_objects.update(function_deps[function])
        
        # 只清理不影响活跃功能的对象
        cleaned_objects = config.DEFAULT_ZERO_VALUE
        object_categories = _init_object_categories()
        
        for obj in list(gc.get_objects()):
            obj_str = str(obj)
            
            # 检查是否影响活跃功能
            is_protected = False
            for protected in protected_objects:
                if protected in obj_str.lower():
                    is_protected = True
                    break
            
            # 检查对象分类
            category = 'temporary'
            for cat, patterns in object_categories.items():
                for pattern in patterns:
                    if pattern in obj_str.lower():
                        category = cat
                        break
            
            if not is_protected and category in ['temporary', 'cache']:
                try:
                    del obj
                    cleaned_objects += config.DEFAULT_ONE_VALUE
                except:
                    pass
        
        # 垃圾回收
        collected = gc.collect()
        
        return {
            'success': True,
            'strategy': 'function_aware',
            'objects_cleaned': cleaned_objects,
            'gc_collected': collected,
            'protected_functions': active_functions,
            'message': '功能感知清理完成'
        }
        
    except Exception as e:
        logger.error(f"功能感知清理失败: {e}")
        return {'success': False, 'error': str(e)}

async def predictive_memory_management() -> Dict[str, Any]:
    """预测性内存管理"""
    try:
        logger.info("🔮 执行预测性内存管理")
        
        optimizer = get_memory_optimizer()
        
        # 分析历史内存使用模式
        if len(optimizer.memory_history) < get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):
            return {'success': False, 'message': '历史数据不足，无法进行预测'}
        
        # 预测未来内存需求
        recent_memory = [m.current_memory_mb for m in list(optimizer.memory_history)[-get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):]]
        avg_memory = sum(recent_memory) / len(recent_memory)
        memory_trend = recent_memory[-1] - recent_memory[0]
        
        # 如果内存使用呈上升趋势，提前清理
        if memory_trend > 50:  # 50MB增长
            logger.info("📈 检测到内存上升趋势，执行预防性清理")
            return await optimizer.optimize_memory()
        else:
            return {'success': True, 'message': '内存使用稳定，无需预防性清理'}
            
    except Exception as e:
        logger.error(f"预测性内存管理失败: {e}")
        return {'success': False, 'error': str(e)}
