# 硬编码类型判断移除总结

**改进时间**: 2025-11-09  
**问题**: `_get_dynamic_similarity_threshold`方法中仍有硬编码的查询类型判断

## 🔍 问题分析

### 原有问题
```python
# ❌ 硬编码类型判断（不可扩展）
if query_type_lower in ['name', 'location', 'person', 'country']:
    threshold = min(0.50, base_threshold + 0.05)
    return threshold

if query_type_lower in ['numerical', 'ranking', 'mathematical', 'number']:
    threshold = max(0.30, base_threshold - 0.10)
    return threshold
```

**问题**:
- 使用固定的类型列表（`['name', 'location', 'person', 'country']`）
- 新增查询类型需要修改代码
- 无法灵活适应新的查询特征

## 🔧 重构方案

### 新方案：基于查询特征动态调整（可扩展）

#### 策略1: 从配置中心获取阈值调整规则（优先）
```python
# ✅ 从配置中心获取规则（可扩展）
adjustment_rules = config_center.get_config_value(
    'similarity_threshold', 'adjustment_rules', {}
)
# 格式：{"person_name": 0.05, "location": 0.05, "numerical": -0.10, ...}
```

#### 策略2: 基于查询特征判断（而非固定类型列表）
```python
# ✅ 检测查询特征（而非固定类型）
has_person_name_feature = self._has_person_name_feature(query)
has_location_feature = self._has_location_feature(query)
has_numerical_feature = self._has_numerical_feature(query)

# 基于特征调整阈值（而非固定类型）
if has_person_name_feature or has_location_feature:
    threshold = min(0.50, base_threshold + 0.05)
    return threshold
```

## 📝 新增方法

### 1. `_get_threshold_adjustment_from_config`
- **功能**: 从配置中心获取阈值调整规则
- **可扩展性**: 通过配置中心动态配置，无需修改代码
- **格式**: `{"person_name": 0.05, "location": 0.05, "numerical": -0.10, ...}`

### 2. `_has_person_name_feature`
- **功能**: 检测查询是否包含人名特征
- **方法**: 
  - 使用正则表达式检测人名格式（如 "John Smith"）
  - 从配置中心获取人名关键词
- **可扩展性**: 通过配置中心添加新的人名关键词，无需修改代码

### 3. `_has_location_feature`
- **功能**: 检测查询是否包含地名特征
- **方法**:
  - 使用正则表达式检测地名格式（如 "France", "New York"）
  - 从配置中心获取地名关键词
- **可扩展性**: 通过配置中心添加新的地名关键词，无需修改代码

### 4. `_has_numerical_feature`
- **功能**: 检测查询是否包含数字特征
- **方法**:
  - 检测查询中是否包含数字
  - 检测数值关键词（how many, count, number, etc.）
  - 从配置中心获取数值关键词
- **可扩展性**: 通过配置中心添加新的数值关键词，无需修改代码

## 🎯 优势

### 1. 可扩展性 ✅
- **配置驱动**: 通过配置中心动态配置，无需修改代码
- **特征驱动**: 基于查询特征（而非固定类型）判断
- **灵活适应**: 可以轻松添加新的查询特征

### 2. 可维护性 ✅
- **集中配置**: 所有阈值调整规则集中在配置中心
- **易于调试**: 可以轻松查看和修改配置
- **减少硬编码**: 消除了固定类型列表

### 3. 智能性 ✅
- **特征检测**: 基于查询内容特征（而非类型标签）判断
- **多源支持**: 支持正则表达式和配置中心关键词
- **灵活匹配**: 可以处理各种查询格式

## 📊 对比

### 改进前
```python
# ❌ 硬编码类型列表
if query_type_lower in ['name', 'location', 'person', 'country']:
    # 固定处理
```

**问题**:
- 新增类型需要修改代码
- 无法灵活适应新特征
- 维护成本高

### 改进后
```python
# ✅ 基于特征检测
has_person_name_feature = self._has_person_name_feature(query)
if has_person_name_feature:
    # 动态处理
```

**优势**:
- 新增特征只需配置，无需修改代码
- 灵活适应各种查询格式
- 维护成本低

## ✅ 完成状态

- ✅ 移除硬编码类型判断
- ✅ 实现基于特征检测的动态阈值调整
- ✅ 实现配置中心驱动的阈值调整规则
- ✅ 新增特征检测方法（人名、地名、数字）
- ✅ 支持从配置中心获取关键词

## 🎯 使用示例

### 配置中心配置示例
```json
{
  "similarity_threshold": {
    "adjustment_rules": {
      "person_name": 0.05,
      "location": 0.05,
      "numerical": -0.10,
      "ranking": -0.10
    }
  },
  "query_features": {
    "person_keywords": ["who", "person", "name"],
    "location_keywords": ["where", "country", "city", "location"],
    "numerical_keywords": ["how many", "count", "number", "amount"]
  }
}
```

### 代码使用
```python
# 自动检测查询特征并调整阈值
threshold = self._get_dynamic_similarity_threshold(query_type, query)
# 如果查询包含人名特征，自动提高阈值
# 如果查询包含数字特征，自动降低阈值
```

## 📋 后续优化建议

1. **LLM驱动的特征检测**（可选）
   - 使用LLM检测查询特征（更准确）
   - 作为特征检测的补充

2. **学习机制**（可选）
   - 根据历史查询和结果学习最佳阈值
   - 自适应调整阈值规则

3. **特征组合**（可选）
   - 支持多个特征组合（如"人名+地点"）
   - 更精细的阈值调整

