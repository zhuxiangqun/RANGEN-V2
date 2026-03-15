# Bug修复验证计划 - 2025-11-23

## 🎯 验证目标

验证L2缓存禁用修复是否解决了"Jane Ballou"问题

---

## 📋 验证步骤

### 步骤1: 小规模测试（10个样本）

**目的**: 快速验证修复是否生效

**执行命令**:
```bash
python scripts/run_core_with_frames.py --sample-count 10
```

**验证指标**:
1. ✅ 是否还有多个样本返回"Jane Ballou"？
2. ✅ 准确率是否提升？
3. ✅ 错误样本是否减少？

**预期结果**:
- 只有样本1返回"Jane Ballou"（如果样本1的期望答案确实是"Jane Ballou"）
- 准确率应该显著提升（从68.32%提升到80%以上）

---

### 步骤2: 中等规模测试（50个样本）

**目的**: 进一步验证修复的稳定性

**执行命令**:
```bash
python scripts/run_core_with_frames.py --sample-count 50
```

**验证指标**:
1. ✅ 是否还有多个样本返回"Jane Ballou"？
2. ✅ 准确率是否稳定在较高水平？
3. ✅ 错误样本分布是否正常？

**预期结果**:
- 只有样本1返回"Jane Ballou"（如果样本1的期望答案确实是"Jane Ballou"）
- 准确率应该稳定在85%以上

---

### 步骤3: 完整评测（101个样本）

**目的**: 最终验证修复效果

**执行命令**:
```bash
python scripts/run_core_with_frames.py --sample-count 101
```

**验证指标**:
1. ✅ 是否还有多个样本返回"Jane Ballou"？
2. ✅ 准确率是否恢复到90%以上？
3. ✅ 错误样本是否减少到10个以下？

**预期结果**:
- 只有样本1返回"Jane Ballou"（如果样本1的期望答案确实是"Jane Ballou"）
- 准确率应该恢复到90%以上（接近修复前的93.07%）
- 错误样本应该减少到10个以下

---

## 📊 对比指标

### 修复前（101个样本）
- 准确率: 68.32% (69/101)
- 错误样本: 32个
- 返回"Jane Ballou"的样本: 36个

### 修复后（预期）
- 准确率: ≥90% (≥91/101)
- 错误样本: ≤10个
- 返回"Jane Ballou"的样本: 1个（样本1，如果期望答案确实是"Jane Ballou"）

---

## 🔍 验证方法

### 1. 检查返回"Jane Ballou"的样本数

```bash
python3 -c "
import json
data = json.load(open('evaluation_results.json'))
actual = data['frames_analysis']['accuracy']['actual_answers']
jane_count = sum(1 for a in actual if 'Jane Ballou' in a)
print(f'返回\"Jane Ballou\"的样本数: {jane_count}/{len(actual)}')
"
```

### 2. 检查准确率

```bash
grep "real_accuracy" evaluation_results.json
```

### 3. 检查错误样本

```bash
python3 -c "
import json
data = json.load(open('evaluation_results.json'))
expected = data['frames_analysis']['accuracy']['expected_answers']
actual = data['frames_analysis']['accuracy']['actual_answers']
errors = [(i+1, e, a) for i, (e, a) in enumerate(zip(expected, actual)) if e != a]
print(f'错误样本数: {len(errors)}')
"
```

---

## ✅ 验证完成标准

1. ✅ 返回"Jane Ballou"的样本数 ≤ 1（只有样本1，如果期望答案确实是"Jane Ballou"）
2. ✅ 准确率 ≥ 90%
3. ✅ 错误样本数 ≤ 10个
4. ✅ 没有其他明显的系统性错误

---

**创建时间**: 2025-11-23  
**状态**: 🔄 进行中

