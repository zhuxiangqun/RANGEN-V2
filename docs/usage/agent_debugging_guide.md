# 智能体单独调试指南

> 基于 LangGraph 框架的智能体调试方法

## 一、为什么可以单独调试？

### 1.1 节点化设计

在 LangGraph 框架中，**每个智能体（Agent）都是一个独立的节点**，这意味着：

- ✅ **节点是独立的函数**：每个节点都是一个 `async` 函数，可以独立调用
- ✅ **状态输入输出**：节点接收状态作为输入，返回修改后的状态
- ✅ **无副作用**：节点之间通过状态传递数据，不直接依赖其他节点
- ✅ **可测试性**：每个节点都可以独立测试和调试

### 1.2 实际例子

在 `src/core/langgraph_unified_workflow.py` 中，Agent 节点是这样定义的：

```python
async def _agent_think_node(self, state: ResearchSystemState) -> ResearchSystemState:
    """Agent 思考节点 - 可以独立调试"""
    # 这个节点可以独立调用和测试
    query = state.get('query', '')
    # ... Agent 思考逻辑 ...
    return state
```

## 二、单独调试方法

### 2.1 方法1：直接调用节点函数

**最简单的方法**：直接调用节点函数，传入测试状态

```python
import asyncio
from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow

async def test_agent_think_node():
    """单独测试 Agent 思考节点"""
    # 1. 创建工作流实例
    workflow = UnifiedResearchWorkflow(system=None)
    
    # 2. 准备测试状态
    test_state = {
        'query': '测试查询',
        'context': {},
        'agent_thoughts': [],
        'agent_actions': [],
        'agent_observations': []
    }
    
    # 3. 直接调用节点函数
    result_state = await workflow._agent_think_node(test_state)
    
    # 4. 检查结果
    print(f"思考结果: {result_state.get('agent_thoughts')}")
    assert len(result_state['agent_thoughts']) > 0
    
    return result_state

# 运行测试
asyncio.run(test_agent_think_node())
```

### 2.2 方法2：使用工作流的单节点执行

LangGraph 支持执行单个节点：

```python
from langgraph.graph import StateGraph

async def test_single_node():
    """测试单个节点执行"""
    workflow = UnifiedResearchWorkflow(system=None)
    
    # 准备初始状态
    initial_state = {
        'query': '测试查询',
        'context': {},
        'agent_thoughts': []
    }
    
    # 执行单个节点（不执行整个工作流）
    # 注意：这需要 LangGraph 的支持
    result = await workflow.workflow.nodes['agent_think'].ainvoke(initial_state)
    
    print(f"节点执行结果: {result}")
    return result
```

### 2.3 方法3：使用 Mock 和单元测试

**推荐方法**：使用 pytest 和 Mock 进行单元测试

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow

@pytest.mark.asyncio
async def test_agent_think_node_with_mock():
    """使用 Mock 测试 Agent 思考节点"""
    # 1. 创建 Mock 系统
    mock_system = Mock()
    mock_llm = AsyncMock()
    mock_llm.call.return_value = "这是一个思考结果"
    
    # 2. 创建工作流（注入 Mock）
    workflow = UnifiedResearchWorkflow(system=mock_system)
    
    # 3. Mock LLM 调用
    with patch.object(workflow, '_call_llm', new=mock_llm):
        # 4. 准备测试状态
        test_state = {
            'query': '测试查询',
            'context': {},
            'agent_thoughts': []
        }
        
        # 5. 执行节点
        result = await workflow._agent_think_node(test_state)
        
        # 6. 验证结果
        assert 'agent_thoughts' in result
        assert len(result['agent_thoughts']) > 0
        assert mock_llm.call.called  # 验证 LLM 被调用
```

### 2.4 方法4：使用检查点调试

LangGraph 的检查点机制支持从任意节点恢复执行：

```python
async def debug_from_checkpoint():
    """从检查点调试特定节点"""
    workflow = UnifiedResearchWorkflow(system=None)
    
    # 1. 执行到某个节点并保存检查点
    initial_state = {'query': '测试查询', 'context': {}}
    
    # 执行到 agent_think 节点
    config = {"configurable": {"thread_id": "debug_thread_1"}}
    
    # 执行到 agent_think 节点
    async for event in workflow.workflow.astream(initial_state, config=config):
        for node_name, node_state in event.items():
            if node_name == 'agent_think':
                # 2. 在这里可以检查状态
                print(f"Agent Think 节点状态: {node_state}")
                
                # 3. 可以修改状态后继续执行
                # 或者停止在这里进行调试
                break
