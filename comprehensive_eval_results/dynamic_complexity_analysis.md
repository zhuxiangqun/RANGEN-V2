# 动态复杂度分析：为什么都是simple？

**分析时间**: 2025-11-18  
**问题**: 动态复杂度是如何得到的？为什么都是simple？

---

## 🔍 动态复杂度的计算逻辑

### 1. 计算位置

**位置**: `src/core/real_reasoning_engine.py` - `_assess_complexity_progressively()`

**调用时机**: 在证据检索阶段（`stage="evidence_retrieval"`）调用

**代码位置**: 第6031行
```python
dynamic_complexity = self._assess_complexity_progressively("evidence_retrieval", evidence_context)
```

---

### 2. 评估逻辑（证据检索阶段）

**当前逻辑**:
```python
def _assess_complexity_progressively(self, stage: str, context: Dict[str, Any]) -> str:
    if stage == "evidence_retrieval":
        evidence_count = context.get('evidence_count', 0)
        evidence_relevance = context.get('evidence_relevance', 1.0)
        query_length = context.get('query_length', 0)
        query_type = context.get('query_type', 'general')
        
        complexity_score = 0
        
        # 1. 证据数量（权重：2）
        if evidence_count == 0:
            complexity_score += 3  # 无证据
        elif evidence_count > 5:
            complexity_score += 2  # 证据多
        elif evidence_count > 3:
            complexity_score += 1  # 中等数量证据
        # 如果 evidence_count <= 3，复杂度评分 = 0
        
        # 2. 证据相关性（权重：1）
        if evidence_relevance < 0.3:
            complexity_score += 2  # 相关性低
        elif evidence_relevance < 0.6:
            complexity_score += 1  # 相关性中等
        # 如果 evidence_relevance >= 0.6，复杂度评分 = 0
        
        # 3. 查询长度（权重：1）
        if query_length > 200:
            complexity_score += 1
        elif query_length > 100:
            complexity_score += 0.5
        # 如果 query_length <= 100，复杂度评分 = 0
        
        # 4. 查询类型（权重：1）
        complex_types = ['temporal', 'multi_hop', 'complex', 'numerical', 'spatial']
        if query_type in complex_types:
            complexity_score += 1
        # 如果 query_type = 'general'，复杂度评分 = 0
        
        # 转换为复杂度等级
        if complexity_score >= 3:
            return "complex"
        elif complexity_score >= 1.5:
            return "medium"
        else:
            return "simple"  # ⚠️ 如果评分 < 1.5，返回 "simple"
```

---

## ⚠️ 为什么都是simple？

### 问题分析

**典型场景**:
- 证据数量: 5个（> 3，但 <= 5）→ 复杂度评分 = 1
- 证据相关性: 0.8（>= 0.6）→ 复杂度评分 = 0
- 查询长度: 100字符（<= 100）→ 复杂度评分 = 0
- 查询类型: 'general'（不在复杂类型中）→ 复杂度评分 = 0

**总评分**: 1 + 0 + 0 + 0 = **1 < 1.5** → 返回 **"simple"**

---

### 根本原因

1. **阈值过高**: 需要评分 >= 1.5 才能达到 "medium"，>= 3 才能达到 "complex"
2. **评估因素不足**: 只考虑4个因素，且权重分配不合理
3. **查询类型都是general**: 所有查询都被判定为 'general'，无法获得复杂度加分
4. **证据数量阈值不合理**: 只有 > 5 才加2分，5个证据只加1分

---

## 🔧 优化方案（分步实施）

### 步骤1: 降低阈值（最简单，立即生效）✅

**问题**: 阈值过高（1.5/3），导致大多数查询都被判定为simple

**优化**:
```python
# 优化前
if complexity_score >= 3:
    return "complex"
elif complexity_score >= 1.5:
    return "medium"
else:
    return "simple"

# 优化后
if complexity_score >= 2.5:  # 从3降低到2.5
    return "complex"
elif complexity_score >= 1.0:  # 从1.5降低到1.0
    return "medium"
else:
    return "simple"
```

**预期效果**:
- 更多查询被判定为 "medium" 或 "complex"
- 立即生效，无需其他改动

---

### 步骤2: 改进评估因素（中等难度）⏳

**问题**: 评估因素不足，权重分配不合理

