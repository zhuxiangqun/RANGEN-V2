"""
服务层模块
提供各种外部服务的统一接口
"""

import logging

logger = logging.getLogger(__name__)

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

# 配置服务
try:
    from .config_service import ConfigService
    __all__.append('ConfigService')
except ImportError:
    logger.warning("ConfigService not available")

# 多模型配置服务
try:
    from .multi_model_config_service import (
        ModelProvider,
        RoutingStrategy,
        ModelConfig,
        RoutingConfig,
        CostOptimizationConfig,
        PerformanceBenchmarkConfig,
        MultiModelConfigService,
        get_multi_model_config_service
    )
    __all__.extend([
        'ModelProvider',
        'RoutingStrategy',
        'ModelConfig',
        'RoutingConfig',
        'CostOptimizationConfig',
        'PerformanceBenchmarkConfig',
        'MultiModelConfigService',
        'get_multi_model_config_service'
    ])
except ImportError as e:
    logger.warning(f"Multi model config service not available: {e}")

# 故障容忍服务
try:
    from .fault_tolerance_service import (
        ModelPriority,
        FailureType,
        ModelHealth,
        FallbackChainConfig,
        FaultToleranceStats,
        FaultToleranceService,
        get_fault_tolerance_service
    )
    __all__.extend([
        'ModelPriority',
        'FailureType',
        'ModelHealth',
        'FallbackChainConfig',
        'FaultToleranceStats',
        'FaultToleranceService',
        'get_fault_tolerance_service'
    ])
except ImportError as e:
    logger.warning(f"Fault tolerance service not available: {e}")

# StepFlash适配器服务
try:
    from .stepflash_adapter import StepFlashAdapter
    __all__.append('StepFlashAdapter')
except ImportError:
    logger.warning("StepFlashAdapter not available")
