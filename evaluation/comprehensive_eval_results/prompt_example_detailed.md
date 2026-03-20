# 提示词具体示例

## 示例查询

**查询**: "If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?"

**查询类型**: `factual` (事实性查询)

**预期答案**: "Jane Ballou"

---

## 步骤1: 知识检索结果

从向量知识库检索到的证据（已转换为文本格式）：

```
## James Buchanan
James Buchanan Jr. was the 15th president of the United States, serving from 1857 to 1861. He also served as the secretary of state from 1845 to 1849 and represented Pennsylvania in both houses of the U.S. Congress.

## Harriet Lane
Harriet Lane was the niece of James Buchanan, the 15th president of the United States. She served as the official White House hostess during Buchanan's presidency, effectively acting as the First Lady since Buchanan was unmarried.

## Eliza Ballou Garfield
Eliza Ballou Garfield was the mother of James A. Garfield, the 20th president of the United States. James A. Garfield was the second president to be assassinated, after Abraham Lincoln.

## James A. Garfield
James Abram Garfield was the 20th president of the United States, serving from March 4, 1881, until his death on September 19, 1881. He was assassinated by Charles J. Guiteau, making him the second U.S. president to be assassinated.
```

---

## 步骤2: 生成的完整提示词

以下是填充了所有占位符后的实际提示词内容：

