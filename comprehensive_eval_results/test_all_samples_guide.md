# 测试所有样本数据使用指南

**更新时间**: 2025-11-18  
**目标**: 测试FRAMES数据集的所有样本

---

## 📋 可用的测试脚本

### 1. `scripts/run_core_with_frames.sh` - 核心系统测试脚本（推荐）✅

**功能**: 运行核心系统处理FRAMES数据集样本，生成日志供评测系统使用

**用法**:
```bash
# 测试所有样本（不指定sample-count会使用默认值50）
./scripts/run_core_with_frames.sh

# 测试指定数量的样本
./scripts/run_core_with_frames.sh --sample-count 100

# 测试所有样本（需要先知道总样本数）
./scripts/run_core_with_frames.sh --sample-count 824

# 指定数据集路径
./scripts/run_core_with_frames.sh --sample-count 824 --data-path data/frames_dataset.json
```

**参数说明**:
- `--sample-count N`: 指定要测试的样本数量（可选，默认50）
- `--data-path FILE`: 指定数据集文件路径（可选，默认使用环境变量或默认路径）

**特点**:
- ✅ 自动激活虚拟环境
- ✅ 生成日志文件供评测系统使用
- ✅ 支持指定样本数量

---

### 2. `scripts/run_evaluation.sh` - 评测脚本

**功能**: 基于日志文件生成评测报告

**用法**:
```bash
# 先运行核心系统测试（生成日志）
./scripts/run_core_with_frames.sh --sample-count 824

# 然后运行评测（分析日志）
./scripts/run_evaluation.sh
```

**特点**:
- ✅ 自动分析日志文件
- ✅ 生成评测报告
- ✅ 报告位置: `comprehensive_eval_results/evaluation_report.md`

---

### 3. `run_chunked_evaluation.sh` - 分块评测脚本

**功能**: 分块处理样本，避免内存问题

**用法**:
```bash
# 分块测试所有样本（每次10个样本，块间休息5秒）
./run_chunked_evaluation.sh
```

**特点**:
- ✅ 自动分块处理（每块10个样本）
- ✅ 块间休息，避免系统过载
- ✅ 自动合并结果

---

## 🎯 测试所有样本的完整流程

### 方法1: 使用核心系统测试脚本（推荐）✅

**步骤1: 检查数据集大小**
```bash
# 查看数据集总样本数
python3 -c "
import json
with open('data/frames_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    if isinstance(data, list):
        print(f'总样本数: {len(data)}')
    elif isinstance(data, dict) and 'samples' in data:
        print(f'总样本数: {len(data[\"samples\"])}')
"
```

**步骤2: 运行测试（测试所有样本）**
```bash
# 假设总样本数是824
./scripts/run_core_with_frames.sh --sample-count 824
```

**步骤3: 生成评测报告**
```bash
./scripts/run_evaluation.sh
```

**步骤4: 查看结果**
```bash
# 查看评测报告
cat comprehensive_eval_results/evaluation_report.md

# 或使用编辑器打开
open comprehensive_eval_results/evaluation_report.md
```

---

### 方法2: 使用分块评测脚本（适合大量样本）✅

**步骤1: 运行分块评测**
```bash
./run_chunked_evaluation.sh
```

**步骤2: 查看结果**
```bash
# 查看合并后的结果
cat results/merged_evaluation_results.json
```

**特点**:
- ✅ 自动分块处理
- ✅ 避免内存问题
- ✅ 自动合并结果

---

## 📊 脚本参数详解

### `scripts/run_core_with_frames.sh`

**完整用法**:
```bash
./scripts/run_core_with_frames.sh [--sample-count N] [--data-path FILE]
```

**参数**:
- `--sample-count N`: 要测试的样本数量
  - 如果不指定，默认使用环境变量 `MAX_EVALUATION_ITEMS` 或 50
  - 示例: `--sample-count 824` 测试所有样本
  - 示例: `--sample-count 100` 测试前100个样本

- `--data-path FILE`: 数据集文件路径
  - 如果不指定，默认使用环境变量 `FRAMES_DATASET_PATH` 或 `frames_dataset.json`
  - 示例: `--data-path data/frames_dataset.json`

**示例**:
```bash
# 测试所有样本（假设824个）
./scripts/run_core_with_frames.sh --sample-count 824

# 测试前100个样本
./scripts/run_core_with_frames.sh --sample-count 100

# 测试所有样本，指定数据集路径
./scripts/run_core_with_frames.sh --sample-count 824 --data-path data/frames_dataset.json
```

---

## ⚠️ 注意事项

### 1. 测试时间

**估算**:
- 平均每个样本处理时间: 85.03秒（根据最新评测报告）
- 824个样本总时间: 85.03 × 824 ≈ 70,065秒 ≈ **19.5小时**

**建议**:
- ⚠️ 测试所有样本需要很长时间（约20小时）
- ✅ 可以先测试部分样本（例如100个）验证系统正常
- ✅ 如果时间允许，再测试所有样本

---

### 2. 系统资源

**要求**:
- 内存: 建议至少4GB可用内存
- 磁盘: 日志文件可能很大（每个样本约4KB，824个样本约3.3MB）
- 网络: 需要稳定的网络连接（LLM API调用）

**建议**:
- ✅ 确保有足够的磁盘空间
- ✅ 确保网络连接稳定
- ✅ 可以考虑使用分块评测脚本（`run_chunked_evaluation.sh`）

