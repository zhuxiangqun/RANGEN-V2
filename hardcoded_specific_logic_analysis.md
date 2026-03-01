# 特定问题定制代码分析报告

**分析时间**: 2025-12-16  
**问题**: 发现多处针对特定问题（FRAMES数据集）的硬编码逻辑

---

## 🔍 发现的特定问题定制代码

### 1. `src/services/historical_knowledge_helper.py` ⚠️

**问题**: 虽然注释说"通用工具"，但实际上硬编码了特定实体类型

#### 问题1: `extract_historical_entities()` 方法
**位置**: 第124-183行

**硬编码内容**:
```python
# 提取总统序数（如"15th president", "第15任总统"）
president_match = re.search(r'(\d+)(?:th|st|nd|rd)?\s*(?:president|总统)', query_lower)
if president_match:
    entities["president_ordinal"] = int(president_match.group(1))
    entities["query_type"] = "president_query"

# 提取第一夫人序数
first_lady_match = re.search(r'(\d+)(?:th|st|nd|rd)?\s*(?:first\s+lady|第一夫人)', query_lower)
if first_lady_match:
    entities["first_lady_ordinal"] = int(first_lady_match.group(1))
    entities["query_type"] = "first_lady_query"

# 提取遇刺总统序数
assassinated_match = re.search(r'(?:second|2nd|第二位|第2位).*?(?:assassinated|遇刺)', query_lower)
if assassinated_match:
    entities["assassinated_president_order"] = 2
    entities["query_type"] = "assassinated_president_query"
```

**问题**:
- ❌ 硬编码"president"、"first lady"、"assassinated"等特定实体类型
- ❌ 只能处理特定的历史人物查询
- ❌ 无法扩展到其他领域（如"15th prime minister"、"second female CEO"等）

#### 问题2: `generate_enhanced_queries()` 方法
**位置**: 第185-228行

**硬编码内容**:
```python
# 如果检测到总统序数，生成专门查询
if entities.get("president_ordinal"):
    ordinal = entities["president_ordinal"]
    enhanced_queries.append(f"{ordinal}th president")
    enhanced_queries.append(f"{ordinal}th US president")
    enhanced_queries.append(f"{ordinal}th president United States")

# 如果检测到第一夫人序数，生成专门查询
if entities.get("first_lady_ordinal"):
    ordinal = entities["first_lady_ordinal"]
    enhanced_queries.append(f"{ordinal}th first lady")
    enhanced_queries.append(f"{ordinal}th US first lady")
    enhanced_queries.append(f"{ordinal}th first lady United States")
```

**问题**:
- ❌ 硬编码查询生成逻辑
- ❌ 只能生成特定实体类型的查询变体
- ❌ 无法扩展到其他实体类型

---

### 2. `src/core/reasoning/cognitive_answer_extractor.py` ⚠️

**问题**: `_extract_maiden_name()` 方法包含大量特定模式的硬编码逻辑

#### 问题: `_extract_maiden_name()` 方法
**位置**: 第546-666行

**硬编码内容**:
```python
# 策略1: 查找 "née" 或 "born" 标记
née_patterns = [
    rf'\b{re.escape(person_first_name)}\s+(?:\(née\s+)?([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)*',
    rf'\b{re.escape(person_first_name)}\s+([A-Z][a-z]+)\s+\(née\s+([A-Z][a-z]+)\)',
]

# 策略2: 查找姐妹关系，提取姐妹的姓氏
sister_patterns = [
    rf'(?:his|her)\s+sister\s+{re.escape(person_first_name)}[^,]*?,\s+([A-Z][a-z]+)',
    rf'{re.escape(person_first_name)}[^,]*?,\s+([A-Z][a-z]+)[^,]*?sister',
    rf'sister\s+{re.escape(person_first_name)}[^,]*?,\s+([A-Z][a-z]+)',
]

# 策略3: 查找 "wed her sister" 或类似模式
```

**问题**:
- ❌ 硬编码特定关系模式（"née"、"sister"等）
- ❌ 虽然注释说"通用方法"，但实际上针对特定文本模式
- ❌ 应该使用通用的实体提取和关系查询功能

**建议**:
- ✅ 应该使用 `SemanticUnderstandingPipeline.extract_entities_intelligent()` 提取实体
- ✅ 应该使用知识图谱查询关系，而不是硬编码模式匹配

---

### 3. `src/core/reasoning/evidence_processor.py` ⚠️

**问题**: 包含针对特定问题的硬编码模式匹配

#### 问题1: `_simplify_query_for_retrieval()` 方法
**位置**: 第830-870行

**硬编码内容**:
```python
# 提取序数+实体模式（如"15th first lady"）
ordinal_entity_match = re.search(r'(\d+(?:st|nd|rd|th))\s+([^?\'"]+?)(?:\'s|of|$)', query, re.IGNORECASE)
if ordinal_entity_match:
    ordinal = ordinal_entity_match.group(1)
    entity_part = ordinal_entity_match.group(2).strip()
    # 移除"of the United States"等修饰语
    entity_part = re.sub(r'\s+of\s+the\s+United\s+States', '', entity_part, flags=re.IGNORECASE)
    entity_part = entity_part.strip()
    if entity_part:
        return f"Who was the {ordinal} {entity_part}?"
```