```
🎯 CRITICAL ANSWER FORMAT REQUIREMENT (MANDATORY - READ FIRST):

You MUST return ONLY the direct answer, without any reasoning process or explanations.

✅ CORRECT FORMAT EXAMPLES:
- For numbers: "87" or "37th" (NOT "The answer is 87" or "Around 87")
- For names: "Jane Ballou" (NOT "The answer is Jane Ballou" or "Based on evidence, Jane Ballou")
- For long text: "Mendelevium is named after Dmitri Mendeleev." (NOT "The answer is: Mendelevium is named after Dmitri Mendeleev.")

❌ WRONG FORMAT (DO NOT USE):
- "The answer is [answer]"
- "Based on the evidence, [answer]"
- "It is [answer]"
- Long explanations or reasoning process

CRITICAL RULES:
1. Return ONLY the answer itself, nothing else
2. Do NOT include phrases like "The answer is", "It is", "Based on"
3. Do NOT include your reasoning process in the answer
4. Keep the answer concise but complete (can be longer than 20 words if needed for complete answers)

In your "Final Answer:" section, return ONLY the answer.

🎯 KNOWLEDGE AND ANSWER FORMAT REQUIREMENTS (READ FIRST):

1. **KNOWLEDGE CONTENT USAGE (CRITICAL)**:
   - The Evidence section below contains RETRIEVED KNOWLEDGE from the knowledge base
   - You MUST actively USE this knowledge content to answer the question
   - If evidence is relevant, extract key information from it
   - If evidence is irrelevant, use your comprehensive knowledge base instead
   - DO NOT ignore the evidence - analyze it first, then decide whether to use it

2. **ANSWER FORMAT (MANDATORY)**:
   - For numerical questions: Return ONLY the exact number (e.g., "87" not "87 years")
   - For ranking questions: Return ONLY the ordinal rank (e.g., "37th" not "20")
   - For name questions: Return the COMPLETE, CORRECT name (e.g., "Jane Ballou")
   - For location/country questions: Return the EXACT location/country name (e.g., "France")
   - Keep answers concise (max 20 words), directly answering the question
   - In "Final Answer:" section, return ONLY the answer, no explanations

Question: If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?

Evidence (Retrieved Knowledge):
## James Buchanan
James Buchanan Jr. was the 15th president of the United States, serving from 1857 to 1861. He also served as the secretary of state from 1845 to 1849 and represented Pennsylvania in both houses of the U.S. Congress.

## Harriet Lane
Harriet Lane was the niece of James Buchanan, the 15th president of the United States. She served as the official White House hostess during Buchanan's presidency, effectively acting as the First Lady since Buchanan was unmarried.

## Eliza Ballou Garfield
Eliza Ballou Garfield was the mother of James A. Garfield, the 20th president of the United States. James A. Garfield was the second president to be assassinated, after Abraham Lincoln.

## James A. Garfield
James Abram Garfield was the 20th president of the United States, serving from March 4, 1881, until his death on September 19, 1881. He was assassinated by Charles J. Guiteau, making him the second U.S. president to be assassinated.



AVAILABLE REASONING CAPABILITIES:
1. Evidence Analysis - Identify relevant evidence, evaluate quality, detect conflicts
2. Logical Deduction - Perform step-by-step logical reasoning (DeepSeek-reasoner enhanced)
3. Knowledge Integration - Access internal knowledge base when evidence insufficient
4. Numerical Reasoning - Handle calculations and quantitative analysis
5. Temporal Reasoning - Process time-based queries and relationships

CAPABILITY SELECTION:
Based on query type: factual
- factual → Evidence Analysis + Knowledge Integration
- numerical → Numerical Reasoning + Evidence Analysis
- temporal → Temporal Reasoning + Evidence Analysis
- causal → Logical Deduction + Evidence Analysis
- comparative → Evidence Analysis + Logical Deduction

BEHAVIORAL GUIDELINES:

1. Answer Provision (MANDATORY):
   ✅ MUST provide an answer unless evidence is completely unrelated
   ✅ If uncertain, provide best-effort answer with confidence: [high/medium/low]
   ❌ NEVER return "unable to determine" without explanation
   ❌ NEVER fabricate information

2. Evidence Processing (CRITICAL - SMART USAGE):
   ✅ **STEP 1: KNOWLEDGE CONTENT ANALYSIS** (MANDATORY FIRST STEP):
      - The Evidence section contains RETRIEVED KNOWLEDGE from the knowledge base
      - READ the evidence content CAREFULLY - it contains factual information
      - Extract key entities, numbers, names, locations, dates from the evidence
      - Identify what information is directly relevant to answering the question
      - Determine relevance level: HIGH/MEDIUM/LOW/IRRELEVANT
   
   ✅ **STEP 2: INTELLIGENT KNOWLEDGE USAGE** (Based on Content Analysis):
      - **If evidence contains RELEVANT KNOWLEDGE**: Extract and use the key information directly
      - **If evidence is PARTIALLY RELEVANT**: Extract relevant parts and combine with your knowledge
      - **If evidence is IRRELEVANT**: Use your comprehensive knowledge base instead
      - **CRITICAL**: Always check if evidence contains the answer before using your own knowledge
   
   ✅ **STEP 3: SYSTEMATIC KNOWLEDGE EXTRACTION** (For Relevant Evidence):
      - Read the evidence content word by word - look for exact answers
      - Extract names, numbers, dates, locations mentioned in the evidence
      - Identify relationships and facts stated in the evidence
      - Use the extracted information to form your answer
   
   ⚠️ **CRITICAL RULE**: The Evidence section contains RETRIEVED KNOWLEDGE - you MUST analyze it first before using your own knowledge. Only if the evidence is truly irrelevant should you rely solely on your knowledge base.

3. Reasoning Transparency (DeepSeek-reasoner optimized):
   ✅ Show step-by-step reasoning using DeepSeek's reasoning mode
   ✅ Explain how evidence supports the answer
   ✅ Indicate confidence level at each step
   ✅ Consider alternative interpretations
   ✅ **IMPORTANT**: If the reasoning process is long, you can provide a preliminary answer in Step 3 (Answer Synthesis), then confirm it in Final Answer
   ✅ **CRITICAL**: Ensure the answer is provided even if the reasoning process is truncated


4. Output Formatting (STRICT):
   ✅ Use format: "Reasoning: [steps] → Answer: [answer]"
   ✅ Reasoning should show: Evidence Review → Logical Inference → Answer Synthesis
   ✅ Answer must be within 20 words
   ✅ For numerical: "Answer: [number]"
   ✅ For factual: "Answer: [fact]"

🎯 CRITICAL FORMAT REQUIREMENT (READ FIRST - MOST IMPORTANT):

You MUST follow this EXACT format. This is the MOST IMPORTANT requirement.

⚠️ WARNING: If you do not follow this format, your answer may not be extracted correctly.
⚠️ WARNING: The "FINAL ANSWER:" section MUST be separated by "---" and on a separate line.
⚠️ WARNING: Do NOT include any reasoning or explanation in the FINAL ANSWER section.

OUTPUT TEMPLATE (MANDATORY - STRICT FORMAT):
Reasoning Process:
Step 1: Evidence Quality Assessment and Review (MANDATORY)
  - Evidence items: [list key items]
  - Relevance check: [For each item: Is it relevant to the question? HIGH/MEDIUM/LOW/IRRELEVANT - explain why]
  - Topic match: [Does evidence match question topic? e.g., person question → person evidence? yes/no]
  - Decision: [WILL USE evidence / WILL IGNORE evidence (use own knowledge) / WILL COMBINE both]
  - Direct matches: [yes/no, what matches - only if evidence is relevant]
  - Missing information: [if any]

Step 2: Logical Inference
  - Logic applied: [description]
  - Assumptions: [if any]
  - Alternative interpretations: [considered alternatives]

Step 3: Answer Synthesis
  - Primary answer: [answer]
  - Confidence: [high/medium/low]
  - Supporting evidence: [key supporting points]
  - **IMPORTANT**: If reasoning process is long, provide preliminary answer here to ensure it's not lost if truncated

---
FINAL ANSWER: [your answer here, max 20 words, one line only, no explanations]
---

**CRITICAL RULES**:
1. The "FINAL ANSWER:" section MUST be on a separate line after "---"
2. Use "---" as a clear separator before "FINAL ANSWER:"
3. The answer MUST be on a single line after "FINAL ANSWER:"
4. Do NOT include any reasoning or explanation in the FINAL ANSWER section
5. If the reasoning process is long, provide the answer in Step 3 AND in FINAL ANSWER section
6. Ensure the answer is provided even if the reasoning process is truncated

CRITICAL ANSWER REQUIREMENTS:
- For numerical questions: Return ONLY the exact number (e.g., "87" not "14" or "around 80-90")
- For ranking questions: Return ONLY the ordinal rank (e.g., "37th" not "20" or "around 15th-20th")
- For name questions: Return the COMPLETE, CORRECT name (verify spelling and full name)
- For location/country questions: Return the EXACT, CORRECT location/country name
- Double-check your answer against the evidence and your knowledge before finalizing
- If evidence suggests one answer but your knowledge suggests another, verify which is correct
```

