# 重新导入知识库的正确方式

**更新时间**: 2025-11-03  
**状态**: ✅ 脚本已修改，默认抓取完整内容

---

## ✅ 正确的导入方式

### 方式1: 使用Shell脚本（推荐，自动处理）

```bash
# 直接运行，会自动：
# 1. 检测FRAMES数据集
# 2. 下载数据集（如果不存在）
# 3. 调用修改后的导入脚本（默认抓取完整内容）
./scripts/import_dataset.sh https://huggingface.co/datasets/google/frames-benchmark
```

**注意**: 
- Shell脚本会调用 `import_wikipedia_from_frames.py`
- **默认会断点续传**（使用之前的进度）
- **修改后的脚本默认抓取完整内容**（`include_full_text=True`）

**如果要从头开始**（不使用之前的进度）:
- 需要手动修改Shell脚本，添加 `--no-resume` 参数
- 或直接使用方式2

---

### 方式2: 直接使用Python脚本（推荐，可控制参数）

```bash
# 确保数据集文件存在
# 如果不存在，先运行：
# python knowledge_management_system/scripts/import_dataset.py https://huggingface.co/datasets/google/frames-benchmark --no-fetch-wikipedia

# 然后运行导入脚本（从头开始，抓取完整内容）
python knowledge_management_system/scripts/import_wikipedia_from_frames.py \
    data/frames_dataset.json \
    --no-resume \
    --batch-size 10
```

**参数说明**:
- `--no-resume`: **从头开始**，不使用之前的进度
- `--batch-size 10`: 每批处理10个数据项
- **默认行为**: 抓取完整内容（`include_full_text=True`，已修改）

---

## 🔍 Shell脚本的自动处理逻辑

`scripts/import_dataset.sh` 的处理流程：

1. **检测FRAMES数据集**:
   ```bash
   if [[ "$DATASET_SOURCE" == *"frames-benchmark"* ]]; then
   ```

2. **检查本地数据集文件**:
   ```bash
   if [ -f "$PROJECT_ROOT/data/frames_dataset.json" ]; then
       DATASET_FILE="$PROJECT_ROOT/data/frames_dataset.json"
   else
       # 下载数据集
       python3 import_dataset.py "$DATASET_SOURCE" --no-fetch-wikipedia
   fi
   ```

3. **调用Wikipedia导入脚本**:
   ```bash
   python3 import_wikipedia_from_frames.py "$DATASET_FILE" --batch-size 10
   ```

**问题**: Shell脚本调用时**没有传递 `--no-resume`**，所以会使用之前的进度（断点续传）

---

## 💡 推荐方案

### 方案1: 直接运行Shell脚本（如果已有进度，继续导入）

```bash
./scripts/import_dataset.sh https://huggingface.co/datasets/google/frames-benchmark
```

**适用场景**: 
- 已有部分导入进度
- 想继续从上次中断的地方导入

---

### 方案2: 修改Shell脚本或直接运行Python（从头开始）

**选项A: 修改Shell脚本**

在 `scripts/import_dataset.sh` Line 125 添加 `--no-resume`:
```bash
# 修改前
python3 "$PROJECT_ROOT/knowledge_management_system/scripts/import_wikipedia_from_frames.py" "$DATASET_FILE" --batch-size 10

# 修改后
python3 "$PROJECT_ROOT/knowledge_management_system/scripts/import_wikipedia_from_frames.py" "$DATASET_FILE" --batch-size 10 --no-resume
```

**选项B: 直接运行Python脚本（推荐）**

```bash
python knowledge_management_system/scripts/import_wikipedia_from_frames.py \
    data/frames_dataset.json \
    --no-resume \
    --batch-size 10
```

**适用场景**:
- 想从头开始重新导入
- 需要更精细的控制参数

---

## 📊 当前配置确认

### 已修改的默认行为

✅ **`include_full_text=True`** - 默认抓取完整内容（而不是摘要）
- `knowledge_management_system/scripts/import_wikipedia_from_frames.py` Line 141
- `knowledge_management_system/utils/wikipedia_fetcher.py` Line 324

### Shell脚本的行为

⚠️ **默认断点续传**（`resume=True`）
- 如果要从头开始，需要添加 `--no-resume`

---

## 🎯 建议

由于我们已经清除了知识库，**建议从头开始重新导入**：

### 推荐命令：

```bash
# 确保数据集存在
if [ ! -f "data/frames_dataset.json" ]; then
    python knowledge_management_system/scripts/import_dataset.py \
        https://huggingface.co/datasets/google/frames-benchmark \
        --no-fetch-wikipedia
fi

# 从头开始导入（抓取完整内容）
python knowledge_management_system/scripts/import_wikipedia_from_frames.py \
    data/frames_dataset.json \
    --no-resume \
    --batch-size 10
```

或者，如果已经有数据集文件：

```bash
python knowledge_management_system/scripts/import_wikipedia_from_frames.py \
    data/frames_dataset.json \
    --no-resume \
    --batch-size 10
```

---

## ✅ 总结

1. ✅ **可以继续使用** `scripts/import_dataset.sh`
2. ⚠️ **但默认会断点续传**（如果要从头开始，需要添加 `--no-resume`）
3. ✅ **修改后的脚本默认抓取完整内容**（`include_full_text=True`）
4. 💡 **推荐**: 直接运行Python脚本并添加 `--no-resume`，从头开始导入

