"""
UnifiedResearchSystem 模块化版本

本模块将原来的单一文件拆分为多个独立模块:
- cache_manager: 缓存管理
- performance_monitor: 性能监控
- query_analyzer: 查询分析
- result_processor: 结果处理
- decision_validator: 决策验证
- context_builder: 上下文构建

主要类:
- UnifiedResearchSystem: 主系统类 (重构后)
- CacheManager: 缓存管理器
- PerformanceMonitor: 性能监控器
- QueryAnalyzer: 查询分析器
- ResultProcessor: 结果处理器
- DecisionValidator: 决策验证器
- ContextBuilder: 上下文构建器
"""

# 导出所有模块
from .cache_manager import CacheManager
from .performance_monitor import PerformanceMonitor
from .query_analyzer import QueryAnalyzer, QueryAnalysis
from .result_processor import ResultProcessor, ProcessingResult
from .decision_validator import DecisionValidator, Decision, EvidenceTrajectory
from .context_builder import ContextBuilder

__all__ = [
    # 主类
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
