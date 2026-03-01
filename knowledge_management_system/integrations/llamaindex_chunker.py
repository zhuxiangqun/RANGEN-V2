#!/usr/bin/env python3
"""
LlamaIndex 文档分块器
使用 LlamaIndex 的智能文档分块功能
"""

from typing import List, Dict, Any, Optional
from ..utils.logger import get_logger

logger = get_logger()

# 尝试导入 LlamaIndex（可选依赖）
try:
    from llama_index.core.node_parser import (
        SemanticSplitterNodeParser,
        SentenceSplitter,
        SimpleNodeParser
    )
    from llama_index.core import Document
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    logger.warning("LlamaIndex 未安装，智能分块功能将不可用。如需使用，请运行: pip install llamaindex")


class LlamaIndexChunker:
    """使用 LlamaIndex 的智能文档分块"""
    
    def __init__(self, chunk_strategy: str = "sentence", embedding_model=None):
        """
        初始化分块器
        
        Args:
            chunk_strategy: 分块策略
                - "semantic": 基于语义的分块（推荐，需要embedding模型）
                - "sentence": 基于句子的分块（默认，不需要额外模型）
                - "simple": 简单分块
            embedding_model: Embedding模型（仅semantic策略需要）
        """
        self.enabled = LLAMAINDEX_AVAILABLE
        self.chunk_strategy = chunk_strategy
        self.embedding_model = embedding_model
        self.logger = logger
        
        if self.enabled:
            self._init_parsers()
        else:
            self.parser = None
    
    def _init_parsers(self):
        """初始化解析器"""
        try:
            if self.chunk_strategy == "semantic":
                # 需要 embedding 模型
                if self.embedding_model is None:
                    # 尝试使用默认的embedding模型
                    try:
                        # 使用Jina embedding（如果可用）
                        from ..utils.jina_service import get_jina_service
                        jina_service = get_jina_service()
                        if jina_service:
                            # 创建一个简单的embedding适配器
                            # 注意：这里需要适配LlamaIndex的embedding接口
                            self.logger.warning("语义分块需要embedding模型，降级到句子分块")
                            self.chunk_strategy = "sentence"
                            self.parser = SentenceSplitter(
                                chunk_size=1024,
                                chunk_overlap=200
                            )
                        else:
                            raise ValueError("未找到embedding模型")
                    except Exception as e:
                        self.logger.warning(f"无法初始化语义分块，降级到句子分块: {e}")
                        self.chunk_strategy = "sentence"
                        self.parser = SentenceSplitter(
                            chunk_size=1024,
                            chunk_overlap=200
                        )
                else:
                    self.parser = SemanticSplitterNodeParser(
                        buffer_size=1,
                        breakpoint_percentile_threshold=95,
                        embed_model=self.embedding_model
                    )
            elif self.chunk_strategy == "sentence":
                self.parser = SentenceSplitter(
                    chunk_size=1024,
                    chunk_overlap=200
                )
            else:
                self.parser = SimpleNodeParser()
            
            self.logger.info(f"✅ LlamaIndex 文档分块器初始化成功（策略: {self.chunk_strategy}）")
        except Exception as e:
            self.logger.error(f"LlamaIndex 文档分块器初始化失败: {e}")
            self.enabled = False
            self.parser = None
    
    def chunk_document(
        self, 
        text: str, 
        metadata: Dict = None
    ) -> List[Dict[str, Any]]:
        """
        对文档进行智能分块
        
        Args:
            text: 文档文本
            metadata: 文档元数据
        
        Returns:
            分块结果列表，每个块包含 content 和 metadata
        """
        if not self.enabled or self.parser is None:
            self.logger.warning("LlamaIndex 分块器未启用，返回原始文本作为单个块")
            return [{
                'content': text,
                'metadata': metadata or {},
                'node_id': 'chunk_0'
            }]
        
        try:
            doc = Document(text=text, metadata=metadata or {})
            nodes = self.parser.get_nodes_from_documents([doc])
            
            chunks = []
            for idx, node in enumerate(nodes):
                chunks.append({
                    'content': node.text,
                    'metadata': {**(node.metadata or {}), **(metadata or {})},
                    'node_id': node.node_id or f'chunk_{idx}'
                })
            
            self.logger.debug(f"✅ 文档分块完成: {len(chunks)} 个块")
            return chunks
            
        except Exception as e:
            self.logger.error(f"文档分块失败: {e}")
            # 降级：返回原始文本作为单个块
            return [{
                'content': text,
                'metadata': metadata or {},
                'node_id': 'chunk_0'
            }]

