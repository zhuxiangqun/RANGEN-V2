# Cursor节点Docstring同步更新指南

## 概述

本指南说明如何通过Cursor的设定，在修改节点功能时自动同步更新docstring，并确保提供清晰的description。

## Cursor规则配置

### 1. `.cursorrules` 文件

项目根目录的 `.cursorrules` 文件已包含节点docstring规范：

- **统一格式要求**: 所有节点函数必须使用单行docstring格式 `"""节点名称 - 功能说明"""`
- **修改时同步更新**: 修改节点功能时，必须同步更新docstring
- **格式检查清单**: 提供了检查清单确保docstring与功能同步

### 2. 代码片段（Code Snippets）

VSCode/Cursor支持代码片段快速创建符合规范的节点函数。

#### 安装代码片段

代码片段文件位于：`.vscode/langgraph-node.code-snippets`

#### 使用方法

1. **创建节点函数**:
   - 输入 `lgnode` 然后按 Tab
   - 会自动生成带docstring的节点函数模板

2. **创建独立节点函数**:
   - 输入 `lgstandalone` 然后按 Tab
   - 生成独立的节点函数模板

3. **插入docstring**:
   - 输入 `lgdoc` 然后按 Tab
   - 插入docstring模板

#### 代码片段示例

```python
# 输入 lgnode，然后按 Tab
async def route_query_node(self, state: ResearchSystemState) -> ResearchSystemState:
    """路由查询节点 - 初始化状态并判断查询复杂度"""
    logger.info(f"🚀 [路由查询节点] 开始处理...")
    # ... 自动生成的模板代码
```

## 工作流程

### 修改节点功能时的步骤

1. **修改节点实现**:
   ```python
   async def _route_query_node(self, state: ResearchSystemState) -> ResearchSystemState:
       """路由查询节点 - 初始化状态并判断查询复杂度"""
       # 添加新功能：智能路由
       if self._should_use_smart_routing(state):
           return self._smart_route(state)
       # ... 原有逻辑
   ```

2. **同步更新docstring**:
   ```python
   async def _route_query_node(self, state: ResearchSystemState) -> ResearchSystemState:
       """路由查询节点 - 初始化状态并判断查询复杂度（支持智能路由）"""
       # 新功能已实现
   ```

3. **运行检查脚本**:
   ```bash
   python scripts/check_node_docstrings.py
   ```

4. **验证可视化系统**:
   - 刷新可视化页面
   - 检查节点说明是否已更新

## 检查工具

### 检查脚本

运行检查脚本验证所有节点函数的docstring：

```bash
# 检查所有节点函数的docstring
python scripts/check_node_docstrings.py

# 自动修复格式问题（实验性）
python scripts/check_node_docstrings.py --fix
```

### 检查内容

脚本会检查：
- ✅ docstring是否存在
- ✅ docstring格式是否正确（单行格式）
- ✅ docstring是否符合规范（节点名称 - 功能说明）
- ✅ docstring是否反映了当前功能

## 最佳实践

### 1. 创建新节点时

1. 使用代码片段 `lgnode` 创建节点函数
2. 填写清晰的节点名称和功能说明
3. 实现节点逻辑
4. 运行检查脚本验证

### 2. 修改节点功能时

1. **先更新docstring**，再修改实现（TDD风格）
2. 如果功能变化较大，更新docstring中的功能说明
3. 如果添加了新特性，在docstring中简要说明
4. 运行检查脚本验证

### 3. Docstring编写规范

#### ✅ 好的示例

```python
"""路由查询节点 - 初始化状态并判断查询复杂度"""
"""知识检索智能体节点 - 从知识库中检索相关知识，提供证据和引用"""
"""学习聚合节点 - 从执行结果和反馈中聚合学习数据，优化系统性能"""
```

#### ❌ 不好的示例

```python
"""路由节点"""  # 缺少功能说明
"""路由查询节点"""  # 缺少功能说明
"""节点 - 处理查询"""  # 节点名称不清晰
"""路由查询节点 - 这是一个用于路由查询的节点，它会分析查询的复杂度，然后决定使用哪种路由方式，包括简单路由、复杂路由、多智能体路由和推理链路由"""  # 太长，应该简洁
```

### 4. 动态生成的节点

对于能力节点等动态生成的节点：

```python
def create_capability_node(capability_plugin):
    def capability_node(state):
        # ... 实现
    
    # 🚀 必须设置docstring
    plugin_name = getattr(capability_plugin, 'name', 'unknown')
    plugin_desc = getattr(capability_plugin, 'description', None)
    if plugin_desc:
        capability_node.__doc__ = f"能力节点({plugin_name}) - {plugin_desc}"
    else:
        capability_node.__doc__ = f"能力节点({plugin_name}) - 执行能力插件功能"
    
    return capability_node
```

## Cursor AI助手提示

### 修改节点时的提示词

当要求Cursor修改节点功能时，可以使用以下提示词：

```
修改 [节点名称] 节点，添加 [新功能]。请确保：
1. 同步更新docstring以反映新功能
2. docstring格式为："""节点名称 - 功能说明（新功能）"""
3. 运行检查脚本验证docstring格式
```

### 示例对话

**用户**: "修改路由查询节点，添加智能路由功能"

**Cursor AI**: 
1. 修改节点实现，添加智能路由逻辑
2. 更新docstring：`"""路由查询节点 - 初始化状态并判断查询复杂度（支持智能路由）"""`
3. 运行检查脚本验证

## 自动化集成

### Pre-commit钩子（可选）

可以创建pre-commit钩子自动检查：

```bash
#!/bin/bash
# .git/hooks/pre-commit

python scripts/check_node_docstrings.py
if [ $? -ne 0 ]; then
    echo "❌ 节点docstring检查失败，请修复后重试"
    exit 1
fi
```

### CI/CD集成（可选）

在CI/CD流程中添加检查：

```yaml
# .github/workflows/check-docstrings.yml
name: Check Node Docstrings

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: python scripts/check_node_docstrings.py
```

## 故障排除

### 问题1: 可视化系统中节点说明未更新

**原因**: docstring格式不正确或未更新

**解决**:
1. 检查docstring格式是否正确
2. 运行检查脚本验证
3. 刷新可视化页面

### 问题2: 检查脚本报告格式错误

**原因**: docstring不符合规范

**解决**:
1. 查看检查脚本输出的具体错误
2. 参考"好的示例"修复格式
3. 重新运行检查脚本

### 问题3: 代码片段不工作

**原因**: VSCode/Cursor未加载代码片段文件

**解决**:
1. 确认 `.vscode/langgraph-node.code-snippets` 文件存在
2. 重启VSCode/Cursor
3. 检查设置中是否启用了代码片段

## 总结

通过以下方式确保节点docstring同步更新：

1. ✅ **Cursor规则**: `.cursorrules` 文件中的规范
2. ✅ **代码片段**: 快速创建符合规范的节点函数
3. ✅ **检查脚本**: 自动验证docstring格式
4. ✅ **最佳实践**: 修改功能时先更新docstring
5. ✅ **可视化系统**: 自动从docstring提取说明

遵循这些规范，可以确保节点说明始终与功能保持同步！

