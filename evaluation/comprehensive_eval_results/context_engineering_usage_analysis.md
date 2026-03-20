# 上下文工程在提示词工程中的使用情况分析

## 当前状况

### ✅ 已集成的部分

1. **PromptEngine支持上下文占位符**：
   - `context_summary` - 上下文摘要
   - `keywords` - 关键词
   - `context_confidence` - 上下文置信度
   - `context_confidence_guidance` - 置信度指导

2. **_generate_optimized_prompt提取上下文信息**：
   - 从`enhanced_context`提取`session_context`
   - 从`enhanced_context`提取`keywords`
   - 从`enhanced_context`提取`context_confidence`

3. **上下文信息传递给模板**：
   - 通过`prompt_kwargs`传递给`generate_prompt`
   - 模板中的占位符会被替换

### ⚠️ 存在的问题

1. **上下文摘要质量低**：
   ```python
   # 当前实现（real_reasoning_engine.py:494-502）
   recent_queries = []
   for fragment in session_context[-3:]:
       frag_query = fragment.get('query', '') or fragment.get('content', '')
       if frag_query:
           recent_queries.append(frag_query[:50])
   context_summary = f"Recent conversation context: {'; '.join(recent_queries)}"
   ```
   - **问题**：只是简单拼接查询文本，没有真正的摘要
   - **应该**：使用NLP引擎或LLM生成真正的摘要

2. **关键词提取不够智能**：
   ```python
   # 当前实现（real_reasoning_engine.py:826-829）
   words = context_text.lower().split()
   keywords = [w for w in words if len(w) > 3][:10]
   ```
   - **问题**：只是简单的词分割，没有考虑语义重要性
   - **应该**：使用NLP引擎提取语义关键词

3. **上下文工程模块没有被充分利用**：
   - `EnhancedContextEngineering.process_data`被调用，但返回的`answer`没有被用于生成摘要
   - 上下文工程模块的功能没有被充分利用

4. **上下文置信度使用不充分**：
   - 只在置信度>0.8时添加简单提示
   - 没有根据置信度调整提示词的详细程度或结构

## 改进建议

### 1. 使用NLP引擎生成真正的上下文摘要

```python
def _generate_context_summary(self, session_context: List[Dict]) -> str:
    """生成真正的上下文摘要"""
    if not session_context:
        return ""
    
    try:
        from src.ai.nlp_engine import get_nlp_engine
        nlp_engine = get_nlp_engine()
        
        # 收集所有上下文文本
        context_texts = []
        for fragment in session_context[-5:]:  # 最近5个
            if isinstance(fragment, dict):
                text = fragment.get('query', '') or fragment.get('content', '')
                if text:
                    context_texts.append(text)
        
        if not context_texts:
            return ""
        
        # 合并文本
        combined_text = ' '.join(context_texts)
        
        # 使用NLP引擎生成摘要
        summary = nlp_engine.generate_summary(combined_text, max_sentences=3)
        
        return f"Conversation context: {summary}"
    except Exception as e:
        self.logger.debug(f"NLP摘要生成失败，使用简单摘要: {e}")
        # Fallback到简单摘要
        return self._generate_simple_context_summary(session_context)
```

### 2. 使用NLP引擎提取语义关键词

```python
def _extract_context_keywords(self, context_text: str, query: str) -> List[str]:
    """提取语义关键词"""
    try:
        from src.ai.nlp_engine import get_nlp_engine
        nlp_engine = get_nlp_engine()
        
        # 合并查询和上下文
        combined_text = f"{query} {context_text}"
        
        # 使用NLP引擎提取关键词
        keywords = nlp_engine.extract_keywords(combined_text, top_k=5)
        
        return keywords
    except Exception as e:
        self.logger.debug(f"NLP关键词提取失败，使用简单提取: {e}")
        # Fallback到简单提取
        return self._extract_simple_keywords(context_text)
```

### 3. 充分利用上下文工程模块

```python
def _enhance_context_with_engineering(self, query: str, base_context: Dict) -> Dict:
    """使用上下文工程模块增强上下文"""
    enhanced_context = base_context.copy()
    
    if self.context_engineering:
        try:
            # 调用上下文工程模块
            context_request = ContextRequest(
                query=query,
                metadata={'original_context': str(base_context)}
            )
            context_response = self.context_engineering.process_data(context_request)
            
            if context_response and context_response.answer:
                # 使用上下文工程的结果
                enhanced_context['content'] = context_response.answer
                enhanced_context['context_confidence'] = context_response.confidence
                
                # 从上下文工程的结果中提取摘要和关键词
                if hasattr(self.context_engineering, 'generate_summary'):
                    enhanced_context['summary'] = self.context_engineering.generate_summary(
                        context_response.answer
                    )
                if hasattr(self.context_engineering, 'extract_keywords'):
                    enhanced_context['keywords'] = self.context_engineering.extract_keywords(
                        context_response.answer
                    )
        except Exception as e:
            self.logger.debug(f"上下文工程处理失败: {e}")
    
    return enhanced_context
```

### 4. 根据上下文置信度调整提示词

```python
def _adjust_prompt_by_confidence(self, prompt: str, confidence: float) -> str:
    """根据上下文置信度调整提示词"""
    if confidence > 0.8:
        # 高置信度：强调使用上下文
        prompt += "\n\n⚠️ IMPORTANT: High-confidence context information is available. Please prioritize using this context in your reasoning."
    elif confidence > 0.5:
        # 中等置信度：建议参考上下文
        prompt += "\n\nℹ️ NOTE: Context information is available. Consider it in your reasoning, but verify with your knowledge base."
    else:
        # 低置信度：主要依赖知识库
        prompt += "\n\n⚠️ NOTE: Context information has low confidence. Rely primarily on your knowledge base."
    
    return prompt
```

## 实施优先级

### P0（高优先级）
1. ✅ 使用NLP引擎生成真正的上下文摘要
2. ✅ 使用NLP引擎提取语义关键词

### P1（中优先级）
3. 充分利用上下文工程模块的功能
4. 根据上下文置信度调整提示词

### P2（低优先级）
5. 在更多模板中使用上下文信息
6. 建立上下文使用效果评估机制

## 结论

**当前状态**：
- ✅ 基础集成已完成（占位符、参数传递）
- ⚠️ 上下文信息质量不高（简单拼接、简单提取）
- ⚠️ 上下文工程模块功能未充分利用

**改进方向**：
1. 使用NLP引擎提升上下文摘要和关键词质量
2. 充分利用上下文工程模块的功能
3. 根据上下文置信度动态调整提示词

**预期效果**：
- 上下文信息质量提升（真正的摘要、语义关键词）
- 提示词质量提升（更准确的上下文指导）
- 答案质量提升（更好的上下文理解）

