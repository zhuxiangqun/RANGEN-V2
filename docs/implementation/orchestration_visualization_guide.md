# 编排过程可视化指南

## 概述

系统现在支持可视化显示 Agent、工具、提示词工程、上下文工程的编排过程。这需要在关键位置添加追踪钩子。

## 已实现的功能

### 1. 编排追踪器 (`src/visualization/orchestration_tracker.py`)

- ✅ 支持追踪 Agent 执行（开始、结束、思考、规划、行动、观察）
- ✅ 支持追踪工具调用（开始、结束）
- ✅ 支持追踪提示词工程（生成、优化、编排）
- ✅ 支持追踪上下文工程（增强、更新、合并）
- ✅ 支持事件树结构（层级关系）
- ✅ 支持实时推送事件到前端

### 2. 可视化服务器集成

- ✅ 在 `BrowserVisualizationServer` 中集成编排追踪器
- ✅ 添加 API 端点：`/api/orchestration/{execution_id}`
- ✅ 添加 WebSocket 实时推送编排事件

## 需要添加追踪钩子的位置

### 1. Agent 执行追踪

在以下文件中添加追踪钩子：

#### `src/agents/react_agent.py`

```python
# 在 _think 方法中
async def _think(self, query: str, context: Dict[str, Any]) -> str:
    # 获取编排追踪器
    tracker = getattr(self, '_orchestration_tracker', None)
    if tracker:
        parent_event_id = tracker.track_agent_start(self.agent_id, "react_agent", context)
    
    try:
        thought = await self._call_llm(...)
        
        # 追踪思考
        if tracker:
            tracker.track_agent_think(self.agent_id, thought, parent_event_id)
        
        return thought
    finally:
        if tracker:
            tracker.track_agent_end(self.agent_id)

# 在 _plan_action 方法中
async def _plan_action(self, thought: str, query: str, dependencies: Dict) -> Optional[Action]:
    tracker = getattr(self, '_orchestration_tracker', None)
    
    try:
        action = await self._call_llm(...)
        
        # 追踪规划
        if tracker:
            tracker.track_agent_plan(self.agent_id, {"action": action.dict()}, parent_event_id)
        
        return action
    except Exception as e:
        # 错误处理
        pass

# 在 _act 方法中
async def _act(self, action: Action) -> Dict[str, Any]:
    tracker = getattr(self, '_orchestration_tracker', None)
    
    # 追踪行动
    if tracker:
        tracker.track_agent_act(self.agent_id, action.dict(), parent_event_id)
    
    # 追踪工具调用
    if tracker and action.tool_name:
        tool_event_id = tracker.track_tool_start(action.tool_name, action.params, parent_event_id)
    
    try:
        result = await tool.call(**tool_params)
        
        # 追踪工具结束
        if tracker and action.tool_name:
            tracker.track_tool_end(action.tool_name, result.to_dict())
        
        return result
    except Exception as e:
        if tracker and action.tool_name:
            tracker.track_tool_end(action.tool_name, None, str(e))
        raise

# 在 _observe 方法中
async def _observe(self, observation: Dict[str, Any]) -> Dict[str, Any]:
    tracker = getattr(self, '_orchestration_tracker', None)
    
    # 追踪观察
    if tracker:
        tracker.track_agent_observe(self.agent_id, observation, parent_event_id)
    
    return observation
```

#### `src/agents/expert_agent.py`

类似地，在 `execute`、`_plan_action`、`_execute_action` 方法中添加追踪。

### 2. 工具调用追踪

#### `src/agents/tools/base_tool.py`

```python
async def call(self, **kwargs) -> ToolResult:
    tracker = getattr(self, '_orchestration_tracker', None)
    
    # 追踪工具开始
    if tracker:
        tool_event_id = tracker.track_tool_start(self.tool_name, kwargs)
    
    try:
        result = await self._call(**kwargs)
        
        # 追踪工具结束
        if tracker:
            tracker.track_tool_end(self.tool_name, result.to_dict() if hasattr(result, 'to_dict') else result)
        
        return result
    except Exception as e:
        if tracker:
            tracker.track_tool_end(self.tool_name, None, str(e))
        raise
```

### 3. 提示词工程追踪

#### `src/utils/unified_prompt_manager.py`