---

### 3. 日志文件

**位置**: `research_system.log`

**大小**: 
- 每个样本约4KB日志
- 824个样本约3.3MB日志

**建议**:
- ✅ 测试前备份现有日志（如果需要）
- ✅ 测试后可以清理旧日志（如果需要）

---

## 🚀 快速开始

### 测试所有样本（最简单的方式）

```bash
# 1. 确保在项目根目录
cd /Users/syu/workdata/person/zy/RANGEN-main\(syu-python\)

# 2. 激活虚拟环境（如果还没有激活）
source .venv/bin/activate

# 3. 检查数据集大小
python3 -c "
import json
with open('data/frames_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    total = len(data) if isinstance(data, list) else len(data.get('samples', []))
    print(f'总样本数: {total}')
"

# 4. 运行测试（假设总样本数是824，替换为实际数量）
./scripts/run_core_with_frames.sh --sample-count 824

# 5. 等待测试完成（可能需要20小时）

# 6. 生成评测报告
./scripts/run_evaluation.sh

# 7. 查看结果
cat comprehensive_eval_results/evaluation_report.md
```

---

### 测试部分样本（快速验证）

```bash
# 1. 测试前50个样本（快速验证）
./scripts/run_core_with_frames.sh --sample-count 50

# 2. 生成评测报告
./scripts/run_evaluation.sh

# 3. 查看结果
cat comprehensive_eval_results/evaluation_report.md
```

---

## 📝 完整示例

### 示例1: 测试所有样本并生成报告

```bash
#!/bin/bash
# 测试所有样本的完整流程

# 1. 进入项目目录
cd /Users/syu/workdata/person/zy/RANGEN-main\(syu-python\)

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 获取总样本数
TOTAL_SAMPLES=$(python3 -c "
import json
with open('data/frames_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    if isinstance(data, list):
        print(len(data))
    elif isinstance(data, dict) and 'samples' in data:
        print(len(data['samples']))
    else:
        print(824)
")

echo "📊 数据集总样本数: $TOTAL_SAMPLES"

# 4. 运行测试
echo "🚀 开始测试所有样本..."
./scripts/run_core_with_frames.sh --sample-count $TOTAL_SAMPLES

# 5. 生成评测报告
echo "📊 生成评测报告..."
./scripts/run_evaluation.sh

# 6. 显示结果
echo "✅ 测试完成！"
echo "📄 评测报告位置: comprehensive_eval_results/evaluation_report.md"
```

---

### 示例2: 使用分块评测

```bash
#!/bin/bash
# 使用分块评测测试所有样本

# 1. 进入项目目录
cd /Users/syu/workdata/person/zy/RANGEN-main\(syu-python\)

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 运行分块评测
./run_chunked_evaluation.sh

# 4. 查看结果
echo "✅ 分块评测完成！"
echo "📄 结果文件: results/merged_evaluation_results.json"
```

---

## 🔍 常见问题

### Q1: 如何知道数据集总样本数？

**方法1: 使用Python脚本**
```bash
python3 -c "
import json
with open('data/frames_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    if isinstance(data, list):
        print(len(data))
    elif isinstance(data, dict) and 'samples' in data:
        print(len(data['samples']))
"
```

**方法2: 查看脚本输出**
```bash
# 运行脚本时会显示加载的样本数
./scripts/run_core_with_frames.sh --sample-count 1000
# 输出会显示: "成功加载 XXX 个样本"
```

---

### Q2: 测试过程中可以中断吗？

**答案**: 可以，但需要注意：

1. **日志会保留**: 已处理的样本日志会保留在 `research_system.log` 中
2. **可以断点续传**: 重新运行脚本会继续处理未完成的样本（如果脚本支持）
3. **建议**: 使用分块评测脚本（`run_chunked_evaluation.sh`），支持断点续传

---

### Q3: 如何查看测试进度？

**方法1: 查看日志文件**
```bash
# 实时查看日志
tail -f research_system.log

# 查看已处理的样本数
grep -c "FRAMES sample=" research_system.log
```

**方法2: 查看脚本输出**
```bash
# 脚本会实时输出进度
# 例如: "FRAMES sample=50/824 started query=..."
```

---

### Q4: 测试需要多长时间？

**估算**:
- 平均每个样本: 85.03秒
- 824个样本: 约19.5小时

**优化建议**:
- 可以先测试部分样本验证系统正常
- 使用分块评测脚本，可以随时中断和恢复

---

## 📝 总结

### 推荐流程

1. **快速验证**（5-10分钟）:
   ```bash
   ./scripts/run_core_with_frames.sh --sample-count 10
   ./scripts/run_evaluation.sh
   ```

2. **中等规模测试**（1-2小时）:
   ```bash
   ./scripts/run_core_with_frames.sh --sample-count 50
   ./scripts/run_evaluation.sh
   ```

3. **完整测试**（约20小时）:
   ```bash
   # 获取总样本数
   TOTAL=$(python3 -c "import json; data=json.load(open('data/frames_dataset.json')); print(len(data) if isinstance(data,list) else len(data.get('samples',[])))")
   
   # 运行测试
   ./scripts/run_core_with_frames.sh --sample-count $TOTAL
   
   # 生成报告
   ./scripts/run_evaluation.sh
   ```

---

*更新时间: 2025-11-18*