```

### 2.5 方法5：使用可视化系统调试

**最直观的方法**：使用浏览器可视化系统实时查看节点执行

```python
# 1. 启动可视化服务器
python examples/start_visualization_server.py

# 2. 在浏览器中打开 http://localhost:8080

# 3. 执行查询，实时查看：
#    - Agent 节点的执行过程
#    - 输入状态和输出状态
#    - 执行时间
#    - 错误信息（如果有）
```

## 三、调试特定 Agent 节点

### 3.1 Agent Think 节点调试

```python
async def debug_agent_think():
    """调试 Agent 思考节点"""
    workflow = UnifiedResearchWorkflow(system=None)
    
    test_state = {
        'query': '谁是美国第15任第一夫人？',
        'context': {},
        'agent_thoughts': [],
        'agent_actions': [],
        'agent_observations': []
    }
    
    # 直接调用节点
    result = await workflow._agent_think_node(test_state)
    
    # 检查思考结果
    print(f"思考内容: {result.get('agent_thoughts', [])}")
    
    # 可以设置断点在这里检查状态
    import pdb; pdb.set_trace()
    
    return result
```

### 3.2 Agent Plan 节点调试

```python
async def debug_agent_plan():
    """调试 Agent 规划节点"""
    workflow = UnifiedResearchWorkflow(system=None)
    
    test_state = {
        'query': '测试查询',
        'agent_thoughts': ['需要检索知识库'],
        'agent_actions': [],
        'context': {}
    }
    
    result = await workflow._agent_plan_node(test_state)
    
    print(f"规划的行动: {result.get('agent_actions', [])}")
    return result
```

### 3.3 Agent Act 节点调试

```python
async def debug_agent_act():
    """调试 Agent 行动节点"""
    workflow = UnifiedResearchWorkflow(system=None)
    
    test_state = {
        'query': '测试查询',
        'agent_actions': [{
            'tool_name': 'knowledge_retrieval',
            'params': {'query': '测试查询'}
        }],
        'agent_observations': []
    }
    
    # Mock 工具调用
    with patch('src.agents.tools.rag_tool.RAGTool.call') as mock_tool:
        mock_tool.return_value = Mock(success=True, data='测试结果')
        
        result = await workflow._agent_act_node(test_state)
        
        print(f"观察结果: {result.get('agent_observations', [])}")
        return result
```

### 3.4 Agent Observe 节点调试

```python
async def debug_agent_observe():
    """调试 Agent 观察节点"""
    workflow = UnifiedResearchWorkflow(system=None)
    
    test_state = {
        'query': '测试查询',
        'agent_observations': [{
            'tool_name': 'knowledge_retrieval',
            'result': '测试结果',
            'success': True
        }],
        'agent_thoughts': []
    }
    
    result = await workflow._agent_observe_node(test_state)
    
    print(f"新的思考: {result.get('agent_thoughts', [])}")
    return result
```

## 四、调试工具和技巧

### 4.1 使用 Python 调试器

```python
import pdb

async def debug_with_pdb():
    """使用 pdb 调试"""
    workflow = UnifiedResearchWorkflow(system=None)
    
    test_state = {'query': '测试查询', 'context': {}}
    
    # 设置断点
    pdb.set_trace()
    
    result = await workflow._agent_think_node(test_state)
    
    # 在这里可以：
    # - 检查变量：print(state)
    # - 单步执行：n (next), s (step)
    # - 查看调用栈：bt (backtrace)
    # - 修改变量：state['query'] = '新查询'
    
    return result
```

### 4.2 使用日志调试

```python
import logging

# 配置详细日志
logging.basicConfig(level=logging.DEBUG)

async def debug_with_logging():
    """使用日志调试"""
    workflow = UnifiedResearchWorkflow(system=None)
    
    # 节点内部已经有详细的日志
    # 只需要设置日志级别为 DEBUG
    test_state = {'query': '测试查询', 'context': {}}
    result = await workflow._agent_think_node(test_state)
    
    # 查看日志输出
    return result
