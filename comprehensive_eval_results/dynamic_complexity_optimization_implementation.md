# 动态复杂度优化实施总结

**实施时间**: 2025-11-18  
**优化目标**: 修复动态复杂度评估，使更多查询被正确分类为medium/complex

---

## ✅ 已实施的优化

### 步骤1: 降低阈值 ✅

**位置**: `src/core/real_reasoning_engine.py` - `_assess_complexity_progressively()` 和 `_assess_complexity_dynamically()`

**优化内容**:
- ✅ 证据检索阶段阈值: 1.5/3 → **1.0/2.5**
- ✅ 推理阶段阈值: 1.5/3 → **1.0/2.5**
- ✅ 最终评估阈值: 3/6 → **2/4**

**代码变更**:
```python
# 证据检索阶段和推理阶段
if complexity_score >= 2.5:  # 从3降低到2.5
    return "complex"
elif complexity_score >= 1.0:  # 从1.5降低到1.0
    return "medium"
else:
    return "simple"

# 最终评估
if complexity_score >= 4:  # 从6降低到4
    return "complex"
elif complexity_score >= 2:  # 从3降低到2
    return "medium"
else:
    return "simple"
```

**预期效果**:
- 更多查询被判定为 "medium" 或 "complex"
- 立即生效，无需其他改动

---

### 步骤2: 改进评估因素 ✅

**位置**: `src/core/real_reasoning_engine.py` - `_assess_complexity_progressively()`

**优化内容**:

#### 1. 调整证据数量阈值
- ✅ 从 `> 5` 调整为 `> 8`（适应新的证据数量限制）
- ✅ 从 `> 3` 调整为 `> 5`

#### 2. 调整证据相关性阈值
- ✅ 从 `< 0.3` 调整为 `< 0.4`
- ✅ 从 `< 0.6` 调整为 `< 0.7`

#### 3. 调整查询长度阈值
- ✅ 从 `> 200` 调整为 `> 150`
- ✅ 从 `> 100` 调整为 `> 80`

#### 4. 扩展复杂查询类型
- ✅ 新增: `'causal', 'comparative', 'analytical'`

#### 5. 新增查询语义复杂度评估
- ✅ 检查复杂关键词: `['compare', 'analyze', 'explain', 'why', 'how', 'relationship', ...]`
- ✅ 权重: 0.5

**代码变更**:
```python
# 1. 证据数量（调整阈值）
if evidence_count > 8:  # 从5调整到8
    complexity_score += 2
elif evidence_count > 5:  # 从3调整到5
    complexity_score += 1

# 2. 证据相关性（调整阈值）
if evidence_relevance < 0.4:  # 从0.3提高到0.4
    complexity_score += 2
elif evidence_relevance < 0.7:  # 从0.6提高到0.7
    complexity_score += 1

# 3. 查询长度（调整阈值）
if query_length > 150:  # 从200降低到150
    complexity_score += 1
elif query_length > 80:  # 从100降低到80
    complexity_score += 0.5

# 4. 查询类型（扩展复杂类型）
complex_types = ['temporal', 'multi_hop', 'complex', 'numerical', 'spatial', 
               'causal', 'comparative', 'analytical']  # 新增类型

# 5. 新增查询语义复杂度
query_lower = query_text.lower()
complex_keywords = ['compare', 'analyze', 'explain', 'why', 'how', 'relationship', ...]
if any(keyword in query_lower for keyword in complex_keywords):
    complexity_score += 0.5
```

**预期效果**:
- 更准确地评估查询复杂度
- 更多查询被正确分类

---

## 📊 优化效果预期

### 典型场景分析

**场景1: 简单查询（优化前）**
- 证据数量: 5个 → 评分 = 1
- 证据相关性: 0.8 → 评分 = 0
- 查询长度: 100字符 → 评分 = 0.5
- 查询类型: 'general' → 评分 = 0
- **总评分**: 1.5 → **"medium"**（优化前是"simple"）

**场景2: 中等查询（优化前）**
- 证据数量: 6个 → 评分 = 1
- 证据相关性: 0.75 → 评分 = 1
- 查询长度: 120字符 → 评分 = 0.5
- 查询类型: 'general' → 评分 = 0
- 语义复杂度: 包含'how' → 评分 = 0.5
- **总评分**: 3.0 → **"complex"**（优化前是"medium"）

**场景3: 复杂查询（优化前）**
- 证据数量: 10个 → 评分 = 2
- 证据相关性: 0.65 → 评分 = 1
- 查询长度: 180字符 → 评分 = 1
- 查询类型: 'temporal' → 评分 = 1
- 语义复杂度: 包含'compare' → 评分 = 0.5
- **总评分**: 5.5 → **"complex"**（优化前是"complex"）

---

## 🎯 预期改进

### 1. 更多查询被正确分类

**优化前**:
- simple: 90%+
- medium: <10%
- complex: <1%

**优化后（预期）**:
- simple: 60-70%
- medium: 20-30%
- complex: 10-20%

---

### 2. 动态复杂度评估更准确

**改进**:
- 降低阈值，使评估更合理
- 调整评估因素阈值，适应新的证据数量限制
- 新增语义复杂度评估，考虑更多因素

---

### 3. 证据数量动态调整更有效

**改进**:
- 更多查询被判定为medium/complex
- 这些查询可以使用更多证据（10-15个）
- 知识库利用率提升

---

## 📝 实施总结

### 已完成的优化

1. ✅ **降低阈值** - 从1.5/3降低到1.0/2.5（立即生效）
2. ✅ **改进评估因素** - 调整阈值，新增语义复杂度评估

### 待实施的优化

3. ⏳ **改进查询类型识别** - 更准确地识别复杂查询类型
4. ⏳ **结合多个阶段的评估** - 使用多阶段评估结果

### 预期效果

- **更多查询被判定为medium/complex**: 从<10%提升到30-40%
- **动态复杂度评估更准确**: 考虑更多因素，阈值更合理
- **证据数量动态调整更有效**: 复杂查询可以使用更多证据

---

*实施时间: 2025-11-18*

