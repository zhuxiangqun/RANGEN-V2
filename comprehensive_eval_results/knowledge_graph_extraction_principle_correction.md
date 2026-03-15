# 知识图谱提取原则修正

**修正时间**: 2025-11-09  
**核心原则修正**: prompt/expected_answer不应该用于构建知识图谱

---

## 🎯 核心原则

### 正确的逻辑关系

**知识图谱 ↔ prompt/expected_answer 的关系**：
- **知识图谱**：从知识条目的**内容（content）**中提取实体和关系构建
- **prompt/expected_answer**：是基于知识图谱推理出来的**查询和答案**
- **关系方向**：知识图谱 → prompt/expected_answer（推理方向）
- **错误方向**：prompt/expected_answer → 知识图谱（不应该反向构建）

### 为什么不能反向使用？

1. **逻辑错误**：
   - prompt/expected_answer是查询和答案，是推理的结果
   - 不应该反过来用于构建知识图谱
   - 这会导致循环依赖：知识图谱 → 推理 → prompt/answer → 知识图谱？

2. **数据来源错误**：
   - 知识图谱应该反映知识条目的实际内容
   - prompt/answer只是查询和答案，不是知识本身
   - 使用prompt/answer构建知识图谱会导致知识图谱不准确

3. **设计原则**：
   - 知识图谱是知识的基础结构
   - prompt/answer是基于知识图谱的查询和推理结果
   - 应该保持单向依赖：知识图谱 → 推理系统

---

## 🔧 修正内容

### 修正前（错误）

```python
# 错误：使用prompt/answer作为补充信息
if query or answer:
    analysis_text = f"{text}\n\nContext: {query} {answer}".strip()
else:
    analysis_text = text
```

**问题**：将prompt/answer作为上下文，参与实体和关系的提取。

### 修正后（正确）

```python
# 正确：只从text（知识条目内容）中提取
analysis_text = text
```

**改进**：完全移除对prompt/answer的依赖，只从知识条目的实际内容中提取。

---

## 📊 修正后的提取流程

### 当前流程

1. **方法1**：从元数据中提取结构化信息（如果存在`entities`和`relations`字段）
2. **方法2**：从知识条目内容（`text`）中提取，**不使用prompt/answer**
3. **方法3**：使用NLP引擎从内容中提取实体
4. **方法4**：使用Jina Embedding从内容中提取
5. **方法5**：使用LLM从内容中提取，**不使用prompt/answer**

### 核心原则

- **唯一数据源**：知识条目的`content`字段（即`text`参数）
- **不参与提取**：`prompt`和`expected_answer`完全不参与实体和关系的提取
- **知识图谱反映**：知识条目的实际内容，而不是查询和答案

---

## ✅ 修正完成

所有修正已完成，提取逻辑现在：
1. ✅ 完全移除对prompt/expected_answer的依赖
2. ✅ 只从知识条目的内容（content）中提取实体和关系
3. ✅ 保持正确的逻辑关系：知识图谱 → prompt/answer（推理方向）

---

*本修正基于2025-11-09的用户反馈和设计原则分析生成*

