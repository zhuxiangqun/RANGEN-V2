"""
统一FAISS服务
解决多处并发访问问题，提供单例模式的FAISS管理
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入统一配置模块
try:
    from src.utils.unified_centers import get_unified_center
    def get_config(key: str, default: Any = None) -> Any:
        try:
            center = get_unified_center("get_unified_config_center")
            if center is not None:
                return center.get_config(key, default)
            return default
        except:
            return default
except ImportError:
    # 如果导入失败，使用os.getenv作为回退
    import os
    def get_config(key: str, default: Any = None) -> Any:
        return os.getenv(key, default)

# 🚀 迁移：优先使用知识库管理系统（第四系统）
try:
    from knowledge_management_system.api.service_interface import get_knowledge_service
    KMS_AVAILABLE = True
    _get_knowledge_service_func = get_knowledge_service
except ImportError:
    KMS_AVAILABLE = False
    _get_knowledge_service_func = None  # type: ignore

# 回退：如果知识库管理系统不可用，使用旧系统（过渡期）
try:
    from memory.enhanced_faiss_memory import EnhancedFAISSMemory
    OLD_FAISS_AVAILABLE = True
except ImportError:
    OLD_FAISS_AVAILABLE = False
    EnhancedFAISSMemory = None

logger = logging.getLogger(__name__)

class FAISSService:
    """统一FAISS服务 - 🚀 迁移：现在作为适配器，内部使用知识库管理系统（第四系统）"""
    
    def __init__(self):
        # 🚀 迁移：优先使用知识库管理系统
        self._kms_service = None
        self._use_kms = False
        
        if KMS_AVAILABLE and _get_knowledge_service_func is not None:
            try:
                self._kms_service = _get_knowledge_service_func()
                self._use_kms = True
                logger.info("✅ FAISSService使用知识库管理系统（第四系统）")
            except Exception as e:
                logger.warning(f"知识库管理系统初始化失败: {e}，回退到旧系统")
                self._use_kms = False
        
        # 回退：使用旧FAISS内存系统（过渡期）
        self._instance: Optional[Any] = None  # type: ignore
        self._lock = asyncio.Lock()
        self._initialization_lock = asyncio.Lock()
        self._is_initializing = False
        self._last_health_check = 0
        self._health_check_interval = 60  # 60秒检查一次

    async def get_instance(self) -> Any:  # type: ignore
        """获取FAISS实例 - 懒加载 + 单例"""
        try:
            # 健康检查
            if not await self._is_healthy():
                await self._reinitialize_if_needed()
            
            if not self._instance:
                async with self._lock:
                    if not self._instance:
                        await self._initialize_faiss()
            
            return self._instance
            
        except Exception as e:
            logger.error(f"获取FAISS实例失败: {e}")
            # 返回一个基本的实例作为回退
            return await self._create_fallback_instance()
    
    async def _is_healthy(self) -> bool:
        """检查FAISS实例是否健康"""
        try:
            if not self._instance:
                return False
            
            current_time = time.time()
            if current_time - self._last_health_check < self._health_check_interval:
                return True
            
            # 执行健康检查
            health_status = await self._perform_health_check()
            self._last_health_check = current_time
            
            return health_status
            
        except Exception as e:
            logger.warning(f"健康检查失败: {e}")
            return False
    
    async def _perform_health_check(self) -> bool:
        """执行健康检查"""
        try:
            if not self._instance:
                return False
            
            # 检查实例是否响应
            # 这里可以添加具体的健康检查逻辑
            return True
            
        except Exception as e:
            logger.warning(f"健康检查执行失败: {e}")
            return False
    
    async def _reinitialize_if_needed(self):
        """如果需要，重新初始化"""
        try:
            if self._instance and await self._is_healthy():
                return
            
            logger.info("重新初始化FAISS实例...")
            self._instance = None
            await self._initialize_faiss()
            
        except Exception as e:
            logger.error(f"重新初始化失败: {e}")
    
    async def _create_fallback_instance(self) -> Any:  # type: ignore
        """创建回退实例"""
        if not OLD_FAISS_AVAILABLE or EnhancedFAISSMemory is None:
            raise RuntimeError("EnhancedFAISSMemory不可用，无法创建回退实例")
        try:
            logger.warning("创建FAISS回退实例...")
            return EnhancedFAISSMemory(dimension=384)
        except Exception as e:
            logger.error(f"创建回退实例失败: {e}")
            # 返回一个最小的实例
            return EnhancedFAISSMemory(dimension=384)

    async def _initialize_faiss(self):
        """初始化FAISS - 只初始化一次"""
        if self._is_initializing:
            while self._is_initializing:
                await asyncio.sleep(0.1)
            return

        async with self._initialization_lock:
            if self._instance:  # 双重检查
                return

            self._is_initializing = True
            try:
                if not OLD_FAISS_AVAILABLE or EnhancedFAISSMemory is None:
                    logger.error("EnhancedFAISSMemory不可用，无法初始化")
                    return
                
                logger.info("🔧 开始初始化FAISS服务...")
                start_time = time.time()

                self._instance = EnhancedFAISSMemory(dimension=384)

                if self._instance is not None:
                    if hasattr(self._instance, 'ensure_index_ready'):
                        await asyncio.wait_for(
                            self._instance.ensure_index_ready(),  # type: ignore
                            timeout=10.0
                        )
                    elif hasattr(self._instance, 'wait_for_initialization'):
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(
                            None,
                            lambda: self._instance.wait_for_initialization(timeout=10.0) if self._instance else None  # type: ignore
                        )

                init_time = time.time() - start_time
                logger.info(f"✅ FAISS服务初始化完成，耗时: {init_time:.2f}秒")

            except Exception as e:
                logger.error(f"❌ FAISS服务初始化失败: {e}")
                self._instance = None
                raise
            finally:
                self._is_initializing = False

    async def search(self, query: str, top_k: int, similarity_threshold: float = get_config("medium_threshold", 0.7)) -> List[Dict[str, Any]]:
        """
        搜索知识 - 🚀 迁移：优先使用知识库管理系统
        
        Args:
            query: 查询文本
            top_k: 返回数量
            similarity_threshold: 相似度阈值
        
        Returns:
            搜索结果列表
        """
        # 🚀 迁移：优先使用知识库管理系统
        if self._use_kms and self._kms_service:
            try:
                # 🚀 启用rerank，在知识库管理系统中完成
                # 🆕 P0：启用LlamaIndex增强检索（查询扩展+多策略融合）
                results = self._kms_service.query_knowledge(
                    query=query,
                    modality="text",
                    top_k=top_k,
                    similarity_threshold=similarity_threshold,
                    use_rerank=True,  # 🚀 在知识库管理系统中完成rerank
                    use_llamaindex=True  # 🆕 P0：启用LlamaIndex增强检索
                )
                
                # 转换为旧格式（兼容旧接口）
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        'content': result.get('content', ''),
                        'similarity_score': result.get('similarity_score', 0.0),
                        'entry_id': result.get('knowledge_id', ''),
                        'rank': result.get('rank', 0),
                        'metadata': result.get('metadata', {})
                    })
                
                return formatted_results
            except Exception as e:
                logger.warning(f"知识库管理系统搜索失败: {e}，回退到旧系统")
        
        # 回退：使用旧FAISS系统（过渡期）
        if not OLD_FAISS_AVAILABLE:
            logger.error("旧FAISS系统不可用")
            return []
        
        try:
            # 使用旧search方法（保持原逻辑）
            instance = await self.get_instance()
            if not instance:
                logger.warning("⚠️ FAISS实例未初始化")
                return []

            if not await self._quick_health_check():
                logger.warning("⚠️ FAISS索引状态异常")
                return []

            results = instance.search(query, top_k)

            formatted_results = []
            for result in results:
                if isinstance(result, dict):
                    formatted_results.append({
                        'content': result.get('content', ''),
                        'title': result.get('metadata', {}).get('query', ''),
                        'source': 'faiss_service',
                        'confidence': result.get('similarity', get_config("medium_threshold", 0.7)),
                        'similarity_score': result.get('similarity', get_config("medium_threshold", 0.7))
                    })

            logger.debug(f"FAISS搜索完成: 查询='{query[:30]}...', 结果数={len(formatted_results)}")
            return formatted_results

        except Exception as e:
            logger.error(f"❌ FAISS搜索失败: {e}")
            return []

    async def add_entry(self, entry: Dict[str, Any]) -> bool:
        """统一的添加接口"""
        try:
            instance = await self.get_instance()
            if not instance:
                return False

            if hasattr(instance, 'add_entry'):
                await instance.add_entry(entry)
                return True
            else:
                logger.warning("⚠️ FAISS实例不支持添加条目")
                return False

        except Exception as e:
            logger.error(f"❌ 添加FAISS条目失败: {e}")
            return False

    async def ensure_index_ready(self) -> bool:
        """统一的索引就绪检查"""
        try:
            instance = await self.get_instance()
            if not instance:
                return False

            if hasattr(instance, 'ensure_index_ready'):
                return await instance.ensure_index_ready()
            elif hasattr(instance, 'wait_for_initialization'):
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None,
                    lambda: instance.wait_for_initialization(timeout=5.0)
                )
            else:
                return True

        except Exception as e:
            logger.error(f"❌ 检查FAISS索引就绪状态失败: {e}")
            return False

    async def _quick_health_check(self) -> bool:
        """快速健康检查 - 避免频繁深度检查"""
        current_time = time.time()

        if current_time - self._last_health_check < self._health_check_interval:
            return True

        try:
            instance = await self.get_instance()
            if not instance:
                return False

            # 🚀 改进：索引可能正在重建中，允许索引为空的情况
            if not hasattr(instance, 'index'):
                logger.debug("⚠️ FAISS实例缺少index属性")
                return False
            
            # 🚀 改进：如果索引为空但正在初始化中，返回True（允许继续等待）
            if instance.index is None:
                # 检查是否正在初始化或重建
                if hasattr(instance, '_index_needs_rebuild') and instance._index_needs_rebuild:
                    logger.debug("🔄 索引正在重建中，跳过健康检查")
                    return True  # 允许继续，等待重建完成
                logger.debug("⚠️ FAISS索引未初始化")
                return False

            # 🚀 改进：知识条目可以为空（新系统或重建中）
            # 只要有索引即可，知识条目可能正在加载
            if not hasattr(instance, 'knowledge_entries'):
                logger.debug("⚠️ FAISS实例缺少knowledge_entries属性")
                return False
            
            # 即使knowledge_entries为空，只要有索引就认为健康（可能正在重建）

            self._last_health_check = current_time
            return True

        except Exception as e:
            logger.warning(f"FAISS健康检查失败: {e}")
            return False

    async def rebuild_index(self) -> bool:
        """重建索引"""
        try:
            instance = await self.get_instance()
            if not instance:
                return False

            if hasattr(instance, '_rebuild_index_smart'):
                await instance._rebuild_index_smart()
                logger.info("✅ FAISS索引重建完成")
                return True
            else:
                logger.warning("⚠️ FAISS实例不支持索引重建")
                return False

        except Exception as e:
            logger.error(f"❌ FAISS索引重建失败: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            'has_instance': self._instance is not None,
            'is_initializing': self._is_initializing,
            'last_health_check': self._last_health_check,
            'health_check_interval': self._health_check_interval
        }

    async def shutdown(self):
        """关闭服务"""
        try:
            if self._instance:
                if hasattr(self._instance, 'close'):
                    await self._instance.close()
                elif hasattr(self._instance, 'shutdown'):
                    await self._instance.shutdown()

            self._instance = None
            logger.info("✅ FAISS服务已关闭")

        except Exception as e:
            logger.error(f"❌ 关闭FAISS服务失败: {e}")

_global_faiss_service: Optional[FAISSService] = None

def get_faiss_service() -> FAISSService:
    """获取全局FAISS服务实例"""
    global _global_faiss_service
    if _global_faiss_service is None:
        _global_faiss_service = FAISSService()
    return _global_faiss_service

async def shutdown_faiss_service():
    """关闭全局FAISS服务"""
    global _global_faiss_service
    if _global_faiss_service:
        await _global_faiss_service.shutdown()
        _global_faiss_service = None
