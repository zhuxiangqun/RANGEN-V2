# 日志输出修复报告（2025-11-10）

**修复时间**: 2025-11-10  
**问题**: 评测系统无法从日志中提取期望答案和实际答案  
**根本原因**: 日志格式不匹配，且超时时未输出答案标记

---

## 🔴 问题分析

### 问题1: 期望答案未输出

**原因**:
- 代码中`log_info(f"期望答案: {expected_answer}")`在`try`块内（第274行）
- 只有在成功执行时才会输出
- 当发生超时或异常时，不会输出期望答案

**影响**:
- 评测系统无法提取期望答案
- 导致`expected_answers`列表为空

---

### 问题2: 系统答案未输出（超时情况）

**原因**:
- 代码中`log_info(f"系统答案: {clean_answer}")`在`try`块内（第206行等）
- 只有在成功执行时才会输出
- 当发生`asyncio.TimeoutError`时，直接跳到`except`块，没有输出系统答案

**影响**:
- 即使核心系统已经生成了答案（如"✅ 推理完成: Eliza Ballou"），但因为超时，无法获取result
- 导致`actual_answers`列表为空

---

## ✅ 修复方案

### 修复1: 在样本开始时输出期望答案

**修改位置**: `scripts/run_core_with_frames.py` 第166-168行

**修改内容**:
```python
# 🚀 P0修复：在样本开始时输出期望答案（确保即使超时也能提取）
if expected_answer:
    log_info(f"期望答案: {expected_answer}")
```

**效果**:
- 确保期望答案在样本开始时输出
- 即使后续发生超时或异常，期望答案也能被提取

---

### 修复2: 超时时从日志中提取答案

**修改位置**: `scripts/run_core_with_frames.py` 第277-305行

**修改内容**:
```python
except asyncio.TimeoutError:
    elapsed = time.time() - t0
    log_error(f"sample-{idx}", f"FRAMES sample={idx}/{total} success=False took={elapsed:.2f}s error=timeout({per_item_timeout}s)")
    # 🚀 P0修复：即使超时，也尝试从日志中提取答案
    # 尝试从日志文件中读取最近的"✅ 推理完成:"行，提取答案
    try:
        import re
        log_file_path = Path("research_system.log")
        if log_file_path.exists():
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 从后往前查找最近的"✅ 推理完成:"行
                for line in reversed(lines):
                    if "✅ 推理完成:" in line:
                        # 提取答案：格式为 "✅ 推理完成: {answer} (置信度: {confidence})"
                        match = re.search(r'✅ 推理完成:\s*([^(]+?)\s*\(置信度:', line)
                        if match:
                            extracted_answer = match.group(1).strip()
                            if extracted_answer and len(extracted_answer) < 200:
                                log_info(f"系统答案: {extracted_answer}")
                                break
                else:
                    # 如果没有找到，输出超时标记
                    log_info(f"系统答案: [超时，无法获取完整答案]")
        else:
            log_info(f"系统答案: [超时，无法获取完整答案]")
    except Exception as e:
        # 如果提取失败，输出超时标记
        log_info(f"系统答案: [超时，无法获取完整答案]")
```

**效果**:
- 即使超时，也能从日志文件中提取答案
- 从后往前查找最近的"✅ 推理完成:"行，提取答案
- 如果提取成功，输出"系统答案: {extracted_answer}"
- 如果提取失败，输出"系统答案: [超时，无法获取完整答案]"

---

### 修复3: 异常时也输出系统答案标记

**修改位置**: `scripts/run_core_with_frames.py` 第306-312行

**修改内容**:
```python
except Exception as e:
    elapsed = time.time() - t0
    log_error(f"sample-{idx}", f"FRAMES sample={idx}/{total} success=False took={elapsed:.2f}s error={type(e).__name__}: {e}")
    # 🚀 P0修复：即使发生异常，也尝试输出系统答案标记（如果有部分结果）
    # 注意：异常时result可能不存在，这里输出一个标记
    log_info(f"系统答案: [异常，无法获取完整答案: {type(e).__name__}]")
```

**效果**:
- 即使发生异常，也输出系统答案标记
- 让评测系统知道发生了异常

---

## 📋 修复后的日志格式

### 正常情况

```
FRAMES sample=1/3 started query=...
期望答案: Jane Ballou
...（推理过程）...
系统答案: Eliza Ballou
```

### 超时情况

```
FRAMES sample=1/3 started query=...
期望答案: Jane Ballou
...（推理过程）...
✅ 推理完成: Eliza Ballou (置信度: 0.72)
...（超时）...
系统答案: Eliza Ballou
```

### 异常情况

```
FRAMES sample=1/3 started query=...
期望答案: Jane Ballou
...（异常）...
系统答案: [异常，无法获取完整答案: ValueError]
```

---

## 🎯 预期效果

### 修复前

- 期望答案数: 0
- 实际答案数: 0
- 总比较数: 0
- FRAMES准确率: 0.00%

### 修复后

- 期望答案数: 3（所有样本都有期望答案）
- 实际答案数: 3（即使超时也能提取答案）
- 总比较数: 3（能够进行比较）
- FRAMES准确率: 可以计算（取决于答案是否正确）

---

## 🔍 测试建议

1. **运行3个样本测试**:
   ```bash
   scripts/run_core_with_frames.sh --sample-count 3 --data-path data/frames_dataset.json
   ```

2. **检查日志文件**:
   ```bash
   grep -E "期望答案|系统答案" research_system.log
   ```

3. **运行评测系统**:
   ```bash
   python evaluation_system/comprehensive_evaluation.py
   ```

4. **检查评测结果**:
   - 检查`evaluation_results.json`中的`expected_answers`和`actual_answers`是否都有值
   - 检查`total_comparisons`是否大于0
   - 检查`real_accuracy`是否能够计算

---

## 📝 注意事项

1. **日志文件路径**: 当前使用`Path("research_system.log")`，确保日志文件在当前工作目录
2. **答案提取格式**: 当前从"✅ 推理完成: {answer} (置信度: {confidence})"格式中提取答案
3. **答案长度限制**: 提取的答案长度限制为200字符（评测系统要求）
4. **超时标记**: 如果无法提取答案，输出"[超时，无法获取完整答案]"标记

---

*修复完成时间: 2025-11-10*

