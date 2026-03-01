# 数据集导入工具

## 功能说明

这个工具可以将各种数据集导入到向量知识库中，支持：

- ✅ Hugging Face 数据集（如 `google/frames-benchmark`）
- ✅ 本地 JSON 文件
- ✅ 本地 CSV 文件
- ✅ 本地 JSONL 文件

## ⚠️ 重要提示：JINA_API_KEY

**文本向量化需要 JINA_API_KEY 才能正常工作！**

如果没有设置API密钥，导入的数据将无法生成向量，无法进行向量搜索。

### 设置方法

#### 方法1：环境变量（推荐）

```bash
export JINA_API_KEY='your-api-key-here'
```

#### 方法2：配置文件

在 `knowledge_management_system/config/system_config.json` 中添加：

```json
{
  "api_keys": {
    "jina": "your-api-key-here"
  }
}
```

**注意**：不推荐在配置文件中存储API密钥，建议使用环境变量。

#### 获取API密钥

访问 https://jina.ai/ 注册并获取API密钥。

## 使用方法

### 方式1：使用 Shell 脚本（推荐）

**Shell 脚本位置**: `./scripts/import_dataset.sh`

```bash
# 在项目根目录下运行

# Hugging Face 数据集
./scripts/import_dataset.sh https://huggingface.co/datasets/google/frames-benchmark

# 或简化的路径格式
./scripts/import_dataset.sh google/frames-benchmark

# 本地 JSON 文件
./scripts/import_dataset.sh /path/to/dataset.json

# 本地 CSV 文件
./scripts/import_dataset.sh /path/to/dataset.csv
```

### 方式2：直接使用 Python 脚本

```bash
# 在项目根目录下运行
python knowledge_management_system/scripts/import_dataset.py google/frames-benchmark

# 指定批处理大小
python knowledge_management_system/scripts/import_dataset.py google/frames-benchmark --batch-size 200
```

## 示例

### 导入 FRAMES 数据集

```bash
./scripts/import_dataset.sh google/frames-benchmark
```

### 导入本地数据集

```bash
./scripts/import_dataset.sh data/my_knowledge.json
```

## 数据格式要求

### JSON 格式

```json
[
  {
    "content": "知识内容文本",
    "metadata": {
      "source": "数据来源",
      "category": "分类"
    }
  },
  ...
]
```

或：

```json
{
  "entries": [
    {
      "content": "知识内容",
      "metadata": {}
    }
  ]
}
```

### CSV 格式

CSV 文件应包含至少一个内容列（如 `content`、`text`、`query` 等），其他列将作为元数据。

## 依赖要求

如果导入 Hugging Face 数据集，需要安装 `datasets` 库：

```bash
pip install datasets
```

## 注意事项

1. **首次导入 Hugging Face 数据集**时会下载数据，可能需要一些时间
2. **大批量数据**会分批处理，默认每批100条
3. **向量化过程**需要 Jina API Key（如果使用 Jina Embedding）

## 验证导入结果

导入完成后，可以使用以下代码验证：

```python
from knowledge_management_system.api.service_interface import get_knowledge_service

service = get_knowledge_service()

# 获取统计信息
stats = service.get_statistics()
print(f"总条目数: {stats['total_entries']}")
print(f"向量索引大小: {stats['vector_index_size']}")

# 测试查询
results = service.query_knowledge("测试查询", top_k=5)
print(f"查询结果数: {len(results)}")
```

