# LangGraph 故障排除指南

## 问题诊断

### 问题1：LangGraph 已启用但未使用

**症状**：
- 日志显示 "✅ LangGraph 已启用"
- 但系统仍使用智能协调层或标准循环路径
- 没有看到 "🚀 使用LangGraph ReAct Agent执行查询" 的日志

**可能原因**：
1. Entry Router 未正确初始化
2. Entry Router 路由到其他路径（如 `mas` 或 `standard_loop`）
3. LangGraph Agent 初始化失败

**诊断步骤**：

1. **检查 Entry Router 初始化**：
   ```python
   # 在代码中添加调试日志
   logger.info(f"Entry Router: {system._entry_router is not None}")
   logger.info(f"LangGraph启用: {system._use_langgraph}")
   logger.info(f"LangGraph Agent: {system._langgraph_react_agent is not None}")
   ```

2. **检查路由决策**：
   查看日志中是否有 "✅ [Entry Router] 路由决策" 的输出

3. **检查 LangGraph Agent 初始化**：
   查看日志中是否有 "✅ LangGraph Agent初始化成功"

**解决方案**：

1. **确保 LangGraph 正确安装**：
   ```bash
   pip install langgraph
   ```

2. **确保环境变量正确设置**：
   ```bash
   export USE_LANGGRAPH=true
   ```

3. **检查初始化顺序**：
   - LangGraph Agent 必须在 Entry Router 之前初始化
   - Entry Router 需要知道 LangGraph 的状态

### 问题2：Entry Router 未初始化

**症状**：
- 日志显示 "⚠️ Entry Router未初始化，直接使用智能协调层（向后兼容）"
- 系统直接使用智能协调层

**可能原因**：
1. Entry Router 初始化失败
2. 初始化顺序问题

**解决方案**：
1. 检查初始化日志，查找 Entry Router 初始化错误
2. 确保所有依赖项都已正确安装

### 问题3：路由到错误路径

**症状**：
- Entry Router 路由到 `standard_loop` 或 `mas` 而不是 `react_agent`
- 即使启用了 LangGraph

**解决方案**：
- 检查 Entry Router 的路由逻辑
- 确保 `use_langgraph` 参数正确传递

## 调试技巧

### 1. 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 检查系统状态

```python
system = await create_unified_research_system()
print(f"Entry Router: {system._entry_router is not None}")
print(f"LangGraph启用: {system._use_langgraph}")
print(f"LangGraph Agent: {system._langgraph_react_agent is not None}")
```

### 3. 强制使用 LangGraph

如果 Entry Router 路由不正确，可以临时修改代码强制使用 LangGraph：

```python
# 在 execute_research 方法中，临时强制使用 LangGraph
if self._use_langgraph and self._langgraph_react_agent:
    result = await self._execute_with_langgraph_agent(request)
    return result
```

## 常见错误

### 错误1：ImportError: LangGraph is required

**原因**：LangGraph 未安装

**解决**：
```bash
pip install langgraph
```

### 错误2：LangGraph Agent not initialized

**原因**：LangGraph Agent 初始化失败

**解决**：
1. 检查 LangGraph 是否正确安装
2. 检查初始化日志中的错误信息
3. 确保所有依赖项都已安装

### 错误3：Entry Router 路由到 standard_loop

**原因**：简单查询被路由到快速路径

**解决**：
- 这是正常行为（简单查询使用快速路径）
- 如果要测试 LangGraph，可以使用更复杂的查询
- 或者修改 Entry Router 逻辑，强制使用 LangGraph

## 验证 LangGraph 是否工作

运行示例并检查日志：

```bash
python examples/simple_langgraph_example.py
```

应该看到：
1. "✅ LangGraph 已启用"
2. "✅ [Entry Router] 路由决策: ReAct Agent (LangGraph)"
3. "🚀 使用LangGraph ReAct Agent执行查询"

如果没有看到这些日志，说明 LangGraph 未正确使用。

