# LangGraph 使用指南

## 一、安装和配置

### 1.1 安装 LangGraph

```bash
# 方式1：直接安装
pip install langgraph

# 方式2：使用项目提供的 requirements 文件
pip install -r requirements_langgraph.txt
```

### 1.2 配置 API Key

**重要**：确保在项目根目录的 `.env` 文件中配置了 API key：

```bash
# .env 文件示例
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_MODEL=deepseek-reasoner
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_FAST_MODEL=deepseek-chat
```

系统会在初始化时自动加载 `.env` 文件。如果遇到 "API key 未设置" 的错误，请检查：
1. `.env` 文件是否在项目根目录
2. `DEEPSEEK_API_KEY` 是否正确配置
3. API key 格式是否正确（应该是 `sk-` 开头）

### 1.3 验证安装

```python
try:
    from langgraph.graph import StateGraph
    print("✅ LangGraph 安装成功")
except ImportError:
    print("❌ LangGraph 未安装")
```

## 二、基本使用

### 2.1 启用 LangGraph（可选）

LangGraph 集成是可选的，默认使用传统流程。要启用 LangGraph，设置环境变量：

```bash
# Linux/Mac
export USE_LANGGRAPH=true

# Windows
set USE_LANGGRAPH=true

# 或在 Python 代码中
import os
os.environ['USE_LANGGRAPH'] = 'true'
```

### 2.2 基本使用示例

```python
import asyncio
from src.unified_research_system import create_unified_research_system, ResearchRequest

async def main():
    # 创建系统实例
    system = await create_unified_research_system()
    
    # 创建研究请求
    request = ResearchRequest(
        query="What is the capital of France?",
        context={}
    )
    
    # 执行研究
    result = await system.execute_research(request)
    
    # 查看结果
    print(f"Success: {result.success}")
    print(f"Answer: {result.answer}")
    print(f"Confidence: {result.confidence}")
    print(f"Execution Time: {result.execution_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
```

## 三、直接使用 LangGraph Agent

### 3.1 使用 LangGraph ReAct Agent

```python
import asyncio
from src.agents.langgraph_react_agent import LangGraphReActAgent

async def main():
    # 创建 LangGraph Agent
    agent = LangGraphReActAgent(agent_name="MyAgent")
    
    # 执行查询
    context = {
        "query": "What is the capital of France?",
        "context": {}
    }
    
    result = await agent.execute(context)
    
    print(f"Success: {result.success}")
    print(f"Answer: {result.data.get('answer', '') if result.data else 'N/A'}")
    print(f"Iterations: {result.metadata.get('iterations', 0) if result.metadata else 0}")

asyncio.run(main())
```

### 3.2 使用 LangGraph 推理工作流

```python
import asyncio
from src.core.reasoning.langgraph_reasoning_workflow import LangGraphReasoningWorkflow

async def main():
    # 创建工作流
    workflow = LangGraphReasoningWorkflow()
    
    # 执行推理
    query = "Who was the 15th first lady of the United States?"
    thread_id = "my_thread_123"
    
    result = await workflow.execute(query, thread_id=thread_id)
    
    print(f"Success: {result['success']}")
    print(f"Answer: {result.get('answer', '')}")
    print(f"Steps: {len(result.get('steps', []))}")

asyncio.run(main())
```

## 四、检查点和状态恢复

### 4.1 使用检查点

```python
import asyncio
from src.agents.langgraph_react_agent import LangGraphReActAgent

async def main():
    agent = LangGraphReActAgent(agent_name="CheckpointAgent")
    
    # 第一次执行（创建检查点）
    thread_id = "checkpoint_example_123"
    context = {"query": "What is the capital of France?"}
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # 执行工作流
    initial_state = {
        'query': context['query'],
        'thoughts': [],
        'observations': [],
        'actions': [],
        'task_complete': False,
        'iteration': 0,
        'max_iterations': 10,
        'error': None,
        'current_thought': None,
        'current_action': None,
        'current_observation': None
    }
    
    result = await agent.workflow.ainvoke(initial_state, config)
    print(f"First execution completed: {result.get('iteration', 0)} iterations")
    
    # 从检查点恢复（如果需要）
    # 注意：具体实现取决于 LangGraph 的 API

asyncio.run(main())
```

## 五、配置选项

### 5.1 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `USE_LANGGRAPH` | 是否启用 LangGraph | `false` |
| `USE_AGENT_LOOP` | 是否使用标准 Agent 循环 | `false` |

### 5.2 代码配置

```python
import os

# 启用 LangGraph
os.environ['USE_LANGGRAPH'] = 'true'

# 创建系统（会自动检测环境变量）
system = await create_unified_research_system()
```

## 六、运行示例

### 6.1 运行完整示例

```bash
# 运行 LangGraph 使用示例
python examples/langgraph_usage_example.py
```

### 6.2 示例输出

```
================================================================================
LangGraph 使用示例
================================================================================

这些示例演示了如何使用 LangGraph 框架实现可描述、可治理、
可复用、可恢复的 Agent 工作流。

注意：需要先安装 LangGraph:
  pip install langgraph

================================================================================
================================================================================
示例1: LangGraph ReAct Agent
================================================================================

查询: What is the capital of France?

执行中...

✅ 执行成功: True
答案: Paris
迭代次数: 3
置信度: 0.95
执行时间: 2.34秒
```

## 七、高级用法

### 7.1 自定义工作流

```python
from langgraph.graph import StateGraph, END
from src.agents.langgraph_react_agent import AgentState

# 创建自定义工作流
workflow = StateGraph(AgentState)

# 添加自定义节点
def custom_node(state: AgentState) -> AgentState:
    # 自定义逻辑
    return state

workflow.add_node("custom", custom_node)
workflow.set_entry_point("custom")
workflow.add_edge("custom", END)

# 编译工作流
compiled = workflow.compile()
```

### 7.2 可视化工作流

```python
# 获取图结构（Mermaid 格式）
graph = agent.workflow.get_graph()
mermaid_diagram = graph.draw_mermaid()

# 保存为文件
with open("workflow_diagram.md", "w") as f:
    f.write(f"```mermaid\n{mermaid_diagram}\n```")
```

### 7.3 监控和调试

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 执行时会输出详细的节点执行信息
result = await agent.execute(context)
```

## 八、故障排除

### 8.1 常见问题

**问题1：LangGraph 未安装**

```
ImportError: LangGraph is required. Install with: pip install langgraph
```

**解决方案：**
```bash
pip install langgraph
```

**问题2：环境变量未生效**

确保在创建系统实例之前设置环境变量：

```python
import os
os.environ['USE_LANGGRAPH'] = 'true'  # 必须在创建系统之前

system = await create_unified_research_system()
```

**问题3：检查点恢复失败**

检查点功能需要正确配置检查点存储：

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

# 开发环境：使用内存
checkpointer = MemorySaver()

# 生产环境：使用 SQLite
checkpointer = SqliteSaver.from_conn_string(":memory:")
```

## 九、最佳实践

1. **开发环境**：使用 `MemorySaver` 进行快速测试
2. **生产环境**：使用 `SqliteSaver` 或 `PostgresSaver` 持久化状态
3. **错误处理**：始终检查 `result.success` 并处理错误
4. **性能监控**：记录执行时间和迭代次数
5. **状态管理**：合理设置 `max_iterations` 避免无限循环

## 十、更多资源

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [迁移方案](./architecture/langgraph_migration_plan.md)
- [集成指南](./architecture/langgraph_integration_guide.md)
- [对比分析](./architecture/langgraph_comparison.md)

