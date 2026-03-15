# 知识图谱质量分析报告

**分析时间**: 2025-11-15  
**数据规模**: 10704个实体，7332条关系

---

## 📊 总体评估

### ✅ 正常指标
1. **实体完整性**：
   - 实体总数：10704个
   - 无空名称实体：✅
   - 无重复名称实体：✅
   - 实体类型分布合理：Person (55.4%), Date (14.3%), Location (12.0%) 等

2. **关系完整性**：
   - 关系总数：7332条
   - 无缺失实体引用：✅（所有关系都正确关联到实体）
   - 无重复关系：✅
   - 关系类型分布合理：related_to (28.0%), son_of (27.9%) 等

3. **图谱连通性**：
   - 无孤立实体：✅（100%实体都连通）
   - 平均度：1.37（每个实体平均连接1.37条关系）

---

## ⚠️ 发现的问题

### 🔴 问题1：实体属性完全缺失（严重）

**现象**：
- **有属性的实体：0 (0.0%)**
- **无属性的实体：10704 (100.0%)**

**影响**：
- 实体只有名称和类型，缺少描述、出生日期、职业、国籍等关键属性
- 限制了知识图谱的查询能力和信息丰富度
- 无法支持基于属性的查询（如"查找所有出生在法国的Person"）

**可能原因**：
1. **LLM提取时未提取属性**：检查 `_extract_entities_and_relations_with_llm_single` 的prompt，可能只要求提取实体名称和类型，没有要求提取属性
2. **属性传递丢失**：虽然 `build_from_structured_data` 尝试从 `item.get('entity1_properties')` 获取属性，但如果提取阶段没有生成属性，这里就是 `None`
3. **属性格式不匹配**：LLM可能提取了属性，但格式不符合预期，导致被忽略

---

### 🔴 问题2：关系属性完全缺失（严重）

**现象**：
- **有属性的关系：0 (0.0%)**
- **无属性的关系：7332 (100.0%)**

**影响**：
- 关系只有类型，缺少时间、地点、置信度来源等元数据
- 无法支持时间查询（如"查找1990-2000年期间的关系"）
- 无法追踪关系来源和置信度依据

**可能原因**：
与实体属性缺失类似，LLM提取时可能没有提取关系属性。

---

### 🟡 问题3：自环关系过多（中等）

**现象**：
- **自环关系：1063条**（实体指向自己）
- 占总关系数的 **14.5%**

**影响**：
- 自环关系通常没有实际意义（如"Person related_to Person"）
- 可能表示实体提取或关系提取的误判
- 浪费存储空间和查询资源

**可能原因**：
1. **实体名称重复**：同一实体被提取为两个不同的实体，然后建立了自环关系
2. **关系提取错误**：LLM错误地将实体与自身建立了关系
3. **实体规范化不足**：没有对实体名称进行规范化（如"John Smith" vs "John A. Smith"）

---

### 🟡 问题4：图谱碎片化（中等）

**现象**：
- **连通分量数：4514个**
- **最大连通分量大小：1478个实体**
- 平均每个连通分量只有 **2.37个实体**

**影响**：
- 图谱被分割成大量小片段，连通性较差
- 无法进行长距离的图遍历查询
- 限制了知识图谱的推理能力

**可能原因**：
1. **关系提取不充分**：只提取了直接关系，没有提取间接关系
2. **实体链接不足**：同一实体的不同表述没有被正确链接
3. **关系类型限制**：只提取了特定类型的关系，忽略了其他类型的关系

---

## 🔍 根本原因分析

### 核心问题：属性提取缺失

**检查点1：LLM提取Prompt**

查看 `_extract_entities_and_relations_with_llm_single` 方法中的prompt：

```python
prompt = f"""Extract entities and relations from the following knowledge entry content.
...
Please analyze the knowledge entry content and extract entities and relations in JSON format:
{{
  "entities": [
    {{"name": "entity_name", "type": "Person|Location|Organization|Event|Other"}},
    ...
  ],
  "relations": [
    {{"entity1": "entity1_name", "entity2": "entity2_name", "relation": "relation_type"}},
    ...
  ]
}}
```

**问题**：
- ❌ 实体JSON格式中**没有要求提取属性**（如 `description`, `birth_date`, `nationality` 等）
- ❌ 关系JSON格式中**没有要求提取属性**（如 `date`, `location`, `confidence_source` 等）

**结论**：LLM提取时根本没有要求提取属性，所以所有实体和关系都没有属性。

---

## 🎯 解决方案

### 方案1：增强LLM提取Prompt（推荐）

**修改 `_extract_entities_and_relations_with_llm_single` 方法**：

```python
prompt = f"""Extract entities and relations from the following knowledge entry content.

Knowledge Entry Content:
{prompt_text}

Please analyze the knowledge entry content and extract entities and relations in JSON format:
{{
  "entities": [
    {{
      "name": "entity_name",
      "type": "Person|Location|Organization|Event|Date|Work|Other",
      "properties": {{
        "description": "brief description if available",
        "birth_date": "birth date if Person",
        "death_date": "death date if Person",
        "nationality": "nationality if Person",
        "location": "location if Location",
        "founded_date": "founded date if Organization",
        "date": "date if Date or Event",
        "other": "any other relevant properties"
      }}
    }},
    ...
  ],
  "relations": [
    {{
      "entity1": "entity1_name",
      "entity2": "entity2_name",
      "relation": "relation_type",
      "properties": {{
        "date": "date of the relation if available",
        "location": "location of the relation if available",
        "description": "additional context if available"
      }}
    }},
    ...
  ]
}}
```

**优点**：
- 直接解决属性缺失问题
- 不需要修改其他代码逻辑
- 向后兼容（如果LLM不返回属性，现有代码也能正常工作）

---

### 方案2：减少自环关系

**在 `build_from_structured_data` 中添加检查**：

```python
# 在创建关系前检查
if entity1_id == entity2_id:
    logger.debug(f"跳过自环关系: {entity1_name} -> {entity2_name}")
    continue
```

**优点**：
- 简单直接
- 立即减少无效关系

---

### 方案3：实体规范化

**在实体创建前进行名称规范化**：
- 统一大小写
- 移除多余空格
- 处理缩写（如 "John A. Smith" vs "John Smith"）

**优点**：
- 减少重复实体
- 提高实体链接准确性

---

## 📋 优先级建议

1. **🔴 高优先级**：修复属性提取（方案1）
   - 影响最大，直接关系到知识图谱的信息丰富度
   - 实施简单，只需修改prompt

2. **🟡 中优先级**：减少自环关系（方案2）
   - 影响中等，主要是数据质量
   - 实施简单，只需添加检查

3. **🟡 中优先级**：实体规范化（方案3）
   - 影响中等，提高数据质量
   - 实施较复杂，需要设计规范化规则

4. **🟢 低优先级**：图谱连通性优化
   - 影响较小，主要是查询性能
   - 需要更深入的关系提取策略

---

## 📊 预期改进效果

### 修复属性提取后：
- **实体属性覆盖率**：预计从 0% 提升到 **60-80%**
- **关系属性覆盖率**：预计从 0% 提升到 **30-50%**
- **知识图谱信息丰富度**：显著提升

### 减少自环关系后：
- **自环关系数量**：预计从 1063 减少到 **<100**
- **数据质量**：显著提升

---

*分析时间: 2025-11-15*

