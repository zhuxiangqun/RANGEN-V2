#!/usr/bin/env python3
"""
统一依赖管理器 - 解决循环导入和依赖管理问题
"""
import logging
import importlib
import asyncio
from typing import Any, Optional, Dict, List, Callable, Type
from functools import lru_cache
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time

logger = logging.getLogger(__name__)

class DependencyStatus(Enum):
    """依赖状态"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    LOADING = "loading"
    ERROR = "error"

@dataclass
class DependencyInfo:
    """依赖信息"""
    name: str
    module_path: str
    item_name: str
    status: DependencyStatus
    fallback: Optional[Any] = None
    error_message: Optional[str] = None
    last_attempt: Optional[datetime] = None
    retry_count: int = config.DEFAULT_ZERO_VALUE
    max_retries: int = 3

class UnifiedDependencyManager:
    """统一依赖管理器"""
    
    def __init__(self):
        self.dependencies: Dict[str, DependencyInfo] = {}
        self.dependency_cache: Dict[str, Any] = {}
        self.dependency_factories: Dict[str, Callable] = {}
        self.circular_dependency_check = True
        self.dependency_graph: Dict[str, List[str]] = {}
        
        # 防重复调用机制
        self._loading_dependencies: set = set()  # 正在加载的依赖
        self._call_count: Dict[str, int] = {}    # 调用次数统计
        self._max_calls_per_dependency = config.DEFAULT_LIMIT     # 每个依赖最大调用次数（增加到config.DEFAULT_LIMIT）
        
        # 缓存管理配置
        self.cache_config = {
            'max_cache_size': config.DEFAULT_TEXT_LIMIT,           # 最大缓存数量（增加到config.DEFAULT_TEXT_LIMIT）
            'cache_ttl': 7config.DEFAULT_TEXT_LIMIT,               # 缓存生存时间（秒，增加到config.DEFAULT_TWO_VALUE小时）
            'cleanup_interval': 3config.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUE,         # 清理间隔（秒）
            'enable_auto_cleanup': True      # 启用自动清理
        }
        
        # 缓存统计
        self.cache_stats = {
            'hits': config.DEFAULT_ZERO_VALUE,
            'misses': config.DEFAULT_ZERO_VALUE,
            'evictions': config.DEFAULT_ZERO_VALUE,
            'last_cleanup': time.time()
        }
        
        # 性能指标
        self.performance_metrics = {
            'dependency_load_times': {},
            'cache_hit_rates': {},
            'error_counts': {},
            'fallback_usage': {}
        }
        
        # 依赖优先级配置
        self.dependency_priorities = {
            'unified_intelligent_center': config.DEFAULT_ONE_VALUE,      # 最高优先级
            'performance_monitor': config.DEFAULT_TWO_VALUE,              # 高优先级
            'unified_config_center': config.DEFAULT_MAX_RETRIES,           # 高优先级
            'security_center': 4,                 # 中高优先级
            'prompt_engine': 5,                   # 中优先级
            'memory_optimizer': 6,                # 中优先级
            'unified_threshold_manager': 7,       # 中低优先级
            'unified_scoring_center': config.DEFAULT_EIGHT_VALUE           # 低优先级
        }
        
        # 回退使用统计
        self.fallback_usage_stats = {}
        
        # 初始化核心依赖
        self._initialize_core_dependencies()
        logger.info("✅ 统一依赖管理器初始化完成")
    
    def _initialize_core_dependencies(self):
        """初始化核心依赖"""
        core_dependencies = {
            'unified_intelligent_center': {
                'module_path': 'src.utils.unified_intelligent_center',
                'item_name': 'get_unified_intelligent_center',
                'fallback': None
            },
            'unified_config_center': {
                'module_path': 'src.utils.unified_config_center',
                'item_name': 'UnifiedConfigCenter',
                'fallback': None
            },
            'unified_threshold_manager': {
                'module_path': 'src.utils.unified_threshold_manager',
                'item_name': 'get_unified_threshold_manager',
                'fallback': None
            },
            'unified_scoring_center': {
                'module_path': 'src.utils.unified_scoring_center',
                'item_name': 'get_unified_intelligent_scorer',
                'fallback': None
            },
            'prompt_engine': {
                'module_path': 'src.utils.prompt_engine',
                'item_name': 'get_unified_prompt_engine',
                'fallback': None
            },
            'memory_optimizer': {
                'module_path': 'src.utils.memory_optimizer',
                'item_name': 'get_memory_optimizer',
                'fallback': None
            },
            'security_center': {
                'module_path': 'src.utils.unified_security_center',
                'item_name': 'get_unified_security_center',
                'fallback': None
            },
            'performance_monitor': {
                'module_path': 'src.utils.performance_monitor',
                'item_name': 'get_performance_monitor',
                'fallback': None
            },
            'unified_answer_center': {
                'module_path': 'src.utils.unified_answer_center',
                'item_name': 'get_unified_answer_center',
                'fallback': None
            },

        }
        
        for name, config in core_dependencies.items():
            self.register_dependency(
                name=name,
                module_path=config['module_path'],
                item_name=config['item_name'],
                fallback=config['fallback']
            )
        
        # 注册智能回退工厂
        self._register_fallback_factories()
    
    def _register_fallback_factories(self):
        """注册智能回退工厂"""
        fallback_factories = {
            'unified_intelligent_center': self._create_intelligent_center_fallback,
            'unified_config_center': self._create_config_center_fallback,
            'prompt_engine': self._create_prompt_engine_fallback,
            'memory_optimizer': self._create_memory_optimizer_fallback,
            'performance_monitor': self._create_performance_monitor_fallback,
            'security_center': self._create_security_center_fallback
        }
        
        for name, factory in fallback_factories.items():
            self.register_factory(name, factory)
    
    def _create_intelligent_center_fallback(self):
        """创建智能中心回退实例 - 使用统一智能中心"""
        try:
            # 直接使用统一智能中心，避免重复定义
            from src.utils.unified_intelligent_center import UnifiedIntelligentCenter
            return UnifiedIntelligentCenter()
        except Exception as e:
            logger.error(f"创建智能中心回退实例失败: {e}")
            return None
    
    def _create_config_center_fallback(self):
        """创建配置中心回退实例 - 使用统一配置中心"""
        try:
            # 直接使用统一配置中心，避免重复定义
            from src.utils.unified_config_center import UnifiedConfigCenter
            return UnifiedConfigCenter()
        except Exception as e:
            logger.error(f"创建配置中心回退实例失败: {e}")
            return None
    
    def _create_prompt_engine_fallback(self):
        """创建提示词引擎回退实例"""
        try:
            class FallbackPromptEngine:
                def __init__(self):
                    self.name = "FallbackPromptEngine"
                    logger.warning("使用提示词引擎回退实例")
                
                def create_answer_framework_prompt(self, query_type: str, content: str) -> str:
                    """回退答案框架提示词生成"""
                    return f"请为{query_type}类型的问题生成答案框架，内容：{content[:config.DEFAULT_LIMIT]}..."
                
                def create_prompt(self, prompt_type: str, **kwargs) -> str:
                    """回退提示词生成"""
                    return f"请根据{prompt_type}类型生成相应的提示词，参数：{kwargs}"
            
            return FallbackPromptEngine()
            
        except Exception as e:
            logger.error(f"创建提示词引擎回退实例失败: {e}")
            return None
    
    def _create_memory_optimizer_fallback(self):
        """创建内存优化器回退实例"""
        try:
            class FallbackMemoryOptimizer:
                def __init__(self):
                    self.name = "FallbackMemoryOptimizer"
                    logger.warning("使用内存优化器回退实例")
                
                def optimize_memory(self):
                    """回退内存优化"""
                    return {'status': 'fallback', 'memory_freed': 0}
                
                def get_memory_usage(self):
                    """获取内存使用情况"""
                    return {'total': 0, 'used': 0, 'free': 0}
                
                def cleanup_cache(self):
                    """清理缓存"""
                    return {'status': 'fallback', 'cleaned': 0}
            
            return FallbackMemoryOptimizer()
            
        except Exception as e:
            logger.error(f"创建内存优化器回退实例失败: {e}")
            return None
    
    def _create_performance_monitor_fallback(self):
        """创建性能监控器回退实例"""
        try:
            class FallbackPerformanceMonitor:
                def __init__(self):
                    self.name = "FallbackPerformanceMonitor"
                    logger.warning("使用性能监控器回退实例")
                
                def record_metric(self, name: str, value: float, metric_type=None):
                    """记录指标"""
                    pass
                
                def get_metrics(self):
                    """获取指标"""
                    return {}
                
                def start_monitoring(self):
                    """开始监控"""
                    pass
                
                def stop_monitoring(self):
                    """停止监控"""
                    pass
            
            return FallbackPerformanceMonitor()
            
        except Exception as e:
            logger.error(f"创建性能监控器回退实例失败: {e}")
            return None
    
    def _create_security_center_fallback(self):
        """创建安全中心回退实例"""
        try:
            class FallbackSecurityCenter:
                def __init__(self):
                    self.name = "FallbackSecurityCenter"
                    logger.warning("使用安全中心回退实例")
                
                def check_security(self, content: str):
                    """安全检查"""
                    return {'secure': True, 'method': 'fallback'}
                
                def audit_log(self, action: str, details: str):
                    """审计日志"""
                    pass
            
            return FallbackSecurityCenter()
            
        except Exception as e:
            logger.error(f"创建安全中心回退实例失败: {e}")
            return None
    
    def register_dependency(self, name: str, module_path: str, item_name: str, 
                           fallback: Optional[Any] = None, dependencies: Optional[List[str]] = None):
        """注册依赖"""
        try:
            dependency_info = DependencyInfo(
                name=name,
                module_path=module_path,
                item_name=item_name,
                status=DependencyStatus.UNAVAILABLE,
                fallback=fallback
            )
            
            self.dependencies[name] = dependency_info
            
            if dependencies:
                self.dependency_graph[name] = dependencies
                # 检查循环依赖
                if self.circular_dependency_check and self._has_circular_dependency(name):
                    logger.warning(f"⚠️ 检测到循环依赖: {name}")
            
            logger.info(f"✅ 依赖 {name} 注册成功")
            
        except Exception as e:
            logger.error(f"注册依赖 {name} 失败: {e}")
    
    def register_factory(self, name: str, factory_func: Callable):
        """注册依赖工厂函数"""
        try:
            self.dependency_factories[name] = factory_func
            logger.info(f"✅ 依赖工厂 {name} 注册成功")
        except Exception as e:
            logger.error(f"注册依赖工厂 {name} 失败: {e}")
    
    def _get_cache_key(self, name: str) -> str:
        """生成缓存键"""
        return f"dep_{name}"
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """检查缓存是否有效"""
        if 'timestamp' not in cache_entry:
            return False
        
        current_time = time.time()
        return (current_time - cache_entry['timestamp']) < self.cache_config['cache_ttl']
    
    def _add_to_cache(self, name: str, instance: Any):
        """添加到缓存"""
        try:
            cache_key = self._get_cache_key(name)
            
            # 检查缓存大小限制
            if len(self.dependency_cache) >= self.cache_config['max_cache_size']:
                self._cleanup_cache()
            
            # 添加到缓存
            self.dependency_cache[cache_key] = {
                'instance': instance,
                'timestamp': time.time(),
                'access_count': config.DEFAULT_ZERO_VALUE
            }
            
            logger.debug(f"依赖 {name} 已添加到缓存")
            
        except Exception as e:
            logger.debug(f"添加依赖 {name} 到缓存失败: {e}")
    
    def _get_from_cache(self, name: str) -> Optional[Any]:
        """从缓存获取"""
        try:
            cache_key = self._get_cache_key(name)
            
            if cache_key in self.dependency_cache:
                cache_entry = self.dependency_cache[cache_key]
                
                # 检查缓存有效性
                if self._is_cache_valid(cache_entry):
                    # 更新访问统计
                    cache_entry['access_count'] += config.DEFAULT_ONE_VALUE
                    self.cache_stats['hits'] += config.DEFAULT_ONE_VALUE
                    
                    logger.debug(f"从缓存获取依赖: {name}")
                    return cache_entry['instance']
                else:
                    # 缓存过期，移除
                    del self.dependency_cache[cache_key]
                    logger.debug(f"依赖 {name} 缓存已过期，已移除")
            
            self.cache_stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.debug(f"从缓存获取依赖 {name} 失败: {e}")
            return None
    
    def _cleanup_cache(self):
        """清理缓存"""
        try:
            current_time = time.time()
            expired_keys = []
            
            # 找出过期的缓存项
            for key, entry in self.dependency_cache.items():
                if not self._is_cache_valid(entry):
                    expired_keys.append(key)
            
            # 移除过期的缓存项
            for key in expired_keys:
                del self.dependency_cache[key]
                self.cache_stats['evictions'] += config.DEFAULT_ONE_VALUE
            
            # 如果缓存仍然过大，移除最少访问的项
            if len(self.dependency_cache) > self.cache_config['max_cache_size']:
                # 按访问次数排序，移除最少访问的项
                sorted_items = sorted(
                    self.dependency_cache.items(),
                    key=lambda x: x[config.DEFAULT_ONE_VALUE]['access_count']
                )
                
                items_to_remove = len(sorted_items) - self.cache_config['max_cache_size']
                for i in range(items_to_remove):
                    key = sorted_items[i][0]
                    del self.dependency_cache[key]
                    self.cache_stats['evictions'] += config.DEFAULT_ONE_VALUE
            
            self.cache_stats['last_cleanup'] = current_time
            
            if expired_keys or len(self.dependency_cache) > self.cache_config['max_cache_size']:
                logger.info(f"缓存清理完成，移除了 {len(expired_keys)} 个过期项")
                
        except Exception as e:
            logger.error(f"缓存清理失败: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            hit_rate = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
            if self.cache_stats['hits'] + self.cache_stats['misses'] > config.DEFAULT_ZERO_VALUE:
                hit_rate = self.cache_stats['hits'] / (self.cache_stats['hits'] + self.cache_stats['misses']) * get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))
            
            return {
                'cache_size': len(self.dependency_cache),
                'max_cache_size': self.cache_config['max_cache_size'],
                'hits': self.cache_stats['hits'],
                'misses': self.cache_stats['misses'],
                'hit_rate': f"{hit_rate:.config.DEFAULT_ONE_VALUEf}%",
                'evictions': self.cache_stats['evictions'],
                'last_cleanup': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.cache_stats['last_cleanup']))
            }
            
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {}
    
    def clear_cache(self):
        """清除缓存"""
        try:
            old_size = len(self.dependency_cache)
            self.dependency_cache.clear()
            
            # 重置缓存统计
            self.cache_stats['hits'] = config.DEFAULT_ZERO_VALUE
            self.cache_stats['misses'] = config.DEFAULT_ZERO_VALUE
            self.cache_stats['evictions'] = config.DEFAULT_ZERO_VALUE
            self.cache_stats['last_cleanup'] = time.time()
            
            logger.info(f"✅ 依赖缓存已清除，释放了 {old_size} 个缓存项")
            
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
    
    def _get_dependency_priority(self, name: str) -> int:
        """获取依赖优先级"""
        return self.dependency_priorities.get(name, 999)  # 默认最低优先级
    
    def _sort_dependencies_by_priority(self, dependency_names: List[str]) -> List[str]:
        """按优先级排序依赖"""
        return sorted(dependency_names, key=lambda x: self._get_dependency_priority(x))
    
    def _record_fallback_usage(self, dependency_name: str, fallback_type: str):
        """记录回退使用情况"""
        if dependency_name not in self.fallback_usage_stats:
            self.fallback_usage_stats[dependency_name] = {
                'total_attempts': config.DEFAULT_ZERO_VALUE,
                'fallback_usage': config.DEFAULT_ZERO_VALUE,
                'fallback_types': {},
                'last_fallback': None,
                'error_history': []
            }
        
        stats = self.fallback_usage_stats[dependency_name]
        stats['total_attempts'] += config.DEFAULT_ONE_VALUE
        stats['fallback_usage'] += config.DEFAULT_ONE_VALUE
        stats['last_fallback'] = time.time()
        
        if fallback_type not in stats['fallback_types']:
            stats['fallback_types'][fallback_type] = config.DEFAULT_ZERO_VALUE
        stats['fallback_types'][fallback_type] += config.DEFAULT_ONE_VALUE
        
        logger.info(f"📊 依赖 {dependency_name} 使用回退机制: {fallback_type}")
    
    def _record_dependency_error(self, dependency_name: str, error: Exception, error_type: str):
        """记录依赖错误"""
        if dependency_name not in self.fallback_usage_stats:
            self.fallback_usage_stats[dependency_name] = {
                'total_attempts': config.DEFAULT_ZERO_VALUE,
                'fallback_usage': config.DEFAULT_ZERO_VALUE,
                'fallback_types': {},
                'last_fallback': None,
                'error_history': []
            }
        
        stats = self.fallback_usage_stats[dependency_name]
        stats['total_attempts'] += config.DEFAULT_ONE_VALUE
        
        error_info = {
            'timestamp': time.time(),
            'error_type': error_type,
            'error_message': str(error),
            'error_class': type(error).__name__
        }
        stats['error_history'].append(error_info)
        
        # 保持错误历史在合理范围内
        if len(stats['error_history']) > 20:
            stats['error_history'] = stats['error_history'][-get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):]
        
        logger.warning(f"⚠️ 依赖 {dependency_name} 发生错误: {error_type} - {error}")
    
    def get_dependency(self, name: str) -> Optional[Any]:
        """获取依赖实例 - 智能优先级策略"""
        start_time = time.time()
        
        try:
            # 防重复调用检查
            if name in self._loading_dependencies:
                logger.warning(f"⚠️ 依赖 {name} 正在加载中，跳过重复调用")
                return None
            
            # 先检查缓存 - 缓存命中不增加调用计数
            cached_instance = self._get_from_cache(name)
            if cached_instance is not None:
                logger.debug(f"✅ 依赖 {name} 从缓存获取成功")
                return cached_instance
            
            # 只有缓存未命中时才检查调用次数限制
            call_count = self._call_count.get(name, config.DEFAULT_ZERO_VALUE)
            if call_count >= self._max_calls_per_dependency:
                logger.warning(f"⚠️ 依赖 {name} 调用次数超过限制 ({call_count}/{self._max_calls_per_dependency})，跳过")
                return None
            
            # 增加调用计数（只有缓存未命中时才计数）
            self._call_count[name] = call_count + config.DEFAULT_ONE_VALUE
            
            # 标记为正在加载
            self._loading_dependencies.add(name)
            
            # 记录缓存未命中
            self._record_performance_metric('cache_hit_rates', config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE, name)
            
            # 按优先级尝试不同的获取策略
            instance = self._try_get_dependency_with_priority(name)
            
            if instance:
                # 添加到缓存
                self._add_to_cache(name, instance)
                
                # 记录性能指标
                load_time = time.time() - start_time
                self._record_performance_metric('dependency_load_times', load_time, f"{name}_priority")
                
                logger.info(f"✅ 依赖 {name} 通过优先级策略获取成功")
                return instance
            
            # 检查是否应该使用回退机制
            if self._should_use_fallback(name):
                fallback_instance = self._create_smart_fallback(name)
                if fallback_instance:
                    self._add_to_cache(name, fallback_instance)
                    logger.debug(f"⚠️ 依赖 {name} 使用回退机制")
                    return fallback_instance
            
            logger.warning(f"⚠️ 依赖 {name} 所有获取策略都失败")
            return None
            
        except Exception as e:
            logger.error(f"获取依赖 {name} 时发生错误: {e}")
            self._record_dependency_error(name, e, 'critical_error')
            return None
        finally:
            # 清理加载状态
            self._loading_dependencies.discard(name)
            
            # 记录总加载时间
            total_time = time.time() - start_time
            self._record_performance_metric('dependency_load_times', total_time, f"{name}_total")
    
    def _try_get_dependency_with_priority(self, name: str) -> Optional[Any]:
        """按优先级尝试获取依赖"""
        # 策略1: 工厂函数（最高优先级）
        if name in self.dependency_factories:
            try:
                logger.debug(f"🎯 策略config.DEFAULT_ONE_VALUE: 使用工厂函数获取依赖 {name}")
                instance = self.dependency_factories[name]()
                if instance:
                    logger.info(f"✅ 工厂函数成功创建依赖 {name}")
                    return instance
                else:
                    logger.warning(f"⚠️ 工厂函数返回None: {name}")
                    self._record_fallback_usage(name, 'factory_returned_none')
            except Exception as e:
                logger.warning(f"⚠️ 工厂函数执行失败: {name} - {e}")
                self._record_dependency_error(name, e, 'factory_error')
        
        # 策略config.DEFAULT_TWO_VALUE: 直接导入（高优先级）
        if name in self.dependencies:
            try:
                logger.debug(f"🎯 策略config.DEFAULT_TWO_VALUE: 尝试直接导入依赖 {name}")
                instance = self._try_direct_import(name)
                if instance:
                    logger.info(f"✅ 直接导入成功: {name}")
                    return instance
            except Exception as e:
                logger.warning(f"⚠️ 直接导入失败: {name} - {e}")
                self._record_dependency_error(name, e, 'import_error')
        
        # 策略3: 统一依赖管理器（中优先级）- 移除循环导入
        # 注意：这里移除了循环导入，避免无限递归
        logger.debug(f"🎯 策略3: 跳过统一依赖管理器获取 {name}（避免循环导入）")
        
        # 策略4: 智能回退（最低优先级）
        try:
            logger.debug(f"🎯 策略4: 使用智能回退机制 {name}")
            fallback_instance = self._create_smart_fallback(name)
            if fallback_instance:
                logger.info(f"✅ 智能回退成功: {name}")
                self._record_fallback_usage(name, 'smart_fallback')
                return fallback_instance
        except Exception as e:
            logger.warning(f"⚠️ 智能回退失败: {name} - {e}")
            self._record_dependency_error(name, e, 'fallback_error')
        
        return None
    
    def _try_direct_import(self, name: str) -> Optional[Any]:
        """尝试直接导入依赖"""
        if name not in self.dependencies:
            return None
        
        dependency_info = self.dependencies[name]
        
        try:
            dependency_info.status = DependencyStatus.LOADING
            dependency_info.last_attempt = datetime.now()
            
            # 处理导入路径
            try:
                # 首先尝试直接导入
                module = importlib.import_module(dependency_info.module_path)
            except ImportError:
                # 如果失败，尝试添加src前缀
                try:
                    src_path = f"src.{dependency_info.module_path}"
                    module = importlib.import_module(src_path)
                except ImportError:
                    # 如果还是失败，尝试从当前包导入
                    try:
                        current_package = __name__.split('.')[0]
                        full_path = f"{current_package}.{dependency_info.module_path}"
                        module = importlib.import_module(full_path)
                    except ImportError as e:
                        raise ImportError(f"无法导入模块 {dependency_info.module_path}: {e}")
            
            item = getattr(module, dependency_info.item_name)
            
            if callable(item):
                instance = item()
            else:
                instance = item
            
            dependency_info.status = DependencyStatus.AVAILABLE
            dependency_info.retry_count = 0
            
            return instance
            
        except Exception as e:
            dependency_info.status = DependencyStatus.ERROR
            dependency_info.error_message = str(e)
            dependency_info.retry_count += config.DEFAULT_ONE_VALUE
            raise e
    
    def _should_use_fallback(self, name: str) -> bool:
        """检查是否应该使用回退机制"""
        try:
            # 检查调用次数，如果调用次数过多，减少回退机制的使用
            call_count = self._call_count.get(name, config.DEFAULT_ZERO_VALUE)
            if call_count > self._max_calls_per_dependency * config.DEFAULT_HIGH_THRESHOLD:  # 80%阈值
                logger.debug(f"依赖 {name} 调用次数过多，减少回退机制使用")
                return False
            
            # 检查错误历史，如果错误过多，减少回退机制的使用
            if name in self.dependencies:
                dependency_info = self.dependencies[name]
                # 使用retry_count作为错误指标
                if dependency_info.retry_count > 3:  # 重试次数阈值
                    logger.debug(f"依赖 {name} 重试次数过多，减少回退机制使用")
                    return False
            
            # 对于关键依赖，优先使用回退机制
            critical_dependencies = [
                'unified_config_center', 'unified_intelligent_center', 
                'faiss_service', 'performance_monitor'
            ]
            if name in critical_dependencies:
                return True
            
            # 对于非关键依赖，减少回退机制的使用
            return False
            
        except Exception as e:
            logger.debug(f"检查回退机制使用条件失败: {e}")
            return False

    def _create_smart_fallback(self, name: str) -> Optional[Any]:
        """创建智能回退实例"""
        fallback_creators = {
            'unified_intelligent_center': self._create_intelligent_center_fallback,
            'unified_config_center': self._create_config_center_fallback,
            'prompt_engine': self._create_prompt_engine_fallback,
            'memory_optimizer': self._create_memory_optimizer_fallback,
            'performance_monitor': self._create_performance_monitor_fallback,
            'security_center': self._create_security_center_fallback,
            'intelligent_value_manager': self._create_intelligent_value_manager_fallback,
            'ml_rule_generator': self._create_ml_rule_generator_fallback,
            'unified_config_manager': self._create_config_center_fallback,  # 使用config_center作为回退
            'intelligent_strategy_fusion': self._create_strategy_fusion_fallback,
            'feature_extractor': self._create_feature_extractor_fallback,
            'learning_optimizer': self._create_learning_optimizer_fallback,
            'zero_hardcode_rule_engine': self._create_zero_hardcode_fallback,

        }
        
        if name in fallback_creators:
            try:
                return fallback_creators[name]()
            except Exception as e:
                logger.error(f"创建回退实例失败: {name} - {e}")
                return None
        
        # 通用回退实例
        return self._create_generic_fallback(name)
    
    def _create_generic_fallback(self, name: str) -> Optional[Any]:
        """创建通用回退实例"""
        try:
            class GenericFallback:
                def __init__(self, dep_name: str):
                    self.name = f"GenericFallback_{dep_name}"
                    self.dependency_name = dep_name
                    logger.warning(f"使用通用回退实例: {dep_name}")
                
                def __getattr__(self, attr):
                    """处理未知属性访问"""
                    logger.debug(f"通用回退实例 {self.dependency_name} 访问未知属性: {attr}")
                    return lambda *args, **kwargs: None
                
                def __call__(self, *args, **kwargs):
                    """处理未知方法调用"""
                    logger.debug(f"通用回退实例 {self.dependency_name} 调用未知方法: {args}, {kwargs}")
                    return None
            
            return GenericFallback(name)
            
        except Exception as e:
            logger.error(f"创建通用回退实例失败: {name} - {e}")
            return None
    
    def _record_performance_metric(self, metric_name: str, value: float, operation: str = ""):
        """记录性能指标"""
        try:
            if metric_name not in self.performance_metrics:
                self.performance_metrics[metric_name] = {}
            
            if operation not in self.performance_metrics[metric_name]:
                self.performance_metrics[metric_name][operation] = []
            
            self.performance_metrics[metric_name][operation].append({
                'value': value,
                'timestamp': time.time()
            })
            
            # 保持指标数量在合理范围内
            if len(self.performance_metrics[metric_name][operation]) > get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")):
                self.performance_metrics[metric_name][operation] = self.performance_metrics[metric_name][operation][-50:]
                
        except Exception as e:
            logger.debug(f"记录性能指标失败: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        try:
            summary = {}
            
            # 计算平均加载时间
            for metric_name, operations in self.performance_metrics.items():
                summary[metric_name] = {}
                for operation, values in operations.items():
                    if values:
                        if metric_name == 'dependency_load_times':
                            # 计算平均加载时间
                            avg_time = sum(v['value'] for v in values) / len(values)
                            summary[metric_name][operation] = f"{avg_time:.4f}s"
                        elif metric_name == 'cache_hit_rates':
                            # 计算缓存命中率
                            hit_rate = sum(v['value'] for v in values) / len(values) * get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))
                            summary[metric_name][operation] = f"{hit_rate:.1f}%"
                        elif metric_name == 'error_counts':
                            # 计算错误总数
                            total_errors = sum(v['value'] for v in values)
                            summary[metric_name][operation] = total_errors
                        elif metric_name == 'fallback_usage':
                            # 计算回退使用次数
                            fallback_count = sum(v['value'] for v in values)
                            summary[metric_name][operation] = fallback_count
            
            return summary
            
        except Exception as e:
            logger.error(f"获取性能摘要失败: {e}")
            return {}
    
    def get_fallback_summary(self) -> Dict[str, Any]:
        """获取回退使用摘要"""
        try:
            summary = {}
            
            for dep_name, stats in self.fallback_usage_stats.items():
                summary[dep_name] = {
                    'total_attempts': stats['total_attempts'],
                    'fallback_usage': stats['fallback_usage'],
                    'fallback_rate': f"{(stats['fallback_usage'] / stats['total_attempts'] * config.DEFAULT_LIMIT):.config.DEFAULT_ONE_VALUEf}%" if stats['total_attempts'] > config.DEFAULT_ZERO_VALUE else "config.DEFAULT_ZERO_VALUE%",
                    'fallback_types': stats['fallback_types'],
                    'last_fallback': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats['last_fallback'])) if stats['last_fallback'] else 'Never',
                    'error_count': len(stats['error_history'])
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"获取回退摘要失败: {e}")
            return {}
    
    async def get_dependency_async(self, name: str) -> Optional[Any]:
        """异步获取依赖实例"""
        try:
            # 在事件循环中运行同步操作
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.get_dependency, name)
        except Exception as e:
            logger.error(f"异步获取依赖 {name} 失败: {e}")
            return None
    
    def safe_import(self, module_path: str, item_name: str, fallback: Any = None) -> Any:
        """安全导入模块或类"""
        try:
            module = importlib.import_module(module_path)
            item = getattr(module, item_name, fallback)
            return item
        except ImportError as e:
            logger.warning(f"导入 {module_path}.{item_name} 失败: {e}")
            return fallback
        except Exception as e:
            logger.error(f"导入 {module_path}.{item_name} 时发生错误: {e}")
            return fallback
    
    def lazy_import(self, module_path: str, item_name: str, fallback: Any = None):
        """延迟导入"""
        def import_and_call(*args, **kwargs):
            item = self.safe_import(module_path, item_name, fallback)
            if callable(item):
                return item(*args, **kwargs)
            else:
                logger.warning(f"{item_name} 不是可调用的")
                return fallback
        return import_and_call
    
    def _has_circular_dependency(self, dependency_name: str) -> bool:
        """检查是否有循环依赖"""
        try:
            visited = set()
            rec_stack = set()
            
            def dfs(node: str) -> bool:
                if node in rec_stack:
                    return True
                if node in visited:
                    return False
                
                visited.add(node)
                rec_stack.add(node)
                
                for neighbor in self.dependency_graph.get(node, []):
                    if dfs(neighbor):
                        return True
                
                rec_stack.remove(node)
                return False
            
            return dfs(dependency_name)
            
        except Exception as e:
            logger.error(f"检查循环依赖失败: {e}")
            return False
    
    def resolve_dependencies(self, dependency_names: List[str]) -> List[Any]:
        """解析多个依赖"""
        resolved = []
        for name in dependency_names:
            instance = self.get_dependency(name)
            if instance:
                resolved.append(instance)
            else:
                logger.warning(f"依赖 {name} 无法解析")
        return resolved
    
    def get_dependency_status(self, name: str) -> Optional[DependencyStatus]:
        """获取依赖状态"""
        if name in self.dependencies:
            return self.dependencies[name].status
        return None
    
    def get_dependency_info(self, name: str) -> Optional[DependencyInfo]:
        """获取依赖信息"""
        return self.dependencies.get(name)
    
    def get_dependency_summary(self) -> Dict[str, Any]:
        """获取依赖摘要"""
        summary = {
            'total_dependencies': len(self.dependencies),
            'available_dependencies': 0,
            'unavailable_dependencies': 0,
            'error_dependencies': 0,
            'loading_dependencies': 0,
            'cached_dependencies': len(self.dependency_cache),
            'factory_dependencies': len(self.dependency_factories)
        }
        
        for dep_info in self.dependencies.values():
            if dep_info.status == DependencyStatus.AVAILABLE:
                summary['available_dependencies'] += 1
            elif dep_info.status == DependencyStatus.UNAVAILABLE:
                summary['unavailable_dependencies'] += 1
            elif dep_info.status == DependencyStatus.ERROR:
                summary['error_dependencies'] += 1
            elif dep_info.status == DependencyStatus.LOADING:
                summary['loading_dependencies'] += 1
        
        return summary

    def _create_intelligent_value_manager_fallback(self) -> Any:
        """创建智能值管理器回退实例"""
        class IntelligentValueManagerFallback:
            def __init__(self):
                self.name = "IntelligentValueManagerFallback"
            
            def get_value(self, key: str, default: Any = None) -> Any:
                return default
            
            def set_value(self, key: str, value: Any) -> None:
                pass
        
        return IntelligentValueManagerFallback()

    def _create_ml_rule_generator_fallback(self) -> Any:
        """创建ML规则生成器回退实例"""
        class MLRuleGeneratorFallback:
            def __init__(self):
                self.name = "MLRuleGeneratorFallback"
            
            def generate_rule(self, *args, **kwargs) -> str:
                return "default_rule"
        
        return MLRuleGeneratorFallback()

    def _create_strategy_fusion_fallback(self) -> Any:
        """创建策略融合回退实例"""
        class StrategyFusionFallback:
            def __init__(self):
                self.name = "StrategyFusionFallback"
            
            def fuse_strategies(self, *args, **kwargs) -> Any:
                return None
        
        return StrategyFusionFallback()

    def _create_feature_extractor_fallback(self) -> Any:
        """创建特征提取器回退实例"""
        class FeatureExtractorFallback:
            def __init__(self):
                self.name = "FeatureExtractorFallback"
            
            def extract_features(self, *args, **kwargs) -> Any:
                return {}
        
        return FeatureExtractorFallback()

    def _create_learning_optimizer_fallback(self) -> Any:
        """创建学习优化器回退实例"""
        class LearningOptimizerFallback:
            def __init__(self):
                self.name = "LearningOptimizerFallback"
            
            def optimize(self, *args, **kwargs) -> Any:
                return None
        
        return LearningOptimizerFallback()

    def _create_zero_hardcode_fallback(self) -> Any:
        """创建零硬编码规则引擎回退实例"""
        class ZeroHardcodeRuleEngineFallback:
            def __init__(self):
                self.name = "ZeroHardcodeRuleEngineFallback"
            
            def process_rule(self, *args, **kwargs) -> Any:
                return None
        
        return ZeroHardcodeRuleEngineFallback()



# 全局依赖管理器实例
_unified_dependency_manager = None

def get_unified_dependency_manager() -> UnifiedDependencyManager:
    """获取统一依赖管理器实例"""
    global _unified_dependency_manager
    if _unified_dependency_manager is None:
        _unified_dependency_manager = UnifiedDependencyManager()
    return _unified_dependency_manager

# 便捷函数
def get_dependency(name: str) -> Optional[Any]:
    """获取依赖的便捷函数"""
    return get_unified_dependency_manager().get_dependency(name)

def safe_import(module_path: str, item_name: str, fallback: Any = None) -> Any:
    """安全导入的便捷函数"""
    return get_unified_dependency_manager().safe_import(module_path, item_name, fallback)

def lazy_import(module_path: str, item_name: str, fallback: Any = None):
    """延迟导入的便捷函数"""
    return get_unified_dependency_manager().lazy_import(module_path, item_name, fallback)
