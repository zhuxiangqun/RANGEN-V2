# 为什么要压缩证据？

**分析时间**: 2025-11-08

---

## 🔍 当前压缩逻辑

**代码位置**: `src/core/real_reasoning_engine.py` Line 319-373

**压缩目标长度**:
- 简单查询: **1200字符**
- 中等查询: **1500字符**
- 复杂查询: **2000字符**

**压缩策略**:
1. 提取与查询最相关的片段
2. 智能截断（保留开头和结尾）
3. 简单截断（保留开头）

---

## ❓ 为什么要压缩？

### 原因1: LLM Context Window限制（推测）

**理论原因**:
- LLM的context window有限制（如DeepSeek的32K tokens）
- 提示词太长会影响：
  - **性能**: 处理时间增加
  - **成本**: API调用费用增加
  - **质量**: 关键信息可能被稀释

**但代码中没有明确限制**:
- 代码中没有检查context window
- 没有明确的token limit检查
- 压缩长度（1200-2000字符）似乎是一个经验值

---

### 原因2: 提高LLM注意力（推测）

**理论原因**:
- 证据太长，LLM可能无法关注关键信息
- 压缩后保留最相关的部分，提高答案质量

**但可能的问题**:
- 压缩可能丢失关键信息
- 如果关键信息在压缩时被截断，反而降低质量

---

### 原因3: 降低API成本（推测）

**理论原因**:
- 提示词越短，API调用费用越低
- 1200-2000字符是一个平衡点

---

## ⚠️ 当前压缩的问题

### 问题1: 压缩可能丢失关键信息

**示例**:
- 查询: "Bronte tower height ranking"
- 证据: 包含完整的排名列表（1st, 2nd, ..., 37th, ...）
- 压缩后: 可能只保留开头，丢失"37th"的信息

**代码问题**:
```python
# 策略3: 简单截断（保留开头）
result = evidence_text[:target_length]
```
- 如果关键信息在末尾，会被截断

---

### 问题2: 压缩长度可能不够

**当前限制**:
- 简单查询: 1200字符
- 这可能不够包含完整的排名列表或详细信息

**示例**:
- 一个排名列表可能需要3000+字符
- 但被压缩到1200字符，可能丢失关键信息

---

### 问题3: 没有考虑查询类型

**当前逻辑**:
```python
query_complexity = len(query.split())  # 只根据查询长度判断
```

**问题**:
- 排名查询可能需要完整的列表
- 数值查询可能需要完整的计算过程
- 但压缩逻辑没有考虑这些

---

## 💡 改进建议

### 建议1: 根据查询类型调整压缩策略

```python
def _process_evidence_intelligently(self, query: str, evidence_text: str, query_type: str):
    # 根据查询类型确定目标长度
    if query_type in ['ranking', 'numerical']:
        target_length = 3000  # 排名和数值查询需要更多信息
    elif query_type in ['factual', 'name']:
        target_length = 2000  # 事实查询需要中等长度
    else:
        target_length = 1500  # 其他查询
```

---

### 建议2: 智能保留关键信息

```python
# 对于排名查询，优先保留排名列表
if query_type == 'ranking':
    ranking_section = self._extract_ranking_section(evidence_text)
    if ranking_section:
        return ranking_section  # 保留完整排名列表
```

---

### 建议3: 检查LLM Context Window

```python
# 检查提示词总长度
total_prompt_length = len(prompt)
if total_prompt_length > MAX_CONTEXT_WINDOW:
    # 需要压缩
    # 但应该智能压缩，保留关键信息
```

---

### 建议4: 记录压缩效果

```python
# 记录压缩前后的信息
self.logger.info(
    f"证据压缩: 原始={len(evidence_text)}, "
    f"压缩后={len(compressed_evidence)}, "
    f"压缩比={len(compressed_evidence)/len(evidence_text):.2%}"
)
```

---

## 🎯 结论

### 为什么要压缩？

**可能的原因**（代码中没有明确说明）:
1. **LLM Context Window限制** - 但代码中没有检查
2. **提高注意力** - 但可能丢失关键信息
3. **降低API成本** - 但影响答案质量

### 当前问题

1. **压缩可能丢失关键信息** - 特别是排名列表
2. **压缩长度可能不够** - 1200字符可能太少
3. **没有考虑查询类型** - 所有查询使用相同的压缩策略

### 建议

1. **根据查询类型调整压缩策略**
2. **智能保留关键信息**（如排名列表）
3. **检查LLM Context Window**（如果有明确限制）
4. **记录压缩效果**，便于诊断问题

---

## 📝 下一步行动

1. **检查是否有明确的Context Window限制**
2. **分析压缩是否真的必要**
3. **改进压缩策略，保留关键信息**
4. **记录压缩效果，验证改进效果**

