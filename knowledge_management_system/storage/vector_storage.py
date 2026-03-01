#!/usr/bin/env python3
"""
向量存储模块
管理向量索引的存储
"""

from pathlib import Path
from typing import Optional
from ..core.vector_index_builder import VectorIndexBuilder
from ..utils.logger import get_logger

logger = get_logger()


class VectorStorage:
    """向量存储管理器"""
    
    def __init__(self, index_path: str = "data/knowledge_management/vector_index.bin"):
        self.logger = logger
        self.index_builder = VectorIndexBuilder(index_path)
    
    def is_ready(self) -> bool:
        """检查存储是否就绪"""
        return self.index_builder.ensure_index_ready()
    
    def get_index_builder(self) -> VectorIndexBuilder:
        """获取索引构建器"""
        return self.index_builder

