"""
Embedding模型优化器 - 清理警告和提高性能
"""
import logging
import warnings
import os
from typing import Optional

logger = logging.getLogger(__name__)

def suppress_embedding_warnings():
    """抑制embedding模型相关的警告"""
    warnings.filterwarnings("ignore", category=FutureWarning, module="sentence_transformers")

    warnings.filterwarnings("ignore", message=".*use_auth_token.*")
    warnings.filterwarnings("ignore", message=".*No sentence-transformers model found.*")

    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

def get_optimized_model_name() -> str:
    """获取优化的模型名称"""
    return "all-MiniLM-L6-v2"  # 不使用sentence-transformers/前缀

def initialize_embedding_model_safely():
    """安全初始化embedding模型 - 使用全局管理器避免重复加载"""
    try:
        suppress_embedding_warnings()

            from src.utils.global_model_manager import get_sentence_transformer_model

        model_name = get_optimized_model_name()
        logger.info("通过全局管理器获取优化的embedding模型: {model_name}")

        device = 'cpu'
        try:
            import torch
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = 'mps'
            elif torch.cuda.is_available():
                device = 'cuda'
        except:
            pass

        model = get_sentence_transformer_model(
            model_name=model_name,
            device=device,
            cache_folder='models/cache'
        )

        if model is not None:
            logger.info("✅ 通过全局管理器获取Embedding模型成功，设备: {device}")
        else:
            logger.error("❌ 全局管理器获取Embedding模型失败")

        return model

    except Exception as e:
        logger.error("Embedding模型初始化失败: {e}")
        return None
