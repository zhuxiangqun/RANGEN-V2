# 节点说明自动更新机制

## 概述

节点说明自动更新机制实现了从节点函数的docstring动态提取说明，当节点功能发生变化时，说明会自动更新，无需手动维护硬编码字典。

## 实现原理

### 1. 工作流程

```
可视化服务器请求工作流图数据
    ↓
传递workflow对象给WorkflowGraphBuilder
    ↓
get_node_descriptions(workflow=workflow)
    ↓
_extract_node_descriptions_from_workflow(workflow)
    ↓
从workflow对象中提取节点函数
    ↓
_extract_docstring(node_func)
    ↓
提取并格式化docstring
    ↓
合并到节点说明字典（优先使用动态说明）
```

### 2. 核心方法

#### `get_node_descriptions(workflow=None)`

```python
def get_node_descriptions(self, workflow=None) -> Dict[str, str]:
    """
    获取节点功能说明映射（用于 tooltip）
    
    🚀 增强：优先从节点函数的docstring动态提取说明，如果没有则使用硬编码的说明
    这样当节点功能发生变化时，说明会自动更新
    
    Args:
        workflow: LangGraph工作流对象（可选），如果提供则尝试动态提取节点说明
    
    Returns:
        节点名称到说明的映射字典
    """
    descriptions = self.NODE_DESCRIPTIONS.copy()  # 硬编码的说明作为后备
    
    # 如果提供了工作流对象，尝试动态提取节点说明
    if workflow is not None:
        try:
            dynamic_descriptions = self._extract_node_descriptions_from_workflow(workflow)
            # 合并动态说明（优先使用动态说明）
            for node_name, desc in dynamic_descriptions.items():
                if desc:  # 只有当动态说明不为空时才使用
                    descriptions[node_name] = desc
        except Exception as e:
            logger.warning(f"⚠️ [节点说明] 动态提取节点说明失败: {e}，使用硬编码说明")
    
    return descriptions
```

#### `_extract_node_descriptions_from_workflow(workflow)`

从LangGraph工作流对象中提取节点函数的docstring，支持多种获取方式：

1. **方法1**: 从 `workflow.nodes` 获取
2. **方法2**: 从 `workflow.get_graph().nodes` 获取
3. **方法3**: 从 `workflow._builder._nodes` 获取（内部结构）

#### `_extract_docstring(node_func)`

从节点函数中提取docstring并格式化为说明文本：

1. **获取docstring**:
   - 直接获取 `__doc__`
   - 如果是装饰器包装的函数，获取 `__wrapped__.__doc__`
   - 如果是方法对象，获取 `__func__.__doc__`

2. **格式化docstring**:
   - 提取第一行或前两行作为简要说明
   - 移除docstring格式标记（`"""`, `'''`）
   - 处理节点名称重复的情况（移除 "节点名称 - " 前缀）

## 使用方式

### 1. 节点函数docstring格式

统一使用单行格式：

```python
async def _route_query_node(self, state: ResearchSystemState) -> ResearchSystemState:
    """路由查询节点 - 初始化状态并判断查询复杂度"""
    # ... 实现代码
```

### 2. 动态生成的节点

对于动态生成的节点（如能力节点），通过设置 `__doc__` 属性：

```python
def create_capability_node(capability_plugin):
    def capability_node(state):
        # ... 实现代码
    
    # 动态设置docstring
    plugin_name = getattr(capability_plugin, 'name', 'unknown')
    plugin_desc = getattr(capability_plugin, 'description', None)
    if plugin_desc:
        capability_node.__doc__ = f"能力节点({plugin_name}) - {plugin_desc}"
    else:
        capability_node.__doc__ = f"能力节点({plugin_name}) - 执行能力插件功能"
    
    return capability_node
```

## 优势

1. **自动更新**: 节点功能变化时，说明自动从docstring更新
2. **向后兼容**: 如果没有docstring，使用硬编码说明
3. **灵活提取**: 支持多种函数类型和获取方式
4. **智能格式化**: 自动清理和格式化docstring

## 注意事项

1. **docstring格式**: 建议统一使用单行格式 `"""节点名称 - 简要说明"""`，便于提取和显示
2. **保持更新**: 修改节点功能时，同步更新docstring
3. **动态节点**: 能力节点等动态生成的节点，确保插件提供清晰的 `description`

## 示例

### 修改节点功能

```python
# 修改前
async def _route_query_node(self, state: ResearchSystemState) -> ResearchSystemState:
    """路由查询节点 - 初始化状态并判断查询复杂度"""
    # ... 旧实现

# 修改后
async def _route_query_node(self, state: ResearchSystemState) -> ResearchSystemState:
    """路由查询节点 - 初始化状态并判断查询复杂度（支持智能路由）"""
    # ... 新实现（添加了智能路由功能）
```

修改后，可视化系统中的节点说明会自动更新为新的说明，无需手动修改硬编码字典。

