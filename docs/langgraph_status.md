# Langgraph 文件状态总结

> 更新日期: 2026-03-12

## 生产使用情况

### 活跃使用 (被其他文件引用)

| 文件 | 引用数 | 使用位置 |
|------|--------|----------|
| `langgraph_unified_workflow.py` | 3 | core/, api/ |
| `langgraph_error_recovery.py` | 1 | 仅自身 |
| `langgraph_enhanced_error_recovery.py` | 1 | 仅自身 |
| `langgraph_performance_monitor.py` | 1 | 仅自身 |
| `langgraph_resilient_node.py` | 1 | 仅自身 |
| `langgraph_agent_nodes.py` | 2 | core/ |
| `langgraph_reasoning_nodes.py` | 2 | core/ |
| `langgraph_core_nodes.py` | 1 | core/ |
| `langgraph_config_nodes.py` | 1 | core/ |
| `langgraph_capability_nodes.py` | 1 | core/ |
| `langgraph_detailed_processing_nodes.py` | 1 | core/ |
| `langgraph_collaboration_nodes.py` | 1 | core/ |
| `langgraph_learning_nodes.py` | 1 | core/ |
| `langgraph_parallel_execution.py` | 1 | core/ |
| `langgraph_configurable_router.py` | 1 | core/ |
| `langgraph_subgraph_builder.py` | 1 | core/ |
| `langgraph_sop_nodes.py` | 1 | core/ |
| `langgraph_state_version_manager.py` | 1 | core/ |

### 已添加废弃警告

1. ✅ `langgraph_error_recovery.py`
2. ✅ `langgraph_enhanced_error_recovery.py`
3. ✅ `langgraph_performance_monitor.py`
4. ✅ `langgraph_monitoring_adapter.py`

---

## 建议清理计划

### P0 (立即可做)

1. **归档以下文件** (未被生产代码引用):
   - `langgraph_layered_workflow.py`
   - `langgraph_layered_workflow_fixed.py`
   - `simplified_layered_workflow.py`
   - `simplified_business_workflow.py`
   - `enhanced_simplified_workflow.py`
   - `langgraph_dynamic_workflow.py`

### P1 (需要测试)

1. **移除废弃警告** (这会破坏导入):
   - 不推荐，需要更新所有引用

### P2 (长期)

1. **合并节点文件**:
   - 将 10+ 个节点文件合并为一个目录
   - `langgraph_nodes/`

---

## 当前系统架构

```
API Server (:8000)
    │
    ├── RANGEN_USE_ENHANCED=1 → EnhancedExecutionCoordinator
    │                                  (推荐)
    │
    ├── RANGEN_USE_UNIFIED_RESEARCH=1 → UnifiedResearchSystem
    │                                        (完整但复杂)
    │
    └── 默认 → ExecutionCoordinator
                     │
                     └── StateGraph (5 nodes)
```

---

## 推荐的工作流

| 场景 | 推荐 | 原因 |
|------|------|------|
| 简单问答 | ExecutionCoordinator | 最快 |
| 需要Hook/自学习 | EnhancedExecutionCoordinator | 功能完整 |
| 复杂多Agent | UnifiedResearchSystem | 功能最全 |

---

*本文件由系统自动生成 - 2026-03-12*
