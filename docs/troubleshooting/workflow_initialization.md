# LangGraph 工作流初始化问题排查

## 问题：No workflow available. LangGraph workflow not initialized.

### 快速诊断

运行诊断脚本：

```bash
python3 scripts/diagnose_workflow.py
```

或使用修复脚本：

```bash
bash scripts/fix_workflow_init.sh
```

## 常见原因和解决方案

### 1. LangGraph 未安装

**症状**：
- 错误信息：`LangGraph is required. Install with: pip install langgraph`
- 或：`ImportError: cannot import name 'StateGraph' from 'langgraph.graph'`

**解决方案**：

```bash
pip install langgraph
```

验证安装：

```bash
python3 -c "import langgraph; print(langgraph.__version__)"
```

### 2. 环境变量未设置

**症状**：
- 工作流未初始化
- 日志显示：`统一工作流已禁用（ENABLE_UNIFIED_WORKFLOW=false）`

**解决方案**：

```bash
# 方法1：设置环境变量
export ENABLE_UNIFIED_WORKFLOW=true

# 方法2：在 .env 文件中设置
echo "ENABLE_UNIFIED_WORKFLOW=true" >> .env
```

### 3. 工作流初始化失败

**症状**：
- 日志显示：`统一工作流初始化失败`
- 但没有明确的错误信息

**解决方案**：

1. **检查详细日志**：
   ```bash
   # 查看系统日志，寻找错误信息
   tail -f research_system.log | grep -i "workflow\|langgraph"
   ```

2. **运行诊断脚本**：
   ```bash
   python3 scripts/diagnose_workflow.py
   ```

3. **手动测试初始化**：
   ```python
   from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow
   workflow = UnifiedResearchWorkflow(system=None)
   print(f"工作流初始化成功: {workflow.workflow is not None}")
   ```

### 4. 依赖冲突

**症状**：
- 导入错误
- 版本不兼容

**解决方案**：

```bash
# 检查已安装的版本
pip show langgraph

# 升级到最新版本
pip install --upgrade langgraph

# 或安装特定版本
pip install langgraph>=0.2.0
```

### 5. 初始化顺序问题

**症状**：
- 可视化服务器启动时工作流还未初始化

**解决方案**：

工作流应该在系统初始化时自动创建。检查初始化顺序：

```python
# 在 UnifiedResearchSystem._initialize_agents 中
# 顺序应该是：
# 1. 初始化 LangGraph Agent（如果启用）
# 2. 初始化 Entry Router
# 3. 初始化统一工作流
# 4. 初始化可视化服务器
```

## 诊断步骤

### 步骤1：检查 LangGraph 安装

```bash
python3 -c "import langgraph; print('✅ LangGraph:', langgraph.__version__)"
```

### 步骤2：检查环境变量

```bash
python3 -c "import os; print('ENABLE_UNIFIED_WORKFLOW:', os.getenv('ENABLE_UNIFIED_WORKFLOW', 'not set'))"
```

### 步骤3：检查工作流模块

```bash
python3 -c "from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow; print('✅ 模块可用')"
```

### 步骤4：测试工作流初始化

```bash
python3 -c "
from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow
try:
    workflow = UnifiedResearchWorkflow(system=None)
    print('✅ 工作流初始化成功')
    print(f'✅ 工作流对象: {workflow.workflow is not None}')
except Exception as e:
    print(f'❌ 初始化失败: {e}')
    import traceback
    traceback.print_exc()
"
```

### 步骤5：检查系统初始化

查看系统初始化日志，确认工作流是否成功初始化：

```bash
# 查找初始化日志
grep -i "统一工作流" research_system.log
grep -i "workflow" research_system.log
```

## 自动修复

使用修复脚本：

```bash
bash scripts/fix_workflow_init.sh
```

脚本会自动：
1. 检查并安装 LangGraph（如果需要）
2. 检查环境变量
3. 运行诊断
4. 提供修复建议

## 手动修复

如果自动修复失败，按以下步骤手动修复：

### 1. 安装 LangGraph

```bash
pip install langgraph
```

### 2. 设置环境变量

```bash
# 临时设置
export ENABLE_UNIFIED_WORKFLOW=true

# 或添加到 .env 文件
echo "ENABLE_UNIFIED_WORKFLOW=true" >> .env
```

### 3. 重启系统

```bash
# 如果系统正在运行，重启它
# 确保环境变量生效
```

### 4. 验证

```bash
python3 scripts/diagnose_workflow.py
```

## 降级方案

如果无法使用 LangGraph 工作流，系统会自动降级到传统流程：

- 可视化界面会显示简化的工作流图
- 查询仍然可以正常执行
- 只是没有详细的工作流追踪

## 获取帮助

如果问题仍然存在：

1. 运行诊断脚本并查看输出
2. 检查系统日志中的详细错误信息
3. 查看 [LangGraph 集成指南](../usage/langgraph_usage_guide.md)
4. 查看 [LangGraph 故障排除](../usage/langgraph_troubleshooting.md)

