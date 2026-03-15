# 长提示词问题解决方案

**问题**: 使用原始知识库内容会导致提示词很长，可能超出模型的上下文窗口限制

**分析时间**: 2025-11-13

---

## 📊 问题分析

### 当前情况

1. **提示词模板长度**: ~7,410 字符（~1,852 tokens）
2. **原始证据长度**: 可能数千到数万字符
3. **总提示词长度**: 可能达到 10,000-50,000+ 字符（2,500-12,500+ tokens）

### 模型上下文限制

- **DeepSeek-reasoner**: 64K tokens
- **DeepSeek-chat**: 32K tokens
- **其他模型**: 通常 4K-32K tokens

### 风险

1. **超出上下文窗口**: 如果提示词+证据超过模型限制，会被截断
2. **性能下降**: 即使不超出限制，过长的提示词也会：
   - 增加处理时间
   - 增加API成本
   - 降低注意力质量（关键信息被稀释）

---

## 🎯 解决方案

### 方案1: 智能分层证据处理 ⭐⭐⭐ (推荐)

**核心思想**: 
- 保留原始证据的完整性
- 但根据模型的上下文限制和查询类型，智能选择使用完整证据还是处理后的证据
- 优先保留最相关的部分

**实施策略**:

#### 1.1 计算可用空间

```python
def _calculate_available_evidence_space(
    self, 
    model: str, 
    prompt_template_length: int,
    query_length: int,
    reserved_tokens: int = 2000  # 为输出预留的tokens
) -> int:
    """计算可用于证据的token空间"""
    # 获取模型的上下文限制
    model_limits = {
        'deepseek-reasoner': 64000,
        'deepseek-chat': 32000,
        'default': 16000
    }
    
    max_context = model_limits.get(model.lower(), model_limits['default'])
    
    # 计算已使用的tokens
    used_tokens = (
        prompt_template_length // 4 +  # 模板tokens
        query_length // 4 +            # 查询tokens
        reserved_tokens                 # 输出预留
    )
    
    # 可用空间（保留20%的安全边际）
    available_tokens = int((max_context - used_tokens) * 0.8)
    available_chars = available_tokens * 4  # 粗略估算：1 token ≈ 4 字符
    
    return max(1000, available_chars)  # 至少保留1000字符
```

#### 1.2 智能证据选择

```python
def _select_evidence_strategy(
    self,
    original_evidence: str,
    available_space: int,
    query: str,
    query_type: str
) -> tuple[str, bool]:
    """
    智能选择证据策略
    
    Returns:
        (evidence_text, is_original): 证据文本和是否使用原始证据
    """
    original_length = len(original_evidence)
    
    # 策略1: 如果原始证据在可用空间内，直接使用
    if original_length <= available_space:
        return original_evidence, True
    
    # 策略2: 根据查询类型选择处理策略
    if query_type == 'ranking':
        # 排名查询：优先保留完整排名列表
        ranking_section = self._extract_ranking_section(original_evidence, query)
        if ranking_section and len(ranking_section) <= available_space:
            return ranking_section, False  # 使用提取的排名列表
    
    # 策略3: 提取最相关的片段
    relevant_segments = self._extract_relevant_segments(
        query, original_evidence, available_space
    )
    if relevant_segments and len(relevant_segments) >= available_space * 0.8:
        return relevant_segments, False
    
    # 策略4: 智能截断（保留开头+结尾+关键部分）
    if original_length > available_space * 2:
        # 超长证据：保留开头30% + 结尾30% + 中间关键部分40%
        first_part = int(available_space * 0.3)
        last_part = int(available_space * 0.3)
        middle_part = available_space - first_part - last_part
        
        # 提取中间的关键部分（包含查询关键词的部分）
        middle_start = original_length // 2 - middle_part // 2
        middle_end = middle_start + middle_part
        
        # 查找包含查询关键词的片段
        query_keywords = set(query.lower().split())
        best_middle_start = middle_start
        best_score = 0
        
        # 在中间区域搜索包含最多关键词的位置
        search_range = min(5000, original_length - middle_part)
        for i in range(max(0, middle_start - search_range), 
                      min(original_length - middle_part, middle_start + search_range), 
                      100):
            segment = original_evidence[i:i+middle_part]
            score = sum(1 for keyword in query_keywords if keyword in segment.lower())
            if score > best_score:
                best_score = score
                best_middle_start = i
        
        result = (
            f"{original_evidence[:first_part]}\n\n"
            f"[... {original_length - first_part - last_part - middle_part} characters omitted ...]\n\n"
            f"{original_evidence[best_middle_start:best_middle_start+middle_part]}\n\n"
            f"[... {original_length - first_part - last_part - middle_part} characters omitted ...]\n\n"
            f"{original_evidence[-last_part:]}"
        )
        return result, False
    
    # 策略5: 简单截断（保留开头）
    return original_evidence[:available_space], False
```

#### 1.3 实施位置

**文件**: `src/core/real_reasoning_engine.py`

**修改位置**: Line 5357-5380

**修改内容**:

