# Chief Agent 统一架构测试指南

## 概述

本测试指南用于验证 Chief Agent 统一架构的实施效果，确保：
1. 所有路径（simple、complex、reasoning、multi_agent）都通过 Chief Agent
2. Simple 查询仍然快速（通过快速路径）
3. Complex 查询使用完整智能体序列
4. Reasoning 查询使用推理引擎策略
5. 回退机制正常工作

## 测试脚本

### 主测试脚本

**位置**: `scripts/test_chief_agent_unified_architecture.py`

**功能**:
- 测试 Simple 查询快速路径
- 测试 Complex 查询完整智能体序列
- 测试 Reasoning 路径推理引擎
- 验证路由逻辑

### 运行测试

```bash
# 方法1: 直接运行脚本
python scripts/test_chief_agent_unified_architecture.py

# 方法2: 使用 pytest（如果可用）
pytest tests/test_chief_agent_unified_architecture.py -v
```

## 测试用例

### 测试1: Simple 查询快速路径

**查询**: "What is the capital of France?"

**预期行为**:
- ✅ 路由到 `chief_agent` 节点
- ✅ 使用快速路径策略（`_handle_simple_path`）
- ✅ 执行时间 < 30秒（理想情况下 < 10秒）
- ✅ 直接使用知识检索服务，跳过部分智能体
- ✅ 返回答案
 
**验证点**:
- 检查日志中是否有 "⚡ [快速路径]" 或 "⚡ [核心大脑] 使用快速路径策略"
- 检查执行时间是否在预期范围内
- 检查答案是否正确

### 测试2: Complex 查询完整智能体序列

**查询**: "Compare the economic policies of the United States and China in the 21st century"

**预期行为**:
- ✅ 路由到 `chief_agent` 节点
- ✅ 使用完整智能体序列策略（`_handle_full_agent_sequence`）
- ✅ 通过 Chief Agent 协调所有专家智能体
- ✅ 执行顺序：`chief_agent` → `memory_agent` → `knowledge_retrieval_agent` → `reasoning_agent` → `answer_generation_agent` → `citation_agent`
- ✅ 返回答案

**验证点**:
- 检查日志中是否有 "🔧 [核心大脑] 使用完整智能体序列策略"
- 检查是否调用了 Chief Agent 的 `execute` 方法
- 检查答案是否完整和准确

### 测试3: Reasoning 路径推理引擎

**查询**: "Who was the 15th first lady of the United States?"

**预期行为**:
- ✅ 路由到 `chief_agent` 节点
- ✅ 使用推理引擎策略（`_handle_reasoning_path`）
- ✅ 使用推理引擎处理推理链查询
- ✅ 返回答案

**验证点**:
- 检查日志中是否有 "🧠 [核心大脑] 使用推理引擎策略"
- 检查是否调用了 `system.execute_research` 或推理引擎
- 检查答案是否正确

### 测试4: 路由逻辑验证

**功能**: 验证工作流构建时的路由配置

**预期行为**:
- ✅ 所有路径（simple、complex、reasoning、multi_agent）都路由到 `chief_agent`
- ✅ `chief_agent_node` 方法存在
- ✅ 策略处理方法存在（`_handle_simple_path`、`_handle_reasoning_path`、`_handle_full_agent_sequence`）

**验证点**:
- 检查工作流构建日志
- 检查路由映射配置
- 检查方法是否存在

## 性能指标

### Simple 查询性能

**目标**: 执行时间 < 30秒（理想情况下 < 10秒）

**测量方法**:
```python
start_time = time.time()
result = await system.execute_research(request)
execution_time = time.time() - start_time
```

**基准**:
- 之前（跳过 Chief Agent）: 几秒
- 现在（通过 Chief Agent 快速路径）: < 30秒

### Complex 查询性能

**目标**: 正常执行，使用完整智能体序列

**测量方法**: 检查执行时间和答案质量

### Reasoning 查询性能

**目标**: 正常执行，使用推理引擎

**测量方法**: 检查执行时间和答案质量

## 日志检查

### 关键日志信息

**快速路径**:
```
⚡ [核心大脑] 使用快速路径策略（Simple查询优化）
⚡ [快速路径] 直接检索知识库（跳过部分智能体）...
✅ [快速路径] 直接答案生成成功
```

**完整智能体序列**:
```
🔧 [核心大脑] 使用完整智能体序列策略（Complex/Multi-agent查询）
🧠 [核心大脑] ChiefAgent 开始协调多智能体系统
✅ [完整智能体序列] 协调完成
```

**推理引擎策略**:
```
🧠 [核心大脑] 使用推理引擎策略（推理链处理）
✅ [推理路径] 推理完成
```

### 路由日志

**工作流构建时**:
```
✅ [工作流构建] 统一架构：所有路径都通过核心大脑（ChiefAgent）协调
   → 路由映射: simple/complex/multi_agent/reasoning → chief_agent（核心大脑）
```

## 回退机制测试

### 测试场景

1. **快速路径失败**: 知识检索失败时，应该回退到完整智能体序列
2. **推理引擎不可用**: 推理引擎不可用时，应该回退到完整智能体序列

### 验证方法

检查日志中是否有回退信息：
```
⚠️ [快速路径] 知识检索失败，回退到完整智能体序列
⚠️ [推理路径] 推理引擎不可用，回退到完整智能体序列
```

## 常见问题

### Q1: Simple 查询执行时间过长

**可能原因**:
- 快速路径未启用
- 知识检索服务响应慢
- LLM API 响应慢

**解决方法**:
- 检查日志，确认是否使用了快速路径
- 检查知识检索服务的性能
- 检查 LLM API 的响应时间

### Q2: Complex 查询未使用完整智能体序列

**可能原因**:
- Chief Agent 不可用
- 路由配置错误

**解决方法**:
- 检查 Chief Agent 是否初始化成功
- 检查路由映射配置

### Q3: Reasoning 查询未使用推理引擎

**可能原因**:
- 推理引擎不可用
- `needs_reasoning_chain` 标志未设置

**解决方法**:
- 检查推理引擎是否初始化成功
- 检查复杂度判断服务是否正确设置了 `needs_reasoning_chain`

## 测试报告模板

```markdown
# Chief Agent 统一架构测试报告

**测试日期**: YYYY-MM-DD
**测试人员**: [姓名]

## 测试结果

| 测试用例 | 状态 | 执行时间 | 备注 |
|---------|------|---------|------|
| Simple 查询快速路径 | ✅/❌ | X.XX秒 | |
| Complex 查询完整序列 | ✅/❌ | X.XX秒 | |
| Reasoning 路径推理引擎 | ✅/❌ | X.XX秒 | |
| 路由逻辑验证 | ✅/❌ | - | |

## 性能分析

- Simple 查询平均执行时间: X.XX秒
- Complex 查询平均执行时间: X.XX秒
- Reasoning 查询平均执行时间: X.XX秒

## 问题记录

[记录测试中发现的问题]

## 结论

[测试结论和建议]
```

## 下一步

1. 运行测试脚本，验证所有功能
2. 检查日志，确认策略选择正确
3. 测量性能，确保 Simple 查询仍然快速
4. 验证回退机制是否正常工作
5. 记录测试结果和问题

