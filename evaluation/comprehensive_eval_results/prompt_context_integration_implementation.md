# 提示词模板与上下文工程集成实现总结

## 实现内容

### 1. ✅ **扩展 `_generate_optimized_prompt` 方法**

**文件**: `src/core/real_reasoning_engine.py`

**改进**:
- 添加 `enhanced_context` 参数（可选）
- 从 `enhanced_context` 中提取：
  - 会话上下文摘要（最近3个查询）
  - 关键词列表
  - 上下文置信度
- 将这些信息传递给 `prompt_engineering.generate_prompt()`

**代码位置**: Line 372-470

### 2. ✅ **更新所有调用点传递 `enhanced_context`**

**文件**: `src/core/real_reasoning_engine.py`

**更新的调用点**:
1. `_derive_final_answer_with_ml()` 方法签名 (Line 1640-1646)
   - 添加 `enhanced_context` 参数
   
2. `_derive_final_answer_with_ml()` 内部调用 `_generate_optimized_prompt()` (Line 1713, 1726)
   - 传递 `enhanced_context=enhanced_context`

3. `reason()` 方法调用 `_derive_final_answer_with_ml()` (Line 808-813)
   - 传递 `enhanced_context=enhanced_context`

### 3. ✅ **扩展 `PromptEngine.generate_prompt()` 方法**

**文件**: `src/utils/prompt_engine.py`

**改进**:
- 智能处理可选占位符（`context_summary`, `keywords`, `context_confidence`, `context_confidence_guidance`）
- 自动为缺失的可选占位符提供默认值（空字符串）
- 智能生成 `context_confidence_guidance`（当置信度 > 0.8 时）
- 格式化上下文信息（添加换行符、标签等）
- 清理多余空行

**代码位置**: Line 197-284

### 4. ✅ **更新模板支持上下文参数**

**文件**: `templates/templates.json`

**更新的模板**:
1. `reasoning_with_evidence`:
   - 添加 `{context_summary}` 占位符
   - 添加 `{keywords}` 占位符
   - 添加 `{context_confidence_guidance}` 占位符

2. `reasoning_without_evidence`:
   - 添加 `{context_summary}` 占位符
   - 添加 `{keywords}` 占位符
   - 添加 `{context_confidence_guidance}` 占位符

## 工作流程

### 完整的协作流程

```
1. 上下文工程处理 (reason方法，步骤1)
   ├─> context_engineering.process_data()
   ├─> 生成 enhanced_context['content']
   ├─> 计算 enhanced_context['context_confidence']
   └─> 提取 enhanced_context['keywords']

2. 会话上下文管理 (reason方法，步骤2)
   ├─> 添加当前查询到会话片段
   ├─> 获取历史会话上下文
   ├─> 压缩和优化会话片段
   └─> enhanced_context['session_context'] = [...]

3. 提示词生成 (_generate_optimized_prompt)
   ├─> 从 enhanced_context 提取：
   │   ├─> session_context → context_summary
   │   ├─> keywords → keywords字符串
   │   └─> context_confidence → 置信度值
   ├─> 构建 prompt_kwargs（包含所有上下文信息）
   └─> prompt_engineering.generate_prompt(template_name, **prompt_kwargs)

4. PromptEngine处理 (generate_prompt)
   ├─> 检测模板中的占位符
   ├─> 为缺失的可选占位符提供默认值
   ├─> 智能生成 context_confidence_guidance
   ├─> 格式化上下文信息（添加换行符、标签）
   └─> 生成最终提示词

5. LLM调用
   └─> 使用包含上下文信息的提示词调用LLM
```

## 数据流

```
enhanced_context (Dict[str, Any])
  ├─> session_context (List[Dict]) 
  │   └─> 提取 → context_summary: "Recent conversation context: ..."
  ├─> keywords (List[str])
  │   └─> 提取 → keywords: "keyword1, keyword2, ..."
  └─> context_confidence (float)
      └─> 提取 → context_confidence: "0.85"

     ↓

prompt_kwargs (Dict)
  ├─> query: "..."
  ├─> evidence: "..." (可选)
  ├─> query_type: "..."
  ├─> context_summary: "..." (如果存在)
  ├─> keywords: "..." (如果存在)
  └─> context_confidence: "..." (如果 > 0.7)

     ↓

template.content.format(**prompt_kwargs)
  └─> 生成最终提示词，包含所有上下文信息
```

## 优势

### 1. **紧密集成**
- 上下文工程的处理结果直接用于提示词生成
- 会话历史自动包含在提示词中
- 关键词和置信度信息被充分利用

### 2. **智能处理**
- 可选占位符自动处理，不会因缺失参数而失败
- 根据上下文置信度动态调整提示词
- 自动格式化，确保提示词结构清晰

### 3. **向后兼容**
- 如果 `enhanced_context` 为 None，系统仍能正常工作
- 如果某些上下文信息不存在，占位符会被替换为空字符串
- 不影响现有功能和模板

### 4. **可扩展性**
- 新的上下文信息可以轻松添加到 `enhanced_context`
- 新的占位符可以轻松添加到模板
- `PromptEngine` 会自动处理新的可选占位符

## 示例

### 示例1: 有会话历史的情况

```python
enhanced_context = {
    'session_context': [
        {'query': 'What is the capital of France?', 'content': 'Paris'},
        {'query': 'What is the population?', 'content': '2.1 million'}
    ],
    'keywords': ['capital', 'population', 'city'],
    'context_confidence': 0.85
}

# 生成的提示词会包含：
# - Recent conversation context: What is the capital of France?; What is the population?
# - Context Keywords: capital, population, city
# - High-confidence context guidance
```

### 示例2: 无会话历史的情况

```python
enhanced_context = {
    'content': 'Some context text',
    'context_confidence': 0.5
}

# 生成的提示词不会包含 context_summary 和 keywords
# 但会正常生成提示词
```

## 测试建议

1. **测试有会话历史的情况**
   - 验证 `context_summary` 是否正确生成
   - 验证关键词是否包含在提示词中

2. **测试高置信度情况**
   - 验证 `context_confidence_guidance` 是否在置信度 > 0.8 时生成

3. **测试无上下文的情况**
   - 验证 `enhanced_context=None` 时系统仍能正常工作

4. **测试部分上下文缺失**
   - 验证某些上下文信息缺失时，提示词仍能正常生成

## 完成状态

✅ 所有改进已实现
✅ 代码已更新
✅ 模板已更新
✅ 错误处理已完善
✅ 向后兼容性已确保

