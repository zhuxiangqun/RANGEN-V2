# 工具模块 (Tools)

本目录包含RANGEN系统的所有辅助工具模块，这些模块不属于核心系统功能，而是用于检测、监控、评估和分析的独立工具。

## 目录结构

```
tools/
├── detection/         # 检测工具模块
│   ├── quality/       # 质量检测工具
│   ├── monitoring/    # 监控工具
│   ├── evaluation/    # 评估工具
│   ├── analysis/      # 分析工具
│   └── README.md
└── README.md
```

## 模块分类

### 检测工具 (detection/)
- **质量检测** (quality/): 代码质量检测、数据质量分析
- **监控工具** (monitoring/): 系统健康检查、性能监控、资源监控
- **评估工具** (evaluation/): 系统评估、功能评估
- **分析工具** (analysis/): 特征分析、语义分析

## 使用说明

这些工具模块可以独立使用，不依赖核心系统：

```python
# 质量检测工具
from tools.detection.quality import UnifiedIntelligentQualityCenter

# 监控工具
from tools.detection.monitoring import SystemHealthChecker

# 评估工具
from tools.detection.evaluation import AsyncEvaluationSystem

# 分析工具
from tools.detection.analysis import IntelligentFeatureAnalyzer
```

## 设计原则

1. **独立性**: 工具模块可以独立运行，不依赖核心系统
2. **模块化**: 每个工具功能独立，可以单独使用
3. **可配置**: 支持配置参数和规则
4. **可扩展**: 支持添加新的工具功能
5. **可维护**: 清晰的代码结构和文档

## 注意事项

- 这些是辅助工具，不是核心系统功能
- 可以独立开发和测试
- 建议在开发环境中使用
- 生产环境可选使用
