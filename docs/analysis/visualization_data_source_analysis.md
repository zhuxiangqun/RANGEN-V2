# 可视化界面数据来源分析

## 问题描述

用户报告可视化界面中不同面板显示的内容不一致：
- **执行路径 (Execution Path)**: 只显示到 "Scheduling Optimization"
- **Execution Status**: 显示了很多已完成的节点（Route Query, Query Analysis, Scheduling Optimization, Generate Steps, Execute Step, Gather Evidence, Extract Step Answer, Format）
- **Orchestration Process**: 没有记录到编排事件
- **Final Answer**: 没有显示

## 数据来源分析

### 1. 执行路径 (Execution Path)

**数据来源**: 前端 `window.executionPath` 数组
**更新机制**: 
- 通过 `updateWorkflowGraphNode(nodeName, status)` 函数更新
- 该函数在收到 `node_update` WebSocket 消息时被调用
- 只有当节点状态变化（`running` 或 `completed`）时才会添加到执行路径

**问题**: 
- 如果 `node_update` 消息没有正确发送所有节点，执行路径就会不完整
- 如果节点名称不匹配（后端发送 `generate_steps`，前端查找 `Generate Steps`），节点可能找不到

### 2. Execution Status

**数据来源**: 前端 `nodeStatusMap` 对象
**更新机制**:
- 通过 `updateNodeStatus(nodeInfo)` 函数更新
- 该函数在收到 `node_update` WebSocket 消息时被调用
- 每个节点状态都会更新到 `nodeStatusMap[nodeName] = status`

**问题**:
- 如果 `node_update` 消息正确发送，但 `updateWorkflowGraphNode` 没有正确调用，会导致执行路径不完整

### 3. Orchestration Process

**数据来源**: 
- 主要：WebSocket 消息 `orchestration_events`（批量）或 `orchestration_event`（单个）
- 备用：API `/api/orchestration/{execution_id}`

**更新机制**:
- 通过 `displayOrchestrationEvent(event)` 函数显示
- 如果 WebSocket 消息中没有编排事件，会延迟 2 秒后从 API 获取

**问题**:
- 如果后端没有正确发送编排事件，或者发送时机不对，前端可能收不到

### 4. Final Answer

**数据来源**:
- 主要：WebSocket 消息 `execution_end` 中的 `final_result`
- 备用：API `/api/execution/{execution_id}`

**更新机制**:
- 通过 `displayFinalAnswer(result)` 函数显示
- 如果 WebSocket 消息中没有最终结果，会延迟 2 秒后从 API 获取

**问题**:
- 如果后端没有正确发送 `final_result`，或者发送时机不对，前端可能收不到

## 根本原因

### 问题 1: 执行路径不完整

**原因**: 
- `updateWorkflowGraphNode` 函数依赖于 `node_update` WebSocket 消息
- 如果某些节点的 `node_update` 消息没有发送，或者节点名称不匹配，执行路径就会不完整
- 在 `execution_end` 消息中，我们尝试通过 `executed_nodes` 列表补充，但这可能不够及时

**解决方案**:
- 确保所有执行的节点都发送 `node_update` 消息
- 在 `execution_end` 消息中，确保 `executed_nodes` 列表包含所有实际执行的节点
- 统一节点名称格式（后端使用下划线，前端也使用下划线）

### 问题 2: 编排事件缺失

**原因**:
- 编排事件可能没有正确发送，或者发送时机不对
- 前端可能在编排事件发送之前就尝试获取

**解决方案**:
- 确保在 `execution_end` 消息发送之前，所有编排事件都已发送
- 增加重试机制，如果 WebSocket 消息中没有编排事件，从 API 获取

### 问题 3: 最终答案缺失

**原因**:
- `final_result` 可能没有正确构建或发送
- 前端可能在 `final_result` 发送之前就尝试获取

**解决方案**:
- 确保 `final_result` 正确构建并包含在 `execution_end` 消息中
- 增加重试机制，如果 WebSocket 消息中没有最终结果，从 API 获取

## 数据流统一方案

### 方案 1: 统一数据源（推荐）

**目标**: 所有面板都从同一个数据源获取数据

**实现**:
1. 后端在 `execution_end` 消息中发送完整的状态快照：
   ```json
   {
     "type": "execution_end",
     "executed_nodes": ["route_query", "query_analysis", ...],
     "final_result": {...},
     "orchestration_events": [...],
     "node_states": {
       "route_query": {"status": "completed", "timestamp": ...},
       "query_analysis": {"status": "completed", "timestamp": ...},
       ...
     }
   }
   ```

2. 前端在收到 `execution_end` 消息时，统一更新所有面板：
   - 更新执行路径（从 `executed_nodes`）
   - 更新 Execution Status（从 `node_states`）
   - 显示编排事件（从 `orchestration_events`）
   - 显示最终答案（从 `final_result`）

### 方案 2: 增强实时更新

**目标**: 确保所有 `node_update` 消息都正确发送和接收

**实现**:
1. 后端确保每个节点执行时都发送 `node_update` 消息（包括 `running` 和 `completed` 状态）
2. 前端确保所有 `node_update` 消息都正确更新执行路径和状态
3. 在 `execution_end` 消息中，发送完整的节点列表作为补充

## 当前修复状态

### 已修复

1. ✅ **执行路径更新**: 在 `execution_end` 消息处理中，将所有 `executed_nodes` 添加到执行路径
2. ✅ **编排事件发送**: 在 `execution_end` 消息发送之前，批量发送所有编排事件
3. ✅ **最终答案发送**: 确保 `execution_end` 消息包含 `final_result`
4. ✅ **节点状态判断**: 修复了 OpenTelemetry Traces 的状态判断逻辑

### 待优化

1. ⚠️ **节点名称统一**: 确保后端发送的节点名称与前端查找的节点名称一致
2. ⚠️ **数据同步**: 确保所有面板的数据都从同一个数据源获取，避免不一致

## 建议

1. **统一节点名称格式**: 后端和前端都使用下划线格式（如 `generate_steps`），前端显示时再转换为可读格式（如 `Generate Steps`）
2. **增强日志**: 在关键位置添加日志，帮助诊断数据流问题
3. **数据验证**: 在 `execution_end` 消息中，验证所有必要的数据都已包含
4. **错误处理**: 如果某个数据源失败，自动从备用数据源获取

