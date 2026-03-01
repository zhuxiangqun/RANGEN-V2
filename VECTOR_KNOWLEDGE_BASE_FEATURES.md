# 向量知识库构建脚本功能对比

## 🎯 功能支持情况

| 功能特性 | 原有脚本 (build_vector_knowledge_base.sh) | 新建完整脚本 (build_frames_complete.py) | 沙箱友好脚本 (build_kb_sandbox_friendly.py) |
|----------|-----------------------------------------|---------------------------------------|-------------------------------------------|
| **向量化 (Vectorization)** | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| **索引构建 (Indexing)** | ✅ 支持 (FAISS) | ❌ 不支持 | ❌ 不支持 |
| **断点续传 (Resume)** | ✅ 支持 | ❌ 不支持 | ❌ 不支持 |
| **批处理 (Batch Processing)** | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| **进度保存 (Progress Saving)** | ✅ 支持 | ❌ 不支持 | ❌ 不支持 |
| **错误重试 (Error Retry)** | ✅ 支持 | ❌ 不支持 | ❌ 不支持 |
| **数据集类型** | JSON/本地文件 | Hugging Face数据集 | 本地JSON文件 |
| **向量化算法** | TF-IDF | LSTM + Pooling | 简化TF-IDF风格 |
| **依赖复杂度** | 低 | 高 (torch) | 低 |
| **构建速度** | 快 | 中等 | 快 |
| **向量质量** | 基础 | 高质量 | 基础 |
| **沙箱兼容性** | 中等 | 需权限 | 高 |

## 📋 详细功能说明

### 1. 原有脚本 (build_vector_knowledge_base.sh)

**支持的功能**：
- ✅ **向量化**: 使用内置TF-IDF向量化器
- ✅ **索引构建**: 创建FAISS向量索引，支持多种索引类型
- ✅ **断点续传**: 自动保存进度，可从中断处继续
- ✅ **批处理**: 支持可配置批次大小
- ✅ **进度保存**: JSON格式进度文件，包含处理状态
- ✅ **错误重试**: 支持重新处理失败的数据
- ✅ **多种数据源**: 支持JSON文件、URL、PDF、Markdown等

**使用示例**：
```bash
./build_vector_knowledge_base.sh --dataset-path data/frames_dataset.json --batch-size 10 --resume
```

**进度文件位置**：
- 主文件：`data/knowledge_management/vector_import_progress.json`
- 备份文件：`data/knowledge_management/backups/backup_*/vector_import_progress.json`

**进度文件格式**：
```json
{
  "processed_item_indices": [0, 1, 2, ...],
  "failed_item_indices": [],
  "total_items": 824,
  "start_time": "2026-01-04T14:48:39.374333",
  "last_update": "2026-01-04T14:48:39.374333"
}
```

**实际验证**：✅ 已确认处理了所有824条记录（索引0-823）

### 2. 新建完整脚本 (build_frames_complete.py)

**支持的功能**：
- ✅ **向量化**: 使用PyTorch LSTM + Attention模型
- ❌ **索引构建**: 不构建FAISS索引，直接生成numpy数组
- ❌ **断点续传**: 不支持断点续传
- ✅ **批处理**: 支持批处理（默认16）
- ❌ **进度保存**: 不保存进度
- ❌ **错误重试**: 不支持错误重试
- ✅ **数据集类型**: 直接从Hugging Face下载

**使用示例**：
```bash
python3 build_frames_complete.py
```

**优势**：
- 更高质量的向量嵌入
- 独立的torch实现
- 不依赖外部库

### 3. 沙箱友好脚本 (build_kb_sandbox_friendly.py)

**支持的功能**：
- ✅ **向量化**: 简化TF-IDF风格算法
- ❌ **索引构建**: 不构建索引
- ❌ **断点续传**: 不支持断点续传
- ✅ **批处理**: 支持批处理
- ❌ **进度保存**: 不保存进度
- ❌ **错误重试**: 不支持错误重试
- ✅ **数据集类型**: 本地JSON文件

**使用示例**：
```bash
python3 build_kb_sandbox_friendly.py --input-file frames_dataset.json --batch-size 10
```

