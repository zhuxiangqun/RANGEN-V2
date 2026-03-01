#!/usr/bin/env python3
"""
向量知识库 - 使用FAISS实现高效向量检索
"""

import numpy as np
import pickle
import os
import hashlib
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS未安装，向量检索功能将不可用")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("SentenceTransformers未安装，向量检索功能将不可用")


logger = logging.getLogger(__name__)


class VectorKnowledgeBase:
    """向量知识库 - 使用FAISS进行高效语义检索"""
    
    def __init__(self, dimension: int = 384, index_path: str = "data/vector_knowledge_index.bin"):
        """
        初始化向量知识库
        
        Args:
            dimension: 向量维度
            index_path: 索引文件路径
        """
        self.dimension = dimension
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.index = None
        self.embeddings = []  # 存储原始嵌入
        self.metadata = []   # 存储元数据（文本、来源等）
        
        # 🚀 方案5.3：查询Embedding缓存（避免重复调用Jina API，支持环境变量配置TTL）
        self._embedding_cache: Dict[str, Dict[str, Any]] = {}  # 内存缓存
        import os
        self._embedding_cache_ttl = int(os.getenv('EMBEDDING_CACHE_TTL', '86400'))  # 默认24小时，可通过环境变量配置
        self._embedding_cache_path = Path("data/learning/embedding_cache.json")  # 持久化缓存路径
        self._embedding_cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._embedding_cache_hits = 0  # 缓存命中次数
        self._embedding_cache_misses = 0  # 缓存未命中次数
        self._embedding_cache_save_counter = 0  # 缓存保存计数器
        
        # 🆕 优先使用本地模型（完全免费，无需API密钥）
        self.model = None
        self._jina_service = None
        self._local_model = None
        
        # 检查是否使用英文向量化器配置
        self.use_english_vectorizer = os.getenv("USE_ENGLISH_VECTORIZER", "true").lower() == "true"
        
        # 优先尝试加载本地模型
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # 根据配置选择合适的英文模型
                if self.use_english_vectorizer:
                    local_model_name = os.getenv("ENGLISH_EMBEDDING_MODEL", "all-mpnet-base-v2")
                else:
                    local_model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "all-mpnet-base-v2")
                
                # 🆕 尝试使用镜像源（如果网络有问题）
                hf_endpoint = os.getenv("HF_ENDPOINT")
                if not hf_endpoint:
                    # 默认使用镜像源，提高下载成功率
                    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                    logger.debug("使用HuggingFace镜像源: https://hf-mirror.com")
                
                model_type = "英文向量化模型" if self.use_english_vectorizer else "本地embedding模型"
                logger.info(f"🔄 正在加载{model_type}: {local_model_name}...")
                # 🆕 优先尝试从本地缓存加载（避免网络连接）
                try:
                    # 首先尝试只使用本地文件（如果模型已下载）
                    self._local_model = SentenceTransformer(local_model_name, local_files_only=True)
                    self.embedding_dim = self._local_model.get_sentence_embedding_dimension()
                    logger.info(f"✅ 已从本地缓存加载{model_type}: {local_model_name} (维度: {self.embedding_dim})")
                except Exception as local_error:
                    # 如果本地加载失败，尝试网络下载（使用镜像源）
                    logger.debug(f"本地缓存加载失败，尝试网络下载: {local_error}")
                    self._local_model = SentenceTransformer(local_model_name, local_files_only=False)
                    self.embedding_dim = self._local_model.get_sentence_embedding_dimension()
                    logger.info(f"✅ 已从网络加载{model_type}: {local_model_name} (维度: {self.embedding_dim})")
                
                if self.use_english_vectorizer:
                    logger.info("💡 提示: 使用英文向量化模型处理英文Wikipedia内容")
                else:
                    logger.info("💡 提示: 本地模型完全免费，优先使用本地模型")
            except Exception as e:
                logger.warning(f"⚠️ 加载本地模型失败: {e}，将尝试Jina API fallback")
                logger.warning("💡 提示: 可以运行 scripts/download_local_model.py 手动下载模型")
                self._local_model = None
        
        # Fallback: 如果本地模型不可用，尝试Jina API
        if not self._local_model:
            try:
                from src.utils.unified_jina_service import get_jina_service
                self._jina_service = get_jina_service()
                if self._jina_service and self._jina_service.api_key:
                    # 通过一次测试调用确定向量维度
                    test_embedding = self._jina_service.get_embedding("test")
                    if test_embedding is not None:
                        self.embedding_dim = int(test_embedding.shape[0])
                        logger.info(f"✅ 使用Jina Embedding服务（fallback），向量维度: {self.embedding_dim}")
                    else:
                        self.embedding_dim = dimension
                        logger.warning("⚠️ Jina服务测试失败，使用默认维度")
                else:
                    self.embedding_dim = dimension
                    logger.warning("⚠️ 本地模型和Jina API都不可用，使用默认维度")
            except Exception as e:
                logger.warning(f"⚠️ Jina服务初始化失败: {e}，使用默认维度")
                self.embedding_dim = dimension
        
        # 初始化索引
        if FAISS_AVAILABLE:
            try:
                self.index = faiss.IndexFlatL2(self.embedding_dim)  # type: ignore
            except Exception as e:
                logger.warning(f"初始化FAISS索引失败: {e}")
                self.index = None
                self.memory_index = {}
        else:
            logger.warning("FAISS未安装，使用内存存储")
            self.memory_index = {}  # 简单的内存索引
        
        self._loaded = False
        
        # 🚀 性能优化：加载持久化embedding缓存
        self._load_embedding_cache()
        
        # 🚀 性能优化：注册程序退出时保存缓存
        import atexit
        atexit.register(self._save_embedding_cache)
        
        # 尝试自动加载已有索引
        self.load()
    
    def encode_text(self, text: str) -> np.ndarray:
        """将文本编码为向量（🚀 优化：统一使用Jina API + Embedding缓存）"""
        # 🚀 性能优化：检查embedding缓存
        cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
        current_time = time.time()
        
        # 检查内存缓存
        if cache_key in self._embedding_cache:
            cached = self._embedding_cache[cache_key]
            cache_time = cached.get('timestamp', 0)
            cache_age = current_time - cache_time
            
            # 检查缓存是否过期
            if cache_age < self._embedding_cache_ttl:
                self._embedding_cache_hits += 1
                # 转换为numpy数组并返回
                embedding_array = np.array(cached['embedding'], dtype=np.float32)
                
                # 🚀 性能监控：记录缓存命中（前10次）
                if self._embedding_cache_hits <= 10:
                    logger.debug(f"✅ Embedding缓存命中: 文本='{text[:50]}...', 缓存年龄={cache_age/3600:.2f}小时")
                
                # 每10次命中记录一次统计
                if self._embedding_cache_hits % 10 == 0:
                    total_calls = self._embedding_cache_hits + self._embedding_cache_misses
                    if total_calls > 0:
                        hit_rate = (self._embedding_cache_hits / total_calls) * 100
                        logger.info(f"📊 Embedding缓存统计: 命中率={hit_rate:.1f}% (命中={self._embedding_cache_hits}, 未命中={self._embedding_cache_misses})")
                
                return embedding_array
            else:
                # 缓存过期，删除
                logger.debug(f"⏰ Embedding缓存过期: 文本='{text[:50]}...', 缓存年龄={cache_age/3600:.2f}小时")
                del self._embedding_cache[cache_key]
        
        # 缓存未命中，🆕 优先使用本地模型
        self._embedding_cache_misses += 1
        embedding_start_time = time.time()
        
        # 🆕 优先使用本地模型（完全免费，无需API密钥）
        if self._local_model:
            try:
                embedding = self._local_model.encode(text, convert_to_numpy=True)
                if embedding is not None:
                    embedding_array = np.array(embedding, dtype=np.float32)
                    embedding_time = time.time() - embedding_start_time
                    
                    # 保存到缓存
                    self._embedding_cache[cache_key] = {
                        'embedding': embedding_array.tolist(),  # 转换为列表以便JSON序列化
                        'timestamp': current_time,
                        'text_preview': text[:100]  # 保存文本预览用于调试
                    }
                    
                    # 🚀 性能优化：定期保存缓存（每10次调用保存一次）
                    self._embedding_cache_save_counter += 1
                    if self._embedding_cache_save_counter >= 10:
                        self._save_embedding_cache()
                        self._embedding_cache_save_counter = 0
                    
                    return embedding_array
            except Exception as e:
                logger.warning(f"⚠️ 本地模型向量化失败: {e}，尝试Jina API fallback")
        
        # Fallback: 如果本地模型不可用，尝试Jina API
        if self._jina_service and self._jina_service.api_key:
            try:
                embedding = self._jina_service.get_embedding(text)
                if embedding is not None:
                    embedding_array = np.array(embedding, dtype=np.float32)
                    embedding_time = time.time() - embedding_start_time
                    
                    # 🚀 性能监控：记录Jina API调用时间（超过5秒的警告）
                    if embedding_time > 5.0:
                        logger.warning(f"⚠️ Jina Embedding调用耗时: {embedding_time:.2f}秒 (文本='{text[:50]}...')")
                    elif self._embedding_cache_misses <= 10:
                        logger.debug(f"🔍 Jina Embedding调用: {embedding_time:.2f}秒 (文本='{text[:50]}...')")
                    
                    # 保存到缓存
                    self._embedding_cache[cache_key] = {
                        'embedding': embedding_array.tolist(),  # 转换为列表以便JSON序列化
                        'timestamp': current_time,
                        'text_preview': text[:100]  # 保存文本预览用于调试
                    }
                    
                    # 🚀 性能优化：定期保存缓存（每10次调用保存一次）
                    self._embedding_cache_save_counter += 1
                    if self._embedding_cache_save_counter >= 10:
                        self._save_embedding_cache()
                        self._embedding_cache_save_counter = 0
                    
                    return embedding_array
            except Exception as e:
                logger.warning(f"⚠️ Jina embedding失败: {e}，回退随机向量")
        
        # 最后fallback: 返回随机向量（临时方案，不依赖外部模型）
        logger.warning("⚠️ 本地模型和Jina API都不可用，返回随机向量")
        return np.random.randn(self.embedding_dim).astype('float32')
    
    def add_knowledge(self, text: str, metadata: Optional[Dict[str, Any]] = None, validate_quality: bool = True):
        """
        添加知识到向量库（🚀 增强：添加质量验证）
        
        Args:
            text: 知识文本
            metadata: 元数据（来源、时间等）
            validate_quality: 是否进行质量验证（默认True）
        
        Returns:
            bool: 是否成功添加
        """
        try:
            # 🚀 新增：质量验证
            if validate_quality:
                quality_result = self._validate_content_quality(text)
                if not quality_result['is_valid']:
                    logger.warning(
                        f"跳过低质量内容，不添加到向量库: {quality_result.get('reason', '质量检查失败')} | "
                        f"内容预览: {text[:100]}..."
                    )
                    return False
            
            embedding = self.encode_text(text)
            
            if FAISS_AVAILABLE and self.index:
                # 使用FAISS索引
                self.index.add(embedding.reshape(1, -1))  # type: ignore
                self.embeddings.append(embedding)
            else:
                # 使用内存存储
                idx = len(self.memory_index)
                self.memory_index[idx] = embedding
            
            self.metadata.append({
                'text': text,
                'metadata': metadata or {}
            })
            
            logger.debug(f"添加知识到向量库: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"添加知识失败: {e}")
            return False
    
    def add_knowledge_batch(self, texts: List[str], metadata_list: Optional[List[Dict[str, Any]]] = None, validate_quality: bool = True):
        """批量添加知识（🚀 增强：添加质量验证）"""
        if not texts:
            return
        
        # 🚀 新增：质量验证和过滤
        valid_texts = []
        valid_metadata = []
        skipped_count = 0
        
        for i, text in enumerate(texts):
            if validate_quality:
                quality_result = self._validate_content_quality(text)
                if not quality_result['is_valid']:
                    skipped_count += 1
                    logger.debug(f"跳过低质量内容: {quality_result.get('reason', '质量检查失败')}")
                    continue
            
            valid_texts.append(text)
            valid_metadata.append(metadata_list[i] if metadata_list and i < len(metadata_list) else {})
        
        if not valid_texts:
            logger.warning(f"批量添加：所有 {len(texts)} 个条目都未通过质量验证")
            return
        
        embeddings = []
        for text in valid_texts:
            embedding = self.encode_text(text)
            embeddings.append(embedding)
        
        embeddings_array = np.vstack(embeddings).astype('float32')
        
        if FAISS_AVAILABLE and self.index:
            self.index.add(embeddings_array)  # type: ignore
        
        for i, text in enumerate(valid_texts):
            self.metadata.append({
                'text': text,
                'metadata': valid_metadata[i]
            })
        
        logger.info(f"批量添加 {len(valid_texts)} 个知识条目（跳过 {skipped_count} 个低质量条目）")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关知识
        
        Args:
            query: 查询文本
            top_k: 返回top_k个结果
            
        Returns:
            List of [{'text': ..., 'metadata': ..., 'distance': ...}]
        """
        try:
            query_embedding = self.encode_text(query)
            
            if FAISS_AVAILABLE and self.index:
                # 使用FAISS搜索
                distances, indices = self.index.search(  # type: ignore
                    query_embedding.reshape(1, -1),
                    min(top_k, len(self.metadata))
                )
                
                results = []
                for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                    if idx < len(self.metadata):
                        results.append({
                            'text': self.metadata[idx]['text'],
                            'metadata': self.metadata[idx]['metadata'],
                            'distance': float(distance),
                            'rank': i + 1
                        })
                
                return results
            
            else:
                # 使用内存搜索（简单版本）
                results = []
                for idx, stored_embedding in self.memory_index.items():
                    distance = np.linalg.norm(query_embedding - stored_embedding)
                    if idx < len(self.metadata):
                        results.append({
                            'text': self.metadata[idx]['text'],
                            'metadata': self.metadata[idx]['metadata'],
                            'distance': float(distance),
                            'rank': 0
                        })
                
                # 按距离排序
                results.sort(key=lambda x: x['distance'])
                return results[:top_k]
        
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def save(self):
        """保存向量索引"""
        try:
            if self.index_path and self.index:
                # 保存FAISS索引
                faiss.write_index(self.index, str(self.index_path))  # type: ignore
                
                # 保存元数据
                metadata_path = self.index_path.with_suffix('.metadata')
                with open(metadata_path, 'wb') as f:
                    pickle.dump(self.metadata, f)
                
                logger.info(f"向量索引已保存到: {self.index_path}")
        except Exception as e:
            logger.error(f"保存向量索引失败: {e}")
    
    def load(self):
        """加载向量索引"""
        try:
            if self.index_path.exists() and FAISS_AVAILABLE:
                # 加载FAISS索引
                self.index = faiss.read_index(str(self.index_path))  # type: ignore
                
                # 加载元数据
                metadata_path = self.index_path.with_suffix('.metadata')
                if metadata_path.exists():
                    with open(metadata_path, 'rb') as f:
                        self.metadata = pickle.load(f)
                
                self._loaded = True
                logger.info(f"向量索引已加载: {self.index_path}")
                return True
        except Exception as e:
            logger.error(f"加载向量索引失败: {e}")
        
        return False
    
    def size(self) -> int:
        """获取知识库大小"""
        if FAISS_AVAILABLE and self.index:
            return self.index.ntotal
        else:
            return len(self.memory_index)
    
    def clear(self):
        """清空知识库"""
        if FAISS_AVAILABLE:
            self.index = faiss.IndexFlatL2(self.embedding_dim)  # type: ignore
        else:
            self.memory_index = {}
        
        self.metadata = []
        logger.info("知识库已清空")
    
    def _load_embedding_cache(self) -> None:
        """🚀 性能优化：从文件加载持久化embedding缓存"""
        try:
            if self._embedding_cache_path.exists():
                with open(self._embedding_cache_path, 'r', encoding='utf-8') as f:
                    loaded_cache = json.load(f)
                    
                    # 过滤过期缓存
                    current_time = time.time()
                    valid_cache = {}
                    expired_count = 0
                    
                    for key, value in loaded_cache.items():
                        if isinstance(value, dict):
                            cache_time = value.get('timestamp', 0)
                            cache_age = current_time - cache_time
                            # 只保留未过期的缓存
                            if cache_age < self._embedding_cache_ttl:
                                valid_cache[key] = value
                            else:
                                expired_count += 1
                    
                    self._embedding_cache = valid_cache
                    logger.info(f"✅ Embedding缓存已从文件加载: {self._embedding_cache_path}")
                    logger.info(f"   总缓存条目: {len(loaded_cache)}条")
                    logger.info(f"   有效缓存: {len(valid_cache)}条 (TTL: {self._embedding_cache_ttl/3600:.1f}小时)")
                    logger.info(f"   过期缓存: {expired_count}条")
            else:
                logger.info(f"Embedding缓存文件不存在，使用空缓存: {self._embedding_cache_path}")
        except Exception as e:
            logger.warning(f"加载Embedding缓存失败，使用空缓存: {e}")
    
    def _save_embedding_cache(self) -> None:
        """🚀 性能优化：保存embedding缓存到文件"""
        try:
            import time
            
            # 确保目录存在
            self._embedding_cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 过滤过期缓存（只保存有效缓存）
            current_time = time.time()
            valid_cache = {}
            
            for key, value in self._embedding_cache.items():
                if isinstance(value, dict):
                    cache_time = value.get('timestamp', 0)
                    # 只保存未过期的缓存
                    if current_time - cache_time < self._embedding_cache_ttl:
                        valid_cache[key] = value
            
            # 保存缓存
            with open(self._embedding_cache_path, 'w', encoding='utf-8') as f:
                json.dump(valid_cache, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Embedding缓存已保存到: {self._embedding_cache_path} ({len(valid_cache)}条)")
        except Exception as e:
            logger.warning(f"保存Embedding缓存失败: {e}")
    
    def _validate_content_quality(self, text: str) -> Dict[str, Any]:
        """🚀 新增：验证内容质量
        
        Args:
            text: 要验证的文本内容
        
        Returns:
            验证结果字典，包含is_valid、reason、quality_score等字段
        """
        try:
            if not text or not isinstance(text, str):
                return {
                    'is_valid': False,
                    'reason': '内容为空或不是字符串',
                    'quality_score': 0
                }
            
            text_stripped = text.strip()
            
            # 1. 基本长度检查
            if len(text_stripped) < 10:
                return {
                    'is_valid': False,
                    'reason': f'内容过短（{len(text_stripped)}字符，最少需要10字符）',
                    'quality_score': 0
                }
            
            if len(text_stripped) > 10000:
                return {
                    'is_valid': False,
                    'reason': f'内容过长（{len(text_stripped)}字符，最多允许10000字符）',
                    'quality_score': 0
                }
            
            quality_score = 100
            issues = []
            
            # 2. 检查是否包含HTML标签（未清理）
            if "<" in text_stripped and ">" in text_stripped:
                html_tags = ["<div", "<span", "<p>", "<br", "<a href", "<script", "<style"]
                if any(tag in text_stripped for tag in html_tags):
                    issues.append("包含未清理的HTML标签")
                    quality_score -= 30
            
            # 3. 检查是否包含引用标记（应该被清理）
            import re
            citation_pattern = r'\[\d+\]'
            if re.search(citation_pattern, text_stripped):
                issues.append("包含引用标记（如[1]、[2]等）")
                quality_score -= 10
            
            # 4. 检查是否包含特殊字符（可能是JSON残留）
            if '}},"i":0}}]}' in text_stripped or 'id="mw' in text_stripped:
                issues.append("包含JSON残留或HTML属性")
                quality_score -= 20
            
            # 5. 检查内容是否主要是空白字符
            if len(text_stripped) < len(text) * 0.5:
                issues.append("包含过多空白字符")
                quality_score -= 15
            
            # 6. 检查是否包含有效文本（至少有一些字母或中文）
            if not re.search(r'[a-zA-Z\u4e00-\u9fff]', text_stripped):
                return {
                    'is_valid': False,
                    'reason': '不包含有效文本（无字母或中文）',
                    'quality_score': 0
                }
            
            # 7. 检查是否是问题而非知识（简单检查）
            question_indicators = [
                '?', '？', 'how many', 'how much', 'what is', 'who is', 'when did',
                'where is', 'why did', 'how do', 'how can', 'can you', 'could you'
            ]
            text_lower = text_stripped.lower()
            question_count = sum(1 for indicator in question_indicators if indicator in text_lower[:200])
            
            # 如果包含多个问题指示词，且文本较短，可能是问题
            if question_count >= 2 and len(text_stripped) < 200:
                issues.append("可能是问题而非知识")
                quality_score -= 25
            
            # 8. 检查是否包含无意义的格式化内容
            meaningless_patterns = [
                '涉及的数字', '涉及的关键词', '问题主题',
                'numbers found', 'entities found', '问题:',
                '问题内容:', 'I understand you\'re asking'
            ]
            if any(pattern in text_stripped for pattern in meaningless_patterns):
                return {
                    'is_valid': False,
                    'reason': '包含无意义的格式化内容',
                    'quality_score': 0
                }
            
            # 9. 检查内容完整性（至少包含一些有意义的词）
            words = text_stripped.split()
            if len(words) < 5:
                issues.append("内容过短（少于5个词）")
                quality_score -= 20
            
            # 10. 检查是否主要是重复字符
            if len(set(text_stripped)) < len(text_stripped) * 0.1:
                return {
                    'is_valid': False,
                    'reason': '内容主要是重复字符',
                    'quality_score': 0
                }
            
            # 质量分数阈值：至少60分才通过
            is_valid = quality_score >= 60
            
            return {
                'is_valid': is_valid,
                'reason': '; '.join(issues) if issues else '质量检查通过',
                'quality_score': max(0, quality_score),
                'issues': issues
            }
            
        except Exception as e:
            logger.warning(f"内容质量验证失败: {e}")
            # 验证失败时，默认通过（避免误过滤）
            return {
                'is_valid': True,
                'reason': f'验证过程出错: {str(e)}',
                'quality_score': 50
            }


# 全局实例
_knowledge_base = None


def get_vector_knowledge_base() -> VectorKnowledgeBase:
    """获取向量知识库实例（单例模式）"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = VectorKnowledgeBase()
        # 尝试加载已有索引
        _knowledge_base.load()
    return _knowledge_base


def initialize_vector_knowledge_base():
    """初始化向量知识库"""
    base = get_vector_knowledge_base()
    
    # 如果索引为空，初始化一些默认知识
    if base.size() == 0:
        logger.info("初始化默认知识库...")
        # 可以在这里添加初始知识
        # base.add_knowledge("示例知识", {"source": "default"})
    
    return base

