# Parlant项目提示词最佳实践分析

## Parlant项目简介

**项目链接**：https://github.com/emcie-co/parlant

**项目描述**：Parlant是一个开源的对话式大型语言模型（LLM）代理框架，旨在帮助开发者快速创建符合业务需求的AI代理。

## Parlant的核心设计理念

### 1. **行为准则（Guidelines）**
- 通过自然语言定义代理在特定情境下应采取的行动
- 确保行为的一致性和可预测性
- **关键点**：使用清晰、具体的规则，而不是模糊的指令

### 2. **工具使用（Tool Use）**
- 将外部API、数据获取器或后端服务与特定的交互事件关联
- 增强代理的功能性
- **关键点**：明确可用的工具和调用时机

### 3. **领域适应（Domain Adaptation）**
- 教授代理特定领域的术语和响应方式
- 提供更专业的服务
- **关键点**：针对不同领域定制语言和知识

### 4. **预设响应（Canned Responses）**
- 使用响应模板
- 消除幻觉，确保风格一致性
- **关键点**：为常见场景准备标准回复

### 5. **可解释性（Explainability）**
- 确保代理的行为可追溯、可解释
- 提供清晰的行为依据
- **关键点**：输出包含推理过程

## Parlant对当前系统的启示

### 当前系统的优点 ✅

1. ✅ **结构化指令**：使用了清晰的步骤化指令
2. ✅ **输出格式规范**：指定了答案格式要求
3. ✅ **角色定义**：定义了"professional reasoning assistant"

### 可以借鉴Parlant的改进方向

#### 1. **更明确的行为准则（Guidelines）**

**当前**：
```
CRITICAL INSTRUCTIONS:
1. **YOU MUST PROVIDE AN ANSWER** - Do NOT return "unable to determine"...
```

**Parlant方式**（建议改进）：
```
BEHAVIORAL GUIDELINES:
1. Answer Provision (MANDATORY):
   - MUST provide an answer in all cases except when evidence is completely unrelated
   - If evidence is unrelated, explain why and what information would be needed
   - NEVER return generic responses like "unable to determine" without explanation

2. Evidence Handling:
   - Always cite specific evidence when available
   - If evidence conflicts, identify the conflict and choose the most reliable source
   - If evidence is insufficient, clearly state what is missing

3. Reasoning Transparency:
   - Show your reasoning process explicitly
   - Explain how you arrived at your answer
   - If uncertain, indicate confidence level
```

#### 2. **工具/能力明确化**

**当前**：提示词中没有明确说明可用的能力

**Parlant方式**（建议添加）：
```
AVAILABLE CAPABILITIES:
1. Evidence Analysis: Can analyze provided evidence for relevance and accuracy
2. Knowledge Retrieval: Can access internal knowledge base when evidence is insufficient
3. Logical Reasoning: Can perform step-by-step logical deduction
4. Mathematical Calculation: Can perform numerical calculations
5. Temporal Reasoning: Can handle time-based queries and relationships

USE APPROPRIATE CAPABILITIES based on the query type:
- Factual queries → Evidence Analysis + Knowledge Retrieval
- Numerical queries → Mathematical Calculation + Evidence Analysis
- Temporal queries → Temporal Reasoning + Evidence Analysis
```

#### 3. **领域术语和上下文适应**

**当前**：通用提示词，没有针对特定领域的优化

**Parlant方式**（建议添加）：
```
DOMAIN CONTEXT:
- Use domain-appropriate terminology
- Consider domain-specific constraints and requirements
- Adapt reasoning style to domain (e.g., scientific rigor for science queries)

{context_summary}  # 已有但可以更结构化
{keywords}  # 已有但可以更结构化
```

#### 4. **预设响应模板**

**当前**：没有预设响应机制

**Parlant方式**（建议添加）：
```
STANDARD RESPONSE TEMPLATES:

For numerical answers:
"Answer: [number]" or "Answer: [number] [unit]"

For factual answers:
"Answer: [fact]" (maximum 20 words)

For comparative answers:
"Answer: [entity1] is [comparison] than [entity2]"

For causal answers:
"Answer: [cause] leads to [effect]"
```

#### 5. **可解释性增强**

**当前**：有推理步骤，但不够结构化

**Parlant方式**（建议改进）：
```
EXPLANATION STRUCTURE:

Step 1: Evidence Review
  - Evidence items analyzed: [list]
  - Relevant items: [list]
  - Irrelevant items (and why): [list]

Step 2: Reasoning Process
  - Logic applied: [description]
  - Assumptions made: [list]
  - Alternative interpretations considered: [list]

Step 3: Answer Synthesis
  - Primary answer: [answer]
  - Confidence level: [high/medium/low]
  - Supporting evidence: [references]
```

## 针对DeepSeek的具体优化建议

### 结合Parlant和DeepSeek的特点

