#!/usr/bin/env python3
"""
LlamaIndex 适配器
提供增强的检索能力，包括查询扩展和多策略检索
"""

import os
from typing import List, Dict, Any, Optional
from ..utils.logger import get_logger

logger = get_logger()

# 尝试导入 LlamaIndex（可选依赖）
try:
    from llama_index.core import VectorStoreIndex, Settings, Document, QueryBundle
    from llama_index.core.query_engine import RetrieverQueryEngine, RouterQueryEngine
    from llama_index.core.retrievers import VectorIndexRetriever
    from llama_index.core.postprocessor import SimilarityPostprocessor
    from llama_index.core.node_parser import SimpleNodeParser
    from llama_index.core.schema import NodeWithScore, TextNode
    # query_pipeline 在新版本中可能已移除，改为可选导入
    try:
        from llama_index.core.query_pipeline import QueryPipeline  # type: ignore
    except ImportError:
        QueryPipeline = None  # type: ignore
    # RouterQueryEngine相关
    try:
        from llama_index.core.selectors import LLMSingleSelector, LLMMultiSelector
    except ImportError:
        LLMSingleSelector = None  # type: ignore
        LLMMultiSelector = None  # type: ignore
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    QueryPipeline = None  # type: ignore
    LLMSingleSelector = None  # type: ignore
    LLMMultiSelector = None  # type: ignore
    logger.warning("LlamaIndex 未安装，相关功能将不可用。如需使用，请运行: pip install llamaindex")


