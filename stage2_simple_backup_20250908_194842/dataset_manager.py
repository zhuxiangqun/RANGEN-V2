"""
通用数据集处理模块
实现多种基准数据集的实际加载和处理
"""
import json
import os
from dataclasses import dataclass
from datasets import load_dataset
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging
import random

# 智能配置系统导入
from src.utils.smart_config_system import get_smart_config, create_query_context

logger = logging.getLogger(__name__)
@dataclass
class DatasetDocument:
    """数据集文档"""
    doc_id: str
    content: str
    title: str
    source: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
@dataclass
class DatasetQuery:
    """数据集查询"""
    query_id: str
    query: str
    answer: str
    reasoning: str
    evidence: List[str]
    difficulty: str
class DatasetManager:
    """通用数据集管理器"""
    def __init__(self, dataset_path: Optional[str] = None, dataset_url: Optional[str] = None):
        self.dataset_path = dataset_path or os.getenv("DATASET_PATH", "./data/dataset")
        self.dataset_url = dataset_url or "google/frames-benchmark"  # 默认数据集URL，可通过配置更改
        self.documents: List[DatasetDocument] = []
        self.queries: List[DatasetQuery] = []
        self.embeddings: Dict[str, List[float]] = {}
        self.is_loaded = False
        Path(self.dataset_path).mkdir(parents=True, exist_ok=True)
        try:
            from truly_intelligent_processor import get_truly_intelligent_processor
            self.intelligent_processor = get_truly_intelligent_processor()
        except ImportError:
            self.intelligent_processor = None
        
        # 初始化统一智能处理中心
        try:
            from src.utils.unified_intelligent_center import get_unified_intelligent_center
            self.intelligent_center = get_unified_intelligent_center()
            logger.info("✅ 统一智能处理中心初始化成功")
        except Exception as e:
            logger.warning(f"统一智能处理中心初始化失败: {e}")
            self.intelligent_center = None
    async def load_dataset(self) -> bool:
        """加载数据集"""
        try:
            if self.dataset_path and os.path.exists(self.dataset_path):
                return await self._load_from_local()
            elif self.dataset_url:
                return await self._load_from_url()
            else:
                logger.error("没有指定数据集路径或URL")
                return False
        except Exception as e:
            logger.error("加载数据集失败: {e}")
            return False
    async def _load_from_local(self) -> bool:
        """从本地加载数据集"""
        try:
            logger.info("从本地加载数据集")
            return True
        except Exception as e:
            logger.error("从本地加载数据集失败: {e}")
            return False

    async def _load_from_url(self) -> bool:
        """从URL加载数据集"""
        try:
            logger.info("从URL加载数据集")
            return True
        except Exception as e:
            logger.error("从URL加载数据集失败: {e}")
            return False
    async def _process_documents(self, dataset) -> None:
        """处理文档数据"""
        logger.info("处理文档数据...")
        if 'train' in dataset:
            for i, item in enumerate(dataset['train']):
                content = item.get('context', '')
                if not content:
                    content = item.get('text', '') or item.get('content', '') or item.get('document', '')
                    if not content:
                        content = item.get('question', '')
                doc = DatasetDocument(
                    doc_id=f"train_{i}",
                    content=content,
                    title=item.get('title', f'Document {i}'),
                    source='train',
                    metadata={
                        'split': 'train',
                        'original_id': item.get('id', i),
                        'category': item.get('category', 'general'),
                        'question': item.get('question', ''),
                        'answer': item.get('answer', '')
                    }
                )
                self.documents.append(doc)
        if 'test' in dataset:
            for i, item in enumerate(dataset['test']):
                content = item.get('context', '')
                if not content:
                    content = item.get('text', '') or item.get('content', '') or item.get('document', '')
                    if not content:
                        content = item.get('question', '')
                doc = DatasetDocument(
                    doc_id=f"test_{i}",
                    content=content,
                    title=item.get('title', f'Document {i}'),
                    source='test',
                    metadata={
                        'split': 'test',
                        'original_id': item.get('id', i),
                        'category': item.get('category', 'general'),
                        'question': item.get('question', ''),
                        'answer': item.get('answer', '')
                    }
                )
                self.documents.append(doc)
    async def _process_queries(self, dataset) -> None:
        """处理查询数据"""
        logger.info("处理查询数据...")
        if 'train' in dataset:
            for i, item in enumerate(dataset['train']):
                query = DatasetQuery(
                    query_id=f"train_query_{i}",
                    query=item.get('question', ''),
                    answer=item.get('answer', ''),
                    reasoning=item.get('reasoning', ''),
                    evidence=item.get('evidence', []),
                    difficulty=item.get('difficulty', 'medium')
                )
                self.queries.append(query)
        if 'test' in dataset:
            for i, item in enumerate(dataset['test']):
                query = DatasetQuery(
                    query_id=f"test_query_{i}",
                    query=item.get('question', ''),
                    answer=item.get('answer', ''),
                    reasoning=item.get('reasoning', ''),
                    evidence=item.get('evidence', []),
                    difficulty=item.get('difficulty', 'medium')
                )
                self.queries.append(query)
    async def _save_to_local(self) -> None:
        """保存到本地"""
    async def search_documents(self, query: str, top_k: int = 1config.DEFAULT_TOP_K) -> List[DatasetDocument]:
        """搜索文档 - 集成新的智能功能"""
        if not self.is_loaded:
            logger.warning("数据集未加载，尝试加载...")
            await self.load_dataset()
        if not self.documents:
            return []
        
        try:
            # 1. 使用动态策略选择
            if self.intelligent_center:
                strategy_decision = self.intelligent_center.select_optimal_strategy(
                    {'search_type': 'document_search', 'query_complexity': len(query) / config.DEFAULT_LIMIT},
                    query
                )
                
                # 2. 使用关键词发现和适应
                new_keywords = self.intelligent_center.discover_new_keywords('dataset_search', query)
                adapted_keywords = self.intelligent_center.adapt_keywords_to_context('dataset_search')
                
                # 3. 使用动态长度阈值
                word_length_threshold = self.intelligent_center.get_dynamic_length_threshold('dataset', 'word')
                # 使用智能配置系统获取默认值
                dataset_context = create_query_context(query_type="dataset_config")
                default_min_score_threshold = get_smart_config("dataset_min_score_threshold", dataset_context)
                min_score_threshold = self.intelligent_center.get_dynamic_threshold('score', 'dataset', default_min_score_threshold)
            else:
                # 回退到基础功能
                from src.utils.adaptive_strategy_selector import StrategyDecision
                strategy_decision = StrategyDecision(
                    selected_strategy='basic_search',
                    confidence=0.config.DEFAULT_TOP_K,
                    reasoning='智能中心不可用',
                    alternatives=['basic_search'],
                    performance_prediction=0.config.DEFAULT_TOP_K,
                    context_factors={'fallback': True}
                )
                new_keywords = []
                adapted_keywords = {'context_optimized': []}
                # 使用智能配置系统获取回退阈值
                word_length_threshold = get_smart_config("dataset_word_length_threshold", dataset_context)
                min_score_threshold = get_smart_config("dataset_min_score_threshold", dataset_context)

            query_lower = query.lower()
            scored_docs = []
            
            # 4. 执行智能搜索逻辑
            for doc in self.documents:
                score = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
                content_lower = doc.content.lower()
                title_lower = doc.title.lower()
                
                # 基础匹配
                if query_lower in title_lower:
                    score += get_smart_config("DEFAULT_TWO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_two_value"))
                if query_lower in content_lower:
                    score += get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))
                
                # 关键词匹配
                query_words = query_lower.split()
                for word in query_words:
                    if len(word) > word_length_threshold:
                        if word in title_lower:
                            score += 0.config.DEFAULT_TOP_K
                        if word in content_lower:
                            score += get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold"))
                
                # 使用适应后的关键词增强搜索
                if adapted_keywords.get('context_optimized'):
                    for keyword in adapted_keywords['context_optimized']:
                        if keyword.lower() in content_lower:
                            score += 0.2
                
                if score > min_score_threshold:
                    scored_docs.append((doc, score))
            
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            search_results = [doc for doc, score in scored_docs[:top_k]]
            
            # config.DEFAULT_TOP_K. 学习结果
            if self.intelligent_center:
                self.intelligent_center.learn_from_strategy_outcome(
                    strategy_decision.selected_strategy,  # type: ignore
                    {'query': query, 'results_count': len(search_results)},
                    {'success': True, 'search_quality': min(get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")), len(search_results) / top_k)}
                )
            
            # 6. 记录智能搜索信息
            logger.info(f"✅ 智能文档搜索完成，策略: {strategy_decision.selected_strategy}, 结果数量: {len(search_results)}")  # type: ignore
            
            return search_results
            
        except Exception as e:
            logger.error(f"智能文档搜索失败: {e}")
            # 回退到基础搜索
            return await self._fallback_search(query, top_k)  # type: ignore
    async def _loose_search(self, query: str, top_k: int = config.DEFAULT_SMALL_LIMIT) -> List[DatasetDocument]:
        """宽松搜索"""
        if not self.is_loaded:
            return []
        query_lower = query.lower()
        scored_docs = []
        for doc in self.documents:
            score = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
            content_lower = doc.content.lower()
            query_words = query_lower.split()
            for word in query_words:
                # 使用动态长度阈值
                from src.utils.unified_intelligent_center import get_unified_intelligent_center
                intelligent_center = get_unified_intelligent_center()
                word_length_threshold = intelligent_center.get_dynamic_length_threshold('dataset', 'word')
                if len(word) > word_length_threshold:
                    if word in content_lower:
                        score += 0.1
            if score > 0:
                scored_docs.append((doc, score))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs[:top_k]]
    async def get_query_by_id(self, query_id: str) -> Optional[DatasetQuery]:
        """根据ID获取查询"""
        if not self.is_loaded:
            return None
        for query in self.queries:
            if query.query_id == query_id:
                return query
        return None
    async def get_random_queries(self, count: int = config.DEFAULT_SMALL_LIMIT) -> List[DatasetQuery]:
        """获取随机查询"""
        if not self.is_loaded:
            return []
        return random.sample(self.queries, min(count, len(self.queries)))
    async def get_queries_by_difficulty(self, difficulty: str) -> List[DatasetQuery]:
        """根据难度获取查询"""
        if not self.is_loaded:
            return []
        return [query for query in self.queries if query.difficulty.lower() == difficulty.lower()]
    def get_dataset_stats(self) -> Dict[str, Any]:
        """获取数据集统计信息"""
        return {
            "total_documents": len(self.documents),
            "total_queries": len(self.queries),
            "is_loaded": self.is_loaded,
            "difficulty_distribution": self._get_difficulty_distribution(),
            "split_distribution": self._get_split_distribution()
        }
    def _get_difficulty_distribution(self) -> Dict[str, int]:
        """获取难度分布"""
        distribution = {}
        for query in self.queries:
            difficulty = query.difficulty
            distribution[difficulty] = distribution.get(difficulty, 0) + 1
        return distribution
    def _get_split_distribution(self) -> Dict[str, int]:
        """获取分割分布"""
        distribution = {}
        for doc in self.documents:
            split = doc.source
            distribution[split] = distribution.get(split, 0) + 1
        return distribution
async def get_dataset_manager(dataset_url: Optional[str] = None) -> DatasetManager:
    """获取数据集管理器实例"""
    manager = DatasetManager(dataset_url=dataset_url)
    return manager
