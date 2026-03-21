# 检测模块 (Detection Modules)

本目录包含RANGEN系统的所有检测相关模块，这些模块不属于核心系统功能，而是用于质量检测、监控、评估和分析的辅助工具。

## 目录结构

```
src/detection/
├── quality/           # 质量检测模块
│   ├── unified_intelligent_quality_center.py
│   ├── code_quality_checker.py
│   ├── automated_quality_monitor.py
│   └── __init__.py
├── monitoring/        # 监控模块
│   ├── system_health_checker.py
│   ├── system_monitor.py
│   ├── performance_monitor.py
│   ├── resource_monitor.py
│   └── __init__.py
├── evaluation/        # 评估模块
│   ├── async_evaluation_system.py
│   ├── evaluation_performance_optimizer.py
│   ├── evaluation_optimizer.py
│   └── __init__.py
├── analysis/          # 分析模块
│   ├── intelligent_feature_analyzer.py
│   ├── semantic_embedding_analyzer.py
│   └── __init__.py
└── README.md
```

## 模块分类

### 质量检测模块 (quality/)
- **UnifiedIntelligentQualityCenter**: 统一智能质量检测中心
- **CodeQualityChecker**: 代码质量检查器
- **AutomatedQualityMonitor**: 自动化质量监控器

### 监控模块 (monitoring/)
- **SystemHealthChecker**: 系统健康检查器
- **SystemMonitor**: 系统监控器
- **PerformanceMonitor**: 性能监控器
- **ResourceMonitor**: 资源监控器

### 评估模块 (evaluation/)
- **AsyncEvaluationSystem**: 异步评估系统
- **EvaluationPerformanceOptimizer**: 评估性能优化器
- **EvaluationOptimizer**: 评估优化器

### 分析模块 (analysis/)
- **IntelligentFeatureAnalyzer**: 智能特征分析器
- **SemanticEmbeddingAnalyzer**: 语义嵌入分析器

## 使用示例

### 质量检测
```python
from src.detection.quality import UnifiedIntelligentQualityCenter, CodeQualityChecker

# 使用质量检测中心
quality_center = UnifiedIntelligentQualityCenter()
issues = quality_center.analyze_file('src/agents/base_agent.py')

# 使用代码质量检查器
checker = CodeQualityChecker()
issues = checker.check_code_quality('src/agents/base_agent.py', content)
```

### 系统监控
```python
from src.detection.monitoring import SystemHealthChecker, SystemMonitor

# 使用系统健康检查器
health_checker = SystemHealthChecker()
report = await health_checker.run_comprehensive_health_check()

# 使用系统监控器
monitor = SystemMonitor()
monitor.start_monitoring()
```

### 自动化质量监控
```python
from src.detection.quality import AutomatedQualityMonitor

# 运行质量扫描
monitor = AutomatedQualityMonitor()
report = monitor.run_quality_scan(['src/agents', 'src/utils'])
```

## 设计原则

1. **分离关注点**: 检测模块与核心系统功能分离
2. **模块化设计**: 每个检测功能独立成模块
3. **统一接口**: 提供一致的检测接口
4. **可扩展性**: 支持添加新的检测功能
5. **可配置性**: 支持配置检测参数和规则

## 注意事项

- 这些模块是辅助工具，不是核心系统功能
- 可以独立运行，不依赖核心系统
- 建议在开发环境中使用，生产环境可选
- 定期运行质量检测以保持代码质量
