# 本地模型开发环境指南

## 一、概述

为了在开发环境中降低成本和加快开发速度，系统支持使用小型本地模型（如 DistilBERT）替代 Google Gemini API。

### 优势

- ✅ **零成本**：不需要 Google API Key，完全本地运行
- ✅ **快速响应**：无需网络请求，本地推理速度快
- ✅ **隐私保护**：数据不离开本地环境
- ✅ **离线开发**：可以在没有网络的环境下开发

### 适用场景

- 开发环境
- 本地测试
- 功能验证
- 原型开发

## 二、安装依赖

### 基础依赖

```bash
# 安装 transformers 和 torch
pip install transformers torch

# 如果需要 GPU 加速（可选）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 完整安装（包含 LangExtract）

```bash
# 安装所有依赖
pip install transformers torch
pip install langextract  # 可选，用于生产环境
```

## 三、配置

### 方法1：环境变量（推荐）

```bash
# 不使用 Google API Key，自动使用本地模型
# 不设置 GOOGLE_API_KEY 或设置为空
unset GOOGLE_API_KEY

# 或者明确指定使用本地模型
export USE_LOCAL_MODEL=true
export LOCAL_MODEL_NAME=distilbert-base-uncased
```

### 方法2：代码配置

```python
from src.services.local_model_extract_service import HybridExtractService

# 强制使用本地模型
service = HybridExtractService(
    use_local_model=True,
    local_model_name="distilbert-base-uncased"
)

# 或者自动检测（如果没有 GOOGLE_API_KEY，使用本地模型）
service = HybridExtractService()
```

### 方法3：配置文件

在 `.env` 文件中：

```env
# 开发环境：使用本地模型
USE_LOCAL_MODEL=true
LOCAL_MODEL_NAME=distilbert-base-uncased

# 生产环境：使用 LangExtract（需要设置 GOOGLE_API_KEY）
# USE_LOCAL_MODEL=false
# GOOGLE_API_KEY=your-api-key-here
```

## 四、支持的模型

### 推荐模型（按性能排序）

#### 1. DistilBERT（推荐用于开发）

```python
service = HybridExtractService(
    use_local_model=True,
    local_model_name="distilbert-base-uncased"
)
```

**特点**：
- ✅ 轻量级（66M 参数）
- ✅ 快速推理
- ✅ 内存占用小
- ⚠️ 准确度略低于 BERT

#### 2. BERT Base

```python
service = HybridExtractService(
    use_local_model=True,
    local_model_name="bert-base-uncased"
)
```

**特点**：
- ✅ 标准 BERT 模型
- ✅ 准确度较高
- ⚠️ 模型较大（110M 参数）
- ⚠️ 推理速度较慢

#### 3. RoBERTa Base

```python
service = HybridExtractService(
    use_local_model=True,
    local_model_name="roberta-base"
)
```

**特点**：
- ✅ 性能优于 BERT
- ✅ 准确度高
- ⚠️ 模型较大（125M 参数）

#### 4. 中文模型（如果需要中文支持）

```python
service = HybridExtractService(
    use_local_model=True,
    local_model_name="bert-base-chinese"
)
```

## 五、使用示例

### 示例1：基本使用

```python
import asyncio
from src.services.local_model_extract_service import LocalModelExtractService

async def main():
    # 初始化本地模型服务
    service = LocalModelExtractService(
        model_name="distilbert-base-uncased",
        task="ner"  # 命名实体识别
    )
    
    # 准备证据
    evidence = [
        {
            "content": "Barack Obama was the 44th President of the United States.",
            "source": "wikipedia"
        }
    ]
    
    # 提取结构化信息
    result = await service.extract_from_evidence(
        evidence=evidence,
        schema={"type": "object", "properties": {}},
        query="Who was the 44th President?"
    )
    
    print("提取的实体：")
    for entity in result["entities"]:
        print(f"  - {entity['text']} ({entity['type']})")

