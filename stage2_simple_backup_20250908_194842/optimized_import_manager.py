#!/usr/bin/env pythonconfig.DEFAULT_MAX_RETRIES
"""
优化导入管理器
统一管理模块导入，减少循环依赖和重复导入，提高加载性能
"""

import logging
import sys
from typing import Dict, Any, Optional, Callable
import threading
import time

logger = logging.getLogger(__name__)

class OptimizedImportManager:
    """优化导入管理器"""

    def __init__(self):
        self._imports_cache: Dict[str, Any] = {}
        self._import_times: Dict[str, float] = {}
        self._failed_imports: Set[str] = set()
        self._lock = threading.RLock()

        # 预定义的模块映射
        self._module_mappings = {
            # 统一中心系统
            'unified_data_center': ('src.utils.unified_data_center', 'get_unified_data_center'),
            'unified_monitoring_center': ('src.utils.unified_monitoring_center', 'get_unified_monitoring_center'),
            'unified_config_center': ('src.utils.unified_config_center', 'get_unified_config_center'),
            'unified_intelligent_center': ('src.utils.unified_intelligent_center', 'get_unified_intelligent_center'),

            # 智能化组件
            'intelligent_data_classifier': ('src.utils.intelligent_data_classifier', 'get_intelligent_data_classifier'),
            'data_quality_analyzer': ('src.utils.data_quality_analyzer', 'get_data_quality_analyzer'),
            'predictive_data_manager': ('src.utils.predictive_data_manager', 'get_predictive_data_manager'),
            'personalized_recommendation_engine': ('src.utils.personalized_recommendation_engine', 'get_personalized_recommendation_engine'),
            'intelligent_conversation_guide': ('src.utils.intelligent_conversation_guide', 'get_intelligent_conversation_guide'),

            # 配置和智能系统
            'smart_config_system': ('src.utils.smart_config_system', 'get_smart_config,create_query_context'),
            'dynamic_config_manager': ('src.utils.dynamic_config_manager', 'get_dynamic_config_manager'),

            # 其他工具
            'reflection_integrator': ('src.utils.reflection_integrator', 'ReflectionIntegrator'),
            'wiki_content_updater': ('src.utils.wiki_content_updater', 'get_wiki_content_updater'),
        }

    def get_module(self, module_name: str) -> Any:
        """获取模块，避免重复导入"""
        with self._lock:
            if module_name in self._imports_cache:
                return self._imports_cache[module_name]

            if module_name in self._failed_imports:
                return None

            try:
                start_time = time.time()

                if module_name in self._module_mappings:
                    module_path, factory_name = self._module_mappings[module_name]
                    module = self._import_with_fallback(module_path)

                    if module and factory_name:
                        # 如果有工厂函数，调用它
                        if ',' in factory_name:
                            # 多个导入项
                            factory_names = [name.strip() for name in factory_name.split(',')]
                            result = {}
                            for name in factory_names:
                                if hasattr(module, name):
                                    result[name] = getattr(module, name)
                        else:
                            # 单个工厂函数
                            if hasattr(module, factory_name):
                                factory_func = getattr(module, factory_name)
                                if callable(factory_func):
                                    result = factory_func()
                                else:
                                    result = factory_func
                            else:
                                result = module
                    else:
                        result = module
                else:
                    # 直接导入
                    result = self._import_with_fallback(module_name)

                import_time = time.time() - start_time
                self._import_times[module_name] = import_time

                if result is not None:
                    self._imports_cache[module_name] = result
                    logger.debug(f"模块 {module_name} 导入成功，耗时 {import_time:.config.DEFAULT_MAX_RETRIESf}s")
                else:
                    self._failed_imports.add(module_name)

                return result

            except Exception as e:
                logger.warning(f"导入模块失败 {module_name}: {e}")
                self._failed_imports.add(module_name)
                return None

    def _import_with_fallback(self, module_path: str) -> Optional[Any]:
        """带回退机制的导入"""
        try:
            # 首先尝试直接导入
            module_parts = module_path.split('.')
            module = __import__(module_path, fromlist=[module_parts[-1]])

            # 如果是src开头的模块，尝试从不同路径导入
            if module_path.startswith('src.'):
                try:
                    alt_path = module_path[4:]  # 移除src.
                    alt_module = __import__(alt_path, fromlist=[module_parts[-1]])
                    if alt_module and hasattr(alt_module, module_parts[-1]):
                        return getattr(alt_module, module_parts[-1])
                except ImportError:
                    pass

            return module

        except ImportError as e:
            logger.debug(f"直接导入失败 {module_path}: {e}")

            # 尝试从上级目录导入
            try:
                parent_path = '.'.join(module_path.split('.')[:-1])
                if parent_path:
                    parent_module = __import__(parent_path, fromlist=[module_path.split('.')[-1]])
                    if hasattr(parent_module, module_path.split('.')[-1]):
                        return getattr(parent_module, module_path.split('.')[-1])
            except ImportError:
                pass

            return None

    def get_function(self, module_name: str, function_name: str) -> Optional[Callable]:
        """获取模块中的函数"""
        module = self.get_module(module_name)
        if module and hasattr(module, function_name):
            func = getattr(module, function_name)
            if callable(func):
                return func
        return None

    def call_function(self, module_name: str, function_name: str, *args, **kwargs) -> Any:
        """调用模块中的函数"""
        func = self.get_function(module_name, function_name)
        if func:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"调用函数失败 {module_name}.{function_name}: {e}")
        return None

    def get_import_stats(self) -> Dict[str, Any]:
        """获取导入统计信息"""
        with self._lock:
            return {
                'cached_imports': len(self._imports_cache),
                'failed_imports': len(self._failed_imports),
                'import_times': self._import_times,
                'total_import_time': sum(self._import_times.values()),
                'average_import_time': sum(self._import_times.values()) / max(len(self._import_times), 1)
            }

    def clear_cache(self):
        """清空缓存"""
        with self._lock:
            self._imports_cache.clear()
            self._import_times.clear()
            self._failed_imports.clear()
            logger.info("导入缓存已清空")

    def preload_common_modules(self):
        """预加载常用模块"""
        common_modules = [
            'unified_config_center',
            'smart_config_system',
            'unified_monitoring_center'
        ]

        logger.info("开始预加载常用模块...")
        for module_name in common_modules:
            self.get_module(module_name)

        logger.info("常用模块预加载完成")

