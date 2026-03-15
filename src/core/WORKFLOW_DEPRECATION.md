# 工作流文件状态说明

## 状态：已整理

### 当前活跃的工作流

| 文件 | 状态 | 说明 |
|------|------|------|
| `execution_coordinator.py` | ✅ 活跃 | API 实际使用的工作流 (LangGraph) |
| `simplified_layered_workflow.py` | ✅ 可选 | 分层工作流替代实现 (asyncio) |
| `simplified_business_workflow.py` | ✅ 可选 | 业务工作流替代实现 (LangGraph) |
| `langgraph_unified_workflow.py` | ⚠️ 保留 | 状态定义模块 (ResearchSystemState)，仅用于类型定义 |

### 统一入口

| 文件 | 说明 |
|------|------|
| `unified_workflow_facade.py` | 统一工作流门面，支持模式切换 |

### 状态定义说明

| 状态类 | 位置 | 字段数 | 使用场景 |
|--------|------|--------|----------|
| `AgentState` | execution_coordinator.py | 10 | ✅ 生产默认 |
| `ExtendedAgentState` | unified_state.py | 30+ | 推荐用于新功能 |
| `ReActState` | workflows/react_workflow.py | 15 | ReasoningAgent |
| `ResearchSystemState` | langgraph_unified_workflow.py | 60+ | ❌ 未使用 |

### 访问方式

```python
# 方式 1: 直接使用 ExecutionCoordinator (当前默认)
from src.core.execution_coordinator import ExecutionCoordinator
coordinator = ExecutionCoordinator()

# 方式 2: 使用统一工作流门面 (支持模式切换)
from src.core.unified_workflow_facade import get_workflow, WorkflowMode
facade = get_workflow()

# 获取不同模式的工作流
workflow = facade.get_workflow()  # 默认
workflow = facade.get_workflow(WorkflowMode.LAYERED)
workflow = facade.get_workflow(WorkflowMode.BUSINESS)
```

### 已弃用的文件 (Deprecation Warnings Added)

以下文件已添加弃用警告，不建议在新代码中使用：

- `langgraph_parallel_execution.py` ❌
- `langgraph_dynamic_workflow.py` ❌
- `langgraph_learning_nodes.py` ❌
- `langgraph_collaboration_nodes.py` ❌
- `langgraph_capability_nodes.py` ❌
- `langgraph_error_recovery.py` ❌
- `langgraph_enhanced_error_recovery.py` ❌
- `langgraph_performance_monitor.py` ❌
- `langgraph_monitoring_adapter.py` ❌

### 决策说明

1. **保留 `langgraph_unified_workflow.py`**: 被 17+ 核心文件导入用作 `ResearchSystemState` 类型定义
2. **保留两个简化工作流**: 实现方式不同（asyncio vs LangGraph），保留作为可选替代
3. **API 保持使用 ExecutionCoordinator**: 向后兼容，UnifiedWorkflowFacade 可选使用
4. **新增 UnifiedWorkflowFacade**: 提供统一入口，支持工作流模式切换
5. **统一状态定义**: 推荐使用 `AgentState` (生产) 或 `ExtendedAgentState` (新功能)
