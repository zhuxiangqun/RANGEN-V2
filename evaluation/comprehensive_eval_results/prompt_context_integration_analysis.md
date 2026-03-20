# 提示词模板与上下文工程配合使用分析

## 当前协作方式

### 1. **执行顺序**
```
推理流程 (reason方法):
├── 步骤1: 上下文工程处理
│   ├── 调用 context_engineering.process_data()
│   ├── 处理原始上下文（清理、预处理）
│   └── 生成增强上下文 (enhanced_context)
├── 步骤2: 会话上下文管理
│   ├── 添加当前查询到会话片段
│   ├── 获取历史会话上下文
│   └── 压缩和优化会话片段
├── 步骤3: 提示词工程
│   ├── 配置 prompt_config (包含 enhanced_context)
│   └── 但实际生成提示词时没有充分利用 enhanced_context
└── 步骤4-8: 证据收集、推理执行等
    └── 在 _generate_optimized_prompt 中生成提示词
```

### 2. **当前问题**

#### 问题1: 上下文工程处理结果未被充分利用
```python
# 在 reason 方法中 (line 616-624)
context_response = self.context_engineering.process_data(context_request)
if context_response and context_response.answer:
    enhanced_context['content'] = context_response.answer  # ✅ 保存了结果
    enhanced_context['enhanced'] = True
    enhanced_context['context_confidence'] = context_response.confidence
```

但是，在后续的提示词生成中（`_generate_optimized_prompt`），并没有使用这些增强后的上下文信息。

#### 问题2: 提示词模板参数不完整
```python
# 在 _generate_optimized_prompt 方法中 (line 1655-1660)
prompt = self._generate_optimized_prompt(
    "reasoning_with_evidence",
    query=query,
    evidence=enhanced_evidence_text,  # ✅ 使用了增强的证据
    query_type=query_type
    # ❌ 但没有传递增强后的上下文信息
    # ❌ 没有传递 session_context
    # ❌ 没有传递关键词、置信度等元数据
)
```

#### 问题3: 会话上下文没有被传递给提示词
```python
# 在 reason 方法中 (line 685-697)
enhanced_context['session_context'] = session_context['fragments']
enhanced_context['session_metadata'] = session_context

# 但这些信息在提示词生成时没有被使用
```

## 理想的协作方式

### 设计原则

1. **上下文工程处理原始数据**
   - 清理和规范化上下文内容
   - 提取关键信息和关键词
   - 压缩和优化长文本
   - 计算上下文质量和置信度

2. **提示词模板使用增强后的上下文**
   - 接收增强后的上下文数据
   - 包含关键词、会话历史、置信度等元数据
   - 根据上下文质量调整提示词策略

3. **会话管理提供连续上下文**
   - 维护多轮对话的历史
   - 压缩和优化历史片段
   - 将相关历史传递给提示词

### 改进方案

#### 方案1: 增强 `_generate_optimized_prompt` 方法

```python
def _generate_optimized_prompt(
    self, 
    template_name: str, 
    query: str, 
    evidence: Optional[str] = None, 
    query_type: str = "general",
    enhanced_context: Optional[Dict[str, Any]] = None  # 🚀 新增参数
) -> str:
    """生成优化的提示词（使用增强后的上下文）"""
    
    # 提取增强后的上下文信息
    session_context = enhanced_context.get('session_context', []) if enhanced_context else []
    keywords = enhanced_context.get('keywords', []) if enhanced_context else []
    context_confidence = enhanced_context.get('context_confidence', 0.5) if enhanced_context else 0.5
    
    # 构建上下文摘要
    context_summary = ""
    if session_context:
        recent_queries = [f.get('query', '') for f in session_context[-3:] if f.get('query')]
        if recent_queries:
            context_summary = f"Recent conversation context: {'; '.join(recent_queries)}"
    
    # 传递给提示词模板
    if self.prompt_engineering:
        prompt = self.prompt_engineering.generate_prompt(
            template_name,
            query=query,
            evidence=evidence,
            query_type=query_type,
            context_summary=context_summary,  # 🚀 新增
            keywords=', '.join(keywords[:5]) if keywords else '',  # 🚀 新增
            context_confidence=context_confidence  # 🚀 新增
        )
```

