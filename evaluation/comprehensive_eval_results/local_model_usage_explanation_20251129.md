# 本地模型在RAG系统中的作用说明

**更新时间**: 2025-11-29

---

## 📋 概述

本地模型（sentence-transformers）在RAG系统中主要用于**两个核心功能**：

1. **Embedding（向量化）** - 将文本转换为向量
2. **Rerank（重排序）** - 对检索结果进行重新排序

---

## 1. Embedding（向量化）

### 作用
将文本（查询或文档）转换为数值向量（embedding），用于语义相似度计算。

### 使用场景

#### 1.1 知识库构建阶段
- **文档向量化**: 将知识库中的文档转换为向量
- **存储到向量索引**: 将向量存储到FAISS索引中，用于快速检索

**代码位置**: `knowledge_management_system/api/service_interface.py`
```python
# 导入知识时，将文档内容向量化
processor = self.text_processor  # 使用本地模型
vector = processor.encode(content)  # 转换为向量
self.index_builder.add_vector(vector, knowledge_id)  # 存储到索引
```

#### 1.2 查询阶段
- **查询向量化**: 将用户查询转换为向量
- **向量相似度搜索**: 在向量索引中搜索最相似的文档

**代码位置**: `knowledge_management_system/api/service_interface.py`
```python
# 查询时，将查询文本向量化
query_vector = processor.encode(query)  # 使用本地模型将查询转换为向量

# 在向量索引中搜索最相似的文档
results = self.index_builder.search(
    query_vector, 
    top_k=top_k,
    similarity_threshold=similarity_threshold
)
```

### 工作流程

```
用户查询: "第15位第一夫人的母亲是谁？"
    ↓
本地模型 (sentence-transformers)
    ↓
查询向量: [0.123, -0.456, 0.789, ...] (768维)
    ↓
向量相似度搜索 (FAISS)
    ↓
找到最相似的文档向量
    ↓
返回相关文档
```

### 使用的模型
- **模型名称**: `all-mpnet-base-v2`
- **维度**: 768维（与Jina v2相同）
- **特点**: 
  - 完全免费，无需API密钥
  - 本地运行，无需网络请求
  - 性能优秀，适合大多数场景

---

## 2. Rerank（重排序）

### 作用
对初步检索到的文档进行重新排序，提高检索结果的准确性。

### 使用场景

#### 2.1 检索结果优化
- **初步检索**: 使用向量相似度搜索得到候选文档（可能很多，如30-50个）
- **重排序**: 使用rerank模型对候选文档进行重新排序，选出最相关的文档

**代码位置**: `knowledge_management_system/api/service_interface.py`
```python
# 初步检索（向量相似度搜索）
results = self.index_builder.search(query_vector, top_k=30)

# 重排序（使用本地rerank模型）
if use_rerank and len(enriched_results) > 1:
    documents = [r['content'] for r in enriched_results]
    rerank_results = self.jina_service.rerank(
        query=query,
        documents=documents,
        top_n=top_k
    )
    # 使用rerank结果重新排序
```

### 工作流程

```
初步检索结果（30个文档）:
  1. 文档A (相似度: 0.85)
  2. 文档B (相似度: 0.82)
  3. 文档C (相似度: 0.80)
  ...
  
    ↓
本地Rerank模型 (CrossEncoder)
    ↓
重排序结果（5个最相关文档）:
  1. 文档C (rerank分数: 0.95) ← 更准确！
  2. 文档A (rerank分数: 0.88)
  3. 文档B (rerank分数: 0.85)
  ...
```

### 为什么需要Rerank？

1. **向量相似度搜索的局限性**:
   - 基于embedding的相似度搜索可能不够精确
   - 可能返回语义相关但不够精确的文档

2. **Rerank的优势**:
   - 使用CrossEncoder模型，同时考虑查询和文档
   - 更准确地判断文档与查询的相关性
   - 提高最终检索结果的准确性

### 使用的模型
- **模型类型**: CrossEncoder（交叉编码器）
- **特点**: 
  - 完全免费，无需API密钥
  - 本地运行，无需网络请求
  - 专门用于重排序任务，准确性高

---

## 🔄 完整工作流程

### 知识检索的完整流程

```
1. 用户查询
   "第15位第一夫人的母亲是谁？"
    ↓
2. 查询向量化（本地模型 - Embedding）
   query_vector = processor.encode(query)
    ↓
3. 向量相似度搜索（FAISS）
   results = index_builder.search(query_vector, top_k=30)
    ↓
4. 获取文档内容
   enriched_results = get_knowledge_content(results)
    ↓
5. 重排序（本地模型 - Rerank）
   rerank_results = jina_service.rerank(query, documents, top_n=5)
    ↓
6. 返回最相关的文档
   return rerank_results
```

---

## 💡 为什么使用本地模型？

### 优势

1. **完全免费**: 无需API密钥，无需付费
2. **本地运行**: 无需网络请求，速度快
3. **隐私保护**: 数据不离开本地
4. **稳定可靠**: 不依赖外部服务，不会因为API限制而失败

### 与Jina API的对比

| 特性 | 本地模型 | Jina API |
|------|---------|----------|
| 费用 | 免费 | 需要付费 |
| 速度 | 快（本地） | 取决于网络 |
| 稳定性 | 高（不依赖网络） | 依赖API服务 |
| 准确性 | 优秀 | 优秀 |
| 配置 | 需要安装sentence-transformers | 需要API密钥 |

---

## 🔧 如何切换？

### 使用本地模型（默认）
```bash
# 不需要任何配置，默认使用本地模型
# 确保已安装: pip install sentence-transformers
```

### 使用Jina API
```bash
# 设置环境变量
export USE_JINA_API=true          # 使用Jina API进行embedding
export USE_JINA_RERANK_API=true   # 使用Jina API进行rerank
export JINA_API_KEY=your_api_key  # 设置API密钥
```

---

## 📊 性能对比

### Embedding性能
- **本地模型**: ~0.1-0.3秒/查询（取决于文本长度）
- **Jina API**: ~0.5-1.0秒/查询（取决于网络延迟）

### Rerank性能
- **本地模型**: ~0.1-0.5秒/批次（取决于文档数量）
- **Jina API**: ~0.5-2.0秒/批次（取决于网络延迟）

---

## 🎯 总结

本地模型在RAG系统中的核心作用：

1. **Embedding（向量化）**: 
   - 将文本转换为向量
   - 用于向量相似度搜索
   - 是RAG系统的基础

2. **Rerank（重排序）**: 
   - 对检索结果进行重新排序
   - 提高检索结果的准确性
   - 是RAG系统的优化

**默认使用本地模型，完全免费且性能优秀！**

---

**文档生成时间**: 2025-11-29

