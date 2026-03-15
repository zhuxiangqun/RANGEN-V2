# Langgraph 文件状态说明

> 最后更新: 2026-03-12

## 实际生产使用情况

### 错误处理
| 实现 | 状态 | 使用位置 | 说明 |
|------|------|----------|------|
| `UnifiedErrorHandler` (utils/research_logger.py) | ✅ **生产** | 10+ 文件 | 实际使用的错误处理 |
| `CheckpointErrorRecovery` (langgraph_error_recovery.py) | ❌ 未使用 | 仅 langgraph_unified_workflow.py | 未使用的工作流 |
| `EnhancedErrorRecovery` (langgraph_enhanced_error_recovery.py) | ❌ 未使用 | 仅 langgraph_unified_workflow.py | 未使用的工作流 |

### 监控/可观测性
| 实现 | 状态 | 使用位置 | 说明 |
|------|------|----------|------|
| `PerformanceMonitor` (tools/monitoring/) | ✅ **生产** | 多个服务 | 实际使用的性能监控 |
| `ModelPerformanceMonitor` (ml_framework/) | ✅ **生产** | ML训练 | 模型性能监控 |
| `HookMonitor` (hook/) | ✅ **生产** | Hook系统 | Hook监控 |
| `langgraph_monitoring_adapter.py` | ❌ 未使用 | 仅测试 | 未使用 |
| `langgraph_performance_monitor.py` | ❌ 未使用 | 仅 langgraph_unified_workflow.py | 未使用的工作流 |

---

## 生产状态总结

| 类别 | 实际使用 | 未使用 |
|------|----------|--------|
| **工作流** | ExecutionCoordinator, UnifiedResearchSystem | 25+ 变体 |
| **错误处理** | UnifiedErrorHandler | 3个 langgraph_*error* 文件 |
| **监控** | PerformanceMonitor, ModelPerformanceMonitor, HookMonitor | 2个 langgraph_*monitor* 文件 |

---

## 需归档文件 (未在生产使用)

以下文件可以归档或标记废弃：

### 错误处理 (仅被未使用的工作流引用)
- [ ] `src/core/langgraph_error_recovery.py`
- [ ] `src/core/langgraph_enhanced_error_recovery.py`
- [ ] `src/core/langgraph_error_handler.py`
- [ ] `src/core/langgraph_resilient_node.py`

### 监控 (仅被未使用的工作流引用)
- [ ] `src/core/langgraph_monitoring_adapter.py`
- [ ] `src/core/langgraph_performance_monitor.py`
- [ ] `src/core/langgraph_opentelemetry_integration.py`
- [ ] `src/core/langgraph_performance_optimizer.py`

### 状态定义 (未被生产代码引用)
- [ ] `src/core/langgraph_layered_workflow.py` - LayeredWorkflowState
- [ ] `src/core/simplified_business_workflow.py` - SimplifiedBusinessState
- [ ] `src/core/simplified_layered_workflow.py`
- [ ] `src/core/enhanced_simplified_workflow.py`
- [ ] `src/core/langgraph_dynamic_workflow.py`
- [ ] `src/core/langgraph_state_optimizer.py`
- [ ] `src/core/langgraph_state_version_manager.py`

---
#JB|
#JB|## 归档状态
#JB|
#JB|### 已添加废弃警告的文件 (2026-03-12)
#JB|
#JB|这些文件保留了导入功能，但会在导入时显示废弃警告：
#JB|
#JB|1. ✅ `langgraph_error_recovery.py` - 已添加 `warnings.warn(DeprecationWarning)`
#JB|2. ✅ `langgraph_enhanced_error_recovery.py` - 已添加 `warnings.warn(DeprecationWarning)`
#JB|3. ✅ `langgraph_performance_monitor.py` - 已添加 `warnings.warn(DeprecationWarning)`
#JB|4. ✅ `langgraph_monitoring_adapter.py` - 已添加 `warnings.warn(DeprecationWarning)`
#JB|
#JB|### 可归档文件 (未被任何活跃代码导入)
#JB|
#JB|以下文件可以安全归档 (未添加废弃警告以避免破坏可能的依赖):
#JB|
#JB|- `langgraph_layered_workflow.py`
#JB|- `langgraph_layered_workflow_fixed.py`
#JB|- `simplified_layered_workflow.py`
#JB|- `simplified_business_workflow.py`
#JB|- `enhanced_simplified_workflow.py`
#JB|- `langgraph_dynamic_workflow.py`
#JB|- `langgraph_state_optimizer.py`
#JB|- `langgraph_state_version_manager.py`
#JB|
#JB|归档位置: `src/core/archive/`
#JB|
#JB|---
#JB|
#JB|## 决策记录
#JB|
#JB|- 2026-03-12: 分析完成，确认实际使用的错误处理是 `UnifiedErrorHandler`
#JB|- 2026-03-12: 分析完成，确认实际使用的监控是分散的
#JB|- 2026-03-12: 为4个关键未使用文件添加了废弃警告
#JB|- 2026-03-12: 创建了 archive/ 目录准备归档其他文件

## 决策记录

- 2026-03-12: 分析完成，确认实际使用的错误处理是 `UnifiedErrorHandler`
- 2026-03-12: 分析完成，确认实际使用的监控是分散的 (PerformanceMonitor, ModelPerformanceMonitor, HookMonitor)
- 2026-03-12: 确定 25+ 文件可以被归档

---

## 建议行动

1. **P0 (立即)**: 无需行动 - 生产代码未受影响
2. **P1 (1周)**: 将未使用文件移动到 `archive/` 文件夹
3. **P2 (1月)**: 考虑合并分散的监控实现 (可选)
