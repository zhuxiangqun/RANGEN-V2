# DeepSeek提示词模板优化分析

## 当前提示词模板分析

### 1. 核心推理模板

#### `reasoning_with_evidence` 模板
```
You are a professional reasoning assistant. Your task is to answer the question based on the provided evidence.

Question: {query}

Evidence:
{evidence}

{context_summary}

{keywords}

CRITICAL INSTRUCTIONS:
1. **YOU MUST PROVIDE AN ANSWER** - Do NOT return "unable to determine" unless...
2. **Reasoning Process**: Think step by step:
   a) First, check if the evidence directly contains the answer
   b) If not, try to infer the answer from the evidence using logical reasoning
   c) If the evidence is insufficient, use your own knowledge to reason about the question
   d) Always try to provide the most likely answer based on available information
3. **Answer Format**: Use "The answer is: [answer]" or "Final answer is: [answer]" at the end
4. **Answer Requirements**:
   - Keep it concise (within 20 words)
   - Return only the answer, no explanation (except the answer identifier)
   - For numerical answers, return the number directly
   - For names/locations, return the complete name

REMEMBER: Your goal is to find the answer, not to give up. Even if you're not 100% certain, provide your best reasoning result.
```

### 2. 系统提示词

**当前系统提示词**（`src/core/llm_integration.py`）：
```python
self.system_prompt = (
    "You are a professional text analysis assistant, "
    "expert at determining whether text content contains specific types of information."
)
```

## DeepSeek最佳实践对比

### ✅ 当前模板的优点

1. **清晰的角色定义**：✅ "You are a professional reasoning assistant"
2. **结构化指令**：✅ 使用编号和步骤化指令
3. **明确输出格式**：✅ 指定了答案格式
4. **Chain-of-thought推理**：✅ 包含"Think step by step"
5. **具体约束**：✅ 明确的答案要求（20词内、直接返回等）

### ⚠️ 可以改进的地方

基于DeepSeek模型的特点（特别是`deepseek-reasoner`），以下方面可以优化：

#### 1. **System Prompt不够具体**

**当前**：
```python
"You are a professional text analysis assistant, expert at determining whether text content contains specific types of information."
```

**问题**：
- 过于通用，不够聚焦推理任务
- 对于推理模型（deepseek-reasoner），应该更强调推理能力

**建议优化**：
```python
# 针对推理任务
"You are an expert reasoning assistant specialized in logical deduction, evidence analysis, and step-by-step problem solving. You excel at breaking down complex questions into manageable steps and synthesizing answers from available information."

# 针对分类任务
"You are a precise classification assistant with expertise in semantic analysis. You accurately categorize queries and content based on their meaning, complexity, and intent."
```

#### 2. **缺少Few-shot Examples**

**问题**：
- 对于分类和特定任务，few-shot examples可以显著提升准确性
- DeepSeek对few-shot学习支持良好

**建议**：
```python
# 在query_type_classification模板中添加示例
"""
Classify the following query into one of these types:

Examples:
Query: "What is the capital of France?" → factual
Query: "How many people live in Tokyo?" → numerical
Query: "Why did World War II start?" → causal

Query: {query}
Type:
"""
```

#### 3. **Chain-of-thought不够结构化**

**当前**：
```
Think step by step:
a) First, check if the evidence directly contains the answer
b) If not, try to infer...
```

**问题**：
- 对于deepseek-reasoner，应该更明确地使用推理链格式
- 可以使用更结构化的推理框架

**建议优化**：
```
Reasoning Chain:
Step 1: Evidence Analysis
  - Review the provided evidence
  - Identify key facts and relationships
  - Check for direct answer matches

Step 2: Logical Inference
  - If direct answer not found, apply logical reasoning
  - Connect evidence points to form conclusions
  - Consider alternative interpretations

Step 3: Knowledge Integration
  - Combine evidence with your knowledge base
  - Validate consistency
  - Identify the most likely answer

Step 4: Answer Synthesis
  - Formulate concise answer
  - Ensure accuracy and completeness
```

