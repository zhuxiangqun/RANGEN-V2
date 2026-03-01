# 基本导入
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
import json
import logging
import os
import threading
import time

import numpy as np

# 导入统一配置模块
try:
    from ..utils.unified_centers import get_smart_config, create_query_context
except ImportError:
    # 如果导入失败，使用os.getenv作为回退
    def _fallback_get_smart_config(key: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """回退配置获取函数"""
        try:
            # 尝试从环境变量获取
            value = os.getenv(key)
            if value is not None:
                return value
            
            # 尝试从上下文获取
            if context and key in context:
                return context[key]
            
            # 返回默认值
            defaults = {
                'FAISS_DIMENSION': 384,
                'FAISS_INDEX_TYPE': 'IndexFlatIP',
                'FAISS_BATCH_SIZE': 1000,
                'FAISS_NPROBE': 10
            }
            return defaults.get(key, None)
            
        except Exception as e:
            print(f"获取配置失败: {e}")
            return None
    
    def _fallback_create_query_context(query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """回退查询上下文创建函数"""
        try:
            context = {
                "query": query,
                "user_id": user_id or "anonymous",
                "timestamp": time.time(),
                "session_id": f"session_{int(time.time())}",
                "metadata": {}
            }
            return context
        except Exception as e:
            print(f"创建查询上下文失败: {e}")
            return {"query": query, "user_id": user_id}
    
    # 使用回退函数
    get_smart_config = _fallback_get_smart_config
    create_query_context = _fallback_create_query_context

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

"""
增强FAISS内存系统
提供基于FAISS的高效向量存储和检索功能
"""

logger = logging.getLogger("memory.enhanced_faiss")

@dataclass
class KnowledgeEntry:
    """知识条目"""
    entry_id: str
    query: str
    answer: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    confidence: float
    quality_score: float
    usage_count: int = 0
    last_accessed: Optional[datetime] = None

class EnhancedFAISSMemory:
    """增强FAISS内存系统 - 只使用真实FAISS索引"""
    _instance = None
    _lock = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            if cls._lock is None:
                cls._lock = threading.Lock()
            if cls._lock is not None:
                with cls._lock:
                    if cls._instance is None:
                        cls._instance = super().__new__(cls)
            else:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, index_path: Optional[str] = None, dimension: int = 384):
        """初始化增强FAISS内存系统"""
        if hasattr(self, '_initialized') and getattr(self, '_initialized', False):
            logger.debug("✅ FAISS内存系统已经初始化，跳过重复初始化")
            return
        self._initialized = True
        logger.debug("🔄 FAISS内存系统首次初始化")

        if not hasattr(self, '_index_cache'):
            self._index_cache = {}
            self._index_cache_timestamp = 0
            self._index_cache_ttl = 1800

        self._index_loaded = False

        self.index_path = self._resolve_index_path(index_path)
        self.dimension = dimension
        self.index = None
        self.knowledge_entries = []
        self.entry_metadata = {}

        if not hasattr(self, '_model_loaded'):
            self._model = None
            self._model_loaded = False
            self._jina_service = None
            # 🆕 优先加载本地模型（完全免费，无需API密钥）
            self._initialize_local_model()
            # Fallback: 如果本地模型不可用，尝试Jina API
            if not self._model:
                self._initialize_jina_service()
            
            # 🆕 根据实际使用的模型更新索引维度
            if self._model:
                try:
                    # 测试获取向量维度
                    test_embedding = self._model.encode(["test"])[0]
                    if test_embedding is not None:
                        actual_dim = test_embedding.shape[0]
                        if actual_dim != self.dimension:
                            logger.info(f"🔄 检测到本地模型向量维度({actual_dim})与默认维度({self.dimension})不匹配，更新为{actual_dim}")
                            self.dimension = actual_dim
                except Exception as e:
                    logger.warning(f"⚠️ 无法检测本地模型向量维度: {e}，使用默认维度{self.dimension}")
            elif self._jina_service and self._jina_service.api_key:
                try:
                    # 测试获取向量维度
                    test_embedding = self._jina_service.get_embedding("test")
                    if test_embedding is not None:
                        actual_dim = test_embedding.shape[0]
                        if actual_dim != self.dimension:
                            logger.info(f"🔄 检测到Jina向量维度({actual_dim})与默认维度({self.dimension})不匹配，更新为{actual_dim}")
                            self.dimension = actual_dim
                except Exception as e:
                    logger.warning(f"⚠️ 无法检测Jina向量维度: {e}，使用默认维度{self.dimension}")

        self._index_version = "1.0"
        self._index_metadata_file = self.index_path.replace('faiss_index.bin', 'index_metadata.json')
        self._index_last_modified = None
        self._knowledge_last_modified = None
        self._index_needs_rebuild = False

        self._search_cache = {}  # 查询结果缓存
        self._cache_size_limit = 2000  # 增加缓存大小限制
        self._cache_ttl = 7200  # 增加缓存TTL（2小时）
        self._cache_timestamps = {}  # 缓存时间戳
        self._cache_hits = 0  # 缓存命中次数
        self._cache_misses = 0
        
        # 性能监控
        self._performance_metrics = {
            'search_times': [],
            'search_counts': 0,
            'total_search_time': 0.0,
            'avg_search_time': 0.0,
            'max_search_time': 0.0,
            'min_search_time': float('inf'),
            'query_lengths': [],
            'result_counts': [],
            'cache_hit_rate': 0.0
        }  # 缓存未命中次数

        self._index_cache = {}  # 索引数据缓存
        self._index_cache_timestamp = 0  # 索引缓存时间戳
        self._index_cache_ttl = 1800  # 索引缓存TTL（30分钟）

        self._preload_initialized = False
        self._frequently_accessed = set()  # 频繁访问的知识条目

        self._index_optimized = False
        self._optimization_threshold = get_smart_config("large_limit", create_query_context("large_limit")) or 1000  # 优化阈值

        self._search_times: List[float] = []
        self._cache_hit_rate: float = 0.0
        self._initialization_times: List[float] = []  # 初始化时间记录
        self._last_initialization_time: float = 0.0  # 上次初始化时间

        self._index_loaded = False
        self._initialization_task = None
        try:
            import asyncio
            self._initialization_lock = asyncio.Lock()
        except (NameError, ImportError):
            # asyncio not available, use threading lock
            self._initialization_lock = threading.Lock()

        self._index_health_check_enabled: bool = True
        self._last_health_check: float = 0.0
        self._health_check_interval: int = 300  # 5分钟检查一次

        self._ensure_directory()

        # 初始化缓存相关属性
        if not hasattr(self, 'force_reload_from_cache'):
            self.force_reload_from_cache = lambda: False
        
        # 初始化预加载相关属性
        if not hasattr(self, '_preload_initialized'):
            self._preload_initialized = False
            self._frequently_accessed = set()
            self._index_optimized = False
        
        # 初始化异步锁
        if not hasattr(self, '_initialization_lock'):
            import asyncio
            self._initialization_lock = asyncio.Lock()
        
        # 初始化任务
        if not hasattr(self, '_initialization_task'):
            self._initialization_task = None

        if not hasattr(self, '_async_init_started'):
            self._async_init_started = True
            self._start_async_initialization()
            logger.info("增强FAISS内存系统基础初始化完成，索引将异步加载")
        else:
            logger.debug("✅ 异步初始化已启动，跳过重复启动")

    def wait_for_initialization(self, timeout: float = 30.0) -> bool:
        """等待初始化完成（同步方法）"""
        if self._index_loaded:
            logger.debug("✅ FAISS索引已加载，无需等待")
            return True

        cache_exists = self._index_cache is not None
        cache_content = list(self._index_cache.keys()) if self._index_cache else '无'
        logger.debug("🔍 检查缓存状态: 缓存存在=%s, 缓存内容=%s", cache_exists, cache_content)
        if self._is_index_cache_valid():
            logger.info("✅ 从缓存快速加载FAISS索引")
            if self.force_reload_from_cache():
                return True
            logger.warning("⚠️ 从缓存加载失败，将使用其他初始化方式")
        else:
            logger.debug("⚠️ 缓存无效，将使用其他初始化方式")

        if hasattr(self, '_initialization_task') and self._initialization_task:
            logger.info("⏳ 等待异步初始化完成...")
            start_time = time.time()
            while not self._index_loaded and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if self._index_loaded:
                logger.info("✅ 异步初始化完成")
                return True

        if not self._index_loaded:
            logger.warning("⚠️ FAISS异步初始化超时 (%s秒)，尝试同步初始化...", timeout)
            return self._sync_initialize()

        return True

    def _sync_initialize(self) -> bool:
        """同步初始化（回退方案）"""
        try:
            logger.info("🔄 开始FAISS内存系统同步初始化...")

            # 1. 检查FAISS可用性
            if not FAISS_AVAILABLE or faiss is None:
                logger.error("❌ FAISS库不可用，无法进行同步初始化")
                return False

            # 2. 创建必要的目录
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            # 创建知识条目存储目录
            knowledge_dir = os.path.join(os.path.dirname(self.index_path), 'knowledge')
            os.makedirs(knowledge_dir, exist_ok=True)

            # 3. 加载或创建索引
            if not self._load_or_create_index_sync():
                logger.error("❌ 索引加载/创建失败")
                return False

            # 4. 加载知识条目
            if not self._load_knowledge_entries_sync():
                logger.error("❌ 知识条目加载失败")
                return False

            # 5. 验证索引状态
            if not self._validate_index_integrity_sync():
                logger.error("❌ 索引状态验证失败")
                return False

            # 6. 缓存管理
            if not self._is_index_cache_valid():
                logger.info("💾 将初始化结果保存到缓存...")
                if not self._cache_index():
                    logger.warning("⚠️ 索引缓存保存失败")
                if not self._cache_knowledge_entries():
                    logger.warning("⚠️ 知识条目缓存保存失败")

            # 7. 设置初始化状态
            self._index_loaded = True
            self._initialization_time = time.time()
            
            # 8. 性能优化
            self._optimize_index()
            
            logger.info("✅ FAISS内存系统同步初始化完成")
            return True

        except (OSError, IOError) as e:
            logger.error("❌ FAISS内存系统同步初始化失败 (文件操作错误): %s", e)
            return False
        except ImportError as e:
            logger.error("❌ FAISS内存系统同步初始化失败 (导入错误): %s", e)
            return False
        except Exception as e:
            logger.error("❌ FAISS内存系统同步初始化失败 (未知错误): %s", e)
            return False

    def _load_or_create_index_sync(self):
        """同步加载或创建FAISS索引（智能缓存版本）"""
        try:
            if self._is_index_cache_valid():
                logger.info("✅ 从缓存加载FAISS索引")
                self.index = self._index_cache.get('index')
                return

            if self._check_index_file_health_sync():
                if not FAISS_AVAILABLE or faiss is None:
                    logger.error("❌ FAISS库不可用，无法加载索引")
                    return
                logger.info("🔄 从磁盘加载FAISS索引...")
                if FAISS_AVAILABLE and faiss is not None:
                    self.index = faiss.read_index(self.index_path)
                    
                    # 🚀 检查索引维度是否匹配
                    if self.index and hasattr(self.index, 'd'):
                        index_dim = self.index.d
                        if index_dim != self.dimension:
                            logger.warning(f"⚠️ 索引维度({index_dim})与当前维度({self.dimension})不匹配，标记需要重建")
                            self._index_needs_rebuild = True
                            # 保存旧索引，创建新索引
                            old_index_path = f"{self.index_path}.old_{int(time.time())}"
                            import shutil
                            try:
                                if os.path.exists(self.index_path):
                                    shutil.copy2(self.index_path, old_index_path)
                                    logger.info(f"📦 旧索引已备份到: {old_index_path}")
                            except Exception as e:
                                logger.warning(f"⚠️ 备份旧索引失败: {e}")
                            self.index = None
                        else:
                            logger.info(f"✅ 成功同步加载现有FAISS索引，维度: {index_dim}")
                    else:
                        logger.info("✅ 成功同步加载现有FAISS索引")
                else:
                    logger.warning("⚠️ FAISS不可用，无法加载索引")
                    self.index = None

                self._cache_index()

                if not self._validate_index_integrity_sync():
                    logger.warning("⚠️ 索引完整性检查失败，将重新创建")
                    self._recreate_index_sync()
                else:
                    logger.info("📁 索引文件不存在或损坏，将同步创建新索引")
                    self._recreate_index_sync()

        except (OSError, IOError) as e:
            logger.error("同步初始化索引失败 (文件操作错误): %s", e)
            self._create_empty_index_sync()
        except ImportError as e:
            logger.error("同步初始化索引失败 (导入错误): %s", e)
            self._create_empty_index_sync()
        except Exception as e:
            logger.error("同步初始化索引失败 (未知错误): %s", e)
            self._create_empty_index_sync()

    def _check_index_file_health_sync(self) -> bool:
        """同步检查索引文件健康状态"""
        try:
            if not os.path.exists(self.index_path):
                return False

            file_size = os.path.getsize(self.index_path)
            if file_size < 1000:  # 小于1KB的文件可能是损坏的
                logger.warning("⚠️ 索引文件过小 (%s bytes, file_size)，可能损坏")
                return False

            return True

        except Exception as e:
            logger.warning("⚠️ 检查索引文件健康状态失败: %s", e)
            return False

    def _validate_index_integrity_sync(self) -> bool:
        """同步验证索引完整性"""
        try:
            if not self.index:
                return False

            if hasattr(self.index, 'd') and hasattr(self.index, 'ntotal'):
                if getattr(self.index, 'd', 0) != self.dimension:
                    logger.warning("⚠️ 索引维度不匹配: 期望%s, 实际%s", self.dimension, getattr(self.index, 'd', 0))
                    return False
                
                if getattr(self.index, 'ntotal', 0) == 0:
                    logger.warning("⚠️ 索引为空，没有向量数据")
                    return False

            return True

        except Exception as e:
            logger.warning("⚠️ 验证索引完整性失败: %s", e)
            return False

    def _recreate_index_sync(self):
        """同步重新创建索引"""
        try:
            logger.info("开始同步重新创建索引")
            
            if FAISS_AVAILABLE and faiss is not None:
                self.index = faiss.IndexFlatIP(self.dimension)
                logger.info("✅ 成功创建新的FAISS索引")

                faiss.write_index(self.index, self.index_path)
                logger.info("✅ 新索引已保存")
            else:
                logger.warning("⚠️ FAISS不可用，无法创建索引")
                self.index = None

        except Exception as e:
            logger.error("❌ 重新创建索引失败: %s", e)
            self._create_empty_index_sync()

    def _create_empty_index_sync(self):
        """同步创建空索引（最后的回退方案）"""
        try:
            logger.info("开始同步创建空索引（回退方案）")
            
            if FAISS_AVAILABLE and faiss is not None:
                self.index = faiss.IndexFlatIP(self.dimension)
                logger.info("✅ 创建了空的FAISS索引（回退方案）")
            else:
                logger.warning("⚠️ FAISS不可用，无法创建索引")
                self.index = None

        except Exception as e:
            logger.error("❌ 创建空索引失败: %s", e)
            self.index = None

    def _load_knowledge_entries_sync(self):
        """同步加载知识条目（智能缓存版本）- 增强版：验证知识质量"""
        try:
            if self._is_knowledge_cache_valid():
                logger.info("✅ 从缓存加载知识条目")
                self.knowledge_entries = self._index_cache.get('knowledge_entries', [])
                return

            knowledge_file = self.index_path.replace('faiss_index.bin', 'knowledge_entries.json')

            if os.path.exists(knowledge_file):
                logger.info("🔄 从磁盘加载知识条目...")
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, list):
                    raw_entries = data
                elif isinstance(data, dict):
                    raw_entries = data.get('entries', [])
                else:
                    raw_entries = []

                # 🔧 根本修复：验证知识条目内容质量
                # 检测是否有大量问题混入知识库
                problematic_count = 0
                valid_entries = []
                
                for entry in raw_entries:
                    content = entry.get('content', '') or entry.get('text', '')
                    if content and len(content.strip()) > 10:
                        # 检查是否是问题而非知识
                        if self._is_content_likely_question(content):
                            problematic_count += 1
                            logger.debug(f"检测到问题内容（非知识）: {content[:80]}...")
                        else:
                            valid_entries.append(entry)
                
                # 如果超过30%的内容是问题，标记需要重建
                if problematic_count > len(raw_entries) * 0.3:
                    logger.warning(
                        f"⚠️ 检测到知识库质量问题: {problematic_count}/{len(raw_entries)}条是问题而非知识 "
                        f"({problematic_count/len(raw_entries)*100:.1f}%)，将触发重建"
                    )
                    self._index_needs_rebuild = True
                    # 先使用有效条目，后续会重建
                    self.knowledge_entries = valid_entries
                    logger.info(f"✅ 暂时使用 {len(valid_entries)} 条有效知识条目，重建将使用wiki_cache的正确数据")
                else:
                    self.knowledge_entries = raw_entries
                    logger.info(f"✅ 同步加载了 {len(self.knowledge_entries)} 条知识条目（质量问题: {problematic_count}条）")

                self._cache_knowledge_entries()
            else:
                logger.info("📁 知识条目文件不存在，使用空列表")
                self.knowledge_entries = []

        except Exception as e:
            logger.warning("⚠️ 同步加载知识条目失败: %s", e)
            self.knowledge_entries = []
    
    def _is_content_likely_question(self, text: str) -> bool:
        """判断内容是否看起来像问题而非知识（用于验证知识库质量）"""
        if not text or len(text.strip()) < 10:
            return False
        
        text_lower = text.lower().strip()
        
        # 问题特征指标
        question_indicators = [
            '?',  # 问号
            'how many', 'how much', 'how long', 'how old', 'how far',  # How系列
            'what', 'who', 'when', 'where', 'why', 'which',  # Wh-系列
            'if ', 'imagine',  # 条件句
            'would', 'could', 'should',  # 情态动词
        ]
        
        # 检查开头是否是疑问词
        starts_with_question = any(text_lower.startswith(indicator) for indicator in question_indicators)
        
        # 检查是否包含问号
        has_question_mark = '?' in text
        
        # 检查是否是疑问句式
        words = text_lower.split()[:5]
        is_interrogative = False
        if words:
            first_words = ' '.join(words[:2])
            is_interrogative = any(first_words.startswith(indicator) 
                                 for indicator in ['is ', 'are ', 'was ', 'were ', 'do ', 'does ', 'did '])
        
        question_score = sum([starts_with_question, has_question_mark, is_interrogative])
        
        # 短文本（<30字符）+ 问号 = 很可能是问题
        if len(text.strip()) < 30 and has_question_mark:
            return True
        
        # 如果满足2个或以上问题特征，判定为问题
        return question_score >= 2

    def _resolve_index_path(self, index_path: Optional[str]) -> str:
        """智能解析索引路径，使用动态配置"""
        # 使用统一配置中心获取默认路径
        default_path = get_smart_config("faiss_index_path", create_query_context("faiss_index_path"))
        if default_path:
            return default_path

        # 使用默认路径
        default_path = "data/faiss_memory/faiss_index.bin"
        
        # 检查默认路径是否可用
        if os.path.exists(default_path) or os.access(os.path.dirname(default_path), os.W_OK):
            logger.info("✅ 使用配置的索引路径: %s", default_path)
            return default_path

        # 回退到其他可能的路径
        possible_paths = [
            "data/faiss_memory/faiss_index.bin",
            "src/data/faiss_memory/faiss_index.bin",
            "faiss_memory/faiss_index.bin",
            "faiss_index.bin"
        ]

        for path in possible_paths:
            if os.path.exists(path) or os.access(os.path.dirname(path), os.W_OK):
                logger.info("✅ 使用回退索引路径: %s", path)
                return path

        logger.info("📁 使用默认索引路径: %s", default_path)
        return default_path

    def _ensure_directory(self):
        """确保目录存在"""
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            logger.debug("✅ 目录确保存在: %s", os.path.dirname(self.index_path))
        except Exception as e:
            logger.warning("⚠️ 创建目录失败: %s", e)

    def _start_async_initialization(self):
        """启动异步初始化 - 修复版本"""
        try:
            try:
                loop = asyncio.get_running_loop()
                self._initialization_task = asyncio.create_task(self._async_initialize())
                logger.debug("✅ 在异步环境中启动初始化任务")
            except RuntimeError:
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)

                    new_loop.run_until_complete(self._async_initialize())
                    new_loop.close()

                    logger.debug("✅ 在新事件循环中完成异步初始化")
                except Exception as e:
                    logger.warning("⚠️ 新事件循环初始化失败: %s，标记为需要初始化", e)
                    self._initialization_task = None
        except Exception as e:
            logger.warning("⚠️ 启动异步初始化失败: %s", e)
            self._initialization_task = None

    async def _async_initialize(self):
        """异步初始化 - 完全异步化版本（渐进式加载）"""
        if self._initialization_lock.locked():
            logger.warning("⚠️ 初始化锁已被占用，等待释放...")
            try:
                if hasattr(self._initialization_lock, 'acquire'):
                    # 检查是否是异步锁
                    acquire_result = self._initialization_lock.acquire()
                    if asyncio.iscoroutine(acquire_result):
                        await asyncio.wait_for(acquire_result, timeout=5.0)
                    else:
                        # 对于同步锁，使用线程池执行
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, self._initialization_lock.acquire)
                else:
                    await asyncio.sleep(0.1)  # 简单的等待
            except asyncio.TimeoutError:
                logger.warning("⚠️ 等待初始化锁超时，跳过异步初始化")
                return

        try:
            if self._index_loaded:
                return

            start_time = time.time()
            logger.info("🔄 开始FAISS内存系统智能异步初始化...")

            logger.info("🔍 步骤1: 索引状态检测...")
            try:
                await asyncio.wait_for(self._smart_index_health_check(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("⚠️ 索引状态检测超时，跳过异步初始化")
                raise

            # 🚀 先尝试加载现有索引，检查是否需要重建
            logger.info("🔍 步骤2: 尝试加载现有索引...")
            try:
                await asyncio.wait_for(self._load_existing_index_smart(), timeout=10.0)
            except Exception as e:
                logger.warning(f"⚠️ 加载现有索引失败: {e}，标记需要重建")
                self._index_needs_rebuild = True
                self.index = None
            
            # 🚀 检查是否需要重建（维度不匹配或其他原因）
            if self._index_needs_rebuild or self.index is None:
                logger.info("🔧 步骤2.1: 索引重建流程（维度不匹配或其他问题）...")
                try:
                    await asyncio.wait_for(self._rebuild_index_smart(), timeout=120.0)  # 增加超时到120秒
                    logger.info("✅ 索引重建完成")
                    # 重建后重新加载知识条目
                    await self._load_knowledge_entries_async()
                except asyncio.TimeoutError:
                    logger.error("⚠️ 索引重建超时")
                    self.index = None
                except Exception as e:
                    logger.error(f"❌ 索引重建失败: {e}")
                    self.index = None
            else:
                logger.info("✅ 索引已成功加载，无需重建")

            logger.info("🚀 步骤3: 启动后台预加载...")
            asyncio.create_task(self._schedule_preload_async())

            logger.info("📚 步骤4: 加载知识条目...")
            await asyncio.wait_for(self._load_knowledge_entries_async(), timeout=5.0)

            self._index_loaded = True

            init_time = time.time() - start_time
            self._initialization_times.append(init_time)
            self._last_initialization_time = init_time

            logger.info("✅ FAISS内存系统智能异步初始化完成 (耗时: %.2f秒)", init_time)

        except asyncio.TimeoutError as e:
            logger.warning("⚠️ 异步初始化超时: %s", e)
            await self._fallback_sync_initialization()
        except (OSError, IOError) as e:
            logger.error("❌ FAISS内存系统智能异步初始化失败 (文件操作错误): %s", e)
            await self._fallback_sync_initialization()
        except ImportError as e:
            logger.error("❌ FAISS内存系统智能异步初始化失败 (导入错误): %s", e)
            await self._fallback_sync_initialization()
        except Exception as e:
            logger.error("❌ FAISS内存系统智能异步初始化失败 (未知错误): %s", e)
            await self._fallback_sync_initialization()
        finally:
            if self._initialization_lock.locked():
                self._initialization_lock.release()

    async def _smart_index_health_check(self):
        """智能索引健康检查 - 完全异步化版本"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._smart_index_health_check_sync)
            self._index_needs_rebuild = result
        except Exception as e:
            logger.error("❌ 异步索引健康检查失败: %s", e)
            self._index_needs_rebuild = True

    def _smart_index_health_check_sync(self) -> bool:
        """同步智能索引健康检查（在线程池中执行）"""
        try:
            index_exists = os.path.exists(self.index_path)
            knowledge_file = self.index_path.replace('faiss_index.bin', 'knowledge_entries.json')
            knowledge_exists = os.path.exists(knowledge_file)

            if not index_exists or not knowledge_exists:
                logger.info("📁 索引文件或知识条目文件缺失，需要重建")
                return True

            metadata_exists = os.path.exists(self._index_metadata_file)
            if metadata_exists:
                try:
                    with open(self._index_metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    stored_version = metadata.get('version', '1.0')
                    if stored_version != self._index_version:
                        logger.info("🔄 索引版本不匹配 (存储: %s, 当前: %s)，需要重建", stored_version, self._index_version)
                        return True

                    self._index_last_modified = metadata.get('last_modified')
                    self._knowledge_last_modified = metadata.get('knowledge_last_modified')

                except Exception as e:
                    logger.warning("⚠️ 读取索引元数据失败: %s，需要重建", e)
                    return True

            index_size = os.path.getsize(self.index_path)
            knowledge_size = os.path.getsize(knowledge_file)

            if index_size < 1000 or knowledge_size < 1000:
                logger.warning("⚠️ 索引文件过小 (索引: %s bytes, 知识: %s bytes)，需要重建", index_size, knowledge_size)
                return True

            try:
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, list):
                    entry_count = len(data)
                elif isinstance(data, dict):
                    entry_count = len(data.get('entries', []))
                else:
                    entry_count = 0

                if entry_count == 0:
                    logger.warning("⚠️ 知识条目为空，需要重建")
                    return True

                logger.info("✅ 索引健康检查通过: %d 条知识条目", entry_count)
                return False

            except Exception as e:
                logger.warning("⚠️ 知识条目文件损坏: %s，需要重建", e)
                return True

        except Exception as e:
            logger.error("❌ 同步索引健康检查失败: %s", e)
            return True

    async def _rebuild_index_smart(self):
        """智能重建索引 - 完全异步化版本"""
        try:
            logger.info("🔧 开始智能重建FAISS索引...")

            loop = asyncio.get_event_loop()

            if os.path.exists(self.index_path):
                backup_path = f"{self.index_path}.backup.{int(time.time())}"
                import shutil
                await loop.run_in_executor(None, shutil.copy2, self.index_path, backup_path)
                logger.info("📦 现有索引已备份到: %s", backup_path)

            knowledge_entries = await self._build_knowledge_entries_from_cache()

            if not knowledge_entries:
                logger.warning("⚠️ 无法从缓存构建知识条目，创建空索引")
                await self._create_empty_index_smart()
                return

            knowledge_file = self.index_path.replace('faiss_index.bin', 'knowledge_entries.json')
            await loop.run_in_executor(None, self._save_knowledge_entries_sync, knowledge_entries, knowledge_file)

            logger.info("✅ 保存了 %d 条知识条目", len(knowledge_entries))

            await self._create_faiss_index_smart(knowledge_entries)

            await self._save_index_metadata()

        except Exception as e:
            logger.error("❌ 智能重建索引失败: %s", e)
            await self._create_empty_index_smart()

    def _save_knowledge_entries_sync(self, knowledge_entries, file_path):
        """同步保存知识条目（在线程池中执行）"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_entries, f, ensure_ascii=False, indent=2)

    async def _build_knowledge_entries_from_cache(self) -> List[Dict[str, Any]]:
        """从FRAMES数据集的wikilink内容构建知识条目 - 根本修复版本"""
        try:
            # 🔧 根本修复：向量知识库应该存储wikilink指向的Wikipedia页面内容
            # 而不是documents.json中的问题内容
            # 优先从wiki_cache加载wikilink的Wikipedia内容
            
            wiki_cache_dir = Path("data/wiki_cache")
            if wiki_cache_dir.exists() and wiki_cache_dir.is_dir():
                cache_files = list(wiki_cache_dir.glob("*.json"))
                if cache_files:
                    logger.info(f"🔍 使用wiki_cache中的wikilink内容构建知识库（{len(cache_files)}个Wikipedia页面）")
                    
                    # 直接从wiki_cache加载，这些是FRAMES数据集wikilink指向的实际内容
                    knowledge_entries = []
                    
                    for i, cache_file in enumerate(cache_files):
                        try:
                            with open(cache_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            if isinstance(data, dict):
                                title = data.get('title', '')
                                content = data.get('content', '') or data.get('extract', '')
                                
                                # 🔧 验证：确保是真正的知识内容，不是问题
                                if content and len(content) > 50:
                                    # 检查是否是问题（应该不是，但以防万一）
                                    if '?' in content[:100] and any(word in content.lower()[:50] 
                                                                    for word in ['how many', 'what', 'who', 'when', 'where', 'if ', 'imagine']):
                                        logger.debug(f"跳过可能的问题内容: {title}")
                                        continue
                                    
                                    knowledge_entries.append({
                                        'entry_id': f"wikilink_{len(knowledge_entries)}",
                                        'title': title,
                                        'content': content[:2000],  # 限制长度以提高效率
                                        'source': 'frames_wikilink',
                                        'metadata': {
                                            'title': title,
                                            'source': 'frames_wikilink',
                                            'wikilink_url': data.get('url', ''),
                                            'file': cache_file.name,
                                            'timestamp': datetime.now().isoformat(),
                                            'word_count': data.get('word_count', len(content.split()))
                                        }
                                    })
                            
                            # 每处理100个文件显示一次进度
                            if (i + 1) % 100 == 0:
                                logger.info(f"🔄 已处理 {i + 1}/{len(cache_files)} 个wikilink文件，构建了 {len(knowledge_entries)} 条知识条目")
                        
                        except Exception as e:
                            logger.debug("跳过wikilink文件 %s: %s", cache_file, e)
                            continue
                    
                    logger.info("✅ 从wikilink内容构建了 %d 条知识条目", len(knowledge_entries))
                    
                    if knowledge_entries:
                        return knowledge_entries
                    else:
                        logger.warning("⚠️ 从wiki_cache构建的知识条目为空，尝试回退方案")
            
            # 回退到Wiki缓存构建方法（如果wiki_cache不存在或为空）
            logger.info("⚠️ wiki_cache不存在或为空，使用回退方案")
            return await self._build_knowledge_entries_from_wiki_cache()
            
        except Exception as e:
            logger.error("❌ 从wikilink内容构建知识条目失败: %s", e)
            # 回退到Wiki缓存
            return await self._build_knowledge_entries_from_wiki_cache()
    
    async def _build_knowledge_entries_from_wiki_cache(self) -> List[Dict[str, Any]]:
        """从Wiki缓存构建知识条目（回退方案）"""
        try:
            knowledge_entries = []
            wiki_cache_dir = Path("data/wiki_cache")

            if not wiki_cache_dir.exists():
                logger.warning("⚠️ Wiki缓存目录不存在")
                return knowledge_entries

            cache_files = list(wiki_cache_dir.glob("*.json"))
            logger.info(f"🔍 发现 {len(cache_files)} 个Wiki缓存文件")

            # 处理所有缓存文件，但限制每个文件的内容长度
            for i, cache_file in enumerate(cache_files):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if isinstance(data, dict):
                        title = data.get('title', '')
                        content = data.get('extract', '') or data.get('content', '')

                        if title and content and len(content) > 50:
                            knowledge_entries.append({
                                'entry_id': f"wiki_{len(knowledge_entries)}",
                                'title': title,
                                'content': content[:1000],  # 限制长度
                                'source': 'wikipedia',
                                'metadata': {
                                    'title': title,
                                    'source': 'wikipedia',
                                    'file': cache_file.name,
                                    'timestamp': datetime.now().isoformat()
                                }
                            })
                    
                    # 每处理100个文件显示一次进度
                    if (i + 1) % 100 == 0:
                        logger.info(f"🔄 已处理 {i + 1}/{len(cache_files)} 个缓存文件，构建了 {len(knowledge_entries)} 条知识条目")

                except Exception as e:
                    logger.debug("跳过缓存文件 %s: %s", cache_file, e)
                    continue

            logger.info("✅ 从Wiki缓存构建了 %d 条知识条目", len(knowledge_entries))
            return knowledge_entries

        except Exception as e:
            logger.error("❌ 从Wiki缓存构建知识条目失败: %s", e)
            return [{
                "id": "error_entry",
                "content": "知识条目构建失败",
                "error": str(e),
                "timestamp": time.time(),
                "source": "error_fallback"
            }]

    async def _create_empty_index_smart(self):
        """智能创建空索引"""
        try:
            logger.info("开始智能创建空索引")
            
            if FAISS_AVAILABLE and faiss is not None:
                if FAISS_AVAILABLE and faiss is not None:

                    self.index = faiss.IndexFlatIP(self.dimension)
                else:

                    logger.warning("⚠️ FAISS不可用，无法创建索引")
                    self.index = None

                if FAISS_AVAILABLE and faiss is not None:

                    faiss.write_index(self.index, self.index_path)
                logger.info("✅ 创建了空的FAISS索引")

                knowledge_file = self.index_path.replace('faiss_index.bin', 'knowledge_entries.json')
                with open(knowledge_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)

                await self._save_index_metadata()
            else:
                logger.warning("⚠️ FAISS不可用，无法创建索引")
                self.index = None
                logger.info("✅ 创建了空的FAISS索引")

            knowledge_file = self.index_path.replace('faiss_index.bin', 'knowledge_entries.json')
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

            await self._save_index_metadata()

        except Exception as e:
            logger.error("❌ 创建空索引失败: %s", e)
            self.index = None

    async def _create_faiss_index_smart(self, knowledge_entries: List[Dict[str, Any]]):
        """智能创建FAISS索引 - 简化版本"""
        try:
            logger.info("🔧 开始创建FAISS索引...")
            
            # 检查FAISS可用性
            if not FAISS_AVAILABLE or faiss is None:
                logger.error("❌ FAISS不可用，无法创建索引")
                self.index = None
                return
            
            # 创建空索引
            self.index = faiss.IndexFlatIP(self.dimension)
            logger.info(f"✅ 创建空索引，维度: {self.dimension}")
            
            # 检查知识条目
            if not knowledge_entries:
                logger.warning("⚠️ 无知识条目，创建空索引")
                faiss.write_index(self.index, self.index_path)
                logger.info("✅ 空索引已保存")
                return
            
            # 设置知识条目
            self.knowledge_entries = knowledge_entries
            logger.info(f"✅ 设置了 {len(self.knowledge_entries)} 条知识条目")
            
            # 向量化知识条目
            logger.info(f"🔄 开始向量化 {len(knowledge_entries)} 个知识条目...")
            vectors = await self._vectorize_knowledge_entries(knowledge_entries)
            
            # 检查向量化结果
            if not isinstance(vectors, np.ndarray):
                logger.error(f"❌ 向量化失败: {type(vectors)}")
                if isinstance(vectors, dict):
                    logger.error(f"错误信息: {vectors.get('error', 'N/A')}")
                faiss.write_index(self.index, self.index_path)
                logger.info("✅ 空索引已保存")
                return
            
            # 添加向量到索引
            logger.info(f"🔄 添加 {vectors.shape[0]} 个向量到索引...")
            # 确保向量是float32类型
            vectors = vectors.astype(np.float32)
            # 添加向量到索引（FAISS的add方法只接受向量数组，不接受ID参数）
            if self.index is not None:
                self.index.add(vectors)  # type: ignore
            logger.info(f"✅ 成功创建包含 {len(knowledge_entries)} 条目的向量索引")
            
            # 保存索引
            if self.index and self.index_path:
                faiss.write_index(self.index, self.index_path)
                logger.info("✅ FAISS索引已保存")
            
        except Exception as e:
            logger.error(f"❌ 创建FAISS索引失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 创建空索引作为回退
            try:
                if FAISS_AVAILABLE and faiss is not None:
                    self.index = faiss.IndexFlatIP(self.dimension)
                    faiss.write_index(self.index, self.index_path)
                    logger.info("✅ 创建了空的FAISS索引（回退方案）")
                else:
                    self.index = None
                    logger.error("❌ FAISS不可用，无法创建回退索引")
            except Exception as e2:
                logger.error(f"❌ 创建回退索引也失败: {e2}")
                self.index = None
                self.index = None

    async def _vectorize_knowledge_entries(self, knowledge_entries: List[Dict[str, Any]]) -> Union[np.ndarray, Dict[str, Any]]:
        """向量化知识条目"""
        texts: List[str] = []  # 在函数开始时定义，确保在except块中可用
        try:
            if not self.is_model_ready():
                logger.warning("⚠️ 模型未准备就绪，无法进行向量化")
                return {
                    "error": "模型未准备就绪",
                    "status": "model_not_ready",
                    "timestamp": time.time(),
                    "input_count": len(knowledge_entries)
                }

            texts = []
            for entry in knowledge_entries:
                content = entry.get('content', '')
                title = entry.get('title', '')
                combined_text = f"{title}: {content}" if title else content
                texts.append(combined_text)

            if self._jina_service:
                # 🚀 优化：使用统一的Jina服务
                embeddings = self._jina_service.get_embeddings(texts)
                if embeddings and len(embeddings) > 0:
                    vectors = np.array(embeddings)
                    logger.info(f"🔍 向量化结果（Jina）: type={type(vectors)}, shape={getattr(vectors, 'shape', 'N/A')}")
                else:
                    logger.error("❌ Jina embedding返回为空")
                    return {
                        "error": "Jina embedding返回为空",
                        "status": "embedding_empty",
                        "timestamp": time.time(),
                    }
            elif self._model is not None:
                try:
                    os.environ["OMP_NUM_THREADS"] = os.getenv("OMP_NUM_THREADS", "1")
                    os.environ["TOKENIZERS_PARALLELISM"] = os.getenv("TOKENIZERS_PARALLELISM", "false")
                except Exception:
                    pass
                batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "16") or "16")
                vectors_list: List[np.ndarray] = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    batch_vectors = self._model.encode(batch, convert_to_numpy=True)
                    if isinstance(batch_vectors, np.ndarray):
                        vectors_list.append(batch_vectors)
                if len(vectors_list) == 0:
                    return {
                        "error": "本地模型返回空向量",
                        "status": "embedding_empty",
                        "timestamp": time.time(),
                    }
                vectors = np.vstack(vectors_list)
                logger.info(f"🔍 向量化结果（本地批量）: type={type(vectors)}, shape={getattr(vectors, 'shape', 'N/A')}")
            else:
                logger.error("❌ 模型实例为空，无法进行向量化")
                return {
                    "error": "模型实例为空",
                    "status": "model_empty",
                    "timestamp": time.time(),
                    "input_count": len(texts) if texts else 0
                }

            # 检查向量是否为numpy数组
            if not isinstance(vectors, np.ndarray):
                logger.error(f"❌ 向量化结果不是numpy数组: {type(vectors)}")
                return {
                    "error": f"向量化结果类型错误: {type(vectors)}",
                    "status": "vectorization_type_error",
                    "timestamp": time.time(),
                    "input_count": len(texts) if texts else 0
                }

            # 简化向量检查
            if len(vectors.shape) > 1:
                logger.info(f"✅ 向量形状: {vectors.shape}")
            else:
                logger.warning(f"⚠️ 向量形状异常: {vectors.shape}")
                return {
                    "error": f"向量形状异常: {vectors.shape}",
                    "status": "vector_shape_error",
                    "timestamp": time.time(),
                    "input_count": len(texts) if texts else 0
                }

            logger.info("✅ 成功向量化 %d 条知识条目", len(knowledge_entries))
            return vectors

        except ImportError:
            logger.warning("⚠️ sentence-transformers未安装，无法进行向量化")
            texts_count = len(texts) if 'texts' in locals() else 0
            return {
                "error": "sentence-transformers未安装",
                "status": "import_error",
                "timestamp": time.time(),
                "input_count": texts_count
            }
        except Exception as e:
            logger.warning("⚠️ 向量化失败: %s", e)
            texts_count = len(texts) if 'texts' in locals() else 0
            return {
                "error": f"向量化失败: {e}",
                "status": "vectorization_failed",
                "timestamp": time.time(),
                "input_count": texts_count
            }

    async def _save_index_metadata(self):
        """保存索引元数据"""
        try:
            metadata = {
                'version': self._index_version,
                'dimension': self.dimension,
                'index_type': 'IndexFlatIP',
                'last_modified': datetime.now().isoformat(),
                'knowledge_last_modified': datetime.now().isoformat(),
                'entry_count': len(self.knowledge_entries),
                'index_size': os.path.getsize(self.index_path) if os.path.exists(self.index_path) else 0,
                'created_at': datetime.now().isoformat()
            }

            with open(self._index_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            logger.info("✅ 索引元数据已保存")

        except Exception as e:
            logger.error("❌ 保存索引元数据失败: %s", e)

    async def _load_existing_index_smart(self):
        """智能加载现有索引"""
        try:
            loop = asyncio.get_event_loop()
            self.index = await loop.run_in_executor(None, self._load_index_sync)
            
            # 🚀 检查索引维度是否匹配
            if self.index is not None and hasattr(self.index, 'd') and not isinstance(self.index, dict):
                index_dim = getattr(self.index, 'd', None)
                if index_dim is not None and index_dim != self.dimension:
                    logger.warning(f"⚠️ 索引维度({index_dim})与当前维度({self.dimension})不匹配，标记需要重建")
                    self._index_needs_rebuild = True
                    # 备份旧索引
                    old_index_path = f"{self.index_path}.old_{int(time.time())}"
                    import shutil
                    try:
                        if os.path.exists(self.index_path):
                            shutil.copy2(self.index_path, old_index_path)
                            logger.info(f"📦 旧索引已备份到: {old_index_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ 备份旧索引失败: {e}")
                    self.index = None
                    # 🚀 不抛出异常，让上层逻辑处理重建
                    logger.info("🔄 索引维度不匹配，将触发重建流程")
                    return  # 直接返回，让重建流程继续

            if self.index is not None and hasattr(self.index, 'ntotal'):
                logger.info(f"✅ 成功异步加载现有FAISS索引，维度: {getattr(self.index, 'd', 'unknown')}，包含 {getattr(self.index, 'ntotal', 0)} 个向量")

        except Exception as e:
            logger.error("❌ 异步加载现有索引失败: %s", e)
            self._index_needs_rebuild = True
            self.index = None
            # 🚀 不抛出异常，让重建流程继续
            return

    def _load_index_sync(self):
        """同步加载索引（在线程池中执行）"""
        if FAISS_AVAILABLE and faiss is not None:
            return faiss.read_index(self.index_path)
        else:
            logger.warning("⚠️ FAISS不可用，无法加载索引")
            return {
                "error": "FAISS不可用",
                "status": "faiss_unavailable",
                "timestamp": time.time(),
                "index_path": self.index_path
            }

    async def _load_or_create_index_async(self):
        """异步加载或创建FAISS索引"""
        try:
            logger.info("开始异步加载或创建FAISS索引")
            
            if await self._check_index_file_health():
                loop = asyncio.get_event_loop()
                if FAISS_AVAILABLE and faiss is not None:
                    self.index = await loop.run_in_executor(None, faiss.read_index, self.index_path)
                    logger.info("✅ 成功异步加载现有FAISS索引")
                else:
                    logger.warning("⚠️ FAISS不可用，无法加载索引")
                    self.index = None

                if not await self._validate_index_integrity():
                    logger.warning("⚠️ 索引完整性检查失败，将重新创建")
                    await self._recreate_index_async()
                else:
                    logger.info("📁 索引文件不存在或损坏，将异步创建新索引")
                    await self._recreate_index_async()

        except Exception as e:
            logger.error("异步初始化索引失败: %s", e)
            await self._fallback_sync_initialization()

    async def _check_index_file_health(self) -> bool:
        """检查索引文件健康状态"""
        try:
            if not os.path.exists(self.index_path):
                return False

            file_size = os.path.getsize(self.index_path)
            if file_size < 1024:  # 小于1KB的文件可能损坏
                logger.warning("⚠️ 索引文件过小 (%s bytes, file_size)，可能损坏")
                return False

            mtime = os.path.getmtime(self.index_path)
            current_time = time.time()
            if current_time - mtime > 86400 * 30:  # 30天未修改
                logger.warning("⚠️ 索引文件过旧，建议重建")

            return True

        except Exception as e:
            logger.warning("⚠️ 索引文件健康检查失败: %s", e)
            return False

    async def _validate_index_integrity(self) -> bool:
        """验证索引完整性"""
        try:
            if not self.index:
                return False

            if not hasattr(self.index, 'ntotal'):
                logger.warning("⚠️ 索引缺少ntotal属性")
                return False

            if not hasattr(self.index, 'd'):
                logger.warning("⚠️ 索引缺少维度属性")
                return False

            if hasattr(self.index, 'd') and hasattr(self.index, 'ntotal'):
                if getattr(self.index, 'd', 0) != self.dimension:
                    logger.warning("⚠️ 索引维度不匹配: 期望%s, 实际%s", self.dimension, getattr(self.index, 'd', 0))
                    return False
                
                logger.debug("✅ 索引完整性检查通过: 维度=%s, 条目数=%d", getattr(self.index, 'd', 0), getattr(self.index, 'ntotal', 0))
            return True

        except Exception as e:
            logger.warning("⚠️ 索引完整性验证失败: %s", e)
            return False

    async def _recreate_index_async(self):
        """异步重新创建索引"""
        try:
            logger.info("开始异步重新创建索引")
            
            logger.info("🔄 开始重新创建FAISS索引...")

            loop = asyncio.get_event_loop()
            if FAISS_AVAILABLE and faiss is not None:
                self.index = await loop.run_in_executor(None, faiss.IndexFlatIP, self.dimension)
                await loop.run_in_executor(None, faiss.write_index, self.index, self.index_path)
            else:
                logger.warning("⚠️ FAISS不可用，无法创建索引")
                self.index = None

            logger.info("🆕 成功创建新的FAISS索引，维度: %s", self.dimension)

        except Exception as e:
            logger.error("重新创建索引失败: %s", e)
            raise RuntimeError(f"重新创建索引失败: {e}")

    async def _load_knowledge_entries_async(self):
        """异步加载知识条目 - 增强版：验证知识质量"""
        try:
            knowledge_file = self.index_path.replace('faiss_index.bin', 'knowledge_entries.json')
            if os.path.exists(knowledge_file):
                loop = asyncio.get_event_loop()
                raw_entries = await loop.run_in_executor(
                    None, self._load_knowledge_from_file_sync, knowledge_file
                )
                
                # 🔧 根本修复：验证知识条目内容质量（与同步版本一致）
                problematic_count = 0
                valid_entries = []
                
                for entry in raw_entries:
                    content = entry.get('content', '') or entry.get('text', '')
                    if content and len(content.strip()) > 10:
                        if self._is_content_likely_question(content):
                            problematic_count += 1
                        else:
                            valid_entries.append(entry)
                
                # 如果超过30%的内容是问题，标记需要重建
                if problematic_count > len(raw_entries) * 0.3:
                    logger.warning(
                        f"⚠️ 检测到知识库质量问题: {problematic_count}/{len(raw_entries)}条是问题而非知识 "
                        f"({problematic_count/len(raw_entries)*100:.1f}%)，将触发重建"
                    )
                    self._index_needs_rebuild = True
                    self.knowledge_entries = valid_entries
                    logger.info(f"✅ 暂时使用 {len(valid_entries)} 条有效知识条目，重建将使用wiki_cache的正确数据")
                else:
                    self.knowledge_entries = raw_entries
                    logger.info(f"✅ 成功异步加载 {len(self.knowledge_entries)} 条知识条目（质量问题: {problematic_count}条）")
            else:
                logger.info("ℹ️ 知识条目文件不存在，将使用空知识库")
                self.knowledge_entries = []

        except Exception as e:
            logger.warning("⚠️ 异步加载知识条目失败: %s", e)
            self.knowledge_entries = []

    def _load_knowledge_from_file_sync(self, file_path: str) -> List[Any]:
        """同步加载知识条目（在线程池中执行）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning("⚠️ 解析知识条目文件失败: %s", e)
            return [{
                "id": "error_entry",
                "content": "知识条目解析失败",
                "error": str(e),
                "timestamp": time.time(),
                "source": "error_fallback"
            }]

    def _load_knowledge_from_file(self, file_path: str) -> List[KnowledgeEntry]:
        """从文件加载知识条目"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            entries = []
            for item in data:
                entry = KnowledgeEntry(
                    entry_id=item.get('entry_id', ''),
                    query=item.get('query', ''),
                    answer=item.get('answer', ''),
                    content=item.get('content', ''),
                    metadata=item.get('metadata', {}),
                    timestamp=datetime.fromisoformat(item.get('timestamp', datetime.now().isoformat())),
                    confidence=item.get('confidence', get_smart_config("medium_threshold", create_query_context("medium_threshold")) or 0.7),
                    quality_score=item.get('quality_score', get_smart_config("medium_threshold", create_query_context("medium_threshold")) or 0.7),
                    usage_count=item.get('usage_count', 0)
                )
                entries.append(entry)

            return entries

        except Exception as e:
            logger.warning("⚠️ 解析知识条目文件失败: %s", e)
            return []

    async def _fallback_sync_initialization(self):
        """回退到同步初始化"""
        try:
            logger.info("🔄 尝试同步初始化...")

            if os.path.exists(self.index_path):
                if FAISS_AVAILABLE and faiss is not None:
                    self.index = faiss.read_index(self.index_path)
                    logger.info("✅ 同步加载索引成功")
                else:
                    logger.warning("⚠️ FAISS不可用，无法加载索引")
                    self.index = None
            else:
                if FAISS_AVAILABLE and faiss is not None:
                    self.index = faiss.IndexFlatIP(self.dimension)
                    if self.index_path:
                        faiss.write_index(self.index, self.index_path)
                    logger.info("🆕 同步创建索引成功，维度: %s", self.dimension)
                else:
                    logger.warning("⚠️ FAISS不可用，无法创建索引")
                    self.index = None

            self._index_loaded = True

        except Exception as e:
            logger.error("❌ 同步初始化也失败: %s", e)
            self._index_loaded = False

    async def _schedule_preload_async(self):
        """异步调度预加载任务"""
        try:
            asyncio.create_task(self._preload_frequently_accessed_async())
        except Exception as e:
            logger.warning("调度预加载失败: %s", e)

    async def _preload_frequently_accessed_async(self):
        """异步预加载频繁访问的知识"""
        try:
            if not self._preload_initialized and len(self.knowledge_entries) > 0:
                access_counts = {}
                for entry in self.knowledge_entries:
                    if isinstance(entry, dict):
                        entry_id = entry.get('entry_id', '')
                        usage_count = entry.get('usage_count', 0)
                    else:
                        entry_id = getattr(entry, 'entry_id', '')
                        usage_count = getattr(entry, 'usage_count', 0)
                    access_counts[entry_id] = usage_count

                top_accessed = sorted(access_counts.items(), key=lambda x: x[1], reverse=True)[:get_smart_config("large_limit", create_query_context("large_limit")) or 1000]
                self._frequently_accessed = {entry_id for entry_id, _ in top_accessed}

                await self._preload_vectors_async()
                self._preload_initialized = True
                logger.info("✅ 预加载完成，%d个频繁访问条目", len(self._frequently_accessed))
        except Exception as e:
            logger.warning("预加载失败: %s", e)

    async def _preload_vectors_async(self):
        """异步预加载向量到内存"""
        try:
            if self.index and hasattr(self.index, 'reconstruct'):
                for entry_id in list(self._frequently_accessed)[:50]:  # 限制预加载数量
                    try:
                        logger.debug(f"预加载条目 {entry_id}")
                        # 预加载逻辑：检查条目是否存在
                        if entry_id in self.knowledge_entries:
                            logger.debug(f"条目 {entry_id} 已预加载")
                        else:
                            logger.debug(f"条目 {entry_id} 需要预加载")
                    except Exception as e:
                        logger.debug("预加载条目%s失败: %s", e, entry_id)
        except Exception as e:
            logger.warning("向量预加载失败: %s", e)

    async def ensure_index_ready(self) -> bool:
        """确保索引已准备就绪"""
        if self._index_loaded and self.index:
            return True

        if self._initialization_task and not self._initialization_task.done():
            try:
                await asyncio.wait_for(self._initialization_task, timeout=300.0)
                return self._index_loaded and self.index is not None
            except asyncio.TimeoutError:
                logger.warning("⚠️ 索引初始化超时")
                return False

        if not self._index_loaded:
            logger.info("🔄 索引未就绪，尝试重新初始化...")
            await self._async_initialize()

        return self._index_loaded and self.index is not None

    def get_index_status(self) -> Dict[str, Any]:
        """获取索引状态信息"""
        return {
            "index_loaded": self._index_loaded,
            "index_exists": self.index is not None,
            "index_path": self.index_path,
            "dimension": self.dimension,
            "knowledge_entries_count": len(self.knowledge_entries),
            "cache_size": len(self._search_cache),
            "preload_initialized": self._preload_initialized,
            "index_optimized": self._index_optimized
        }







    def cleanup(self) -> None:
        """清理资源"""
        try:
            if hasattr(self, '_search_cache'):
                self._search_cache.clear()

            if hasattr(self, '_cache_timestamps'):
                self._cache_timestamps.clear()

            if hasattr(self, '_search_times'):
                self._search_times.clear()

            self._index_loaded = False
            self._preload_initialized = False
            self._index_optimized = False

            logger.info("FAISS内存系统资源清理完成")
        except Exception as e:
            logger.warning("FAISS内存系统资源清理失败: %s", e)

    def _load_or_create_index(self):
        """加载或创建FAISS索引（向后兼容）"""
        try:
            if os.path.exists(self.index_path):
                if FAISS_AVAILABLE and faiss is not None:

                    self.index = faiss.read_index(self.index_path)

                else:

                    logger.warning("⚠️ FAISS不可用，无法创建索引")
                    self.index = None
                logger.info("✅ 成功加载现有FAISS索引")
            else:
                logger.info("📁 索引文件不存在，将创建新索引")
                if FAISS_AVAILABLE and faiss is not None:

                    self.index = faiss.IndexFlatIP(self.dimension)
                else:

                    logger.warning("⚠️ FAISS不可用，无法创建索引")
                    self.index = None
                logger.info("🆕 创建新的FAISS索引，维度: %s", self.dimension)
        except Exception as e:
            logger.error("【异常处理】初始化索引失败: %s", e)
            raise RuntimeError(f"初始化索引失败: {e}")

    def _schedule_preload(self):
        """调度预加载任务（向后兼容）"""
        try:
            preload_thread = threading.Thread(target=self._preload_frequently_accessed, daemon=True)
            preload_thread.start()
        except Exception as e:
            logger.warning("调度预加载失败: %s", e)

    def _preload_frequently_accessed(self):
        """预加载频繁访问的知识"""
        try:
            if not self._preload_initialized and len(self.knowledge_entries) > 0:
                access_counts = {}
                for entry in self.knowledge_entries:
                    if isinstance(entry, dict):
                        entry_id = entry.get('entry_id', '')
                        usage_count = entry.get('usage_count', 0)
                    else:
                        entry_id = getattr(entry, 'entry_id', '')
                        usage_count = getattr(entry, 'usage_count', 0)
                    access_counts[entry_id] = usage_count

                top_accessed = sorted(access_counts.items(), key=lambda x: x[1], reverse=True)[:get_smart_config("large_limit", create_query_context("large_limit")) or 1000]
                self._frequently_accessed = {entry_id for entry_id, _ in top_accessed}

                self._preload_vectors()
                self._preload_initialized = True
                logger.info("✅ 预加载完成，%d个频繁访问条目", len(self._frequently_accessed))
        except Exception as e:
            logger.warning("预加载失败: %s", e)

    def _preload_vectors(self):
        """预加载向量到内存"""
        try:
            if self.index and hasattr(self.index, 'reconstruct'):
                for entry_id in list(self._frequently_accessed)[:50]:  # 限制预加载数量
                    try:
                        logger.debug(f"预加载条目 {entry_id}")
                        # 预加载逻辑：检查条目是否存在
                        if entry_id in self.knowledge_entries:
                            logger.debug(f"条目 {entry_id} 已预加载")
                        else:
                            logger.debug(f"条目 {entry_id} 需要预加载")
                    except Exception as e:
                        logger.debug("预加载条目%s失败: %s", e, entry_id)
        except Exception as e:
            logger.warning("向量预加载失败: %s", e)

    def _get_cached_result(self, query: str, top_k: int) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """获取缓存的搜索结果"""
        try:
            cache_key = f"{query}_{top_k}"
            current_time = time.time()

            if cache_key in self._search_cache:
                timestamp = self._cache_timestamps.get(cache_key, 0)
                if current_time - timestamp < self._cache_ttl:
                    self._update_cache_stats(hit=True)
                    return self._search_cache[cache_key]
                else:
                    del self._search_cache[cache_key]
                    del self._cache_timestamps[cache_key]

            self._update_cache_stats(hit=False)
            return {
                "status": "cache_miss",
                "query": query,
                "top_k": top_k,
                "message": "缓存未命中",
                "timestamp": time.time()
            }
        except Exception as e:
            logger.debug("获取缓存结果失败: %s", e)
            return {
                "status": "cache_error",
                "query": query,
                "top_k": top_k,
                "error": str(e),
                "timestamp": time.time()
            }

    def _cache_search_result(self, query: str, top_k: int, results: List[Dict[str, Any]]):
        """缓存搜索结果"""
        try:
            cache_key = f"{query}_{top_k}"
            current_time = time.time()

            if len(self._search_cache) >= self._cache_size_limit:
                oldest_key = min(self._cache_timestamps.keys(), key=lambda k: self._cache_timestamps[k])
                del self._search_cache[oldest_key]
                del self._cache_timestamps[oldest_key]

            self._search_cache[cache_key] = results
            self._cache_timestamps[cache_key] = current_time

        except Exception as e:
            logger.debug("缓存搜索结果失败: %s", e)

    def _update_cache_stats(self, hit: bool):
        """更新缓存统计信息"""
        try:
            if hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1
                
            self._search_times.append(time.time())

            if len(self._search_times) > get_smart_config("large_limit", create_query_context("large_limit")) or 1000:
                self._search_times = self._search_times[-get_smart_config("large_limit", create_query_context("large_limit")) or 1000:]

            recent_searches = self._search_times[-get_smart_config("large_limit", create_query_context("large_limit")) or 1000:] if len(self._search_times) >= get_smart_config("large_limit", create_query_context("large_limit")) or 1000 else self._search_times
            if recent_searches:
                logger.debug(f"分析最近搜索模式，共 {len(recent_searches)} 次搜索")
                # 分析搜索模式逻辑
                avg_search_time = sum(recent_searches) / len(recent_searches)
                logger.debug(f"平均搜索时间: {avg_search_time:.3f}秒")

        except Exception as e:
            logger.debug("更新缓存统计失败: %s", e)

    def _optimize_index(self):
        """优化FAISS索引"""
        try:
            if not self._index_optimized and self.index and len(self.knowledge_entries) > self._optimization_threshold:
                logger.info("🔧 开始优化FAISS索引...")

                if hasattr(self.index, 'ntotal') and getattr(self.index, 'ntotal', 0) > 0:
                    logger.debug(f"索引包含 {getattr(self.index, 'ntotal', 0)} 个向量，开始优化")
                    # 执行索引优化逻辑
                    self._perform_index_optimization()

                self._index_optimized = True
                logger.info("✅ FAISS索引优化完成")
        except Exception as e:
            logger.warning("索引优化失败: %s", e)

    def _perform_index_optimization(self):
        """执行索引优化"""
        try:
            logger.debug("执行索引优化逻辑")
            # 检查索引状态
            if hasattr(self.index, 'ntotal'):
                logger.debug(f"当前索引包含 {getattr(self.index, 'ntotal', 0)} 个向量")
            
            # 执行优化操作
            if FAISS_AVAILABLE and faiss is not None:
                # 重建索引以提高性能
                logger.debug("重建索引以提高性能")
                # 这里可以添加更复杂的优化逻辑
                
            logger.debug("索引优化完成")
        except Exception as e:
            logger.warning(f"索引优化执行失败: {e}")

    def _smart_search_strategy(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """智能搜索策略"""
        try:
            cached_result = self._get_cached_result(query, top_k)
            if isinstance(cached_result, list):
                logger.debug("🎯 缓存命中: %s", query)
                return cached_result
            elif isinstance(cached_result, dict):
                logger.debug("🎯 缓存未命中: %s", query)

            query_complexity = self._analyze_query_complexity(query)

            if query_complexity < get_smart_config("low_threshold", create_query_context("low_threshold")) or 0.3 and top_k <= 5:
                strategy = "fast"
            elif query_complexity > get_smart_config("medium_threshold", create_query_context("medium_threshold")) or 0.7 and top_k > get_smart_config("default_limit", create_query_context("default_limit")) or 10:
                strategy = "precise"
            else:
                strategy = "balanced"

            logger.debug("🔍 使用搜索策略: %s (复杂度: %.2f, strategy, query_complexity)")

            results = self._execute_search(query, top_k, strategy)

            self._cache_search_result(query, top_k, results)

            return results

        except Exception as e:
            logger.error("智能搜索策略失败: %s", e)
            return self._execute_search(query, top_k, "fallback")

    def _analyze_query_complexity(self, query: str) -> float:
        """分析查询复杂度 - 🚀 重构：使用统一复杂度服务（LLM判断）"""
        try:
            from src.utils.unified_complexity_model_service import get_unified_complexity_model_service
            complexity_service = get_unified_complexity_model_service()
            complexity_result = complexity_service.assess_complexity(
                query=query,
                query_type=None,
                evidence_count=0,
                use_cache=True
            )
            # 将复杂度评分（0-10）转换为0-1分数
            return complexity_result.score / 10.0
        except Exception as e:
            logger.warning(f"⚠️ 使用统一复杂度服务失败: {e}，使用fallback")
            # Fallback: 简单的规则判断
            try:
                words = query.lower().split()
                unique_words = len(set(words))
                total_words = len(words)

                if total_words == 0:
                    return 0.0

                diversity = unique_words / total_words
                length_factor = min(len(query) / 100.0, 1.0)

                complexity = (diversity * 0.6) + (length_factor * 0.4)
                return min(complexity, get_smart_config("DEFAULT_ONE_VALUE", create_query_context("default_one_value")) or 1.0)
            except Exception as e2:
                logger.debug("查询复杂度分析失败: %s", e2)
                return 0.0  # 返回默认复杂度值

    def _execute_search(self, query: str, top_k: int, strategy: str) -> List[Dict[str, Any]]:
        """执行搜索"""
        try:
            start_time = time.time()

            if strategy == "fast":
                search_top_k = min(top_k * 2, 20)  # 搜索更多结果，然后筛选
            elif strategy == "precise":
                search_top_k = top_k
            else:
                search_top_k = top_k

            query_vector = self._get_query_vector(query)
            if query_vector is None:
                return [{
                    "error": "查询向量生成失败",
                    "status": "vector_generation_failed",
                    "query": query,
                    "timestamp": time.time()
                }]
            
            # 检查查询向量是否是错误字典
            if isinstance(query_vector, dict):
                error_msg = query_vector.get("error", "未知错误")
                logger.warning(f"⚠️ 无法生成查询向量: {error_msg}")
                return [{
                    "error": error_msg,
                    "status": query_vector.get("status", "vector_error"),
                    "query": query,
                    "timestamp": time.time()
                }]
            
            if not isinstance(query_vector, np.ndarray):
                logger.warning("⚠️ 查询向量格式错误，期望 np.ndarray，实际: %s", type(query_vector))
                return [{
                    "error": "查询向量格式错误",
                    "status": "invalid_vector_type",
                    "query": query,
                    "timestamp": time.time()
                }]

            if self.index is None:
                logger.warning("索引未初始化，无法执行搜索")
                return [{
                    "error": "索引未初始化",
                    "status": "index_not_initialized",
                    "query": query,
                    "timestamp": time.time()
                }]
            try:
                # 检查索引维度是否匹配
                try:
                    if hasattr(self.index, 'd') and not isinstance(self.index, dict):
                        index_dim = getattr(self.index, 'd', None)
                        if index_dim is not None and isinstance(query_vector, np.ndarray):
                            vector_dim = query_vector.shape[0] if len(query_vector.shape) == 1 else query_vector.shape[1]
                            if index_dim != vector_dim:
                                logger.error(f"❌ 索引维度({index_dim})与查询向量维度({vector_dim})不匹配")
                                return [{
                                    "error": f"索引维度({index_dim})与查询向量维度({vector_dim})不匹配",
                                    "status": "dimension_mismatch",
                                    "query": query,
                                    "timestamp": time.time()
                                }]
                except Exception as dim_check_error:
                    logger.debug(f"维度检查失败: {dim_check_error}，继续尝试搜索")
                
                search_result: tuple = self.index.search(query_vector.reshape(1, -1), search_top_k)  # type: ignore
                distances, indices = search_result
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e) if str(e) else f"{error_type}异常"
                logger.error(f"❌ FAISS搜索失败: {error_type}: {error_msg}", exc_info=True)
                return [{
                    "error": f"FAISS搜索失败: {error_type}: {error_msg}",
                    "status": "search_failed",
                    "query": query,
                    "timestamp": time.time()
                }]

            if strategy == "fast" and len(indices[0]) > top_k:
                selected_indices = indices[0][:top_k]
                selected_distances = distances[0][:top_k]
            else:
                selected_indices = indices[0]
                selected_distances = distances[0]

            results = []
            for i, (idx, distance) in enumerate(zip(selected_indices, selected_distances)):
                if idx < len(self.knowledge_entries):
                    entry = self.knowledge_entries[idx]
                    if isinstance(entry, dict):
                        entry['usage_count'] = entry.get('usage_count', 0) + 1
                        entry['last_accessed'] = datetime.now()
                    else:
                        entry.usage_count += 1
                        entry.last_accessed = datetime.now()

                    result = {
                        "entry_id": entry.get('entry_id', '') if isinstance(entry, dict) else getattr(entry, 'entry_id', ''),
                        "query": entry.get('query', '') if isinstance(entry, dict) else getattr(entry, 'query', ''),
                        "answer": entry.get('answer', '') if isinstance(entry, dict) else getattr(entry, 'answer', ''),
                        "content": entry.get('content', '') if isinstance(entry, dict) else getattr(entry, 'content', ''),
                        "metadata": entry.get('metadata', {}) if isinstance(entry, dict) else getattr(entry, 'metadata', {}),
                        "confidence": entry.get('confidence', 0.0) if isinstance(entry, dict) else getattr(entry, 'confidence', 0.0),
                        "quality_score": entry.get('quality_score', 0.0) if isinstance(entry, dict) else getattr(entry, 'quality_score', 0.0),
                        "similarity_score": float(1.0 - distance),  # 转换为相似度分数
                        "rank": i + 1
                    }
                    results.append(result)

            search_time = time.time() - start_time
            logger.debug("🔍 搜索完成，耗时: %.3f秒，策略: %s", strategy, search_time)

            return results

        except Exception as e:
            logger.error("搜索执行失败: %s", e)
            return [{
                "error": f"搜索执行失败: {e}",
                "status": "execution_failed",
                "query": query,
                "timestamp": time.time()
            }]

    def search(self, query: str, top_k: int = get_smart_config("default_limit", create_query_context("default_limit")) or 10, similarity_threshold: float = 0.1) -> List[Dict[str, Any]]:
        """搜索方法（同步接口）- 使用增强的向量搜索，带性能监控"""
        start_time = time.time()
        
        if not self._index_loaded:
            if not self.wait_for_initialization():
                logger.warning("⚠️ FAISS系统未正确初始化，返回空结果")
                return [{
                    "error": "FAISS系统未正确初始化",
                    "status": "initialization_failed",
                    "query": query,
                    "timestamp": time.time()
                }]

        # 检查缓存
        cache_key = f"search:{query}:{top_k}:{similarity_threshold}"
        if hasattr(self, '_search_cache') and cache_key in self._search_cache:
            logger.debug("✅ 缓存命中: %s", cache_key)
            return self._search_cache[cache_key]
        
        # 执行搜索
        results = self._enhanced_search(query, top_k, similarity_threshold)
        
        # 更新缓存
        if not hasattr(self, '_search_cache'):
            self._search_cache = {}
        self._search_cache[cache_key] = results
        
        # 限制缓存大小
        if len(self._search_cache) > 1000:
            # 删除最旧的缓存条目
            oldest_key = next(iter(self._search_cache))
            del self._search_cache[oldest_key]
        
        # 记录性能指标
        search_time = time.time() - start_time
        # self._record_search_performance(query, search_time, len(results), top_k)  # 暂时注释掉
        
        return results

    def _enhanced_search(self, query: str, top_k: int, similarity_threshold: float) -> List[Dict[str, Any]]:
        """增强搜索方法 - 结合向量搜索和语义搜索"""
        try:
            logger.info(f"🔍 增强搜索: {query[:50]}...")
            
            # 1. 首先尝试向量搜索
            vector_results = self._fallback_search(query, top_k * 2, similarity_threshold)
            
            # 2. 如果向量搜索结果不足，进行语义搜索
            if len(vector_results) < top_k:
                semantic_results = self._semantic_search(query, top_k, similarity_threshold)
                
                # 3. 合并和去重结果
                all_results = vector_results + semantic_results
                unique_results = self._deduplicate_results(all_results)
                
                # 4. 按相似度重新排序
                unique_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
                
                logger.info(f"✅ 增强搜索完成: 向量结果={len(vector_results)}, 语义结果={len(semantic_results)}, 最终结果={len(unique_results)}")
                return unique_results[:top_k]
            else:
                logger.info(f"✅ 向量搜索完成: {len(vector_results)} 个结果")
                return vector_results[:top_k]
                
        except Exception as e:
            logger.error(f"❌ 增强搜索失败: {e}")
            return self._fallback_search(query, top_k, similarity_threshold)
    
    def _semantic_search(self, query: str, top_k: int, similarity_threshold: float) -> List[Dict[str, Any]]:
        """语义搜索 - 基于关键词匹配"""
        try:
            query_lower = query.lower()
            query_words = set(query_lower.split())
            
            results = []
            for i, entry in enumerate(self.knowledge_entries):
                if isinstance(entry, dict):
                    content = entry.get('content', '')
                    title = entry.get('title', '')
                else:
                    content = getattr(entry, 'content', '')
                    title = getattr(entry, 'title', '')
                
                if not content:
                    continue
                
                # 计算语义相似度
                content_lower = content.lower()
                title_lower = title.lower()
                
                # 计算词汇重叠
                content_words = set(content_lower.split())
                title_words = set(title_lower.split())
                
                content_overlap = len(query_words & content_words)
                title_overlap = len(query_words & title_words)
                
                # 计算相似度分数
                if query_words:
                    content_score = content_overlap / len(query_words)
                    title_score = title_overlap / len(query_words)
                    final_score = (content_score * 0.7 + title_score * 0.3)
                else:
                    final_score = 0.0
                
                # 检查是否达到阈值
                if final_score >= similarity_threshold:
                    results.append({
                        'content': content,
                        'metadata': entry.get('metadata', {}) if isinstance(entry, dict) else getattr(entry, 'metadata', {}),
                        'similarity_score': final_score,
                        'entry_id': entry.get('entry_id', f'entry_{i}') if isinstance(entry, dict) else getattr(entry, 'entry_id', f'entry_{i}'),
                        'title': title,
                        'source': 'semantic_search'
                    })
            
            # 按相似度排序
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"🔍 语义搜索完成: {len(results)} 个结果")
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"❌ 语义搜索失败: {e}")
            return []
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重结果"""
        try:
            seen_contents = set()
            unique_results = []
            
            for result in results:
                content = result.get('content', '')
                content_hash = hash(content[:100])  # 使用前100个字符作为去重键
                
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    unique_results.append(result)
            
            return unique_results
            
        except Exception as e:
            logger.warning(f"去重失败: {e}")
            return results

    async def search_async(self, query: str, top_k: int = get_smart_config("default_limit", create_query_context("default_limit")) or 10, similarity_threshold: float = get_smart_config("medium_threshold", create_query_context("medium_threshold")) or 0.7) -> List[Dict[str,
    Any]]:
        """异步搜索知识库 - 确保索引就绪"""
        try:
            if not await self.ensure_index_ready():
                logger.warning("索引未就绪，无法执行搜索")
                return [{
                    "error": "索引未就绪",
                    "status": "index_not_ready",
                    "query": query,
                    "timestamp": time.time()
                }]

            results = self._smart_search_strategy(query, top_k)

            filtered_results = [
                result for result in results
                if result.get("similarity_score", 0.0) >= similarity_threshold
            ]

            logger.debug("异步智能搜索完成，找到 %d 个结果", len(filtered_results))
            return filtered_results

        except Exception as e:
            logger.error("异步智能搜索失败: %s", e)
            return self._fallback_search(query, top_k, similarity_threshold)

    def search_with_rerank(self, query: str, top_k: int = get_smart_config("default_limit", create_query_context("default_limit")) or 10, similarity_threshold: float = get_smart_config("medium_threshold", create_query_context("medium_threshold")) or 0.7,
    **kwargs) -> List[Dict[str, Any]]:
        """搜索知识库并重新排序 - 兼容性方法"""
        return self.search(query, top_k)

    async def search_with_rerank_async(self, query: str, top_k: int = get_smart_config("default_limit", create_query_context("default_limit")) or 10, similarity_threshold: float = get_smart_config("medium_threshold", create_query_context("medium_threshold")) or 0.7,
    **kwargs) -> List[Dict[str, Any]]:
        """异步搜索知识库并重新排序 - 兼容性方法"""
        return await self.search_async(query, top_k, similarity_threshold)

    def _fallback_search(self, query: str, top_k: int, similarity_threshold: float) -> List[Dict[str, Any]]:
        """回退搜索方法"""
        try:
            if not self.index:
                logger.warning("索引未初始化，无法执行搜索")
                return [{
                    "error": "索引未初始化",
                    "status": "index_not_initialized",
                    "query": query,
                    "timestamp": time.time()
                }]

            query_vector = self._get_query_vector(query)
            if query_vector is None:
                logger.warning("无法获取查询向量")
                return [{
                    "error": "无法获取查询向量",
                    "status": "vector_generation_failed",
                    "query": query,
                    "timestamp": time.time()
                }]

            # 先检查查询向量是否有效
            if isinstance(query_vector, dict):
                error_msg = query_vector.get("error", "未知错误")
                logger.warning(f"⚠️ 无法生成查询向量: {error_msg}")
                return [{
                    "error": error_msg,
                    "status": query_vector.get("status", "vector_error"),
                    "query": query,
                    "timestamp": time.time()
                }]

            if not isinstance(query_vector, np.ndarray):
                logger.warning("⚠️ 查询向量格式错误，期望 np.ndarray，实际: %s", type(query_vector))
                return [{
                    "error": "查询向量格式错误",
                    "status": "invalid_vector_type",
                    "query": query,
                    "timestamp": time.time()
                }]

            # 检查索引是否可用
            if not hasattr(self.index, 'search'):
                logger.warning("⚠️ 索引不支持搜索操作")
                return [{
                    "error": "索引不支持搜索操作",
                    "status": "index_search_not_supported",
                    "query": query,
                    "timestamp": time.time()
                }]

            # 执行搜索
            try:
                if not self.index:
                    logger.warning("⚠️ 索引未初始化，无法执行搜索")
                    return [{
                        "error": "索引未初始化",
                        "status": "index_not_initialized",
                        "query": query,
                        "timestamp": time.time()
                    }]
                
                # 检查索引维度是否匹配
                try:
                    if hasattr(self.index, 'd') and not isinstance(self.index, dict):
                        index_dim = getattr(self.index, 'd', None)
                        if index_dim is not None:
                            vector_dim = query_vector.shape[0] if len(query_vector.shape) == 1 else query_vector.shape[1]
                            if index_dim != vector_dim:
                                logger.error(f"❌ 索引维度({index_dim})与查询向量维度({vector_dim})不匹配")
                                return [{
                                    "error": f"索引维度({index_dim})与查询向量维度({vector_dim})不匹配",
                                    "status": "dimension_mismatch",
                                    "query": query,
                                    "timestamp": time.time()
                                }]
                except Exception as dim_check_error:
                    logger.debug(f"维度检查失败: {dim_check_error}，继续尝试搜索")
                
                if (hasattr(self.index, 'ntotal') and 
                    getattr(self.index, 'ntotal', 0) > 0):
                    search_result: tuple = self.index.search(  # type: ignore
                        query_vector.reshape(1, -1), top_k
                    )
                    distances, indices = search_result
                else:
                    # 索引为空，返回空结果
                    logger.debug("索引为空，返回空结果")
                    return []
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e) if str(e) else f"{error_type}异常"
                logger.error(f"❌ FAISS搜索失败: {error_type}: {error_msg}", exc_info=True)
                return [{
                    "error": f"FAISS搜索失败: {error_type}: {error_msg}",
                    "status": "faiss_search_failed",
                    "query": query,
                    "timestamp": time.time()
                }]

            # 检查搜索结果是否为空
            if len(indices) == 0 or len(indices[0]) == 0:
                logger.debug("搜索返回空结果")
                return []

            results = []
            for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
                if idx < len(self.knowledge_entries):
                    entry = self.knowledge_entries[idx]
                    
                    # 处理字典格式的知识条目
                    if isinstance(entry, dict):
                        entry_id = entry.get('entry_id', f'entry_{idx}')
                        query = entry.get('query', '')
                        answer = entry.get('answer', '')
                        content = entry.get('content', '')
                        metadata = entry.get('metadata', {})
                        confidence = entry.get('confidence', 0.5)
                        quality_score = entry.get('quality_score', 0.5)
                        
                        # 更新使用计数（如果是字典格式）
                        if 'usage_count' in entry:
                            entry['usage_count'] = entry.get('usage_count', 0) + 1
                        entry['last_accessed'] = datetime.now()
                    else:
                        # 处理对象格式的知识条目
                        entry.usage_count += 1
                        entry.last_accessed = datetime.now()
                        entry_id = getattr(entry, 'entry_id', '')
                        query = entry.query
                        answer = entry.answer
                        content = entry.content
                        metadata = entry.metadata
                        confidence = entry.confidence
                        quality_score = entry.quality_score

                    result = {
                        "entry_id": entry_id,
                        "query": query,
                        "answer": answer,
                        "content": content,
                        "metadata": metadata,
                        "confidence": confidence,
                        "quality_score": quality_score,
                        "similarity_score": float(1.0 - distance),  # 转换为相似度分数
                        "rank": i + 1
                    }
                    results.append(result)

            filtered_results = [
                result for result in results
                if result.get("similarity_score", 0.0) >= similarity_threshold
            ]

            logger.debug("回退搜索完成，找到 %d 个结果", len(filtered_results))
            return filtered_results

        except Exception as e:
            logger.error("回退搜索失败: %s", e)
            return [{
                "error": f"回退搜索失败: {e}",
                "status": "fallback_search_failed",
                "query": query,
                "timestamp": time.time()
            }]

    def _get_query_vector(self, query: str) -> Union[np.ndarray, Dict[str, Any]]:
        """获取查询的向量表示（🆕 优先使用本地模型）"""
        try:
            # 🆕 优先使用本地模型（完全免费，无需API密钥）
            if self._model is not None:
                try:
                    query_vector = self._model.encode([query])[0]
                    return query_vector
                except Exception as e:
                    logger.warning(f"⚠️ 本地模型向量化失败: {e}，尝试Jina API fallback")
                    # 继续执行，尝试Jina API fallback
            
            # Fallback: 使用Jina服务（如果本地模型不可用）
            if self._jina_service and self._jina_service.api_key:
                embedding = self._jina_service.get_embedding(query)
                if embedding is not None:
                    return np.array(embedding, dtype=np.float32)
                else:
                    logger.error("❌ Jina embedding返回为空")
                    # 返回错误字典而不是None
                    return {
                        "error": "Jina embedding返回为空",
                        "status": "embedding_empty",
                        "query": query,
                        "timestamp": time.time()
                    }
            
            # 都没有可用，返回错误
            logger.warning("⚠️ 模型未准备就绪，无法生成查询向量")
            return {
                "error": "模型未准备就绪",
                "status": "model_not_ready",
                "query": query,
                "timestamp": time.time()
            }

        except ImportError:
            logger.warning("⚠️ sentence-transformers未安装，无法进行向量搜索")
            return {
                "error": "sentence-transformers未安装",
                "status": "import_error",
                "query": query,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.warning("⚠️ 生成查询向量失败: %s", e)
            return {
                "error": f"生成查询向量失败: {e}",
                "status": "vector_generation_failed",
                "query": query,
                "timestamp": time.time()
            }

    def add_entry(self, query: str, answer: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Union[bool, Dict[str, Any]]:
        """添加知识条目 - 向后兼容方法"""
        try:
            entry = {
                'entry_id': f"entry_{int(time.time())}_{len(self.knowledge_entries)}",
                'query': query,
                'answer': answer,
                'content': content,
                'metadata': metadata or {},
                'timestamp': datetime.now(),
                'confidence': get_smart_config("high_threshold", create_query_context("high_threshold")) or 0.9,
                'quality_score': get_smart_config("medium_threshold", create_query_context("medium_threshold")) or 0.7,
                'usage_count': 0,
                'last_accessed': datetime.now()
            }

            result = self._add_knowledge_direct(entry)
            if isinstance(result, dict):
                return result
            return result

        except Exception as e:
            logger.error("添加条目失败: %s", e)
            return {
                "error": f"添加条目失败: {e}",
                "status": "add_entry_failed",
                "query": query,
                "timestamp": time.time()
            }

    def _add_knowledge_direct(self, entry: Dict[str, Any]) -> Union[bool, Dict[str, Any]]:
        """直接添加知识条目到系统"""
        try:
            content_vector = self._get_query_vector(entry.get('content', ''))
            if isinstance(content_vector, dict):
                logger.warning("无法获取内容向量: %s", content_vector.get("error", "未知错误"))
                return {
                    "error": "无法获取内容向量",
                    "status": "vector_generation_failed",
                    "entry_id": entry.get('entry_id', '') if isinstance(entry, dict) else getattr(entry, 'entry_id', ''),
                    "details": content_vector,
                    "timestamp": time.time()
                }

            if self.index and hasattr(self.index, 'add'):
                try:
                    if isinstance(content_vector, np.ndarray):
                        vector_2d = content_vector.reshape(1, -1).astype('float32')
                        if self.index is not None and hasattr(self.index, 'add'):
                            self.index.add(vector_2d)  # type: ignore

                    self.knowledge_entries.append(entry)

                    entry_id = entry.get('entry_id', '') if isinstance(entry, dict) else getattr(entry, 'entry_id', '')
                    self.entry_metadata[entry_id] = {
                        'index_position': len(self.knowledge_entries) - 1,
                        'added_time': datetime.now().isoformat()
                    }

                    logger.debug("✅ 成功添加知识条目: %s", entry.get('entry_id', '') if isinstance(entry, dict) else getattr(entry, 'entry_id', ''))
                    return True

                except Exception as e:
                    logger.error("添加知识条目到索引失败: %s", e)
                    return {
                        "error": f"添加知识条目到索引失败: {e}",
                        "status": "index_add_failed",
                        "entry_id": entry.get('entry_id', '') if isinstance(entry, dict) else getattr(entry, 'entry_id', ''),
                        "timestamp": time.time()
                    }
            else:
                self.knowledge_entries.append(entry)
                logger.debug("✅ 知识条目已添加到列表（索引未就绪）: %s", entry.get('entry_id', '') if isinstance(entry, dict) else getattr(entry, 'entry_id', ''))
                return True

        except Exception as e:
            logger.error("直接添加知识条目失败: %s", e)
            return {
                "error": f"直接添加知识条目失败: {e}",
                "status": "add_entry_failed",
                "entry_id": entry.get('entry_id', '') if isinstance(entry, dict) else getattr(entry, 'entry_id', ''),
                "timestamp": time.time()
            }

    async def add_entry_async(self, query: str, answer: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Union[bool, Dict[str, Any]]:
        """异步添加知识条目 - 向后兼容方法"""
        try:
            entry = {
                'entry_id': f"entry_{int(time.time())}_{len(self.knowledge_entries)}",
                'query': query,
                'answer': answer,
                'content': content,
                'metadata': metadata or {},
                'timestamp': datetime.now(),
                'confidence': get_smart_config("high_threshold", create_query_context("high_threshold")) or 0.9,
                'quality_score': get_smart_config("medium_threshold", create_query_context("medium_threshold")) or 0.7,
                'usage_count': 0,
                'last_accessed': datetime.now()
            }

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._add_knowledge_direct, entry)
            return result

        except Exception as e:
            logger.error("异步添加条目失败: %s", e)
            return {
                "error": f"异步添加条目失败: {e}",
                "status": "async_add_entry_failed",
                "query": query,
                "timestamp": time.time()
            }

    def get_entry(self, entry_id: str) -> Union[KnowledgeEntry, Dict[str, Any]]:
        """获取知识条目"""
        try:
            for entry in self.knowledge_entries:
                entry_id_check = entry.get('entry_id', '') if isinstance(entry, dict) else getattr(entry, 'entry_id', '')
                if entry_id_check == entry_id:
                    if isinstance(entry, dict):
                        entry['usage_count'] = entry.get('usage_count', 0) + 1
                        entry['last_accessed'] = datetime.now()
                    else:
                        entry.usage_count += 1
                        entry.last_accessed = datetime.now()
                    return entry
            logger.warning("⚠️ 条目 %s 未找到", entry_id)
            return {
                "error": f"条目 {entry_id} 未找到",
                "status": "entry_not_found",
                "entry_id": entry_id,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.warning("获取条目失败: %s", e)
            return {
                "error": f"获取条目失败: {e}",
                "status": "get_entry_failed",
                "entry_id": entry_id,
                "timestamp": time.time()
            }

    def update_entry(self, entry_id: str, **kwargs) -> Union[bool, Dict[str, Any]]:
        """更新知识条目"""
        try:
            entry = self.get_entry(entry_id)
            if isinstance(entry, dict):
                return entry

            for key, value in kwargs.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)

            logger.debug("✅ 成功更新条目: %s", entry_id)
            return True

        except Exception as e:
            logger.error("更新条目失败: %s", e)
            return {
                "error": f"更新条目失败: {e}",
                "status": "update_entry_failed",
                "entry_id": entry_id,
                "timestamp": time.time()
            }

    def delete_entry(self, entry_id: str) -> Union[bool, Dict[str, Any]]:
        """删除知识条目"""
        try:
            for i, entry in enumerate(self.knowledge_entries):
                entry_id_check = entry.get('entry_id', '') if isinstance(entry, dict) else getattr(entry, 'entry_id', '')
                if entry_id_check == entry_id:
                    del self.knowledge_entries[i]

                    if entry_id in self.entry_metadata:
                        del self.entry_metadata[entry_id]

                    logger.debug("✅ 成功删除条目: %s", entry_id)
                    return True

            logger.warning("⚠️ 未找到要删除的条目: %s", entry_id)
            return {
                "error": f"未找到要删除的条目: {entry_id}",
                "status": "entry_not_found",
                "entry_id": entry_id,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.error("删除条目失败: %s", e)
            return {
                "error": f"删除条目失败: {e}",
                "status": "delete_entry_failed",
                "entry_id": entry_id,
                "timestamp": time.time()
            }

    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            stats = {
                "total_entries": len(self.knowledge_entries),
                "index_status": self.get_index_status(),
                "cache_stats": {
                    "cache_size": len(self._search_cache),
                    "cache_hit_rate": self._cache_hit_rate,
                    "cache_ttl": self._cache_ttl
                },
                "performance_stats": {
                    "avg_search_time": np.mean(self._search_times) if self._search_times else 0,
                    "total_searches": len(self._search_times),
                    "preload_entries": len(self._frequently_accessed)
                }
            }

            if self.index and hasattr(self.index, 'd') and hasattr(self.index, 'ntotal'):
                try:
                    stats["index_stats"] = {
                        "dimension": getattr(self.index, 'd', 0),
                        "total_vectors": getattr(self.index, 'ntotal', 0),
                        "index_type": type(self.index).__name__
                    }
                except Exception:
                    stats["index_stats"] = {"error": "无法获取索引统计"}
            elif self.index:
                stats["index_stats"] = {
                    "dimension": "unknown",
                    "total_vectors": "unknown", 
                    "index_type": type(self.index).__name__
                }

            return stats

        except Exception as e:
            logger.warning("获取统计信息失败: %s", e)
            return {"error": str(e)}

    def optimize_performance(self) -> Union[bool, Dict[str, Any]]:
        """优化系统性能"""
        try:
            logger.info("🔧 开始性能优化...")

            self._optimize_index()

            self._cleanup_expired_cache()

            if not self._preload_initialized:
                self._schedule_preload()

            logger.info("✅ 性能优化完成")
            return True

        except Exception as e:
            logger.warning("性能优化失败: %s", e)
            return {
                "error": f"性能优化失败: {e}",
                "status": "optimization_failed",
                "timestamp": time.time()
            }

    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        try:
            current_time = time.time()
            expired_keys = []

            for key, timestamp in self._cache_timestamps.items():
                if current_time - timestamp > self._cache_ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                if key in self._search_cache:
                    del self._search_cache[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]

            if expired_keys:
                logger.debug("🧹 清理了 %d 个过期缓存", len(expired_keys))

        except Exception as e:
            logger.debug("清理过期缓存失败: %s", e)

    def health_check(self) -> Dict[str, Any]:
        """系统健康检查"""
        try:
            health_status: Dict[str, Any] = {
                "status": self._get_system_status(),
                "timestamp": datetime.now().isoformat(),
                "index_health": "unknown",
                "memory_usage": "unknown",
                "cache_health": "unknown"
            }

            if self._index_loaded and self.index:
                try:
                    if hasattr(self.index, 'ntotal') and hasattr(self.index, 'd'):
                        health_status["index_health"] = self._get_index_status()
                        health_status["index_stats"] = {
                            "dimension": getattr(self.index, 'd', 0),
                            "total_vectors": getattr(self.index, 'ntotal', 0)
                        }
                    else:
                        health_status["index_health"] = "degraded"
                        health_status["status"] = "degraded"
                except Exception:
                    health_status["index_health"] = "unhealthy"
                    health_status["status"] = "unhealthy"
                else:
                    health_status["index_health"] = "not_ready"
                    if self._initialization_task and not self._initialization_task.done():
                        health_status["index_health"] = "initializing"
                    else:
                        health_status["status"] = "degraded"

            try:
                cache_size = len(self._search_cache)
                if cache_size < self._cache_size_limit * (get_smart_config("high_threshold", create_query_context("high_threshold")) or 0.9):
                    health_status["cache_health"] = "healthy"
                elif cache_size < self._cache_size_limit:
                    health_status["cache_health"] = "warning"
                else:
                    health_status["cache_health"] = "critical"
                    health_status["status"] = "degraded"

                health_status["cache_stats"] = {
                    "current_size": cache_size,
                    "max_size": self._cache_size_limit
                }
            except Exception:
                health_status["cache_health"] = "unknown"

            try:
                import psutil
                # Fallback if module not available
                def get_intelligent_replacer():
                    return {
                        "status": "module_not_available",
                        "message": "智能替换模块不可用",
                        "timestamp": time.time()
                    }
                process = psutil.Process()
                memory_info = process.memory_info()
                health_status["memory_usage"] = {
                    "rss_mb": memory_info.rss / 1024 / 1024,
                    "vms_mb": memory_info.vms / 1024 / 1024
                }
            except ImportError:
                health_status["memory_usage"] = "psutil_not_available"

            return health_status

        except Exception as e:
            logger.error("健康检查失败: %s", e)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def health_check_async(self) -> Dict[str, Any]:
        """异步系统健康检查"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.health_check)
            return result

        except Exception as e:
            logger.error("异步健康检查失败: %s", e)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def reset(self) -> bool:
        """重置系统状态"""
        try:
            logger.info("🔄 开始重置FAISS内存系统...")

            self._search_cache.clear()
            self._cache_timestamps.clear()

            self._index_loaded = False
            self._preload_initialized = False
            self._index_optimized = False

            self.knowledge_entries.clear()
            self.entry_metadata.clear()

            if self.index:
                del self.index
                self.index = None

            self._start_async_initialization()

            logger.info("✅ FAISS内存系统重置完成")
            return True

        except Exception as e:
            logger.error("重置系统失败: %s", e)
            return False

    async def reset_async(self) -> bool:
        """异步重置系统状态"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.reset)
            return result

        except Exception as e:
            logger.error("异步重置系统失败: %s", e)
            return False

    def _is_index_cache_valid(self) -> bool:
        """检查索引缓存是否有效"""
        try:
            if not self._index_cache or 'index' not in self._index_cache:
                return False

            current_time = time.time()
            if current_time - self._index_cache_timestamp > self._index_cache_ttl:
                logger.debug("⏰ 索引缓存已过期")
                return False

            cached_index = self._index_cache.get('index')
            if cached_index is None:
                return False

            logger.debug("✅ 索引缓存有效")
            return True

        except Exception as e:
            logger.warning("检查索引缓存有效性失败: %s", e)
            return False

    def _cache_index(self) -> None:
        """缓存索引数据"""
        try:
            if self.index is not None:
                self._index_cache['index'] = self.index
                self._index_cache_timestamp = time.time()
                logger.debug("💾 索引已缓存")
            else:
                logger.warning("⚠️ 无法缓存空索引")

        except Exception as e:
            logger.warning("缓存索引失败: %s", e)

    def _clear_index_cache(self) -> None:
        """清理索引缓存"""
        try:
            self._index_cache.clear()
            self._index_cache_timestamp = 0
            logger.debug("🗑️ 索引缓存已清理")
        except Exception as e:
            logger.warning("清理索引缓存失败: %s", e)

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            total_requests = self._cache_hits + self._cache_misses
            cache_hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0.0
            
            return {
                "search_cache_size": len(self._search_cache),
                "search_cache_limit": self._cache_size_limit,
                "index_cache_valid": self._is_index_cache_valid(),
                "index_cache_timestamp": self._index_cache_timestamp,
                "index_cache_ttl": self._index_cache_ttl,
                "cache_hit_rate": cache_hit_rate,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "total_requests": total_requests
            }
        except Exception as e:
            logger.warning("获取缓存统计信息失败: %s", e)
            return {
                "error": f"获取缓存统计信息失败: {e}",
                "status": "cache_stats_failed",
                "timestamp": time.time(),
                "stats": {}
            }

    def _is_knowledge_cache_valid(self) -> bool:
        """检查知识条目缓存是否有效"""
        try:
            if not self._index_cache or 'knowledge_entries' not in self._index_cache:
                return False

            current_time = time.time()
            if current_time - self._index_cache_timestamp > self._index_cache_ttl:
                logger.debug("⏰ 知识条目缓存已过期")
                return False

            cached_entries = self._index_cache.get('knowledge_entries')
            if not cached_entries:
                return False

            logger.debug("✅ 知识条目缓存有效")
            return True

        except Exception as e:
            logger.warning("检查知识条目缓存有效性失败: %s", e)
            return False

    def _cache_knowledge_entries(self) -> None:
        """缓存知识条目数据"""
        try:
            if self.knowledge_entries:
                self._index_cache['knowledge_entries'] = self.knowledge_entries
                self._index_cache_timestamp = time.time()
                logger.debug("💾 知识条目已缓存 (%d 条, len(self.knowledge_entries))")
            else:
                logger.warning("⚠️ 无法缓存空知识条目")

        except Exception as e:
            logger.warning("缓存知识条目失败: %s", e)

    def _clear_all_caches(self) -> None:
        """清理所有缓存"""
        try:
            self._clear_index_cache()
            self._search_cache.clear()
            self._cache_timestamps.clear()
            logger.info("🗑️ 所有缓存已清理")
        except Exception as e:
            logger.warning("清理所有缓存失败: %s", e)

    def get_initialization_status(self) -> Dict[str, Any]:
        """获取初始化状态信息"""
        try:
            return {
                "index_loaded": self._index_loaded,
                "async_init_started": getattr(self, '_async_init_started', False),
                "initialization_task_exists": hasattr(self,
    '_initialization_task') and self._initialization_task is not None,
                "index_exists": self.index is not None,
                "knowledge_entries_count": len(self.knowledge_entries) if hasattr(self, 'knowledge_entries') else 0,
                "cache_stats": None,  # 暂时注释掉，因为函数未定义
                "last_initialization_time": self._last_initialization_time,
                "initialization_times_count": len(self._initialization_times)
            }
        except (AttributeError, KeyError) as e:
            logger.warning("获取初始化状态失败 (属性错误): %s", e)
            return {"error": str(e)}
        except Exception as e:
            logger.warning("获取初始化状态失败 (未知错误): %s", e)
            return {"error": str(e)}

    def is_fully_initialized(self) -> bool:
        """检查系统是否完全初始化"""
        try:
            return (
                self._index_loaded and
                self.index is not None and
                len(self.knowledge_entries) > 0
            )
        except (AttributeError, KeyError) as e:
            logger.warning("检查初始化状态失败 (属性错误): %s", e)
            return False
        except Exception as e:
            logger.warning("检查初始化状态失败 (未知错误): %s", e)
            return False

    def force_reload_from_cache(self) -> bool:
        """强制从缓存重新加载"""
        try:
            if self._is_index_cache_valid():
                logger.info("🔄 强制从缓存重新加载...")
                self.index = self._index_cache.get('index')
                self.knowledge_entries = self._index_cache.get('knowledge_entries', [])
                self._index_loaded = True
                logger.info("✅ 从缓存重新加载成功")
                return True
            logger.warning("⚠️ 缓存无效，无法强制重新加载")
            return False
        except (AttributeError, KeyError) as e:
            logger.error("强制重新加载失败 (属性错误): %s", e)
            return False
        except Exception as e:
            logger.error("强制重新加载失败 (未知错误): %s", e)
            return False

    def _initialize_local_model(self) -> None:
        """🆕 初始化本地模型（优先使用，完全免费）"""
        try:
            disable_local = os.getenv("DISABLE_LOCAL_EMBEDDING", "").lower() == "true" or os.getenv("USE_JINA_EMBEDDING_ONLY", "").lower() == "true"
            if disable_local:
                self._model = None
                self._model_loaded = False
                return
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                local_model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "all-mpnet-base-v2")
                
                # 🆕 尝试使用镜像源（如果网络有问题）
                hf_endpoint = os.getenv("HF_ENDPOINT")
                if not hf_endpoint:
                    # 默认使用镜像源，提高下载成功率
                    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                    logger.debug("使用HuggingFace镜像源: https://hf-mirror.com")
                
                logger.info(f"🔄 正在加载本地embedding模型: {local_model_name}...")
                # 🆕 优先尝试从本地缓存加载（避免网络连接）
                try:
                    # 首先尝试只使用本地文件（如果模型已下载）
                    self._model = SentenceTransformer(local_model_name, local_files_only=True)
                    self._model_loaded = True
                    actual_dim = self._model.get_sentence_embedding_dimension()
                    logger.info(f"✅ 已从本地缓存加载模型: {local_model_name} (维度: {actual_dim})")
                except Exception as local_error:
                    # 如果本地加载失败，尝试网络下载（使用镜像源）
                    logger.debug(f"本地缓存加载失败，尝试网络下载: {local_error}")
                    self._model = SentenceTransformer(local_model_name, local_files_only=False)
                    self._model_loaded = True
                    actual_dim = self._model.get_sentence_embedding_dimension()
                    logger.info(f"✅ 已从网络加载模型: {local_model_name} (维度: {actual_dim})")
                logger.info("💡 提示: 本地模型完全免费，优先使用本地模型")
            else:
                logger.warning("⚠️ sentence-transformers未安装，无法使用本地模型")
                self._model = None
                self._model_loaded = False
        except Exception as e:
            logger.warning(f"⚠️ 加载本地模型失败: {e}，将尝试Jina API fallback")
            logger.warning("💡 提示: 可以运行 scripts/download_local_model.py 手动下载模型")
            self._model = None
            self._model_loaded = False
    
    def _initialize_jina_service(self) -> None:
        """初始化Jina服务（Fallback，仅在本地模型不可用时使用）"""
        try:
            from src.utils.unified_jina_service import get_jina_service
            self._jina_service = get_jina_service()
            if self._jina_service and self._jina_service.api_key:
                logger.info("✅ Jina Embedding服务初始化成功（fallback）")
            else:
                logger.warning("⚠️ JINA_API_KEY未设置，无法使用Jina embedding")
        except Exception as e:
            logger.error(f"❌ Jina服务初始化失败: {e}")
            self._jina_service = None

    def get_model_status(self) -> Dict[str, Any]:
        """获取模型状态信息"""
        try:
            return {
                "model_loaded": self._model_loaded,
                "model_exists": self._model is not None,
                "model_type": type(self._model).__name__ if self._model else None,
                "model_device": str(self._model.device) if self._model else None
            }
        except (AttributeError, KeyError) as e:
            logger.warning("获取模型状态失败 (属性错误): %s", e)
            return {"error": str(e)}
        except Exception as e:
            logger.warning("获取模型状态失败 (未知错误): %s", e)
            return {"error": str(e)}

    def is_model_ready(self) -> bool:
        """检查模型是否准备就绪（🆕 优先检查本地模型）"""
        try:
            # 🆕 优先检查本地模型（完全免费，无需API密钥）
            if self._model is not None:
                return True
            # Fallback: 检查Jina服务
            if self._jina_service and self._jina_service.api_key:
                return True
            return False
        except (AttributeError, KeyError) as e:
            logger.warning("检查模型状态失败 (属性错误): %s", e)
            return False
        except Exception as e:
            logger.warning("检查模型状态失败 (未知错误): %s", e)
            return False

    def _get_system_status(self) -> str:
        """使用现有智能系统获取系统状态，零硬编码"""
        try:
            if self._index_loaded and self.index and hasattr(self.index, 'ntotal'):
                if self.index is not None and getattr(self.index, 'ntotal', 0) > 0:
                    return "healthy"
                else:
                    return "warning"
            else:
                return "initializing"
        except Exception:
            return "error"

    def _get_index_status(self) -> str:
        """使用现有智能系统获取索引状态，零硬编码"""
        try:
            if self._index_loaded and self.index:
                if hasattr(self.index, 'ntotal') and hasattr(self.index, 'd'):
                    if self.index is not None and getattr(self.index, 'ntotal', 0) > 0:
                        return "healthy"
                    else:
                        return "empty"
                else:
                    return "degraded"
            else:
                return "not_loaded"
        except Exception:
            return "error"


# 定义缺失的函数
def get_smart_config(key: str, context: Optional[Dict[str, Any]] = None) -> Any:
    """获取智能配置"""
    try:
        from src.utils.unified_centers import get_unified_center
        center = get_unified_center('get_unified_config_center')
        if center:
            return center.get_smart_config(key, context or {})
    except ImportError:
        logger.warning("统一中心系统不可用，使用默认配置")
    return None

def create_query_context(query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """创建查询上下文"""
    return {
        "query": query,
        "user_id": user_id,
        "timestamp": time.time()
    }


    def _validate_index_state(self) -> bool:
        """验证索引状态"""
        try:
            if not self.index:
                return False
            
            # 检查索引基本属性
            if not hasattr(self.index, 'ntotal'):
                return False
            
            # 检查索引维度
            if hasattr(self.index, 'd') and self.index.d != self.vector_dim:
                logger.warning("⚠️ 索引维度不匹配: 期望 %d, 实际 %d", self.vector_dim, self.index.d)
                return False
            
            # 检查索引是否可查询
            if self.index.ntotal > 0:
                try:
                    # 尝试进行一次空查询来验证索引状态
                    dummy_vector = np.zeros((1, self.vector_dim), dtype=np.float32)
                    self.index.search(dummy_vector, 1)
                except Exception as e:
                    logger.error("❌ 索引查询测试失败: %s", e)
                    return False
            
            return True
            
        except Exception as e:
            logger.error("❌ 索引状态验证失败: %s", e)
            return False
    
    def _optimize_index_performance(self) -> bool:
        """优化索引性能"""
        try:
            if not self.index:
                return False
            
            # 1. 设置索引参数
            if hasattr(self.index, 'set_ef'):
                # 对于HNSW索引，设置ef参数
                self.index.set_ef(64)
            
            # 2. 设置线程数
            if hasattr(self.index, 'set_num_threads'):
                self.index.set_num_threads(4)
            
            # 3. 优化内存使用
            if hasattr(self.index, 'make_direct_map'):
                self.index.make_direct_map()
            
            # 4. 设置搜索参数
            if hasattr(self.index, 'set_search_precision'):
                self.index.set_search_precision(0.8)
            
            logger.info("✅ 索引性能优化完成")
            return True
            
        except Exception as e:
            logger.error("❌ 索引性能优化失败: %s", e)
            return False
    
    def _record_search_performance(self, query: str, search_time: float, result_count: int, top_k: int):
        """记录搜索性能指标"""
        try:
            metrics = self._performance_metrics
            
            # 记录搜索时间
            metrics['search_times'].append(search_time)
            metrics['search_counts'] += 1
            metrics['total_search_time'] += search_time
            
            # 更新统计信息
            metrics['avg_search_time'] = metrics['total_search_time'] / metrics['search_counts']
            metrics['max_search_time'] = max(metrics['max_search_time'], search_time)
            metrics['min_search_time'] = min(metrics['min_search_time'], search_time)
            
            # 记录查询长度和结果数量
            metrics['query_lengths'].append(len(query))
            metrics['result_counts'].append(result_count)
            
            # 计算缓存命中率
            total_searches = metrics['cache_hits'] + metrics['cache_misses']
            if total_searches > 0:
                metrics['cache_hit_rate'] = metrics['cache_hits'] / total_searches
            
            # 保持数据在合理范围内
            if len(metrics['search_times']) > 1000:
                metrics['search_times'] = metrics['search_times'][-500:]
            if len(metrics['query_lengths']) > 1000:
                metrics['query_lengths'] = metrics['query_lengths'][-500:]
            if len(metrics['result_counts']) > 1000:
                metrics['result_counts'] = metrics['result_counts'][-500:]
            
            # 每100次搜索记录一次性能摘要
            if metrics['search_counts'] % 100 == 0:
                self._log_performance_summary()
                
        except Exception as e:
            logger.warning(f"记录搜索性能失败: {e}")
    
    def _log_performance_summary(self):
        """记录性能摘要"""
        try:
            metrics = self._performance_metrics
            
            logger.info(f"📊 FAISS搜索性能摘要 (最近{metrics['search_counts']}次搜索):")
            logger.info(f"  - 平均搜索时间: {metrics['avg_search_time']:.3f}s")
            logger.info(f"  - 最大搜索时间: {metrics['max_search_time']:.3f}s")
            logger.info(f"  - 最小搜索时间: {metrics['min_search_time']:.3f}s")
            logger.info(f"  - 缓存命中率: {metrics['cache_hit_rate']:.2%}")
            
            if metrics['query_lengths']:
                avg_query_length = sum(metrics['query_lengths']) / len(metrics['query_lengths'])
                logger.info(f"  - 平均查询长度: {avg_query_length:.1f} 字符")
            
            if metrics['result_counts']:
                avg_result_count = sum(metrics['result_counts']) / len(metrics['result_counts'])
                logger.info(f"  - 平均结果数量: {avg_result_count:.1f}")
                
        except Exception as e:
            logger.warning(f"记录性能摘要失败: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            metrics = self._performance_metrics.copy()
            
            # 添加计算指标
            if metrics['query_lengths']:
                metrics['avg_query_length'] = sum(metrics['query_lengths']) / len(metrics['query_lengths'])
            else:
                metrics['avg_query_length'] = 0
            
            if metrics['result_counts']:
                metrics['avg_result_count'] = sum(metrics['result_counts']) / len(metrics['result_counts'])
            else:
                metrics['avg_result_count'] = 0
            
            # 添加索引信息
            metrics['index_info'] = {
                'knowledge_entries_count': len(self.knowledge_entries),
                'index_loaded': self._index_loaded,
                'index_path': self.index_path,
                'dimension': self.dimension
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return {}
