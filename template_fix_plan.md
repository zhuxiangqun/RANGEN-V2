# 模板修复计划

生成时间: 2025-12-04

## 修复策略

由于模板文件很大（389行），采用**渐进式修复**策略：

### 第一阶段：修复核心模板（立即执行）

1. **reasoning_with_evidence** - 最重要的模板
   - 统一 final_answer 格式
   - 统一置信度格式
   - 添加 metadata 字段说明

2. **reasoning_without_evidence** - 重要模板
   - 统一 final_answer 格式
   - 统一置信度格式
   - 统一参数名称

3. **reasoning_steps_generation** - 已更新，需要验证格式一致性

### 第二阶段：修复其他模板（后续）

4. 统一所有模板的参数名称
5. 添加证据质量评估模板
6. 简化步骤类型系统

## 关键修复点

### 1. Final Answer 格式统一

**当前问题**：
- 有些模板使用 `Final Answer:`
- 有些模板使用 `FINAL ANSWER:`
- 有些模板没有明确格式要求

**修复方案**：
- 统一使用 `---\nFINAL ANSWER: [答案]\n---`
- 在所有模板中明确要求此格式

### 2. 置信度格式统一

**当前问题**：
- `reasoning_with_evidence`: 使用 `high/medium/low` + 百分比
- `reasoning_without_evidence`: 使用 `high/medium/low`
- `answer_validation`: 使用 `0.0-1.0` 数值

**修复方案**：
- 统一为 `{"score": 0.85, "level": "high"}` 格式
- 在模板中明确要求此格式

### 3. 参数名称统一

**当前问题**：
- `general_query` 使用 `{question}`
- 其他模板使用 `{query}`

**修复方案**：
- 统一使用 `{query}`
- 更新所有模板

---

**计划状态**: 准备执行第一阶段修复