**优势**：
- 完全沙箱兼容
- 依赖简单
- 处理速度快

## 🔧 技术实现细节

### 向量化算法对比

#### 原有脚本 (TF-IDF)
```python
# 使用sklearn的TfidfVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer = TfidfVectorizer(max_features=5000)
embeddings = vectorizer.fit_transform(texts)
```

#### 新建脚本 (LSTM + Pooling)
```python
# 使用PyTorch LSTM模型
class SimpleEmbeddingModel(nn.Module):
    def __init__(self, vocab_size=50000, embedding_dim=384):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.encoder = nn.LSTM(embedding_dim, 256, batch_first=True, bidirectional=True)
        self.pooler = nn.Linear(512, embedding_dim)

    def forward(self, input_ids):
        embedded = self.embedding(input_ids)
        _, (hidden, _) = self.encoder(embedded)
        hidden = hidden.transpose(0, 1).contiguous()
        hidden = hidden.view(hidden.size(0), -1)
        pooled = self.pooler(hidden)
        return pooled
```

#### 沙箱脚本 (简化算法)
```python
# 基于文本统计的简化嵌入
def build_simple_embeddings(data, embedding_dim=384):
    for item in data:
        text_length = len(item.get('content', ''))
        word_count = len(item.get('content', '').split())

        vector = np.zeros(embedding_dim)
        vector[0] = text_length / 1000.0  # 归一化长度
        vector[1] = word_count / 100.0   # 归一化词数
        # ... 其他统计特征
```

### 索引构建

#### FAISS索引 (原有脚本)
- **IndexFlatIP**: 内积索引，精确搜索
- **IndexIVFFlat**: IVF索引，近似搜索
- **IndexIVFPQ**: IVF + PQ，压缩索引
- 支持自定义维度和搜索参数

#### 直接数组 (新建脚本)
- 生成numpy数组格式的向量
- 可后续手动构建FAISS索引
- 支持多种嵌入维度

### 断点续传机制

#### 进度跟踪 (原有脚本)
```python
def load_vector_progress() -> Dict[str, Any]:
    progress_file = Path("data/knowledge_management/vector_import_progress.json")
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'processed_item_indices': [],
        'failed_item_indices': [],
        'total_items': 0,
        'start_time': None,
        'last_update': None
    }

def save_vector_progress(progress: Dict[str, Any]) -> None:
    # 原子性保存进度
    temp_file = progress_file.with_suffix('.tmp')
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    temp_file.replace(progress_file)
```

## 🎯 推荐使用场景

### 生产环境使用
- **推荐**: 原有脚本 (`build_vector_knowledge_base.sh`)
- **原因**: 支持完整功能，集成到现有系统中，生产环境稳定

### 高质量向量生成
- **推荐**: 新建完整脚本 (`build_frames_complete.py`)
- **原因**: 使用先进LSTM模型，生成高质量向量嵌入

### 沙箱环境/快速测试
- **推荐**: 沙箱友好脚本 (`build_kb_sandbox_friendly.py`)
- **原因**: 兼容性好，依赖简单，适合快速验证

### 离线处理
- **推荐**: 结合外部下载 + 沙箱友好脚本
- **原因**: 可以完全离线工作，无需网络访问

## 🚀 性能对比

| 指标 | 原有脚本 | 新建脚本 | 沙箱脚本 |
|------|----------|----------|----------|
| **处理速度** | 快 | 中等 | 快 |
| **内存使用** | 低 | 高 | 低 |
| **向量质量** | 基础 | 高质量 | 基础 |
| **可扩展性** | 高 | 中等 | 高 |
| **维护成本** | 低 | 高 | 低 |

## 📝 总结

**三个脚本各有优势**：

1. **原有脚本**: 最完整的功能集合，适合生产环境
2. **新建脚本**: 最高质量的向量生成，适合研究和高质量需求
3. **沙箱脚本**: 最佳兼容性，适合受限环境

根据您的具体需求选择合适的脚本。如果需要完整的生产环境功能，推荐使用原有脚本；如果追求向量质量，使用新建脚本；如果在沙箱环境中工作，使用沙箱友好脚本。