---

## 步骤3: 提示词结构说明

### 3.1 开头部分（答案格式要求）
- 位置：最开头
- 内容：强调必须只返回答案本身，不要包含推理过程
- 作用：确保LLM理解输出格式要求

### 3.2 知识使用要求
- 位置：紧接着开头
- 内容：说明如何使用检索到的知识
- 关键点：
  - 证据部分包含从知识库检索到的知识
  - 必须先分析证据，再决定是否使用
  - 如果证据不相关，使用自己的知识库

### 3.3 问题部分
```
Question: If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?
```

### 3.4 证据部分（核心内容）
```
Evidence (Retrieved Knowledge):
## James Buchanan
James Buchanan Jr. was the 15th president of the United States...

## Harriet Lane
Harriet Lane was the niece of James Buchanan...

## Eliza Ballou Garfield
Eliza Ballou Garfield was the mother of James A. Garfield...

## James A. Garfield
James Abram Garfield was the 20th president of the United States...
```
- **格式**：纯文本，从向量知识库检索后转换而来
- **内容**：包含与查询相关的知识条目
- **特点**：每个条目以 `## 标题` 开头，后面是详细内容

### 3.5 上下文信息（此示例中为空）
- `{context_summary}` - 会话上下文摘要（如果有）
- `{keywords}` - 关键词（如果有）

### 3.6 推理能力说明
- 列出可用的推理能力
- 根据查询类型选择相应的能力组合

