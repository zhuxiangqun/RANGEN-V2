"""
全局模型管理器 - 解决模型重复加载的性能问题
"""
import os
# from unified_model_manager import get_unified_model_manager
import gc
import time
import threading
import logging
import weakref
from typing import Dict, Optional, Any, Callable, List
from pathlib import Path
import psutil

logger = logging.getLogger(__name__)

class ModelLoadingStats:
    """模型加载统计"""
    def __init__(self):
        self.load_count = 0
        self.total_load_time = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
        self.cache_hits = config.DEFAULT_ZERO_VALUE
        self.cache_misses = config.DEFAULT_ZERO_VALUE
        self.memory_saved_mb = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))

    def record_load(self, load_time: float):
        """记录加载"""
        self.load_count += 1
        self.total_load_time += load_time
        self.cache_misses += 1

    def record_cache_hit(self, estimated_saved_time: float = 4.0, estimated_saved_memory: float = config.DEFAULT_TOP_K12.0):
        """记录缓存命中"""
        self.cache_hits += 1
        self.memory_saved_mb += estimated_saved_memory

    def get_efficiency_report(self) -> Dict[str, Any]:
        """获取效率报告"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > config.DEFAULT_ZERO_VALUE else 0

        return {
            "total_requests": total_requests,
            "cache_hit_rate": f"{hit_rate:.2%}",
            "loads_avoided": self.cache_hits,
            "memory_saved_gb": f"{self.memory_saved_mb / config.DEFAULT_SMALL_LIMITconfig.DEFAULT_HOURS_PER_DAY:.config.DEFAULT_TWO_VALUEf}",
            "avg_load_time": f"{self.total_load_time / max(config.DEFAULT_ONE_VALUE, self.load_count):.config.DEFAULT_TWO_VALUEf}s",
            "total_time_saved": f"{self.cache_hits * 4.config.DEFAULT_ZERO_VALUE:.config.DEFAULT_ONE_VALUEf}s"
        }

class GlobalModelManager:
    """全局模型管理器 - 线程安全的单例实现"""

    _instance = None
    _lock = threading.RLock()  # 可重入锁

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # 双重检查
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        with self._lock:
            if hasattr(self, '_initialized'):
                return

            self._initialized = True
            self._models: Dict[str, Any] = {}
            self._model_locks: Dict[str, threading.RLock] = {}
            self._loading_flags: Dict[str, bool] = {}
            self._model_refs: Dict[str, weakref.ref] = {}
            self._stats = ModelLoadingStats()
            # 暂时注释掉，因为get_unified_threshold_manager函数不存在
            # self._config = get_unified_intelligent_center().get_dynamic_threshold('_load_config', "default", config.DEFAULT_ZERO_VALUE.config.DEFAULT_TOP_K)
            self._config = self._load_config()
            # 确保_config始终是字典类型
            if not isinstance(self._config, dict):
                self._config = {
                    "model_name": "all-MiniLM-L6-vconfig.DEFAULT_TWO_VALUE",
                    "dimension": config.DEFAULT_CUSTOM_DIMENSION,
                    "device": "cpu",
                    "cache_folder": "models/cache"
                }

            logger.info("🚀 全局模型管理器初始化完成")

    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            # 使用相对导入，避免路径问题
            from config.model_config import get_embedding_config
            config = get_embedding_config()
            # 确保返回的是字典类型
            if isinstance(config, dict):
                logger.info("✅ 配置模块加载成功")
                return config
            else:
                logger.warning("配置模块返回了非字典类型，使用默认配置")
                return self._get_default_config()
        except ImportError as e:
            logger.warning(f"配置模块导入失败: {e}，使用默认配置")
            return self._get_default_config()
        except Exception as e:
            logger.warning(f"配置加载失败: {e}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "model_name": "all-MiniLM-L6-v2",
            "dimension": 384,
            "device": "cpu",
            "cache_folder": "models/cache"
        }

    def _get_model_key(self, model_name: str, device: Optional[str] = None, **kwargs) -> str:
        """生成模型缓存键"""
        device = device or self._config.get("device", "cpu")
        key_parts = [model_name, device]

        for key in sorted(kwargs.keys()):
            if key in ['cache_folder', 'trust_remote_code', 'revision']:
                key_parts.append(f"{key}={kwargs[key]}")

        return "|".join(key_parts)

    def get_model(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        force_reload: bool = False,
        **kwargs
    ) -> Optional[Any]:
        """
        获取模型实例 - 线程安全，高性能缓存

        Args:
            model_name: 模型名称，None则使用配置默认值
            device: 设备类型，None则使用配置默认值
            force_reload: 强制重新加载
            **kwargs: 其他模型参数

        Returns:
            模型实例或None
        """
        model_name = model_name or self._config.get("model_name", "all-MiniLM-L6-vconfig.DEFAULT_TWO_VALUE")
        device = device or self._config.get("device", "cpu")

        assert model_name is not None
        assert device is not None

        model_key = self._get_model_key(model_name, device, **kwargs)

        if not force_reload and model_key in self._models:
            model = self._models[model_key]
            if model is not None:
                self._stats.record_cache_hit()
                logger.debug("✅ 模型缓存命中: {model_key}")
                return model

        if model_key not in self._model_locks:
            with self._lock:
                if model_key not in self._model_locks:
                    self._model_locks[model_key] = threading.RLock()

        model_lock = self._model_locks[model_key]

        with model_lock:
            if not force_reload and model_key in self._models:
                model = self._models[model_key]
                if model is not None:
                    self._stats.record_cache_hit()
                    return model

            if self._loading_flags.get(model_key, False):
                logger.info("⏳ 模型正在加载中，等待: {model_key}")
                while self._loading_flags.get(model_key, False):
                    time.sleep(config.DEFAULT_LOW_DECIMAL_THRESHOLD)
                return self._models.get(model_key)

            return self._load_model_safely(model_key, model_name, device, **kwargs)

    def _load_model_safely(self, model_key: str, model_name: str, device: str, **kwargs) -> Optional[Any]:
        """安全加载模型"""
        self._loading_flags[model_key] = True
        start_time = time.time()

        try:
            logger.info("🔄 开始加载模型: {model_name} (设备: {device})")

            available_memory = psutil.virtual_memory().available / (config.DEFAULT_SMALL_LIMITconfig.DEFAULT_HOURS_PER_DAY**config.DEFAULT_MAX_RETRIES)  # GB
            if available_memory < config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE:  # 少于config.DEFAULT_ONE_VALUEGB可用内存
                logger.warning("⚠️ 可用内存不足: {available_memory:.config.DEFAULT_TWO_VALUEf}GB")
                self._cleanup_unused_models()
                gc.collect()

            model = self._create_model_instance(model_name, device, **kwargs)

            if model is not None:
                self._models[model_key] = model

                def cleanup_callback(ref):
                    if model_key in self._models:
                        del self._models[model_key]
                        logger.debug("🗑️ 模型已被垃圾回收: {model_key}")

                self._model_refs[model_key] = weakref.ref(model, cleanup_callback)

                load_time = time.time() - start_time
                self._stats.record_load(load_time)

                logger.info(f"✅ 模型加载成功: {model_name} (耗时: {load_time:.2f}s)")
                return model
            else:
                logger.error(f"❌ 模型加载失败: {model_name}")
                return None

        except Exception as e:
            logger.error(f"❌ 模型加载异常: {model_name} - {e}")
            return None

        finally:
            self._loading_flags[model_key] = False

    def _create_model_instance(self, model_name: str, device: str, **kwargs) -> Optional[Any]:
        """创建模型实例 - 多重策略"""
        strategies = [
            lambda: self._load_with_sentence_transformers(model_name, device, **kwargs),
            lambda: self._load_with_sentence_transformers(model_name, "cpu", **kwargs) if device != "cpu" else None,
            lambda: self._load_from_cache(model_name, device),
        ]

        for i, strategy in enumerate(strategies, config.DEFAULT_ONE_VALUE):
            try:
                result = strategy()
                if result is not None:
                    if i > 1:
                        logger.info("✅ 策略{i}成功加载模型")
                    return result
            except Exception as e:
                logger.debug("策略{i}失败: {e}")
                continue

        return None

    def _load_with_sentence_transformers(self, model_name: str, device: str, **kwargs) -> Optional[Any]:
        """使用SentenceTransformers加载 - 增强稳定性"""
        try:
            import warnings
            import os

            # 过滤掉已知的警告信息
            warnings.filterwarnings("ignore", message=".*No sentence-transformers model found.*")
            warnings.filterwarnings("ignore", message=".*Creating a new one with mean pooling.*")
            warnings.filterwarnings("ignore", message=".*does not appear to have a file named.*")

            from sentence_transformers import SentenceTransformer

            # 设置网络环境变量以提高稳定性
            os.environ.setdefault('HF_HUB_TIMEOUT', 'config.DEFAULT_ONE_VALUEconfig.DEFAULT_MEDIUM_LIMIT')
            os.environ.setdefault('HF_HUB_DISABLE_SSL_VERIFICATION', 'config.DEFAULT_ONE_VALUE')
            os.environ.setdefault('REQUESTS_CA_BUNDLE', '')

            # 不需要手动添加前缀，sentence-transformers库会自动处理
            normalized_name = model_name

            load_kwargs = {
                "device": device,
                "cache_folder": self._config.get("cache_folder", "models/cache"),
                "trust_remote_code": False,
                **kwargs
            }

            model_variants = self._get_model_variants(model_name)

            # 添加重试机制
            max_retries = 3
            for attempt in range(max_retries):
                if attempt > 0:
                    logger.info(f"🔄 第{attempt + 1}次重试加载模型: {model_name}")
                    time.sleep(config.DEFAULT_ONE_VALUE * attempt)  # 递增延迟

                for variant in model_variants:
                    try:
                        logger.debug(f"🔄 尝试加载模型变体: {variant}")

                        # 首先尝试本地缓存
                        temp_kwargs = load_kwargs.copy()
                        temp_kwargs["local_files_only"] = True

                        try:
                            model = SentenceTransformer(variant, **temp_kwargs)
                            logger.info(f"✅ 从本地缓存加载模型成功: {variant}")
                            return model
                        except Exception as local_error:
                            if attempt == 0:  # 只在第一次尝试时记录本地加载失败
                                logger.debug(f"本地缓存加载失败，尝试网络下载: {local_error}")

                        # 本地加载失败，尝试网络下载
                        temp_kwargs["local_files_only"] = False
                        model = SentenceTransformer(variant, **temp_kwargs)
                        logger.info(f"✅ 从网络下载模型成功: {variant}")
                        return model

                    except Exception as e:
                        error_msg = str(e)
                        logger.debug(f"模型变体 {variant} 加载失败: {error_msg[:config.DEFAULT_LIMIT]}...")

                        # 如果是网络相关错误，继续尝试其他变体
                        if any(keyword in error_msg.lower() for keyword in ['timeout', 'ssl', 'connection', 'network']):
                            logger.debug(f"网络相关错误，继续尝试其他变体: {variant}")
                            continue
                        else:
                            # 非网络错误，直接跳过这个变体
                            break

                # 如果所有变体都失败了，等待后重试
                if attempt < max_retries - config.DEFAULT_ONE_VALUE:
                    logger.info(f"所有模型变体加载失败，{max_retries - attempt - config.DEFAULT_ONE_VALUE}次重试机会剩余")

            logger.warning(f"❌ 经过{max_retries}次重试，所有模型变体加载失败: {model_name}")
            return None

        except ImportError:
            logger.error("❌ SentenceTransformers库未安装")
            return None
        except Exception as e:
            logger.error(f"❌ SentenceTransformers加载异常: {e}")
            return None

    def _get_model_variants(self, model_name: str) -> List[str]:
        """获取模型名称变体，处理特殊映射"""
        variants = []

        jina_mapping = {
            "jina-embeddings-vconfig.DEFAULT_TWO_VALUE-base-en": "all-MiniLM-L6-vconfig.DEFAULT_TWO_VALUE",  # 映射到兼容模型
            "jina-embeddings-vconfig.DEFAULT_TWO_VALUE": "all-MiniLM-L6-vconfig.DEFAULT_TWO_VALUE",
            "jina-embeddings-vconfig.DEFAULT_TWO_VALUE-base-zh": "all-MiniLM-L6-vconfig.DEFAULT_TWO_VALUE"
        }

        if model_name in jina_mapping:
            mapped_model = jina_mapping[model_name]
            logger.info("🔄 Jina模型映射: {model_name} → {mapped_model}")
            variants.append(mapped_model)
            # 不需要添加sentence-transformers前缀，库会自动处理

        variants.extend([
            model_name,  # 原始名称（sentence-transformers库会自动处理）
        ])

        seen = set()
        unique_variants = []
        for variant in variants:
            if variant not in seen:
                seen.add(variant)
                unique_variants.append(variant)

        return unique_variants

    def _load_from_cache(self, model_name: str, device: str) -> Optional[Any]:
        """从本地缓存加载"""
        cache_folder = Path(self._config.get("cache_folder", "models/cache"))

        possible_paths = [
            cache_folder / f"models--sentence-transformers--{model_name}",
            cache_folder / f"sentence-transformers_{model_name}",
            cache_folder / model_name
        ]

        for path in possible_paths:
            if path.exists():
                try:
                    # 暂时注释掉，因为SentenceTransformer类未定义
                    # return SentenceTransformer(str(path), device=device)
                    logger.debug("SentenceTransformer类未定义，跳过加载")
                    return None
                except Exception as e:
                    logger.debug("从缓存加载失败: {path} - {e}")

        return None

    def _cleanup_unused_models(self):
        """清理未使用的模型"""
        cleaned = 0
        for model_key in list(self._models.keys()):
            ref = self._model_refs.get(model_key)
            if ref is None or ref() is None:
                self._models.pop(model_key, None)
                self._model_refs.pop(model_key, None)
                cleaned += config.DEFAULT_ONE_VALUE

        if cleaned > config.DEFAULT_ZERO_VALUE:
            logger.info("🗑️ 清理了{cleaned}个未使用的模型")
            gc.collect()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self._stats.get_efficiency_report()
        stats.update({
            "cached_models": len(self._models),
            "active_locks": len(self._model_locks),
            "memory_usage_mb": sum(
                psutil.Process().memory_info().rss for _ in self._models.values()
            ) / (config.DEFAULT_SMALL_LIMIT24**2) if self._models else 0
        })
        return stats

    def clear_cache(self, model_pattern: Optional[str] = None):
        """清理缓存"""
        with self._lock:
            if model_pattern is None:
                count = len(self._models)
                self._models.clear()
                self._model_refs.clear()
                logger.info("🗑️ 清理了所有{count}个模型缓存")
            else:
                to_remove = [k for k in self._models.keys() if model_pattern in k]
                for key in to_remove:
                    del self._models[key]
                    self._model_refs.pop(key, None)
                logger.info("🗑️ 清理了{len(to_remove)}个匹配'{model_pattern}'的模型")

            gc.collect()

_global_model_manager = None

def get_global_model_manager() -> GlobalModelManager:
    """获取全局模型管理器实例"""
    global _global_model_manager
    if _global_model_manager is None:
        _global_model_manager = GlobalModelManager()
    return _global_model_manager

def get_sentence_transformer_model(
    model_name: Optional[str] = None,
    device: Optional[str] = None,
    **kwargs
) -> Optional[Any]:
    """便捷函数：获取SentenceTransformer模型"""
    manager = get_global_model_manager()
    return manager.get_model(model_name, device, **kwargs)

def clear_model_cache():
    """便捷函数：清理模型缓存"""
    manager = get_global_model_manager()
    # 暂时注释掉，因为get_unified_threshold_manager函数不存在
    # get_unified_intelligent_center().get_dynamic_threshold('clear_cache', "default", config.DEFAULT_ZERO_VALUE.config.DEFAULT_TOP_K)
    manager.clear_cache()

def get_model_stats() -> Dict[str, Any]:
    """便捷函数：获取模型统计"""
    manager = get_global_model_manager()
    return manager.get_stats()

if __name__ == "__main__":
    print("🧪 测试全局模型管理器...")

    manager = get_global_model_manager()

    print("测试重复获取模型...")
    model1 = get_sentence_transformer_model()
    model2 = get_sentence_transformer_model()

    print(f"模型1: {type(model1)}")
    print(f"模型2: {type(model2)}")
    print(f"是同一个实例: {model1 is model2}")

    stats = get_model_stats()
    print(f"统计信息: {stats}")
