# 根本原因详细分析报告

## 问题现象

**最终答案**: `[ERROR] Prompt中未找到查询内容，无法调用LLM`  
**期望答案**: `Jane Ballou`  
**执行时间**: 327.32秒

## 执行流程追踪

### 1. 查询传递路径

```
用户查询
  ↓
IntelligentOrchestrator.orchestrate()
  ↓
RealReasoningEngine.reason(query, context, session_id)
  ↓
AnswerExtractor.derive_final_answer_with_ml(query, evidence, steps, ...)
  ↓
PromptGenerator.generate_optimized_prompt("reasoning_with_evidence", query=query, ...)
  ↓
PromptEngine.generate_prompt(template_name, **prompt_kwargs)
  ↓
模板替换: template.content.format(**safe_kwargs)
  ↓
返回 prompt
  ↓
AnswerExtractor 验证 prompt 是否包含查询内容
```

### 2. 代码检查结果

#### 2.1 查询参数传递 ✅

**位置**: `src/core/reasoning/prompt_generator.py:127-130`
```python
prompt_kwargs = {
    'query': query,  # ✅ query 被正确传递
    'query_type': query_type
}
```

**确认**: `query` 参数被正确传递到 `prompt_kwargs` 中。

#### 2.2 模板占位符 ✅

**位置**: `templates/templates.json:38`
```json
{
  "name": "reasoning_with_evidence",
  "content": "Question: {query}\n\nEvidence: {evidence}\n\n..."
}
```

**确认**: 模板中包含 `{query}` 占位符。

#### 2.3 占位符替换逻辑 ✅

**位置**: `src/utils/prompt_engine.py:303-305`
```python
try:
    prompt = escaped_content.format(**safe_kwargs)
except KeyError as e:
    # 如果占位符缺失，会抛出 KeyError
```

**确认**: 占位符替换逻辑正常，如果 `query` 不在 `safe_kwargs` 中会抛出 `KeyError`。

#### 2.4 验证逻辑 ⚠️

**位置**: `src/core/reasoning/answer_extractor.py:1386-1422`
```python
# 检查查询关键词
query_keywords = ["Query:", "query:", "问题:", "问题：", "Question:", "question:"]
query_in_prompt = any(keyword in prompt for keyword in query_keywords)

# 如果关键词检查失败，检查查询内容本身
if not query_in_prompt:
    query_prefix = query[:50].strip()
    if query_prefix and len(query_prefix) > 10:
        query_in_prompt = query_prefix in prompt

# 如果还是没找到，检查查询的关键词
if not query_in_prompt:
    query_words = query.lower().split()
    key_words = [w for w in query_words if len(w) > 3][:5]
    if key_words:
        prompt_lower = prompt.lower()
        query_in_prompt = any(word in prompt_lower for word in key_words)

if not query_in_prompt:
    # 即使验证失败，也尝试继续执行（记录警告）
    self.logger.warning(f"⚠️ Prompt验证失败，但尝试继续调用LLM")
    # 不返回错误，继续执行
```

**问题**: 验证逻辑已经被修改为即使验证失败也继续执行，但日志中仍然显示返回了错误。

## 根本原因分析

### 假设1: Prompt 生成失败，返回 None 或空字符串

**检查**: `src/core/reasoning/prompt_generator.py:184-267`

```python
prompt = self.prompt_engineering.generate_prompt(template_name, **prompt_kwargs)

if prompt:
    # 处理 prompt
    return prompt

# Fallback: 使用简单提示词
return self.get_fallback_prompt(template_name, query, evidence, query_type)
```

**结论**: 如果 `prompt_engineering.generate_prompt` 返回 None，会调用 `get_fallback_prompt`，它应该生成包含 `Query: {query}` 的 prompt。

### 假设2: 模板中的 {query} 占位符被错误转义

**检查**: `src/utils/prompt_engine.py:265-301`

代码逻辑：
1. 先保护所有有效的占位符（使用临时标记）
2. 转义所有剩余的大括号（`{` → `{{`, `}` → `}}`）
3. 恢复占位符

**潜在问题**: 如果 `query` 不在 `valid_placeholders` 中（即不在 `safe_kwargs` 中），那么 `{query}` 会被转义为 `{{query}}`，导致占位符无法被替换。

**验证**: 需要检查 `safe_kwargs` 是否包含 `query`。

### 假设3: Query 参数为空或 None

**检查**: `src/core/reasoning/answer_extractor.py:1258`

```python
async def derive_final_answer_with_ml(
    self, 
    query: str,  # 类型提示是 str，但可能是 None 或空字符串
    ...
)
```

**潜在问题**: 如果 `query` 是空字符串或 None，那么：
1. `prompt_kwargs['query'] = query` 会设置 `query` 为空字符串
2. 模板替换后，prompt 中会有 `Question: ` 但没有查询内容
3. 验证逻辑可能无法识别这种情况

