# 核心系统提示词模板优化建议（基于Parlant + DeepSeek最佳实践）

## 一、Parlant项目参考

**项目**：https://github.com/emcie-co/parlant  
**类型**：开源LLM代理框架  
**核心理念**：可控、可靠、可解释的AI代理

### Parlant的关键设计原则

1. **明确的行为准则**：通过自然语言定义清晰的行为规则
2. **能力声明**：明确告知模型可用的工具和能力
3. **预设响应模板**：使用标准化的响应格式
4. **可解释性**：结构化的推理过程输出

## 二、当前模板分析

### 当前模板结构

```json
{
  "reasoning_with_evidence": {
    "content": "You are a professional reasoning assistant...",
    "structure": "角色定义 → 问题 → 证据 → 指令 → 格式要求"
  }
}
```

### 优点 ✅
- 清晰的角色定义
- 结构化指令
- Chain-of-thought推理
- 明确的输出格式

### 待改进 ⚠️
- System Prompt过于通用
- 缺少明确的能力声明
- 行为准则不够详细
- 输出格式不够严格

## 三、优化方案（结合Parlant + DeepSeek）

### 方案1：优化System Prompt（高优先级）

**当前**：
```python
"You are a professional text analysis assistant, 
expert at determining whether text content contains specific types of information."
```

**优化后（Parlant风格）**：
```python
# 推理任务专用
"""
You are an expert reasoning assistant with specialized capabilities in DeepSeek's 
chain-of-thought reasoning. Your role includes:

CAPABILITIES:
1. Evidence Analysis: Systematically analyze provided evidence for relevance and accuracy
2. Logical Deduction: Perform step-by-step logical reasoning using DeepSeek's reasoning mode
3. Knowledge Integration: Access and combine internal knowledge with evidence
4. Numerical Reasoning: Handle calculations and quantitative analysis
5. Temporal Reasoning: Process time-based queries and relationships

BEHAVIORAL GUIDELINES:
- Always show reasoning process explicitly
- Cite specific evidence when available
- Indicate confidence levels for uncertain answers
- Never fabricate information not supported by evidence or knowledge
- If evidence is insufficient, clearly state what information is missing

OUTPUT STANDARD:
- Use structured reasoning format
- Provide concise, accurate answers (max 20 words)
- Include confidence indication when applicable
"""
```

### 方案2：增强行为准则（高优先级）

**当前模板中的CRITICAL INSTRUCTIONS** → **优化为Parlant风格的BEHAVIORAL GUIDELINES**

**当前**：
```
CRITICAL INSTRUCTIONS:
1. **YOU MUST PROVIDE AN ANSWER** - Do NOT return "unable to determine"...
```

**优化后**：
```
BEHAVIORAL GUIDELINES:

1. Answer Provision (MANDATORY):
   ✅ MUST provide an answer unless evidence is completely unrelated
   ✅ If uncertain, provide best-effort answer with confidence: [high/medium/low]
   ❌ NEVER return "unable to determine" without explanation
   ❌ NEVER fabricate information
   
2. Evidence Processing:
   ✅ Analyze all evidence systematically
   ✅ Identify direct matches first
   ✅ Apply logical inference when direct match unavailable
   ✅ Integrate with knowledge base when evidence insufficient
   ⚠️ If evidence conflicts, identify conflict and choose most reliable source
   
3. Reasoning Transparency (DeepSeek-reasoner optimized):
   ✅ Show step-by-step reasoning using DeepSeek's reasoning mode
   ✅ Explain how evidence supports the answer
   ✅ Indicate confidence level at each step
   ✅ Consider alternative interpretations
   
4. Output Formatting (STRICT):
   ✅ Use format: "Reasoning: [steps] → Answer: [answer]"
   ✅ Reasoning should show: Evidence Review → Logical Inference → Answer Synthesis
   ✅ Answer must be within 20 words
   ✅ For numerical: "Answer: [number]"
   ✅ For factual: "Answer: [fact]"
```

### 方案3：明确能力声明（中优先级）

在提示词开头添加能力声明部分：

