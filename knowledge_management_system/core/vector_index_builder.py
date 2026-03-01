#!/usr/bin/env python3
"""
向量索引构建器
负责构建和维护FAISS向量索引
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

from ..utils.logger import get_logger
from ..modalities.text_processor import TextProcessor
from ..modalities.image_processor import ImageProcessor
from ..modalities.audio_processor import AudioProcessor
from ..modalities.video_processor import VideoProcessor

logger = get_logger()

# 全局缓存FAISS模块（避免重复导入）
_faiss_module = None
_faiss_available = None


def _check_faiss_available() -> bool:
    """运行时动态检查FAISS是否可用"""
    global _faiss_module, _faiss_available
    
    if _faiss_available is not None:
        return _faiss_available
    
    try:
        import faiss
        _faiss_module = faiss
        _faiss_available = True
        return True
    except ImportError as e:
        # 记录详细的导入错误信息
        logger.warning(f"⚠️ FAISS导入失败: {e} (类型: {type(e).__name__})")
        _faiss_available = False
        return False
    except Exception as e:
        # 捕获其他可能的异常（如系统库缺失）
        logger.warning(f"⚠️ FAISS导入时发生意外错误: {e} (类型: {type(e).__name__})")
        _faiss_available = False
        return False


def _get_faiss():
    """获取FAISS模块（如果可用）"""
    if not _check_faiss_available():
        raise ImportError("FAISS未安装")
    return _faiss_module


class VectorIndexBuilder:
    """向量索引构建器"""
    
    def __init__(
        self, 
        index_path: str = "data/knowledge_management/vector_index.bin",
        dimension: int = 768
    ):
        self.logger = logger
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化模态处理器
        self.processors = {
            'text': TextProcessor(),
            'image': ImageProcessor(),
            'audio': AudioProcessor(),
            'video': VideoProcessor()
        }
        
        # 🆕 从处理器获取实际维度（而不是使用固定值）
        text_processor = self.processors.get('text')
        if text_processor:
            actual_dimension = text_processor.get_dimension()
            if actual_dimension != dimension:
                self.logger.info(f"⚠️ 检测到维度不匹配: 配置维度={dimension}, 实际维度={actual_dimension}，使用实际维度")
                dimension = actual_dimension
        
        self.dimension = dimension
        
        # FAISS索引
        self.index = None
        self.entry_mapping: Dict[int, str] = {}  # FAISS内部ID -> 知识ID的映射
        self.reverse_mapping: Dict[str, int] = {}  # 知识ID -> FAISS内部ID的映射
        self.entry_count = 0
        
        if not _check_faiss_available():
            self.logger.warning("⚠️ FAISS未安装，向量索引功能不可用")
    
    def _create_index(self):
        """创建FAISS索引"""
        if not _check_faiss_available():
            # 再次尝试导入以获取详细错误信息
            try:
                import faiss
                # 如果能导入，说明之前的检查有误，更新状态
                global _faiss_module, _faiss_available
                _faiss_module = faiss
                _faiss_available = True
                self.logger.info("✅ FAISS模块已成功加载（之前检查失败可能是缓存问题）")
            except Exception as import_error:
                self.logger.error(f"FAISS未安装，无法创建索引。导入错误: {import_error} (类型: {type(import_error).__name__})")
                return False
        
        try:
            faiss_module = _get_faiss()
            # 使用内积索引（适合归一化向量）
            self.index = faiss_module.IndexFlatIP(self.dimension)  # type: ignore
            self.logger.info(f"创建FAISS索引: dimension={self.dimension}, type=IndexFlatIP")
            return True
        except Exception as e:
            self.logger.error(f"创建FAISS索引失败: {e} (类型: {type(e).__name__})")
            import traceback
            self.logger.debug(f"完整错误堆栈:\n{traceback.format_exc()}")
            return False
    
    def _load_index(self) -> bool:
        """加载现有索引"""
        if not _check_faiss_available():
            return False
        
        try:
            faiss_module = _get_faiss()
            if self.index_path.exists():
                self.index = faiss_module.read_index(str(self.index_path))  # type: ignore
                
                # 加载映射文件
                mapping_path = self.index_path.with_suffix('.mapping.json')
                if mapping_path.exists():
                    import json
                    with open(mapping_path, 'r', encoding='utf-8') as f:
                        self.reverse_mapping = json.load(f)
                    # 构建反向映射
                    self.entry_mapping = {v: k for k, v in self.reverse_mapping.items()}
                
                self.entry_count = self.index.ntotal if hasattr(self.index, 'ntotal') else 0
                self.logger.info(f"加载FAISS索引: {self.entry_count} 条向量")
                return True
            return False
        except Exception as e:
            self.logger.error(f"加载FAISS索引失败: {e}")
            return False
    
    def _save_index(self):
        """保存索引"""
        if not _check_faiss_available() or self.index is None:
            return False
        
        try:
            faiss_module = _get_faiss()
            faiss_module.write_index(self.index, str(self.index_path))  # type: ignore
            
            # 保存映射文件
            mapping_path = self.index_path.with_suffix('.mapping.json')
            import json
            with open(mapping_path, 'w', encoding='utf-8') as f:
                json.dump(self.reverse_mapping, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"保存FAISS索引: {self.entry_count} 条向量")
            return True
        except Exception as e:
            self.logger.error(f"保存FAISS索引失败: {e}")
            return False
    
    def ensure_index_ready(self) -> bool:
        """确保索引就绪"""
        if self.index is not None:
            return True
        
        # 尝试加载
        if self._load_index():
            return True
        
        # 创建新索引
        return self._create_index()
    
    def add_vector(
        self, 
        vector: np.ndarray, 
        knowledge_id: str,
        modality: str = "text"
    ) -> bool:
        """
        添加向量到索引
        
        Args:
            vector: 向量
            knowledge_id: 知识ID
            modality: 模态类型
        
        Returns:
            是否成功
        """
        if not self.ensure_index_ready():
            return False
        
        try:
            # 验证向量维度
            if vector.shape[0] != self.dimension:
                self.logger.error(f"向量维度不匹配: 期望{self.dimension}, 实际{vector.shape[0]}")
                return False
            
            # 归一化向量（内积索引需要归一化）
            norm = np.linalg.norm(vector)
            if norm < 1e-6:
                self.logger.warning(f"向量模长接近0，无法归一化: knowledge_id={knowledge_id}")
                return False
                
            vector = vector / norm
            vector = vector.astype(np.float32).reshape(1, -1)
            
            # 添加到索引
            self.index.add(vector)  # type: ignore
            
            # 更新映射
            faiss_id = self.entry_count
            self.entry_mapping[faiss_id] = knowledge_id
            self.reverse_mapping[knowledge_id] = faiss_id
            self.entry_count += 1
            
            self.logger.debug(f"添加向量到索引: knowledge_id={knowledge_id}, faiss_id={faiss_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加向量失败: {e}")
            return False
    
    def search(
        self, 
        query_vector: np.ndarray, 
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        搜索向量
        
        Args:
            query_vector: 查询向量
            top_k: 返回数量
            similarity_threshold: 相似度阈值
        
        Returns:
            搜索结果列表
        """
        if not self.ensure_index_ready() or self.entry_count == 0:
            return []
        
        try:
            # 归一化查询向量
            query_vector = query_vector / np.linalg.norm(query_vector)
            query_vector = query_vector.astype(np.float32).reshape(1, -1)
            
            # 搜索
            # 🚀 修复：如果阈值是0.0，获取更多候选结果（top_k * 2），以便后续筛选
            search_k = min(top_k * 2 if similarity_threshold == 0.0 else top_k, self.entry_count)
            similarities, indices = self.index.search(query_vector, search_k)  # type: ignore
            
            results = []
            for similarity, idx in zip(similarities[0], indices[0]):
                if idx < 0:  # FAISS返回-1表示无结果
                    continue
                
                # 🚀 修复：如果阈值是0.0，不过滤，返回所有结果（由上层筛选）
                if similarity_threshold > 0.0 and similarity < similarity_threshold:
                    continue
                
                knowledge_id = self.entry_mapping.get(int(idx))
                if knowledge_id:
                    results.append({
                        'knowledge_id': knowledge_id,
                        'similarity_score': float(similarity),
                        'rank': len(results) + 1
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"向量搜索失败: {e}")
            return []
    
    def rebuild_index(self, knowledge_entries: List[Dict[str, Any]]) -> bool:
        """
        重建索引
        
        Args:
            knowledge_entries: 知识条目列表
        
        Returns:
            是否成功
        """
        self.logger.info(f"开始重建索引: {len(knowledge_entries)} 条知识")
        
        # 创建新索引
        if not self._create_index():
            return False
        
        # 清空映射
        self.entry_mapping = {}
        self.reverse_mapping = {}
        self.entry_count = 0
        
        # 批量处理
        success_count = 0
        for entry in knowledge_entries:
            knowledge_id = entry.get('id')
            content = entry.get('content')
            modality = entry.get('modality', 'text')
            
            if not knowledge_id or not content:
                continue
            
            # 获取对应的处理器
            processor = self.processors.get(modality)
            if not processor or not processor.enabled:
                continue
            
            # 向量化
            vector = processor.encode(content)
            if vector is None:
                continue
            
            # 添加到索引
            if self.add_vector(vector, knowledge_id, modality):
                success_count += 1
        
        # 保存索引
        self._save_index()
        
        self.logger.info(f"索引重建完成: {success_count}/{len(knowledge_entries)} 条成功")
        return success_count > 0

