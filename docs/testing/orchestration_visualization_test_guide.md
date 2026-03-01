# 编排过程可视化功能测试指南

## 概述

本文档说明如何测试编排过程可视化功能，验证 Agent、工具、提示词工程、上下文工程的追踪是否正常工作。

## 测试准备

### 1. 环境要求

- Python 3.8+
- 已安装所有依赖（`pip install -r requirements.txt`）
- 已安装 LangGraph（`pip install langgraph`）
- 已安装可视化依赖（`pip install fastapi uvicorn websockets`）

### 2. 环境变量配置

确保 `.env` 文件中包含：

```bash
# 启用浏览器可视化
ENABLE_BROWSER_VISUALIZATION=true

# 启用统一工作流
ENABLE_UNIFIED_WORKFLOW=true

# 可视化服务器端口
VISUALIZATION_PORT=8080

# LLM 配置
DEEPSEEK_API_KEY=your_api_key
LLM_PROVIDER=deepseek
```

## 测试步骤

### 步骤1：启动可视化服务器

在一个终端中运行：

```bash
python examples/start_visualization_server.py
```

应该看到：

```
🌐 LangGraph Workflow Visualizer
================================================================================

1. 初始化 UnifiedResearchSystem...
   ✅ 系统初始化完成
   ✅ 统一工作流已初始化

2. 启动可视化服务器...
   端口: 8080
   访问地址: http://localhost:8080

提示:
- 在浏览器中打开上述地址即可查看可视化界面
- 按 Ctrl+C 停止服务器
```

### 步骤2：运行测试脚本

在另一个终端中运行：

```bash
python examples/test_orchestration_visualization.py
```

测试脚本会执行以下测试：

1. **基础编排追踪**：测试系统是否能追踪基本事件
2. **Agent 执行追踪**：测试 Agent 开始、思考、规划、行动、观察的追踪
3. **工具调用追踪**：测试工具开始和结束的追踪
4. **提示词工程追踪**：测试提示词生成和编排的追踪
5. **上下文工程追踪**：测试上下文增强、更新、合并的追踪
6. **完整工作流追踪**：测试完整查询执行的所有事件追踪

### 步骤3：在浏览器中查看可视化

1. 打开浏览器访问：`http://localhost:8080`
2. 在查询输入框中输入一个查询，例如：`Who was the 15th first lady of the United States?`
3. 点击"执行查询"按钮
4. 查看"编排过程"面板，应该能看到：
   - 🤖 Agent 开始/结束事件
   - 💭 Agent 思考事件
   - 📋 Agent 规划事件
   - ⚡ Agent 行动事件
   - 👁️ Agent 观察事件
   - 🔧 工具开始/结束事件
   - 📝 提示词生成事件
   - 🎼 提示词编排事件
   - 🔍 上下文增强事件
   - 🔄 上下文更新事件
   - 🔗 上下文合并事件

## 预期结果

### 1. 控制台输出

测试脚本应该输出：

```
================================================================================
测试1: 基础编排追踪
================================================================================
执行查询: Who was the 15th first lady of the United States?
查询完成: success=True
答案长度: XXX
追踪到 XX 个事件
事件类型统计:
  agent_start: X
  agent_think: X
  agent_plan: X
  agent_act: X
  agent_observe: X
  tool_start: X
  tool_end: X
  prompt_generate: X
  prompt_orchestrate: X
  context_enhance: X
  context_update: X
  context_merge: X
```

### 2. 浏览器可视化界面

在浏览器中应该看到：

1. **工作流图**：显示 LangGraph 工作流结构
2. **节点状态**：显示各个节点的执行状态
3. **编排过程面板**：显示所有编排事件的实时流
   - 事件按时间顺序显示
   - 不同组件类型用不同颜色标识
   - 支持层级显示（子事件缩进显示）
   - 可以展开查看事件详情

### 3. 事件层级结构

编排事件应该形成层级结构：

```
🤖 Agent 开始 (react_agent)
  ├─ 💭 Agent 思考
  ├─ 📋 Agent 规划
  ├─ ⚡ Agent 行动
  │   └─ 🔧 工具开始 (rag)
  │       └─ ✅ 工具结束 (rag)
  └─ 👁️ Agent 观察
```

## 验证检查清单

- [ ] 可视化服务器能正常启动
- [ ] 测试脚本能正常运行
- [ ] Agent 事件能正确追踪（开始、思考、规划、行动、观察、结束）
- [ ] 工具事件能正确追踪（开始、结束）
- [ ] 提示词工程事件能正确追踪（生成、编排）
- [ ] 上下文工程事件能正确追踪（增强、更新、合并）
- [ ] 事件能实时推送到浏览器
- [ ] 浏览器界面能正确显示事件
- [ ] 事件层级关系正确（子事件正确缩进）
- [ ] 不同组件类型用不同颜色标识
- [ ] 可以展开查看事件详情

## 常见问题

### 问题1：追踪器未初始化

**症状**：测试脚本输出 "⚠️ 追踪器未初始化"

**解决方案**：
1. 确保 `ENABLE_BROWSER_VISUALIZATION=true`
2. 检查 `UnifiedResearchSystem` 是否正确初始化追踪器

### 问题2：浏览器看不到编排事件

**症状**：浏览器界面显示 "No orchestration events yet"

**解决方案**：
1. 检查 WebSocket 连接是否正常
2. 检查浏览器控制台是否有错误
3. 确保 `_execute_system_query` 方法正确设置了回调

### 问题3：事件不显示层级关系

**症状**：所有事件都是平级显示，没有缩进

**解决方案**：
1. 检查 `parent_event_id` 是否正确传递
2. 检查前端 JavaScript 是否正确处理 `parent_event_id`

## 测试脚本说明

测试脚本 `examples/test_orchestration_visualization.py` 包含以下测试函数：

1. `test_basic_orchestration()`：基础编排追踪测试
2. `test_agent_tracking()`：Agent 执行追踪测试
3. `test_tool_tracking()`：工具调用追踪测试
4. `test_prompt_tracking()`：提示词工程追踪测试
5. `test_context_tracking()`：上下文工程追踪测试
6. `test_full_workflow()`：完整工作流追踪测试

每个测试函数都会：
- 初始化系统或组件
- 执行操作
- 检查追踪事件
- 输出统计信息

## 下一步

测试通过后，可以：

1. 继续实施阶段1的工作（优化节点使用系统实例的方式）
2. 进行性能测试
3. 优化可视化界面显示效果
4. 添加更多事件类型和详细信息

## 相关文档

- [编排过程可视化指南](../implementation/orchestration_visualization_guide.md)
- [智能体单独调试指南](../usage/agent_debugging_guide.md)
- [LangGraph 架构重构方案](../architecture/langgraph_architectural_refactoring.md)

