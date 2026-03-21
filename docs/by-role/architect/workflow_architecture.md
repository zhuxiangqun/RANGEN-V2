# RANGEN 工作流架构设计

> 最后更新: 2026-03-22

## 核心理念

```
基盘 = 执行引擎 + 内部工作流
用户工作流 = 数据 (由用户或自动创建系统生成)
```

## 一、执行引擎

**文件**: `src/orchestration/executor/production_workflow.py`

基于 langgraph_unified_workflow.py 简化而来的生产版本。

### 核心节点

```
route_query → [simple/complex/reasoning] → synthesize → format → END
```

| 节点 | 功能 |
|------|------|
| route_query | 路由判断 |
| simple_query | 简单查询 |
| complex_query | 复杂查询 + RAG |
| reasoning | 深度推理 |
| synthesize | 综合结果 |
| format | 格式化输出 |

## 二、核心组件

### 推理引擎
**文件**: `src/orchestration/real_reasoning_engine.py`

### 编排层组件
| 组件 | 文件位置 | 说明 |
|------|----------|------|
| ExecutionCoordinator | `src/orchestration/executor/execution_coordinator.py` | 执行协调 |
| UnifiedToolExecutor | `src/orchestration/executor/unified_tool_executor.py` | 工具执行 |
| IntelligentRouter | `src/orchestration/routing/intelligent_router.py` | 智能路由 |

### LangGraph节点
| 节点 | 文件位置 |
|------|----------|
| Agent节点 | `src/orchestration/langgraph_nodes/langgraph_agent_nodes.py` |
| 推理节点 | `src/orchestration/langgraph_nodes/langgraph_reasoning_nodes.py` |
| 核心节点 | `src/orchestration/langgraph_nodes/langgraph_core_nodes.py` |
| 学习节点 | `src/orchestration/langgraph_nodes/langgraph_learning_nodes.py` |

## 三、启动方式

### 统一服务器
```bash
python scripts/start_unified_server.py --port 8080
```

### 可视化服务器
```bash
python examples/start_visualization_server.py
```

---

*最后更新: 2026-03-22*
