"""
动态分块检索器

解决"大海捞针"问题：对长文档进行智能分块，提高检索精度。
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChunkInfo:
    """分块信息"""
    content: str
    start_pos: int
    end_pos: int
    chunk_type: str  # paragraph, list, table, sentence
    relevance_score: float
    original_doc: Dict[str, Any]


class DynamicChunkingRetriever:
    """动态分块检索器 - 解决信息粒度不匹配问题"""
    
    def __init__(self, llm_integration=None, chunk_size=500, overlap=50):
        """
        初始化动态分块检索器
        
        Args:
            llm_integration: LLM集成（可选，用于高级分析）
            chunk_size: 分块大小（字符数）
            overlap: 分块重叠大小（字符数）
        """
        self.llm_integration = llm_integration
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.logger = logging.getLogger(__name__)
        # 确保logger已配置
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def retrieve_with_chunking(
        self, 
        query: str, 
        original_docs: List[Dict[str, Any]], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """对检索结果进行动态分块和重新评分
        
        Args:
            query: 查询文本
            original_docs: 原始检索结果
            top_k: 返回前k个结果
            
        Returns:
            分块后的检索结果列表
        """
        try:
            chunked_results = []
            
            for doc in original_docs:
                content = doc.get('content', '') or doc.get('text', '')
                if not content or len(content) < 100:
                    # 内容太短，直接使用
                    chunked_results.append({
                        **doc,
                        'chunk_type': 'short',
                        'chunk_relevance': doc.get('similarity', 0.5) or doc.get('similarity_score', 0.5)
                    })
                    continue
                
                # 1. 智能分块
                chunks = self._smart_chunking(content)
                
                # 2. 为每个块计算查询相关性
                for chunk in chunks:
                    relevance_score = self._compute_chunk_relevance(chunk.content, query, doc)
                    
                    # 考虑块的类型
                    if self._is_likely_answer_in_chunk(chunk.content, query):
                        relevance_score *= 1.5
                    
                    chunked_results.append({
                        'content': chunk.content,
                        'original_doc': doc,
                        'similarity': relevance_score,
                        'similarity_score': relevance_score,
                        'chunk_type': chunk.chunk_type,
                        'chunk_start': chunk.start_pos,
                        'chunk_end': chunk.end_pos,
                        'metadata': doc.get('metadata', {}),
                        'source': doc.get('source', 'unknown'),
                        'knowledge_id': doc.get('knowledge_id'),
                        'chunk_relevance': relevance_score
                    })
            
            # 3. 重新排序
            chunked_results.sort(key=lambda x: x.get('chunk_relevance', 0.0), reverse=True)
            
            # 4. 去重（避免同一文档的多个块都返回）
            deduplicated = self._deduplicate_chunks(chunked_results, top_k)
            
            self.logger.info(f"🔍 [动态分块] 原始文档: {len(original_docs)}, 分块后: {len(chunked_results)}, 去重后: {len(deduplicated)}")
            
            return deduplicated[:top_k]
            
        except Exception as e:
            self.logger.error(f"动态分块检索失败: {e}", exc_info=True)
            # 失败时返回原始结果
            return original_docs[:top_k]
    
    def _smart_chunking(self, content: str) -> List[ChunkInfo]:
        """智能分块，尊重文档结构
        
        Args:
            content: 文档内容
            
        Returns:
            分块信息列表
        """
        chunks = []
        
        # 策略1: 优先按段落分块
        paragraphs = re.split(r'\n\s*\n+', content)
        
        current_pos = 0
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_start = current_pos
            para_end = current_pos + len(para)
            
            # 检查段落类型
            chunk_type = self._classify_chunk_type(para)
            
            if len(para) > self.chunk_size:
                # 大段落进一步分割
                sub_chunks = self._split_by_sentences(para, para_start)
                chunks.extend(sub_chunks)
            else:
                chunks.append(ChunkInfo(
                    content=para,
                    start_pos=para_start,
                    end_pos=para_end,
                    chunk_type=chunk_type,
                    relevance_score=0.0,  # 稍后计算
                    original_doc={}
                ))
            
            current_pos = para_end + 2  # +2 for \n\n
        
        # 如果没有找到段落，按句子分割
        if not chunks:
            chunks = self._split_by_sentences(content, 0)
        
        return chunks
    
    def _split_by_sentences(self, text: str, start_pos: int) -> List[ChunkInfo]:
        """按句子分割文本
        
        Args:
            text: 文本内容
            start_pos: 起始位置
            
        Returns:
            分块信息列表
        """
        chunks = []
        
        # 句子分割模式
        sentence_pattern = r'[.!?]\s+'
        sentences = re.split(sentence_pattern, text)
        
        current_chunk = ""
        current_start = start_pos
        current_pos = start_pos
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 如果当前块加上新句子超过大小限制，保存当前块
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunk_type = self._classify_chunk_type(current_chunk)
                chunks.append(ChunkInfo(
                    content=current_chunk.strip(),
                    start_pos=current_start,
                    end_pos=current_pos,
                    chunk_type=chunk_type,
                    relevance_score=0.0,
                    original_doc={}
                ))
                current_chunk = sentence
                current_start = current_pos
            else:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
            
            current_pos += len(sentence) + 2  # +2 for ". "
        
        # 添加最后一个块
        if current_chunk:
            chunk_type = self._classify_chunk_type(current_chunk)
            chunks.append(ChunkInfo(
                content=current_chunk.strip(),
                start_pos=current_start,
                end_pos=current_pos,
                chunk_type=chunk_type,
                relevance_score=0.0,
                original_doc={}
            ))
        
        return chunks
    
    def _classify_chunk_type(self, text: str) -> str:
        """分类块类型
        
        Args:
            text: 文本内容
            
        Returns:
            块类型：paragraph, list, table, sentence
        """
        text_lower = text.lower()
        
        # 检查是否是列表
        list_indicators = [
            r'^\d+[\.\)]\s+',  # 数字列表
            r'^[•\-\*]\s+',  # 项目符号
            r'^\w+:\s*\n',  # 键值对列表
        ]
        for pattern in list_indicators:
            if re.search(pattern, text, re.MULTILINE):
                return 'list'
        
        # 检查是否是表格
        if '\t' in text or '|' in text:
            lines = text.split('\n')
            if len(lines) > 2 and any('|' in line or '\t' in line for line in lines[:3]):
                return 'table'
        
        # 检查是否是段落
        if len(text) > 200 and '\n' in text:
            return 'paragraph'
        
        return 'sentence'
    
    def _compute_chunk_relevance(
        self, 
        chunk_content: str, 
        query: str, 
        original_doc: Dict[str, Any]
    ) -> float:
        """计算块与查询的相关性
        
        Args:
            chunk_content: 块内容
            query: 查询文本
            original_doc: 原始文档
            
        Returns:
            相关性分数 (0.0-1.0)
        """
        # 基础分数：使用原始文档的相似度
        base_score = original_doc.get('similarity', 0.5) or original_doc.get('similarity_score', 0.5)
        
        # 关键词匹配增强
        query_lower = query.lower()
        chunk_lower = chunk_content.lower()
        
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        chunk_words = set(re.findall(r'\b\w+\b', chunk_lower))
        
        # 计算关键词重叠率
        if query_words:
            overlap_ratio = len(query_words & chunk_words) / len(query_words)
            # 关键词匹配可以提升分数
            enhanced_score = base_score + (overlap_ratio * 0.3)
            return min(enhanced_score, 1.0)
        
        return base_score
    
    def _is_likely_answer_in_chunk(self, chunk_content: str, query: str) -> bool:
        """判断块中是否可能包含答案
        
        Args:
            chunk_content: 块内容
            query: 查询文本
            
        Returns:
            是否可能包含答案
        """
        query_lower = query.lower()
        chunk_lower = chunk_content.lower()
        
        # 检查查询中的关键实体是否在块中
        # 提取可能的实体（大写开头的词、数字等）
        query_entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        query_entities.extend(re.findall(r'\d+(?:st|nd|rd|th)', query_lower))
        
        for entity in query_entities:
            if entity.lower() in chunk_lower:
                return True
        
        # 检查是否是列表类型（列表通常包含答案）
        if self._classify_chunk_type(chunk_content) == 'list':
            return True
        
        return False
    
    def _deduplicate_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        top_k: int
    ) -> List[Dict[str, Any]]:
        """去重分块结果（避免同一文档的多个块都返回）
        
        Args:
            chunks: 分块结果列表
            top_k: 返回数量
            
        Returns:
            去重后的分块列表
        """
        seen_docs = {}
        deduplicated = []
        
        for chunk in chunks:
            doc_id = chunk.get('knowledge_id') or chunk.get('source', 'unknown')
            
            # 如果这个文档还没有被选择，或者这个块的相关性更高
            if doc_id not in seen_docs:
                seen_docs[doc_id] = chunk
                deduplicated.append(chunk)
            else:
                # 如果这个块的相关性更高，替换之前的
                existing_score = seen_docs[doc_id].get('chunk_relevance', 0.0)
                current_score = chunk.get('chunk_relevance', 0.0)
                if current_score > existing_score:
                    # 替换
                    deduplicated.remove(seen_docs[doc_id])
                    seen_docs[doc_id] = chunk
                    deduplicated.append(chunk)
        
        # 重新排序
        deduplicated.sort(key=lambda x: x.get('chunk_relevance', 0.0), reverse=True)
        
        return deduplicated