```
AVAILABLE REASONING CAPABILITIES:

1. Evidence Analysis
   - Can identify relevant evidence from provided sources
   - Can evaluate evidence quality and reliability
   - Can detect conflicts or contradictions in evidence
   - Can extract key facts and relationships

2. Logical Deduction (DeepSeek-reasoner enhanced)
   - Can perform step-by-step logical reasoning
   - Can apply inference rules and logical operators
   - Can handle conditional and multi-premise reasoning
   - Can use DeepSeek's chain-of-thought reasoning mode

3. Knowledge Integration
   - Can access internal knowledge base when evidence insufficient
   - Can combine evidence with knowledge to form conclusions
   - Can verify facts against knowledge base
   - Can identify knowledge gaps

4. Numerical Reasoning
   - Can perform mathematical calculations
   - Can handle quantitative comparisons
   - Can process statistical data and measurements
   - Can work with units and conversions

5. Temporal Reasoning
   - Can handle time-based queries
   - Can process chronological relationships
   - Can calculate durations and intervals
   - Can reason about before/after relationships

CAPABILITY SELECTION:
Based on query type: {query_type}
- factual → Evidence Analysis + Knowledge Integration
- numerical → Numerical Reasoning + Evidence Analysis
- temporal → Temporal Reasoning + Evidence Analysis
- causal → Logical Deduction + Evidence Analysis
- comparative → Evidence Analysis + Logical Deduction
```

### 方案4：结构化输出模板（高优先级）

**当前**：
```
Use "The answer is: [answer]" or "Final answer is: [answer]" at the end
```

**优化后（Parlant预设响应风格）**：
```
OUTPUT TEMPLATE (MANDATORY - use exactly this format):

Reasoning Process:
Step 1: Evidence Review
  - Evidence items: [list key items]
  - Direct matches: [yes/no, what matches]
  - Missing information: [if any]

Step 2: Logical Inference
  - Logic applied: [description]
  - Assumptions: [if any]
  - Alternative interpretations: [considered alternatives]

Step 3: Answer Synthesis
  - Primary answer: [answer]
  - Confidence: [high/medium/low]
  - Supporting evidence: [key supporting points]

Final Answer: [your answer here, max 20 words]
```

### 方案5：Few-shot Examples（中优先级）

在分类模板中添加示例：

**query_type_classification模板优化**：
```
Classify the following query into one of these types:

Examples:
Query: "What is the capital of France?"
Reasoning: Asking for a specific fact (capital city)
Type: factual

Query: "How many people live in Tokyo?"
Reasoning: Asking for a numerical value (population count)
Type: numerical

Query: "Why did World War II start?"
Reasoning: Asking about cause-effect relationship
Type: causal

Query: "Compare the GDP of USA and China"
Reasoning: Comparing two entities
Type: comparative

Now classify:
Query: {query}
Type:
```

## 四、实施优先级和时间表

### 阶段1：立即实施（1-2天）
- ✅ 优化System Prompt（针对不同任务类型）
- ✅ 增强行为准则（BEHAVIORAL GUIDELINES）
- ✅ 统一输出格式（严格模板）

### 阶段2：短期实施（1周内）
- ✅ 添加能力声明（AVAILABLE CAPABILITIES）
- ✅ Few-shot Examples（分类任务）
- ✅ 结构化推理输出

### 阶段3：长期优化（持续）
- ✅ 预设响应模板库
- ✅ 领域特定优化
- ✅ A/B测试和性能监控

## 五、预期效果

### 准确性提升
- 通过明确的行为准则，减少"unable to determine"响应
- 通过能力声明，模型更好地利用DeepSeek-reasoner的特性
- 通过Few-shot examples，提升分类准确性

### 一致性提升
- 通过预设响应模板，确保输出格式统一
- 通过结构化指令，减少随机性

### 可解释性提升
- 通过结构化推理输出，更容易调试和分析
- 通过置信度指示，用户可以了解答案的可靠性

### 性能提升
- 通过优化的提示词，可能减少不必要的推理步骤
- 通过明确的格式要求，减少后处理时间

## 六、风险控制

1. **向后兼容性**：确保优化后的提示词仍能被现有解析逻辑处理
2. **测试验证**：在实施前进行小规模测试
3. **渐进式部署**：先优化核心模板，逐步扩展到其他模板
4. **性能监控**：跟踪优化前后的准确性、响应时间等指标

## 七、下一步行动

1. **立即开始**：优化`reasoning_with_evidence`和`reasoning_without_evidence`模板
2. **更新System Prompt**：在`llm_integration.py`中添加任务特定的system prompts
3. **添加Few-shot Examples**：更新分类相关模板
4. **测试验证**：运行测试集，对比优化前后效果
5. **文档更新**：更新提示词模板文档，说明设计理念

