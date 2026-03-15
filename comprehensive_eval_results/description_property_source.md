# Description属性来源说明

**创建时间**: 2025-11-16

---

## Description属性的两个来源

### 1. LLM从文本中提取的description属性 ✅

**来源**: LLM根据prompt从文本内容中提取

**Prompt要求**:
```
**IMPORTANT - PROPERTY EXTRACTION GUIDELINES**:
1. **Extract ALL properties mentioned in the text** - this is critical for knowledge graph quality
2. **Look carefully for property information** in the text:
   - For Person entities: birth_date, death_date, nationality, occupation, description
   - For Location entities: location, country, region, description
   - For Organization entities: founded_date, location, description
   - For Event entities: date, location, description
   - For all entities: description (brief summary of what the entity is)
3. **Extract properties from context** - even if not explicitly stated, infer from the text:
   - If the text says 'John Adams was born in 1735', extract birth_date: '1735'
   - If the text says 'Harvard University in Cambridge', extract location: 'Cambridge'
   - If the text describes what an entity is, extract a description property
4. **Properties should be concise and factual**, extracted directly from the text or inferred from context
5. **DO NOT return empty properties objects {{}}** - if you cannot find any properties, at least provide a 'description' property based on the entity's role in the text
6. **Be thorough** - extract all relevant properties mentioned or implied in the text
```

**提取方式**:
- LLM分析文本内容，识别实体的描述信息
- 从文本中提取实体的简要描述（brief summary）
- 基于实体在文本中的角色和上下文推断description

**示例**:
- 如果文本说"John Adams was the second President of the United States"，LLM可能提取：
  ```json
  {
    "name": "John Adams",
    "type": "Person",
    "properties": {
      "description": "second President of the United States"
    }
  }
  ```

---

### 2. 系统自动补充的默认description属性 ✅

**触发条件**: 当LLM没有提取到任何属性时（属性为空）

**补充逻辑**:
```python
# 如果实体没有属性，基于实体类型生成默认description
if not filtered_properties:
    entity_type = e.get('type', 'Entity')
    if entity_type == 'Person':
        filtered_properties['description'] = f"Person mentioned in the text: {entity_name}"
    elif entity_type == 'Location':
        filtered_properties['description'] = f"Location mentioned in the text: {entity_name}"
    elif entity_type == 'Organization':
        filtered_properties['description'] = f"Organization mentioned in the text: {entity_name}"
    elif entity_type == 'Event':
        filtered_properties['description'] = f"Event mentioned in the text: {entity_name}"
    else:
        filtered_properties['description'] = f"Entity mentioned in the text: {entity_name}"
```

**默认description格式**:
- Person: `"Person mentioned in the text: {entity_name}"`
- Location: `"Location mentioned in the text: {entity_name}"`
- Organization: `"Organization mentioned in the text: {entity_name}"`
- Event: `"Event mentioned in the text: {entity_name}"`
- 其他: `"Entity mentioned in the text: {entity_name}"`

**关系属性的默认description**:
```python
# 如果关系没有属性，生成默认description
if not filtered_relation_properties:
    filtered_relation_properties['description'] = f"Relation {relation_type} between {entity1} and {entity2}"
```

**默认description格式**:
- `"Relation {relation_type} between {entity1} and {entity2}"`

---

## 优先级

1. **优先使用LLM提取的description**: 如果LLM从文本中提取到了description属性，使用LLM提取的值
2. **补充默认description**: 只有当LLM没有提取到任何属性时，才补充默认description

---

## 日志记录

### LLM提取的description
- 日志级别: `INFO`
- 日志内容: `✅ 提取到实体属性: {entity_name} -> {filtered_properties}`

### 系统补充的默认description
- 日志级别: `WARNING`
- 日志内容: `⚠️ 实体 '{entity_name}' 没有属性，已补充默认description属性`

---

## 示例

### 示例1: LLM提取的description
**文本**: "John Adams was the second President of the United States, serving from 1797 to 1801."

**LLM提取**:
```json
{
  "name": "John Adams",
  "type": "Person",
  "properties": {
    "description": "second President of the United States",
    "occupation": "President"
  }
}
```

**结果**: 使用LLM提取的description，不会补充默认description

---

### 示例2: 系统补充的默认description
**文本**: "John Adams"

**LLM提取**:
```json
{
  "name": "John Adams",
  "type": "Person",
  "properties": {}
}
```

**系统补充**:
```json
{
  "name": "John Adams",
  "type": "Person",
  "properties": {
    "description": "Person mentioned in the text: John Adams"
  }
}
```

**结果**: 使用系统补充的默认description

---

## 总结

Description属性有两个来源：
1. **LLM提取**（优先）: 从文本内容中提取的真实描述信息
2. **系统补充**（保底）: 当LLM没有提取到属性时，自动补充的默认description

这确保了：
- ✅ 优先使用文本中的真实信息
- ✅ 保证每个实体和关系都有至少一个属性（知识图谱基本规则）
- ✅ 默认description提供基本的信息，即使文本中没有详细描述

