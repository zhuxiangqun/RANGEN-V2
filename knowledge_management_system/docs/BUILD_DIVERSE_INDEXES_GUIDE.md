# 构建多元化索引指南

## 📋 概述

本指南介绍如何从现有知识库构建LlamaIndex的多元化索引，包括：
- **树索引 (Tree Index)**: 适合层次化查询和摘要
- **关键词表索引 (Keyword Table Index)**: 适合精确关键词匹配
- **列表索引 (List Index)**: 适合顺序访问和列表查询
- **向量索引 (Vector Store Index)**: 适合语义相似度查询

## 🚀 快速开始

### 1. 前提条件

确保已安装LlamaIndex：
```bash
pip install 'llama-index[all]>=0.9.0'
```

### 2. 构建所有索引

```bash
cd knowledge_management_system/scripts
python build_diverse_indexes.py --index-types all
```

### 3. 构建特定索引

```bash
# 只构建树索引和关键词索引
python build_diverse_indexes.py --index-types tree keyword

# 只构建向量索引
python build_diverse_indexes.py --index-types vector
```

### 4. 构建并测试

```bash
python build_diverse_indexes.py --index-types all --test-query "What is the main topic?"
```

## 📊 索引类型说明

### 树索引 (Tree Index)

**适用场景**:
- 层次化查询（如："总结文档的主要内容"）
- 摘要查询
- 需要理解文档结构的查询

**构建命令**:
```bash
python build_diverse_indexes.py --index-types tree
```

### 关键词表索引 (Keyword Table Index)

**适用场景**:
- 精确关键词匹配
- 基于关键词的快速检索
- 不需要语义理解的查询（如："包含'Python'的文档"）

**构建命令**:
```bash
python build_diverse_indexes.py --index-types keyword
```

### 列表索引 (List Index)

**适用场景**:
- 顺序访问
- 需要保持文档顺序的查询
- 简单列表查询

**构建命令**:
```bash
python build_diverse_indexes.py --index-types list
```

### 向量索引 (Vector Store Index)

**适用场景**:
- 语义相似度查询
- 基于embedding的检索
- 模糊匹配查询

**构建命令**:
```bash
python build_diverse_indexes.py --index-types vector
```

## 🔧 集成到现有系统

### 方法1：在服务接口中启用索引管理器

修改 `knowledge_management_system/api/service_interface.py`:

```python
# 在 __init__ 中
if self.llamaindex_enabled:
    from ..integrations.llamaindex_adapter import LlamaIndexAdapter
    self.llamaindex_adapter = LlamaIndexAdapter(enable_llamaindex=True)
    
    # 🆕 初始化索引管理器
    if self.llamaindex_adapter:
        self.index_manager = self.llamaindex_adapter.get_index_manager()
```

### 方法2：在查询时使用路由查询引擎

修改 `query_knowledge` 方法:

```python
def query_knowledge(
    self,
    query: str,
    use_router: bool = False,  # 🆕 是否使用路由查询引擎
    ...
):
    # 如果使用路由查询引擎
    if use_router and self.index_manager:
        result = self.index_manager.query_with_router(query)
        # 转换结果格式
        return self._convert_llamaindex_result(result)
    
    # 否则使用现有逻辑
    ...
```

### 方法3：在导入知识时自动构建索引

修改 `import_knowledge` 方法:

```python
def import_knowledge(
    self,
    knowledge_data: Any,
    auto_build_indexes: bool = False,  # 🆕 是否自动构建索引
    index_types: List[str] = ['tree', 'keyword'],  # 🆕 要构建的索引类型
    ...
):
    # 现有导入逻辑
    ...
    
    # 🆕 自动构建索引
    if auto_build_indexes and self.index_manager:
        documents = self._convert_to_llamaindex_documents([...])
        for index_type in index_types:
            if index_type == 'tree':
                self.index_manager.build_tree_index(documents)
            elif index_type == 'keyword':
                self.index_manager.build_keyword_index(documents)
            # ...
```

## 📝 使用示例

### Python代码示例

```python
from knowledge_management_system.api.service_interface import get_knowledge_service
from knowledge_management_system.integrations.llamaindex_index_manager import LlamaIndexIndexManager

# 获取知识库服务
kms = get_knowledge_service()

# 获取索引管理器
index_manager = kms.llamaindex_adapter.get_index_manager() if kms.llamaindex_adapter else None

if index_manager:
    # 使用路由查询引擎（自动选择最佳索引）
    result = index_manager.query_with_router("What is the main topic?")
    print(result)
    
    # 或直接使用特定索引
    if index_manager.tree_index:
        result = index_manager.tree_index.as_query_engine().query("Summarize the document")
        print(result)
```

### 命令行示例

```bash
# 1. 构建所有索引
python build_diverse_indexes.py --index-types all

# 2. 构建特定索引并测试
python build_diverse_indexes.py \
    --index-types tree keyword \
    --test-query "What is Python?"

# 3. 保存索引到指定路径
python build_diverse_indexes.py \
    --index-types all \
    --save-path /path/to/indexes
```

## ⚠️ 注意事项

1. **内存占用**: 多元化索引会占用更多内存，建议根据实际需求选择索引类型
2. **构建时间**: 构建索引需要时间，特别是对于大型知识库
3. **索引更新**: 当知识库更新时，需要重新构建索引
4. **LlamaIndex版本**: 确保使用兼容的LlamaIndex版本

## 🔄 索引更新策略

### 策略1：增量更新

```python
# 只对新导入的知识构建索引
def import_knowledge_with_index_update(self, ...):
    # 导入知识
    new_entries = self.import_knowledge(...)
    
    # 转换为Document
    new_documents = convert_knowledge_to_documents(new_entries)
    
    # 更新索引（需要LlamaIndex支持）
    if self.index_manager and new_documents:
        # 注意：LlamaIndex的索引更新可能需要重建
        # 或者使用支持增量更新的索引类型
        pass
```

### 策略2：定期重建

```python
# 定期重建所有索引
def rebuild_all_indexes(self):
    from knowledge_management_system.scripts.build_diverse_indexes import build_diverse_indexes
    results = build_diverse_indexes(index_types=['all'])
    return results['success']
```

## 📈 性能优化建议

1. **选择性构建**: 只构建需要的索引类型
2. **分批处理**: 对于大型知识库，分批构建索引
3. **缓存索引**: 将构建好的索引保存到磁盘，避免重复构建
4. **异步构建**: 在后台异步构建索引，不阻塞主流程

## 🐛 故障排除

### 问题1：LlamaIndex未安装

**错误**: `ImportError: No module named 'llama_index'`

**解决**:
```bash
pip install 'llama-index[all]>=0.9.0'
```

### 问题2：索引构建失败

**错误**: `构建索引失败: ...`

**解决**:
- 检查知识库是否有数据
- 检查LlamaIndex版本是否兼容
- 查看详细错误日志

### 问题3：内存不足

**错误**: `MemoryError`

**解决**:
- 减少要构建的索引类型
- 分批处理知识条目
- 增加系统内存

## 📚 相关文档

- [LlamaIndex官方文档](https://docs.llamaindex.ai/)
- [LlamaIndex集成方案](../LLAMAINDEX_INTEGRATION_PROPOSAL.md)
- [知识库管理系统使用指南](../USAGE_EXAMPLES.md)

