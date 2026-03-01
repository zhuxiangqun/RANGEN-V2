# 知识库管理系统架构文档

**系统编号**: 第四系统  
**设计原则**: 完全独立，零耦合，支持多模态扩展

---

## 🏗️ 系统架构

### 系统定位

知识库管理系统是第四个独立系统，专门负责：
1. **知识库建立**：导入、处理、存储知识
2. **知识库维护**：更新、删除、版本管理
3. **向量索引管理**：构建和维护向量索引
4. **多模态支持**：文本、图像、音频、视频等

### 独立性保证

✅ **零耦合设计**：
- 不导入核心系统模块
- 不导入评测系统模块
- 不导入质量分析系统模块
- 独立的依赖、配置、日志系统

✅ **标准接口**：
- 通过`service_interface.py`提供服务
- 其他系统通过标准函数调用，不直接访问内部实现

---

## 📦 模块结构

### 1. 核心模块 (`core/`)

#### `knowledge_importer.py`
- **功能**：知识导入
- **支持格式**：JSON、CSV、字典、列表
- **数据验证**：自动验证数据格式和内容

#### `knowledge_manager.py`
- **功能**：知识CRUD操作
- **特性**：
  - 创建、读取、更新、删除知识
  - 版本控制
  - 分类和标签管理
  - 统计信息

#### `vector_index_builder.py`
- **功能**：向量索引构建和维护
- **特性**：
  - FAISS索引创建和管理
  - 向量添加和搜索
  - 索引重建
  - 多模态向量支持

### 2. 多模态模块 (`modalities/`)

#### 基类：`ModalityProcessor`
```python
class ModalityProcessor(ABC):
    @abstractmethod
    def encode(self, data: Any) -> Optional[np.ndarray]
    @abstractmethod
    def validate(self, data: Any) -> bool
    def get_dimension(self) -> int
```

#### 实现类：
- **`TextProcessor`** ✅ 已实现（使用Jina Embedding）
- **`ImageProcessor`** 📋 框架已准备（待实现CLIP）
- **`AudioProcessor`** 📋 框架已准备（待实现Wav2Vec）
- **`VideoProcessor`** 📋 框架已准备（待实现Video-CLIP）

### 3. 存储模块 (`storage/`)

#### `vector_storage.py`
- **功能**：向量索引存储管理
- **后端**：FAISS索引文件

#### `metadata_storage.py`
- **功能**：元数据存储管理
- **后端**：JSON文件

### 4. API接口 (`api/`)

#### `service_interface.py`
- **功能**：标准服务接口（供其他系统调用）
- **主要方法**：
  - `import_knowledge()` - 导入知识
  - `query_knowledge()` - 查询知识
  - `rebuild_index()` - 重建索引
  - `get_statistics()` - 获取统计

---

## 🔌 系统调用方式

### 核心系统调用（示例）

```python
# 核心系统代码（不直接导入内部模块）
from knowledge_management_system.api.service_interface import get_knowledge_service

# 获取服务实例（单例）
service = get_knowledge_service()

# 查询知识
results = service.query_knowledge(
    query="Who is Jane Ballou?",
    modality="text",
    top_k=5
)

# 导入知识（如果需要）
knowledge_ids = service.import_knowledge(
    data=[{"content": "知识内容"}],
    modality="text",
    source_type="list"
)
```

### 独立性验证

✅ **核心系统不直接访问**：
- ❌ 不导入 `knowledge_management_system.core.*`
- ❌ 不导入 `knowledge_management_system.modalities.*`
- ❌ 不导入 `knowledge_management_system.storage.*`
- ✅ 只导入 `knowledge_management_system.api.service_interface`

---

## 🎯 多模态扩展

### 当前状态

- ✅ **文本模态**：完全实现（Jina Embedding）
- 📋 **图像模态**：框架已准备（待实现CLIP）
- 📋 **音频模态**：框架已准备（待实现Wav2Vec）
- 📋 **视频模态**：框架已准备（待实现Video-CLIP）

### 扩展方式

```python
# 1. 在对应processor中实现encode和validate方法
class ImageProcessor(ModalityProcessor):
    def encode(self, data: Any) -> Optional[np.ndarray]:
        # 实现图像向量化逻辑
        pass

# 2. 在config/system_config.json中启用
{
  "modalities": {
    "image": {
      "enabled": true,  # 启用
      "encoder": "clip"
    }
  }
}

# 3. 系统自动识别并使用
```

---

## 📊 数据流

### 导入流程

```
数据源（JSON/CSV/字典）
  ↓
KnowledgeImporter（导入和验证）
  ↓
KnowledgeManager（创建知识条目）
  ↓
ModalityProcessor（向量化）
  ↓
VectorIndexBuilder（添加到索引）
  ↓
保存到存储
```

### 查询流程

```
查询文本
  ↓
ModalityProcessor（向量化）
  ↓
VectorIndexBuilder（向量搜索）
  ↓
KnowledgeManager（获取完整内容）
  ↓
返回结果
```

---

## ✅ 系统独立性检查清单

- ✅ 独立目录结构
- ✅ 独立依赖（requirements.txt）
- ✅ 独立配置（config/system_config.json）
- ✅ 独立日志系统（utils/logger.py）
- ✅ 标准服务接口（api/service_interface.py）
- ✅ 不导入其他系统模块
- ✅ 其他系统通过接口调用，不直接访问内部

---

## 🚀 使用示例

### 示例1：导入FRAMES数据集知识

```python
from knowledge_management_system.api.service_interface import get_knowledge_service

service = get_knowledge_service()

# 从FRAMES数据集导入知识
knowledge_ids = service.import_knowledge(
    data="data/frames_benchmark/documents.json",
    modality="text",
    source_type="json"
)

print(f"导入 {len(knowledge_ids)} 条知识")
```

### 示例2：查询知识

```python
# 查询知识
results = service.query_knowledge(
    query="Who is Jane Ballou?",
    modality="text",
    top_k=5
)

for result in results:
    print(f"相似度: {result['similarity_score']:.2f}")
    print(f"内容: {result['content']}")
```

### 示例3：重建索引

```python
# 重建索引（当向量维度变化时）
success = service.rebuild_index()
print(f"索引重建: {'成功' if success else '失败'}")
```

---

## 🔧 配置说明

### 配置文件：`config/system_config.json`

```json
{
  "storage": {
    "vector_index_path": "data/knowledge_management/vector_index.bin",
    "metadata_path": "data/knowledge_management/metadata.json"
  },
  "vector": {
    "default_dimension": 768,
    "similarity_threshold": 0.7
  },
  "modalities": {
    "text": {
      "enabled": true,
      "encoder": "jina"
    },
    "image": {
      "enabled": false,
      "encoder": "clip"
    }
  }
}
```

---

## 📋 下一步开发

1. **实现图像模态**：集成CLIP模型
2. **实现音频模态**：集成Wav2Vec模型
3. **实现视频模态**：集成Video-CLIP模型
4. **REST API**：提供HTTP接口（可选）
5. **批量导入优化**：支持大规模数据导入
6. **索引优化**：支持更高效的索引类型（IVF、HNSW等）

---

**系统状态**: ✅ 基础架构已完成，文本模态已实现，多模态框架已准备

