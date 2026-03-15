# 🤖 本地模型使用指南

本文档介绍如何在RANGEN系统中使用本地模型替代云API，以降低成本和加快开发速度。

## 📋 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [安装配置](#安装配置)
4. [使用示例](#使用示例)
5. [高级配置](#高级配置)
6. [性能调优](#性能调优)
7. [常见问题](#常见问题)

## 📊 概述

### 为什么使用本地模型？

- ✅ **零成本**：不需要API Key，完全本地运行
- ✅ **快速响应**：无需网络请求，本地推理速度快
- ✅ **隐私保护**：数据不离开本地环境
- ✅ **离线开发**：可以在没有网络的环境下开发
- ✅ **可定制性**：可以微调模型以适应特定任务

### 适用场景

- **开发环境**：本地开发和测试
- **功能验证**：验证系统功能而不产生API成本
- **原型开发**：快速原型验证
- **离线场景**：在没有网络连接的环境中使用
- **数据敏感场景**：处理敏感数据，不希望发送到云端

### 支持的模型

系统支持以下本地模型：

1. **DistilBERT**：轻量级BERT模型，适合大多数NLP任务
2. **TinyBERT**：更小的BERT变体，适合资源受限环境
3. **MiniLM**：小型但强大的语言模型
4. **自定义模型**：支持加载自定义的HuggingFace模型

## 🚀 快速开始

### 最简单的使用方式

```python
from src.services.local_model_extract_service import HybridExtractService

# 自动选择：如果没有 GOOGLE_API_KEY，使用本地模型
service = HybridExtractService()

# 使用本地模型提取信息
result = await service.extract_from_evidence(
    evidence=[{"content": "文本内容", "source": "来源"}],
    schema={},
    query="查询"
)
```

### 手动指定使用本地模型

```python
from src.services.local_model_extract_service import HybridExtractService

# 强制使用本地模型
service = HybridExtractService(force_local=True)

# 或者通过环境变量
import os
os.environ['FORCE_LOCAL_MODEL'] = 'true'
```

## 📦 安装配置

### 基础依赖安装

```bash
# 安装 transformers 和 torch
pip install transformers torch

# 安装 sentence-transformers（用于嵌入）
pip install sentence-transformers

# 安装加速库（可选，提升性能）
pip install accelerate

# 验证安装
python -c "import transformers; import torch; print('✅ 所有依赖安装成功')"
```

### GPU加速（可选）

```bash
# 安装支持CUDA的PyTorch（需要NVIDIA GPU）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 验证GPU支持
python -c "import torch; print(f'CUDA可用: {torch.cuda.is_available()}')"
```

### 模型下载

系统会自动下载所需的模型，但您也可以手动下载：

```python
from transformers import AutoModel, AutoTokenizer

# 下载DistilBERT模型
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# 保存到本地缓存
model.save_pretrained("./models/distilbert")
tokenizer.save_pretrained("./models/distilbert")
```

## 💻 使用示例

### 基本提取任务

```python
from src.services.local_model_extract_service import HybridExtractService

async def basic_extraction():
    # 创建服务实例
    service = HybridExtractService()
    
    # 准备证据数据
    evidence = [
        {
            "content": "苹果公司于1976年4月1日由史蒂夫·乔布斯、史蒂夫·沃兹尼亚克和罗纳德·韦恩创立。",
            "source": "维基百科"
        },
        {
            "content": "苹果公司总部位于美国加利福尼亚州库比蒂诺。",
            "source": "公司官网"
        }
    ]
    
    # 定义提取模式
    schema = {
        "company_name": "string",
        "founders": "array",
        "founded_date": "string",
        "headquarters": "string"
    }
    
    # 执行提取
    result = await service.extract_from_evidence(
        evidence=evidence,
        schema=schema,
        query="提取苹果公司的基本信息"
    )
    
    # 输出结果
    if result.success:
        print(f"✅ 提取成功: {result.data}")
    else:
        print(f"❌ 提取失败: {result.error}")
    
    return result
```

### 批量处理

```python
async def batch_processing():
    service = HybridExtractService()
    
    # 批量证据
    batch_evidence = [
        {
            "id": "doc1",
            "evidence": [{"content": "内容1", "source": "来源1"}],
            "schema": {"field1": "string"},
            "query": "查询1"
        },
        {
            "id": "doc2",
            "evidence": [{"content": "内容2", "source": "来源2"}],
            "schema": {"field2": "string"},
            "query": "查询2"
        }
    ]
    
    # 批量提取
    results = await service.batch_extract(batch_evidence)
    
    for result in results:
        print(f"文档 {result.id}: {result.status}")
    
    return results
```

### 自定义模型

```python
from src.services.local_model_extract_service import CustomModelExtractService

async def custom_model_example():
    # 使用自定义模型路径
    model_path = "./models/my-custom-model"
    
    # 创建自定义模型服务
    service = CustomModelExtractService(
        model_path=model_path,
        device="cuda" if torch.cuda.is_available() else "cpu"
    )
    
    # 使用自定义模型
    result = await service.extract_from_evidence(
        evidence=[{"content": "文本内容", "source": "来源"}],
        schema={},
        query="查询"
    )
    
    return result
```

## ⚙️ 高级配置

### 配置选项

```python
from src.services.local_model_extract_service import HybridExtractService

# 高级配置示例
service = HybridExtractService(
    force_local=True,            # 强制使用本地模型
    model_name="distilbert-base-uncased",  # 指定模型
    max_length=512,              # 最大序列长度
    batch_size=8,                # 批量大小
    device="cuda:0",             # 使用指定GPU
    cache_dir="./model_cache",   # 模型缓存目录
    enable_caching=True,         # 启用结果缓存
    cache_ttl=3600               # 缓存有效期（秒）
)
```

### 环境变量配置

```bash
# 强制使用本地模型
export FORCE_LOCAL_MODEL=true

# 指定模型名称
export LOCAL_MODEL_NAME=distilbert-base-uncased

# 指定设备
export LOCAL_MODEL_DEVICE=cuda

# 启用详细日志
export LOCAL_MODEL_DEBUG=true

# 设置缓存目录
export LOCAL_MODEL_CACHE_DIR=./model_cache
```

### 性能配置

```python
# 性能优化配置
performance_config = {
    "use_fp16": True,           # 使用半精度浮点数（节省内存）
    "use_gradient_checkpointing": True,  # 梯度检查点（节省内存）
    "max_batch_size": 16,       # 最大批量大小
    "chunk_size": 128,          # 文本分块大小
    "overlap_size": 32,         # 分块重叠大小
    "enable_streaming": True    # 启用流式处理
}

service = HybridExtractService(**performance_config)
```

## 🚀 性能调优

### 内存优化

```python
# 内存优化配置
memory_config = {
    "use_gradient_checkpointing": True,  # 梯度检查点
    "use_8bit": True,                    # 8位量化（实验性）
    "use_4bit": True,                    # 4位量化（实验性）
    "offload_to_cpu": True,              # 将部分层卸载到CPU
    "max_memory": {0: "8GB"}             # 限制GPU内存使用
}

# 或者使用自动配置
from src.services.local_model_extract_service import OptimizedExtractService
service = OptimizedExtractService(mode="memory_efficient")
```

### 速度优化

```python
# 速度优化配置
speed_config = {
    "use_fp16": True,           # 半精度推理
    "use_cuda_graph": True,     # CUDA图优化（需要特定硬件）
    "batch_size": 32,           # 增加批量大小
    "num_workers": 4,           # 数据加载工作线程数
    "pin_memory": True          # 固定内存（加速数据传输）
}

service = HybridExtractService(**speed_config)
```

### 精度优化

```python
# 精度优化配置
accuracy_config = {
    "use_fp32": True,           # 全精度浮点数
    "max_length": 1024,         # 增加序列长度
    "num_beams": 5,             # 束搜索宽度
    "temperature": 0.7,         # 采样温度
    "top_p": 0.9,               # 核采样参数
    "repetition_penalty": 1.2   # 重复惩罚
}

service = HybridExtractService(**accuracy_config)
```

## 🛠️ 常见问题

### 问题1: 模型加载失败

**错误信息**:
```
OSError: Unable to load weights from pytorch checkpoint file
```

**解决方案**:
```bash
# 清理模型缓存
rm -rf ~/.cache/huggingface/hub

# 重新下载模型
python -c "from transformers import AutoModel; AutoModel.from_pretrained('distilbert-base-uncased', force_download=True)"

# 或者指定本地模型文件
export TRANSFORMERS_OFFLINE=1
export LOCAL_FILES_ONLY=1
```

### 问题2: 内存不足

**错误信息**:
```
CUDA out of memory
```

**解决方案**:
```python
# 减少批量大小
service = HybridExtractService(batch_size=2)

# 使用内存优化模式
from src.services.local_model_extract_service import OptimizedExtractService
service = OptimizedExtractService(mode="low_memory")

# 启用梯度检查点
service = HybridExtractService(use_gradient_checkpointing=True)
```

### 问题3: 推理速度慢

**解决方案**:
```python
# 启用GPU加速（如果有）
service = HybridExtractService(device="cuda")

# 启用半精度推理
service = HybridExtractService(use_fp16=True)

# 增加批量大小
service = HybridExtractService(batch_size=16)

# 使用更小的模型
service = HybridExtractService(model_name="google/bert_uncased_L-4_H-256_A-4")
```

### 问题4: 提取精度低

**解决方案**:
```python
# 使用更大的模型
service = HybridExtractService(model_name="bert-base-uncased")

# 增加序列长度
service = HybridExtractService(max_length=1024)

# 调整提取参数
service = HybridExtractService(
    num_beams=5,
    temperature=0.7,
    top_p=0.9
)

# 使用集成方法
from src.services.ensemble_extract_service import EnsembleExtractService
service = EnsembleExtractService(model_names=["distilbert", "roberta", "albert"])
```

## 📊 性能基准

### 硬件要求

| 配置 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 4核心 | 8核心或更多 |
| 内存 | 4GB | 16GB或更多 |
| 磁盘 | 2GB可用空间 | 10GB可用空间 |
| GPU | 可选 | NVIDIA GPU（8GB+显存） |

### 性能指标

| 模型 | 内存使用 | 推理速度 | 精度 |
|------|----------|----------|------|
| DistilBERT | 约 250MB | 100样本/秒 | 中等 |
| TinyBERT | 约 150MB | 150样本/秒 | 中等 |
| MiniLM | 约 200MB | 120样本/秒 | 中等 |
| BERT-base | 约 440MB | 50样本/秒 | 高 |

*注：性能指标基于CPU推理，批量大小=8*

## 🔧 高级功能

### 模型微调

```python
from src.services.model_finetuning import ModelFinetuningService

# 创建微调服务
finetuning = ModelFinetuningService(
    base_model="distilbert-base-uncased",
    task_type="extraction"
)

# 准备训练数据
training_data = [
    {
        "text": "苹果公司成立于1976年。",
        "labels": {"company": "苹果公司", "year": "1976"}
    },
    # 更多训练样本...
]

# 执行微调
finetuned_model = await finetuning.finetune(
    training_data=training_data,
    epochs=3,
    batch_size=8,
    learning_rate=2e-5
)

# 保存微调后的模型
finetuned_model.save_pretrained("./models/finetuned-distilbert")
```

### 模型评估

```python
from src.services.model_evaluation import ModelEvaluationService

# 创建评估服务
evaluation = ModelEvaluationService()

# 评估模型性能
metrics = await evaluation.evaluate_model(
    model_path="./models/finetuned-distilbert",
    test_data=test_dataset,
    metrics=["accuracy", "f1", "precision", "recall"]
)

print(f"准确率: {metrics['accuracy']:.2%}")
print(f"F1分数: {metrics['f1']:.3f}")
```

## 📚 相关资源

- [HuggingFace Transformers文档](https://huggingface.co/docs/transformers)
- [PyTorch文档](https://pytorch.org/docs/)
- [模型微调指南](../reference/models/finetuning-guide.md)
- [性能优化指南](../best-practices/performance-tuning.md)

## 🎯 下一步

1. **开始使用**：尝试基本提取任务
2. **性能调优**：根据您的硬件配置优化性能
3. **模型微调**：为您的特定任务微调模型
4. **集成测试**：将本地模型集成到完整工作流中

祝您使用愉快！🚀