#### 方案2: 扩展提示词模板支持上下文参数

在 `templates.json` 中的模板可以包含上下文相关的占位符：

```json
{
  "name": "reasoning_with_evidence",
  "content": "You are a professional reasoning assistant.\n\nQuery: {query}\n\nEvidence:\n{evidence}\n\n{context_summary}\n\nContext Keywords: {keywords}\n\n[If context_confidence > 0.8, add:] Based on high-confidence context analysis, please prioritize the following insights...\n\nCRITICAL INSTRUCTIONS:\n..."
}
```

#### 方案3: 上下文感知的模板选择

根据增强后的上下文质量选择不同的模板：

```python
def _select_prompt_template(
    self, 
    query: str, 
    enhanced_context: Dict[str, Any],
    has_evidence: bool
) -> str:
    """根据上下文质量选择最佳模板"""
    
    context_confidence = enhanced_context.get('context_confidence', 0.5)
    session_context = enhanced_context.get('session_context', [])
    
    if has_evidence:
        if context_confidence > 0.8 and session_context:
            return "reasoning_with_evidence_and_context"  # 高置信度+会话历史
        else:
            return "reasoning_with_evidence"  # 标准模板
    else:
        if context_confidence > 0.8:
            return "reasoning_without_evidence_high_confidence"
        else:
            return "reasoning_without_evidence"
```

## 具体改进建议

### 优先级1: 立即改进（高优先级）

1. **修改 `_generate_optimized_prompt` 方法**
   - 添加 `enhanced_context` 参数
   - 提取会话上下文、关键词等元数据
   - 将这些信息传递给 `prompt_engineering.generate_prompt()`

2. **扩展模板占位符**
   - 在关键模板中添加 `{context_summary}`, `{keywords}`, `{context_confidence}` 等占位符
   - 在模板中根据上下文置信度调整提示词策略

### 优先级2: 中期改进（中优先级）

3. **上下文感知的模板选择**
   - 根据上下文质量自动选择最佳模板
   - 为不同场景创建专用模板（高置信度、低置信度、会话上下文丰富等）

4. **增强上下文工程的处理能力**
   - 提取更丰富的元数据（实体、主题、情感等）
   - 提供更智能的压缩和摘要
   - 计算更准确的置信度

### 优先级3: 长期优化（低优先级）

5. **动态提示词生成**
   - 根据上下文动态调整提示词内容和结构
   - 实现上下文感知的提示词优化

6. **上下文反馈循环**
   - 根据LLM响应质量反馈调整上下文处理策略
   - 学习最优的上下文-提示词组合

## 当前代码中的具体位置

### 需要修改的文件和位置

1. **`src/core/real_reasoning_engine.py`**:
   - `_generate_optimized_prompt()` (line 372-418): 添加 `enhanced_context` 参数
   - `_derive_final_answer_with_ml()` (line 1487-1690): 传递 `enhanced_context` 给 `_generate_optimized_prompt()`

2. **`templates/templates.json`**:
   - `reasoning_with_evidence`: 添加上下文相关的占位符
   - `reasoning_without_evidence`: 添加上下文相关的占位符

3. **`src/utils/prompt_engine.py`**:
   - `generate_prompt()`: 支持新的上下文相关参数

## 总结

当前系统**已经实现了上下文工程和提示词工程的基础协作**，但存在以下改进空间：

✅ **已实现**:
- 上下文工程处理原始上下文
- 会话上下文管理
- 提示词模板系统

❌ **需要改进**:
- 增强后的上下文信息没有被充分利用
- 提示词模板没有接收增强后的上下文参数
- 会话历史没有被传递给提示词

通过上述改进，可以让上下文工程和提示词工程更紧密地协作，充分利用增强后的上下文信息，生成更精准和上下文感知的提示词。

