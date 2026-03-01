# LangGraph 集成指南

## 一、安装依赖

```bash
# 安装 LangGraph
pip install langgraph

# 或使用 requirements 文件
pip install -r requirements_langgraph.txt
```

## 二、基本使用

### 2.1 使用 LangGraph ReAct Agent

```python
from src.agents.langgraph_react_agent import LangGraphReActAgent

# 创建 Agent
agent = LangGraphReActAgent(agent_name="MyReActAgent")

# 执行查询
context = {"query": "What is the capital of France?"}
result = await agent.execute(context)

print(f"Answer: {result.data['answer']}")
print(f"Iterations: {result.metadata['iterations']}")
```

### 2.2 使用 LangGraph 推理工作流

```python
from src.core.reasoning.langgraph_reasoning_workflow import LangGraphReasoningWorkflow

# 创建工作流
workflow = LangGraphReasoningWorkflow(reasoning_engine=your_reasoning_engine)

# 执行推理
result = await workflow.execute(
    query="If my future wife has the same first name as the 15th first lady...",
    thread_id="my_thread_123"
)

print(f"Answer: {result['answer']}")
print(f"Steps: {len(result['steps'])}")
```

## 三、检查点机制

### 3.1 使用内存检查点（开发环境）

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
workflow = workflow.compile(checkpointer=checkpointer)
```

### 3.2 使用 SQLite 检查点（生产环境）

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
workflow = workflow.compile(checkpointer=checkpointer)
```

### 3.3 从检查点恢复

```python
# 执行时指定 thread_id
config = {"configurable": {"thread_id": "my_thread_123"}}
result = await workflow.ainvoke(initial_state, config)

# 后续可以从同一个 thread_id 恢复
# LangGraph 会自动从检查点恢复状态
```

## 四、可视化工作流

### 4.1 使用 LangGraph Studio（推荐）

```bash
# 安装 LangGraph Studio
pip install langgraph-studio

# 启动 Studio
langgraph-studio
```

### 4.2 导出工作流图

```python
# 导出为 Mermaid 格式
mermaid_graph = workflow.get_graph().draw_mermaid()

# 保存到文件
with open("workflow.mmd", "w") as f:
    f.write(mermaid_graph)
```

## 五、集成到现有系统

### 5.1 在 UnifiedResearchSystem 中使用

```python
# 在 UnifiedResearchSystem.__init__ 中
from src.agents.langgraph_react_agent import LangGraphReActAgent

# 创建 LangGraph ReAct Agent
self._langgraph_react_agent = LangGraphReActAgent(
    agent_name="LangGraphReActAgent"
)

# 在 _execute_research_agent_loop 中使用
async def _execute_research_agent_loop(self, request, start_time):
    # 使用 LangGraph Agent
    react_context = {
        "query": request.query,
        "observations": self.observations,
        "thoughts": self.thoughts
    }
    
    agent_result = await self._langgraph_react_agent.execute(react_context)
    
    # 转换为 ResearchResult
    return self._convert_to_research_result(agent_result, request)
```

### 5.2 并行运行（对比测试）

```python
# 同时运行原有 Agent 和 LangGraph Agent
original_result = await self._react_agent.execute(context)
langgraph_result = await self._langgraph_react_agent.execute(context)

# 对比结果
compare_results(original_result, langgraph_result)
```

## 六、最佳实践

### 6.1 状态设计

- 使用 TypedDict 定义状态，确保类型安全
- 状态应该是不可变的，通过返回新状态来更新
- 使用 Annotated 添加元数据

### 6.2 节点设计

- 每个节点应该是独立的、可测试的
- 节点应该处理自己的错误
- 使用日志记录节点执行情况

### 6.3 条件路由

- 条件函数应该简单、清晰
- 使用 Literal 类型确保类型安全
- 处理所有可能的状态

### 6.4 检查点配置

- 开发环境使用 MemorySaver
- 生产环境使用 SQLiteSaver 或 PostgreSQL
- 定期清理旧的检查点

## 七、故障排除

### 7.1 常见问题

**问题1：导入错误**
```python
# 确保安装了 LangGraph
pip install langgraph
```

**问题2：检查点不工作**
```python
# 确保在 compile 时传入了 checkpointer
workflow = workflow.compile(checkpointer=checkpointer)
```

**问题3：状态更新不生效**
```python
# 确保返回新状态，而不是修改原状态
def my_node(state):
    new_state = state.copy()
    new_state['key'] = 'value'
    return new_state
```

## 八、性能优化

### 8.1 节点并行执行

```python
# LangGraph 支持节点并行执行
# 在图中定义多个入口点，它们会并行执行
workflow.add_edge("node1", "node3")
workflow.add_edge("node2", "node3")
# node1 和 node2 会并行执行
```

### 8.2 检查点频率

```python
# 可以配置检查点保存频率
config = {
    "configurable": {
        "thread_id": "my_thread",
        "checkpoint_ns": "my_namespace"
    },
    "checkpoint_at": ["node1", "node2"]  # 只在特定节点保存检查点
}
```

## 九、监控和调试

### 9.1 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 9.2 追踪执行路径

```python
# LangGraph 会自动记录执行路径
# 可以通过检查点查看执行历史
checkpoint = await checkpointer.get({"configurable": {"thread_id": "my_thread"}})
print(checkpoint['metadata']['execution_path'])
```

## 十、迁移检查清单

- [ ] 安装 LangGraph 依赖
- [ ] 创建 LangGraph 版本的 Agent
- [ ] 编写单元测试
- [ ] 性能对比测试
- [ ] 集成到现有系统
- [ ] 端到端测试
- [ ] 文档更新
- [ ] 团队培训

