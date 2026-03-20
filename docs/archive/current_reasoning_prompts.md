# 当前使用的推理链生成提示词

生成时间: 2025-12-04

## 一、提示词使用流程

系统使用提示词的优先级：

1. **优先使用模板提示词**（`templates/templates.json`）
   - 通过 `prompt_generator.generate_optimized_prompt("reasoning_steps_generation", ...)`
   - 使用 `prompt_engineering.generate_prompt()` 从模板生成
   - 模板名称: `"reasoning_steps_generation"`

2. **如果模板失败，使用 Fallback 提示词**
   - 通过 `_get_fallback_reasoning_steps_prompt()` 方法
   - 这是硬编码在 `step_generator.py` 中的提示词

## 二、模板提示词（templates/templates.json）

**模板名称**: `reasoning_steps_generation`

**提示词内容**:
```
You are a reasoning expert. Your task is to break down a complex query into a series of logical, sequential, and executable sub-questions.

Query: {query}
Context: {context}
Evidence (if any): {evidence}

**CRITICAL REQUIREMENTS - READ CAREFULLY**:

1. **MANDATORY: Break down the query into explicit sub-problems**
   - DO NOT simply restate the original query
   - DO NOT combine multiple questions into one step
   - For queries with multiple conditions (e.g., "A and B"), you MUST create separate steps for each condition
   - Example: If asked "What is X and what is Y?", create:
     * Step 1: "What is X?" (sub-problem A)
     * Step 2: "What is Y?" (sub-problem B)
     * Step 3: Combine results from Step 1 and Step 2

2. **Each step must be a SINGLE, EXECUTABLE sub-question**
   - Each sub_query must be a pure question that can be used to search the knowledge base
   - Format: "What is...?", "Who is...?", "Where is...?", etc.
   - DO NOT include answers, reasoning, or explanations in the sub_query
   - DO NOT include multiple questions in one sub_query (e.g., "What is X and what is Y?")
   - DO NOT include reasoning statements (e.g., "The 15th president was James Buchanan...")

3. **Sequential and logical progression**
   - Each step should build on the previous one
   - Use results from previous steps when needed
   - Example: Step 1 finds "Harriet Lane", Step 2 asks "Who was Harriet Lane's mother?"

4. **Complete reasoning chain**
   - Include ALL intermediate steps needed to answer the query
   - For multi-hop queries, each hop must be a separate step
   - Example for "What is the first name of the 15th first lady's mother?":
     * Step 1: "Who was the 15th president of the United States?"
     * Step 2: "Who was the first lady during the 15th president's term?"
     * Step 3: "Who was [first lady's name]'s mother?"
     * Step 4: "What is [mother's name]'s first name?"

5. **Final step: Answer synthesis**
   - Combine results from previous steps
   - Mark the final answer clearly

Return in JSON format:
{"steps": [
  {
    "type": "step_type (evidence_gathering, query_analysis, logical_deduction, answer_synthesis, etc.)",
    "description": "Brief description of what this step does (e.g., 'Find the 15th president of the United States')",
    "sub_query": "A SINGLE, PURE question for this step (e.g., 'Who was the 15th president of the United States?') - NO answers, NO reasoning, NO multiple questions",
    "reasoning": "Why this step is necessary and how it connects to previous steps (optional)",
    "confidence": 0.8
  }
]}

**IMPORTANT EXAMPLES**:

❌ WRONG - Do NOT do this:
- Step 1: sub_query: "What is the first name of the 15th first lady's mother and the maiden name of the second assassinated president's mother?" (Multiple questions in one)
- Step 2: sub_query: "What is the 15th first lady of the United States. The 15th president was James Buchanan..." (Contains reasoning/answers)

✅ CORRECT - Do this instead:
- Step 1: sub_query: "Who was the 15th president of the United States?"
- Step 2: sub_query: "Who was the first lady during the 15th president's term?"
- Step 3: sub_query: "Who was [first lady's name]'s mother?"
- Step 4: sub_query: "What is [mother's name]'s first name?"
- Step 5: sub_query: "Who was the second assassinated president of the United States?"
- Step 6: sub_query: "Who was [president's name]'s mother?"
- Step 7: sub_query: "What is [mother's name]'s maiden name?"
- Step 8: sub_query: "What is the full name combining [first name from Step 4] and [maiden name from Step 7]?"

Reasoning steps (JSON):
```

