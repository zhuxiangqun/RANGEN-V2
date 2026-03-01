# LangGraph 工作流快速修复指南

## 问题：No workflow available. LangGraph workflow not initialized.

### 快速修复（3步）

#### 步骤1：安装 LangGraph

```bash
pip install langgraph
```

#### 步骤2：设置环境变量

```bash
export ENABLE_UNIFIED_WORKFLOW=true
```

或添加到 `.env` 文件：

```bash
echo "ENABLE_UNIFIED_WORKFLOW=true" >> .env
```

#### 步骤3：重启系统

重启你的应用程序，确保环境变量生效。

### 验证修复

运行诊断脚本：

```bash
python3 scripts/diagnose_workflow.py
```

应该看到：

```
✅ LangGraph 已安装: x.x.x
✅ 工作流模块可用
✅ 工作流初始化成功
```

### 自动修复

使用修复脚本（推荐）：

```bash
bash scripts/fix_workflow_init.sh
```

脚本会自动：
- 检查并安装 LangGraph
- 检查环境变量
- 运行诊断
- 提供修复建议

### 如果仍然失败

查看详细排查指南：[工作流初始化问题排查](./workflow_initialization.md)