```python
async def get_prompt(
    self,
    prompt_type: str,
    query: str,
    context: Optional[Dict[str, Any]] = None,
    use_rl_optimization: bool = True,
    use_orchestration: bool = True
) -> str:
    tracker = getattr(self, '_orchestration_tracker', None)
    
    # 追踪提示词生成
    if tracker:
        prompt_event_id = tracker.track_prompt_generate(prompt_type, query, context)
    
    try:
        # 如果使用编排
        if use_orchestration:
            orchestrated_prompt = await self.orchestrator.orchestrate(...)
            
            # 追踪提示词编排
            if tracker:
                tracker.track_prompt_orchestrate(
                    orchestration_strategy,
                    fragments,
                    prompt_event_id
                )
            
            return orchestrated_prompt
        
        # 其他逻辑...
    except Exception as e:
        # 错误处理
        pass
```

#### `src/agents/prompt_engineering_agent.py`

在 `execute` 和 `_generate_optimized_prompt` 方法中添加追踪。

### 4. 上下文工程追踪

#### `src/utils/unified_context_engineering_center.py`

```python
def enhance_context(
    self,
    session_id: str,
    query: str,
    context_fragments: List[ContextFragment],
    enhancement_type: str = "semantic"
) -> Dict[str, Any]:
    tracker = getattr(self, '_orchestration_tracker', None)
    
    # 追踪上下文增强
    if tracker:
        context_event_id = tracker.track_context_enhance(enhancement_type, {"query": query})
    
    try:
        enhanced_context = self._enhance_context_internal(...)
        
        # 追踪上下文更新
        if tracker:
            tracker.track_context_update(enhancement_type, enhanced_context, context_event_id)
        
        return enhanced_context
    except Exception as e:
        # 错误处理
        pass
```

### 5. 在 UnifiedResearchSystem 中传递追踪器

#### `src/unified_research_system.py`

在 `execute_research` 方法中，确保追踪器被传递到各个组件：

```python
async def execute_research(self, request: ResearchRequest) -> ResearchResult:
    # 如果可视化追踪器已设置，传递到各个组件
    if hasattr(self, '_orchestration_tracker') and self._orchestration_tracker:
        # 传递到 Agent
        if self._react_agent:
            self._react_agent._orchestration_tracker = self._orchestration_tracker
        if self._langgraph_react_agent:
            self._langgraph_react_agent._orchestration_tracker = self._orchestration_tracker
        
        # 传递到工具注册表
        if self._tool_registry:
            for tool in self._tool_registry.get_all_tools():
                tool._orchestration_tracker = self._orchestration_tracker
        
        # 传递到提示词管理器
        if hasattr(self, '_prompt_manager') and self._prompt_manager:
            self._prompt_manager._orchestration_tracker = self._orchestration_tracker
        
        # 传递到上下文工程中心
        if hasattr(self, '_context_engineering_center') and self._context_engineering_center:
            self._context_engineering_center._orchestration_tracker = self._orchestration_tracker
```

## 前端显示

前端 HTML 已更新，支持显示编排过程。需要在前端 JavaScript 中处理编排事件：

```javascript
// 在 handleWebSocketMessage 函数中添加
function handleWebSocketMessage(message) {
    if (message.type === 'orchestration_event') {
        const event = message.event;
        displayOrchestrationEvent(event);
    }
    // ... 其他处理
}

function displayOrchestrationEvent(event) {
    // 在编排面板中显示事件
    const panel = document.getElementById('orchestration-panel');
    // 创建事件元素并添加到面板
}
```

## 测试

1. 启动可视化服务器：`python examples/start_visualization_server.py`
2. 在浏览器中打开：`http://localhost:8080`
3. 执行一个查询
4. 查看编排过程面板，应该能看到：
   - Agent 执行过程（思考、规划、行动、观察）
   - 工具调用过程
   - 提示词生成和编排过程
   - 上下文增强和更新过程

## 下一步

1. ✅ 创建编排追踪器
2. ✅ 集成到可视化服务器
3. ⏳ 在关键位置添加追踪钩子（需要逐步实现）
4. ⏳ 更新前端显示编排过程（需要更新 HTML/JS）
5. ⏳ 测试和优化

