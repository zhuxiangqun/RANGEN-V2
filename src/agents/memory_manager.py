#!/usr/bin/env python3
"""
MemoryManager - 记忆管理器 (L4基础智能)
智能压缩算法、关联网络优化、自适应记忆管理
from ..utils.unified_centers import get_unified_config_center
from ..utils.unified_threshold_manager import get_unified_threshold_manager


优化特性：
- 智能压缩算法：语义压缩和重要性排序
- 关联网络优化：动态关联图构建和遍历
- 自适应记忆管理：基于访问模式的智能遗忘
- 上下文感知检索：语义相似度和关联性排序
"""

import time
import logging
import asyncio
import hashlib
import json
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor
import re
import math

from .expert_agent import ExpertAgent
from .base_agent import AgentResult
from src.utils.logging_helper import get_module_logger, ModuleType
from src.utils.unified_centers import get_unified_config_center
from src.utils.unified_threshold_manager import get_unified_threshold_manager

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class CompressionStrategy(Enum):
    """压缩策略"""
    SEMANTIC_SUMMARY = "semantic_summary"
    KEYWORD_EXTRACTION = "keyword_extraction"
    IMPORTANCE_RANKING = "importance_ranking"
    TEMPORAL_COMPRESSION = "temporal_compression"


@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    content: Any
    memory_type: MemoryType
    created_at: float
    last_accessed: float
    access_count: int = 0
    importance_score: float = 0.5
    associations: Set[str] = field(default_factory=set)
    compressed_content: Optional[Any] = None
    compression_ratio: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssociationLink:
    """关联链接"""
    source_id: str
    target_id: str
    strength: float
    link_type: str
    created_at: float
    access_count: int = 0