### 假设4: 验证逻辑过于严格，误判有效 prompt

**检查**: 从日志中看到，验证逻辑已经被修改为即使验证失败也继续执行，但最终答案仍然是错误。

**可能原因**:
1. 验证失败后，虽然代码继续执行，但 LLM 调用可能因为其他原因失败
2. 或者，验证逻辑在某个地方仍然返回了错误（代码可能有多个返回点）

## 最可能的原因

基于代码分析，**最可能的原因是假设3: Query 参数为空或 None**。

### 证据支持

1. **日志显示**: `💾 [证据收集-缓存保存] 查询='James Garfield What name mother...'`
   - 查询被截断了，可能在实际传递时被进一步截断或丢失

2. **验证逻辑**: 验证逻辑检查多种格式，如果都失败，说明 prompt 中确实没有查询内容

3. **代码流程**: 
   - `prompt_generator.generate_optimized_prompt` 接收 `query` 参数
   - 如果 `query` 是空字符串，`prompt_kwargs['query'] = ''`
   - 模板替换后，prompt 中会有 `Question: ` 但没有查询内容
   - 验证逻辑检查 `"Question:" in prompt` 会成功，但检查查询内容本身会失败

## 解决方案

### 方案1: 在 prompt_generator 中添加查询验证

**位置**: `src/core/reasoning/prompt_generator.py:36`

```python
def generate_optimized_prompt(
    self, 
    template_name: str, 
    query: str,  # 添加验证
    ...
) -> str:
    # 🚀 P0修复：验证查询是否为空
    if not query or not query.strip():
        self.logger.error(f"❌ 查询为空，无法生成prompt: template_name={template_name}")
        return self.get_fallback_prompt(template_name, "", evidence, query_type)
    
    # 确保 query 不为空
    query = query.strip()
    
    # 继续原有逻辑
    ...
```

### 方案2: 在 answer_extractor 中添加更详细的日志

**位置**: `src/core/reasoning/answer_extractor.py:1343`

```python
if self.prompt_generator:
    prompt = self.prompt_generator.generate_optimized_prompt(
        "reasoning_with_evidence",
        query=query,
        ...
    )
    
    # 🚀 P0修复：记录 prompt 生成结果
    if not prompt:
        self.logger.error(f"❌ Prompt生成失败: query长度={len(query) if query else 0}, query预览={query[:100] if query else 'None'}")
    else:
        self.logger.debug(f"✅ Prompt生成成功: query长度={len(query) if query else 0}, prompt长度={len(prompt)}, prompt预览={prompt[:200]}")
```

### 方案3: 改进验证逻辑，记录详细的 prompt 内容

**位置**: `src/core/reasoning/answer_extractor.py:1411`

```python
if not query_in_prompt:
    error_msg = "[ERROR] Prompt中未找到查询内容，无法调用LLM"
    # 🚀 P0修复：记录完整的prompt内容用于调试
    prompt_preview = prompt[:1000] if prompt else "None"  # 增加到1000字符
    self.logger.error(f"❌ {error_msg}: query='{query[:100] if query else 'None'}...', query长度={len(query) if query else 0}, prompt长度={len(prompt) if prompt else 0}")
    self.logger.error(f"❌ Prompt完整内容（前1000字符）: {prompt_preview}")
    
    # 🚀 P0修复：检查 prompt 中是否包含 "Question:" 但没有查询内容
    if "Question:" in prompt or "question:" in prompt.lower():
        # 提取 Question: 后面的内容
        import re
        question_match = re.search(r'Question:\s*(.+?)(?:\n|$)', prompt, re.IGNORECASE)
        if question_match:
            question_content = question_match.group(1).strip()
            self.logger.error(f"❌ Prompt中包含 'Question:' 但内容为空或无效: '{question_content[:100]}'")
    
    # 即使验证失败，也尝试继续执行
    self.logger.warning(f"⚠️ Prompt验证失败，但尝试继续调用LLM（可能是验证逻辑过于严格）")
    # 不返回错误，继续执行
```

## 下一步行动

1. **立即实施**: 添加详细的日志记录，记录 prompt 生成和验证的完整过程
2. **验证**: 运行测试，查看日志中的 prompt 内容，确认查询是否被正确包含
3. **修复**: 根据日志结果，修复具体的问题点

## 关键检查点

1. ✅ `query` 参数是否被正确传递到 `prompt_generator.generate_optimized_prompt`
2. ✅ `prompt_kwargs` 是否包含 `query` 键
3. ✅ 模板中是否有 `{query}` 占位符
4. ⚠️ `query` 参数是否为空或 None
5. ⚠️ 占位符替换是否成功
6. ⚠️ 生成的 prompt 是否包含查询内容

