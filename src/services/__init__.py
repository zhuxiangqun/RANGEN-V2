"""
服务层模块
提供各种外部服务的统一接口
"""

# 本地模型服务（开发环境）
try:
    from .local_model_extract_service import (
        LocalModelExtractService,
        HybridExtractService
    )
    __all__ = ['LocalModelExtractService', 'HybridExtractService']
except (ImportError, PermissionError, OSError) as e:
    logger.warning(f"Local model extract service not available: {e}")
    __all__ = []

# LangExtract 服务（生产环境）
try:
    from .langextract_service import LangExtractService
    __all__.append('LangExtractService')
except ImportError:
    pass
