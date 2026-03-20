# 为什么直接判断与核心系统判断复杂度差异巨大？

**分析时间**: 2025-11-25  
**问题**: 为什么让DeepSeek直接判断数据集数据时，需要深度思考模型的问题轮次 ≈ 10–15%，而核心系统判断时却是几乎100%？

---

## 🔍 关键发现

### 1. **数据集字段提取问题**

#### 核心系统提取查询的逻辑

```python
# scripts/run_core_with_frames.py:281
query_text = (item.get("query") or item.get("question") or str(item)).strip()
```

**问题**：
- 优先使用 `"query"` 字段
- 如果没有，使用 `"question"` 字段
- 如果都没有，使用 `str(item)`（整个字典转成字符串）

#### 数据集实际字段

| 数据集文件 | 使用的字段 | 字段名 |
|-----------|-----------|--------|
| `data/frames_dataset.json` | `"Prompt"` | ❌ 不是 `"query"` |
| `data/frames_benchmark/frames_dataset.json` | `"query"` | ✅ 是 `"query"` |
| `data/frames-benchmark/queries.json` | `"query"` | ✅ 是 `"query"` |

**关键问题**：
- 如果使用 `data/frames_dataset.json`（使用 `"Prompt"` 字段）
- 核心系统会找不到 `"query"` 字段
- 会使用 `str(item)`，把整个字典转成字符串
- 这会导致查询文本完全不同！

### 2. **查询文本差异**

#### 直接判断数据集数据

**使用的文本**：
```json
{
  "Prompt": "If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name? "
}
```

**提取的查询**：
```
"If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name? "
```

#### 核心系统判断（如果字段提取错误）

**如果使用 `str(item)`**：
```python
str(item) = "{'Unnamed: 0': 0, 'Prompt': 'If my future wife...', 'Answer': 'Jane Ballou', 'wikipedia_link_1': 'https://...', ...}"
```

**提取的查询**：
```
"{'Unnamed: 0': 0, 'Prompt': 'If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name? ', 'Answer': 'Jane Ballou', 'wikipedia_link_1': 'https://en.wikipedia.org/wiki/President_of_the_United_States', 'wikipedia_link_2': 'https://en.wikipedia.org/wiki/James_Buchanan', ...}"
```

**差异**：
- 直接判断：只使用查询文本本身（~150字符）
- 核心系统（错误提取）：使用整个字典的字符串表示（可能包含所有字段，数千字符）

### 3. **LLM判断时的文本截断**

#### LLM复杂度判断的提示词

```python
# src/core/llm_integration.py:435
Query: {query[:500]}  # 只使用前500个字符
```

**如果查询文本是字典字符串**：
- 前500字符可能包含：`{'Unnamed: 0': 0, 'Prompt': '...', 'Answer': '...', 'wikipedia_link_1': '...', ...}`
- LLM看到的不是查询本身，而是包含答案、链接等信息的字典字符串
- 这会导致LLM误判复杂度

---

## 🔍 为什么会产生差异？

### 1. **字段提取错误**

**如果核心系统使用 `data/frames_dataset.json`**：
- 数据集使用 `"Prompt"` 字段
- 核心系统优先查找 `"query"` 字段
- 找不到 `"query"` 字段
- 使用 `str(item)`，把整个字典转成字符串
- 查询文本变成包含所有字段的字典字符串

**如果核心系统使用 `data/frames_benchmark/frames_dataset.json`**：
- 数据集使用 `"query"` 字段
- 核心系统找到 `"query"` 字段
- 查询文本正确提取

### 2. **查询文本长度差异**

| 场景 | 查询文本长度 | 内容 |
|------|------------|------|
| **直接判断** | ~100-200字符 | 只包含查询本身 |
| **核心系统（正确）** | ~100-200字符 | 只包含查询本身 |
| **核心系统（错误）** | ~1000-5000字符 | 包含查询+答案+链接+所有字段 |

### 3. **LLM判断时的上下文差异**

#### 直接判断

