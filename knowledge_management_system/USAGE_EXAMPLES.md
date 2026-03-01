# 知识库管理系统使用示例

**系统编号**: 第四系统  
**使用方式**: 通过标准接口调用，保持系统独立性

---

## 📋 基本使用

### 1. 导入知识

#### 从JSON文件导入

```python
from knowledge_management_system.api.service_interface import get_knowledge_service

service = get_knowledge_service()

# 导入JSON文件中的知识
knowledge_ids = service.import_knowledge(
    data="data/frames_benchmark/documents.json",
    modality="text",
    source_type="json"
)

print(f"成功导入 {len(knowledge_ids)} 条知识")
```

#### 从字典导入

```python
# 单个知识条目
knowledge_data = {
    "content": "Jane Ballou was the mother of James A. Garfield, the 20th President of the United States.",
    "metadata": {
        "source": "FRAMES dataset",
        "category": "history"
    }
}

knowledge_id = service.import_knowledge(
    data=knowledge_data,
    modality="text",
    source_type="dict"
)
```

#### 从列表导入

```python
# 批量导入
knowledge_list = [
    {"content": "知识1", "metadata": {"source": "source1"}},
    {"content": "知识2", "metadata": {"source": "source2"}},
    {"content": "知识3", "metadata": {"source": "source3"}}
]

knowledge_ids = service.import_knowledge(
    data=knowledge_list,
    modality="text",
    source_type="list"
)
```

---

### 2. 查询知识

```python
# 查询知识
results = service.query_knowledge(
    query="Who is Jane Ballou?",
    modality="text",
    top_k=5,
    similarity_threshold=0.7
)

for result in results:
    print(f"相似度: {result['similarity_score']:.2f}")
    print(f"内容: {result['content']}")
    print(f"知识ID: {result['knowledge_id']}")
    print("---")
```

---

### 3. 获取统计信息

```python
stats = service.get_statistics()

print(f"总知识条目数: {stats['total_entries']}")
print(f"向量索引大小: {stats['vector_index_size']}")
print(f"模态分布: {stats['modality_distribution']}")
```

---

### 4. 重建索引

```python
# 当向量维度变化或需要优化索引时
success = service.rebuild_index()

if success:
    print("索引重建成功")
else:
    print("索引重建失败")
```

---

## 🔌 核心系统集成示例

### 在核心系统中使用（保持独立性）

```python
# src/agents/enhanced_knowledge_retrieval_agent.py

async def _get_knowledge_from_management_system(self, query: str) -> Optional[Dict[str, Any]]:
    """从知识库管理系统获取知识（独立接口调用）"""
    try:
        # ✅ 只导入接口，不导入内部模块
        from knowledge_management_system.api.service_interface import get_knowledge_service
        
        service = get_knowledge_service()
        
        # 查询知识
        results = service.query_knowledge(
            query=query,
            modality="text",
            top_k=3
        )
        
        if results:
            best_result = results[0]
            return {
                'content': best_result['content'],
                'confidence': best_result['similarity_score'],
                'source': 'knowledge_management_system',
                'metadata': best_result.get('metadata', {})
            }
        
        return None
        
    except ImportError:
        # 如果知识库管理系统不可用，静默失败
        logger.debug("知识库管理系统不可用")
        return None
    except Exception as e:
        logger.error(f"从知识库管理系统获取知识失败: {e}")
        return None
```

---

## 🚀 FRAMES数据集导入示例

### 导入FRAMES数据集知识

```python
from knowledge_management_system.api.service_interface import get_knowledge_service
import json

service = get_knowledge_service()

# 读取FRAMES数据集
with open('data/frames_benchmark/documents.json', 'r', encoding='utf-8') as f:
    frames_data = json.load(f)

# 转换为知识条目格式
knowledge_entries = []
for doc in frames_data:
    knowledge_entries.append({
        "content": doc.get('text', '') or doc.get('content', ''),
        "metadata": {
            "source": "FRAMES dataset",
            "doc_id": doc.get('id', ''),
            "title": doc.get('title', '')
        }
    })

# 导入知识
knowledge_ids = service.import_knowledge(
    data=knowledge_entries,
    modality="text",
    source_type="list"
)

print(f"成功导入 {len(knowledge_ids)} 条FRAMES知识")
```

---

## 📊 批量操作示例

### 批量导入和验证

```python
import os
from pathlib import Path

service = get_knowledge_service()

# 批量导入多个文件
data_dir = Path("data/knowledge_sources")
total_imported = 0

for json_file in data_dir.glob("*.json"):
    print(f"导入文件: {json_file.name}")
    knowledge_ids = service.import_knowledge(
        data=str(json_file),
        modality="text",
        source_type="json"
    )
    total_imported += len(knowledge_ids)
    print(f"  导入 {len(knowledge_ids)} 条知识")

print(f"\n总共导入 {total_imported} 条知识")

# 获取最终统计
stats = service.get_statistics()
print(f"知识库总条目: {stats['total_entries']}")
```

---

## ✅ 独立性验证示例

```python
# 验证系统独立性
import sys

# 检查导入
try:
    from knowledge_management_system.api.service_interface import get_knowledge_service
    
    # ✅ 应该可以导入接口
    print("✅ 接口导入成功")
    
    # ❌ 不应该直接导入核心模块（虽然技术上可能可以，但不应该这样做）
    try:
        from knowledge_management_system.core.knowledge_manager import KnowledgeManager
        print("⚠️ 警告：不应该直接导入核心模块")
    except ImportError:
        print("✅ 核心模块未暴露（符合独立性要求）")
    
    # 测试服务
    service = get_knowledge_service()
    stats = service.get_statistics()
    print(f"✅ 服务可用，知识库条目: {stats['total_entries']}")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
```

---

## 🎯 多模态使用示例（待扩展）

### 文本模态（已实现）

```python
# 文本知识导入和查询
service = get_knowledge_service()

# 导入文本知识
knowledge_id = service.import_knowledge(
    data={"content": "文本内容"},
    modality="text"
)

# 查询文本知识
results = service.query_knowledge(
    query="查询文本",
    modality="text"
)
```

### 图像模态（待实现）

```python
# 未来使用示例
service = get_knowledge_service()

# 导入图像知识（待实现）
knowledge_id = service.import_knowledge(
    data={"image_path": "path/to/image.jpg"},
    modality="image"
)

# 查询图像知识（待实现）
results = service.query_knowledge(
    query="图像描述或路径",
    modality="image"
)
```

---

## 📝 注意事项

### 1. 系统独立性

✅ **正确方式**：
```python
from knowledge_management_system.api.service_interface import get_knowledge_service
```

❌ **错误方式**（虽然可能可行，但违反独立性原则）：
```python
from knowledge_management_system.core.knowledge_manager import KnowledgeManager
```

### 2. 依赖管理

- 知识库管理系统有独立的`requirements.txt`
- 需要单独安装依赖：`pip install -r knowledge_management_system/requirements.txt`

### 3. 配置管理

- 使用独立的配置文件：`config/system_config.json`
- 不读取其他系统的配置

---

**系统状态**: ✅ 基础功能已完成，可以开始使用

