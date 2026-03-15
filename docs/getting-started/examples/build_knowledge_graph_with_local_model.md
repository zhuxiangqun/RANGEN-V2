# 使用本地模型从向量知识库构建知识图谱

## 概述

系统已经支持使用**本地模型**从向量知识库构建知识图谱。这意味着您可以在**完全离线**的情况下，使用本地embedding模型（如`all-mpnet-base-v2`）从**已导入的向量知识库**中提取实体和关系，构建知识图谱。

**重要说明**：`build_knowledge_graph.py` 脚本是**基于现有的向量知识库**构建知识图谱的。它会：
1. 从向量知识库的元数据中读取所有已导入的知识条目
2. 从每个条目的内容（`metadata.content`）中提取实体和关系
3. 使用本地模型进行向量化和语义分析
4. 构建知识图谱并保存到JSON文件

**前提条件**：在执行此脚本之前，您需要先有已导入的向量知识库数据。如果没有，请先使用 `import_dataset.py` 或 `build_vector_knowledge_base.py` 导入知识数据。

## 技术实现

### 1. 本地模型支持

系统使用`TextProcessor`进行文本向量化，它**优先使用本地模型**：

- **默认模型**：`all-mpnet-base-v2`（768维，与Jina v2相同）
  - 这是执行 `build_knowledge_graph.py` 时**默认使用的模型**
  - 模型通过环境变量 `LOCAL_EMBEDDING_MODEL` 指定，未设置时默认为 `all-mpnet-base-v2`
- **模型位置**：本地缓存（`~/.cache/huggingface/hub/models--sentence-transformers--all-mpnet-base-v2/`）
- **完全免费**：无需API密钥，无需网络连接（首次下载后）
- **Fallback机制**：如果本地模型不可用，可以fallback到Jina API（如果配置了API密钥）

### 2. 知识图谱构建流程

```
向量知识库（已导入的知识条目，存储在 metadata.json）
    ↓
读取所有知识条目（通过 knowledge_manager.list_knowledge()）
    ↓
提取知识内容（从每个条目的 metadata.content）
    ↓
使用本地模型向量化文本（TextProcessor 使用 all-mpnet-base-v2）
    ↓
提取实体和关系（基于embedding语义相似度）
    ↓
构建知识图谱（实体和关系存储到 entities.json 和 relations.json）
```

**数据来源**：
- 脚本从 `knowledge_manager.list_knowledge()` 获取所有已存在的知识条目
- 每个条目包含 `id` 和 `metadata` 字段
- 从 `metadata.content` 中提取实际的知识内容
- 如果向量知识库为空，脚本会提示"⚠️ 知识库中没有条目，无法构建知识图谱"

### 3. 实体和关系提取方法

系统使用多种方法提取实体和关系：

1. **模式匹配**：使用正则表达式提取人名、地名、组织等
2. **语义相似度**：使用本地embedding模型计算实体与类型关键词的相似度，进行智能分类
3. **关系提取**：基于embedding语义相似度识别实体间的关系

## 使用方法

### 方法1：使用构建脚本（推荐）

```bash
# 从所有知识条目构建知识图谱（使用默认本地模型：all-mpnet-base-v2）
python knowledge_management_system/scripts/build_knowledge_graph.py

# 指定批次大小（默认100）
python knowledge_management_system/scripts/build_knowledge_graph.py --batch-size 50

# 断点续传（从上次中断的地方继续）
python knowledge_management_system/scripts/build_knowledge_graph.py --resume

# 只提取实体，不提取关系
python knowledge_management_system/scripts/build_knowledge_graph.py --no-relations

# 只提取关系，不提取实体
python knowledge_management_system/scripts/build_knowledge_graph.py --no-entities
```

### 方法2：在代码中使用

