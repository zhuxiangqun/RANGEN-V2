# Orchestration Process 面板显示内容指南

## 📋 概述

**Orchestration Process**（编排过程）面板用于实时显示系统执行过程中的详细编排事件，包括 Agent 执行、工具调用、提示词工程和上下文工程等各个组件的活动。

## 🎯 显示内容

### 1. Agent 事件（🤖 蓝色）

#### Agent 生命周期事件
- **🤖 Agent 开始** (`agent_start`)
  - 显示：Agent 名称、开始时间
  - 详情：执行上下文信息

- **✅ Agent 结束** (`agent_end`)
  - 显示：Agent 名称、结束时间、执行时长
  - 详情：执行结果、错误信息（如果有）

#### Agent 内部活动事件
- **💭 Agent 思考** (`agent_think`)
  - 显示：Agent 名称、思考时间
  - 详情：思考内容

- **📋 Agent 规划** (`agent_plan`)
  - 显示：Agent 名称、规划时间
  - 详情：规划内容（计划步骤、策略等）

- **⚡ Agent 行动** (`agent_act`)
  - 显示：Agent 名称、行动时间
  - 详情：行动内容（调用的工具、参数等）

- **👁️ Agent 观察** (`agent_observe`)
  - 显示：Agent 名称、观察时间
  - 详情：观察结果（工具返回的结果等）

### 2. 工具事件（🔧 绿色）

- **🔧 工具开始** (`tool_start`)
  - 显示：工具名称、开始时间
  - 详情：工具参数

- **✅ 工具结束** (`tool_end`)
  - 显示：工具名称、结束时间、执行时长
  - 详情：工具返回结果、错误信息（如果有）

- **📞 工具调用** (`tool_call`)
  - 显示：工具名称、调用时间
  - 详情：调用参数和结果

### 3. 提示词工程事件（📝 橙色）

- **📝 生成提示词** (`prompt_generate`)
  - 显示：提示词类型、生成时间
  - 详情：生成的提示词内容（前200字符）、上下文信息

- **⚡ 优化提示词** (`prompt_optimize`)
  - 显示：提示词类型、优化时间
  - 详情：优化后的提示词、上下文信息

- **🎼 编排提示词** (`prompt_orchestrate`)
  - 显示：编排策略、编排时间
  - 详情：编排策略、提示词片段列表

### 4. 上下文工程事件（🔍 紫色）

- **🔍 增强上下文** (`context_enhance`)
  - 显示：增强类型、增强时间
  - 详情：增强后的上下文内容

- **🔄 更新上下文** (`context_update`)
  - 显示：更新类型、更新时间
  - 详情：更新的上下文内容

- **🔗 合并上下文** (`context_merge`)
  - 显示：合并类型、合并时间
  - 详情：合并后的上下文内容

## 📊 事件显示格式

每个事件以卡片形式显示，包含以下信息：

```
┌─────────────────────────────────────────┐
│ 🤖 Agent 开始  KnowledgeRetrievalAgent │
│                         14:23:45        │
│ └─ 查看详情                             │
│    {                                    │
│      "context": { ... }                │
│    }                                    │
└─────────────────────────────────────────┘
```

### 事件卡片结构

1. **左侧边框颜色**：根据组件类型显示不同颜色
   - 🔵 蓝色：Agent 事件
   - 🟢 绿色：工具事件
   - 🟠 橙色：提示词工程事件
   - 🟣 紫色：上下文工程事件

2. **事件标签**：显示事件类型和图标
   - 例如：`🤖 Agent 开始`、`🔧 工具开始`

3. **组件名称**：显示具体的 Agent 或工具名称
   - 例如：`KnowledgeRetrievalAgent`、`KnowledgeRetrievalTool`

4. **时间信息**：显示时间戳和执行时长
   - 格式：`14:23:45 (1234ms)`

5. **详细信息**：可展开查看的 JSON 数据
   - 点击"查看详情"展开/折叠
   - 显示事件相关的数据（参数、结果、错误等）

## 🔗 事件层级关系

事件之间通过 `parent_event_id` 建立层级关系：

- **父事件**：Agent 开始事件
- **子事件**：Agent 内部的思考、规划、行动、观察事件
- **子子事件**：工具调用事件（作为 Agent 行动的子事件）