#### 4. **输出格式不够严格**

**当前**：
```
Use "The answer is: [answer]" or "Final answer is: [answer]" at the end
```

**问题**：
- 格式不够统一，可能导致解析困难
- 缺少结构化输出选项

**建议优化**：
```
Output Format (strict):
- Start with "Reasoning:" for your thought process
- End with "Answer: [your answer]"
- For numerical answers: "Answer: [number]"
- For factual answers: "Answer: [fact]"
- Maximum 20 words for the answer

Example:
Reasoning: The evidence shows that Paris is mentioned as the capital. Based on my knowledge, Paris is indeed the capital of France.
Answer: Paris
```

#### 5. **缺少错误处理指导**

**建议添加**：
```
Error Handling:
- If evidence is contradictory, identify the conflict and choose the most reliable source
- If evidence is insufficient, clearly state what information is missing
- If multiple valid answers exist, identify all possibilities
- Never fabricate information not supported by evidence or knowledge
```

#### 6. **对于deepseek-reasoner的特殊优化**

**deepseek-reasoner**支持推理链输出，建议：

```
Reasoning Mode: Use explicit reasoning tokens when available
- Start with [reasoning] tag
- Provide step-by-step analysis
- End with [answer] tag

Format:
[reasoning]
Step 1: [analysis]
Step 2: [analysis]
Conclusion: [summary]
[/reasoning]

[answer]Your answer here[/answer]
```

## 优化建议总结

### 高优先级优化

1. **优化System Prompt**：针对不同任务类型使用更具体的system prompt
2. **添加Few-shot Examples**：在分类任务中添加示例
3. **结构化Chain-of-thought**：使用更清晰的推理步骤格式
4. **统一输出格式**：使用更严格、易于解析的输出格式

### 中优先级优化

5. **错误处理指导**：添加如何处理矛盾和不完整信息的指导
6. **推理链优化**：针对deepseek-reasoner使用推理标记
7. **任务特定优化**：根据查询类型动态调整提示词结构

### 低优先级优化

8. **元提示（Meta-prompting）**：让模型自己优化提示词
9. **自适应提示词**：根据历史表现调整提示词

## Parlant项目参考（已整合）

**项目链接**：https://github.com/emcie-co/parlant

Parlant是一个开源的对话式LLM代理框架，其核心设计理念已整合到本分析中：

### Parlant的核心理念

1. **行为准则（Guidelines）**：通过自然语言定义明确的规则和行为
2. **工具使用（Tool Use）**：明确声明可用的能力和工具
3. **领域适应（Domain Adaptation）**：针对特定领域定制术语和响应
4. **预设响应（Canned Responses）**：使用模板确保一致性和专业性
5. **可解释性（Explainability）**：提供清晰的行为依据和推理过程

### 与当前系统的对比

当前系统已经部分采用了Parlant的理念（如结构化指令），但可以进一步优化：

- ✅ **已有**：结构化指令、角色定义
- ⚠️ **待改进**：更明确的行为准则、能力声明、预设响应模板

## 参考资源

1. **DeepSeek官方文档**：建议查看官方API文档中的提示词示例
2. **Parlant项目**：https://github.com/emcie-co/parlant - LLM代理框架最佳实践
3. **Prompt Engineering最佳实践**：参考OpenAI、Anthropic等的研究
4. **开源项目**：如prompt-optimizer等工具可以参考
5. **社区实践**：GitHub上相关项目的提示词设计

## 实施建议

1. **分阶段优化**：先优化核心推理模板，然后逐步优化其他模板
2. **A/B测试**：对比优化前后的性能，确保改进有效
3. **保持兼容性**：确保优化后的提示词仍能被正确解析
4. **文档化**：记录每个优化点和效果

