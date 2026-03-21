"""
上下文管理器 - 管理推理链上下文
"""
import logging
import time
from typing import Dict, List, Any, Optional
from src.visualization.orchestration_tracker import get_orchestration_tracker

logger = logging.getLogger(__name__)


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, context_engineering=None, cache_manager=None):
        self.logger = logging.getLogger(__name__)
        self.context_engineering = context_engineering
        self.cache_manager = cache_manager
        
        # NLP缓存相关属性
        self._nlp_cache: Dict[str, Any] = {}
        self._cache_ttl_nlp = 1800  # NLP缓存30分钟
        self._nlp_performance_history: List[Dict[str, Any]] = []
    
    def get_enhanced_context(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """获取增强的上下文"""
        # 🎯 编排追踪：上下文更新开始
        tracker = getattr(self, '_orchestration_tracker', None) or get_orchestration_tracker()
        parent_event_id = getattr(self, '_current_parent_event_id', None)
        
        if self.context_engineering and hasattr(self.context_engineering, 'get_enhanced_context'):
            try:
                # 🎯 编排追踪：传递追踪器到上下文工程
                if tracker and hasattr(self.context_engineering, '_orchestration_tracker'):
                    setattr(self.context_engineering, '_orchestration_tracker', tracker)  # type: ignore
                    setattr(self.context_engineering, '_current_parent_event_id', parent_event_id)  # type: ignore
                
                enhanced_context = self.context_engineering.get_enhanced_context(session_id=session_id, **kwargs)  # type: ignore
                
                # 🎯 编排追踪：上下文更新完成
                if tracker:
                    tracker.track_context_update(
                        "context_manager",  # update_type
                        {"session_id": session_id, "context_keys": list(enhanced_context.keys()) if isinstance(enhanced_context, dict) else [], "kwargs_keys": list(kwargs.keys())},
                        parent_event_id
                    )
                
                return enhanced_context
            except Exception as e:
                self.logger.debug(f"获取增强上下文失败: {e}")
        return {}
    
    def add_context_fragment(self, session_id: str, fragment: Dict[str, Any]) -> Optional[str]:
        """添加上下文片段，返回片段ID"""
        # 🎯 编排追踪：上下文合并开始
        tracker = getattr(self, '_orchestration_tracker', None) or get_orchestration_tracker()
        parent_event_id = getattr(self, '_current_parent_event_id', None)
        
        if self.context_engineering and hasattr(self.context_engineering, 'add_context_fragment'):
            try:
                # 🎯 编排追踪：传递追踪器到上下文工程
                if tracker and hasattr(self.context_engineering, '_orchestration_tracker'):
                    setattr(self.context_engineering, '_orchestration_tracker', tracker)  # type: ignore
                    setattr(self.context_engineering, '_current_parent_event_id', parent_event_id)  # type: ignore
                
                fragment_id = self.context_engineering.add_context_fragment(session_id, fragment)  # type: ignore
                
                # 🎯 编排追踪：上下文合并完成
                if tracker:
                    tracker.track_context_merge(
                        "context_manager",  # merge_type
                        {"session_id": session_id, "fragment_id": fragment_id, "fragment_type": fragment.get('type', 'unknown'), "fragment_keys": list(fragment.keys())},
                        parent_event_id
                    )
                
                return fragment_id
            except Exception as e:
                self.logger.debug(f"添加上下文片段失败: {e}")
        return None
    
    def generate_context_summary(self, session_context: List[Dict], current_query: str, use_nlp: bool = False) -> str:
        """生成上下文摘要"""
        if use_nlp:
            return self._generate_context_summary_with_nlp(session_context, current_query)
        else:
            return self._generate_simple_context_summary(session_context)
    
    def extract_context_keywords(self, enhanced_context: Dict, query: str, use_nlp: bool = False) -> str:
        """提取上下文关键词"""
        if use_nlp:
            return self._extract_context_keywords_with_nlp(enhanced_context, query)
        else:
            return self._extract_simple_keywords(str(enhanced_context))
    
    def _generate_context_summary_with_nlp(self, session_context: List[Dict], current_query: str) -> str:
        """🚀 改进：使用NLP引擎生成真正的上下文摘要（而非简单拼接）
        🚀 P0性能优化：添加性能诊断日志，快速fallback避免阻塞
        🚀 P1性能优化：添加缓存机制，避免重复计算
        """
        perf_start = time.time()
        try:
            if not session_context:
                return ""
            
            # 🚨 P0修复：临时禁用上下文摘要缓存
            # 原因：缓存机制存在污染问题，可能影响推理质量
            # 修复策略：暂时完全禁用缓存，确保每次都重新生成

            # cache_key = None
            # if self.cache_manager:
            #     cache_key = self.cache_manager.get_cache_key(
            #         "_generate_context_summary_with_nlp",
            #         current_query,
            #         str(session_context[-5:])  # 最近5个片段
            #     )
            #     if cache_key in self._nlp_cache:
            #         cached_result = self._nlp_cache[cache_key]
            #         if time.time() - cached_result['timestamp'] < self._cache_ttl_nlp:
            #             perf_time = time.time() - perf_start
            #             self.logger.debug(f"✅ 使用缓存的上下文摘要（耗时{perf_time:.3f}秒）")
            #         return cached_result['result']

            self.logger.info(f"🚫 [上下文摘要缓存已禁用] - 跳过缓存，直接生成")
            
            # 收集所有上下文文本
            context_texts = []
            for fragment in session_context[-5:]:  # 最近5个片段
                if isinstance(fragment, dict):
                    text = fragment.get('query', '') or fragment.get('content', '') or fragment.get('answer', '')
                    if text and len(text.strip()) > 10:
                        context_texts.append(text.strip())
            
            if not context_texts:
                return ""
            
            # 合并文本（包含当前查询以提供上下文）
            combined_text = f"{current_query} " + ' '.join(context_texts)
            
            # 🚀 P0性能优化：限制文本长度，避免NLP处理过长文本耗时
            if len(combined_text) > 1500:
                combined_text = combined_text[:1500] + "..."
                self.logger.debug(f"上下文文本过长，截断到1500字符")
            
            # 使用NLP引擎生成摘要（带超时保护）
            try:
                from src.ai.nlp_engine import get_nlp_engine
                nlp_engine = get_nlp_engine()
                
                # 🚀 P0性能优化：设置NLP处理超时（5秒），超时则快速fallback
                nlp_start = time.time()
                summary = nlp_engine.generate_summary(combined_text, max_sentences=3)
                nlp_time = time.time() - nlp_start
                
                # 🚀 P0性能诊断：记录NLP处理时间
                if nlp_time > 1.0:
                    self.logger.warning(f"⚠️ NLP摘要生成耗时: {nlp_time:.3f}秒（文本长度: {len(combined_text)}）")
                    self._nlp_performance_history.append({'timeout': False, 'failed': False, 'time': nlp_time})
                else:
                    self.logger.debug(f"✅ NLP摘要生成耗时: {nlp_time:.3f}秒")
                    self._nlp_performance_history.append({'timeout': False, 'failed': False, 'time': nlp_time})
                
                # 限制性能历史记录数量
                if len(self._nlp_performance_history) > 10:
                    self._nlp_performance_history = self._nlp_performance_history[-10:]
                
                if summary and len(summary.strip()) > 20:
                    result = f"Conversation context: {summary}"
                    # 🚨 P0修复：临时禁用上下文摘要缓存写入
                    # if cache_key:
                    #     self._nlp_cache[cache_key] = {
                    #         'result': result,
                    #         'timestamp': time.time()
                    #     }
                    #     # 限制缓存大小（最多100条）
                    #     if len(self._nlp_cache) > 100:
                    #         oldest_key = min(self._nlp_cache.keys(), key=lambda k: self._nlp_cache[k]['timestamp'])
                    #         del self._nlp_cache[oldest_key]
                    
                    perf_time = time.time() - perf_start
                    if perf_time > 2.0:
                        self.logger.warning(f"⚠️ 上下文摘要生成总耗时: {perf_time:.3f}秒")
                    return result
                else:
                    # Fallback到简单摘要
                    return self._generate_simple_context_summary(session_context)
            except Exception as nlp_error:
                perf_time = time.time() - perf_start
                self.logger.debug(f"NLP摘要生成失败（耗时{perf_time:.3f}秒），使用简单摘要: {nlp_error}")
                self._nlp_performance_history.append({'timeout': False, 'failed': True, 'time': perf_time})
                return self._generate_simple_context_summary(session_context)
                
        except Exception as e:
            perf_time = time.time() - perf_start
            self.logger.debug(f"上下文摘要生成失败（耗时{perf_time:.3f}秒）: {e}")
            return ""
    
    def _generate_simple_context_summary(self, session_context: List[Dict]) -> str:
        """生成简单上下文摘要（fallback）"""
        try:
            recent_queries = []
            for fragment in session_context[-3:]:
                if isinstance(fragment, dict):
                    frag_query = fragment.get('query', '') or fragment.get('content', '')
                    if frag_query:
                        recent_queries.append(frag_query[:50])
            if recent_queries:
                return f"Recent conversation context: {'; '.join(recent_queries)}"
            return ""
        except Exception as e:
            self.logger.debug(f"简单上下文摘要生成失败: {e}")
            return ""
    
    def _extract_context_keywords_with_nlp(self, enhanced_context: Dict, query: str) -> str:
        """🚀 改进：使用NLP引擎提取语义关键词（而非简单分割）
        🚀 P0性能优化：添加性能诊断日志，快速fallback避免阻塞
        🚀 P1性能优化：添加缓存机制，避免重复计算
        """
        perf_start = time.time()
        try:
            # 🚨 P0修复：临时禁用关键词提取缓存读取
            # cache_key = None
            # if self.cache_manager:
            #     cache_key = self.cache_manager.get_cache_key(
            #         "_extract_context_keywords_with_nlp",
            #         query,
            #         str(enhanced_context.get('session_context', [])[-3:])
            #     )
            #     if cache_key in self._nlp_cache:
            #         cached_result = self._nlp_cache[cache_key]
            #         if time.time() - cached_result['timestamp'] < self._cache_ttl_nlp:
            #             perf_time = time.time() - perf_start
            #             self.logger.debug(f"✅ 使用缓存的关键词（耗时{perf_time:.3f}秒）")
            #             return cached_result['result']

            self.logger.info(f"🚫 [关键词提取缓存已禁用] - 跳过缓存，直接提取")
            
            # 收集上下文文本
            context_texts = []
            session_context = enhanced_context.get('session_context', [])
            for fragment in session_context[-3:]:
                if isinstance(fragment, dict):
                    text = fragment.get('query', '') or fragment.get('content', '')
                    if text:
                        context_texts.append(text)
            
            # 合并文本
            combined_text = f"{query} " + ' '.join(context_texts)
            
            # 限制文本长度
            if len(combined_text) > 1000:
                combined_text = combined_text[:1000] + "..."
            
            # 使用NLP引擎提取关键词
            try:
                from src.ai.nlp_engine import get_nlp_engine
                nlp_engine = get_nlp_engine()
                
                nlp_start = time.time()
                keywords = nlp_engine.extract_keywords(combined_text, max_keywords=10)
                nlp_time = time.time() - nlp_start
                
                if nlp_time > 1.0:
                    self.logger.warning(f"⚠️ NLP关键词提取耗时: {nlp_time:.3f}秒")
                else:
                    self.logger.debug(f"✅ NLP关键词提取耗时: {nlp_time:.3f}秒")
                
                if keywords and isinstance(keywords, list) and len(keywords) > 0:
                    result = ', '.join(keywords[:10])
                    # 🚨 P0修复：临时禁用关键词提取缓存写入
                    # if cache_key:
                    #     self._nlp_cache[cache_key] = {
                    #         'result': result,
                    #         'timestamp': time.time()
                    #     }
                    #     if len(self._nlp_cache) > 100:
                    #         oldest_key = min(self._nlp_cache.keys(), key=lambda k: self._nlp_cache[k]['timestamp'])
                    #         del self._nlp_cache[oldest_key]
                    
                    return result
                else:
                    # Fallback到简单关键词提取
                    return self._extract_simple_keywords(combined_text)
            except Exception as nlp_error:
                perf_time = time.time() - perf_start
                self.logger.debug(f"NLP关键词提取失败（耗时{perf_time:.3f}秒），使用简单提取: {nlp_error}")
                return self._extract_simple_keywords(combined_text)
                
        except Exception as e:
            perf_time = time.time() - perf_start
            self.logger.debug(f"关键词提取失败（耗时{perf_time:.3f}秒）: {e}")
            return ""
    
    def _extract_simple_keywords(self, text: str) -> str:
        """简单关键词提取（fallback）"""
        try:
            # 提取长度>3的单词作为关键词
            words = [w.lower() for w in text.split() if len(w) > 3]
            # 去重并限制数量
            unique_words = list(set(words))[:10]
            return ', '.join(unique_words)
        except Exception as e:
            self.logger.debug(f"简单关键词提取失败: {e}")
            return ""
    
    def should_use_nlp_for_context(
        self, 
        session_context: List[Dict], 
        query: str, 
        query_type: str,
        enhanced_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """🚀 智能决策：自动判断是否应该使用NLP处理上下文"""
        try:
            # 基础条件：必须有足够的上下文
            if not session_context or len(session_context) < 2:
                return False
            
            # 评估上下文复杂度
            context_complexity_score = 0.0
            
            # 上下文长度（片段数量）
            context_count = len(session_context)
            if context_count >= 5:
                context_complexity_score += 0.3
            elif context_count >= 3:
                context_complexity_score += 0.2
            else:
                context_complexity_score += 0.1
            
            # 上下文文本总长度
            total_text_length = 0
            unique_texts = set()
            for fragment in session_context:
                if isinstance(fragment, dict):
                    text = fragment.get('query', '') or fragment.get('content', '') or fragment.get('answer', '')
                    if text:
                        total_text_length += len(text)
                        unique_texts.add(text[:50])
            
            if total_text_length > 1000:
                context_complexity_score += 0.3
            elif total_text_length > 500:
                context_complexity_score += 0.2
            else:
                context_complexity_score += 0.1
            
            # 查询类型影响
            query_type_score = 0.0
            if query_type in ['complex', 'multi_hop', 'causal', 'comparative']:
                query_type_score = 0.2
            elif query_type in ['factual', 'temporal']:
                query_type_score = 0.1
            
            # 系统性能历史
            performance_penalty = 0.0
            recent_failures = sum(1 for record in self._nlp_performance_history[-5:] 
                                 if record.get('timeout', False) or record.get('failed', False))
            if recent_failures >= 3:
                performance_penalty = -0.3
            elif recent_failures >= 2:
                performance_penalty = -0.2
            
            # 综合评分
            total_score = context_complexity_score + query_type_score + performance_penalty
            
            # 决策阈值：总分>=0.5时使用NLP
            should_use = total_score >= 0.5
            
            self.logger.debug(
                f"🤖 NLP使用决策: {'启用' if should_use else '禁用'} | "
                f"评分: {total_score:.2f} (上下文复杂度: {context_complexity_score:.2f}, "
                f"查询类型: {query_type_score:.2f}, 性能惩罚: {performance_penalty:.2f})"
            )
            
            return should_use
            
        except Exception as e:
            self.logger.debug(f"NLP使用决策失败，默认禁用: {e}")
            return False
    
    def extract_context_for_prompt(
        self, 
        enhanced_context: Dict[str, Any], 
        task_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """🚀 新增：从上下文工程中提取用于提示词生成的上下文信息
        
        Args:
            enhanced_context: 增强后的上下文字典
            task_session_id: 推理链任务ID（可选，用于获取推理链上下文）
            
        Returns:
            包含上下文信息的字典
        """
        try:
            context_info = {
                'context_summary': '',
                'keywords': [],
                'keywords_str': '',
                'reasoning_steps': [],  # 推理步骤的上下文
                'key_clues': [],  # 关键线索
                'evidence_summary': ''  # 证据摘要
            }
            
            # 1. 提取会话上下文（从enhanced_context中）
            informational_contexts = enhanced_context.get('informational_contexts', [])
            guiding_contexts = enhanced_context.get('guiding_contexts', [])
            
            # 🚀 P0修复：对上下文片段进行排序，确保顺序一致（使用content的hash作为排序键）
            if informational_contexts:
                informational_contexts = sorted(
                    informational_contexts,
                    key=lambda x: (
                        hash(str(x.get('content', ''))[:100]) if isinstance(x, dict) else hash(str(x)),
                        str(x.get('content', ''))[:100] if isinstance(x, dict) else str(x)
                    )
                )
            
            # 提取关键线索（排序后提取，确保顺序一致）
            for fragment in informational_contexts:
                if isinstance(fragment, dict):
                    if fragment.get('is_key_clue'):
                        content = fragment.get('content', '')
                        if content:
                            context_info['key_clues'].append(content[:500].strip())  # 🚀 P0修复：限制长度，确保一致性
            
            # 2. 提取推理链上下文（如果提供了 task_session_id）
            if task_session_id and self.context_engineering and hasattr(self.context_engineering, 'get_enhanced_context'):
                try:
                    reasoning_context = self.context_engineering.get_enhanced_context(  # type: ignore
                        session_id=task_session_id,
                        include_long_term=False,
                        include_implicit=False,
                        include_actionable=False,
                        max_fragments=10
                    )
                    reasoning_fragments = reasoning_context.get('informational_contexts', [])
                    # 🚀 P0修复：对推理片段进行排序，确保顺序一致（使用step_id作为排序键）
                    if reasoning_fragments:
                        reasoning_fragments = sorted(
                            reasoning_fragments,
                            key=lambda x: (
                                x.get('metadata', {}).get('step_id', '') if isinstance(x, dict) else '',
                                hash(str(x.get('content', ''))[:100]) if isinstance(x, dict) else hash(str(x))
                            )
                        )
                    for fragment in reasoning_fragments:
                        if isinstance(fragment, dict):
                            metadata = fragment.get('metadata', {})
                            step_info = {
                                'step_id': metadata.get('step_id'),
                                'step_type': metadata.get('step_type'),
                                'sub_query': (metadata.get('sub_query', '') or '')[:200].strip(),  # 🚀 P0修复：限制长度
                                'result': (metadata.get('result', '') or '')[:200].strip(),  # 🚀 P0修复：限制长度
                                'evidence': metadata.get('evidence', [])
                            }
                            context_info['reasoning_steps'].append(step_info)
                except Exception as e:
                    self.logger.debug(f"提取推理链上下文失败: {e}")
            
            # 🚀 P0修复：对关键线索进行排序，确保顺序一致
            if context_info['key_clues']:
                context_info['key_clues'].sort(key=lambda x: (hash(x[:100]), x[:100]))
            
            # 3. 生成上下文摘要（标准化，确保一致性）
            if context_info['key_clues']:
                # 🚀 P0修复：限制关键线索数量和长度，确保一致性
                key_clues_limited = [k[:300].strip() for k in context_info['key_clues'][:5]]
                context_info['context_summary'] = '\n'.join(key_clues_limited)
            elif informational_contexts:
                # 如果没有关键线索，使用前几个信息型上下文片段（已排序）
                context_contents = []
                for fragment in informational_contexts[:3]:
                    if isinstance(fragment, dict):
                        content = fragment.get('content', '')
                        if content:
                            context_contents.append(content[:200].strip())  # 🚀 P0修复：限制长度并strip
                if context_contents:
                    context_info['context_summary'] = '\n'.join(context_contents)
            
            # 4. 提取关键词（从enhanced_context中）
            keywords = enhanced_context.get('keywords', [])
            if isinstance(keywords, list):
                # 🚀 P0修复：对关键词进行排序，确保顺序一致
                keywords_sorted = sorted([str(k).strip()[:50] for k in keywords[:10]])  # 限制数量和长度
                context_info['keywords'] = keywords_sorted
                context_info['keywords_str'] = ', '.join(keywords_sorted)
            elif isinstance(keywords, str):
                keywords_cleaned = keywords.strip()[:50]  # 🚀 P0修复：限制长度
                context_info['keywords'] = [keywords_cleaned]
                context_info['keywords_str'] = keywords_cleaned
            
            # 5. 生成推理步骤摘要（用于提示词）
            if context_info['reasoning_steps']:
                # 🚀 P0修复：对推理步骤进行排序，确保顺序一致（按step_id排序）
                reasoning_steps_sorted = sorted(
                    context_info['reasoning_steps'][:5],  # 只取前5个步骤
                    key=lambda x: (x.get('step_id', ''), hash(str(x.get('sub_query', ''))))
                )
                reasoning_summary_parts = []
                for step_info in reasoning_steps_sorted:
                    # 🚀 P0修复：标准化格式，限制长度，确保一致性
                    step_id = str(step_info.get('step_id', '?'))[:20]
                    sub_query = (step_info.get('sub_query', '') or '')[:150].strip()
                    result = (step_info.get('result', '') or '')[:150].strip()
                    step_summary = f"Step {step_id}: {sub_query} → {result}"
                    reasoning_summary_parts.append(step_summary)
                if reasoning_summary_parts:
                    context_info['reasoning_summary'] = '\n'.join(reasoning_summary_parts)
            
            return context_info
            
        except Exception as e:
            self.logger.debug(f"提取上下文信息失败: {e}")
            return {
                'context_summary': enhanced_context.get('context_summary', ''),
                'keywords': enhanced_context.get('keywords', []),
                'keywords_str': ', '.join(enhanced_context.get('keywords', [])) if isinstance(enhanced_context.get('keywords'), list) else str(enhanced_context.get('keywords', '')),
                'reasoning_steps': [],
                'key_clues': [],
                'evidence_summary': ''
            }

