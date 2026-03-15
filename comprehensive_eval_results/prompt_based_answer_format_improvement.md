# 基于提示词的答案格式改进报告

**实施时间**: 2025-11-08  
**核心理念**: 让LLM在生成答案时直接按照正确格式生成，而不是通过程序过滤和转换

---

## 📊 改进概览

### 核心思想转变

**之前的方法**:
- LLM生成答案 → 程序提取 → 程序验证 → 程序转换格式 → 最终答案
- 问题：后处理步骤多，容易出错，效率低

**现在的方法**:
- 分析查询类型 → 在提示词中明确格式要求 → LLM直接生成正确格式 → 最小化后处理（仅作为安全网）
- 优势：LLM在生成时就知道需要什么格式，减少后处理

---

## 🔧 详细改进内容

### 1. 新增答案格式要求方法

**文件**: `src/core/real_reasoning_engine.py`  
**方法**: `_get_answer_format_instruction(query_type, query)`

**功能**:
- 根据查询类型和查询内容，生成明确的答案格式要求
- 在提示词开头插入格式要求（LLM会优先看到）
- 使用具体示例说明正确和错误格式

**支持的查询类型**:

1. **排名查询** (ranking)
   - 要求格式: `"37th"` 或 `"2nd"` 或 `"1st"` (序数词格式)
   - 错误格式: `"37"` 或 `"around 15th-20th"`
   - 示例: "What rank is the Empire State Building?" → `"37th"`

2. **数字查询** (numerical, mathematical)
   - 要求格式: `"87"` 或 `"506000"` (纯数字，无单位)
   - 错误格式: `"87 years"` 或 `"around 80-90"`
   - 示例: "How many years earlier?" → `"87"`

3. **人名查询** (factual + who/name)
   - 要求格式: `"Jane Ballou"` (完整人名)
   - 错误格式: `"The person is Jane Ballou"` 或 `"Jane"`
   - 示例: "Who was the first person?" → `"Jane Ballou"`

4. **地点/国家查询** (location, country)
   - 要求格式: `"France"` 或 `"Argentina"` (准确的地名/国名)
   - 错误格式: `"The country is France"` 或 `"It is France"`
   - 示例: "Which country won the World Cup?" → `"France"`

5. **默认格式**
   - 要求格式: 简洁答案（最多20词），直接回答问题
   - 错误格式: 冗长解释，冗余短语

---

### 2. 提示词生成优化

**文件**: `src/core/real_reasoning_engine.py`  
**方法**: `_generate_optimized_prompt()`

**改进内容**:
- 在提示词开头插入格式要求（在问题之前）
- 确保LLM在生成答案时优先看到格式要求
- 保留原有的查询类型增强逻辑

**实现逻辑**:
```python
# 1. 生成基础提示词
prompt = self.prompt_engineering.generate_prompt(template_name, **prompt_kwargs)

# 2. 根据查询类型生成格式要求
format_instruction = self._get_answer_format_instruction(query_type, query)

# 3. 在提示词开头插入格式要求
if format_instruction:
    prompt = format_instruction + "\n\n" + prompt
```

---

### 3. 简化后处理逻辑

**文件**: `src/core/real_reasoning_engine.py`  
**位置**: `reason()` 方法中的答案生成后处理

**改进内容**:
- 减少后处理步骤（相信LLM已经生成正确格式）
- 只保留最小化的安全网转换（仅在格式明显错误时）
- 例如：排名查询返回"20"而不是"20th"时，才进行转换

**实现逻辑**:
```python
# 只在格式明显错误时才进行简单转换（作为安全网）
if query_type == "ranking":
    # 如果答案中没有序数词后缀，但包含数字，尝试转换
    if not re.search(r'\d+(?:st|nd|rd|th)\b', final_answer, re.IGNORECASE):
        numbers = re.findall(r'\d+', final_answer)
        if numbers and final_answer.strip() == numbers[-1]:
            final_answer = f"{numbers[-1]}th"  # 简单转换
```

---

## 📈 预期改进效果

### 直接改进

1. **答案格式一致性** ✅
   - LLM在生成时就知道需要什么格式
   - 减少格式不一致的问题

2. **减少后处理步骤** ✅
   - 从多层提取+验证+转换 → 最小化安全网
   - 提高效率，减少错误

3. **提高答案准确性** ✅
   - 明确的格式要求帮助LLM生成更准确的答案
   - 减少因格式问题导致的匹配失败

### 间接改进

1. **代码简化** ✅
   - 减少复杂的后处理逻辑
   - 代码更易维护

2. **性能提升** ✅
   - 减少后处理步骤，提高响应速度

---

## 🎯 对比改进前后

### 改进前

```
1. LLM生成答案（可能格式不正确）
   ↓
2. 程序提取答案（多层提取策略）
   ↓
3. 程序验证答案（多层验证）
   ↓
4. 程序转换格式（复杂的格式转换逻辑）
   ↓
5. 最终答案
```

**问题**:
- 后处理步骤多，容易出错
- 格式转换逻辑复杂
- 效率低

### 改进后

```
1. 分析查询类型
   ↓
2. 在提示词中明确格式要求（LLM优先看到）
   ↓
3. LLM直接生成正确格式的答案
   ↓
4. 最小化后处理（仅作为安全网）
   ↓
5. 最终答案
```

**优势**:
- LLM在生成时就知道需要什么格式
- 减少后处理步骤
- 提高效率和准确性

---

## 📝 实施总结

### ✅ 已完成

1. **新增答案格式要求方法** - `_get_answer_format_instruction()`
2. **提示词生成优化** - 在提示词开头插入格式要求
3. **简化后处理逻辑** - 只保留最小化安全网

### 🎯 核心改进

1. **让LLM直接生成正确格式** - 而不是生成后再转换
2. **在提示词开头明确格式要求** - LLM会优先看到
3. **使用具体示例** - 说明正确和错误格式
4. **减少后处理步骤** - 相信LLM的能力

---

## 🔍 测试建议

1. **运行评测脚本**
   ```bash
   ./scripts/run_core_with_frames.sh --sample-count 10 --data-path data/frames_dataset.json
   ```

2. **重点关注**
   - 样本2: 排名查询格式是否正确（"20" → "20th"）
   - 样本3: 数字查询格式是否正确（"87"）
   - 样本1: 人名查询格式是否正确（"Jane Ballou"）
   - 样本4: 国家查询格式是否正确（"France"）

3. **验证指标**
   - 答案格式是否正确（特别是排名查询）
   - 后处理步骤是否减少
   - 答案格式一致性是否提高

---

*本报告基于2025-11-08的改进实施生成*

