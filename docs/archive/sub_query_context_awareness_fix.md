# 子查询上下文感知修复

## 问题
用户指出："What is the complete name of my future wife?" 这种子查询问题感觉没头没脑的，找不到相应的证据。

## 根本原因

### 问题1：子查询没有引用前一步的结果 ⚠️ P0

**场景**：
- 原始查询："If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?"
- 第一步子查询："Who was the 15th first lady of the United States?" ✅ 正确
- 第二步子查询："What is the complete name of my future wife?" ❌ 错误 - 没有引用第一步的结果

**根本原因**：
1. LLM生成的推理步骤中，`sub_query`字段可能没有正确引用前一步的结果
2. 子查询增强逻辑（`_enhance_sub_query_with_previous_results`）不够智能，无法正确替换占位符
3. 子查询生成时没有考虑多跳推理的上下文

---

### 问题2：子查询增强逻辑不够智能 ⚠️ P0

**当前实现**：
- `_enhance_sub_query_with_previous_results`只是简单地在子查询前添加实体名称
- 无法处理关系查询（如"X's mother"）
- 无法替换子查询中的占位符（如"my future wife"）

**需要的改进**：
1. 从前一步的证据中提取答案（如"15th first lady = Edith Wilson"）
2. 替换子查询中的占位符（如"my future wife" -> "Edith Wilson's mother"）
3. 生成可执行的子查询（如"What is the first name of Edith Wilson's mother?"）

---

## 修复方案

### 修复1：改进子查询增强逻辑，正确引用前一步结果 ✅

**位置**：`src/core/real_reasoning_engine.py` 第3940-3983行

**修复**：
1. 从前一步的证据中提取答案（使用LLM提取）
2. 分析子查询，识别需要替换的占位符
3. 替换占位符，生成可执行的子查询

---

### 修复2：改进LLM提示词，要求生成可引用的子查询 ✅

**位置**：`src/core/real_reasoning_engine.py` 第10537-10550行

**修复**：
1. 在提示词中明确要求：子查询必须能够独立检索证据
2. 如果子查询需要引用前一步的结果，使用占位符（如"[STEP_1_RESULT]"）
3. 系统会自动替换占位符为前一步的实际结果

---

### 修复3：在子查询生成时检查是否包含无法检索的内容 ✅

**位置**：`src/core/real_reasoning_engine.py` 第2948-3032行

**修复**：
1. 检查子查询是否包含"my future wife"、"the answer"等无法检索的内容
2. 如果包含，尝试从前一步的结果中提取信息，替换这些占位符
3. 如果无法替换，使用原始查询或前一步的结果

---

## 实施步骤

1. **改进`_enhance_sub_query_with_previous_results`方法**：
   - 使用LLM从前一步的证据中提取答案
   - 分析子查询，识别占位符
   - 替换占位符，生成可执行的子查询

2. **改进子查询验证逻辑**：
   - 检查子查询是否包含无法检索的内容
   - 如果包含，自动替换为前一步的结果

3. **改进LLM提示词**：
   - 明确要求子查询必须能够独立检索证据
   - 如果需要引用前一步的结果，使用占位符

