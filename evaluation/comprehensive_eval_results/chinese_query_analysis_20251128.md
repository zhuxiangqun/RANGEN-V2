# 中文查询问题分析报告（2025-11-28）

**分析时间**: 2025-11-28  
**问题**: 日志中出现中文查询内容，而FRAMES数据集应该是英文的

---

## 🔍 问题现象

### 日志中的中文查询

从日志中发现：
```
查询: 美国第15任第一夫人的母亲的名字和第二位遇刺总统的母亲婚前姓氏
```

**问题**：
- FRAMES数据集中的查询应该是英文的
- 但日志中显示的是中文查询
- 这可能导致LLM返回中文答案

---

## 🔍 原因分析

### 原因1：数据集可能包含中文版本 ⚠️

**可能情况**：
1. **数据集被翻译**：可能有中文版本的FRAMES数据集
2. **数据集字段不同**：可能使用了不同的字段（如"Prompt"字段可能是中文）
3. **数据集混合**：可能使用了混合中英文的数据集

**验证方法**：
- 检查实际使用的数据集文件
- 检查数据集中的查询字段内容
- 确认是否有中文版本的数据集

---

### 原因2：查询在某个环节被翻译了 ⚠️

**可能情况**：
1. **数据导入时翻译**：在导入数据集时，查询被翻译成了中文
2. **查询预处理**：在查询预处理阶段，查询被翻译成了中文
3. **日志记录时翻译**：在记录日志时，查询被翻译成了中文

**验证方法**：
- 检查数据导入脚本
- 检查查询预处理逻辑
- 检查日志记录逻辑

---

### 原因3：使用了不同的数据集文件 ⚠️

**可能情况**：
1. **多个数据集文件**：可能有多个版本的FRAMES数据集文件
2. **数据集路径错误**：可能使用了错误的数据集文件路径
3. **数据集格式不同**：可能使用了不同格式的数据集文件

**验证方法**：
- 检查实际使用的数据集文件路径
- 检查数据集文件内容
- 确认数据集格式

---

## 📊 FRAMES数据集标准格式

### 标准FRAMES数据集格式

根据 `data/frames_benchmark/frames_dataset.json`，标准格式应该是：

```json
{
  "query_id": "test_query_0",
  "query": "If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?",
  "expected_answer": "Jane Ballou",
  "answer": "Jane Ballou",
  ...
}
```

**查询应该是英文的**：
- "If my future wife has the same first name as..."
- 而不是："美国第15任第一夫人的母亲的名字..."

---

## 🎯 解决方案

### 方案1：检查数据集文件 ✅

**目标**：确认实际使用的数据集文件内容

**步骤**：
1. 检查 `scripts/run_core_with_frames.py` 中使用的数据集路径
2. 检查数据集文件中的查询字段内容
3. 确认是否有中文版本的数据集

---

### 方案2：添加查询翻译功能（如果需要） ✅

**目标**：如果数据集包含中文查询，自动翻译为英文

**实现**：
```python
def translate_query_to_english(query: str) -> str:
    """将中文查询翻译为英文"""
    # 检测是否包含中文字符
    import re
    if not re.search(r'[\u4e00-\u9fff]', query):
        return query  # 没有中文，直接返回
    
    # 使用LLM翻译
    translation_prompt = f"""Translate the following query to English. 
    Keep the meaning and structure exactly the same, only translate the language.
    
    Query: {query}
    
    English translation:"""
    
    translated = llm._call_llm(translation_prompt)
    return translated.strip() if translated else query
```

**优点**：
- 确保查询是英文的
- 提高LLM理解准确性
- 统一查询格式

**缺点**：
- 增加处理时间
- 增加LLM调用成本

---

### 方案3：检查数据集加载逻辑 ✅

**目标**：确认数据集加载时是否正确提取查询字段

**检查点**：
1. `scripts/run_core_with_frames.py` 中的 `load_frames_dataset` 函数
2. `_process_single_sample` 函数中的查询提取逻辑
3. 确认使用的字段名（"query"、"question"、"Prompt"）

---

## 📝 建议

### 立即行动

1. **检查数据集文件** - 确认实际使用的数据集文件内容
2. **检查查询提取逻辑** - 确认是否正确提取查询字段
3. **检查数据集路径** - 确认是否使用了正确的数据集文件

### 如果需要支持中文查询

1. **添加查询翻译功能** - 在查询处理前，将中文查询翻译为英文
2. **更新提示词** - 确保提示词能够处理中文查询，但要求返回英文答案
3. **增强日志** - 记录原始查询和翻译后的查询

---

## 🔍 验证方法

### 步骤1：检查数据集文件

```bash
# 检查数据集文件中的查询内容
head -n 5 frames_dataset.json | python3 -m json.tool | grep -A 2 "query\|Prompt"
```

### 步骤2：检查日志中的查询来源

```bash
# 检查日志中查询的来源
grep -E "FRAMES sample.*query=" research_system.log | head -5
```

### 步骤3：检查数据集加载逻辑

检查 `scripts/run_core_with_frames.py` 中的查询提取逻辑。

---

## 📝 总结

### 问题

- 日志中出现中文查询，而FRAMES数据集应该是英文的
- 这可能导致LLM返回中文答案

### 可能原因

1. 数据集可能包含中文版本
2. 查询在某个环节被翻译了
3. 使用了不同的数据集文件

### 解决方案

1. 检查数据集文件内容
2. 检查查询提取逻辑
3. 如果需要，添加查询翻译功能

---

**报告生成时间**: 2025-11-28  
**状态**: ⚠️ 需要验证 - 需要检查数据集文件内容，确认中文查询的来源

