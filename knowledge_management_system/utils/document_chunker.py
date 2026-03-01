#!/usr/bin/env python3
"""
文档分块工具
实现前沿的文档分块策略，用于知识库构建
支持递归分块、语义分块等策略
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from ..utils.logger import get_logger

logger = get_logger()


class DocumentChunker:
    """文档分块器 - 支持多种分块策略"""
    
    def __init__(
        self,
        max_chunk_size: int = 3000,  # 🚀 优化：从8000降低到3000（约1024 token，符合文章建议的甜点区）
        overlap_ratio: float = 0.2,
        min_chunk_size: int = 200,
        chunk_strategy: str = "recursive",
        enable_lazy_chunking: bool = True  # 🚀 新增：是否启用Lazy Chunking
    ):
        """
        初始化文档分块器
        
        Args:
            max_chunk_size: 最大块大小（字符数，默认3000≈1024 token，符合文章建议的甜点区512-1024 token）
            overlap_ratio: 重叠比例（0.0-1.0，推荐0.2-0.3）
            min_chunk_size: 最小块大小（字符数）
            chunk_strategy: 分块策略（"recursive", "semantic", "fixed", "structure", "lazy"）
            enable_lazy_chunking: 是否启用Lazy Chunking（能不切就不切，最大化上下文利用）
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_size = int(max_chunk_size * overlap_ratio)
        self.min_chunk_size = min_chunk_size
        self.chunk_strategy = chunk_strategy
        self.enable_lazy_chunking = enable_lazy_chunking
        self.logger = logger
    
    def chunk_document(
        self, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None,
        query: Optional[str] = None,  # 🚀 新增：查询文本（用于动态调整）
        query_type: Optional[str] = None,  # 🚀 新增：查询类型
        query_complexity: Optional[str] = None,  # 🚀 新增：查询复杂度
        parent_id: Optional[str] = None  # 🚀 新增：父文档ID
    ) -> List[Dict[str, Any]]:
        """
        对文档进行分块
        
        Args:
            text: 原始文档文本
            metadata: 文档的元数据（将被添加到每个块的元数据中）
            query: 查询文本（用于动态调整chunk大小）
            query_type: 查询类型（用于动态调整）
            query_complexity: 查询复杂度（用于动态调整）
            
        Returns:
            块列表，每个块包含：
            - content: 块内容
            - chunk_index: 块索引（从0开始）
            - total_chunks: 总块数
            - parent_metadata: 父文档的元数据
            - chunk_metadata: 块的额外元数据
        """
        try:
            if not text or not isinstance(text, str) or len(text.strip()) == 0:
                self.logger.warning("输入文本为空，无法分块")
                return []
            
            # 🚀 优化：动态调整chunk大小（基于ML/RL）
            dynamic_config = None
            if query:
                try:
                    from .dynamic_chunk_manager import get_dynamic_chunk_manager
                    chunk_manager = get_dynamic_chunk_manager()
                    dynamic_config = chunk_manager.get_optimal_chunk_config(
                        query=query,
                        query_type=query_type,
                        query_complexity=query_complexity,
                        document_type=metadata.get('type') if metadata else None,
                        document_length=len(text)
                    )
                    
                    # 应用动态配置
                    original_chunk_size = self.max_chunk_size
                    original_overlap_ratio = self.overlap_ratio
                    self.max_chunk_size = dynamic_config.max_chunk_size
                    self.overlap_size = int(self.max_chunk_size * dynamic_config.overlap_ratio)
                    self.overlap_ratio = dynamic_config.overlap_ratio
                    self.chunk_strategy = dynamic_config.chunk_strategy
                    self.enable_lazy_chunking = dynamic_config.enable_lazy_chunking
                    
                    self.logger.debug(f"🚀 动态调整chunk配置: 大小={self.max_chunk_size} (原={original_chunk_size}), 重叠={self.overlap_ratio:.2f} (原={original_overlap_ratio:.2f})")
                except Exception as e:
                    self.logger.debug(f"动态调整chunk大小失败: {e}，使用默认配置")
            
            # 如果文本小于最大块大小，不需要分块
            if len(text) <= self.max_chunk_size:
                return [{
                    'content': text,
                    'chunk_index': 0,
                    'total_chunks': 1,
                    'parent_metadata': {**(metadata or {}), 'parent_id': parent_id} if parent_id else (metadata or {}),
                    'chunk_metadata': {}
                }]
            
            # 🚀 添加进度日志
            self.logger.debug(f"开始分块处理，文本长度: {len(text)}字符，策略: {self.chunk_strategy}")
            
            # 根据策略选择分块方法
            chunks = []
            try:
                if self.chunk_strategy == "lazy" or (self.enable_lazy_chunking and self.chunk_strategy == "recursive"):
                    # 🚀 新增：Lazy Chunking策略（能不切就不切）
                    chunks = self._lazy_chunk(text)
                elif self.chunk_strategy == "recursive":
                    chunks = self._recursive_chunk(text)
                elif self.chunk_strategy == "semantic":
                    chunks = self._semantic_chunk(text)
                elif self.chunk_strategy == "fixed":
                    chunks = self._fixed_chunk(text)
                elif self.chunk_strategy == "structure":
                    chunks = self._structure_chunk(text)
                else:
                    self.logger.warning(f"未知的分块策略: {self.chunk_strategy}，使用递归分块")
                    chunks = self._recursive_chunk(text)
            except Exception as e:
                self.logger.error(f"分块策略执行失败: {e}")
                import traceback
                self.logger.debug(f"分块策略错误详情:\n{traceback.format_exc()}")
                # 降级到固定长度分块
                try:
                    self.logger.info("尝试使用固定长度分块作为降级方案...")
                    chunks = self._fixed_chunk(text)
                except Exception as e2:
                    self.logger.error(f"固定长度分块也失败: {e2}")
                    raise  # 重新抛出异常
            
            # 🚀 添加进度日志
            if len(chunks) > 100:
                self.logger.debug(f"生成了 {len(chunks)} 个块，开始构建结果...")
            
            # 构建结果
            result = []
            for idx, chunk_content in enumerate(chunks):
                # 🚀 添加进度日志（每100个块输出一次）
                if idx > 0 and idx % 100 == 0:
                    self.logger.debug(f"构建块结果进度: {idx}/{len(chunks)}")
                
                # 添加重叠（除了第一块和最后一块）
                if idx > 0 and idx < len(chunks):
                    # 当前块的开头添加前一块的末尾
                    prev_chunk_end = chunks[idx - 1] if idx > 0 else ""
                    if len(prev_chunk_end) > self.overlap_size:
                        overlap_text = prev_chunk_end[-self.overlap_size:]
                        chunk_content = overlap_text + chunk_content
                elif idx < len(chunks) - 1:
                    # 当前块的末尾添加下一块的开头
                    next_chunk_start = chunks[idx + 1][:self.overlap_size] if idx + 1 < len(chunks) else ""
                    chunk_content = chunk_content + next_chunk_start
                
                # 🚀 优化：增强元信息（添加章节标题、层级路径等）
                chunk_metadata = {
                    'chunk_length': len(chunk_content),
                    'is_first': idx == 0,
                    'is_last': idx == len(chunks) - 1
                }
                
                # 提取章节标题和层级路径
                section_info = self._extract_section_info(chunk_content, metadata)
                chunk_metadata.update(section_info)
                
                # 在chunk内容前添加元信息提示（如果存在）
                content_with_metadata = chunk_content
                if section_info.get('section_title') or section_info.get('hierarchy_path'):
                    metadata_prefix = []
                    if section_info.get('hierarchy_path'):
                        metadata_prefix.append(f"[{section_info['hierarchy_path']}]")
                    if section_info.get('section_title'):
                        metadata_prefix.append(f"{section_info['section_title']}")
                    if metadata_prefix:
                        content_with_metadata = " ".join(metadata_prefix) + "\n\n" + chunk_content
                
                result.append({
                    'content': content_with_metadata,  # 使用带元信息的内容
                    'chunk_index': idx,
                    'total_chunks': len(chunks),
                    'parent_metadata': {**(metadata or {}), 'parent_id': parent_id} if parent_id else (metadata or {}),
                    'chunk_metadata': chunk_metadata
                })
            
            # 🚀 添加更详细的日志
            if len(chunks) > 0:
                avg_chunk_size = sum(len(chunk) for chunk in chunks) // len(chunks)
                self.logger.info(f"文档分块完成: {len(text)}字符 → {len(chunks)}块（策略: {self.chunk_strategy}，平均块大小: {avg_chunk_size}字符）")
            else:
                self.logger.warning(f"文档分块后没有生成任何块: {len(text)}字符")
            
            return result
        
        except Exception as e:
            self.logger.error(f"文档分块过程发生异常: {e}")
            import traceback
            self.logger.error(f"分块异常详情:\n{traceback.format_exc()}")
            raise  # 重新抛出异常，让调用者处理
    
    def _recursive_chunk(self, text: str) -> List[str]:
        """
        递归分块策略（推荐）
        
        策略：
        1. 优先按段落分隔符（\n\n）切分
        2. 如果段落过长，按句子切分
        3. 如果句子仍过长，按固定长度切分
        """
        chunks = []
        
        # 🚀 优化：对于超长文本（>50000字符），直接使用固定长度分块，避免正则表达式性能问题
        if len(text) > 50000:
            self.logger.debug(f"文本过长（{len(text)}字符），使用固定长度分块以提升性能")
            return self._fixed_chunk(text)
        
        # 步骤1: 按段落分隔符切分
        try:
            paragraphs = re.split(r'\n\s*\n', text)
        except Exception as e:
            self.logger.warning(f"正则表达式切分失败: {e}，使用固定长度分块")
            return self._fixed_chunk(text)
        
        current_chunk = ""
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 如果当前块加上新段落不超过限制
            if len(current_chunk) + len(paragraph) + 2 <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果段落本身超过限制，需要进一步切分
                if len(paragraph) > self.max_chunk_size:
                    # 按句子切分
                    sub_chunks = self._split_by_sentences(paragraph)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = paragraph
        
        # 添加最后一块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """按句子切分文本"""
        # 🚀 优化：对于超长文本，直接使用固定长度分块
        if len(text) > 50000:
            self.logger.debug(f"句子切分文本过长（{len(text)}字符），使用固定长度分块")
            return self._fixed_chunk(text)
        
        # 简单的句子切分（按句号、问号、感叹号）
        try:
            sentences = re.split(r'([.!?]\s+)', text)
        except Exception as e:
            self.logger.warning(f"句子切分失败: {e}，使用固定长度分块")
            return self._fixed_chunk(text)
        
        # 合并分隔符和句子
        merged_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                merged_sentences.append(sentences[i] + sentences[i + 1])
            else:
                merged_sentences.append(sentences[i])
        
        chunks = []
        current_chunk = ""
        
        for sentence in merged_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) + 1 <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
                
                # 如果单个句子超过限制，按固定长度切分
                if len(sentence) > self.max_chunk_size:
                    fixed_chunks = self._fixed_chunk(sentence)
                    chunks.extend(fixed_chunks)
                    current_chunk = ""
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _semantic_chunk(self, text: str) -> List[str]:
        """
        语义分块策略（需要embedding模型，简化版本）
        
        简化实现：基于段落语义相似度（近似）
        完整实现需要计算句子间的embedding相似度
        """
        # 简化版本：使用递归分块作为基础
        # 完整的语义分块需要embedding模型来计算相似度
        self.logger.info("使用简化语义分块（基于递归分块），完整语义分块需要embedding模型")
        return self._recursive_chunk(text)
    
    def _fixed_chunk(self, text: str) -> List[str]:
        """
        固定长度分块策略
        
        简单但可能割裂语义
        """
        chunks = []
        start = 0
        max_iterations = (len(text) // (self.max_chunk_size - self.overlap_size)) + 10  # 安全上限，防止死循环
        iteration = 0
        
        while start < len(text) and iteration < max_iterations:
            iteration += 1
            end = min(start + self.max_chunk_size, len(text))
            chunk = text[start:end]
            
            if not chunk:  # 空块，退出循环
                break
            
            chunks.append(chunk)
            
            # 🚀 修复：确保start总是向前推进，防止死循环
            next_start = end - self.overlap_size
            if next_start <= start:  # 如果start没有推进，强制推进
                next_start = start + 1
            start = next_start
            
            # 如果已经到达末尾，退出
            if end >= len(text):
                break
        
        # 🚀 安全检查：如果迭代次数过多，记录警告
        if iteration >= max_iterations:
            self.logger.warning(f"⚠️ 固定长度分块达到最大迭代次数（{max_iterations}），可能存在死循环风险")
        
        return chunks
    
    def _lazy_chunk(self, text: str) -> List[str]:
        """
        🚀 新增：Lazy Chunking策略（能不切就不切，最大化上下文利用）
        
        策略：
        1. 在满足最大长度限制前，尽量把内容塞进同一个chunk
        2. 按段落分割，但如果段落加上当前chunk不超过上限，就合并
        3. 避免过早切分，减少chunk数量，提高信息密度
        
        参考文章：RAG观止系列（四）- Lazy Chunking策略
        """
        chunks = []
        current_chunk = ""
        
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 🚀 Lazy策略：如果加上当前段落不超过上限，就合并
            if len(current_chunk) + len(para) + 2 <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # 超过上限，保存当前chunk，开始新chunk
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果段落本身超过限制，需要进一步切分
                if len(para) > self.max_chunk_size:
                    # 对于超长段落，使用句子切分
                    sub_chunks = self._split_by_sentences(para)
                    chunks.extend(sub_chunks[:-1])  # 除了最后一个
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
                else:
                    current_chunk = para
        
        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks if chunks else [text]
    
    def _extract_section_info(self, chunk_content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        🚀 新增：提取章节信息（标题、层级路径等）
        
        用于增强chunk的元信息，帮助LLM理解chunk在文档中的位置
        """
        section_info = {
            'section_title': None,
            'hierarchy_path': None,
            'document_source': metadata.get('source', 'unknown') if metadata else 'unknown'
        }
        
        try:
            # 提取Markdown标题（## 标题 或 ### 标题）
            markdown_title_pattern = r'^(#{1,6})\s+(.+?)$'
            markdown_matches = re.findall(markdown_title_pattern, chunk_content[:500], re.MULTILINE)  # 只检查前500字符
            
            if markdown_matches:
                # 获取最后一个标题（最接近chunk内容的标题）
                last_match = markdown_matches[-1]
                level = len(last_match[0])  # #的数量表示层级
                title = last_match[1].strip()
                
                section_info['section_title'] = title
                
                # 构建层级路径（如果有多个标题）
                if len(markdown_matches) > 1:
                    hierarchy = []
                    for match in markdown_matches:
                        hierarchy.append(match[1].strip())
                    section_info['hierarchy_path'] = " > ".join(hierarchy)
                else:
                    section_info['hierarchy_path'] = f"第{level}级: {title}"
            
            # 提取HTML标题（<h1>标题</h1>等）
            html_title_pattern = r'<h([1-6])>(.+?)</h[1-6]>'
            html_matches = re.findall(html_title_pattern, chunk_content[:500], re.IGNORECASE)
            
            if html_matches and not section_info['section_title']:
                last_match = html_matches[-1]
                level = int(last_match[0])
                title = last_match[1].strip()
                
                section_info['section_title'] = title
                section_info['hierarchy_path'] = f"第{level}级: {title}"
            
            # 如果没有找到标题，尝试从metadata中获取
            if not section_info['section_title'] and metadata:
                if 'title' in metadata:
                    section_info['section_title'] = metadata['title']
                elif 'section' in metadata:
                    section_info['section_title'] = metadata['section']
        
        except Exception as e:
            self.logger.debug(f"提取章节信息失败: {e}")
        
        return section_info
    
    def _structure_chunk(self, text: str) -> List[str]:
        """
        基于文档结构的分块策略
        
        利用标题、子标题等结构信息
        """
        chunks = []
        
        # 查找标题（Markdown风格或HTML风格）
        # 模式：## 标题 或 <h2>标题</h2>
        title_pattern = r'(?:^|\n)(?:#{1,6}\s+.*?|.*?<h[1-6]>.*?</h[1-6]>.*?)(?=\n|$)'
        title_matches = list(re.finditer(title_pattern, text, re.MULTILINE | re.IGNORECASE))
        
        if not title_matches or len(title_matches) < 2:
            # 如果没有明显的结构，使用递归分块
            self.logger.info("文档结构不明显，使用递归分块")
            return self._recursive_chunk(text)
        
        # 按标题切分
        current_chunk = ""
        last_end = 0
        
        for i, match in enumerate(title_matches):
            section_start = match.start()
            section_text = text[last_end:section_start].strip()
            
            # 如果有内容，添加到当前块
            if section_text:
                if len(current_chunk) + len(section_text) <= self.max_chunk_size:
                    if current_chunk:
                        current_chunk += "\n\n" + section_text
                    else:
                        current_chunk = section_text
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = section_text
                    
                    # 如果单个段落仍然过长，递归切分
                    if len(section_text) > self.max_chunk_size:
                        sub_chunks = self._recursive_chunk(section_text)
                        chunks.extend(sub_chunks[:-1])  # 除了最后一个
                        current_chunk = sub_chunks[-1] if sub_chunks else ""
            
            # 更新最后位置
            last_end = section_start
        
        # 处理最后一部分
        if last_end < len(text):
            remaining = text[last_end:].strip()
            if remaining:
                if len(current_chunk) + len(remaining) <= self.max_chunk_size:
                    current_chunk += "\n\n" + remaining
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    chunks.append(remaining)
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks if chunks else [text]
    
    def should_chunk(self, text: str, threshold: Optional[int] = None) -> bool:
        """
        判断是否应该对文档进行分块
        
        Args:
            text: 文档文本
            threshold: 阈值（如果None，使用max_chunk_size）
            
        Returns:
            是否应该分块
        """
        if threshold is None:
            threshold = self.max_chunk_size
        
        return len(text) > threshold
    
    def get_chunking_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取分块统计信息
        
        Args:
            chunks: 分块结果列表
            
        Returns:
            统计信息字典
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'avg_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0,
                'total_size': 0
            }
        
        chunk_sizes = [len(chunk['content']) for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
            'min_chunk_size': min(chunk_sizes) if chunk_sizes else 0,
            'max_chunk_size': max(chunk_sizes) if chunk_sizes else 0,
            'total_size': sum(chunk_sizes)
        }