#### 1. **System Prompt优化**（Parlant风格 + DeepSeek优化）

**当前**：
```python
"You are a professional text analysis assistant, expert at determining whether text content contains specific types of information."
```

**优化后**（结合Parlant的明确性 + DeepSeek的特性）：
```python
# 推理任务专用
"You are an expert reasoning assistant specialized in DeepSeek's chain-of-thought reasoning capabilities. 
Your role is to:
- Analyze questions and evidence systematically
- Apply step-by-step logical reasoning
- Provide accurate, well-supported answers
- Explain your reasoning process clearly

You have access to:
- Evidence provided by the user
- Internal knowledge base (when evidence is insufficient)
- Advanced reasoning capabilities (DeepSeek-reasoner)

Guidelines:
- Always show your reasoning process
- Cite specific evidence when available
- Indicate confidence levels
- Never fabricate information"
```

#### 2. **结构化行为准则**（Parlant方式）

**优化后的CRITICAL INSTRUCTIONS**：
```
BEHAVIORAL GUIDELINES:

1. Answer Provision (CRITICAL):
   ✅ MUST provide an answer unless evidence is completely unrelated
   ✅ If uncertain, provide best-effort answer with confidence indication
   ❌ NEVER return "unable to determine" without explanation
   
2. Evidence Processing:
   ✅ Analyze all provided evidence systematically
   ✅ Identify direct matches first
   ✅ Apply logical inference when direct match unavailable
   ✅ Integrate with knowledge base when evidence insufficient
   
3. Reasoning Transparency:
   ✅ Show step-by-step reasoning process
   ✅ Explain how evidence supports the answer
   ✅ Indicate which steps had high/low confidence
   
4. Output Formatting:
   ✅ Use specified format: "Reasoning: [steps] → Answer: [answer]"
   ✅ Keep reasoning concise but complete
   ✅ Answer should be within 20 words
```

#### 3. **能力声明**（Parlant工具使用方式）

在提示词中明确声明可用能力：
```
AVAILABLE REASONING CAPABILITIES:

1. Evidence Analysis
   - Can identify relevant evidence
   - Can evaluate evidence quality
   - Can detect conflicts in evidence

2. Logical Deduction
   - Can perform step-by-step reasoning
   - Can apply logical rules
   - Can handle conditional reasoning

3. Knowledge Integration
   - Can access internal knowledge base
   - Can combine evidence with knowledge
   - Can verify facts against knowledge

4. Numerical Reasoning
   - Can perform calculations
   - Can handle quantitative comparisons
   - Can process statistical data

SELECT APPROPRIATE CAPABILITIES based on query type: {query_type}
```

#### 4. **预设响应增强**

添加更明确的输出模板：
```
OUTPUT TEMPLATE (MANDATORY):

For questions with evidence:
Reasoning:
  Step 1: Evidence Analysis → [findings]
  Step 2: Logical Inference → [process]
  Step 3: Knowledge Integration → [if needed]
Answer: [your answer]

For questions without evidence:
Reasoning:
  Step 1: Query Understanding → [analysis]
  Step 2: Knowledge Retrieval → [relevant knowledge]
  Step 3: Answer Synthesis → [conclusion]
Answer: [your answer]
```

## 实施优先级

### 高优先级（立即实施）
1. ✅ **优化System Prompt**：针对不同任务类型
2. ✅ **结构化行为准则**：使用Parlant的Guidelines方式
3. ✅ **明确能力声明**：告诉模型可用的能力

### 中优先级（短期实施）
4. ✅ **增强输出格式**：更严格的模板
5. ✅ **预设响应模板**：常见场景的标准回复
6. ✅ **可解释性增强**：更结构化的推理过程

### 低优先级（长期优化）
7. ✅ **领域适应**：针对不同领域的定制
8. ✅ **动态工具声明**：根据查询类型动态调整
9. ✅ **响应模板库**：建立常用响应模板库

## 与当前系统的对比

| 特性 | 当前系统 | Parlant方式 | 改进效果 |
|------|---------|------------|---------|
| 行为准则 | 基础指令 | 结构化Guidelines | 更高一致性 |
| 能力声明 | 隐式 | 显式声明 | 更好利用能力 |
| 输出格式 | 灵活 | 严格模板 | 更易解析 |
| 可解释性 | 基础 | 结构化 | 更易调试 |
| 领域适应 | 通用 | 可定制 | 更专业 |

## 总结

通过借鉴Parlant项目的设计理念，我们可以：

1. **提高一致性**：通过明确的行为准则
2. **增强可解释性**：通过结构化的推理输出
3. **优化用户体验**：通过预设响应和清晰的格式
4. **提升准确性**：通过明确的能力声明和工具使用指导

这些改进将使核心系统的提示词模板更符合现代LLM代理框架的最佳实践，同时充分利用DeepSeek模型（特别是deepseek-reasoner）的推理能力。