**优化**:
```python
# 1. 证据数量（调整阈值）
if evidence_count == 0:
    complexity_score += 3
elif evidence_count > 8:  # 从5降低到8（因为现在允许15个证据）
    complexity_score += 2
elif evidence_count > 5:  # 从3降低到5
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
if query_type in complex_types:
    complexity_score += 1

# 5. 新增：查询语义复杂度
complex_keywords = ['compare', 'analyze', 'explain', 'why', 'how', 'relationship']
if any(keyword in query.lower() for keyword in complex_keywords):
    complexity_score += 0.5
```

**预期效果**:
- 更准确地评估查询复杂度
- 更多查询被正确分类

---

### 步骤3: 改进查询类型识别（较难）⏳

**问题**: 所有查询都被判定为 'general'，无法获得复杂度加分

**优化**:
- 改进 `_analyze_query_type_with_ml()` 方法
- 使用LLM或更智能的规则识别查询类型
- 识别 temporal、numerical、spatial 等复杂类型

**预期效果**:
- 查询类型识别更准确
- 复杂查询能够被正确识别

---

### 步骤4: 结合多个阶段的评估（较难）⏳

**问题**: 只在证据检索阶段评估，可能不够准确

**优化**:
- 结合证据检索、推理、验证等多个阶段的评估
- 使用加权平均或投票机制
- 最终复杂度 = 各阶段评估的综合结果

**预期效果**:
- 更准确的复杂度评估
- 考虑更多因素

---

## 📊 当前评估逻辑的问题

### 问题1: 阈值过高

| 评分 | 当前等级 | 问题 |
|------|---------|------|
| 0-1.4 | simple | 阈值过高，大多数查询都在这个范围 |
| 1.5-2.9 | medium | 很难达到 |
| 3+ | complex | 几乎不可能达到 |

---

### 问题2: 评估因素不足

**当前因素**:
1. 证据数量（权重：2）
2. 证据相关性（权重：1）
3. 查询长度（权重：1）
4. 查询类型（权重：1）

**缺失因素**:
- 查询语义复杂度
- 多实体/多关系查询
- 时间/数值推理需求
- 推理步骤数（在证据检索阶段未知）

---

### 问题3: 查询类型都是general

**问题**:
- 所有查询都被判定为 'general'
- 无法获得查询类型的复杂度加分
- 导致复杂度评分偏低

**原因**:
- `_analyze_query_type_with_ml()` 可能不够准确
- 或者查询确实都是general类型

---

## 🎯 分步实施计划

### 步骤1: 降低阈值（立即实施）✅

**优先级**: P0（最高）
**难度**: 低
**影响**: 立即生效，更多查询被判定为medium/complex

**实施**:
- 修改 `_assess_complexity_progressively()` 方法
- 将阈值从 1.5/3 降低到 1.0/2.5

---

### 步骤2: 改进评估因素（近期实施）⏳

**优先级**: P1（高）
**难度**: 中
**影响**: 更准确的复杂度评估

**实施**:
- 调整证据数量阈值
- 调整证据相关性阈值
- 调整查询长度阈值
- 扩展复杂查询类型
- 新增查询语义复杂度评估

---

### 步骤3: 改进查询类型识别（中期实施）⏳

**优先级**: P2（中）
**难度**: 高
**影响**: 查询类型识别更准确

**实施**:
- 改进 `_analyze_query_type_with_ml()` 方法
- 使用更智能的规则或LLM识别查询类型

---

### 步骤4: 结合多个阶段的评估（长期实施）⏳

**优先级**: P3（低）
**难度**: 高
**影响**: 最准确的复杂度评估

**实施**:
- 结合多个阶段的评估结果
- 使用加权平均或投票机制

---

## 📝 总结

### 为什么都是simple？

1. **阈值过高**: 需要评分 >= 1.5 才能达到 "medium"
2. **评估因素不足**: 只考虑4个因素，且权重分配不合理
3. **查询类型都是general**: 无法获得复杂度加分
4. **典型场景评分**: 1 + 0 + 0 + 0 = 1 < 1.5 → "simple"

### 优化方向

1. **降低阈值**: 从 1.5/3 降低到 1.0/2.5（立即生效）
2. **改进评估因素**: 调整阈值，新增因素（近期实施）
3. **改进查询类型识别**: 更准确地识别复杂查询类型（中期实施）
4. **结合多个阶段**: 使用多阶段评估结果（长期实施）

---

*分析时间: 2025-11-18*
