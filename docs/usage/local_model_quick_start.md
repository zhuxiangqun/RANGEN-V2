# 本地模型快速开始指南

## 一、快速安装

```bash
# 1. 安装依赖
pip install transformers torch

# 2. 验证安装
python -c "import transformers; print('✅ transformers 安装成功')"
```

## 二、快速使用

### 最简单的使用方式

```python
from src.services.local_model_extract_service import HybridExtractService

# 自动选择：如果没有 GOOGLE_API_KEY，使用本地模型
service = HybridExtractService()

# 使用
result = await service.extract_from_evidence(
    evidence=[{"content": "文本内容", "source": "来源"}],
    schema={},
    query="查询"
)
```

### 强制使用本地模型

```python
from src.services.local_model_extract_service import LocalModelExtractService

# 直接使用本地模型
service = LocalModelExtractService(
    model_name="distilbert-base-uncased",
    task="ner"  # 命名实体识别
)
```

## 三、运行示例

```bash
# 运行示例代码
python examples/local_model_example.py
```

## 四、配置

### 开发环境（.env 文件）

```env
# 不设置 GOOGLE_API_KEY，自动使用本地模型
# GOOGLE_API_KEY=

# 或明确指定
USE_LOCAL_MODEL=true
LOCAL_MODEL_NAME=distilbert-base-uncased
```

### 生产环境（.env 文件）

```env
# 使用 LangExtract + Google Gemini
USE_LOCAL_MODEL=false
GOOGLE_API_KEY=your-api-key-here
```

## 五、推荐模型

| 场景 | 推荐模型 | 说明 |
|------|---------|------|
| 开发/测试 | `distilbert-base-uncased` | 轻量、快速 |
| 功能验证 | `bert-base-uncased` | 平衡性能 |
| 高准确度 | `roberta-base` | 性能最佳 |
| 中文支持 | `bert-base-chinese` | 中文模型 |

## 六、常见问题

### Q: 首次运行很慢？

**A**: 首次运行需要下载模型，请耐心等待。模型会缓存到本地，后续运行会很快。

### Q: 内存不足？

**A**: 使用更小的模型 `distilbert-base-uncased`，或使用 CPU 模式。

### Q: 如何切换到生产环境？

**A**: 设置 `GOOGLE_API_KEY` 环境变量，系统会自动使用 LangExtract。

## 七、更多信息

- 详细文档：[本地模型开发环境指南](./local_model_development_guide.md)
- 集成方案：[LangExtract 集成方案](../architecture/langgraph_architectural_refactoring.md#十langextract-集成方案rag-增强版)

