# Chief Agent 统一架构测试脚本使用说明

## 概述

根据 `docs/testing/chief_agent_unified_architecture_test_guide.md` 创建的完整测试脚本，包含所有测试用例的单独测试方法。

## 测试脚本

### 主测试脚本

**位置**: `scripts/test_chief_agent_all_tests.py`

**功能**: 包含所有5个测试用例的单独测试方法，可以单独运行或批量运行。

## 使用方法

### 1. 运行单个测试

```bash
# 运行测试1: Simple 查询快速路径
python scripts/test_chief_agent_all_tests.py --test 1

# 运行测试2: Complex 查询完整智能体序列
python scripts/test_chief_agent_all_tests.py --test 2

# 运行测试3: Reasoning 路径推理引擎
python scripts/test_chief_agent_all_tests.py --test 3

# 运行测试4: 路由逻辑验证
python scripts/test_chief_agent_all_tests.py --test 4

# 运行测试5: 回退机制测试
python scripts/test_chief_agent_all_tests.py --test 5
```

### 2. 运行所有测试

```bash
python scripts/test_chief_agent_all_tests.py --all
```

### 3. 查看帮助信息

```bash
python scripts/test_chief_agent_all_tests.py
```

## 测试用例说明

### 测试1: Simple 查询快速路径

**方法**: `test_1_simple_query_fast_path()`

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

**超时**: 5分钟

### 测试2: Complex 查询完整智能体序列

**方法**: `test_2_complex_query_full_sequence()`

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

**超时**: 10分钟

### 测试3: Reasoning 路径推理引擎

**方法**: `test_3_reasoning_path()`

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

**超时**: 10分钟

### 测试4: 路由逻辑验证

**方法**: `test_4_routing_logic()`

**功能**: 验证工作流构建时的路由配置

**预期行为**:
- ✅ 所有路径（simple、complex、reasoning、multi_agent）都路由到 `chief_agent`
- ✅ `chief_agent_node` 方法存在
- ✅ 策略处理方法存在（`_handle_simple_path`、`_handle_reasoning_path`、`_handle_full_agent_sequence`）

**验证点**:
- 检查工作流构建日志
- 检查路由映射配置
- 检查方法是否存在

**超时**: 无（静态检查）

### 测试5: 回退机制测试

**方法**: `test_5_fallback_mechanism()`

**场景**: 快速路径失败时，应该回退到完整智能体序列

**预期行为**:
- ✅ 快速路径失败时，自动回退到完整智能体序列
- ✅ 即使快速路径失败，也应该有结果（通过完整序列）

**验证点**:
- 检查日志中是否有回退信息
- 检查是否最终有结果

**超时**: 5分钟

## 其他测试脚本

### 1. 快速诊断脚本

**位置**: `scripts/test_simple_query_quick.py`

**功能**: 快速诊断 Simple 查询快速路径的问题

**使用方法**:
```bash
python scripts/test_simple_query_quick.py
```

### 2. Complex 查询测试脚本

**位置**: `scripts/test_complex_query_full_sequence.py`

**功能**: 单独测试 Complex 查询完整智能体序列

**使用方法**:
```bash
python scripts/test_complex_query_full_sequence.py
```

### 3. 诊断工具

**位置**: `scripts/diagnose_simple_query_test.py`

**功能**: 显示常见错误类型和解决方案

**使用方法**:
```bash
python scripts/diagnose_simple_query_test.py
```

## 测试输出示例

```
================================================================================
📝 测试1: Simple 查询快速路径
================================================================================
🔍 查询: What is the capital of France?
🔍 路由路径: simple
🔍 复杂度: 1.5
⏱️  开始执行（超时：5分钟）...

⏱️  执行时间: 8.45秒
✅ 任务完成: True
📝 答案: Paris is the capital of France...
🎯 置信度: 0.85
⚡ 快速路径已启用（执行时间 < 10秒）✅
```

## 性能指标

### Simple 查询性能

**目标**: 执行时间 < 30秒（理想情况下 < 10秒）

**基准**:
- 之前（跳过 Chief Agent）: 几秒
- 现在（通过 Chief Agent 快速路径）: < 30秒

### Complex 查询性能

**目标**: 正常执行，使用完整智能体序列

**测量方法**: 检查执行时间和答案质量

### Reasoning 查询性能

**目标**: 正常执行，使用推理引擎

**测量方法**: 检查执行时间和答案质量

## 常见问题

### Q1: 测试超时

**解决方法**:
- 检查网络连接
- 检查 API 状态
- 考虑增加超时时间（修改脚本中的 timeout 参数）

### Q2: Agent 节点不可用

**解决方法**:
- 检查系统初始化是否成功
- 检查日志中的错误信息
- 确保所有依赖已正确安装

### Q3: 测试失败但没有错误信息

**解决方法**:
- 查看详细日志输出
- 检查状态中的 `error` 和 `errors` 字段
- 运行诊断脚本：`python scripts/diagnose_simple_query_test.py`

## 测试报告

运行测试后，脚本会输出详细的测试结果，包括：
- 每个测试的执行时间
- 任务完成状态
- 答案内容
- 置信度
- 错误信息（如果有）

## 下一步

1. 运行所有测试，验证功能
2. 检查日志，确认策略选择正确
3. 测量性能，确保 Simple 查询仍然快速
4. 验证回退机制是否正常工作
5. 记录测试结果和问题

