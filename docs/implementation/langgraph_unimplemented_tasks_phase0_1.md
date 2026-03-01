# LangGraph 架构重构未实施任务 - 阶段0和阶段1

## 阶段0：可视化系统 MVP（进行中，85%完成）

### 0.4 编排过程可视化集成（待完成）

#### 已完成的追踪钩子
根据代码检查，以下位置已添加追踪钩子：
- ✅ `src/core/reasoning/context_manager.py` - 上下文工程追踪
- ✅ `src/utils/enhanced_context_engineering.py` - 上下文增强追踪
- ✅ `src/utils/prompt_orchestrator.py` - 提示词编排追踪
- ✅ `src/utils/prompt_engine.py` - 提示词工程追踪
- ✅ `src/agents/expert_agent.py` - Expert Agent 追踪
- ✅ `src/agents/react_agent.py` - ReAct Agent 追踪
- ✅ `src/unified_research_system.py` - 系统级追踪器传递

#### 待完善的任务

**1. Agent 执行追踪完善**
- [ ] 检查 `src/agents/langgraph_react_agent.py` 中的追踪钩子是否完整
- [ ] 确保所有 Agent 的 `_think`, `_plan`, `_act`, `_observe` 方法都有追踪
- [ ] 验证 Agent 追踪事件的层级关系是否正确

**2. 工具调用追踪完善**
- [ ] 检查 `src/agents/tools/base_tool.py` 中的追踪钩子
- [ ] 确保所有具体工具实现都有追踪（如 `KnowledgeRetrievalTool`, `ReasoningTool` 等）
- [ ] 验证工具调用的开始和结束事件是否正确记录

**3. 提示词工程追踪完善**
- [ ] 检查 `src/utils/unified_prompt_manager.py` 中的追踪钩子
- [ ] 确保提示词生成、优化、编排过程都有追踪
- [ ] 验证提示词工程事件的详细信息是否完整

**4. 上下文工程追踪完善**
- [ ] 检查 `src/utils/unified_context_engineering_center.py` 中的追踪钩子
- [ ] 确保上下文增强、更新、合并过程都有追踪
- [ ] 验证上下文工程事件的层级关系

**5. 系统级追踪器传递**
- [ ] 验证 `UnifiedResearchSystem.execute_research` 中追踪器传递是否完整
- [ ] 确保所有子组件都能正确访问追踪器
- [ ] 检查追踪器在异步执行中的传递是否正确

**6. 测试和验证**
- [ ] 创建端到端测试脚本验证编排过程可视化
- [ ] 测试所有追踪钩子是否正常工作
- [ ] 验证前端可视化界面能正确显示编排过程
- [ ] 检查事件树结构是否正确

## 阶段1：工作流 MVP（进行中，70%完成）

### 1.1 状态定义（✅ 已完成）
- ✅ 定义简化的 `ResearchSystemState`（MVP版本）
- ✅ 包含核心字段

### 1.2 核心节点实现（✅ 部分完成，⏳ 待优化）

#### 已完成的节点
- ✅ `entry_node` - 系统入口，初始化状态
- ✅ `route_query_node` - 分析查询，决定路由路径
- ✅ `simple_query_node` - 直接检索知识库
- ✅ `complex_query_node` - 使用多步骤推理
- ✅ `synthesize_node` - 综合证据和答案
- ✅ `format_node` - 格式化最终结果

#### 待优化的任务

**1. 优化 `_complex_query_node` 使用系统实例的方式**
- [ ] 检查当前实现是否与 `_simple_query_node` 保持一致
- [ ] 确保优先使用 `system.execute_research` 方法
- [ ] 优化错误处理和降级策略
- [ ] 添加详细的日志记录

**2. 完善节点错误处理**
- [ ] 为所有节点添加统一的错误处理机制
- [ ] 实现错误分类（可重试错误、致命错误等）
- [ ] 添加错误恢复策略
- [ ] 确保错误信息正确传递到状态中

**3. 节点使用系统实例的方式**
- [ ] 检查所有节点是否正确使用传入的 `system` 实例
- [ ] 确保节点间的依赖关系清晰
- [ ] 优化节点间的数据传递
- [ ] 减少不必要的系统调用

### 1.3 条件路由实现（✅ 已完成）
- ✅ 实现 `_route_decision` 函数
- ✅ 根据复杂度分数路由到简单或复杂查询路径
- ✅ 测试路由逻辑

### 1.4 工作流构建（✅ 已完成）
- ✅ 构建 MVP 工作流图
- ✅ 定义节点和边
- ✅ 设置入口点和条件路由
- ✅ 集成基础检查点机制（MemorySaver）

### 1.5 集成和测试（⏳ 进行中）

**待完成的任务：**

**1. 性能测试**
- [ ] 测试简单查询路径的性能
- [ ] 测试复杂查询路径的性能
- [ ] 测试工作流的整体性能
- [ ] 识别性能瓶颈
- [ ] 优化慢速节点

**2. 更新可视化系统以显示新工作流**
- [ ] 更新工作流图的可视化
- [ ] 添加新节点的可视化支持
- [ ] 更新状态可视化
- [ ] 测试可视化界面的响应性

**3. 端到端测试**
- [ ] 测试完整工作流执行
- [ ] 测试不同复杂度的查询
- [ ] 测试错误场景
- [ ] 测试状态恢复功能

**4. 文档更新**
- [ ] 更新工作流使用文档
- [ ] 添加节点说明文档
- [ ] 更新架构文档

## 下一步行动

### 立即执行（本周）
1. 完成阶段0.4的追踪钩子完善和测试
2. 优化 `_complex_query_node` 的实现
3. 完善节点错误处理
4. 进行基础性能测试

### 短期目标（2周内）
1. 完成阶段1的所有测试任务
2. 更新可视化系统
3. 准备进入阶段2

## 相关文件

### 核心实现文件
- `src/core/langgraph_unified_workflow.py` - 主工作流实现
- `src/visualization/orchestration_tracker.py` - 编排追踪器
- `src/visualization/browser_server.py` - 可视化服务器

### 需要检查的文件
- `src/agents/langgraph_react_agent.py` - LangGraph ReAct Agent
- `src/agents/tools/base_tool.py` - 工具基类
- `src/utils/unified_prompt_manager.py` - 提示词管理器
- `src/utils/unified_context_engineering_center.py` - 上下文工程中心

