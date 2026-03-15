# FRAMES准确率问题深度分析报告

**分析时间**: 2025-11-07  
**问题**: FRAMES准确率仅10.00%（10个样本中只有1个正确）

---

## 🔍 问题现象

### 当前状态

- **FRAMES准确率**: 10.00%
- **测试次数**: 10次
- **成功样本数**: 10个（成功率100%）
- **匹配样本数**: 1个（准确率10%）

### 关键发现

从日志分析中发现，**所有实际答案都是 "Reasoning Process:" 开头的长文本**，包含完整的推理过程，而不是简洁的答案。

**日志示例**:
```
FRAMES sample=1/10 success=True took=39.41s answer=Reasoning Process:
Step 1: Evidence Quality Assessment and Review
  - Evidence items: List of first ladies, references to Martha Jefferson, Rachel Jackson, etc.
  - Relevance check: LOW - The evidence provides general information...
  - Decision: WILL IGNORE evidence (use own knowledge)
```

**期望答案示例**:
```
期望答案: Jane Ballou
```

---

## 🔴 根本原因分析

### 问题1: 答案格式不匹配（核心问题）

#### 1.1 核心系统生成的答案格式

**实际生成的答案**:
- 格式: `Reasoning Process: Step 1: ... Step 2: ...`
- 内容: 包含完整的推理过程、证据评估、决策过程
- 长度: 通常数百到数千字符

**期望的答案格式**:
- 格式: 简洁的答案（如 "Jane Ballou"、"37th"、"2"）
- 内容: 只包含最终答案，不包含推理过程
- 长度: 通常1-50字符

#### 1.2 答案提取逻辑问题

**代码位置**: `evaluation_system/analyzers/frames_analyzer.py:553-587`

```python
def _extract_core_answer(self, full_answer: str) -> str:
    """从完整答案中提取核心答案"""
    # 1. 检查"分析要点 1"格式（中文格式）
    if "分析要点 1" in full_answer:
        # 提取第一个分析要点的内容
        ...
    
    # 2. 查找包含数字、人名、地名的短句
    sentences = full_answer.split('.')
    for sentence in sentences:
        if len(sentence) < 200 and self._is_likely_answer(sentence):
            return sentence
    
    # 3. 如果都找不到，返回前100个字符
    return full_answer[:100] + "..."
```

**问题**:
1. ❌ 没有处理 "Reasoning Process:" 格式
2. ❌ 没有处理 "Step 1:", "Step 2:" 格式
3. ❌ 提取逻辑主要针对中文格式（"分析要点 1"），但实际答案是英文格式
4. ❌ 如果找不到短句，只返回前100个字符，可能包含推理过程而非答案

#### 1.3 答案提取服务问题

**代码位置**: `src/utils/answer_normalization.py:32-76`

```python
def extract_core_answer(self, query: str, answer_content: str, query_type: Optional[str] = None) -> Optional[str]:
    """多层次智能提取核心答案"""
    # 层次1: LLM驱动的智能提取
    extracted = reasoning_engine._extract_answer_standard(query, answer_content, query_type=query_type)
    
    # 层次2: 模式匹配提取
    if not extracted:
        pattern_extracted = self._extract_by_patterns(query, answer_content, query_type)
    
    # 层次3: 关键词提取
    if not extracted:
        keyword_extracted = self._extract_by_keywords(query, answer_content, query_type)
```

**问题**:
1. ⚠️ 虽然有多层次提取，但可能无法从 "Reasoning Process:" 格式中提取答案
2. ⚠️ LLM提取可能失败，回退到模式匹配，但模式匹配可能也无法处理这种格式

---

### 问题2: 答案记录格式问题

**代码位置**: `scripts/run_core_with_frames.py:129`

```python
log_info(f"FRAMES sample={idx}/{total} success={success} took={elapsed:.2f}s answer={answer}")
```

**问题**:
- `answer` 变量直接来自 `result.answer`，可能包含完整的推理过程
- 虽然代码中有 `_extract_core_answer_intelligently` 提取核心答案，但提取后的答案记录在 `系统答案:` 日志中，而不是 `answer=` 字段