子事件会**缩进显示**在父事件下方，形成树形结构：

```
🤖 Agent 开始  KnowledgeRetrievalAgent
  💭 Agent 思考  KnowledgeRetrievalAgent
  📋 Agent 规划  KnowledgeRetrievalAgent
  ⚡ Agent 行动  KnowledgeRetrievalAgent
    🔧 工具开始  KnowledgeRetrievalTool
    ✅ 工具结束  KnowledgeRetrievalTool
  👁️ Agent 观察  KnowledgeRetrievalAgent
✅ Agent 结束  KnowledgeRetrievalAgent
```

## 📝 示例显示内容

### 示例 1：简单查询执行

```
🤖 Agent 开始  ChiefAgent
  💭 Agent 思考  ChiefAgent
  📋 Agent 规划  ChiefAgent
  ⚡ Agent 行动  ChiefAgent
    🔧 工具开始  KnowledgeRetrievalTool
    ✅ 工具结束  KnowledgeRetrievalTool (234ms)
  👁️ Agent 观察  ChiefAgent
✅ Agent 结束  ChiefAgent (1234ms)

📝 生成提示词  answer_generation
⚡ 优化提示词  answer_generation
```

### 示例 2：复杂查询执行（带推理）

```
🤖 Agent 开始  ChiefAgent
  💭 Agent 思考  ChiefAgent
  📋 Agent 规划  ChiefAgent
  ⚡ Agent 行动  ChiefAgent
    🔧 工具开始  KnowledgeRetrievalTool
    ✅ 工具结束  KnowledgeRetrievalTool (456ms)
  👁️ Agent 观察  ChiefAgent
✅ Agent 结束  ChiefAgent (2345ms)

🤖 Agent 开始  ReasoningAgent
  💭 Agent 思考  ReasoningAgent
  📋 Agent 规划  ReasoningAgent
  ⚡ Agent 行动  ReasoningAgent
    🔧 工具开始  StepGeneratorTool
    ✅ 工具结束  StepGeneratorTool (1234ms)
  👁️ Agent 观察  ReasoningAgent
✅ Agent 结束  ReasoningAgent (5678ms)

📝 生成提示词  reasoning_step
🔍 增强上下文  evidence_retrieval
📝 生成提示词  answer_generation
```

## 🔍 如何查看详细信息

1. **展开事件详情**：
   - 点击事件卡片中的"查看详情"
   - 查看 JSON 格式的详细数据

2. **查看层级关系**：
   - 子事件会自动缩进显示在父事件下方
   - 通过缩进可以清楚地看到事件的层级关系

3. **滚动查看**：
   - 面板会自动滚动到最新事件
   - 可以手动滚动查看历史事件

## ⚠️ 注意事项

1. **事件实时更新**：
   - 事件通过 WebSocket 实时推送
   - 如果 WebSocket 连接断开，会在执行结束后从 API 获取所有事件

2. **事件顺序**：
   - 事件按时间戳顺序显示
   - 子事件会显示在父事件下方，即使时间戳稍早

3. **空状态**：
   - 如果没有任何编排事件，会显示："No orchestration events yet."
   - 这通常表示追踪钩子未正确集成或未触发

4. **事件数量**：
   - 复杂查询可能产生大量事件
   - 面板支持滚动查看所有事件

## 🛠️ 故障排查

如果 Orchestration Process 面板没有显示内容：

1. **检查追踪钩子是否集成**：
   - 确认 Agent、工具、提示词工程、上下文工程模块中是否调用了追踪方法

2. **检查 WebSocket 连接**：
   - 查看浏览器控制台是否有 WebSocket 连接错误
   - 确认后端是否正确推送编排事件

3. **检查 API 端点**：
   - 执行结束后，前端会尝试从 `/api/orchestration/{execution_id}` 获取事件
   - 确认该端点是否正常工作

4. **查看浏览器控制台**：
   - 打开浏览器开发者工具
   - 查看是否有 JavaScript 错误
   - 查看是否有编排事件相关的日志

## 📚 相关文档

- [系统使用指南](./system_usage_guide.md)
- [浏览器可视化指南](./browser_visualization_guide.md)
- [编排追踪实现文档](../implementation/orchestration_tracking_completion.md)