```python
# 🚀 修复：保存原始证据文本（过滤后但未处理的完整内容）
original_evidence_text = evidence_text_filtered
self.logger.info(f"📋 保存原始证据文本，长度: {len(original_evidence_text)} 字符")

# 🚀 新增：智能选择证据策略（根据模型限制和可用空间）
# 获取当前使用的模型
current_model = self.llm_integration.current_model if hasattr(self.llm_integration, 'current_model') else 'deepseek-reasoner'

# 计算可用空间
prompt_template_length = len(self._get_prompt_template_length("reasoning_with_evidence"))
available_space = self._calculate_available_evidence_space(
    model=current_model,
    prompt_template_length=prompt_template_length,
    query_length=len(query),
    reserved_tokens=2000  # 为输出预留2000 tokens
)

# 智能选择证据
final_evidence_text, is_original = self._select_evidence_strategy(
    original_evidence=original_evidence_text,
    available_space=available_space,
    query=query,
    query_type=query_type
)

if is_original:
    self.logger.info(f"✅ 使用原始完整证据（长度: {len(final_evidence_text)} 字符，在可用空间内）")
else:
    self.logger.info(f"⚠️ 证据过长，使用智能处理后的证据（原始: {len(original_evidence_text)} 字符，处理后: {len(final_evidence_text)} 字符，可用空间: {available_space} 字符）")

# 使用最终选择的证据
prompt = self._generate_optimized_prompt(
    "reasoning_with_evidence",
    query=query,
    evidence=final_evidence_text,  # 使用智能选择后的证据
    query_type=query_type,
    enhanced_context=enhanced_context
)
```

**预期效果**:
- ✅ 在可用空间内时，使用完整原始证据
- ✅ 超出限制时，智能保留最相关的部分
- ✅ 不会超出模型的上下文窗口
- ✅ 平衡完整性和可用性

---

### 方案2: 分块处理 + 摘要 ⭐⭐ (备选)

**核心思想**: 
- 将长证据分成多个块
- 先对每个块生成摘要
- 在提示词中使用摘要，需要时再查询详细内容

**实施策略**:

```python
def _create_evidence_summary(
    self,
    evidence_text: str,
    query: str,
    max_length: int = 2000
) -> str:
    """创建证据摘要"""
    if len(evidence_text) <= max_length:
        return evidence_text
    
    # 将证据分成块
    chunk_size = 3000
    chunks = [evidence_text[i:i+chunk_size] for i in range(0, len(evidence_text), chunk_size)]
    
    # 为每个块生成摘要（使用LLM或简单提取）
    summaries = []
    for i, chunk in enumerate(chunks):
        # 提取包含查询关键词的句子
        sentences = chunk.split('. ')
        relevant_sentences = [
            s for s in sentences 
            if any(keyword in s.lower() for keyword in query.lower().split())
        ]
        
        if relevant_sentences:
            summaries.append(f"[Chunk {i+1}]: {' '.join(relevant_sentences[:3])}")
        else:
            summaries.append(f"[Chunk {i+1}]: {chunk[:200]}...")
    
    return '\n\n'.join(summaries)
```

**适用场景**:
- 证据非常长（>10,000字符）
- 需要保留所有证据的概览
- 可以接受部分信息丢失

---

### 方案3: 动态Few-shot示例 ⭐ (可选优化)

**核心思想**: 
- 根据证据长度动态调整Few-shot示例
- 如果证据很长，减少或移除Few-shot示例
- 如果证据较短，可以包含更多示例

**实施策略**:

```python
def _get_dynamic_few_shot_examples(
    self,
    evidence_length: int,
    available_space: int,
    query_type: str
) -> str:
    """根据可用空间动态选择Few-shot示例"""
    # 计算Few-shot示例的预算（最多占用20%的可用空间）
    few_shot_budget = int(available_space * 0.2)
    
    if evidence_length > available_space * 0.8:
        # 证据很长，不包含Few-shot示例
        return ""
    elif evidence_length > available_space * 0.6:
        # 证据较长，只包含1个简短示例
        return self._get_short_example(query_type)
    else:
        # 证据较短，可以包含完整示例
        return self._get_full_examples(query_type)
```

---

## 📋 推荐实施方案

### 阶段1: 立即实施（方案1）⭐⭐⭐

**优先级**: 最高

**原因**:
- 平衡了完整性和可用性
- 不会超出模型限制
- 智能保留最相关的部分

**实施步骤**:
1. 实现`_calculate_available_evidence_space`方法
2. 实现`_select_evidence_strategy`方法
3. 修改证据使用逻辑
4. 添加日志记录

**预期效果**:
- ✅ 不会超出模型上下文限制
- ✅ 在可能的情况下使用完整证据
- ✅ 超出限制时智能处理

---

### 阶段2: 可选优化（方案2和3）

**优先级**: 中低

**适用场景**:
- 方案1无法满足需求时
- 需要处理超长证据（>20,000字符）时
- 需要进一步优化token使用

---

## 🎯 实施建议

### 建议1: 优先实施方案1

**理由**:
- 解决了核心问题（不超出限制）
- 保留了原始证据的完整性（在可能的情况下）
- 实施相对简单

### 建议2: 添加配置选项

**允许用户选择策略**:
```python
EVIDENCE_STRATEGY = os.getenv('EVIDENCE_STRATEGY', 'smart')  # 'original', 'smart', 'summary'
```

- `original`: 总是使用原始证据（可能超出限制）
- `smart`: 智能选择（推荐）
- `summary`: 总是使用摘要

### 建议3: 监控和日志

**添加详细日志**:
- 记录原始证据长度
- 记录可用空间
- 记录选择的策略
- 记录最终使用的证据长度

---

## ⚠️ 注意事项

1. **模型限制**: 不同模型的上下文限制不同，需要动态检测
2. **Token估算**: 字符到token的转换是估算，实际可能有偏差
3. **安全边际**: 建议保留20%的安全边际，避免边界情况
4. **性能影响**: 智能处理会增加少量计算开销

---

## 📝 下一步行动

1. **立即实施**: 方案1（智能分层证据处理）
2. **测试验证**: 使用不同长度的证据测试
3. **监控效果**: 跟踪使用情况和性能
4. **根据结果**: 决定是否需要方案2和3

---

*分析时间: 2025-11-13*