**LLM看到的文本**：
```
Query: If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?
```

**LLM判断**：
- 看到的是纯粹的查询文本
- 可以正确判断复杂度
- 对于简单的查询，可能判断为 "simple" 或 "medium"

#### 核心系统判断（如果字段提取错误）

**LLM看到的文本**：
```
Query: {'Unnamed: 0': 0, 'Prompt': 'If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name? ', 'Answer': 'Jane Ballou', 'wikipedia_link_1': 'https://en.wikipedia.org/wiki/President_of_the_United_States', ...
```

**LLM判断**：
- 看到的是包含答案、链接等信息的字典字符串
- 可能误判复杂度（因为文本很长，包含很多信息）
- 更可能判断为 "complex"

---

## 🔍 验证假设

### 假设1：字段提取错误

**验证方法**：
1. 检查实际使用的数据集文件
2. 检查查询文本提取逻辑
3. 检查LLM判断时使用的查询文本

### 假设2：查询文本预处理

**验证方法**：
1. 检查是否有查询文本的预处理
2. 检查是否有查询文本的截断或修改
3. 检查是否有额外的上下文信息

### 假设3：判断时机不同

**验证方法**：
1. 直接判断：在数据集加载后立即判断
2. 核心系统判断：在系统处理流程中判断
3. 检查判断时是否有额外的上下文信息

---

## 🎯 解决方案

### 1. **修复字段提取逻辑**

```python
# 修复前
query_text = (item.get("query") or item.get("question") or str(item)).strip()

# 修复后
query_text = (item.get("query") or item.get("question") or item.get("Prompt") or str(item)).strip()
```

**改进**：
- 添加对 `"Prompt"` 字段的支持
- 确保能正确提取查询文本

### 2. **添加字段提取日志**

```python
# 添加日志，记录实际提取的字段
if "query" in item:
    query_text = item["query"]
    log_info(f"使用query字段提取查询")
elif "Prompt" in item:
    query_text = item["Prompt"]
    log_info(f"使用Prompt字段提取查询")
elif "question" in item:
    query_text = item["question"]
    log_info(f"使用question字段提取查询")
else:
    query_text = str(item)
    log_warning(f"⚠️ 未找到查询字段，使用str(item)，可能导致查询文本错误")
```

### 3. **验证查询文本**

```python
# 验证查询文本是否合理
if len(query_text) > 1000:
    log_warning(f"⚠️ 查询文本过长（{len(query_text)}字符），可能是字段提取错误")
    # 尝试从字典字符串中提取实际的查询
    if "Prompt" in str(item):
        # 尝试提取Prompt字段的内容
        ...
```

---

## 🎯 结论

### 1. **差异的根本原因**

1. **字段提取错误**：
   - 核心系统优先查找 `"query"` 字段
   - 如果数据集使用 `"Prompt"` 字段，会找不到
   - 使用 `str(item)`，把整个字典转成字符串
   - 查询文本变成包含所有字段的字典字符串

2. **查询文本长度差异**：
   - 直接判断：只使用查询本身（~100-200字符）
   - 核心系统（错误）：使用字典字符串（~1000-5000字符）

3. **LLM判断时的上下文差异**：
   - 直接判断：看到纯粹的查询文本
   - 核心系统（错误）：看到包含答案、链接等信息的字典字符串

### 2. **为什么核心系统判断几乎100%为complex**

- 如果字段提取错误，查询文本变成字典字符串
- 字典字符串很长，包含很多信息（答案、链接等）
- LLM看到这种文本，更可能判断为 "complex"
- 导致几乎所有查询都被判断为 "complex"

### 3. **验证方法**

1. 检查实际使用的数据集文件
2. 检查查询文本提取逻辑
3. 检查LLM判断时使用的查询文本
4. 添加日志，记录实际提取的字段和查询文本

---

**报告生成时间**: 2025-11-25  
**分析人员**: AI Assistant  
**状态**: ✅ 差异原因已分析清楚，需要验证字段提取逻辑