**日志格式**:
```
FRAMES sample=1/10 success=True took=39.41s answer=Reasoning Process: Step 1: ...
系统答案: Jane Ballou  ← 提取后的答案在这里
期望答案: Jane Ballou
```

**评测系统提取逻辑**:
- 评测系统只从 `answer=` 字段提取答案，**不提取 `系统答案:` 字段**
- 导致提取到的都是 "Reasoning Process:" 开头的长文本

---

### 问题3: 匹配逻辑问题

**代码位置**: `evaluation_system/analyzers/frames_analyzer.py:226-323`

虽然匹配逻辑很完善（13种匹配方法），但**如果提取的答案本身就是错误的（"Reasoning Process:"），再好的匹配逻辑也无法匹配**。

**匹配流程**:
```
期望答案: "Jane Ballou"
实际答案: "Reasoning Process: Step 1: ..."  ← 提取失败
  ↓
匹配逻辑尝试匹配
  ↓
无法匹配（"Jane Ballou" 不在 "Reasoning Process: ..." 中）
  ↓
匹配失败 → 准确率降低
```

---

## 📊 详细问题分解

### 问题A: 答案提取失败

**现象**: 从 "Reasoning Process: Step 1: ..." 中无法提取出 "Jane Ballou"

**原因**:
1. `_extract_core_answer` 方法没有处理 "Reasoning Process:" 格式
2. 答案可能隐藏在推理过程的某个步骤中，需要更智能的提取

**影响**: ⚠️ 严重 - 导致所有答案提取失败

### 问题B: 答案记录位置错误

**现象**: 提取后的答案记录在 `系统答案:` 中，但评测系统只从 `answer=` 字段提取

**原因**:
- 评测系统的正则表达式只匹配 `answer=` 字段
- 没有匹配 `系统答案:` 字段

**影响**: ⚠️ 严重 - 导致评测系统提取到错误的答案

### 问题C: 答案格式不统一

**现象**: 核心系统生成的是推理过程，而不是简洁答案

**原因**:
- 推理引擎可能没有按照期望格式生成答案
- 答案生成逻辑可能返回了完整的推理过程

**影响**: ⚠️ 中等 - 虽然可以提取，但增加了提取难度

---

## 🎯 解决方案

### 方案1: 修复答案提取逻辑（高优先级）

**目标**: 让评测系统能够从 "Reasoning Process:" 格式中提取答案

**实现**:

1. **增强 `_extract_core_answer` 方法**:
   - 添加对 "Reasoning Process:" 格式的处理
   - 添加对 "Step 1:", "Step 2:" 格式的处理
   - 从推理步骤中提取最终答案

2. **代码修改** (`evaluation_system/analyzers/frames_analyzer.py:553`):

```python
def _extract_core_answer(self, full_answer: str) -> str:
    """从完整答案中提取核心答案 - 增强版，支持Reasoning Process格式"""
    try:
        # 🚀 新增：处理 "Reasoning Process:" 格式
        if "Reasoning Process:" in full_answer or "reasoning process:" in full_answer.lower():
            # 尝试从推理过程中提取最终答案
            # 方法1: 查找 "Final Answer:", "Answer:", "答案是:" 等标记
            final_answer_patterns = [
                r'Final Answer[：:]\s*([^\n]+)',
                r'Answer[：:]\s*([^\n]+)',
                r'答案是[：:]\s*([^\n]+)',
                r'The answer is[：:]\s*([^\n]+)',
                r'最终答案[：:]\s*([^\n]+)',
            ]
            for pattern in final_answer_patterns:
                match = re.search(pattern, full_answer, re.IGNORECASE)
                if match:
                    answer = match.group(1).strip()
                    if answer and len(answer) < 200:
                        return answer
            
            # 方法2: 从最后一个Step中提取关键信息
            steps = re.split(r'Step \d+:', full_answer, flags=re.IGNORECASE)
            if len(steps) > 1:
                last_step = steps[-1]
                # 尝试提取人名、数字、地名等关键信息
                # ... 提取逻辑 ...
        
        # 原有逻辑（处理中文格式等）
        # ...
```

