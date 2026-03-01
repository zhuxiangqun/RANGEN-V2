# 知识库管理系统快速开始

**系统编号**: 第四系统  
**设计原则**: 完全独立，零耦合

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r knowledge_management_system/requirements.txt
```

### 2. 基本使用

```python
from knowledge_management_system.api.service_interface import get_knowledge_service

# 获取服务实例（单例）
service = get_knowledge_service()

# 导入知识
knowledge_ids = service.import_knowledge(
    data=[{"content": "知识内容"}],
    modality="text",
    source_type="list"
)

# 查询知识
results = service.query_knowledge(
    query="查询文本",
    modality="text",
    top_k=5
)

# 获取统计
stats = service.get_statistics()
```

---

## 📋 导入FRAMES数据集示例

```python
from knowledge_management_system.api.service_interface import get_knowledge_service
import json

service = get_knowledge_service()

# 读取FRAMES数据集
with open('data/frames_benchmark/documents.json', 'r', encoding='utf-8') as f:
    frames_data = json.load(f)

# 转换为知识条目
knowledge_entries = []
for doc in frames_data:
    knowledge_entries.append({
        "content": doc.get('text', '') or doc.get('content', ''),
        "metadata": {
            "source": "FRAMES dataset",
            "doc_id": doc.get('id', '')
        }
    })

# 导入知识
knowledge_ids = service.import_knowledge(
    data=knowledge_entries,
    modality="text",
    source_type="list"
)

print(f"成功导入 {len(knowledge_ids)} 条知识")
```

---

## ✅ 系统独立性

### 其他系统调用（正确方式）

```python
# ✅ 正确：通过标准接口调用
from knowledge_management_system.api.service_interface import get_knowledge_service

service = get_knowledge_service()
results = service.query_knowledge(query="...")
```

### 不应直接访问（违反独立性）

```python
# ❌ 不应该这样做（虽然技术上可能可行）
from knowledge_management_system.core.knowledge_manager import KnowledgeManager
```

---

## 📊 系统状态

- ✅ 基础架构已完成
- ✅ 文本模态已实现
- ✅ 多模态框架已准备
- ✅ 标准接口已提供
- ✅ 系统完全独立

---

详细文档：
- `README.md` - 系统说明
- `ARCHITECTURE.md` - 架构文档
- `USAGE_EXAMPLES.md` - 使用示例
- `SYSTEM_SUMMARY.md` - 系统总结

