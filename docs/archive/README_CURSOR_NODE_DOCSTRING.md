# Cursor节点Docstring同步更新快速指南

## 🚀 快速开始

### 1. 使用代码片段创建节点

在Cursor/VSCode中，输入以下代码片段前缀，然后按 `Tab`：

- `lgnode` - 创建类方法节点函数（带完整模板）
- `lgstandalone` - 创建独立节点函数（带完整模板）
- `lgdoc` - 仅插入docstring模板

### 2. 修改节点时的检查清单

修改节点功能时，Cursor AI会自动提醒你：

- ✅ **同步更新docstring** - 功能变化时，docstring必须更新
- ✅ **格式检查** - docstring必须是单行格式：`"""节点名称 - 功能说明"""`
- ✅ **运行检查脚本** - 使用 `python scripts/check_node_docstrings.py` 验证

### 3. Docstring格式规范

**✅ 正确格式**:
```python
"""路由查询节点 - 初始化状态并判断查询复杂度"""
"""知识检索智能体节点 - 从知识库中检索相关知识，提供证据和引用"""
```

**❌ 错误格式**:
```python
"""路由节点"""  # 缺少功能说明
"""路由查询节点"""  # 缺少功能说明
"""节点 - 处理查询"""  # 节点名称不清晰
```

## 📋 工作流程

### 创建新节点

1. 输入 `lgnode` + Tab，生成模板
2. 填写节点名称和功能说明
3. 实现节点逻辑
4. 运行检查脚本验证

### 修改现有节点

1. **先更新docstring**（TDD风格）
2. 修改节点实现
3. 运行检查脚本验证
4. 刷新可视化页面查看更新

## 🔧 工具

### 检查脚本

```bash
# 检查所有节点函数的docstring
python scripts/check_node_docstrings.py

# 自动修复格式问题（实验性）
python scripts/check_node_docstrings.py --fix
```

### Cursor AI提示词

修改节点时，可以这样提示Cursor：

```
修改 [节点名称] 节点，添加 [新功能]。请确保：
1. 同步更新docstring以反映新功能
2. docstring格式为："""节点名称 - 功能说明（新功能）"""
3. 运行检查脚本验证docstring格式
```

## 📚 详细文档

查看完整指南：`docs/development/cursor_node_docstring_guide.md`

## ✨ 优势

1. **自动同步** - 可视化系统自动从docstring提取说明
2. **格式统一** - 所有节点使用相同的docstring格式
3. **易于维护** - 修改功能时只需更新docstring
4. **工具支持** - 代码片段和检查脚本提高效率

