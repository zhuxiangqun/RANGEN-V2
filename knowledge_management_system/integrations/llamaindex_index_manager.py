#!/usr/bin/env python3
"""
LlamaIndex 索引管理器
管理多种类型的 LlamaIndex 索引（树索引、关键词表索引等）
"""

from typing import List, Dict, Any, Optional
from ..utils.logger import get_logger

logger = get_logger()

# 尝试导入 LlamaIndex（可选依赖）
try:
    from llama_index.core import Document, VectorStoreIndex
    from llama_index.core.indices.tree import TreeIndex
    from llama_index.core.indices.keyword_table import KeywordTableIndex
    from llama_index.core.indices.list import ListIndex
    from llama_index.core.query_engine import RouterQueryEngine
    from llama_index.core.selectors import LLMSingleSelector
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    logger.warning("LlamaIndex 未安装，索引管理功能将不可用。如需使用，请运行: pip install llamaindex")


class LlamaIndexIndexManager:
    """管理多种类型的 LlamaIndex 索引"""
    
    def __init__(self):
        """初始化索引管理器"""
        self.enabled = LLAMAINDEX_AVAILABLE
        self.logger = logger
        
        # 存储各种类型的索引
        self.tree_index: Optional[TreeIndex] = None
        self.keyword_index: Optional[KeywordTableIndex] = None
        self.list_index: Optional[ListIndex] = None
        self.vector_index: Optional[VectorStoreIndex] = None
        
        # 路由查询引擎
        self.router_query_engine: Optional[RouterQueryEngine] = None
        
        if self.enabled:
            self.logger.info("✅ LlamaIndex 索引管理器初始化成功")
        else:
            self.logger.warning("LlamaIndex 未安装，索引管理器将使用降级模式")
    
    def build_tree_index(self, documents: List[Document]) -> Optional[TreeIndex]:
        """
        构建树索引
        
        树索引适合：
        - 层次化查询
        - 摘要查询
        - 需要理解文档结构的查询
        
        Args:
            documents: 文档列表
        
        Returns:
            树索引实例
        """
        if not self.enabled:
            self.logger.warning("LlamaIndex 未安装，无法构建树索引")
            return None
        
        try:
            self.tree_index = TreeIndex.from_documents(documents)
            self.logger.info(f"✅ 成功构建树索引，包含 {len(documents)} 个文档")
            return self.tree_index
        except Exception as e:
            self.logger.error(f"构建树索引失败: {e}")
            return None
    
    def build_keyword_index(self, documents: List[Document]) -> Optional[KeywordTableIndex]:
        """
        构建关键词表索引
        
        关键词表索引适合：
        - 精确关键词匹配
        - 基于关键词的快速检索
        - 不需要语义理解的查询
        
        Args:
            documents: 文档列表
        
        Returns:
            关键词表索引实例
        """
        if not self.enabled:
            self.logger.warning("LlamaIndex 未安装，无法构建关键词表索引")
            return None
        
        try:
            self.keyword_index = KeywordTableIndex.from_documents(documents)
            self.logger.info(f"✅ 成功构建关键词表索引，包含 {len(documents)} 个文档")
            return self.keyword_index
        except Exception as e:
            self.logger.error(f"构建关键词表索引失败: {e}")
            return None
    
    def build_list_index(self, documents: List[Document]) -> Optional[ListIndex]:
        """
        构建列表索引
        
        列表索引适合：
        - 顺序访问
        - 需要保持文档顺序的查询
        - 简单列表查询
        
        Args:
            documents: 文档列表
        
        Returns:
            列表索引实例
        """
        if not self.enabled:
            self.logger.warning("LlamaIndex 未安装，无法构建列表索引")
            return None
        
        try:
            self.list_index = ListIndex.from_documents(documents)
            self.logger.info(f"✅ 成功构建列表索引，包含 {len(documents)} 个文档")
            return self.list_index
        except Exception as e:
            self.logger.error(f"构建列表索引失败: {e}")
            return None
    
    def build_vector_index(self, documents: List[Document]) -> Optional[VectorStoreIndex]:
        """
        构建向量索引
        
        向量索引适合：
        - 语义相似度查询
        - 基于embedding的检索
        
        Args:
            documents: 文档列表
        
        Returns:
            向量索引实例
        """
        if not self.enabled:
            self.logger.warning("LlamaIndex 未安装，无法构建向量索引")
            return None
        
        try:
            self.vector_index = VectorStoreIndex.from_documents(documents)
            self.logger.info(f"✅ 成功构建向量索引，包含 {len(documents)} 个文档")
            return self.vector_index
        except Exception as e:
            self.logger.error(f"构建向量索引失败: {e}")
            return None
    
    def query_with_router(
        self, 
        query: str,
        index_types: Optional[List[str]] = None
    ) -> Optional[Any]:
        """
        使用路由查询引擎，自动选择最佳索引
        
        Args:
            query: 查询文本
            index_types: 可用的索引类型列表（如果为None，使用所有已构建的索引）
        
        Returns:
            查询结果
        """
        if not self.enabled:
            self.logger.warning("LlamaIndex 未安装，无法使用路由查询")
            return None
        
        try:
            # 构建查询引擎列表
            query_engines = []
            
            if index_types is None:
                # 使用所有已构建的索引
                if self.tree_index:
                    query_engines.append(("tree", self.tree_index.as_query_engine()))
                if self.keyword_index:
                    query_engines.append(("keyword", self.keyword_index.as_query_engine()))
                if self.list_index:
                    query_engines.append(("list", self.list_index.as_query_engine()))
                if self.vector_index:
                    query_engines.append(("vector", self.vector_index.as_query_engine()))
            else:
                # 使用指定的索引类型
                if "tree" in index_types and self.tree_index:
                    query_engines.append(("tree", self.tree_index.as_query_engine()))
                if "keyword" in index_types and self.keyword_index:
                    query_engines.append(("keyword", self.keyword_index.as_query_engine()))
                if "list" in index_types and self.list_index:
                    query_engines.append(("list", self.list_index.as_query_engine()))
                if "vector" in index_types and self.vector_index:
                    query_engines.append(("vector", self.vector_index.as_query_engine()))
            
            if not query_engines:
                self.logger.warning("没有可用的索引，无法进行路由查询")
                return None
            
            # 创建路由查询引擎
            if len(query_engines) == 1:
                # 只有一个查询引擎，直接使用
                _, query_engine = query_engines[0]
                return query_engine.query(query)
            else:
                # 多个查询引擎，使用路由选择
                try:
                    from llama_index.core.query_engine import RouterQueryEngine
                    from llama_index.core.selectors import LLMSingleSelector
                    
                    self.router_query_engine = RouterQueryEngine.from_defaults(
                        query_engine_tools=[(name, engine) for name, engine in query_engines],
                        selector=LLMSingleSelector.from_defaults()
                    )
                    return self.router_query_engine.query(query)
                except Exception as e:
                    self.logger.warning(f"路由查询引擎创建失败，使用第一个查询引擎: {e}")
                    _, query_engine = query_engines[0]
                    return query_engine.query(query)
            
        except Exception as e:
            self.logger.error(f"路由查询失败: {e}")
            return None
    
    def get_available_index_types(self) -> List[str]:
        """
        获取已构建的索引类型列表
        
        Returns:
            索引类型列表
        """
        available = []
        if self.tree_index:
            available.append("tree")
        if self.keyword_index:
            available.append("keyword")
        if self.list_index:
            available.append("list")
        if self.vector_index:
            available.append("vector")
        return available