```

### 4.3 使用编排追踪器调试

```python
from src.visualization.orchestration_tracker import get_orchestration_tracker

async def debug_with_tracker():
    """使用编排追踪器调试"""
    tracker = get_orchestration_tracker()
    tracker.start_execution("debug_session")
    
    workflow = UnifiedResearchWorkflow(system=None)
    
    # 设置追踪器
    workflow._orchestration_tracker = tracker
    
    test_state = {'query': '测试查询', 'context': {}}
    
    # 执行节点（会自动追踪）
    result = await workflow._agent_think_node(test_state)
    
    # 查看追踪事件
    events = tracker.get_events_by_component('agent_think')
    for event in events:
        print(f"事件: {event.event_type}, 数据: {event.data}")
    
    return result
```

## 五、完整调试示例

### 5.1 调试 Agent 完整循环

```python
import asyncio
from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow

async def debug_agent_full_cycle():
    """调试 Agent 完整循环（Think → Plan → Act → Observe）"""
    workflow = UnifiedResearchWorkflow(system=None)
    
    # 初始状态
    state = {
        'query': '谁是美国第15任第一夫人？',
        'context': {},
        'agent_thoughts': [],
        'agent_actions': [],
        'agent_observations': [],
        'iteration': 0,
        'max_iterations': 5,
        'task_complete': False
    }
    
    # 执行一个完整循环
    print("=== Step 1: Think ===")
    state = await workflow._agent_think_node(state)
    print(f"思考: {state.get('agent_thoughts', [])}")
    
    print("\n=== Step 2: Plan ===")
    state = await workflow._agent_plan_node(state)
    print(f"规划: {state.get('agent_actions', [])}")
    
    print("\n=== Step 3: Act ===")
    # 注意：这里需要 Mock 工具调用
    with patch('src.agents.tools.rag_tool.RAGTool.call') as mock_tool:
        mock_tool.return_value = Mock(success=True, data='测试结果')
        state = await workflow._agent_act_node(state)
        print(f"观察: {state.get('agent_observations', [])}")
    
    print("\n=== Step 4: Observe ===")
    state = await workflow._agent_observe_node(state)
    print(f"新思考: {state.get('agent_thoughts', [])}")
    
    return state

# 运行
asyncio.run(debug_agent_full_cycle())
```

### 5.2 调试特定场景

```python
async def debug_specific_scenario():
    """调试特定场景"""
    workflow = UnifiedResearchWorkflow(system=None)
    
    # 场景：Agent 思考失败
    state = {
        'query': '测试查询',
        'context': {},
        'agent_thoughts': []
    }
    
    # Mock LLM 调用失败
    with patch.object(workflow, '_call_llm', side_effect=Exception("LLM 调用失败")):
        try:
            result = await workflow._agent_think_node(state)
        except Exception as e:
            print(f"捕获错误: {e}")
            # 检查错误处理逻辑
            assert 'error' in state or 'error' in result
```

## 六、最佳实践

### 6.1 调试原则

1. **从简单到复杂**：
   - 先测试单个节点
   - 再测试节点组合
   - 最后测试完整工作流

2. **使用 Mock**：
   - Mock 外部依赖（LLM、工具、数据库）
   - 专注于测试节点逻辑

3. **检查状态**：
   - 验证输入状态
   - 验证输出状态
   - 验证状态转换

4. **使用可视化**：
   - 利用浏览器可视化系统
   - 实时查看节点执行
   - 检查状态变化

### 6.2 调试检查清单

- [ ] 节点函数可以独立调用
- [ ] 输入状态格式正确
- [ ] 输出状态格式正确
- [ ] 错误处理正确
- [ ] 日志输出清晰
- [ ] 性能符合预期
- [ ] 与工作流集成正常

## 七、总结

**使用 LangGraph 框架后，智能体完全可以单独调试**，因为：

1. ✅ **节点化设计**：每个 Agent 节点都是独立函数
2. ✅ **状态驱动**：通过状态传递数据，易于测试
3. ✅ **支持 Mock**：可以 Mock 外部依赖
4. ✅ **可视化支持**：浏览器可视化系统实时查看
5. ✅ **检查点机制**：可以从任意节点恢复执行
6. ✅ **单元测试**：每个节点都可以独立测试

这使得调试变得**更容易、更清晰、更高效**！