### 方案2: 修复答案记录格式（高优先级）

**目标**: 让评测系统能够从 `系统答案:` 字段提取答案

**实现**:

1. **修改答案提取正则表达式** (`evaluation_system/analyzers/frames_analyzer.py:154`):

```python
def _extract_actual_answers(self, log_content: str) -> List[str]:
    """从日志中提取实际答案 - 修复：优先使用系统答案字段"""
    answers = []
    
    # 🚀 修复：优先使用"系统答案:"字段（提取后的答案）
    system_answer_pattern = r"系统答案: ([^\n]+)"
    system_answers = re.findall(system_answer_pattern, log_content, re.IGNORECASE)
    
    if system_answers:
        # 使用系统答案（已提取的核心答案）
        for answer in system_answers:
            cleaned = answer.strip()
            if cleaned and len(cleaned) < 200:
                answers.append(cleaned)
    
    # 如果没有系统答案，回退到原有逻辑（从answer=字段提取）
    if not answers:
        answer_pattern = r"FRAMES sample=(\d+)/\d+ success=True took=[\d.]+s answer=\s*(.+?)(?=\n期望答案|\nFRAMES sample=|\n系统答案=|\Z)"
        matches = re.findall(answer_pattern, log_content, re.MULTILINE | re.DOTALL)
        matches.sort(key=lambda x: int(x[0]))
        
        for sample_num, answer in matches:
            cleaned_answer = answer.strip()
            core_answer = self._extract_core_answer(cleaned_answer)
            if core_answer:
                answers.append(core_answer)
            else:
                answers.append(cleaned_answer)
    
    return answers
```

### 方案3: 改进核心系统答案生成（中优先级）

**目标**: 让核心系统直接生成简洁答案，而不是推理过程

**实现**:
- 修改推理引擎的答案生成逻辑
- 确保 `result.answer` 字段包含简洁答案，而不是推理过程
- 推理过程可以记录在其他字段中（如 `result.reasoning`）

---

## 📋 实施优先级

### 🔴 P0 - 立即实施

1. **修复答案提取逻辑** - 方案1
   - 影响: 直接解决答案提取失败问题
   - 难度: 中等
   - 预期效果: 准确率从10%提升到30-50%

2. **修复答案记录格式** - 方案2
   - 影响: 直接解决答案记录位置错误问题
   - 难度: 低
   - 预期效果: 准确率从10%提升到50-70%

### 🟠 P1 - 高优先级

3. **改进核心系统答案生成** - 方案3
   - 影响: 从根本上解决问题
   - 难度: 高
   - 预期效果: 准确率进一步提升到70-90%

---

## 🧪 验证方法

### 测试步骤

1. **修复后重新运行评测**:
   ```bash
   ./scripts/run_core_with_frames.sh --sample-count 10
   ```

2. **检查日志**:
   - 确认 `系统答案:` 字段包含提取后的答案
   - 确认 `answer=` 字段或提取逻辑能正确提取答案

3. **验证准确率**:
   - 运行评测系统
   - 检查准确率是否提升

### 预期结果

- **修复前**: 准确率 10.00%
- **修复后（方案1+2）**: 准确率 50-70%
- **修复后（方案1+2+3）**: 准确率 70-90%

---

## 📝 总结

### 根本原因

1. **答案提取逻辑无法处理 "Reasoning Process:" 格式** ⚠️ 严重
2. **答案记录位置错误，评测系统提取不到正确答案** ⚠️ 严重
3. **核心系统生成的是推理过程而非简洁答案** ⚠️ 中等

### 解决方案

1. **增强答案提取逻辑** - 支持 "Reasoning Process:" 格式
2. **修复答案记录格式** - 优先使用 `系统答案:` 字段
3. **改进核心系统** - 直接生成简洁答案

### 预期效果

- **短期（方案1+2）**: 准确率从10%提升到50-70%
- **长期（方案1+2+3）**: 准确率提升到70-90%

---

*本分析基于2025-11-07的最新评测结果和代码审查生成*