class MemoryManager(ExpertAgent):
    """MemoryManager - 记忆管理器 (L4基础智能)

    核心职责：
    1. 智能压缩算法 - 语义压缩和重要性排序
    2. 关联网络优化 - 动态关联图构建和遍历
    3. 自适应记忆管理 - 基于访问模式的智能遗忘
    4. 上下文感知检索 - 语义相似度和关联性排序

    优化特性：
    - 多策略压缩：语义摘要、关键词提取、重要性排序
    - 关联网络构建：动态图谱和路径发现
    - 自适应遗忘：基于访问模式和重要性的智能清理
    - 并行处理：并发压缩和检索操作
    """

    def __init__(self):
        """初始化MemoryManager"""
        # 初始化统一配置中心
        self.config_center = get_unified_config_center()
        self.threshold_manager = get_unified_threshold_manager()

        # 获取Agent特定配置
        self.agent_config = self.config_center.get_agent_config(self.__class__.__name__, {
            'enabled': True,
            'max_retries': 3,
            'timeout': 30,
            'debug_mode': False
        })

        # 获取阈值配置
        self.thresholds = self.threshold_manager.get_thresholds(self.__class__.__name__, {
            'performance_warning_threshold': 5.0,
            'error_rate_threshold': 0.1,
            'memory_usage_threshold': 80.0
        })

        super().__init__(
            agent_id="memory_manager",
            domain_expertise="智能记忆管理和上下文压缩",
            capability_level=0.8,  # L4基础智能
            collaboration_style="supportive"
        )

        # 使用模块日志器
        self.module_logger = get_module_logger(ModuleType.AGENT, "MemoryManager")

        # 🚀 新增：记忆存储和索引
        self._memory_store: Dict[str, MemoryItem] = {}
        self._association_graph: Dict[str, List[AssociationLink]] = defaultdict(list)
        self._reverse_associations: Dict[str, List[AssociationLink]] = defaultdict(list)

        # 🚀 新增：压缩和缓存配置
        self._compression_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="memory_compression")
        self._max_memory_items = 10000  # 最大记忆项数量
        self._compression_threshold = 0.8  # 压缩阈值（内容长度比例）
        self._importance_decay_factor = 0.95  # 重要性衰减因子
        self._min_importance_threshold = 0.1  # 最小重要性阈值

        # 🚀 新增：缓存和统计
        self._retrieval_cache = OrderedDict()  # LRU缓存
        self._cache_max_size = 1000
        self._stats = {
            'total_memories': 0,
            'compressed_memories': 0,
            'total_associations': 0,
            'cache_hits': 0,
            'compression_operations': 0,
            'retrieval_operations': 0
        }

        # 🚀 新增：自适应参数
        self._adaptive_params = {
            'forgetfulness_rate': 0.01,  # 遗忘率
            'reinforcement_factor': 1.1,  # 强化因子
            'association_threshold': 0.6,  # 关联阈值
            'compression_interval': 3600  # 压缩检查间隔（秒）
        }

        # 启动维护线程
        self._maintenance_thread: Optional[threading.Thread] = None
        self._running = False
        self._start_maintenance_thread()

    def _get_service(self):
        """MemoryManager不直接使用单一Service"""
        return None

    # 🚀 新增：记忆存储和管理方法
    async def store_memory(self, content: Any, memory_type: MemoryType,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """存储记忆项"""
        memory_id = f"mem_{int(time.time() * 1000)}_{hash(str(content)) % 10000}"

        memory_item = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            created_at=time.time(),
            last_accessed=time.time(),
            metadata=metadata or {}
        )

        # 计算初始重要性分数
        memory_item.importance_score = await self._calculate_importance(content, memory_type)

        # 检查是否需要压缩
        if await self._should_compress(memory_item):
            await self._compress_memory(memory_item)

        self._memory_store[memory_id] = memory_item
        self._stats['total_memories'] += 1

        # 清理过期记忆
        await self._cleanup_expired_memories()

        self.module_logger.debug(f"✅ 记忆已存储: {memory_id}, 类型: {memory_type.value}")
        return memory_id

    async def retrieve_memory(self, query: str, context: Optional[Dict[str, Any]] = None,
                             limit: int = 10) -> List[Dict[str, Any]]:
        """检索记忆（优化版）"""
        start_time = time.time()
        self._stats['retrieval_operations'] += 1

        # 检查缓存
        cache_key = self._get_cache_key(query, context)
        if cache_key in self._retrieval_cache:
            self._retrieval_cache.move_to_end(cache_key)  # LRU更新
            self._stats['cache_hits'] += 1
            return self._retrieval_cache[cache_key]

        # 并行检索策略
        tasks = [
            self._semantic_retrieval(query, context, limit),
            self._associative_retrieval(query, context, limit),
            self._temporal_retrieval(query, context, limit)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并和排序结果
        all_results = []
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)

        # 去重和排序
        unique_results = self._deduplicate_results(all_results)
        ranked_results = self._rank_results(unique_results, query)

        final_results = ranked_results[:limit]

        # 更新访问统计
        for result in final_results:
            memory_id = result.get('id')
            if memory_id in self._memory_store:
                memory = self._memory_store[memory_id]
                memory.access_count += 1
                memory.last_accessed = time.time()
                # 强化重要性
                memory.importance_score = min(1.0, memory.importance_score * self._adaptive_params['reinforcement_factor'])

        # 缓存结果
        if len(self._retrieval_cache) >= self._cache_max_size:
            self._retrieval_cache.popitem(last=False)  # 移除最旧的
        self._retrieval_cache[cache_key] = final_results

        execution_time = time.time() - start_time
        self.module_logger.info(f"✅ 记忆检索完成: {len(final_results)} 项, 耗时={execution_time:.3f}秒")

        return final_results

    # 🚀 新增：智能压缩算法
    async def _should_compress(self, memory: MemoryItem) -> bool:
        """判断是否需要压缩"""
        content_size = len(str(memory.content))

        # 基于内容大小和重要性的压缩决策
        size_threshold = 1000  # 内容长度阈值
        importance_threshold = 0.7  # 重要性阈值

        return (content_size > size_threshold and
                memory.importance_score < importance_threshold and
                memory.compressed_content is None)

    async def _compress_memory(self, memory: MemoryItem):
        """智能压缩记忆"""
        self._stats['compression_operations'] += 1

        compression_tasks = [
            self._semantic_compression(memory),
            self._keyword_extraction_compression(memory),
            self._importance_based_compression(memory)
        ]

        results = await asyncio.gather(*compression_tasks, return_exceptions=True)

        # 选择最佳压缩结果
        best_compression = None
        best_ratio = 1.0

        for result in results:
            if isinstance(result, dict) and 'compressed' in result:
                ratio = result.get('compression_ratio', 1.0)
                if ratio < best_ratio:
                    best_ratio = ratio
                    best_compression = result['compressed']

        if best_compression:
            memory.compressed_content = best_compression
            memory.compression_ratio = best_ratio
            self._stats['compressed_memories'] += 1

            self.module_logger.debug(f"✅ 记忆压缩完成: {memory.id}, 压缩率={best_ratio:.2f}")

    async def _semantic_compression(self, memory: MemoryItem) -> Dict[str, Any]:
        """语义压缩"""
        try:
            content = str(memory.content)

            # 简单的语义压缩：提取关键句子
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip()]

            if len(sentences) <= 3:
                return {'compressed': content, 'compression_ratio': 1.0}

            # 基于位置和长度的重要性评分
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                # 位置权重（开头和结尾更重要）
                position_weight = 1.0
                if i == 0 or i == len(sentences) - 1:
                    position_weight = 1.5

                # 长度权重（适中长度的句子更重要）
                length_weight = min(1.0, len(sentence) / 100)

                score = position_weight * length_weight
                scored_sentences.append((score, sentence))

            # 选择前60%的句子
            scored_sentences.sort(reverse=True)
            selected_count = max(1, int(len(sentences) * 0.6))
            selected_sentences = [s for _, s in scored_sentences[:selected_count]]

            compressed = '. '.join(selected_sentences)
            compression_ratio = len(compressed) / len(content)

            return {
                'compressed': compressed,
                'compression_ratio': compression_ratio,
                'method': 'semantic'
            }

        except Exception as e:
            self.module_logger.warning(f"语义压缩失败: {e}")
            return {'compressed': str(memory.content), 'compression_ratio': 1.0}

    async def _keyword_extraction_compression(self, memory: MemoryItem) -> Dict[str, Any]:
        """关键词提取压缩"""
        try:
            content = str(memory.content)

            # 提取关键词（简单实现）
            words = re.findall(r'\b\w+\b', content.lower())
            word_freq = defaultdict(int)

            # 过滤停用词和短词
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            for word in words:
                if len(word) > 3 and word not in stop_words:
                    word_freq[word] += 1

            # 选择高频关键词
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
            compressed = ', '.join([word for word, _ in top_keywords])

            compression_ratio = len(compressed) / len(content)

            return {
                'compressed': f"Keywords: {compressed}",
                'compression_ratio': compression_ratio,
                'method': 'keywords'
            }

        except Exception as e:
            self.module_logger.warning(f"关键词提取压缩失败: {e}")
            return {'compressed': str(memory.content), 'compression_ratio': 1.0}

    async def _importance_based_compression(self, memory: MemoryItem) -> Dict[str, Any]:
        """基于重要性的压缩"""
        try:
            content = str(memory.content)

            # 如果已经有重要性分数，使用它进行压缩
            if memory.importance_score > 0.8:
                # 高重要性内容保持完整
                return {'compressed': content, 'compression_ratio': 1.0}
            elif memory.importance_score > 0.5:
                # 中等重要性：轻微压缩
                compressed = content[:int(len(content) * 0.8)]
                return {'compressed': compressed, 'compression_ratio': 0.8}
            else:
                # 低重要性：大幅压缩
                compressed = content[:int(len(content) * 0.5)]
                return {'compressed': compressed, 'compression_ratio': 0.5}

        except Exception as e:
            self.module_logger.warning(f"重要性压缩失败: {e}")
            return {'compressed': str(memory.content), 'compression_ratio': 1.0}

    # 🚀 新增：关联网络优化
    async def create_association(self, source_id: str, target_id: str,
                                link_type: str = "related", strength: float = 0.5):
        """创建记忆关联"""
        if source_id not in self._memory_store or target_id not in self._memory_store:
            return False

        association = AssociationLink(
            source_id=source_id,
            target_id=target_id,
            strength=strength,
            link_type=link_type,
            created_at=time.time()
        )

        self._association_graph[source_id].append(association)
        self._reverse_associations[target_id].append(association)
        self._stats['total_associations'] += 1

        # 更新记忆项的关联集合
        if source_id in self._memory_store:
            self._memory_store[source_id].associations.add(target_id)
        if target_id in self._memory_store:
            self._memory_store[target_id].associations.add(source_id)

        self.module_logger.debug(f"✅ 关联已创建: {source_id} -> {target_id} ({link_type})")
        return True

    async def _associative_retrieval(self, query: str, context: Optional[Dict[str, Any]],
                                    limit: int) -> List[Dict[str, Any]]:
        """关联检索"""
        try:
            # 首先进行语义检索找到种子记忆
            seed_memories = await self._semantic_retrieval(query, context, limit=5)

            if not seed_memories:
                return []

            # 从种子记忆扩展关联网络
            associated_memories = set()
            for seed in seed_memories:
                seed_id = seed.get('id')
                if seed_id in self._memory_store:
                    # 广度优先搜索关联网络
                    await self._bfs_association_search(seed_id, associated_memories, max_depth=2)

            # 转换为结果格式
            results = []
            for memory_id in associated_memories:
                if memory_id in self._memory_store:
                    memory = self._memory_store[memory_id]
                    results.append({
                        'id': memory.id,
                        'content': memory.compressed_content or memory.content,
                        'memory_type': memory.memory_type.value,
                        'importance_score': memory.importance_score,
                        'last_accessed': memory.last_accessed,
                        'retrieval_type': 'associative'
                    })

            return results[:limit]

        except Exception as e:
            self.module_logger.warning(f"关联检索失败: {e}")
            return []

    async def _bfs_association_search(self, start_id: str, visited: Set[str], max_depth: int = 2):
        """广度优先搜索关联网络"""
        queue = [(start_id, 0)]  # (node_id, depth)
        visited.add(start_id)

        while queue:
            current_id, depth = queue.pop(0)

            if depth >= max_depth:
                continue

            # 获取关联节点
            for association in self._association_graph.get(current_id, []):
                if association.target_id not in visited and association.strength > 0.3:
                    visited.add(association.target_id)
                    queue.append((association.target_id, depth + 1))

                    # 更新关联强度（使用奖励）
                    association.strength = min(1.0, association.strength * 1.05)
                    association.access_count += 1

    # 🚀 新增：检索策略
    async def _semantic_retrieval(self, query: str, context: Optional[Dict[str, Any]],
                                 limit: int) -> List[Dict[str, Any]]:
        """语义检索"""
        try:
            results = []
            query_lower = query.lower()

            for memory_id, memory in self._memory_store.items():
                content = str(memory.compressed_content or memory.content).lower()

                # 简单的语义匹配（可以替换为更复杂的模型）
                similarity_score = self._calculate_similarity(query_lower, content)

                if similarity_score > 0.1:  # 相似度阈值
                    results.append({
                        'id': memory.id,
                        'content': memory.compressed_content or memory.content,
                        'memory_type': memory.memory_type.value,
                        'importance_score': memory.importance_score,
                        'similarity_score': similarity_score,
                        'last_accessed': memory.last_accessed,
                        'retrieval_type': 'semantic'
                    })

            # 按相似度和重要性排序
            results.sort(key=lambda x: (x['similarity_score'] * 0.7 + x['importance_score'] * 0.3), reverse=True)
            return results[:limit]

        except Exception as e:
            self.module_logger.warning(f"语义检索失败: {e}")
            return []

    async def _temporal_retrieval(self, query: str, context: Optional[Dict[str, Any]],
                                 limit: int) -> List[Dict[str, Any]]:
        """时间序列检索"""
        try:
            # 获取最近的记忆项
            recent_memories = sorted(
                self._memory_store.values(),
                key=lambda m: m.last_accessed,
                reverse=True
            )

            results = []
            for memory in recent_memories[:limit * 2]:  # 多取一些用于过滤
                results.append({
                    'id': memory.id,
                    'content': memory.compressed_content or memory.content,
                    'memory_type': memory.memory_type.value,
                    'importance_score': memory.importance_score,
                    'last_accessed': memory.last_accessed,
                    'retrieval_type': 'temporal'
                })

            return results[:limit]

        except Exception as e:
            self.module_logger.warning(f"时间检索失败: {e}")
            return []

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简化实现）"""
        try:
            # 简单的词袋相似度
            words1 = set(re.findall(r'\b\w+\b', text1))
            words2 = set(re.findall(r'\b\w+\b', text2))

            if not words1 or not words2:
                return 0.0

            intersection = words1 & words2
            union = words1 | words2

            return len(intersection) / len(union)

        except Exception:
            return 0.0

    async def _calculate_importance(self, content: Any, memory_type: MemoryType) -> float:
        """计算记忆重要性"""
        try:
            content_str = str(content)

            # 基于内容特征计算重要性
            importance = 0.5  # 基础分数

            # 长度因素
            length = len(content_str)
            if length > 1000:
                importance += 0.1
            elif length < 50:
                importance -= 0.1

            # 关键词因素
            important_keywords = ['important', 'critical', 'key', 'essential', 'urgent']
            keyword_count = sum(1 for kw in important_keywords if kw in content_str.lower())
            importance += keyword_count * 0.05

            # 记忆类型因素
            type_multipliers = {
                MemoryType.LONG_TERM: 1.2,
                MemoryType.EPISODIC: 1.1,
                MemoryType.SEMANTIC: 1.0,
                MemoryType.SHORT_TERM: 0.9,
                MemoryType.PROCEDURAL: 1.1
            }
            importance *= type_multipliers.get(memory_type, 1.0)

            return min(1.0, max(0.0, importance))

        except Exception as e:
            self.module_logger.warning(f"重要性计算失败: {e}")
            return 0.5

    # 🚀 新增：自适应记忆管理和维护
    async def _cleanup_expired_memories(self):
        """清理过期记忆"""
        try:
            current_time = time.time()
            to_remove = []

            for memory_id, memory in self._memory_store.items():
                # 计算记忆年龄（天）
                age_days = (current_time - memory.created_at) / (24 * 3600)

                # 自适应遗忘策略
                forget_probability = self._adaptive_params['forgetfulness_rate'] * age_days

                # 重要性保护
                importance_protection = memory.importance_score

                # 访问频率保护
                access_frequency = memory.access_count / max(age_days, 1)
                frequency_protection = min(1.0, access_frequency * 0.1)

                # 综合遗忘概率
                total_forget_prob = forget_probability / (importance_protection + frequency_protection + 1.0)

                if (memory.importance_score < self._min_importance_threshold and
                    total_forget_prob > 0.5):
                    to_remove.append(memory_id)

            # 限制最大记忆数量
            if len(self._memory_store) > self._max_memory_items:
                # 按重要性排序，移除最不重要的
                sorted_memories = sorted(
                    self._memory_store.items(),
                    key=lambda x: x[1].importance_score
                )
                to_remove.extend([mid for mid, _ in sorted_memories[:len(sorted_memories) - self._max_memory_items]])

            # 执行清理
            for memory_id in set(to_remove):
                if memory_id in self._memory_store:
                    del self._memory_store[memory_id]
                    # 清理关联
                    if memory_id in self._association_graph:
                        del self._association_graph[memory_id]
                    if memory_id in self._reverse_associations:
                        del self._reverse_associations[memory_id]

            if to_remove:
                self.module_logger.info(f"🧹 清理过期记忆: {len(set(to_remove))} 项")

        except Exception as e:
            self.module_logger.warning(f"记忆清理失败: {e}")

    def _get_cache_key(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """生成缓存键"""
        key_data = {
            'query': query,
            'context_keys': sorted(context.keys()) if context else []
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """结果去重"""
        seen_ids = set()
        deduplicated = []

        for result in results:
            result_id = result.get('id')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                deduplicated.append(result)

        return deduplicated

    def _rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """结果排序"""
        if not results:
            return results

        scored_results = []
        for result in results:
            score = 0.0

            # 相似度分数（40%）
            similarity = result.get('similarity_score', 0.0)
            score += similarity * 0.4

            # 重要性分数（30%）
            importance = result.get('importance_score', 0.5)
            score += importance * 0.3

            # 时间新鲜度（20%）
            last_accessed = result.get('last_accessed', 0)
            recency_score = max(0, 1.0 - (time.time() - last_accessed) / (7 * 24 * 3600))  # 7天衰减
            score += recency_score * 0.2

            # 检索类型权重（10%）
            retrieval_type = result.get('retrieval_type', 'semantic')
            type_weights = {'semantic': 1.0, 'associative': 1.2, 'temporal': 0.8}
            score *= type_weights.get(retrieval_type, 1.0)

            scored_results.append((score, result))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [result for _, result in scored_results]

    # 🚀 新增：维护线程
    def _start_maintenance_thread(self):
        """启动维护线程"""
        self._running = True
        self._maintenance_thread = threading.Thread(target=self._maintenance_worker, daemon=True)
        self._maintenance_thread.start()
        self.module_logger.debug("🔧 记忆维护线程已启动")

    def _maintenance_worker(self):
        """维护工作线程"""
        while self._running:
            try:
                time.sleep(self._adaptive_params['compression_interval'])

                # 创建事件循环来运行异步任务
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    # 执行维护任务
                    loop.run_until_complete(self._cleanup_expired_memories())

                    # 自适应参数调整
                    self._adapt_parameters()

                finally:
                    loop.close()

            except Exception as e:
                self.module_logger.warning(f"记忆维护异常: {e}")

    def _adapt_parameters(self):
        """自适应参数调整"""
        try:
            # 基于统计数据调整参数
            memory_utilization = len(self._memory_store) / self._max_memory_items

            if memory_utilization > 0.9:
                # 内存紧张，增加遗忘率
                self._adaptive_params['forgetfulness_rate'] = min(0.05,
                    self._adaptive_params['forgetfulness_rate'] * 1.2)
            elif memory_utilization < 0.5:
                # 内存充足，降低遗忘率
                self._adaptive_params['forgetfulness_rate'] = max(0.005,
                    self._adaptive_params['forgetfulness_rate'] * 0.8)

            # 基于缓存命中率调整缓存大小
            cache_hit_rate = self._stats['cache_hits'] / max(self._stats['retrieval_operations'], 1)
            if cache_hit_rate > 0.8:
                self._cache_max_size = min(2000, self._cache_max_size * 2)
            elif cache_hit_rate < 0.3:
                self._cache_max_size = max(500, self._cache_max_size // 2)

        except Exception as e:
            self.module_logger.warning(f"参数自适应失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        memory_types = defaultdict(int)
        for memory in self._memory_store.values():
            memory_types[memory.memory_type.value] += 1

        return {
            **self._stats,
            'current_memory_count': len(self._memory_store),
            'memory_types': dict(memory_types),
            'cache_size': len(self._retrieval_cache),
            'avg_importance_score': sum(m.importance_score for m in self._memory_store.values()) / max(len(self._memory_store), 1),
            'compression_ratio_avg': sum(m.compression_ratio for m in self._memory_store.values() if m.compressed_content) / max(sum(1 for m in self._memory_store.values() if m.compressed_content), 1)
        }

    # 核心执行方法
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        执行记忆管理任务

        Args:
            context: 记忆管理请求上下文
                - action: 操作类型 ("store", "retrieve", "associate", "compress", "stats")
                - content: 要存储的内容 (store时需要)
                - memory_type: 记忆类型 (store时需要)
                - query: 检索查询 (retrieve时需要)
                - source_id/target_id: 关联ID (associate时需要)
                - limit: 检索数量限制 (retrieve时可选，默认10)

        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()
        action = context.get("action", "")

        try:
            if action == "store":
                content = context.get("content")
                memory_type_str = context.get("memory_type", "short_term")
                metadata = context.get("metadata")

                try:
                    memory_type = MemoryType(memory_type_str)
                    memory_id = await self.store_memory(content, memory_type, metadata)
                    result_data = {"status": "stored", "memory_id": memory_id}
                except ValueError:
                    result_data = {"error": f"无效记忆类型: {memory_type_str}"}

            elif action == "retrieve":
                query = context.get("query", "")
                limit = context.get("limit", 10)

                if not query:
                    result_data = {"error": "检索查询不能为空"}
                else:
                    memories = await self.retrieve_memory(query, context, limit)
                    result_data = {
                        "status": "retrieved",
                        "memories": memories,
                        "count": len(memories)
                    }

            elif action == "associate":
                source_id = context.get("source_id")
                target_id = context.get("target_id")
                link_type = context.get("link_type", "related")
                strength = context.get("strength", 0.5)

                if not source_id or not target_id:
                    result_data = {"error": "关联需要source_id和target_id"}
                else:
                    success = await self.create_association(source_id, target_id, link_type, strength)
                    result_data = {"status": "associated" if success else "failed"}

            elif action == "compress":
                # 手动触发压缩
                await self._cleanup_expired_memories()
                result_data = {"status": "compressed"}

            elif action == "stats":
                result_data = self.get_stats()

            else:
                result_data = {"error": f"不支持的操作: {action}"}

            return AgentResult(
                success=True,
                data=result_data,
                confidence=0.8,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            self.module_logger.error(f"❌ MemoryManager执行异常: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )

    def shutdown(self):
        """关闭记忆管理器"""
        self._running = False
        if self._maintenance_thread and self._maintenance_thread.is_alive():
            self._maintenance_thread.join(timeout=5)

        self._compression_executor.shutdown(wait=True)
        self.module_logger.info("🛑 MemoryManager已关闭")
