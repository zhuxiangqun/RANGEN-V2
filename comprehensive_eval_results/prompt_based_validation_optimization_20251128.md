# 基于强化提示词的验证优化方案

**分析时间**: 2025-11-28  
**目标**: 用强化提示词替代硬编码和模式匹配的验证逻辑，提高智能化程度和可扩展性

---

## 📊 当前验证处理的问题

### 1. 硬编码验证逻辑

#### `_is_obviously_correct` 方法
- **问题**: 使用硬编码的格式检查
  - 人名查询：检查是否至少两个首字母大写的词
  - 数字查询：使用正则表达式 `r'^\d+(?:st|nd|rd|th)?(?:,\d{3})*(?:\.\d+)?$'`
  - 地点查询：检查是否包含大写字母
- **缺点**: 
  - 不易扩展（需要修改代码）
  - 非智能化（无法理解语义）
  - 可能误判（格式正确但语义错误）

#### `_validate_and_correct_answer_type` 方法
- **问题**: 使用正则表达式和硬编码规则
  - 数值查询：使用 `re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', answer_clean)`
  - 排名查询：使用 `re.search(r'\b(\d+(?:st|nd|rd|th))\b', answer, re.IGNORECASE)`
  - 人名查询：检查是否是数字
- **缺点**: 
  - 模式匹配无法处理复杂情况
  - 硬编码规则难以覆盖所有场景
  - 无法理解语义和上下文

#### `_needs_format_normalization` 方法
- **问题**: 使用硬编码的格式检查
  - 排名查询：检查是否已经是序数格式
  - 数值查询：检查是否包含多余的文字
  - 人名查询：检查是否包含多余的前缀
- **缺点**: 
  - 规则固定，无法适应新场景
  - 无法理解语义

### 2. 模式匹配验证逻辑

#### `_extract_with_patterns` 方法
- **问题**: 使用正则表达式匹配答案
  - 查找 "FINAL ANSWER:" 标记
  - 使用多个硬编码的正则表达式模式
- **缺点**: 
  - 无法处理格式变化
  - 无法理解语义

---

## 🎯 强化提示词方案

### 核心思想

**将验证逻辑集成到主答案生成的提示词中**，让LLM在生成答案时同时完成验证，而不是在生成后进行验证。

### 优势

1. **智能化**: LLM可以理解语义和上下文，而不是依赖硬编码规则
2. **可扩展**: 通过修改提示词模板即可扩展，无需修改代码
3. **减少处理**: 将验证集成到答案生成中，减少后续验证步骤
4. **统一性**: 验证逻辑与答案生成逻辑一致，避免不一致

---

## 📝 实施方案

### 方案1: 强化主答案生成提示词（推荐）

#### 1.1 增强提示词模板

在 `_generate_optimized_prompt` 方法中，为 "reasoning_with_evidence" 模板添加验证要求：

```python
# 在提示词中添加验证要求
validation_requirements = """
CRITICAL VALIDATION REQUIREMENTS:
1. Answer Format Validation:
   - For ranking queries: Return ordinal format (e.g., "37th" not "37")
   - For numerical queries: Return only the number (e.g., "87" not "87 years")
   - For name queries: Return complete name (e.g., "Jane Ballou" not "The person is Jane Ballou")
   - Remove any prefixes, explanations, or extra text

2. Answer Type Validation:
   - Ensure the answer type matches the query type
   - For numerical queries: Return only numbers, not names or places
   - For name queries: Return only names, not numbers
   - For ranking queries: Return only ordinal numbers

3. Answer Completeness Validation:
   - Ensure the answer is complete (e.g., full name, not just first name)
   - Ensure the answer directly answers the query
   - Do not include reasoning steps in the final answer

4. Answer Quality Validation:
   - Ensure the answer is based on the provided evidence
   - Ensure the answer is accurate and reasonable
   - If the answer cannot be determined from the evidence, return "unable to determine"

OUTPUT FORMAT:
- Use the format: "---\nFINAL ANSWER: [your answer here]\n---"
- The answer must be between the "---" markers
- The answer must be a single line (unless the query requires a full sentence)
- Do not include any explanations or reasoning after the answer
"""
```

#### 1.2 修改答案提取逻辑

简化 `_extract_answer_generic` 方法，因为答案已经在提示词中要求了正确的格式：

```python
def _extract_answer_generic(self, query: str, content: str, query_type: Optional[str] = None) -> Optional[str]:
    """简化版答案提取 - 因为提示词已经要求了正确格式"""
    # 1. 优先查找 "FINAL ANSWER:" 标记（提示词要求）
    pattern = r'---\s*\nFINAL ANSWER:\s*(.+?)(?=\n---|$)'
    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
    if matches:
        answer = matches[-1].strip()
        # 基本清理（移除多余空白）
        answer = re.sub(r'\s+', ' ', answer).strip()
        return answer if answer else None
    
    # 2. 如果找不到标记，尝试从响应末尾提取（LLM可能没有严格遵循格式）
    # 但这种情况应该很少，因为提示词已经明确要求了格式
    return None
```