**问题**:
- ❌ 硬编码"of the United States"修饰语移除
- ❌ 虽然使用了通用模式，但处理逻辑仍然针对特定问题

#### 问题2: `_decompose_with_generic_patterns()` 方法
**位置**: 第930-1030行

**硬编码内容**:
```python
# 检查是否包含筛选词（如"assassinated"、"first"、"second"等）
filter_keywords = ['first', 'second', 'third', 'last', 'assassinated', 'elected', 'appointed']
```

**问题**:
- ⚠️ 虽然使用了通用模式，但筛选词列表仍然有限
- ⚠️ 应该从统一配置中心获取，而不是硬编码

---

### 4. `src/core/reasoning/engine.py` ⚠️

**问题**: 包含大量针对特定问题的硬编码逻辑

#### 问题1: 占位符替换中的硬编码验证
**位置**: 第2082-2112行

**硬编码内容**:
```python
# 如果依赖步骤查询的是"second assassinated president"，检查替换值是否合理
if 'second' in dep_sub_query_lower and 'assassinated' in dep_sub_query_lower and 'president' in dep_sub_query_lower:
    # 验证替换值是否合理
    if 'first lady' in replacement.lower() or 'polk' in replacement.lower():
        self.logger.warning(f"❌ 替换值上下文不匹配：依赖步骤查询'second assassinated president'，但替换值是'{replacement}'（可能是第一夫人的名字）")

# 如果依赖步骤查询的是"15th first lady"，检查替换值是否合理
if ('15th' in dep_sub_query_lower or 'fifteenth' in dep_sub_query_lower) and 'first lady' in dep_sub_query_lower:
    # 验证替换值是否合理
    if 'garfield' in replacement.lower() or 'president' in replacement.lower():
        self.logger.warning(f"❌ 替换值上下文不匹配：依赖步骤查询'15th first lady'，但替换值是'{replacement}'（可能是总统的名字）")
```

**问题**:
- ❌ 硬编码特定实体名称（"polk"、"garfield"）
- ❌ 硬编码特定关系（"first lady"、"president"）
- ❌ 应该使用通用的实体类型验证，而不是硬编码名称

---

## 📊 问题总结

### 违反的原则

1. **DRY原则**: 为特定问题创建特定功能，而不是复用通用功能
2. **KISS原则**: 过度设计，增加了不必要的复杂性
3. **统一中心系统优先**: 未使用现有的通用实体提取和关系查询功能

### 影响

1. **可扩展性差**: 无法扩展到其他领域或问题类型
2. **维护成本高**: 需要为每个新问题类型添加特定代码
3. **代码重复**: 与现有通用功能重复

---

## ✅ 建议的通用化方案

### 1. `historical_knowledge_helper.py` 通用化

**当前**: 硬编码"president"、"first lady"等特定实体类型

**建议**: 
- 使用通用的实体类型提取（从查询中提取实体类型，而不是硬编码）
- 使用通用的序数提取（提取序数+实体类型，而不是特定实体类型）
- 使用知识图谱查询关系，而不是硬编码查询生成

### 2. `cognitive_answer_extractor.py` 通用化

**当前**: 硬编码"née"、"sister"等特定模式

**建议**:
- 使用 `SemanticUnderstandingPipeline.extract_entities_intelligent()` 提取实体
- 使用知识图谱查询关系（如"mother"、"maiden_name"等）
- 使用LLM理解语义，而不是硬编码模式匹配

### 3. `evidence_processor.py` 通用化

**当前**: 硬编码特定修饰语和筛选词

**建议**:
- 使用统一配置中心管理筛选词列表
- 使用通用的修饰语移除逻辑（不限于"of the United States"）

### 4. `engine.py` 通用化

**当前**: 硬编码特定实体名称和关系验证

**建议**:
- 使用通用的实体类型验证（通过NER识别实体类型）
- 使用知识图谱验证关系一致性，而不是硬编码名称

---

## 🎯 优先级

### P0 (高优先级)
1. **`historical_knowledge_helper.py`**: 完全重构为通用实体关系查询工具
2. **`engine.py` 中的硬编码验证**: 改为使用通用实体类型验证

### P1 (中优先级)
3. **`cognitive_answer_extractor.py`**: 使用通用实体提取和关系查询
4. **`evidence_processor.py`**: 使用统一配置中心管理筛选词

---

## 📝 相关文件

- `src/services/historical_knowledge_helper.py` - 历史知识辅助工具（需要通用化）
- `src/core/reasoning/cognitive_answer_extractor.py` - 认知答案提取器（需要通用化）
- `src/core/reasoning/evidence_processor.py` - 证据处理器（部分需要通用化）
- `src/core/reasoning/engine.py` - 推理引擎（部分需要通用化）

---

## ✅ 结论

发现多处针对特定问题的硬编码逻辑，这些代码应该被通用化，使用现有的通用功能（如实体提取、关系查询等）来替代。

