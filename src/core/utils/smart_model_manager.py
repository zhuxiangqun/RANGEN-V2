"""
Smart Model Manager
智能模型管理器，支持按需加载和 LRU 淘汰，优化内存使用。
"""

import time
import threading
from typing import Dict, Any, Optional, Tuple
from src.services.logging_service import get_logger

logger = get_logger(__name__)

class SmartModelManager:
    """
    智能模型管理器
    
    Features:
    1. 按需加载 (Lazy Loading)
    2. LRU 缓存淘汰 (Least Recently Used)
    3. 线程安全
    """
    
    def __init__(self, max_models_in_memory: int = 2):
        self.max_models = max_models_in_memory
        # 缓存结构: model_name -> (model_instance, last_access_time)
        self.model_pool: Dict[str, Tuple[Any, float]] = {}
        self.lock = threading.RLock()
        
    def get_model(self, model_name: str, loader_func: callable) -> Optional[Any]:
        """
        获取模型实例
        
        Args:
            model_name: 模型唯一标识符
            loader_func: 加载函数，如果不命中缓存则调用此函数加载模型
            
        Returns:
            模型实例
        """
        with self.lock:
            # 1. 缓存命中
            if model_name in self.model_pool:
                model, _ = self.model_pool[model_name]
                # 更新访问时间
                self.model_pool[model_name] = (model, time.time())
                logger.debug(f"模型缓存命中: {model_name}")
                return model
            
            # 2. 缓存未命中，需要加载
            logger.info(f"模型缓存未命中，开始加载: {model_name}")
            
            # 检查是否需要淘汰
            if len(self.model_pool) >= self.max_models:
                self._evict_oldest_model()
            
            try:
                # 加载模型
                start_time = time.time()
                model = loader_func()
                if model is None:
                    logger.error(f"模型加载函数返回 None: {model_name}")
                    return None
                
                # 放入缓存
                self.model_pool[model_name] = (model, time.time())
                logger.info(f"模型加载完成: {model_name} (耗时 {time.time() - start_time:.2f}s)")
                return model
                
            except Exception as e:
                logger.error(f"加载模型失败 {model_name}: {e}")
                return None

    def _evict_oldest_model(self):
        """淘汰最久未使用的模型"""
        if not self.model_pool:
            return
            
        # 找到访问时间最早的模型
        oldest_name = min(self.model_pool.keys(), key=lambda k: self.model_pool[k][1])
        model, _ = self.model_pool[oldest_name]
        
        # 尝试释放资源（如果模型有 close/cpu 方法）
        try:
            if hasattr(model, 'cpu'):
                model.cpu() # 移出 GPU
            if hasattr(model, 'close'):
                model.close()
        except Exception as e:
            logger.warning(f"释放模型资源失败 {oldest_name}: {e}")
            
        del self.model_pool[oldest_name]
        logger.info(f"已淘汰模型以释放内存: {oldest_name}")
        
        # 强制垃圾回收
        import gc
        gc.collect()

# 全局单例
_manager_instance = None
_manager_lock = threading.Lock()

def get_model_manager() -> SmartModelManager:
    global _manager_instance
    with _manager_lock:
        if _manager_instance is None:
            _manager_instance = SmartModelManager()
    return _manager_instance