# 全局导入管理器实例
_import_manager = None

def get_optimized_import_manager() -> OptimizedImportManager:
    """获取优化导入管理器实例"""
    global _import_manager
    if _import_manager is None:
        _import_manager = OptimizedImportManager()
    return _import_manager

def get_module(module_name: str) -> Any:
    """便捷函数：获取模块"""
    manager = get_optimized_import_manager()
    return manager.get_module(module_name)

def get_function(module_name: str, function_name: str) -> Optional[Callable]:
    """便捷函数：获取函数"""
    manager = get_optimized_import_manager()
    return manager.get_function(module_name, function_name)

def call_function(module_name: str, function_name: str, *args, **kwargs) -> Any:
    """便捷函数：调用函数"""
    manager = get_optimized_import_manager()
    return manager.call_function(module_name, function_name, *args, **kwargs)

# 便捷的统一中心系统获取函数
def get_unified_data_center():
    """获取统一数据中心"""
    return call_function('unified_data_center', 'get_unified_data_center')

def get_unified_monitoring_center():
    """获取统一监控中心"""
    return call_function('unified_monitoring_center', 'get_unified_monitoring_center')

def get_unified_config_center():
    """获取统一配置中心"""
    return call_function('unified_config_center', 'get_unified_config_center')

def get_smart_config(key=None, context=None):
    """获取智能配置"""
    if key is not None:
        return call_function('smart_config_system', 'get_smart_config')(key, context)
    else:
        return call_function('smart_config_system', 'get_smart_config')

def create_query_context(**kwargs):
    """创建查询上下文"""
    return call_function('smart_config_system', 'create_query_context')(**kwargs)
