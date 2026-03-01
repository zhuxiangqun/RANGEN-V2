# 知识检索问题分析

## 查询内容

**原始查询**: "What is the first name of the 15th first lady of the United States' mother and what is the maiden name of the second assassinated president's mother?"

**期望答案**: Jane Ballou

---

## 知识库内容确认

### 1. 知识库中应该包含的信息

根据 `data/knowledge_management/adaptive_params.json` 中的记录，知识库应该包含以下Wikipedia链接的内容：

1. **James Buchanan** (第15任总统)
   - 链接: https://en.wikipedia.org/wiki/James_Buchanan

2. **Harriet Lane** (第15任第一夫人，Buchanan的侄女)
   - 链接: https://en.wikipedia.org/wiki/Harriet_Lane
   - 母亲: Jane Buchanan Lane

3. **James A. Garfield** (第20任总统，第二位被刺杀的总统)
   - 链接: https://en.wikipedia.org/wiki/James_A._Garfield
   - 母亲: Eliza Ballou Garfield (娘家姓: Ballou)

### 2. 关键信息

- **第15任第一夫人的母亲的名字**: Jane (Jane Buchanan Lane)
- **第二位被刺杀总统的母亲的娘家姓**: Ballou (Eliza Ballou Garfield)

---

## 为什么检索不到证据？

### 可能原因1: 子查询格式问题 ⚠️ **最可能**

从之前的日志可以看到，推理链生成的子查询可能包含无法检索的内容：

```
⚠️ 步骤1未检索到证据
⚠️ 步骤2未检索到证据
...
⚠️ 步骤8未检索到证据
```

**问题**:
- 子查询可能包含抽象引用（如 "my future wife"）
- 子查询可能不是有效的检索格式
- 子查询可能缺少必要的上下文信息

**示例问题子查询**:
- "What is the complete name of my future wife?" ❌ 无法检索
- "Who was the 15th First Lady of the United States?" ✅ 可以检索
- "What is the first name of the 15th first lady's mother?" ✅ 可以检索

### 可能原因2: 相似度阈值过高 ⚠️

虽然已经降低了相似度阈值（从0.35到0.25，再到0.15），但可能仍然存在问题：

**问题**:
- 即使阈值降低，如果查询格式不匹配，相似度仍然可能很低
- 知识库中的内容格式可能与查询格式不匹配

**解决方案**:
- 进一步降低阈值（如0.05）
- 使用查询扩展和重写
- 使用LlamaIndex增强检索

### 可能原因3: 知识库内容格式问题 ⚠️

**问题**:
- 知识库中的内容可能以不同的格式存储
- 可能包含在长文档中，而不是独立的条目
- 可能需要多跳检索才能找到相关信息

**示例**:
- 知识库中可能有: "Harriet Lane was the niece of James Buchanan..."
- 但可能没有: "Harriet Lane's mother was Jane Buchanan Lane"
- 需要多跳推理: Harriet Lane → James Buchanan → Jane Buchanan Lane

### 可能原因4: 知识库未正确加载 ⚠️

**问题**:
- 知识库可能没有正确加载所有内容
- 向量索引可能没有正确构建
- 知识库可能只包含部分内容

**检查方法**:
- 检查知识库统计信息（总条目数、向量索引大小）
- 直接查询知识库验证内容是否存在

---

## 建议的解决方案

### 1. 改进子查询生成 ✅ **已实施**

**措施**:
- 使用上下文工程增强子查询
- 从原始查询中提取可检索的实体和关系
- 避免使用抽象引用（如 "my future wife"）

**代码位置**: `src/core/real_reasoning_engine.py`
- `_extract_retrievable_sub_query_from_original_query`
- `_enhance_sub_query_with_context_engineering`

### 2. 进一步降低相似度阈值 ✅ **已实施**

**措施**:
- 将基础阈值从0.25降低到0.15
- 根据查询复杂度动态调整阈值
- 对于复杂查询，进一步降低阈值（如0.05）

**代码位置**: `src/services/knowledge_retrieval_service.py`
- `_get_dynamic_similarity_threshold`

### 3. 启用LlamaIndex增强检索 ✅ **已实施**

**措施**:
- 启用查询扩展
- 使用多策略融合
- 提高检索覆盖率

**代码位置**: `src/services/knowledge_retrieval_service.py`
- `_get_kms_knowledge` 中设置 `use_llamaindex=True`

### 4. 添加诊断日志 ✅ **已实施**

**措施**:
- 记录每个步骤的子查询内容
- 记录知识检索的返回结果
- 记录相似度分数和过滤原因

**代码位置**: `src/core/real_reasoning_engine.py`
- 推理链步骤查询内容显示
- 知识检索详细日志

---

## 验证方法

### 方法1: 直接查询知识库

```python
from knowledge_management_system.api.service_interface import get_knowledge_service

service = get_knowledge_service()

# 测试查询1: 第15任第一夫人
results1 = service.query_knowledge(
    query="15th first lady of the United States",
    modality="text",
    top_k=10,
    similarity_threshold=0.0  # 不进行阈值过滤
)

# 测试查询2: Harriet Lane mother
results2 = service.query_knowledge(
    query="Harriet Lane mother",
    modality="text",
    top_k=10,
    similarity_threshold=0.0
)

# 测试查询3: James Garfield mother maiden name
results3 = service.query_knowledge(
    query="James Garfield mother maiden name",
    modality="text",
    top_k=10,
    similarity_threshold=0.0
)
```

### 方法2: 检查知识库统计信息

```python
stats = service.get_statistics()
print(f"总知识条目数: {stats['total_entries']}")
print(f"向量索引大小: {stats['vector_index_size']}")
```

---

## 结论

**知识库中应该包含相关信息**，但检索不到的原因可能是：

1. **子查询格式问题**（最可能）：推理链生成的子查询包含无法检索的内容
2. **相似度阈值问题**：即使降低了阈值，查询格式不匹配仍然导致相似度低
3. **知识库内容格式问题**：信息可能以不同格式存储，需要多跳检索
4. **知识库未正确加载**：需要验证知识库是否正确加载

**建议**:
1. ✅ 查看推理链生成的子查询内容（已添加日志）
2. ✅ 检查知识检索的返回结果（已添加日志）
3. ⏳ 直接查询知识库验证内容是否存在
4. ⏳ 检查知识库统计信息

