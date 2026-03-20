# 提示词工程优化报告

**实施时间**: 2025-11-08  
**目标**: 优化提示词模板，明确知识内容使用和答案格式要求

---

## 📊 优化概览

### 核心改进

1. **在提示词开头明确知识内容和答案格式要求** ✅
2. **强调知识内容的使用** ✅
3. **明确答案格式要求** ✅

---

## 🔧 详细优化内容

### 1. 优化 `reasoning_with_evidence` 模板

**文件**: `templates/templates.json`

**改进内容**:

1. **在开头添加知识内容和答案格式要求**
   ```
   🎯 KNOWLEDGE AND ANSWER FORMAT REQUIREMENTS (READ FIRST):
   
   1. **KNOWLEDGE CONTENT USAGE (CRITICAL)**:
      - The Evidence section below contains RETRIEVED KNOWLEDGE from the knowledge base
      - You MUST actively USE this knowledge content to answer the question
      - If evidence is relevant, extract key information from it
      - If evidence is irrelevant, use your comprehensive knowledge base instead
      - DO NOT ignore the evidence - analyze it first, then decide whether to use it
   
   2. **ANSWER FORMAT (MANDATORY)**:
      - For numerical questions: Return ONLY the exact number
      - For ranking questions: Return ONLY the ordinal rank
      - For name questions: Return the COMPLETE, CORRECT name
      - For location/country questions: Return the EXACT location/country name
   ```

2. **改进证据处理部分**
   - 将 "Evidence" 改为 "Evidence (Retrieved Knowledge)"，明确这是检索到的知识
   - 强调证据包含知识内容，必须分析使用
   - 改进知识提取步骤，要求逐字阅读证据内容

3. **增强知识内容分析**
   - STEP 1: KNOWLEDGE CONTENT ANALYSIS（知识内容分析）
   - STEP 2: INTELLIGENT KNOWLEDGE USAGE（智能知识使用）
   - STEP 3: SYSTEMATIC KNOWLEDGE EXTRACTION（系统化知识提取）

---

### 2. 优化 `reasoning_without_evidence` 模板

**文件**: `templates/templates.json`

**改进内容**:

1. **在开头添加知识库使用和答案格式要求**
   ```
   🎯 KNOWLEDGE AND ANSWER FORMAT REQUIREMENTS (READ FIRST):
   
   1. **KNOWLEDGE BASE USAGE (CRITICAL)**:
      - You have access to a comprehensive internal knowledge base
      - You MUST actively search and use this knowledge to answer the question
      - Extract relevant facts, entities, relationships from your knowledge
      - DO NOT return "unable to determine" unless you have absolutely no knowledge
   
   2. **ANSWER FORMAT (MANDATORY)**:
      - [同上]
   ```

2. **增强知识集成部分**
   - 强调必须主动搜索知识库
   - 要求提取相关信息（名字、数字、日期、地点、事实）
   - 要求使用提取的知识形成答案
   - 要求验证答案

---

## 📈 优化效果

### 直接改进

1. **知识内容使用更明确** ✅
   - LLM会优先看到知识内容使用要求
   - 明确证据是检索到的知识，必须分析使用
   - 强调必须从知识内容中提取信息

2. **答案格式要求更明确** ✅
   - 在提示词开头就明确格式要求
   - 使用具体示例说明正确和错误格式
   - 针对不同查询类型提供具体格式要求

3. **知识提取步骤更详细** ✅
   - 要求逐字阅读证据内容
   - 要求提取关键实体、数字、名字、地点、日期
   - 要求识别关系和事实

### 间接改进

1. **提高答案准确性** ✅
   - LLM会更主动地使用知识内容
   - 减少忽略知识内容的情况

2. **提高答案格式一致性** ✅
   - LLM在生成时就知道需要什么格式
   - 减少格式转换的需要

---

## 🎯 优化策略

### 1. 在提示词开头明确要求

**优势**:
- LLM会优先看到这些要求
- 确保LLM在生成答案时遵循这些要求

### 2. 使用明确的术语

**改进**:
- "Evidence" → "Evidence (Retrieved Knowledge)"
- 明确说明这是检索到的知识内容
- 强调必须分析和使用

### 3. 提供具体示例

**改进**:
- 为每种查询类型提供正确和错误格式示例
- 使用 ✅ 和 ❌ 标记，清晰对比

---

## ✅ 总结

### 已完成的优化

1. **知识内容使用要求** - 在提示词开头明确要求使用知识内容 ✅
2. **答案格式要求** - 在提示词开头明确格式要求 ✅
3. **知识提取步骤** - 详细的知识内容分析和提取步骤 ✅

### 预期效果

- ✅ LLM会更主动地使用知识内容
- ✅ 答案格式更一致
- ✅ 答案准确性可能提高

---

*本报告基于2025-11-08的优化实施生成*

