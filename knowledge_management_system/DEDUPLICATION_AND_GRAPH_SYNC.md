# 知识库查重与知识图谱同步构建功能

## 功能概述

实现了知识库和知识图谱的智能查重处理，以及向量知识库与知识图谱的同步构建功能。

## 核心功能

### 1. 知识库查重功能 ✅

#### 实现方式
- **基于内容哈希的查重**：使用 SHA256 哈希算法对知识内容进行哈希计算
- **哈希索引管理**：维护 `content_hash_index` 索引，实现 O(1) 时间复杂度查重
- **自动跳过重复**：导入时自动检测并跳过已存在的知识条目

#### 关键实现
- `KnowledgeManager.check_duplicate()`: 检查内容是否已存在
- `KnowledgeManager._compute_content_hash()`: 计算内容哈希值
- `KnowledgeManager._rebuild_hash_index()`: 重建哈希索引（用于数据恢复）

#### 使用方式
```python
# 自动查重（默认启用）
knowledge_id = knowledge_manager.create_knowledge(
    content="知识内容",
    modality="text",
    skip_duplicate=True  # 默认True，自动跳过重复
)
```

### 2. 知识图谱查重功能 ✅

#### 实现方式
- **实体查重**：基于实体名称（大小写不敏感）和类型进行查重
- **关系查重**：基于实体ID对和关系类型进行查重
- **智能匹配**：优先匹配相同类型的实体

#### 关键实现
- `EntityManager.create_entity()`: 支持 `skip_duplicate` 参数
- `RelationManager.create_relation()`: 支持 `skip_duplicate` 参数
- `GraphBuilder.build_from_structured_data()`: 自动启用查重

#### 使用方式
```python
# 实体查重
entity_id = entity_manager.create_entity(
    name="实体名称",
    entity_type="Person",
    skip_duplicate=True  # 默认True，自动跳过重复
)

# 关系查重
relation_id = relation_manager.create_relation(
    entity1_id=entity1_id,
    entity2_id=entity2_id,
    relation_type="mother_of",
    skip_duplicate=True  # 默认True，自动跳过重复
)
```

### 3. 向量知识库与知识图谱同步构建 ✅

#### 实现方式
- **自动提取**：从知识内容和元数据中自动提取实体和关系
- **同步构建**：在导入知识到向量库的同时，构建知识图谱
- **多种提取策略**：
  1. 从元数据中的结构化信息提取（entities/relations）
  2. 从FRAMES格式数据中提取（query/answer字段）
  3. 基于模式匹配的关系提取（未来可扩展NER/RE模型）

#### 关键实现
- `KnowledgeManagementService.import_knowledge()`: 集成查重和知识图谱构建
- `KnowledgeManagementService._extract_entities_and_relations()`: 提取实体和关系
- `GraphBuilder.build_from_structured_data()`: 构建知识图谱

#### 工作流程
```
导入知识
  ↓
查重检查（跳过重复知识）
  ↓
创建知识条目
  ↓
向量化并添加到向量索引
  ↓
提取实体和关系
  ↓
构建知识图谱（自动查重实体和关系）
```

## 统计信息

导入时会显示：
- **新增知识数量**：实际创建的新知识条目
- **重复跳过数量**：检测到重复并跳过的条目
- **实体创建数量**：新创建的实体数量
- **关系创建数量**：新创建的关系数量

示例日志：
```
导入知识完成: 824 条（新增: 600, 重复跳过: 224）
知识图谱构建: 150个实体, 200条关系
```

## 数据结构

### 知识条目元数据
```json
{
  "entries": {
    "knowledge_id": {
      "id": "knowledge_id",
      "modality": "text",
      "content_preview": "...",
      "metadata": {
        "content": "完整内容..."
      },
      "content_hash": "sha256哈希值",
      "created_at": "...",
      "updated_at": "...",
      "version": 1
    }
  },
  "content_hash_index": {
    "hash_value": "knowledge_id"
  }
}
```

### 知识图谱数据
- **实体文件**: `data/knowledge_management/graph/entities.json`
- **关系文件**: `data/knowledge_management/graph/relations.json`

## 性能优化

1. **O(1) 查重**：使用哈希索引实现快速查重
2. **批量处理**：支持批量导入时的批量查重
3. **增量更新**：只处理新知识，跳过已存在的知识

## 未来扩展

1. **智能实体提取**：集成NER（命名实体识别）模型
2. **智能关系提取**：集成RE（关系抽取）模型
3. **相似度查重**：基于向量相似度的模糊查重（当前是精确匹配）
4. **版本管理**：支持知识条目的版本控制和更新

## 注意事项

1. **内容哈希**：基于完整内容计算，内容完全相同才会被认为是重复
2. **实体查重**：基于名称（大小写不敏感）和类型，不同名称的实体不会被认为是重复
3. **关系查重**：相同实体对和关系类型的组合不会重复创建
4. **图谱构建**：目前主要依赖结构化数据，文本自动提取功能需要NER/RE模型支持

