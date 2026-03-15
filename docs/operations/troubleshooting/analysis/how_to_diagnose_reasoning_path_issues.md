# 如何使用现有工具诊断推理路径问题

## 概述

系统已经具备丰富的诊断和监控工具，应该使用这些现有工具来诊断推理路径问题，而不是创建新的诊断工具。

## 现有诊断工具

### 1. 工作流健康检查端点

**位置**: `/api/workflow/health`

**使用方法**:
```bash
curl http://localhost:8080/api/workflow/health
```

**检查内容**:
- 系统是否存在
- 系统是否已初始化
- 工作流实例状态
- 工作流图获取能力
- 环境变量配置
- LangGraph 可用性

### 2. 工作流诊断脚本

**位置**: `scripts/diagnose_workflow.py`

**使用方法**:
```bash
python scripts/diagnose_workflow.py
```

**检查内容**:
- 环境变量配置
- LangGraph 安装状态
- 工作流模块可用性
- 工作流初始化能力
- 系统初始化状态

### 3. 系统健康检查器

**位置**: `tools/detection/monitoring/system_health_checker.py`

**使用方法**:
```python
from tools.detection.monitoring.system_health_checker import SystemHealthChecker

checker = SystemHealthChecker()
report = await checker.run_comprehensive_health_check()
```

**检查内容**:
- 模块导入检查
- 语法检查
- 依赖检查
- 性能检查
- 集成检查
- 安全检查

### 4. 综合系统健康检查

**位置**: `tools/scripts/analysis/comprehensive_system_health_check.py`

**使用方法**:
```bash
python tools/scripts/analysis/comprehensive_system_health_check.py
```

**检查内容**:
- Mock使用健康状态
- 性能健康状态
- 资源健康状态
- 错误恢复能力

### 5. 可视化界面的执行追踪

**位置**: 浏览器可视化界面 (`http://localhost:8080`)

**使用方法**:
1. 打开浏览器访问可视化界面
2. 执行查询
3. 查看执行记录和节点状态
4. 检查浏览器控制台的日志

**检查内容**:
- 节点执行状态
- 状态传递情况
- 错误信息
- 执行时间
- 最终结果

### 6. 后端日志分析

**位置**: 系统日志文件

**使用方法**:
```bash
# 查看最近的错误
grep -i "error\|❌\|warning\|⚠️" research_system.log | tail -50

# 查看推理路径相关日志
grep -i "reasoning\|extract_step\|gather_evidence\|synthesize" research_system.log | tail -100

# 查看答案生成相关日志
grep -i "answer.*generation\|final_answer\|extract.*answer" research_system.log | tail -100
```

## 诊断推理路径问题的步骤

### 步骤1: 使用工作流健康检查端点

```bash
curl http://localhost:8080/api/workflow/health | jq
```

检查：
- `workflow_instance.status`: 应该是 "ok"
- `workflow_property.status`: 应该是 "ok"
- `langgraph_available.available`: 应该是 true

### 步骤2: 查看可视化界面的执行记录

1. 打开浏览器访问 `http://localhost:8080`
2. 执行一个查询
3. 查看执行记录中的节点状态
4. 检查是否有错误节点

**关键检查点**:
- `generate_steps` 节点是否执行成功
- `execute_step` 节点是否执行成功
- `gather_evidence` 节点是否执行成功
- `extract_step_answer` 节点是否执行成功
- `synthesize_answer` 节点是否被执行

### 步骤3: 分析后端日志

```bash
# 查看推理路径的执行日志
grep -E "\[Generate Steps\]|\[Execute Step\]|\[Gather Evidence\]|\[Extract Step Answer\]|\[Synthesize Answer\]" research_system.log | tail -100

# 查看错误信息
grep -E "❌|ERROR|error.*reasoning" research_system.log | tail -50

# 查看状态信息
grep -E "current_step|metadata|step_answers" research_system.log | tail -50
```

### 步骤4: 检查节点状态

从可视化界面或日志中检查：

1. **metadata 初始化**:
   - 检查 `state['metadata']` 是否存在
   - 检查 `state['metadata']['current_step']` 是否存在

2. **步骤执行**:
   - 检查 `reasoning_steps` 是否存在
   - 检查 `current_step_index` 是否正确
   - 检查 `step_answers` 是否被填充

3. **错误状态**:
   - 检查 `state['error']` 是否被设置
   - 检查 `state['errors']` 列表中的错误详情

### 步骤5: 使用系统健康检查器

```python
from tools.detection.monitoring.system_health_checker import SystemHealthChecker
import asyncio

async def check_reasoning_components():
    checker = SystemHealthChecker()
    report = await checker.run_comprehensive_health_check()
    
    # 检查推理相关组件
    reasoning_checks = [r for r in report.check_results 
                       if 'reasoning' in r.component.lower() 
                       or 'workflow' in r.component.lower()]
    
    for check in reasoning_checks:
        print(f"{check.component}: {check.status.value} - {check.message}")

asyncio.run(check_reasoning_components())
```

## 常见问题诊断

### 问题1: 推理路径检测到错误后直接结束

**诊断方法**:
1. 查看日志中的错误信息：
   ```bash
   grep "检测到错误，结束推理" research_system.log
   ```

2. 检查错误来源：
   - 查看 `state['error']` 的值
   - 查看 `state['errors']` 列表中的错误详情

3. 检查节点执行状态：
   - 查看哪个节点设置了错误
   - 查看错误的具体原因

**修复**: 已修复 - 即使有错误，如果有步骤答案，也会尝试合成最终答案

### 问题2: metadata 未初始化

**诊断方法**:
1. 查看日志中的警告：
   ```bash
   grep "没有当前步骤信息\|metadata" research_system.log
   ```

2. 检查状态传递：
   - 查看 `execute_step` 节点是否设置了 `metadata['current_step']`
   - 查看后续节点是否能访问到 `current_step`

**修复**: 已修复 - 所有节点都会先检查并初始化 `metadata`

### 问题3: 步骤答案未正确提取

**诊断方法**:
1. 查看提取答案的日志：
   ```bash
   grep "\[Extract Step Answer\]" research_system.log | tail -20
   ```

2. 检查步骤答案：
   - 查看 `state['step_answers']` 是否被填充
   - 查看每个步骤的答案内容

**修复**: 已修复 - 改进了错误处理，即使提取失败也不会阻止继续执行

## 最佳实践

1. **优先使用可视化界面**: 最直观的方式查看执行状态
2. **结合日志分析**: 查看详细的执行日志
3. **使用健康检查端点**: 快速检查系统状态
4. **利用现有工具**: 不要创建新的诊断工具，使用现有的

## 总结

系统已经具备完整的诊断和监控能力，应该：
- ✅ 使用可视化界面查看执行状态
- ✅ 使用健康检查端点检查系统状态
- ✅ 分析后端日志找出问题
- ✅ 使用现有的诊断脚本
- ❌ 不要创建新的诊断工具

