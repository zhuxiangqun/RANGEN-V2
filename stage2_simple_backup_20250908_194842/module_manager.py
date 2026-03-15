#!/usr/bin/env python3
"""
模块管理器 - 优化模块的加载、缓存和清理
"""

import gc
import sys
import threading
import time
import logging
from typing import Dict, Set, List, Optional, Any, Callable
from collections import defaultdict, deque
import weakref
import importlib

# 智能配置系统导入
from src.utils.smart_config_system import get_smart_config, create_query_context

logger = logging.getLogger(__name__)

class ModuleInfo:
    """模块信息"""
    
    def __init__(self, name: str, module: Any):
        self.name = name
        self.module = module
        self.load_time = time.time()
        self.last_access_time = time.time()
        self.access_count = 0
        self.size_estimate = 0
        self.dependencies: Set[str] = set()
        self.dependents: Set[str] = set()
    
    def access(self):
        """记录访问"""
        self.last_access_time = time.time()
        self.access_count += 1
    
    def get_age(self) -> float:
        """获取模块年龄（秒）"""
        return time.time() - self.load_time
    
    def get_idle_time(self) -> float:
        """获取空闲时间（秒）"""
        return time.time() - self.last_access_time

class ModuleManager:
    """模块管理器"""
    
    def __init__(self, 
                 max_modules: int = config.DEFAULT_TEXT_LIMIT,
                 max_idle_time: float = config.DEFAULT_TIMEOUT0.0,  # 5分钟
                 cleanup_interval: float = 60.0):  # 1分钟
        self.max_modules = max_modules
        self.max_idle_time = max_idle_time
        self.cleanup_interval = cleanup_interval
        
        self._modules: Dict[str, ModuleInfo] = {}
        self._lock = threading.RLock()
        self._cleanup_thread = None
        self._running = False
        
        # 统计信息
        self._stats: Dict[str, Any] = {
            'total_loaded': 0,
            'total_unloaded': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # 启动清理线程
        self.start_cleanup_thread()
        
        logger.info(f"✅ 模块管理器初始化完成: 最大模块数={max_modules}, 最大空闲时间={max_idle_time}秒")
    
    def load_module(self, module_name: str, force_reload: bool = False) -> Any:
        """加载模块"""
        with self._lock:
            # 检查是否已加载
            if module_name in self._modules and not force_reload:
                module_info = self._modules[module_name]
                module_info.access()
                self._stats['cache_hits'] += 1
                logger.debug(f"📦 模块缓存命中: {module_name}")
                return module_info.module
            
            # 加载模块
            start_time = time.time()
            try:
                if force_reload and module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                    module = sys.modules[module_name]
                else:
                    module = importlib.import_module(module_name)
                
                load_time = time.time() - start_time
                
                # 创建模块信息
                module_info = ModuleInfo(module_name, module)
                module_info.size_estimate = self._estimate_module_size(module)
                
                # 分析依赖关系
                self._analyze_dependencies(module_info)
                
                # 添加到缓存
                self._modules[module_name] = module_info
                self._stats['total_loaded'] += 1
                self._stats['cache_misses'] += 1
                
                # 检查是否需要清理
                self._check_and_cleanup()
                
                logger.info(f"📦 模块加载完成: {module_name}, 耗时: {load_time:.3f}秒, 大小: {module_info.size_estimate}字节")
                return module
                
            except Exception as e:
                logger.error(f"❌ 模块加载失败: {module_name}, 错误: {e}")
                raise
    
    def unload_module(self, module_name: str, force: bool = False) -> bool:
        """卸载模块"""
        with self._lock:
            if module_name not in self._modules:
                logger.warning(f"⚠️ 模块未加载: {module_name}")
                return False
            
            module_info = self._modules[module_name]
            
            # 检查依赖关系
            if not force and module_info.dependents:
                logger.warning(f"⚠️ 模块有依赖者，无法卸载: {module_name}, 依赖者: {module_info.dependents}")
                return False
            
            try:
                # 从sys.modules中移除
                if module_name in sys.modules:
                    del sys.modules[module_name]
                
                # 从缓存中移除
                del self._modules[module_name]
                self._stats['total_unloaded'] += 1
                
                # 更新依赖关系
                for dep_name in module_info.dependencies:
                    if dep_name in self._modules:
                        self._modules[dep_name].dependents.discard(module_name)
                
                logger.info(f"🗑️ 模块卸载完成: {module_name}")
                return True
                
            except Exception as e:
                logger.error(f"❌ 模块卸载失败: {module_name}, 错误: {e}")
                return False
    
    def get_module(self, module_name: str) -> Optional[Any]:
        """获取模块"""
        with self._lock:
            if module_name in self._modules:
                module_info = self._modules[module_name]
                module_info.access()
                return module_info.module
            return None
    
    def is_loaded(self, module_name: str) -> bool:
        """检查模块是否已加载"""
        with self._lock:
            return module_name in self._modules
    
    def get_loaded_modules(self) -> List[str]:
        """获取已加载的模块列表"""
        with self._lock:
            return list(self._modules.keys())
    
    def _estimate_module_size(self, module: Any) -> int:
        """估算模块大小"""
        try:
            size = 0
            for attr_name in dir(module):
                try:
                    attr = getattr(module, attr_name)
                    size += sys.getsizeof(attr)
                except:
                    pass
            return size
        except:
            return 0
    
    def _analyze_dependencies(self, module_info: ModuleInfo):
        """分析模块依赖关系"""
        try:
            module = module_info.module
            if hasattr(module, '__file__') and module.__file__:
                # 这里可以实现更复杂的依赖分析
                # 目前只是简单的占位符
                pass
        except Exception as e:
            logger.debug(f"依赖分析失败: {module_info.name}, 错误: {e}")
    
    def _check_and_cleanup(self):
        """检查并清理模块"""
        if len(self._modules) <= self.max_modules:
            return
        
        # 按空闲时间排序，优先清理空闲时间长的模块
        modules_to_cleanup = []
        for name, info in self._modules.items():
            if info.get_idle_time() > self.max_idle_time:
                modules_to_cleanup.append((name, info))
        
        # 按空闲时间降序排序
        modules_to_cleanup.sort(key=lambda x: x[1].get_idle_time(), reverse=True)
        
        # 清理多余的模块
        cleanup_count = len(self._modules) - self.max_modules + config.DEFAULT_TOP_K  # 多清理10个
        for name, info in modules_to_cleanup[:cleanup_count]:
            if not info.dependents:  # 只清理没有依赖者的模块
                self.unload_module(name)
    
    def cleanup_idle_modules(self):
        """清理空闲模块"""
        with self._lock:
            idle_modules = []
            for name, info in self._modules.items():
                if info.get_idle_time() > self.max_idle_time and not info.dependents:
                    idle_modules.append(name)
            
            for name in idle_modules:
                self.unload_module(name)
            
            if idle_modules:
                logger.info(f"🧹 清理了 {len(idle_modules)} 个空闲模块")
    
    def cleanup_all_modules(self):
        """清理所有模块"""
        with self._lock:
            module_names = list(self._modules.keys())
            for name in module_names:
                self.unload_module(name, force=True)
            logger.info("🧹 所有模块清理完成")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            stats = self._stats.copy()
            stats['current_modules'] = len(self._modules)
            stats['max_modules'] = self.max_modules
            stats['cache_hit_rate'] = self._stats['cache_hits'] / max(1, self._stats['cache_hits'] + self._stats['cache_misses'])
            
            # 添加模块详细信息
            module_details = {}
            for name, info in self._modules.items():
                module_details[name] = {
                    'age': info.get_age(),
                    'idle_time': info.get_idle_time(),
                    'access_count': info.access_count,
                    'size_estimate': info.size_estimate,
                    'dependencies': len(info.dependencies),
                    'dependents': len(info.dependents)
                }
            
            stats['module_details'] = module_details
            return stats
    
    def start_cleanup_thread(self):
        """启动清理线程"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return
        
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        logger.info("🚀 模块清理线程启动")
    
    def stop_cleanup_thread(self):
        """停止清理线程"""
        self._running = False
        if self._cleanup_thread:
            cleanup_timeout = get_smart_config("cleanup_timeout", create_query_context(query_type="module_cleanup"))
            self._cleanup_thread.join(timeout=cleanup_timeout)
        logger.info("🛑 模块清理线程停止")
    
    def _cleanup_worker(self):
        """清理工作线程"""
        while self._running:
            try:
                time.sleep(self.cleanup_interval)
                self.cleanup_idle_modules()
            except Exception as e:
                logger.error(f"❌ 模块清理线程错误: {e}")
    
    def __del__(self):
        """析构函数"""
        self.stop_cleanup_thread()
        self.cleanup_all_modules()

# 全局模块管理器实例
_module_manager = None

def get_module_manager() -> ModuleManager:
    """获取全局模块管理器"""
    global _module_manager
    if _module_manager is None:
        _module_manager = ModuleManager()
    return _module_manager

# 装饰器，用于模块缓存
def cached_module(module_name: str):
    """模块缓存装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_module_manager()
            return manager.load_module(module_name)
        return wrapper
    return decorator

# 上下文管理器，用于临时模块加载
class TemporaryModule:
    """临时模块上下文管理器"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.manager = get_module_manager()
        self.was_loaded = False
    
    def __enter__(self):
        self.was_loaded = self.manager.is_loaded(self.module_name)
        return self.manager.load_module(self.module_name)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 如果原来未加载，则卸载
        if not self.was_loaded:
            self.manager.unload_module(self.module_name)

# 预定义的模块加载器
def load_ml_modules():
    """加载机器学习相关模块"""
    manager = get_module_manager()
    
    ml_modules = [
        'torch',
        'transformers',
        'sentence_transformers',
        'faiss',
        'numpy',
        'scipy'
    ]
    
    loaded_modules = []
    for module_name in ml_modules:
        try:
            module = manager.load_module(module_name)
            loaded_modules.append(module_name)
        except Exception as e:
            logger.warning(f"⚠️ 机器学习模块加载失败: {module_name}, 错误: {e}")
    
    logger.info(f"📦 机器学习模块加载完成: {loaded_modules}")
    return loaded_modules

def unload_ml_modules():
    """卸载机器学习相关模块"""
    manager = get_module_manager()
    
    ml_modules = [
        'torch',
        'transformers', 
        'sentence_transformers',
        'faiss',
        'numpy',
        'scipy'
    ]
    
    unloaded_modules = []
    for module_name in ml_modules:
        if manager.unload_module(module_name, force=True):
            unloaded_modules.append(module_name)
    
    logger.info(f"🗑️ 机器学习模块卸载完成: {unloaded_modules}")
    return unloaded_modules
