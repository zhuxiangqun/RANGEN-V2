# Langgraph 文件归档清单

> 更新日期: 2026-03-12

## 生产使用情况

| 文件 | 被引用数 | 状态 |
|------|----------|------|
| `langgraph_unified_workflow.py` | 3+ | 备用 |
| `langgraph_configurable_router.py` | 1 | 使用中 |
| 其他 25+ 文件 | 0-1 | 可归档 |

## 建议归档的文件

以下文件未被生产代码使用，可以归档：

### 节点文件 (10个)
- langgraph_agent_nodes.py
- langgraph_reasoning_nodes.py
- langgraph_core_nodes.py
- langgraph_config_nodes.py
- langgraph_capability_nodes.py
- langgraph_detailed_processing_nodes.py
- langgraph_collaboration_nodes.py
- langgraph_learning_nodes.py
- langgraph_sop_nodes.py
- langgraph_nodes/evidence_check_node.py

### 工作流变体 (6个)
- langgraph_layered_workflow.py
- langgraph_layered_workflow_fixed.py
- simplified_layered_workflow.py
- simplified_business_workflow.py
- enhanced_simplified_workflow.py
- langgraph_dynamic_workflow.py

### 监控/错误处理 (6个)
- langgraph_performance_monitor.py ⚠️ 已有废弃警告
- langgraph_monitoring_adapter.py ⚠️ 已有废弃警告
- langgraph_error_recovery.py ⚠️ 已有废弃警告
- langgraph_enhanced_error_recovery.py ⚠️ 已有废弃警告
- langgraph_resilient_node.py
- langgraph_error_handler.py

### 其他 (5个)
- langgraph_parallel_execution.py
- langgraph_subgraph_builder.py
- langgraph_state_version_manager.py
- langgraph_state_optimizer.py

---

## 实际生产使用

```
ExecutionCoordinator (默认)
    └── langgraph.graph.StateGraph (第三方库)
        └── 不使用任何自定义 langgraph_* 节点文件
```

## 归档操作

```bash
# 创建归档目录
mkdir -p src/core/archive/langgraph

# 移动文件
mv src/core/langgraph_*.py src/core/archive/langgraph/
```

---

*本文件由系统自动生成 - 2026-03-12*