class LlamaIndexAdapter:
    """LlamaIndex 适配器，提供增强的检索能力"""
    
    def __init__(self, enable_llamaindex: bool = False, text_processor=None, jina_service=None):
        """
        初始化适配器
        
        Args:
            enable_llamaindex: 是否启用 LlamaIndex
            text_processor: 文本处理器（用于生成embedding，可选）
            jina_service: Jina服务（用于生成embedding，可选）
        """
        self.enable_llamaindex = enable_llamaindex and LLAMAINDEX_AVAILABLE
        self.logger = logger
        
        # 🚀 升级：保存text_processor和jina_service用于语义相似度计算
        self.text_processor = text_processor
        self.jina_service = jina_service
        
        # 🚀 性能优化：索引缓存（避免重复构建索引）
        self._index_cache = {}  # documents_hash -> index
        self._max_cache_size = 10  # 最大缓存数量
        
        # 🚀 性能优化：索引缓存（避免重复构建索引）
        self._index_cache = {}  # documents_hash -> index
        self._max_cache_size = 10  # 最大缓存数量
        
        # 🆕 阶段2：多样化索引管理器
        self.index_manager = None
        # 🆕 阶段4：聊天引擎和子问题分解器
        self.chat_engine = None
        self.sub_question_decomposer = None
        
        if self.enable_llamaindex:
            self._init_llamaindex()
        else:
            if enable_llamaindex and not LLAMAINDEX_AVAILABLE:
                self.logger.warning("LlamaIndex 未安装，适配器将使用降级模式")
            self.index = None
            self.query_engine = None
    
    def _init_llamaindex(self):
        """初始化 LlamaIndex 组件"""
        try:
            # 🆕 配置LlamaIndex使用本地模型（如果可用）
            # 确保LlamaIndex使用与知识库相同的embedding模型，避免向量空间不一致
            if LLAMAINDEX_AVAILABLE:
                try:
                    from llama_index.core import Settings
                    
                    # 如果text_processor可用且使用本地模型，配置LlamaIndex使用相同的模型
                    if self.text_processor and hasattr(self.text_processor, 'local_model') and self.text_processor.local_model:
                        # 创建自定义embedding适配器，使用本地模型
                        class LocalEmbeddingAdapter:
                            """本地模型embedding适配器，适配LlamaIndex接口"""
                            def __init__(self, text_processor):
                                self.text_processor = text_processor
                                self.model_name = "local_model"
                            
                            def get_query_embedding(self, query: str):
                                """获取查询的embedding向量"""
                                embedding = self.text_processor.encode(query)
                                if embedding is not None:
                                    return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                                return None
                            
                            def get_text_embedding(self, text: str):
                                """获取文本的embedding向量"""
                                embedding = self.text_processor.encode(text)
                                if embedding is not None:
                                    return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                                return None
                            
                            def get_text_embeddings(self, texts: list):
                                """批量获取文本的embedding向量"""
                                embeddings = self.text_processor.encode(texts)
                                if embeddings is not None:
                                    if hasattr(embeddings, 'tolist'):
                                        return embeddings.tolist()
                                    elif isinstance(embeddings, list):
                                        return [e.tolist() if hasattr(e, 'tolist') else list(e) for e in embeddings]
                                    else:
                                        return list(embeddings)
                                return None
                        
                        # 配置LlamaIndex使用本地模型
                        Settings.embed_model = LocalEmbeddingAdapter(self.text_processor)
                        self.logger.info("✅ LlamaIndex已配置使用本地embedding模型（与知识库一致）")
                    else:
                        self.logger.debug("ℹ️ LlamaIndex将使用默认embedding模型（text_processor未使用本地模型）")
                except Exception as e:
                    self.logger.warning(f"配置LlamaIndex使用本地模型失败: {e}，将使用默认设置")
            
            # 注意：这里不立即创建索引，而是在需要时从现有向量存储构建
            # 索引将在首次使用时延迟初始化
            self.index = None
            self.query_engine = None
            
            # 🆕 阶段2：初始化索引管理器
            try:
                from .llamaindex_index_manager import LlamaIndexIndexManager
                self.index_manager = LlamaIndexIndexManager()
                if self.index_manager.enabled:
                    self.logger.info("✅ LlamaIndex 索引管理器已初始化")
            except Exception as e:
                self.logger.warning(f"索引管理器初始化失败: {e}")
                self.index_manager = None
            
            # 🆕 阶段4：聊天引擎和子问题分解器将在需要时初始化
            self.chat_engine = None
            self.sub_question_decomposer = None
            
            self.logger.info("✅ LlamaIndex 适配器初始化成功")
        except Exception as e:
            self.logger.error(f"LlamaIndex 初始化失败: {e}")
            self.enable_llamaindex = False
    
    def enhanced_query(
        self, 
        query: str, 
        existing_results: List[Dict[str, Any]],
        query_expansion: bool = True,
        multi_strategy: bool = True
    ) -> List[Dict[str, Any]]:
        """
        使用 LlamaIndex 增强查询（🚀 性能优化：保持高准确率的前提下提高性能）
        
        Args:
            query: 查询文本
            existing_results: 现有检索结果（来自向量检索）
            query_expansion: 是否进行查询扩展
            multi_strategy: 是否使用多策略检索
        
        Returns:
            增强后的检索结果
        """
        if not self.enable_llamaindex:
            return existing_results
        
        try:
            # 如果现有结果为空，直接返回
            if not existing_results:
                return existing_results
            
            # 🚀 性能优化：评估原始结果质量，决定是否需要增强
            quality_assessment = self._assess_result_quality(existing_results)
            
            # 🚀 性能优化：如果原始结果质量已经很高，跳过所有增强以节省时间
            if quality_assessment['is_high_quality']:
                self.logger.debug(
                    f"🚀 性能优化：原始结果质量已很高(最高分={quality_assessment['top_score']:.3f}, "
                    f"平均分={quality_assessment['avg_score']:.3f})，跳过所有增强以节省时间"
                )
                return existing_results
            
            # 🚀 P0实现：查询扩展和多策略检索融合
            enhanced_results = existing_results.copy()
            
            # 策略1：查询扩展 - 🚀 性能优化：只在质量不够高时进行
            # 🚀 性能优化：对于短查询或结果很少的情况，跳过扩展（减少处理时间）
            should_expand = (
                query_expansion and 
                len(enhanced_results) > 3 and
                not quality_assessment['is_high_quality'] and
                quality_assessment['top_score'] < 0.85  # 🚀 性能优化：只在top_score<0.85时扩展
            )
            
            if should_expand:
                expanded_queries = self._expand_query(query)
                if len(expanded_queries) > 1:
                    self.logger.debug(f"查询扩展: 生成{len(expanded_queries)}个查询变体")
                    # 注意：这里暂时只使用原始查询，扩展查询的额外检索可以在后续版本实现
                    # 当前版本通过重排序来提升质量
            
            # 策略2：多策略检索融合 - 🚀 性能优化：只在质量不够高时进行
            # 🚀 升级：使用 LlamaIndex 的 RouterQueryEngine
            if multi_strategy and not quality_assessment['is_high_quality'] and quality_assessment['top_score'] < 0.85:
                try:
                    # 🚀 升级：使用LlamaIndex的RouterQueryEngine进行多策略检索
                    router_results = self._query_with_llamaindex_router(query, enhanced_results)
                    if router_results:
                        self.logger.debug("✅ 使用LlamaIndex的RouterQueryEngine进行多策略检索")
                        # 合并路由检索结果和原始结果
                        enhanced_results = self._merge_router_results(enhanced_results, router_results)
                except Exception as e:
                    self.logger.warning(f"LlamaIndex RouterQueryEngine多策略检索失败: {e}，使用原始结果")
                    # 降级：通过智能重排序融合多种信号
                    pass
            else:
                self.logger.debug("🚀 性能优化：原始结果质量已足够，跳过多策略检索")
            
            # 策略3：结果重排序 - 🚀 性能优化：渐进式增强
            # 🚀 性能优化：限制重排序数量（通常前20个结果已经足够）
            input_count = len(enhanced_results)
            
            # 🚀 P0优化：添加准确性保护机制 - 如果结果数量很少，跳过增强以避免影响准确性
            if input_count <= 2:
                self.logger.debug(f"LlamaIndex增强跳过: 结果数量过少({input_count}条)，保持原始结果以确保准确性")
                return enhanced_results
            
            # 🚀 性能优化：评估是否需要重排序
            # 如果前3个结果质量都很高，可以跳过重排序
            if quality_assessment['top3_avg_score'] > 0.85:
                self.logger.debug(
                    f"🚀 性能优化：前3个结果平均分={quality_assessment['top3_avg_score']:.3f}，"
                    f"跳过重排序以节省时间"
                )
                return enhanced_results
            
            # 🚀 升级：优先使用LlamaIndex的SimilarityPostprocessor，如果失败则降级到自定义实现
            try:
                reranked_results = self._rerank_with_llamaindex_postprocessor(
                    query, enhanced_results, max_rerank_items=20
                )
                if reranked_results:
                    self.logger.debug("✅ 使用LlamaIndex的SimilarityPostprocessor进行重排序")
                else:
                    # 降级到自定义实现
                    reranked_results = self._rerank_results(query, enhanced_results, max_rerank_items=20)
            except Exception as e:
                self.logger.warning(f"LlamaIndex SimilarityPostprocessor重排序失败: {e}，降级到自定义实现")
                reranked_results = self._rerank_results(query, enhanced_results, max_rerank_items=20)
            output_count = len(reranked_results)
            
            # 🚀 修复：确保结果数量不会减少
            if output_count < input_count:
                self.logger.warning(f"⚠️ LlamaIndex重排序后结果数量减少: {input_count} → {output_count}，尝试恢复")
                # 如果结果数量减少，检查是否有遗漏的结果
                input_ids = {r.get('knowledge_id') or r.get('id') or str(i): r for i, r in enumerate(enhanced_results)}
                output_ids = {r.get('knowledge_id') or r.get('id') or str(i): r for i, r in enumerate(reranked_results)}
                missing_ids = set(input_ids.keys()) - set(output_ids.keys())
                if missing_ids:
                    # 将遗漏的结果追加到末尾
                    for missing_id in missing_ids:
                        reranked_results.append(input_ids[missing_id])
                    self.logger.info(f"✅ 已恢复 {len(missing_ids)} 个遗漏的结果")
            
            # 🚀 P0优化：验证重排序后的结果质量 - 如果最高分显著下降，回退到原始结果
            if len(reranked_results) > 0 and len(enhanced_results) > 0:
                original_top_score = enhanced_results[0].get('similarity_score', 0.0) or enhanced_results[0].get('score', 0.0) or 0.0
                reranked_top_score = reranked_results[0].get('similarity_score', 0.0)
                
                # 如果重排序后的最高分下降超过30%，回退到原始结果
                if original_top_score > 0 and reranked_top_score < original_top_score * 0.7:
                    self.logger.warning(f"⚠️ LlamaIndex重排序导致最高分显著下降: {original_top_score:.3f} → {reranked_top_score:.3f}，回退到原始结果以确保准确性")
                    return enhanced_results
            
            # 记录增强效果
            if len(reranked_results) > 0:
                top_score = reranked_results[0].get('similarity_score', 0.0)
                self.logger.debug(f"LlamaIndex增强完成: 输入{input_count}条 → 输出{len(reranked_results)}条，最高分={top_score:.3f}")
            
            return reranked_results
            
        except Exception as e:
            self.logger.error(f"LlamaIndex 增强查询失败: {e}")
            # 降级到原始结果
            return existing_results
    
    def _expand_query(self, query: str) -> List[str]:
        """
        扩展查询，生成查询变体（P0：解决检索质量问题）
        
        Args:
            query: 原始查询
        
        Returns:
            扩展后的查询列表
        """
        try:
            # 🚀 性能优化：对于短查询，跳过扩展（减少计算开销）
            if len(query.split()) <= 3:
                return [query]
            
            # 🚀 P0实现：使用简单的关键词扩展策略
            # 策略1：提取关键实体和关系词
            expanded_queries = [query]  # 始终包含原始查询
            
            # 策略2：简单的同义词扩展（基于常见模式）
            # 注意：这里使用简单的规则，未来可以使用LLM或同义词库
            
            # 策略3：提取关键实体（大写词、引号内容等）
            import re
            # 提取引号内容
            quoted_terms = re.findall(r'"([^"]+)"', query)
            for term in quoted_terms:
                if term not in expanded_queries:
                    expanded_queries.append(term)
            
            # 提取大写词（可能是专有名词）
            capitalized_words = re.findall(r'\b[A-Z][a-z]+\b', query)
            for word in capitalized_words[:2]:  # 🚀 性能优化：从3个减少到2个
                if len(word) > 2 and word not in expanded_queries:
                    expanded_queries.append(word)
            
            # 策略4：提取数字和日期（可能是关键信息）
            numbers = re.findall(r'\d+', query)
            if numbers:
                # 如果有数字，创建包含数字的简化查询
                simplified = ' '.join([w for w in query.split() if any(n in w for n in numbers)])
                if simplified and simplified not in expanded_queries:
                    expanded_queries.append(simplified)
            
            self.logger.debug(f"查询扩展: 原始查询='{query}', 扩展后={len(expanded_queries)}个变体")
            return expanded_queries[:3]  # 🚀 性能优化：从5个减少到3个变体
            
        except Exception as e:
            self.logger.warning(f"查询扩展失败: {e}，返回原始查询")
            return [query]
    
    def _rerank_results(
        self, 
        query: str, 
        results: List[Dict[str, Any]],
        max_rerank_items: int = 20,  # 🚀 性能优化：限制重排序数量
        use_semantic_similarity: bool = True  # 🚀 升级：使用语义相似度（默认）或关键词匹配（降级）
    ) -> List[Dict[str, Any]]:
        """
        重排序结果（🚀 升级：使用语义相似度）
        
        🚀 升级说明：
        - 优先使用语义相似度（基于embedding向量）进行重排序
        - 如果无法获取embedding，降级到关键词匹配
        - 语义相似度比关键词匹配更准确，能理解同义词和语义关系
        
        Args:
            query: 查询文本
            results: 原始检索结果
            max_rerank_items: 最大重排序数量（性能优化）
            use_semantic_similarity: 是否使用语义相似度（默认True）
        
        Returns:
            重排序后的结果
        """
        if not results or len(results) <= 1:
            return results
        
        # 🚀 性能优化：如果结果数量很少，直接返回（避免不必要的计算）
        if len(results) <= 3:
            return results
        
        try:
            # 🚀 性能优化：只对前N个结果进行重排序（通常前20个已经足够）
            results_to_rerank = results[:max_rerank_items]
            remaining_results = results[max_rerank_items:]
            
            # 🚀 升级：优先使用语义相似度进行重排序
            if use_semantic_similarity and (self.text_processor or self.jina_service):
                try:
                    return self._rerank_with_semantic_similarity(
                        query, results_to_rerank, remaining_results, results
                    )
                except Exception as e:
                    self.logger.warning(f"语义相似度重排序失败: {e}，降级到关键词匹配")
                    # 降级到关键词匹配
                    use_semantic_similarity = False
            
            # 🚀 降级：使用关键词匹配（如果语义相似度不可用）
            if not use_semantic_similarity:
                return self._rerank_with_keyword_matching(
                    query, results_to_rerank, remaining_results, results
                )
            
            # 如果既没有语义相似度也没有关键词匹配，返回原始结果
            return results
            
        except Exception as e:
            self.logger.warning(f"LlamaIndex重排序失败: {e}，返回原始结果")
            return results
    
    def _rerank_with_semantic_similarity(
        self,
        query: str,
        results_to_rerank: List[Dict[str, Any]],
        remaining_results: List[Dict[str, Any]],
        all_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        🚀 升级：使用语义相似度进行重排序（基于embedding向量）
        
        这是提高准确度的根本方式，使用真正的语义理解而非关键词匹配。
        """
        import numpy as np
        
        # 1. 获取查询的embedding向量
        query_vector = None
        if self.text_processor:
            query_vector = self.text_processor.encode(query)
        elif self.jina_service:
            query_vector = self.jina_service.get_embedding(query)
        
        if query_vector is None:
            raise ValueError("无法获取查询的embedding向量")
        
        # 归一化查询向量
        query_vector = np.array(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query_vector)
        if query_norm > 0:
            query_vector = query_vector / query_norm
        
        # 2. 计算每个结果的语义相似度分数
        scored_results = []
        for result in results_to_rerank:
            content = result.get('content', '') or result.get('text', '')
            if not content:
                # 如果没有内容，使用原始分数
                original_score = result.get('similarity_score', 0.0) or result.get('score', 0.0) or 0.0
                scored_results.append((original_score, result))
                continue
            
            # 获取结果的embedding向量
            content_vector = None
            if self.text_processor:
                content_vector = self.text_processor.encode(content)
            elif self.jina_service:
                content_vector = self.jina_service.get_embedding(content)
            
            if content_vector is None:
                # 如果无法获取embedding，使用原始分数
                original_score = result.get('similarity_score', 0.0) or result.get('score', 0.0) or 0.0
                scored_results.append((original_score, result))
                continue
            
            # 归一化内容向量
            content_vector = np.array(content_vector, dtype=np.float32)
            content_norm = np.linalg.norm(content_vector)
            if content_norm > 0:
                content_vector = content_vector / content_norm
            
            # 计算余弦相似度（语义相似度）
            semantic_similarity = float(np.dot(query_vector, content_vector))
            
            # 获取原始相似度分数
            original_score = result.get('similarity_score', 0.0) or result.get('score', 0.0) or 0.0
            
            # 🚀 升级：使用语义相似度作为主要分数，原始分数作为参考
            # 综合分数 = 语义相似度 * 0.7 + 原始分数 * 0.3
            # 这样既利用了语义理解，又保留了原始检索的准确性
            combined_score = semantic_similarity * 0.7 + original_score * 0.3
            
            scored_results.append((combined_score, result))
        
        # 3. 按分数降序排序
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # 4. 更新结果的相似度分数和排序
        reranked = []
        for rank, (score, result) in enumerate(scored_results, 1):
            result_copy = result.copy()
            result_copy['similarity_score'] = score
            result_copy['rank'] = rank
            result_copy['llamaindex_rerank_score'] = score
            result_copy['llamaindex_rerank_method'] = 'semantic_similarity'  # 标记使用语义相似度
            reranked.append(result_copy)
        
        # 5. 追加剩余结果
        if remaining_results:
            for rank_offset, result in enumerate(remaining_results, start=len(reranked) + 1):
                result_copy = result.copy()
                result_copy['rank'] = rank_offset
                reranked.append(result_copy)
        
        # 6. 验证完整性
        if len(reranked) != len(all_results):
            self.logger.warning(f"⚠️ 重排序结果数量不匹配: 期望{len(all_results)}条，实际{len(reranked)}条")
            if len(reranked) < len(all_results):
                return all_results
        
        self.logger.debug(f"🚀 语义相似度重排序: 原始{len(all_results)}条 → 重排序{len(results_to_rerank)}条 → 最终{len(reranked)}条")
        return reranked
    
    def _rerank_with_keyword_matching(
        self,
        query: str,
        results_to_rerank: List[Dict[str, Any]],
        remaining_results: List[Dict[str, Any]],
        all_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        降级方案：使用关键词匹配进行重排序（P0阶段的实现）
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # 计算每个结果的相关性分数
        scored_results = []
        for result in results_to_rerank:
            content = result.get('content', '') or result.get('text', '')
            if not content:
                scored_results.append((0.0, result))
                continue
            
            content_lower = content.lower()
            content_words = set(content_lower.split())
            
            # 计算关键词匹配度
            if query_words:
                word_overlap = len(query_words & content_words) / len(query_words)
            else:
                word_overlap = 0.0
            
            # 计算短语匹配（连续词匹配）
            phrase_match = 0.0
            words = query_lower.split()
            if len(words) <= 10:
                query_phrases = []
                for i in range(len(words) - 1):
                    phrase = f"{words[i]} {words[i+1]}"
                    query_phrases.append(phrase)
                    if phrase in content_lower:
                        phrase_match += 1.0
                
                if query_phrases:
                    phrase_match = phrase_match / len(query_phrases)
            
            # 计算实体匹配（大写词、引号内容）
            entity_match = 0.0
            if any(c.isupper() for c in query):
                import re
                query_entities = set(re.findall(r'\b[A-Z][a-z]+\b', query))
                if query_entities:
                    content_entities = set(re.findall(r'\b[A-Z][a-z]+\b', content))
                    entity_overlap = len(query_entities & content_entities) / len(query_entities)
                    entity_match = entity_overlap
            
            # 综合分数（加权平均）
            original_score = result.get('similarity_score', 0.0) or result.get('score', 0.0) or 0.0
            
            # 综合分数 = 原始分数 * 0.4 + 关键词匹配 * 0.3 + 短语匹配 * 0.2 + 实体匹配 * 0.1
            combined_score = (
                original_score * 0.4 +
                word_overlap * 0.3 +
                phrase_match * 0.2 +
                entity_match * 0.1
            )
            
            scored_results.append((combined_score, result))
        
        # 按分数降序排序
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # 更新结果的相似度分数和排序
        reranked = []
        for rank, (score, result) in enumerate(scored_results, 1):
            result_copy = result.copy()
            result_copy['similarity_score'] = score
            result_copy['rank'] = rank
            result_copy['llamaindex_rerank_score'] = score
            result_copy['llamaindex_rerank_method'] = 'keyword_matching'  # 标记使用关键词匹配
            reranked.append(result_copy)
        
        # 追加剩余结果
        if remaining_results:
            for rank_offset, result in enumerate(remaining_results, start=len(reranked) + 1):
                result_copy = result.copy()
                result_copy['rank'] = rank_offset
                reranked.append(result_copy)
        
        # 验证完整性
        if len(reranked) != len(all_results):
            self.logger.warning(f"⚠️ 重排序结果数量不匹配: 期望{len(all_results)}条，实际{len(reranked)}条")
            if len(reranked) < len(all_results):
                return all_results
        
        self.logger.debug(f"关键词匹配重排序: 原始{len(all_results)}条 → 重排序{len(results_to_rerank)}条 → 最终{len(reranked)}条")
        return reranked
    
    def build_index_from_vectors(
        self, 
        vectors: List,
        texts: List[str],
        metadatas: Optional[List[Dict]] = None
    ):
        """
        从现有向量构建 LlamaIndex 索引
        
        Args:
            vectors: 向量列表
            texts: 文本列表
            metadatas: 元数据列表
        """
        if not self.enable_llamaindex:
            return
        
        try:
            from llama_index.core import Document
            from llama_index.core import VectorStoreIndex
            # FaissVectorStore 可能在不同的路径，尝试导入
            FaissVectorStore = None  # type: ignore
            try:
                from llama_index.vector_stores.faiss import FaissVectorStore  # type: ignore
            except ImportError:
                try:
                    from llama_index.vector_stores import FaissVectorStore  # type: ignore
                except ImportError:
                    self.logger.warning("FaissVectorStore 无法导入，将使用默认向量存储")
                    FaissVectorStore = None  # type: ignore
            
            if FaissVectorStore is None:
                self.logger.error("FaissVectorStore 不可用，无法构建索引")
                return
            
            import faiss
            import numpy as np
            
            # 创建 FAISS 向量存储
            dimension = len(vectors[0]) if vectors else 768
            faiss_index = faiss.IndexFlatIP(dimension)
            
            # 转换为 numpy 数组并归一化
            vectors_array = np.array(vectors).astype('float32')
            faiss.normalize_L2(vectors_array)
            faiss_index.add(vectors_array)  # type: ignore
            
            # 创建向量存储
            vector_store = FaissVectorStore(faiss_index=faiss_index)  # type: ignore
            
            # 创建文档
            documents = []
            metadata_list = metadatas if metadatas is not None else []
            for i, text in enumerate(texts):
                metadata = metadata_list[i] if i < len(metadata_list) else {}
                documents.append(Document(text=text, metadata=metadata))
            
            # 构建索引
            self.index = VectorStoreIndex.from_documents(
                documents,
                vector_store=vector_store
            )
            
            self.logger.info(f"✅ 从 {len(vectors)} 个向量构建 LlamaIndex 索引成功")
            
        except Exception as e:
            self.logger.error(f"构建 LlamaIndex 索引失败: {e}")
            self.index = None
    
    def get_index_manager(self):
        """
        获取索引管理器（阶段2：多样化索引）
        
        Returns:
            索引管理器实例
        """
        return self.index_manager
    
    def get_chat_engine(self, query_engine=None):
        """
        获取聊天引擎（阶段4：多轮对话）
        
        Args:
            query_engine: 查询引擎（可选）
        
        Returns:
            聊天引擎实例
        """
        if not self.enable_llamaindex:
            return None
        
        if self.chat_engine is None:
            try:
                from .llamaindex_chat_engine import LlamaIndexChatEngine
                self.chat_engine = LlamaIndexChatEngine(query_engine=query_engine)
            except Exception as e:
                self.logger.error(f"创建聊天引擎失败: {e}")
                return None
        
        return self.chat_engine
    
    def get_sub_question_decomposer(self, query_engines=None):
        """
        获取子问题分解器（阶段4：复杂查询）
        
        Args:
            query_engines: 查询引擎列表（可选）
        
        Returns:
            子问题分解器实例
        """
        if not self.enable_llamaindex:
            return None
        
        if self.sub_question_decomposer is None:
            try:
                from .llamaindex_sub_question import SubQuestionDecomposer
                self.sub_question_decomposer = SubQuestionDecomposer(query_engines=query_engines)
            except Exception as e:
                self.logger.error(f"创建子问题分解器失败: {e}")
                return None
        
        return self.sub_question_decomposer
    
    def _assess_result_quality(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        🚀 性能优化：评估结果质量，用于决定是否需要增强
        
        Args:
            results: 检索结果列表
        
        Returns:
            质量评估字典，包含：
            - top_score: 最高分
            - avg_score: 平均分
            - top3_avg_score: 前3个结果的平均分
            - is_high_quality: 是否高质量（top_score > 0.9 且 top3_avg_score > 0.85）
        """
        if not results:
            return {
                'top_score': 0.0,
                'avg_score': 0.0,
                'top3_avg_score': 0.0,
                'is_high_quality': False
            }
        
        # 提取分数
        scores = []
        for result in results:
            score = result.get('similarity_score', 0.0) or result.get('score', 0.0) or 0.0
            scores.append(score)
        
        if not scores:
            return {
                'top_score': 0.0,
                'avg_score': 0.0,
                'top3_avg_score': 0.0,
                'is_high_quality': False
            }
        
        top_score = scores[0]
        avg_score = sum(scores) / len(scores)
        top3_avg_score = sum(scores[:3]) / min(3, len(scores))
        
        # 🚀 性能优化：高质量标准
        # top_score > 0.9 且 top3_avg_score > 0.85 认为是高质量
        is_high_quality = top_score > 0.9 and top3_avg_score > 0.85
        
        return {
            'top_score': top_score,
            'avg_score': avg_score,
            'top3_avg_score': top3_avg_score,
            'is_high_quality': is_high_quality
        }
    
    def _cache_index(self, documents_hash: str, index: Any):
        """
        🚀 性能优化：缓存索引（避免重复构建）
        
        Args:
            documents_hash: 文档哈希
            index: 索引对象
        """
        # 限制缓存大小
        if len(self._index_cache) >= self._max_cache_size:
            # 删除最旧的缓存（FIFO）
            oldest_key = next(iter(self._index_cache))
            del self._index_cache[oldest_key]
            self.logger.debug(f"🗑️ 删除最旧的索引缓存: {oldest_key[:8]}...")
        
        # 添加新缓存
        self._index_cache[documents_hash] = index
        self.logger.debug(f"💾 缓存索引: {documents_hash[:8]}... (缓存大小: {len(self._index_cache)})")
    
    def _rerank_with_llamaindex_postprocessor(
        self,
        query: str,
        results: List[Dict[str, Any]],
        max_rerank_items: int = 20
    ) -> List[Dict[str, Any]]:
        """
        🚀 升级：使用 LlamaIndex 的 SimilarityPostprocessor 进行重排序
        
        这是真正使用LlamaIndex的重排序器，而不是自己实现的。
        """
        if not self.enable_llamaindex or not LLAMAINDEX_AVAILABLE:
            return []
        
        if not results or len(results) <= 1:
            return results
        
        try:
            from llama_index.core.postprocessor import SimilarityPostprocessor
            from llama_index.core.schema import NodeWithScore, TextNode
            from llama_index.core import QueryBundle
            
            # 1. 将结果转换为LlamaIndex的NodeWithScore格式
            nodes = []
            for i, result in enumerate(results[:max_rerank_items]):
                content = result.get('content', '') or result.get('text', '')
                if not content:
                    continue
                
                # 创建TextNode
                node = TextNode(
                    text=content,
                    metadata={
                        'knowledge_id': result.get('knowledge_id', ''),
                        'rank': i + 1,
                        **result.get('metadata', {})
                    }
                )
                
                # 获取相似度分数
                score = result.get('similarity_score', 0.0) or result.get('score', 0.0) or 0.0
                score_float = float(score) if score is not None else 0.0
                
                # 创建NodeWithScore
                node_with_score = NodeWithScore(
                    node=node,
                    score=score_float
                )
                nodes.append(node_with_score)
            
            if not nodes:
                return results
            
            # 2. 创建QueryBundle
            query_bundle = QueryBundle(query_str=query)
            
            # 3. 使用SimilarityPostprocessor进行重排序
            # 设置相似度阈值（0.0表示不过滤，只重排序）
            postprocessor = SimilarityPostprocessor(similarity_cutoff=0.0)
            
            # 4. 执行重排序
            reranked_nodes = postprocessor.postprocess_nodes(
                nodes=nodes,
                query_bundle=query_bundle
            )
            
            # 5. 转换回原始格式
            reranked_results = []
            for node_with_score in reranked_nodes:
                node = node_with_score.node
                score = node_with_score.score
                score_float = float(score) if score is not None else 0.0
                
                # 查找原始结果
                knowledge_id = node.metadata.get('knowledge_id', '')
                original_result = next(
                    (r for r in results if r.get('knowledge_id') == knowledge_id),
                    None
                )
                
                if original_result:
                    result_copy = original_result.copy()
                    result_copy['similarity_score'] = score_float
                    result_copy['llamaindex_rerank_score'] = score_float
                    result_copy['llamaindex_rerank_method'] = 'llamaindex_similarity_postprocessor'
                    reranked_results.append(result_copy)
            
            # 6. 追加剩余结果（未重排序的）
            reranked_ids = {r.get('knowledge_id') for r in reranked_results}
            remaining_results = [
                r for r in results[max_rerank_items:]
                if r.get('knowledge_id') not in reranked_ids
            ]
            reranked_results.extend(remaining_results)
            
            self.logger.debug(f"🚀 LlamaIndex SimilarityPostprocessor重排序: {len(nodes)}个节点 → {len(reranked_results)}个结果")
            return reranked_results
            
        except Exception as e:
            self.logger.error(f"LlamaIndex SimilarityPostprocessor重排序失败: {e}")
            import traceback
            self.logger.debug(f"详细错误:\n{traceback.format_exc()}")
            return []
    
    def _query_with_llamaindex_router(
        self,
        query: str,
        existing_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        🚀 升级：使用 LlamaIndex 的 RouterQueryEngine 进行多策略检索
        
        这是真正使用LlamaIndex的多策略检索，而不是自己实现的。
        """
        if not self.enable_llamaindex or not LLAMAINDEX_AVAILABLE:
            return []
        
        if not existing_results:
            return []
        
        try:
            from llama_index.core.query_engine import RouterQueryEngine
            from llama_index.core import VectorStoreIndex, Document
            
            # 1. 从现有结果构建临时的VectorStoreIndex
            documents = []
            for result in existing_results[:20]:  # 限制数量以提高性能
                content = result.get('content', '') or result.get('text', '')
                if not content:
                    continue
                
                doc = Document(
                    text=content,
                    metadata={
                        'knowledge_id': result.get('knowledge_id', ''),
                        **result.get('metadata', {})
                    }
                )
                documents.append(doc)
            
            if not documents:
                return []
            
            # 2. 🚀 性能优化：使用索引缓存（避免重复构建索引）
            import hashlib
            # 生成文档哈希（基于knowledge_id和内容）
            doc_hash = hashlib.md5(
                '|'.join([
                    f"{doc.metadata.get('knowledge_id', '')}:{doc.text[:100]}"
                    for doc in documents
                ]).encode('utf-8')
            ).hexdigest()
            
            # 检查缓存
            cached_index = self._index_cache.get(doc_hash)
            if cached_index is not None:
                self.logger.debug(f"✅ 使用缓存的VectorStoreIndex: {len(documents)}个文档")
                self.index = cached_index
            else:
                # 构建新索引
                if self.index is None:
                    try:
                        self.index = VectorStoreIndex.from_documents(documents)
                        self.logger.debug(f"✅ 构建临时VectorStoreIndex: {len(documents)}个文档")
                        
                        # 🚀 性能优化：缓存索引
                        self._cache_index(doc_hash, self.index)
                    except Exception as e:
                        self.logger.warning(f"构建VectorStoreIndex失败: {e}")
                        return []
            
            # 3. 创建向量查询引擎
            from llama_index.core.postprocessor import SimilarityPostprocessor
            vector_query_engine = self.index.as_query_engine(
                similarity_top_k=min(10, len(documents)),
                node_postprocessors=[
                    SimilarityPostprocessor(similarity_cutoff=0.7)
                ]
            )
            
            # 4. 如果有索引管理器，可以添加更多查询引擎（关键词、树索引等）
            query_engines = {"vector": vector_query_engine}
            
            if self.index_manager and self.index_manager.enabled:
                # 尝试添加关键词查询引擎
                if hasattr(self.index_manager, 'keyword_index') and self.index_manager.keyword_index:
                    try:
                        keyword_query_engine = self.index_manager.keyword_index.as_query_engine()
                        query_engines["keyword"] = keyword_query_engine
                    except Exception:
                        pass
            
            # 5. 如果只有一个查询引擎，直接使用它
            if len(query_engines) == 1:
                try:
                    response = vector_query_engine.query(query)
                    # 提取结果
                    router_results = self._extract_results_from_response(response, existing_results)
                    return router_results
                except Exception as e:
                    self.logger.warning(f"向量查询引擎查询失败: {e}")
                    return []
            
            # 6. 如果有多个查询引擎，使用RouterQueryEngine
            if LLMSingleSelector is not None and len(query_engines) > 1:
                try:
                    # 使用from_defaults方法（与llamaindex_index_manager.py中的用法一致）
                    # 注意：query_engine_tools需要是QueryEngineTool列表，这里简化处理
                    query_engine_tools = [(name, engine) for name, engine in query_engines.items()]  # type: ignore
                    router_query_engine = RouterQueryEngine.from_defaults(
                        query_engine_tools=query_engine_tools,  # type: ignore
                        selector=LLMSingleSelector.from_defaults()
                    )
                    
                    response = router_query_engine.query(query)
                    # 提取结果
                    router_results = self._extract_results_from_response(response, existing_results)
                    return router_results
                except Exception as e:
                    self.logger.warning(f"RouterQueryEngine查询失败: {e}")
                    # 降级到向量查询引擎
                    try:
                        response = vector_query_engine.query(query)
                        router_results = self._extract_results_from_response(response, existing_results)
                        return router_results
                    except Exception:
                        return []
            else:
                # 如果没有LLMSingleSelector，直接使用向量查询引擎
                try:
                    response = vector_query_engine.query(query)
                    router_results = self._extract_results_from_response(response, existing_results)
                    return router_results
                except Exception:
                    return []
            
        except Exception as e:
            self.logger.error(f"LlamaIndex RouterQueryEngine多策略检索失败: {e}")
            import traceback
            self.logger.debug(f"详细错误:\n{traceback.format_exc()}")
            return []
    
    def _extract_results_from_response(
        self,
        response: Any,
        existing_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        从LlamaIndex的响应中提取结果
        """
        try:
            results = []
            
            # 提取source_nodes（包含检索到的节点）
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node_with_score in response.source_nodes:
                    node = node_with_score.node if hasattr(node_with_score, 'node') else node_with_score
                    score = node_with_score.score if hasattr(node_with_score, 'score') else 0.0
                    
                    # 从metadata中获取knowledge_id
                    knowledge_id = None
                    if hasattr(node, 'metadata'):
                        knowledge_id = node.metadata.get('knowledge_id', '')
                    
                    # 查找原始结果
                    if knowledge_id:
                        original_result = next(
                            (r for r in existing_results if r.get('knowledge_id') == knowledge_id),
                            None
                        )
                        if original_result:
                            result_copy = original_result.copy()
                            result_copy['similarity_score'] = float(score)
                            result_copy['llamaindex_router_score'] = float(score)
                            result_copy['llamaindex_router_method'] = 'llamaindex_router_query_engine'
                            results.append(result_copy)
            
            return results
            
        except Exception as e:
            self.logger.warning(f"提取LlamaIndex响应结果失败: {e}")
            return []
    
    def _merge_router_results(
        self,
        original_results: List[Dict[str, Any]],
        router_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        合并路由检索结果和原始结果
        """
        if not router_results:
            return original_results
        
        # 创建原始结果的ID映射
        original_ids = {r.get('knowledge_id'): r for r in original_results}
        
        # 合并结果：优先使用路由检索结果，然后添加原始结果中未包含的
        merged = []
        router_ids = set()
        
        # 1. 添加路由检索结果（优先）
        for router_result in router_results:
            knowledge_id = router_result.get('knowledge_id')
            if knowledge_id:
                router_ids.add(knowledge_id)
                merged.append(router_result)
        
        # 2. 添加原始结果中未包含的
        for original_result in original_results:
            knowledge_id = original_result.get('knowledge_id')
            if knowledge_id and knowledge_id not in router_ids:
                merged.append(original_result)
        
        return merged

