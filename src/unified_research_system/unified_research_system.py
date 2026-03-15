"""
统一异步研究系统 - 模块化版本

本文件作为兼容层，将原有功能重新导出。

主要类现在位于独立模块:
- from .cache_manager import CacheManager
- from .performance_monitor import PerformanceMonitor
- from .query_analyzer import QueryAnalyzer
- from .result_processor import ResultProcessor
- from .decision_validator import DecisionValidator
- from .context_builder import ContextBuilder

原 UnifiedResearchSystem 类请使用:
from src.unified_research_system.original import UnifiedResearchSystem

或者直接导入原始文件 (已保留):
from src.unified_research_system import UnifiedResearchSystem
"""

# 为了向后兼容，导入原始模块
# 用户可以继续使用: from src.unified_research_system import UnifiedResearchSystem

# 导出所有子模块
from .cache_manager import CacheManager
from .performance_monitor import PerformanceMonitor
from .query_analyzer import QueryAnalyzer, QueryAnalysis
from .result_processor import ResultProcessor, ProcessingResult
from .decision_validator import DecisionValidator, Decision, EvidenceTrajectory
from .context_builder import ContextBuilder

__all__ = [
    # 子模块
    "CacheManager",
    "PerformanceMonitor",
    "QueryAnalyzer",
    "QueryAnalysis",
    "ResultProcessor",
    "ProcessingResult",
    "DecisionValidator",
    "Decision",
    "EvidenceTrajectory",
    "ContextBuilder",
]