if __name__ == "__main__":
    asyncio.run(main())
```

### 示例2：混合模式（自动选择）

```python
import asyncio
from src.services.local_model_extract_service import HybridExtractService

async def main():
    # 自动选择：如果有 GOOGLE_API_KEY 使用 LangExtract，否则使用本地模型
    service = HybridExtractService()
    
    evidence = [
        {
            "content": "The capital of France is Paris.",
            "source": "geography_book"
        }
    ]
    
    result = await service.extract_answer_with_source(
        query="What is the capital of France?",
        evidence=evidence
    )
    
    print(f"答案: {result['answer']}")
    print(f"置信度: {result['confidence']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 示例3：集成到现有系统

```python
# src/core/reasoning/evidence_preprocessor.py (修改版)

from src.services.local_model_extract_service import HybridExtractService

class EvidencePreprocessor:
    def __init__(self):
        # 使用混合服务，自动选择本地模型或 LangExtract
        self.extract_service = HybridExtractService()
    
    async def preprocess_evidence(self, evidence, query):
        # 使用提取服务
        structured_info = await self.extract_service.extract_from_evidence(
            evidence=evidence,
            schema=self._build_schema(query),
            query=query
        )
        
        # 处理提取结果
        # ...
```

## 六、性能对比

### 模型性能对比

| 模型 | 参数量 | 推理速度 | 准确度 | 内存占用 | 推荐场景 |
|------|--------|---------|--------|----------|----------|
| DistilBERT | 66M | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 开发环境 |
| BERT Base | 110M | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 平衡场景 |
| RoBERTa Base | 125M | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 高准确度需求 |
| Google Gemini | - | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 生产环境 |

### 成本对比

| 方案 | 成本 | 速度 | 准确度 | 隐私 |
|------|------|------|--------|------|
| 本地模型 | 免费 | 快 | 中等 | 高 |
| Google Gemini | 按使用付费 | 中等 | 高 | 中等 |

## 七、最佳实践

### 1. 开发环境配置

```bash
# .env.development
USE_LOCAL_MODEL=true
LOCAL_MODEL_NAME=distilbert-base-uncased
# 不设置 GOOGLE_API_KEY
```

### 2. 生产环境配置

```bash
# .env.production
USE_LOCAL_MODEL=false
GOOGLE_API_KEY=your-api-key-here
```

### 3. 混合模式（推荐）

```python
# 自动根据环境选择
service = HybridExtractService()
```

### 4. 模型选择建议

- **开发/测试**：使用 `distilbert-base-uncased`（快速、轻量）
- **功能验证**：使用 `bert-base-uncased`（平衡）
- **生产环境**：使用 `gemini-1.5-pro`（高准确度）

## 八、故障排除

### 问题1：模型下载失败

**解决方案**：

```bash
# 使用镜像源
export HF_ENDPOINT=https://hf-mirror.com

# 或手动下载模型
python -c "from transformers import AutoModel; AutoModel.from_pretrained('distilbert-base-uncased')"
```

### 问题2：内存不足

**解决方案**：

```python
# 使用更小的模型
service = LocalModelExtractService(
    model_name="distilbert-base-uncased",  # 最小模型
    device="cpu"  # 使用 CPU（如果 GPU 内存不足）
)
```

### 问题3：推理速度慢

**解决方案**：

```python
# 使用 GPU 加速
service = LocalModelExtractService(
    model_name="distilbert-base-uncased",
    device="cuda"  # 如果有 GPU
)

# 或使用更小的模型
service = LocalModelExtractService(
    model_name="distilbert-base-uncased"  # 已经是最小的了
)
```

## 九、下一步

1. 查看 [LangExtract 集成方案](../architecture/langgraph_architectural_refactoring.md#十langextract-集成方案rag-增强版)
2. 配置开发环境使用本地模型
3. 测试功能是否正常
4. 部署到生产环境时切换到 LangExtract

