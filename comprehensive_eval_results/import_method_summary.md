# 导入方法总结

**更新时间**: 2025-11-03

---

## ✅ 导入方式

### 方式1: 使用Shell脚本（最简单）

```bash
./scripts/import_dataset.sh https://huggingface.co/datasets/google/frames-benchmark
```

**行为**:
- ✅ 自动检测FRAMES数据集
- ✅ 如果数据集不存在，自动下载
- ✅ 调用修改后的导入脚本（默认抓取完整内容）
- ⚠️ 默认断点续传（使用之前的进度）

**如果要从头开始**:
```bash
IMPORT_NO_RESUME=true ./scripts/import_dataset.sh https://huggingface.co/datasets/google/frames-benchmark
```

---

### 方式2: 直接使用Python脚本（推荐，可控）

```bash
# 从头开始，抓取完整内容
python knowledge_management_system/scripts/import_wikipedia_from_frames.py \
    data/frames_dataset.json \
    --no-resume \
    --batch-size 10
```

**优势**:
- ✅ 完全控制参数
- ✅ 明确从头开始（`--no-resume`）
- ✅ 默认抓取完整内容（已修改）

---

## 📊 默认行为（已修改）

✅ **默认抓取完整内容** (`include_full_text=True`)
- 不再只抓取摘要
- 包含完整的排名列表、精确数据

✅ **Shell脚本支持环境变量**
- `IMPORT_NO_RESUME=true` 可以从头开始

---

## 🎯 推荐命令（清除后重新导入）

```bash
# 方式1: 使用环境变量（Shell脚本）
IMPORT_NO_RESUME=true ./scripts/import_dataset.sh https://huggingface.co/datasets/google/frames-benchmark

# 方式2: 直接运行Python（推荐）
python knowledge_management_system/scripts/import_wikipedia_from_frames.py \
    data/frames_dataset.json \
    --no-resume \
    --batch-size 10
```

---

**两个方式都可以使用，方式2更直接！** ✅

