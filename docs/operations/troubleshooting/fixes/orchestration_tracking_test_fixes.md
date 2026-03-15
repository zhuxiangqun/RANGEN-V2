# 编排追踪测试修复

## 问题概述

运行 `pytest tests/test_orchestration_tracking.py -v` 时，有 3 个测试失败：

1. **`test_tool_tracking`** - `TypeError: OrchestrationTracker.track_tool_end() got an unexpected keyword argument 'parent_event_id'`
2. **`test_prompt_tracking`** - `AttributeError: 'OrchestrationTracker' object has no attribute 'track_prompt_optimize'`
3. **`test_event_tree_structure`** - `TypeError: OrchestrationTracker.track_tool_end() got an unexpected keyword argument 'parent_event_id'`

## 根本原因分析

### 问题 1 和 3：`track_tool_end` 缺少 `parent_event_id` 参数

**测试代码期望**：
```python
tracker.track_tool_end("test_tool", {"result": "success"}, parent_event_id=event_id)
```

**实际方法签名**：
```python
def track_tool_end(self, tool_name: str, result: Dict[str, Any] = None, error: Optional[str] = None):
    # 不接受 parent_event_id 参数
```

**问题**：测试需要显式传递 `parent_event_id` 来建立事件层级关系，但方法签名不支持。

### 问题 2：缺少 `track_prompt_optimize` 方法

**测试代码期望**：
```python
tracker.track_prompt_optimize("test_prompt", "What is artificial intelligence?")
```

**实际情况**：
- `OrchestrationEventType` 枚举中有 `PROMPT_OPTIMIZE` 类型
- 但 `OrchestrationTracker` 类中没有对应的 `track_prompt_optimize` 方法
- 只有 `track_prompt_generate` 和 `track_prompt_orchestrate` 方法

### 问题 3（额外）：`track_agent_end` 也需要支持 `parent_event_id`

在 `test_event_tree_structure` 测试中，第134行也调用了：
```python
tracker.track_agent_end("parent_agent", {}, parent_event_id=parent_id)
```

但 `track_agent_end` 方法也不支持 `parent_event_id` 参数。

## 修复方案

### 修复 1：为 `track_tool_end` 添加 `parent_event_id` 参数

**修改位置**：`src/visualization/orchestration_tracker.py` 第167行

**修改前**：
```python
def track_tool_end(self, tool_name: str, result: Dict[str, Any] = None, error: Optional[str] = None):
    """追踪工具执行结束"""
    event_key = f"tool_{tool_name}"
    start_event = self.active_events.pop(event_key, None)
    
    duration = None
    if start_event:
        duration = time.time() - start_event.timestamp
    
    event = OrchestrationEvent(
        event_type=OrchestrationEventType.TOOL_END,
        component_name=tool_name,
        component_type="tool",
        timestamp=time.time(),
        duration=duration,
        data={"result": result, "error": error},
        parent_event_id=start_event.event_id if start_event else None
    )
    self._add_event(event)
    return event.event_id
```

**修改后**：
```python
def track_tool_end(self, tool_name: str, result: Dict[str, Any] = None, error: Optional[str] = None, parent_event_id: Optional[str] = None):
    """追踪工具执行结束"""
    event_key = f"tool_{tool_name}"
    start_event = self.active_events.pop(event_key, None)
    
    duration = None
    if start_event:
        duration = time.time() - start_event.timestamp
        # 如果提供了 parent_event_id，使用它；否则使用 start_event 的 event_id
        final_parent_id = parent_event_id if parent_event_id is not None else start_event.event_id
    else:
        final_parent_id = parent_event_id
    
    event = OrchestrationEvent(
        event_type=OrchestrationEventType.TOOL_END,
        component_name=tool_name,
        component_type="tool",
        timestamp=time.time(),
        duration=duration,
        data={"result": result, "error": error},
        parent_event_id=final_parent_id
    )
    self._add_event(event)
    return event.event_id
```

**逻辑说明**：
- 如果提供了 `parent_event_id`，优先使用它
- 如果没有提供但存在 `start_event`，使用 `start_event.event_id`
- 如果都没有，使用 `None`

### 修复 2：为 `track_agent_end` 添加 `parent_event_id` 参数

**修改位置**：`src/visualization/orchestration_tracker.py` 第80行

**修改逻辑**：与 `track_tool_end` 相同，添加可选的 `parent_event_id` 参数，并优先使用它。

### 修复 3：添加 `track_prompt_optimize` 方法

**修改位置**：`src/visualization/orchestration_tracker.py` 第213行之后

**新增方法**：
```python
def track_prompt_optimize(self, prompt_type: str, optimized_query: str, context: Dict[str, Any] = None, parent_event_id: Optional[str] = None):
    """追踪提示词优化"""
    event = OrchestrationEvent(
        event_type=OrchestrationEventType.PROMPT_OPTIMIZE,
        component_name=prompt_type,
        component_type="prompt_engineering",
        timestamp=time.time(),
        data={"optimized_query": optimized_query, "context": context or {}},
        parent_event_id=parent_event_id
    )
    self._add_event(event)
    return event.event_id
```

## 修复后的行为

### 向后兼容性

✅ **完全向后兼容**：
- `track_tool_end` 和 `track_agent_end` 的 `parent_event_id` 参数是可选的
- 如果不提供，行为与之前完全相同（从 `active_events` 中获取）
- 如果提供，则使用提供的值，允许更灵活的事件层级关系

### 功能增强

✅ **支持显式事件层级**：
- 测试可以显式指定 `parent_event_id`，建立更复杂的事件树结构
- 支持跨组件的层级关系（例如，工具事件可以作为 Agent 事件的子事件）

✅ **完整的提示词工程追踪**：
- 现在支持追踪提示词生成、优化和编排三个步骤
- 与 `OrchestrationEventType` 枚举中的类型完全对应

## 测试验证

✅ **修复成功！所有 8 个测试均已通过**

测试结果（2025年）：
```
============================================================ 8 passed in 3.97s ============================================================
```

通过的测试列表：

1. ✅ `test_tracker_initialization` - 追踪器初始化
2. ✅ `test_agent_tracking` - Agent 追踪
3. ✅ `test_tool_tracking` - 工具追踪（已修复）
4. ✅ `test_prompt_tracking` - 提示词工程追踪（已修复）
5. ✅ `test_context_tracking` - 上下文工程追踪
6. ✅ `test_system_integration` - 系统集成
7. ✅ `test_event_tree_structure` - 事件树结构（已修复）
8. ✅ `test_event_summary` - 事件摘要

**测试执行时间**：3.97 秒（所有测试）

## 相关文件

- **修复文件**：`src/visualization/orchestration_tracker.py`
- **测试文件**：`tests/test_orchestration_tracking.py`
- **文档文件**：`docs/fixes/orchestration_tracking_test_fixes.md`（本文档）

## 总结

本次修复解决了编排追踪器 API 与测试用例之间的不匹配问题：

1. ✅ 添加了 `parent_event_id` 参数支持，增强了事件层级关系的灵活性
2. ✅ 实现了缺失的 `track_prompt_optimize` 方法，完善了提示词工程追踪功能
3. ✅ 保持了向后兼容性，不影响现有代码

所有修复都遵循了项目的编码规范，并保持了 API 的一致性。

