#!/usr/bin/env python3
"""
FAISS Memory Utilities - Index Management Helpers

提取的FAISS索引管理辅助函数
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


def resolve_faiss_index_path(index_path: Optional[str] = None) -> str:
    """解析FAISS索引路径"""
    if index_path:
        return index_path
    
    default_path = os.environ.get('FAISS_INDEX_PATH', './data/faiss_index')
    return default_path


def ensure_directory(path: str) -> None:
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)


def get_faiss_dimension() -> int:
    """获取FAISS向量维度"""
    return int(os.environ.get('FAISS_DIMENSION', 384))


def get_faiss_index_type() -> str:
    """获取FAISS索引类型"""
    return os.environ.get('FAISS_INDEX_TYPE', 'IndexFlatIP')


def get_faiss_batch_size() -> int:
    """获取批处理大小"""
    return int(os.environ.get('FAISS_BATCH_SIZE', 1000))


def get_faiss_nprobe() -> int:
    """获取搜索参数nprobe"""
    return int(os.environ.get('FAISS_NPROBE', 10))


def check_faiss_availability() -> bool:
    """检查FAISS是否可用"""
    try:
        import faiss
        return True
    except ImportError:
        logger.warning("FAISS not available")
        return False


def check_sentence_transformers_availability() -> bool:
    """检查sentence-transformers是否可用"""
    try:
        from sentence_transformers import SentenceTransformer
        return True
    except ImportError:
        logger.warning("sentence-transformers not available")
        return False


def validate_index_file(index_path: str) -> bool:
    """验证索引文件是否存在且有效"""
    if not os.path.exists(index_path):
        return False
    
    # 检查文件大小
    file_size = os.path.getsize(index_path)
    if file_size == 0:
        logger.warning(f"Index file is empty: {index_path}")
        return False
    
    return True


def get_index_file_info(index_path: str) -> Dict[str, Any]:
    """获取索引文件信息"""
    if not os.path.exists(index_path):
        return {
            "exists": False,
            "size": 0,
            "modified": None
        }
    
    stat = os.stat(index_path)
    return {
        "exists": True,
        "size": stat.st_size,
        "modified": stat.st_mtime,
        "path": index_path
    }
