"""
内容处理模块
负责内容的压缩、清理和格式化
"""

from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)


class ContentProcessor:
    """内容处理器 - 负责内容的压缩、清理和格式化"""
    
    def __init__(self, fast_llm_integration=None):
        """初始化内容处理器
        
        Args:
            fast_llm_integration: 快速LLM集成（可选，用于智能压缩）
        """
        self.fast_llm_integration = fast_llm_integration
    
    def compress_content(
        self,
        content: str,
        query: str,
        query_type: str,
        max_length: int = 1200  # 🚀 增加默认max_length，从800增加到1200
    ) -> str:
        """
        🚀 智能化优化：使用LLM智能压缩内容，保留关键信息
        
        不使用硬编码规则，而是让LLM理解查询意图并提取相关内容。
        
        Args:
            content: 原始内容
            query: 查询文本
            query_type: 查询类型
            max_length: 最大长度（字符数）
        
        Returns:
            压缩后的内容
        """
        if not content or len(content) <= max_length:
            return content
        
        # 🚀 智能化优化：优先使用LLM智能提取关键信息
        if self.fast_llm_integration:
            try:
                compressed = self.compress_content_with_llm(content, query, max_length)
                if compressed and len(compressed.strip()) >= 50:  # 确保压缩后内容足够
                    logger.debug(f"✅ 使用LLM智能压缩: {len(content)} → {len(compressed)} 字符")
                    return compressed
            except Exception as e:
                logger.debug(f"LLM压缩失败，使用fallback策略: {e}")
        
        # Fallback策略：使用基于规则的压缩（但更宽松）
        # 策略1: 提取关键句子（基于查询关键词）
        key_sentences = self.extract_key_sentences(content, query, max_length)
        if key_sentences and len(key_sentences.strip()) >= 50:
            logger.debug(f"✅ 使用关键句子压缩: {len(content)} → {len(key_sentences)} 字符")
            return key_sentences
        
        # 策略2: 如果所有策略都失败，保留更多内容（增加到max_length * 1.2）
        extended_length = int(max_length * 1.2)
        return content[:extended_length] + '...'
    
    def compress_content_with_llm(self, content: str, query: str, max_length: int) -> Optional[str]:
        """🚀 智能化优化：使用LLM智能压缩内容，保留与查询相关的关键信息"""
        try:
            if not self.fast_llm_integration:
                return None
            
            prompt = f"""You are an expert at extracting relevant information from text. Your task is to compress the following content while preserving ALL information that is relevant to the query.

**Query**: {query}

**Content** (to compress):
{content[:4000]}  # 限制输入长度，避免token过多

**Requirements**:
1. Preserve ALL information that directly answers the query
2. Keep relevant context and details
3. Remove only irrelevant or redundant information
4. Maintain readability and coherence
5. Maximum length: {max_length} characters
6. If the content is already relevant and concise, return it as-is

**Return ONLY the compressed content, no explanations:**

Compressed content:"""
            
            response = self.fast_llm_integration._call_llm(prompt)
            if response:
                compressed = response.strip()
                # 确保压缩后的内容不超过max_length
                if len(compressed) > max_length:
                    compressed = compressed[:max_length] + '...'
                return compressed
            
            return None
            
        except Exception as e:
            logger.debug(f"LLM压缩内容失败: {e}")
            return None
    
    def extract_key_sentences(
        self,
        content: str,
        query: str,
        max_length: int
    ) -> str:
        """
        🚀 阶段1优化：提取包含查询关键词的关键句子
        """
        if not content or not query:
            return content[:max_length] if content else ""
        
        query_keywords = set(query.lower().split())
        # 过滤掉太短的词（<3字符）
        query_keywords = {kw for kw in query_keywords if len(kw) > 2}
        
        if not query_keywords:
            # 如果没有关键词，返回开头部分
            return content[:max_length]
        
        # 按句子分割
        sentences = re.split(r'[.!?。！？]\s+', content)
        
        # 计算每个句子的相关性
        scored_sentences = []
        for sentence in sentences:
            if len(sentence.strip()) < 10:
                continue
            
            sentence_lower = sentence.lower()
            # 计算匹配的关键词数量
            keyword_count = sum(1 for kw in query_keywords if kw in sentence_lower)
            if keyword_count > 0:
                # 相关性分数 = 关键词匹配数 / 查询关键词总数
                relevance_score = keyword_count / len(query_keywords)
                scored_sentences.append((relevance_score, sentence))
        
        if not scored_sentences:
            # 如果没有匹配的句子，返回开头部分
            return content[:max_length]
        
        # 按相关性排序
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        # 选择句子直到达到长度限制
        selected = []
        total_length = 0
        for score, sentence in scored_sentences:
            sentence_with_dot = sentence + '. '
            if total_length + len(sentence_with_dot) <= max_length:
                selected.append(sentence)
                total_length += len(sentence_with_dot)
            else:
                # 如果加上这个句子会超出，检查是否可以截断
                remaining = max_length - total_length
                if remaining > 50:  # 至少保留50字符
                    selected.append(sentence[:remaining-3] + '...')
                break
        
        result = '. '.join(selected) + '.' if selected else content[:max_length]
        return result
    
    def extract_ranking_list(self, content: str, query: str) -> Optional[str]:
        """
        🚀 阶段1优化：提取排名列表（用于排名查询）
        
        查找格式如 "1st", "2nd", "37th" 或 "1.", "2.", "37." 的排名列表
        """
        # 匹配排名模式：数字 + (st|nd|rd|th|.)
        ranking_pattern = r'(\d+)(?:st|nd|rd|th|\.)\s+([^\n]+?)(?=\n|\d+(?:st|nd|rd|th|\.)|$)'
        matches = re.finditer(ranking_pattern, content, re.IGNORECASE | re.MULTILINE)
        
        ranking_items = []
        for match in matches:
            rank = match.group(1)
            item = match.group(2).strip()
            # 限制item长度，避免过长
            if len(item) > 100:
                item = item[:100] + '...'
            ranking_items.append(f"{rank}{'th' if rank.endswith(('1', '2', '3')) else 'th'}: {item}")
        
        if ranking_items:
            # 返回排名列表（最多50项）
            return '\n'.join(ranking_items[:50])
        
        return None
    
    def extract_numerical_facts(self, content: str, query: str) -> Optional[str]:
        """
        🚀 阶段1优化：提取数值和关键事实（用于数值查询）
        """
        # 提取包含数字的句子
        sentences = re.split(r'[.!?。！？]\s+', content)
        sentences_with_numbers = [
            s.strip() for s in sentences
            if re.search(r'\d+', s) and len(s.strip()) > 10
        ]
        
        if sentences_with_numbers:
            # 提取查询关键词
            query_keywords = set(query.lower().split())
            query_keywords = {kw for kw in query_keywords if len(kw) > 2}
            
            # 如果有关键词，优先选择包含关键词的句子
            if query_keywords:
                scored = []
                for sentence in sentences_with_numbers:
                    sentence_lower = sentence.lower()
                    matches = sum(1 for kw in query_keywords if kw in sentence_lower)
                    if matches > 0:
                        scored.append((matches, sentence))
                
                if scored:
                    scored.sort(reverse=True)
                    return '. '.join([s for _, s in scored[:5]]) + '.'
            
            # 否则返回前几个包含数字的句子
            return '. '.join(sentences_with_numbers[:5]) + '.'
        
        return None
    
    def extract_entity_info(self, content: str, query: str) -> Optional[str]:
        """
        🚀 重构：使用统一实体提取服务（SemanticUnderstandingPipeline）
        
        提取实体和属性（用于实体查询）
        """
        try:
            # 🚀 使用统一实体提取服务
            from src.utils.semantic_understanding_pipeline import get_semantic_understanding_pipeline
            
            semantic_pipeline = get_semantic_understanding_pipeline()
            
            # 提取查询和内容中的实体
            query_entities = semantic_pipeline.extract_entities_intelligent(query)
            content_entities = semantic_pipeline.extract_entities_intelligent(content)
            
            # 如果找到实体，提取包含这些实体的句子
            if query_entities or content_entities:
                # 收集所有实体文本
                entity_texts = set()
                for entity in query_entities:
                    entity_texts.add(entity.get('text', '').lower())
                for entity in content_entities:
                    entity_texts.add(entity.get('text', '').lower())
                
                # 提取包含实体的句子
                sentences = re.split(r'[.!?。！？]\s+', content)
                relevant_sentences = []
                
                for sentence in sentences:
                    if len(sentence.strip()) < 10:
                        continue
                    sentence_lower = sentence.lower()
                    # 检查是否包含实体
                    if any(entity_text in sentence_lower for entity_text in entity_texts if entity_text):
                        relevant_sentences.append(sentence.strip())
                
                if relevant_sentences:
                    return '. '.join(relevant_sentences[:5]) + '.'
            
            # Fallback: 使用简单的关键词匹配
            query_keywords = set(query.lower().split())
            query_keywords = {kw for kw in query_keywords if len(kw) > 2}
            
            if not query_keywords:
                return None
            
            sentences = re.split(r'[.!?。！？]\s+', content)
            relevant_sentences = []
            
            for sentence in sentences:
                if len(sentence.strip()) < 10:
                    continue
                sentence_lower = sentence.lower()
                # 检查是否包含查询关键词
                if any(kw in sentence_lower for kw in query_keywords):
                    relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                return '. '.join(relevant_sentences[:5]) + '.'
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ 使用统一实体提取服务失败: {e}，使用fallback")
            # Fallback: 使用简单的关键词匹配
            query_keywords = set(query.lower().split())
            query_keywords = {kw for kw in query_keywords if len(kw) > 2}
            
            if not query_keywords:
                return None
            
            sentences = re.split(r'[.!?。！？]\s+', content)
            relevant_sentences = []
            
            for sentence in sentences:
                if len(sentence.strip()) < 10:
                    continue
                sentence_lower = sentence.lower()
                if any(kw in sentence_lower for kw in query_keywords):
                    relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                return '. '.join(relevant_sentences[:5]) + '.'
            
            return None

