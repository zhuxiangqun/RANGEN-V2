"""
⚠️ DEPRECATED - 废弃模块

本文件已被废弃!

原始的 UnifiedResearchSystem 类 (5369行) 已拆分为模块化版本:

新的模块化版本位置: src/unified_research_system/

使用新版本:
```python
# 子模块
from src.unified_research_system import CacheManager, PerformanceMonitor
from src.unified_research_system import QueryAnalyzer, ResultProcessor
from src.unified_research_system import DecisionValidator, ContextBuilder

# 原始类 (仅用于兼容)
# from src.unified_research_system.original import UnifiedResearchSystem
```

本文件将在未来版本中移除。请尽快迁移到新版本！

迁移指南:
1. 缓存管理 → CacheManager
2. 性能监控 → PerformanceMonitor  
3. 查询分析 → QueryAnalyzer
4. 结果处理 → ResultProcessor
5. 决策验证 → DecisionValidator
6. 上下文构建 → ContextBuilder
"""

# 重新导出到新位置，保持向后兼容
from src.unified_research_system import (
    CacheManager,
    PerformanceMonitor,
    QueryAnalyzer,
    QueryAnalysis,
    ResultProcessor,
    ProcessingResult,
    DecisionValidator,
    Decision,
    EvidenceTrajectory,
    ContextBuilder,
)

__all__ = [
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
