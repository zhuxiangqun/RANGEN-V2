# 提示词和max_tokens改进状态检查

**检查时间**: 2025-11-09  
**检查项**: 
1. 改进提示词，引导LLM优先输出答案
2. 动态调整 max_tokens

---

## ✅ 检查结果

### 1. 改进提示词，引导LLM优先输出答案

**状态**: ❌ **未完全实施**

**当前状态**:
- ✅ 提示词模板中已有 "Final Answer:" 的要求
- ✅ 提示词模板中已有答案格式要求
- ❌ **缺少明确的"优先输出答案"指令**

**当前提示词内容** (`templates/templates.json`):
```json
"OUTPUT TEMPLATE (MANDATORY):
Reasoning Process:
Step 1: Evidence Quality Assessment and Review (MANDATORY)
...
Step 3: Answer Synthesis
  - Primary answer: [answer]
  - Confidence: [high/medium/low]
  - Supporting evidence: [key supporting points]

Final Answer: [your answer here, max 20 words]"
```

**问题**:
- 提示词要求LLM按照 "Step 1 → Step 2 → Step 3 → Final Answer" 的顺序输出
- 如果推理过程很长，答案在最后，可能被截断
- **缺少"如果推理过程很长，可以在中间步骤中先给出初步答案，最后再确认最终答案"的指令**

**建议改进**:
```json
"重要要求：
1. **在推理过程的最后，明确给出最终答案**
2. 使用格式："最终答案是：[答案内容]"来标识答案
3. **如果推理过程很长，可以在中间步骤中先给出初步答案，最后再确认最终答案**
4. 即使推理过程被截断，也要确保答案已经输出"
```

---

### 2. 动态调整 max_tokens

**状态**: ❌ **未实施**

**当前状态**:
- ✅ `_get_max_tokens` 方法根据模型类型设置不同的默认值
- ❌ **没有根据查询复杂度动态调整**

**当前代码** (`src/core/llm_integration.py` 第190-204行):
```python
def _get_max_tokens(self, model: str) -> int:
    """Get max_tokens configuration from config center"""
    max_tokens_key = "MAX_TOKENS"
    # 推理模型：6000 tokens
    # 其他模型：2000 tokens
    default_max_tokens = 6000 if "reasoner" in model.lower() else 2000
    
    max_tokens = self._get_config_value("ai_ml", max_tokens_key, default_max_tokens)
    return int(max_tokens)
```

**问题**:
- 所有查询使用相同的 max_tokens（推理模型6000，其他2000）
- 简单问题可能不需要6000 tokens（浪费）
- 复杂问题可能需要更多tokens（可能仍然被截断）

**建议改进**:
```python
def _get_max_tokens(self, model: str, query_complexity: str = "medium") -> int:
    """根据查询复杂度动态调整max_tokens"""
    base_tokens = 6000 if "reasoner" in model.lower() else 2000
    
    if query_complexity == "complex":
        return int(base_tokens * 1.5)  # 复杂问题：9000 tokens
    elif query_complexity == "simple":
        return int(base_tokens * 0.8)  # 简单问题：4800 tokens
    else:
        return base_tokens  # 中等问题：6000 tokens
```

---

## 🚀 实施建议

### 改进1：改进提示词，引导LLM优先输出答案（P1）

**位置**: `templates/templates.json` - `reasoning_with_evidence` 和 `reasoning_without_evidence`

**改进内容**:
```json
"重要要求：
1. **在推理过程的最后，明确给出最终答案**
2. 使用格式："最终答案是：[答案内容]"来标识答案
3. **如果推理过程很长，可以在中间步骤中先给出初步答案，最后再确认最终答案**
4. 即使推理过程被截断，也要确保答案已经输出

OUTPUT TEMPLATE (MANDATORY):
Reasoning Process:
Step 1: Evidence Quality Assessment and Review (MANDATORY)
...
Step 3: Answer Synthesis
  - Primary answer: [answer]
  - Confidence: [high/medium/low]
  - Supporting evidence: [key supporting points]
  - **IMPORTANT**: If reasoning process is long, you can provide a preliminary answer here, then confirm in Final Answer

Final Answer: [your answer here, max 20 words]
**CRITICAL**: Ensure the answer is provided even if the reasoning process is truncated"
```

**预期效果**:
- LLM会在推理过程中优先输出答案
- 即使推理过程被截断，答案也可能已经输出
- 减少截断的影响

---

### 改进2：动态调整 max_tokens（P1）

**位置**: `src/core/llm_integration.py` - `_get_max_tokens` 方法

**改进内容**:
```python
def _get_max_tokens(self, model: str, query_complexity: str = None) -> int:
    """根据查询复杂度动态调整max_tokens
    
    Args:
        model: 模型名称
        query_complexity: 查询复杂度 ("simple", "medium", "complex")
                        如果为None，使用默认值
    """
    max_tokens_key = "MAX_TOKENS"
    base_tokens = 6000 if "reasoner" in model.lower() else 2000
    
    # 如果提供了查询复杂度，动态调整
    if query_complexity:
        if query_complexity == "complex":
            adjusted_tokens = int(base_tokens * 1.5)  # 复杂问题：9000 tokens
        elif query_complexity == "simple":
            adjusted_tokens = int(base_tokens * 0.8)  # 简单问题：4800 tokens
        else:
            adjusted_tokens = base_tokens  # 中等问题：6000 tokens
    else:
        adjusted_tokens = base_tokens
    
    max_tokens = self._get_config_value("ai_ml", max_tokens_key, adjusted_tokens)
    self.logger.debug(f"Using max_tokens: {max_tokens} (model: {self.model}, complexity: {query_complexity})")
    return int(max_tokens)
```

**调用方式**:
```python
# 在 _call_deepseek 中调用
query_complexity = self._estimate_query_complexity(prompt)  # 需要实现这个方法
max_tokens = self._get_max_tokens(self.model, query_complexity)
```

**需要实现的方法**:
```python
def _estimate_query_complexity(self, prompt: str) -> str:
    """估算查询复杂度
    
    简单启发式方法：
    - 简单问题：短查询，单一事实问题
    - 中等问题：中等长度，需要一些推理
    - 复杂问题：长查询，多步骤推理，复杂逻辑
    """
    prompt_length = len(prompt)
    word_count = len(prompt.split())
    
    # 简单启发式：根据长度和关键词判断
    if prompt_length < 100 and word_count < 20:
        return "simple"
    elif prompt_length > 500 or word_count > 100:
        return "complex"
    else:
        return "medium"
```

**预期效果**:
- 简单问题使用较少tokens（节省成本和时间）
- 复杂问题使用更多tokens（避免截断）
- 提高资源利用效率

---

## 📊 实施优先级

### P0（已完成）
- ✅ 增加max_tokens，避免推理内容被截断（推理模型6000，其他2000）

### P1（待实施）
- ⏳ 改进提示词，引导LLM优先输出答案
- ⏳ 动态调整 max_tokens

---

## ✅ 总结

**当前状态**:
- ❌ 改进提示词，引导LLM优先输出答案：**未完全实施**
- ❌ 动态调整 max_tokens：**未实施**

**建议**:
- 优先实施提示词改进（P1），引导LLM优先输出答案
- 然后实施动态调整 max_tokens（P1），提高资源利用效率

---

*本检查基于2025-11-09的代码审查生成*