```python
from knowledge_management_system.api.service_interface import get_knowledge_service

# 获取知识库服务
service = get_knowledge_service()

# 获取所有知识条目
all_entries = service.knowledge_manager.list_knowledge(limit=10000)

# 从每个条目提取实体和关系
for entry in all_entries:
    content = entry.get('metadata', {}).get('content', '')
    metadata = entry.get('metadata', {})
    
    # 提取实体和关系（使用本地模型）
    extracted_data = service._extract_entities_and_relations(content, metadata)
    
    # 构建知识图谱
    if extracted_data:
        result = service.graph_builder.build_from_structured_data(extracted_data)
        print(f"创建了 {result['entities_created']} 个实体, {result['relations_created']} 条关系")
```

## 配置本地模型

### 环境变量

```bash
# 指定本地embedding模型（默认：all-mpnet-base-v2）
# 如果不设置此变量，build_knowledge_graph.py 会使用 all-mpnet-base-v2
export LOCAL_EMBEDDING_MODEL="all-mpnet-base-v2"

# 或者使用其他模型，例如：
# export LOCAL_EMBEDDING_MODEL="paraphrase-multilingual-mpnet-base-v2"  # 多语言支持
# export LOCAL_EMBEDDING_MODEL="distiluse-base-multilingual-cased"      # 更小更快

# 使用HuggingFace镜像源（如果网络有问题）
export HF_ENDPOINT="https://hf-mirror.com"

# 禁用Jina API（强制使用本地模型）
# 不设置 USE_JINA_API 或设置为 false
```

### 支持的本地模型

系统支持任何`sentence-transformers`兼容的模型，推荐：

- `all-mpnet-base-v2`（默认，768维，性能好）
- `paraphrase-multilingual-mpnet-base-v2`（多语言支持）
- `distiluse-base-multilingual-cased`（多语言，更小更快）

## 数据存储位置

构建的知识图谱数据存储在：

- **实体文件**：`data/knowledge_management/graph/entities.json`
- **关系文件**：`data/knowledge_management/graph/relations.json`
- **进度文件**：`data/knowledge_management/graph_progress.json`（用于断点续传）

## 性能优化

### 1. 批量处理

脚本默认使用批量处理（`batch_size=100`），可以调整：

```bash
# 小批次（内存占用少，但处理慢）
python build_knowledge_graph.py --batch-size 20

# 大批次（处理快，但内存占用多）
python build_knowledge_graph.py --batch-size 200
```

### 2. 并发处理

脚本使用线程池并发提取实体和关系（默认10个并发），可以提升处理速度。

### 3. 断点续传

如果处理中断，可以使用`--resume`参数继续：

```bash
python build_knowledge_graph.py --resume
```

## 注意事项

1. **首次运行**：首次使用本地模型时，需要下载模型文件（约400MB），下载后会自动缓存到本地。

2. **内存占用**：本地模型会占用一定内存（约500MB-1GB），确保系统有足够内存。

3. **处理速度**：本地模型的处理速度取决于CPU/GPU性能，通常比API调用慢一些，但完全免费且可离线使用。

4. **知识图谱质量**：基于embedding的实体和关系提取质量取决于：
   - 知识条目的内容质量
   - 文本的清晰度和结构化程度
   - 实体和关系的显式程度

5. **当前状态**：根据您的需求，知识图谱构建功能已经实现，但**默认不加载**（因为知识图谱还未建立好）。当您准备好构建知识图谱时，可以运行构建脚本。

## 验证构建结果

构建完成后，可以检查：

```python
from knowledge_management_system.graph.entity_manager import EntityManager
from knowledge_management_system.graph.relation_manager import RelationManager

# 检查实体数量
entity_manager = EntityManager()
entities = entity_manager.list_entities()
print(f"实体数量: {len(entities)}")

# 检查关系数量
relation_manager = RelationManager()
relations = relation_manager.list_relations()
print(f"关系数量: {len(relations)}")
```

## 总结

✅ **可以使用本地模型从向量知识库构建知识图谱**

- 系统已完全支持本地模型（`TextProcessor`优先使用本地模型）
- 有专门的构建脚本（`build_knowledge_graph.py`）
- 支持断点续传、批量处理、并发处理
- 完全免费，无需API密钥，可离线使用
- 知识图谱数据存储在JSON文件中

当您准备好构建知识图谱时，只需运行构建脚本即可！

