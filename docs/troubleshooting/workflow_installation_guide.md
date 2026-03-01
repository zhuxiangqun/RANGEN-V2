# LangGraph 工作流安装指南

## 问题：No workflow available. LangGraph workflow not initialized.

### 根本原因

根据诊断结果，主要原因是 **LangGraph 未安装**。

## 安装步骤

### 方法1：使用 requirements 文件（推荐）

```bash
# 安装 LangGraph 及其依赖
pip install -r requirements_langgraph.txt
```

### 方法2：直接安装

```bash
# 安装 LangGraph
pip install langgraph
```

### 方法3：使用修复脚本（自动）

```bash
bash scripts/fix_workflow_init.sh
```

## 验证安装

### 步骤1：检查安装

```bash
python3 -c "import langgraph; print('✅ LangGraph 已安装')"
```

### 步骤2：运行诊断

```bash
python3 scripts/diagnose_workflow.py
```

应该看到：

```
✅ LangGraph 已安装: x.x.x
✅ 工作流模块可用
✅ 工作流初始化成功
```

### 步骤3：检查环境变量

```bash
# 确保环境变量已设置
export ENABLE_UNIFIED_WORKFLOW=true

# 或添加到 .env 文件
echo "ENABLE_UNIFIED_WORKFLOW=true" >> .env
```

## 常见问题

### Q1: 安装后仍然报错？

**A**: 检查是否在正确的虚拟环境中：

```bash
# 检查当前 Python 环境
which python3
python3 --version

# 检查已安装的包
pip list | grep langgraph
```

### Q2: 虚拟环境问题

**A**: 确保在正确的虚拟环境中安装：

```bash
# 激活虚拟环境
source .venv/bin/activate  # 或你的虚拟环境路径

# 然后安装
pip install langgraph
```

### Q3: 权限问题

**A**: 使用 `--user` 标志或虚拟环境：

```bash
# 方法1：使用 --user
pip install --user langgraph

# 方法2：使用虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate
pip install langgraph
```

## 安装后配置

### 1. 设置环境变量

```bash
# 临时设置
export ENABLE_UNIFIED_WORKFLOW=true

# 永久设置（添加到 .env 文件）
echo "ENABLE_UNIFIED_WORKFLOW=true" >> .env
```

### 2. 重启系统

重启应用程序，确保环境变量生效。

### 3. 验证工作流

运行诊断脚本确认工作流可以正常初始化：

```bash
python3 scripts/diagnose_workflow.py
```

## 快速修复命令

```bash
# 一键修复（推荐）
bash scripts/fix_workflow_init.sh

# 或手动修复
pip install langgraph && export ENABLE_UNIFIED_WORKFLOW=true && python3 scripts/diagnose_workflow.py
```

## 下一步

安装完成后：

1. ✅ 运行诊断验证：`python3 scripts/diagnose_workflow.py`
2. ✅ 重启系统
3. ✅ 检查可视化界面：`http://localhost:8080`

如果问题仍然存在，查看 [详细排查指南](./workflow_initialization.md)