#### 1.3 简化验证流程

由于答案已经在提示词中验证，可以大幅简化验证流程：

```python
# 在 _derive_final_answer_with_ml 中
if extracted_answer:
    # 1. 基本空值检查（必须）
    if not extracted_answer.strip():
        # 处理空答案
        pass
    
    # 2. 基本无效标记检查（必须）
    if self._is_invalid_marker(extracted_answer):
        # 处理无效答案
        pass
    
    # 3. 其他验证可以跳过或简化
    # 因为提示词已经要求了正确的格式和类型
    return extracted_answer
```

### 方案2: 使用LLM进行统一验证（备选）

如果方案1不够，可以在答案生成后使用一次LLM调用进行统一验证：

```python
def _validate_answer_with_llm(self, answer: str, query: str, query_type: str, evidence: str) -> Dict[str, Any]:
    """使用LLM进行统一验证（替代所有硬编码验证）"""
    prompt = f"""Validate the following answer for the given query.

Query: {query}
Query Type: {query_type}
Answer: {answer}
Evidence: {evidence[:1000]}

Please validate the answer and return a JSON response:
{{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "corrected_answer": "corrected answer if needed, or original answer",
    "reasons": ["reason1", "reason2"]
}}

Validation Criteria:
1. Answer format matches query type requirements
2. Answer type matches query type
3. Answer is complete and directly answers the query
4. Answer is based on the provided evidence
5. Answer is accurate and reasonable

JSON Response:"""
    
    response = self.fast_llm_integration._call_llm(prompt, dynamic_complexity="simple")
    # 解析JSON响应
    # 返回验证结果
```

---

## 🔄 迁移计划

### 阶段1: 强化提示词（立即实施）

1. **修改提示词模板**
   - 在 `_generate_optimized_prompt` 中添加验证要求
   - 要求LLM使用 "FINAL ANSWER:" 格式
   - 要求LLM在生成答案时完成格式和类型验证

2. **简化答案提取**
   - 优先查找 "FINAL ANSWER:" 标记
   - 移除复杂的模式匹配逻辑

3. **简化验证流程**
   - 保留基本空值检查
   - 保留基本无效标记检查
   - 移除格式验证（由提示词完成）
   - 移除类型验证（由提示词完成）

### 阶段2: 移除硬编码验证（逐步实施）

1. **移除 `_is_obviously_correct` 中的硬编码检查**
   - 保留证据匹配检查（语义相似度）
   - 移除格式检查

2. **移除 `_validate_and_correct_answer_type`**
   - 完全移除，因为提示词已经要求了正确的类型

3. **移除 `_needs_format_normalization`**
   - 完全移除，因为提示词已经要求了正确的格式

### 阶段3: 优化和测试（验证效果）

1. **测试验证效果**
   - 运行测试集，验证答案格式和类型正确性
   - 对比优化前后的准确率

2. **性能优化**
   - 如果方案2需要，考虑使用快速LLM进行验证
   - 优化提示词长度，减少token消耗

---

## 📈 预期效果

### 优势

1. **智能化提升**
   - LLM可以理解语义，而不是依赖硬编码规则
   - 可以处理复杂和边缘情况

2. **可扩展性提升**
   - 通过修改提示词模板即可扩展
   - 无需修改代码

3. **处理时间减少**
   - 减少验证步骤（从3-4步减少到1-2步）
   - 减少LLM调用次数（如果使用方案1）

4. **一致性提升**
   - 验证逻辑与答案生成逻辑一致
   - 避免不一致导致的错误

### 风险

1. **LLM可能不严格遵循格式要求**
   - 缓解措施：在提示词中强调格式要求
   - 保留基本的格式提取逻辑作为fallback

2. **提示词长度增加**
   - 缓解措施：优化提示词，只包含必要的验证要求
   - 使用快速LLM进行验证（如果使用方案2）

---

## 🎯 实施建议

### 优先级

1. **P0（高优先级）**: 强化主答案生成提示词
   - 立即实施，可以显著减少验证处理
   - 风险低，收益高

2. **P1（中优先级）**: 简化答案提取和验证流程
   - 在阶段1完成后实施
   - 进一步减少处理时间

3. **P2（低优先级）**: 移除硬编码验证逻辑
   - 在阶段2完成后实施
   - 需要充分测试

### 实施步骤

1. **第一步**: 修改提示词模板，添加验证要求
2. **第二步**: 简化答案提取逻辑
3. **第三步**: 简化验证流程
4. **第四步**: 测试和优化
5. **第五步**: 逐步移除硬编码验证逻辑

---

**报告生成时间**: 2025-11-28

