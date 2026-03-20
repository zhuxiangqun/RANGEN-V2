# google/frames-benchmark 数据集构建指南

## 问题分析

### 原始问题
在沙箱环境中构建 google/frames-benchmark 向量知识库时遇到以下问题：

1. **torch 库初始化失败**: `AttributeError: 'function' object has no attribute 'endswith'`
2. **datasets 库导入失败**: 连锁反应导致无法加载 Hugging Face 数据集
3. **网络访问限制**: 沙箱环境阻止从 Hugging Face 下载数据集
4. **keras 补丁干扰**: keras_compat_patch.py 干扰了 torch 的内部机制

### 根本原因
- **沙箱权限限制**: torch 在初始化时需要访问系统文件，但被沙箱阻止
- **keras 补丁副作用**: 补丁脚本修改了 sys.modules，影响了 torch 的 inspect 模块
- **环境隔离**: 沙箱环境无法进行网络访问和某些系统调用

### 解决方案状态
✅ **已解决**: 通过移除干扰性的 keras 补丁，torch 和 datasets 库现在可以在无沙箱限制下正常工作

## 错误现象

```bash
❌ 错误：无法导入 datasets 库: [Errno 1] Operation not permitted
```

## 解决方案

### 方案1：完整生产环境构建（推荐）

1. **准备环境**
   ```bash
   # 创建独立的 Python 环境
   python3 -m venv ~/frames_env
   source ~/frames_env/bin/activate

   # 安装必要依赖
   pip install datasets torch sentence-transformers numpy
   ```

2. **完整构建**
   ```bash
   # 运行完整构建脚本（自动下载数据集并构建向量库）
   python build_frames_kb_full.py --batch-size 10

   # 或者分步执行：
   # 下载数据集
   python build_frames_kb_external.py
   # 构建向量库
   python build_kb_sandbox_friendly.py --input-file frames_dataset.json
   ```

3. **复制到项目**
   ```bash
   # 将构建的文件复制到项目目录
   cp -r data/knowledge_management /path/to/your/project/data/
   ```

### 方案2：沙箱环境兼容版本

如果必须在沙箱环境中工作：

1. **外部下载数据集**
   ```bash
   # 在非沙箱环境中下载
   python3 build_frames_kb_external.py
   ```

2. **沙箱环境构建**
   ```bash
   # 复制数据集到项目
   cp frames_dataset.json /path/to/project/

   # 在沙箱环境中构建（使用简化嵌入）
   python3 build_kb_sandbox_friendly.py --input-file frames_dataset.json
   ```

### 方案3：直接使用项目构建脚本

现在项目构建脚本已经修复，可以正确报告错误：

```bash
# 这会正确报告权限问题，而不是悄无声息失败
./build_vector_knowledge_base.sh --dataset-path google/frames-benchmark --force-download
```

### 方案2：使用替代数据集

如果无法访问外部环境，可以使用项目中已有的知识数据：

```bash
# 使用现有的 ML 知识数据
./build_vector_knowledge_base.sh --input-file data/knowledge_base_ml.json --batch-size 10 --resume
```

## 技术细节

### 数据集信息

- **数据集**: google/frames-benchmark
- **描述**: 包含复杂推理问题的基准数据集
- **大小**: 数千条记录，每条包含 Prompt、Answer 和相关 Wikipedia 链接
- **用途**: 用于训练和测试 RAG 系统的推理能力

### 依赖要求

- `datasets >= 4.3.0`
- `torch >= 2.0.0`
- `sentence-transformers >= 2.0.0`

### 构建流程

1. **数据下载**: 从 Hugging Face 下载原始数据集
2. **数据预处理**: 合并所有分割，转换为统一格式
3. **向量嵌入**: 使用 SentenceTransformer 生成文本向量
4. **索引构建**: 创建 FAISS 向量索引
5. **知识图谱**: 可选构建相关实体关系图

## 故障排除

### 常见问题

1. **PermissionError**: 确认在非沙箱环境中运行
2. **ImportError**: 检查所有依赖是否正确安装
3. **网络错误**: 检查网络连接和 Hugging Face 访问权限
4. **内存不足**: 对于大型数据集，考虑分批处理

### 验证步骤

### 1. 验证数据集完整性
```bash
python3 -c "
import json
with open('data/knowledge_management/frames_dataset.json', 'r') as f:
    data = json.load(f)
print(f'✅ 数据集大小: {len(data)} 条')
print(f'📋 示例字段: {list(data[0].keys())[:5]}...')

# 检查数据质量
prompts = [item.get('Prompt', '') for item in data[:5]]
answers = [item.get('Answer', '') for item in data[:5]]
print(f'🔍 示例问题: {prompts[0][:50]}...')
print(f'💡 示例答案: {answers[0][:50]}...')
"
```

### 2. 验证向量嵌入
```bash
python3 -c "
import numpy as np
embeddings = np.load('data/knowledge_management/frames_embeddings.npy')
print(f'✅ 向量嵌入形状: {embeddings.shape}')
print(f'📊 向量维度: {embeddings.shape[1]}')
print(f'🔢 数据类型: {embeddings.dtype}')
"
```

### 3. 验证元数据
```bash
python3 -c "
import json
with open('data/knowledge_management/metadata.json', 'r') as f:
    metadata = json.load(f)
print('📋 知识库元数据:')
for key, value in metadata.items():
    print(f'  {key}: {value}')
"
```

### 4. 功能测试
```bash
# 测试知识检索功能
python3 scripts/test_knowledge_retrieval.py
```

## 性能优化

- **批处理大小**: 根据内存情况调整 `--batch-size` 参数
- **断点续传**: 使用 `--resume` 避免重复处理
- **并行处理**: 考虑使用多进程加速向量生成

## 文件说明

- `build_frames_kb_external.py`: 外部数据集下载脚本
- `build_vector_knowledge_base.sh`: 主构建脚本
- `keras_compat_patch.py`: Keras 兼容性补丁
- `data/frames_dataset.json`: 下载的原始数据集
- `data/knowledge_management/vector_index/`: 向量索引文件