## 三、Fallback 提示词（step_generator.py）

**方法**: `_get_fallback_reasoning_steps_prompt()`

**提示词内容**:
```
You are a reasoning expert. Your task is to break down a complex query into a series of logical, sequential, and executable sub-questions.

Query: {query}

**CRITICAL REQUIREMENTS - READ CAREFULLY**:

1. **MANDATORY: Break down the query into explicit sub-problems**
   - DO NOT simply restate the original query
   - DO NOT combine multiple questions into one step
   - For queries with multiple conditions (e.g., "A and B"), you MUST create separate steps for each condition
   - Example: If asked "What is X and what is Y?", create:
     * Step 1: "What is X?" (sub-problem A)
     * Step 2: "What is Y?" (sub-problem B)
     * Step 3: Combine results from Step 1 and Step 2

2. **Each step must be a SINGLE, EXECUTABLE sub-question**
   - Each sub_query must be a pure question that can be used to search the knowledge base
   - Format: "What is...?", "Who is...?", "Where is...?", etc.
   - DO NOT include answers, reasoning, or explanations in the sub_query
   - DO NOT include multiple questions in one sub_query (e.g., "What is X and what is Y?")
   - DO NOT include reasoning statements (e.g., "The 15th president was James Buchanan...")

3. **Sequential and logical progression**
   - Each step should build on the previous one
   - Use results from previous steps when needed
   - Example: Step 1 finds "Harriet Lane", Step 2 asks "Who was Harriet Lane's mother?"

4. **Complete reasoning chain**
   - Include ALL intermediate steps needed to answer the query
   - For multi-hop queries, each hop must be a separate step
   - Example for "What is the first name of the 15th first lady's mother?":
     * Step 1: "Who was the 15th president of the United States?"
     * Step 2: "Who was the first lady during the 15th president's term?"
     * Step 3: "Who was [first lady's name]'s mother?"
     * Step 4: "What is [mother's name]'s first name?"

5. **Final step: Answer synthesis**
   - Combine results from previous steps
   - Mark the final answer clearly

Return in JSON format:
{"steps": [
  {
    "type": "step_type (evidence_gathering, query_analysis, logical_deduction, answer_synthesis, etc.)",
    "description": "Brief description of what this step does (e.g., 'Find the 15th president of the United States')",
    "sub_query": "A SINGLE, PURE question for this step (e.g., 'Who was the 15th president of the United States?') - NO answers, NO reasoning, NO multiple questions",
    "reasoning": "Why this step is necessary and how it connects to previous steps (optional)",
    "confidence": 0.8
  }
]}

**IMPORTANT EXAMPLES**:

❌ WRONG - Do NOT do this:
- Step 1: sub_query: "What is the first name of the 15th first lady's mother and the maiden name of the second assassinated president's mother?" (Multiple questions in one)
- Step 2: sub_query: "What is the 15th first lady of the United States. The 15th president was James Buchanan..." (Contains reasoning/answers)

✅ CORRECT - Do this instead:
- Step 1: sub_query: "Who was the 15th president of the United States?"
- Step 2: sub_query: "Who was the first lady during the 15th president's term?"
- Step 3: sub_query: "Who was [first lady's name]'s mother?"
- Step 4: sub_query: "What is [mother's name]'s first name?"
- Step 5: sub_query: "Who was the second assassinated president of the United States?"
- Step 6: sub_query: "Who was [president's name]'s mother?"
- Step 7: sub_query: "What is [mother's name]'s maiden name?"
- Step 8: sub_query: "What is the full name combining [first name from Step 4] and [maiden name from Step 7]?"

Reasoning steps (JSON):
```

## 四、提示词关键要求

### 4.1 必须拆解问题
- ❌ 禁止简单重复原问题
- ❌ 禁止将多个问题合并为一个步骤
- ✅ 对于包含多个条件的问题，必须为每个条件创建单独的步骤

### 4.2 子查询格式要求
- ✅ 每个子查询必须是单一、可执行的问题
- ❌ 禁止包含答案、推理或解释
- ❌ 禁止包含多个问题
- ❌ 禁止包含推理陈述

### 4.3 顺序和逻辑
- ✅ 每个步骤应该基于前一步的结果
- ✅ 包含所有中间步骤

### 4.4 提供示例
- ❌ 明确展示什么是不应该做的
- ✅ 明确展示什么是应该做的

---

**报告生成时间**: 2025-12-04

