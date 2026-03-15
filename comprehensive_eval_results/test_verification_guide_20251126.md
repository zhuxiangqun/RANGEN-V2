# 测试验证指南

**创建时间**: 2025-11-26  
**目的**: 验证核心系统优化改进效果

---

## 🎯 验证目标

1. **准确率**: 恢复到100%（或接近100%）
2. **性能**: 平均处理时间降低到70-100秒（vs 之前的339秒）
3. **模型使用**: 快速模型使用率提高到70-80%

---

## 📋 验证步骤

### 步骤1: 运行测试

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行10个样本的测试
python3 scripts/run_core_with_frames.py --sample-count 10 --data-path data/frames_dataset.json

# 或者使用shell脚本
./scripts/run_core_with_frames.sh --sample-count 10 --data-path data/frames_dataset.json
```

**预期时间**: 每个样本可能需要几分钟，总共可能需要10-30分钟

---

### 步骤2: 监控测试进度

**方法1: 使用监控脚本**
```bash
# 实时监控日志
tail -f research_system.log | grep -E '两阶段流水线|sample=|success='
```

**方法2: 使用Python脚本**
```bash
python3 << 'PYEOF'
import re
from pathlib import Path

log_file = Path('research_system.log')
if log_file.exists():
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统计已完成的样本
    samples_completed = re.findall(r'FRAMES sample=(\d+)/10.*?success=(True|False)', content)
    print(f"已完成的样本: {len(samples_completed)}/10")
    
    # 查找两阶段流水线日志
    two_stage_logs = re.findall(r'\[两阶段流水线\].*', content)
    print(f"两阶段流水线日志数量: {len(two_stage_logs)}")
    
    # 查找LLM复杂度判断
    llm_complexity_logs = re.findall(r'LLM判断查询复杂度:\s*(simple|medium|complex)', content, re.IGNORECASE)
    print(f"LLM复杂度判断数量: {len(llm_complexity_logs)}")
PYEOF
```

---

### 步骤3: 运行评测

**等待所有样本完成后，运行评测:**

```bash
# 运行评测
./scripts/run_evaluation.sh

# 或者直接运行评测脚本
python3 evaluation_system/comprehensive_evaluation.py
```

**评测结果位置**: 
- `comprehensive_eval_results/evaluation_report.md`
- `evaluation_results.json`

---

### 步骤4: 分析结果

**检查关键指标:**

1. **准确率**
   ```bash
   # 查看评测结果
   cat evaluation_results.json | python3 -m json.tool | grep -A 5 "accuracy"
   ```

2. **模型使用情况**
   ```bash
   # 查找快速模型使用情况
   grep -c "快速模型" research_system.log
   grep -c "推理模型" research_system.log
   ```

3. **两阶段流水线执行情况**
   ```bash
   # 查找两阶段流水线日志
   grep "\[两阶段流水线\]" research_system.log | wc -l
   ```

4. **处理时间**
   ```bash
   # 查看处理时间
   grep "took=" research_system.log | grep "sample=" | awk '{print $NF}' | sed 's/took=//' | sed 's/s//' | awk '{sum+=$1; count++} END {print "平均处理时间:", sum/count, "秒"}'
   ```

---

## 🔍 关键日志检查点

### 1. LLM复杂度判断

**应该看到:**
```
LLM判断查询复杂度: simple
LLM判断查询复杂度: medium
LLM判断查询复杂度: complex
```

### 2. 元判断层

**应该看到:**
```
✅ 元判断层：推理模型判断需要使用推理模型，但先尝试快速模型（两阶段流水线）
✅ 元判断层：推理模型判断可以使用快速模型，继续执行优化器学习
```

### 3. 两阶段流水线

**应该看到:**
```
🔍 [两阶段流水线] LLM判断为medium，但当前使用推理模型，先尝试快速模型...
🔍 [两阶段流水线] 第一阶段完成（快速模型），开始质量检查...
✅ [两阶段流水线] 快速模型答案质量检查通过
```

**或者:**
```
🔄 [两阶段流水线] 快速模型答案提取失败，fallback到推理模型
🔄 [两阶段流水线] 快速模型置信度低，fallback到推理模型
```

---

## 📊 预期结果

### 准确率

- **目标**: 100%（或接近100%）
- **之前**: 80%
- **改进**: +20%

### 性能

- **目标**: 平均处理时间 70-100秒
- **之前**: 339秒
- **改进**: 减少约70%

### 模型使用

- **快速模型使用率**: 70-80%
- **推理模型使用率**: 20-30%

---

## ⚠️ 注意事项

1. **测试时间**: 每个样本可能需要几分钟，总共可能需要10-30分钟
2. **日志级别**: 确保日志级别设置为INFO或WARNING，以便看到关键日志
3. **资源**: 确保有足够的API配额和网络连接
4. **缓存**: 如果使用缓存，可能需要清除缓存以获得准确的测试结果

---

## 🐛 故障排查

### 问题1: 没有看到两阶段流水线日志

**可能原因**:
- 日志级别设置过低
- 代码路径未执行到两阶段流水线部分
- 所有查询都被判断为complex，直接使用推理模型

**解决方法**:
- 检查日志级别设置
- 查看LLM复杂度判断日志
- 检查是否有simple或medium判断的查询

### 问题2: 准确率没有提高

**可能原因**:
- 两阶段流水线未正确执行
- 快速模型质量检查过于严格
- 推理模型提示词改进未生效

**解决方法**:
- 检查两阶段流水线日志
- 查看快速模型失败原因
- 验证推理模型提示词是否正确添加

### 问题3: 性能没有改善

**可能原因**:
- 快速模型使用率低
- 两阶段流水线未执行
- 所有查询都使用推理模型

**解决方法**:
- 检查快速模型使用情况
- 查看两阶段流水线执行情况
- 分析模型选择逻辑

---

## 📝 验证报告模板

完成验证后，请填写以下信息:

```markdown
## 验证结果

### 测试时间
- 开始时间: 
- 结束时间: 
- 总耗时: 

### 准确率
- 之前: 80%
- 现在: ___%
- 改进: ___%

### 性能
- 之前平均处理时间: 339秒
- 现在平均处理时间: ___秒
- 改进: ___%

### 模型使用
- 快速模型使用率: ___%
- 推理模型使用率: ___%

### 两阶段流水线
- 执行次数: ___
- 快速模型成功次数: ___
- Fallback到推理模型次数: ___

### 问题
- [ ] 没有看到两阶段流水线日志
- [ ] 准确率没有提高
- [ ] 性能没有改善
- [ ] 其他问题: ___
```

---

**报告生成时间**: 2025-11-26  
**状态**: ✅ 验证指南已创建

