#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量数据库管理器
支持FRAMES数据集的向量化存储和检索
"""

import os
import json
import numpy as np
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import hashlib
import pickle

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("faiss未安装，将使用简化的向量存储")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers未安装，将使用简化的文本向量化")


class VectorDatabaseManager:
    """向量数据库管理器"""
    
    def __init__(self, db_dir: str = "vector_db"):
        """初始化向量数据库管理器"""
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # 文件路径
        self.index_file = self.db_dir / "faiss_index.faiss"
        self.index_file_bin = self.db_dir / "faiss_index.bin"
        self.vectors_file = self.db_dir / "faiss_vectors.npy"
        self.metadata_file = self.db_dir / "metadata.json"
        
        # 向量化模型
        self.embedding_model = None
        self.vector_dim = 384  # 默认向量维度
        
        # 向量索引
        self.index = None
        self.metadata = []
        
        # 初始化
        self._initialize_embedding_model()
        self._load_existing_database()
    
    def _initialize_embedding_model(self):
        """初始化向量化模型（🚀 优化：统一使用Jina API）"""
        # 优先使用统一的Jina服务
        try:
            from src.utils.unified_jina_service import get_jina_service
            self._jina_service = get_jina_service()
            if self._jina_service and self._jina_service.api_key:
                # 通过一次测试调用确定向量维度
                test_embedding = self._jina_service.get_embedding("test")
                if test_embedding is not None:
                    self.vector_dim = int(test_embedding.shape[0])
                    self.logger.info(f"✅ 使用Jina Embedding服务，向量维度: {self.vector_dim}")
                    self.embedding_model = None  # 不再使用SentenceTransformer
                    return
        except Exception as e:
            self.logger.warning(f"⚠️ Jina服务初始化失败: {e}，将使用简化向量化")
        
        # Fallback: 简化向量化
        self._jina_service = None
        self.embedding_model = None
        self._initialize_simple_embedding()
    
    def _initialize_simple_embedding(self):
        """初始化简化的向量化模型"""
        self.logger.info("使用简化的文本向量化方法")
        self.vector_dim = 384
    
    def _text_to_vector(self, text: str) -> np.ndarray:
        """将文本转换为向量（🚀 优化：统一使用Jina API）"""
        # 优先使用统一的Jina服务
        if self._jina_service:
            try:
                embedding = self._jina_service.get_embedding(text)
                if embedding is not None:
                    vec = np.array(embedding, dtype=np.float32)
                    # 同步维度
                    if self.vector_dim is None:
                        self.vector_dim = int(vec.shape[0])
                    return vec
            except Exception as e:
                self.logger.warning(f"⚠️ Jina embedding失败，回退简化向量化: {e}")

        # Fallback: 简化向量化（不依赖外部模型）
        return self._simple_text_to_vector(text)

    
    def _simple_text_to_vector(self, text: str) -> np.ndarray:
        """简化的文本向量化方法"""
        if not text:
            if self.vector_dim is None:
                self.vector_dim = 128
            return np.zeros(self.vector_dim)
        
        # 计算基本特征
        words = text.split()
        word_count = len(words)
        char_count = len(text)
        avg_word_length = char_count / word_count if word_count > 0 else 0
        
        # 创建特征向量
        features = np.array([
            word_count / 100.0,
            char_count / 1000.0,
            avg_word_length / 20.0
        ])
        
        # 填充到目标维度
        if self.vector_dim is None:
            self.vector_dim = 128
        if len(features) < self.vector_dim:
            padding = np.zeros(self.vector_dim - len(features))
            features = np.concatenate([features, padding])
        elif len(features) > self.vector_dim:
            features = features[:self.vector_dim]
        
        return features.astype(np.float32)
    
    def _load_existing_database(self):
        """加载现有的向量数据库"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r", "utf-8') as f:
                    self.metadata = json.load(f)
                
                # 检查是否是FAISS格式的数据
                if isinstance(self.metadata, list) and len(self.metadata) > 0:
                    self.logger.info(f"加载FAISS向量数据库: {len(self.metadata)} 个条目")
                    
                    # 尝试加载FAISS索引
                    if self.index_file.exists() and FAISS_AVAILABLE:
                        import faiss  # type: ignore
                        self.index = faiss.read_index(str(self.index_file))
                        self.logger.info(f"加载FAISS索引: {self.index.ntotal} 个向量")
                    elif self.index_file_bin.exists() and FAISS_AVAILABLE:
                        # 尝试加载.bin格式的索引文件
                        import faiss  # type: ignore
                        self.index = faiss.read_index(str(self.index_file_bin))
                        self.logger.info(f"加载FAISS索引(.bin): {self.index.ntotal} 个向量")
                    else:
                        self.logger.info("FAISS索引文件不存在，将使用简化搜索")
                else:
                    self.logger.info("向量数据库为空")
                    self.metadata = []
            else:
                self.logger.info("未找到现有向量数据库，将创建新的")
                self.metadata = []
        except Exception as e:
            self.logger.warning(f"加载向量数据库失败: {e}")
            self.metadata = []
    
    def _save_database(self):
        """保存向量数据库"""
        try:
            if FAISS_AVAILABLE and self.index:
                import faiss  # type: ignore
                faiss.write_index(self.index, str(self.index_file))
                self.logger.info(f"保存向量索引: {self.index.ntotal} 个向量")
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            
            self.logger.info("向量数据库保存完成")
        except Exception as e:
            self.logger.error(f"保存向量数据库失败: {e}")
    
    def add_samples(self, samples: List[Dict[str, Any]]) -> bool:
        """添加样本到向量数据库"""
        try:
            if not samples:
                return True
            
            self.logger.info(f"开始向量化 {len(samples)} 个样本")
            
            vectors = []
            new_metadata = []
            
            for i, sample in enumerate(samples):
                # 组合查询和答案作为向量化文本
                query = sample.get("type", "")
                answer = sample.get("answer", "")
                reasoning = sample.get("reasoning", "")
                
                # 组合文本
                combined_text = f"{query} {answer} {reasoning}".strip()
                
                # 向量化
                vector = self._text_to_vector(combined_text)
                vectors.append(vector)
                
                # 保存元数据
                metadata_item = {
                    "index": len(self.metadata) + i,
                    "query": query,
                    "answer": answer,
                    "reasoning": reasoning,
                    "reasoning_types": sample.get("reasoning_types", []),
                    "query_id": sample.get("query_id", f"query_{i}")
                }
                new_metadata.append(metadata_item)
            
            # 转换为numpy数组
            vectors = np.array(vectors).astype(np.float32)
            
            if FAISS_AVAILABLE:
                import faiss  # type: ignore
                # 使用faiss索引
                if self.index is None:
                    # 创建新索引
                    vector_dim = self.vector_dim if self.vector_dim is not None else 128
                    self.index = faiss.IndexFlatIP(vector_dim)  # 内积相似度
                
                # 添加向量到索引
                if self.vector_dim is None:
                    self.vector_dim = int(vectors.shape[1]) if len(vectors.shape) > 1 else 128
                # FAISS add方法不需要额外参数，直接添加向量
                if self.index is not None:
                    self.index.add(vectors.astype(np.float32))  # type: ignore
            else:
                # 使用简化的向量存储
                if self.vectors_file.exists():
                    existing_vectors = np.load(self.vectors_file)
                    vectors = np.vstack([existing_vectors, vectors])
                np.save(self.vectors_file, vectors)
            
            # 更新元数据
            self.metadata.extend(new_metadata)
            
            self.logger.info(f"成功添加 {len(samples)} 个样本到向量数据库")
            return True
            
        except Exception as e:
            self.logger.error(f"添加样本到向量数据库失败: {e}")
            return False
    
    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似样本"""
        try:
            if not self.metadata:
                self.logger.warning("向量数据库为空")
                return []
            
            # 向量化查询
            query_vector = self._text_to_vector(query)
            query_vector = query_vector.reshape(1, -1).astype(np.float32)
            
            if FAISS_AVAILABLE and self.index is not None:
                import faiss  # type: ignore
                # 使用faiss搜索
                k = min(top_k, self.index.ntotal) if self.index.ntotal > 0 else top_k
                scores, indices = self.index.search(query_vector.reshape(1, -1), k)  # type: ignore
                
                results = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx < len(self.metadata):
                        result = self.metadata[idx].copy()
                        result["similarity_score"] = float(score)
                        results.append(result)
                
                return results
            else:
                # 使用简化的相似度计算
                results = []
                query_vector_flat = query_vector[0]
                
                for i, metadata_item in enumerate(self.metadata):
                    # 从元数据项中提取文本
                    text = metadata_item.get("type", '') or metadata_item.get("content", '') or metadata_item.get("description", '')
                    if not text:
                        continue
                    
                    # 计算相似度
                    sample_vector = self._text_to_vector(text)
                    similarity = np.dot(query_vector_flat, sample_vector) / (
                        np.linalg.norm(query_vector_flat) * np.linalg.norm(sample_vector)
                    )
                    
                    result = metadata_item.copy()
                    result["similarity_score"] = float(similarity)
                    results.append(result)
                
                # 按相似度排序
                results.sort(key=lambda x: x["similarity_score"], reverse=True)
                return results[:top_k]
        
        except Exception as e:
            self.logger.error(f"搜索相似样本失败: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        stats = {
            "total_metadata_items": len(self.metadata),
            "vector_dimension": self.vector_dim,
            "index_type": "faiss" if FAISS_AVAILABLE and self.index else "numpy",
            "embedding_model": "jina-api" if hasattr(self, '_jina_service') and self._jina_service else "simple",
            "database_size_mb": 0
        }
        
        try:
            if self.index_file.exists():
                stats["database_size_mb"] += self.index_file.stat().st_size / (1024 * 1024)
            if self.metadata_file.exists():
                stats["database_size_mb"] += self.metadata_file.stat().st_size / (1024 * 1024)
            if self.vectors_file.exists():
                stats["database_size_mb"] += self.vectors_file.stat().st_size / (1024 * 1024)
        except Exception as e:
            # 记录文件大小计算错误
            if not hasattr(self, 'file_size_errors'):
                self.file_size_errors = []
            self.file_size_errors.append({
                'error': str(e),
                'timestamp': time.time()
            })
            # 使用默认值
            stats["database_size_mb"] = 0.0
        
        return stats
    
    def clear_database(self):
        """清空向量数据库"""
        try:
            if self.index_file.exists():
                self.index_file.unlink()
            if self.metadata_file.exists():
                self.metadata_file.unlink()
            if self.vectors_file.exists():
                self.vectors_file.unlink()
            
            self.index = None
            self.metadata = []
            
            self.logger.info("向量数据库已清空")
        except Exception as e:
            self.logger.error(f"清空向量数据库失败: {e}")


def get_vector_database_manager() -> VectorDatabaseManager:
    """获取向量数据库管理器实例"""
    return VectorDatabaseManager()
