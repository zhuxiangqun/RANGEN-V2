# 子查询改进计划

## 目标
确保推理链正确，子查询能够找到证据，而不是依赖于回退机制。

## 问题分析

### 问题1：子查询格式错误 ⚠️ P0

**症状**：
- "What is who was the 15th First Lady..." - 语法错误
- 子查询提取时没有正确处理已经包含疑问词的描述

**根本原因**：
1. LLM生成的推理步骤描述可能格式不规范
2. `_extract_executable_sub_query`方法在提取时可能产生语法错误
3. 子查询提取逻辑不够智能，无法正确处理所有格式

---

### 问题2：子查询提取逻辑不够智能 ⚠️ P0

**症状**：
- 从描述"Identify who was the 15th First Lady"提取时，可能产生"What is Identify who was..."
- 规则匹配不够完善，无法处理所有情况

**根本原因**：
1. 规则匹配只检查开头，不检查中间
2. 如果描述是"Identify who was X"，规则匹配会错误地添加"What is"前缀
3. 缺少对描述内容的智能分析

---

### 问题3：LLM生成的sub_query字段可能为空或格式错误 ⚠️ P1

**症状**：
- LLM生成的推理步骤中，`sub_query`字段可能为空
- 即使有`sub_query`，格式可能不正确

**根本原因**：
1. LLM提示词可能不够明确
2. 缺少对LLM生成的`sub_query`的验证

---

## 修复方案

### 修复1：改进子查询提取逻辑，确保格式正确 ✅

**位置**：`src/core/real_reasoning_engine.py` 第10741-10850行

**修复**：
1. 改进疑问词检测：不仅检查开头，还检查整个描述
2. 如果描述已经包含疑问词，直接使用，不添加前缀
3. 改进规则匹配，避免重复添加疑问词

---

### 修复2：改进LLM提示词，确保生成正确的sub_query ✅

**位置**：`src/core/real_reasoning_engine.py` 第10511-10524行

**修复**：
1. 强化提示词，明确要求生成可执行的子查询
2. 提供更多示例，展示正确的子查询格式
3. 要求LLM在`sub_query`字段中直接生成可执行的查询

---

### 修复3：验证和修复LLM生成的sub_query ✅

**位置**：`src/core/real_reasoning_engine.py` 第10632-10644行

**修复**：
1. 验证LLM生成的`sub_query`格式
2. 如果格式错误，使用`_extract_executable_sub_query`修复
3. 确保所有子查询都是可执行的

---

### 修复4：改进子查询生成逻辑，优先使用LLM生成的sub_query ✅

**位置**：`src/core/real_reasoning_engine.py` 第2948-3006行

**修复**：
1. 优先使用LLM生成的`sub_query`字段
2. 如果`sub_query`为空或格式错误，才使用`_extract_executable_sub_query`
3. 验证子查询格式，确保可执行

---

## 实施步骤

1. **改进`_extract_executable_sub_query`方法**：
   - 改进疑问词检测逻辑
   - 避免重复添加疑问词
   - 处理更多格式

2. **改进LLM提示词**：
   - 强化子查询生成要求
   - 提供更多示例
   - 明确格式要求

3. **验证和修复LLM生成的sub_query**：
   - 添加验证逻辑
   - 自动修复格式错误
   - 确保可执行性

4. **改进子查询使用逻辑**：
   - 优先使用LLM生成的`sub_query`
   - 验证格式
   - 确保可执行