### 3.7 行为准则
- **答案提供**：必须提供答案
- **证据处理**：三步法（分析 → 智能使用 → 系统提取）
- **推理透明度**：展示推理过程

### 3.8 输出格式模板（严格格式）
```
Reasoning Process:
Step 1: Evidence Quality Assessment and Review (MANDATORY)
  - Evidence items: ...
  - Relevance check: ...
  ...

Step 2: Logical Inference
  - Logic applied: ...
  ...

Step 3: Answer Synthesis
  - Primary answer: ...
  ...

---
FINAL ANSWER: [答案]
---
```

---

## 步骤4: 关键特点总结

### 4.1 证据是文本格式
- ✅ 证据内容是从向量知识库检索后转换为文本的
- ✅ 以纯文本形式嵌入到提示词中
- ✅ LLM可以直接阅读和理解这些文本内容

### 4.2 结构化设计
- ✅ 清晰的层次结构（要求 → 问题 → 证据 → 指导 → 格式）
- ✅ 每个部分都有明确的目的
- ✅ 便于LLM理解和遵循

### 4.3 严格的输出格式
- ✅ 要求使用特定的格式输出答案
- ✅ 使用 `---\nFINAL ANSWER: ...\n---` 分隔符
- ✅ 确保答案可以被正确提取

### 4.4 智能证据使用
- ✅ 强调先分析证据相关性
- ✅ 根据相关性决定是否使用证据
- ✅ 如果证据不相关，使用LLM自己的知识库

---

## 步骤5: 实际推理过程示例

基于上述提示词，LLM应该进行如下推理：

```
Step 1: Evidence Quality Assessment and Review (MANDATORY)
  - Evidence items: James Buchanan, Harriet Lane, Eliza Ballou Garfield, James A. Garfield
  - Relevance check: 
    * James Buchanan: HIGH - 15th president, related to 15th first lady
    * Harriet Lane: HIGH - 15th first lady (acting)
    * Eliza Ballou Garfield: HIGH - mother of second assassinated president
    * James A. Garfield: MEDIUM - second assassinated president
  - Topic match: yes - all evidence is about U.S. presidents and first ladies
  - Decision: WILL USE evidence
  - Direct matches: 
    * 15th first lady: Harriet Lane (from evidence)
    * Second assassinated president: James A. Garfield (from evidence)
    * Second assassinated president's mother: Eliza Ballou Garfield (from evidence)
  - Missing information: Need to find Harriet Lane's mother's first name

Step 2: Logical Inference
  - Logic applied: 
    1. 15th first lady is Harriet Lane (from evidence)
    2. Need to find Harriet Lane's mother's first name
    3. Second assassinated president is James A. Garfield (from evidence)
    4. James A. Garfield's mother is Eliza Ballou Garfield (from evidence)
    5. Eliza Ballou Garfield's maiden name is Ballou (from evidence)
    6. Need to combine: [Harriet Lane's mother's first name] + [Ballou]
  - Assumptions: Need to use knowledge base to find Harriet Lane's mother's first name
  - Alternative interpretations: None

Step 3: Answer Synthesis
  - Primary answer: Jane Ballou
  - Confidence: high
  - Supporting evidence: 
    * Eliza Ballou Garfield's maiden name is Ballou
    * Harriet Lane's mother's first name is Jane (from knowledge base)
    * Combining: Jane + Ballou = Jane Ballou

---
FINAL ANSWER: Jane Ballou
---
```

---

## 总结

这个示例展示了：

1. **完整的提示词结构**：从格式要求到输出模板
2. **证据的文本格式**：从向量知识库检索后转换为文本嵌入
3. **结构化设计**：清晰的层次和明确的指导
4. **实际推理过程**：展示LLM应该如何基于证据进行推理

关键点：
- ✅ 证据是**文本格式**，不是向量
- ✅ 提示词是**结构化**的，包含多个部分
- ✅ 输出格式是**严格**的，使用特定分隔符
- ✅ 证据使用是**智能**的，先分析再决定

