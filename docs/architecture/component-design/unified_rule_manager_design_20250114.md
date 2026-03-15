# 统一规则管理中心设计 - 2025-01-14

## 一、设计目标

### 1. **统一管理**
- 统一管理所有规则、模式、关键词、阈值
- 提供统一的访问接口
- 支持配置中心集成

### 2. **减少硬编码**
- 移除硬编码的关键词列表
- 移除硬编码的模式定义
- 移除硬编码的阈值

### 3. **增强语义理解**
- 优先使用语义理解
- 硬编码仅作为fallback
- 支持动态学习和优化

### 4. **灵活配置**
- 支持配置文件管理
- 支持运行时动态调整
- 支持配置版本管理

## 二、架构设计

### 核心组件

```
UnifiedRuleManager (统一规则管理中心)
├─ KeywordManager (关键词管理器)
│  ├─ EntityTypeKeywords (实体类型关键词)
│  ├─ QueryTypeKeywords (查询类型关键词)
│  ├─ FilterKeywords (过滤关键词)
│  └─ SemanticKeywords (语义关键词)
│
├─ PatternManager (模式管理器)
│  ├─ AnswerExtractionPatterns (答案提取模式)
│  ├─ ValidationPatterns (验证模式)
│  ├─ EntityPatterns (实体模式)
│  └─ RelationshipPatterns (关系模式)
│
├─ RuleManager (规则管理器)
│  ├─ ValidationRules (验证规则)
│  ├─ TypeInferenceRules (类型推断规则)
│  └─ RelevanceRules (相关性规则)
│
├─ ThresholdManager (阈值管理器)
│  ├─ SimilarityThresholds (相似度阈值)
│  ├─ LengthThresholds (长度阈值)
│  └─ ConfidenceThresholds (置信度阈值)
│
└─ SemanticEnhancer (语义增强器)
   ├─ NERBasedDetection (基于NER的检测)
   ├─ SemanticSimilarity (语义相似度)
   └─ DependencyParsing (依存句法分析)
```

## 三、详细设计

### 1. **UnifiedRuleManager (统一规则管理中心)**

**职责**：
- 统一管理所有规则、模式、关键词、阈值
- 提供统一的访问接口
- 协调各个子管理器

**接口**：
```python
class UnifiedRuleManager:
    def __init__(self, config_center=None, semantic_pipeline=None):
        """初始化统一规则管理中心"""
        self.keyword_manager = KeywordManager(config_center)
        self.pattern_manager = PatternManager(config_center)
        self.rule_manager = RuleManager(config_center)
        self.threshold_manager = ThresholdManager(config_center)
        self.semantic_enhancer = SemanticEnhancer(semantic_pipeline)
    
    def get_keywords(self, category: str, context: Optional[str] = None) -> List[str]:
        """获取关键词列表（优先使用语义理解）"""
        # 1. 优先使用语义理解
        if self.semantic_enhancer:
            semantic_keywords = self.semantic_enhancer.get_semantic_keywords(category, context)
            if semantic_keywords:
                return semantic_keywords
        
        # 2. Fallback到配置中心
        return self.keyword_manager.get_keywords(category)
    
    def match_pattern(self, pattern_type: str, text: str) -> Optional[Match]:
        """匹配模式（优先使用语义理解）"""
        # 1. 优先使用语义理解
        if self.semantic_enhancer:
            semantic_match = self.semantic_enhancer.match_semantic_pattern(pattern_type, text)
            if semantic_match:
                return semantic_match
        
        # 2. Fallback到模式匹配
        return self.pattern_manager.match(pattern_type, text)
    
    def validate(self, rule_type: str, value: Any, context: Optional[Dict] = None) -> bool:
        """验证规则（优先使用语义理解）"""
        # 1. 优先使用语义理解
        if self.semantic_enhancer:
            semantic_result = self.semantic_enhancer.validate_semantic(rule_type, value, context)
            if semantic_result is not None:
                return semantic_result
        
        # 2. Fallback到规则验证
        return self.rule_manager.validate(rule_type, value, context)
    
    def get_threshold(self, threshold_type: str, context: Optional[str] = None) -> float:
        """获取阈值"""
        return self.threshold_manager.get_threshold(threshold_type, context)
```

### 2. **KeywordManager (关键词管理器)**

**职责**：
- 管理所有关键词列表
- 支持从配置中心读取
- 支持动态更新

**接口**：
```python
class KeywordManager:
    def __init__(self, config_center=None):
        self.config_center = config_center
        self._cache = {}
    
    def get_keywords(self, category: str) -> List[str]:
        """获取关键词列表"""
        # 1. 检查缓存
        if category in self._cache:
            return self._cache[category]
        
        # 2. 从配置中心读取
        if self.config_center:
            keywords = self.config_center.get_config_value('keywords', category, None)
            if keywords:
                self._cache[category] = keywords
                return keywords
        
        # 3. 返回空列表（不再硬编码默认值）
        return []
    
    def add_keywords(self, category: str, keywords: List[str]):
        """添加关键词"""
        existing = self.get_keywords(category)
        self._cache[category] = list(set(existing + keywords))
        # 更新配置中心
        if self.config_center:
            self.config_center.set_config_value('keywords', category, self._cache[category])
```

### 3. **PatternManager (模式管理器)**

**职责**：
- 管理所有正则表达式模式
- 支持模式组合和扩展
- 支持模式优化

**接口**：
```python
class PatternManager:
    def __init__(self, config_center=None):
        self.config_center = config_center
        self._patterns = {}
        self._load_patterns()
    
    def _load_patterns(self):
        """加载模式定义"""
        # 从配置中心加载
        if self.config_center:
            patterns = self.config_center.get_config_value('patterns', None, {})
            self._patterns.update(patterns)
    
    def match(self, pattern_type: str, text: str) -> Optional[Match]:
        """匹配模式"""
        patterns = self._patterns.get(pattern_type, [])
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match
        return None
    
    def add_pattern(self, pattern_type: str, pattern: str):
        """添加模式"""
        if pattern_type not in self._patterns:
            self._patterns[pattern_type] = []
        self._patterns[pattern_type].append(pattern)
        # 更新配置中心
        if self.config_center:
            self.config_center.set_config_value('patterns', pattern_type, self._patterns[pattern_type])
```

### 4. **RuleManager (规则管理器)**

**职责**：
- 管理所有验证规则
- 支持规则组合和扩展
- 支持规则优化

**接口**：
```python
class RuleManager:
    def __init__(self, config_center=None):
        self.config_center = config_center
        self._rules = {}
        self._load_rules()
    
    def validate(self, rule_type: str, value: Any, context: Optional[Dict] = None) -> bool:
        """验证规则"""
        rule = self._rules.get(rule_type)
        if not rule:
            return True  # 默认通过
        
        return rule(value, context)
    
    def add_rule(self, rule_type: str, rule: Callable):
        """添加规则"""
        self._rules[rule_type] = rule
```

### 5. **ThresholdManager (阈值管理器)**

**职责**：
- 管理所有阈值
- 支持上下文相关的阈值
- 支持动态调整

**接口**：
```python
class ThresholdManager:
    def __init__(self, config_center=None):
        self.config_center = config_center
        self._thresholds = {}
        self._load_thresholds()
    
    def get_threshold(self, threshold_type: str, context: Optional[str] = None) -> float:
        """获取阈值"""
        # 支持上下文相关的阈值
        key = f"{threshold_type}:{context}" if context else threshold_type
        if key in self._thresholds:
            return self._thresholds[key]
        
        # Fallback到默认阈值
        return self._thresholds.get(threshold_type, 0.5)
    
    def set_threshold(self, threshold_type: str, value: float, context: Optional[str] = None):
        """设置阈值"""
        key = f"{threshold_type}:{context}" if context else threshold_type
        self._thresholds[key] = value
        # 更新配置中心
        if self.config_center:
            self.config_center.set_config_value('thresholds', key, value)
```

### 6. **SemanticEnhancer (语义增强器)**

**职责**：
- 提供基于语义理解的功能
- 优先使用语义理解
- 支持fallback到规则/模式

**接口**：
```python
class SemanticEnhancer:
    def __init__(self, semantic_pipeline=None):
        self.pipeline = semantic_pipeline or get_semantic_understanding_pipeline()
    
    def get_semantic_keywords(self, category: str, context: Optional[str] = None) -> Optional[List[str]]:
        """使用语义理解获取关键词"""
        if not self.pipeline or not context:
            return None
        
        # 使用NER提取实体
        entities = self.pipeline.extract_entities_intelligent(context)
        if entities:
            return [e['text'] for e in entities if e.get('label') == category.upper()]
        return None
    
    def match_semantic_pattern(self, pattern_type: str, text: str) -> Optional[Match]:
        """使用语义理解匹配模式"""
        if not self.pipeline:
            return None
        
        # 根据模式类型使用不同的语义理解方法
        if pattern_type == 'person':
            entities = self.pipeline.extract_entities_intelligent(text)
            person_entities = [e for e in entities if e.get('label') == 'PERSON']
            if person_entities:
                return Match(person_entities[0]['text'])
        
        return None
    
    def validate_semantic(self, rule_type: str, value: Any, context: Optional[Dict] = None) -> Optional[bool]:
        """使用语义理解验证"""
        if not self.pipeline or not context:
            return None
        
        # 根据规则类型使用不同的语义理解方法
        if rule_type == 'relevance':
            query = context.get('query', '')
            evidence = context.get('evidence', '')
            similarity = self.pipeline.calculate_semantic_similarity(query, evidence)
            threshold = context.get('threshold', 0.3)
            return similarity >= threshold
        
        return None
```

## 四、使用示例

### 示例1：获取关键词

```python
# 之前：硬编码
non_person_keywords = ['army', 'war', 'government', ...]
if any(keyword in answer_lower for keyword in non_person_keywords):
    return False

# 改进：使用统一规则管理中心
rule_manager = UnifiedRuleManager()
keywords = rule_manager.get_keywords('non_person_indicators', context=answer)
if keywords and any(keyword in answer_lower for keyword in keywords):
    return False

# 更优：使用语义理解
entities = rule_manager.semantic_enhancer.pipeline.extract_entities_intelligent(answer)
if entities and any(e.get('label') in ['ORG', 'GPE'] for e in entities):
    return False
```

### 示例2：匹配模式

```python
# 之前：硬编码
final_answer_patterns = [
    r'Final Answer:\s*(.+?)(?:\n|$)',
    r'最终答案[：:]\s*(.+?)(?:\n|$)',
]
for pattern in final_answer_patterns:
    match = re.search(pattern, text)
    if match:
        return match.group(1)

# 改进：使用统一规则管理中心
rule_manager = UnifiedRuleManager()
match = rule_manager.match_pattern('final_answer', text)
if match:
    return match.group(1)
```

### 示例3：验证规则

```python
# 之前：硬编码
if len(answer) < 2 or len(answer) > 100:
    return False

# 改进：使用统一规则管理中心
rule_manager = UnifiedRuleManager()
if not rule_manager.validate('answer_length', answer, {'min': 2, 'max': 100}):
    return False
```

### 示例4：获取阈值

```python
# 之前：硬编码
if similarity < 0.3:
    return False

# 改进：使用统一规则管理中心
rule_manager = UnifiedRuleManager()
threshold = rule_manager.get_threshold('semantic_similarity', context='answer_validation')
if similarity < threshold:
    return False
```

## 五、迁移计划

### Phase 1: 创建统一规则管理中心（1-2天）

1. 创建 `UnifiedRuleManager` 类
2. 创建各个子管理器
3. 实现基础功能

### Phase 2: 迁移关键词列表（2-3天）

1. 将所有关键词列表迁移到 `KeywordManager`
2. 更新 `answer_extractor.py` 使用 `UnifiedRuleManager`
3. 移除硬编码的默认值

### Phase 3: 迁移模式定义（2-3天）

1. 将所有模式定义迁移到 `PatternManager`
2. 更新所有使用模式的地方
3. 统一模式管理

### Phase 4: 迁移验证规则（2-3天）

1. 将所有验证规则迁移到 `RuleManager`
2. 更新所有验证逻辑
3. 统一规则管理

### Phase 5: 增强语义理解（3-5天）

1. 实现 `SemanticEnhancer`
2. 在所有地方优先使用语义理解
3. 硬编码仅作为fallback

## 六、配置管理

### 配置文件结构

```yaml
# config/rules.yaml
keywords:
  basic_filter:
    - "United States"
    - "First Lady"
    - "President"
  
  place:
    - "United States"
    - "New York"
    - "America"
  
  organization:
    - "Union Army"
    - "Confederate Army"
    - "Civil War"

patterns:
  final_answer:
    - "Final Answer:\\s*(.+?)(?:\\n|$)"
    - "最终答案[：:]\\s*(.+?)(?:\\n|$)"
  
  date:
    - "\\b(\\d{4})\\b"
    - "\\b(\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4})\\b"

rules:
  answer_length:
    min: 2
    max: 100
  
  alnum_ratio:
    min: 0.7

thresholds:
  semantic_similarity:
    default: 0.3
    answer_validation: 0.2
    evidence_validation: 0.15
  
  confidence:
    default: 0.5
    high: 0.8
```

## 七、优势

### 1. **统一管理**
- 所有规则、模式、关键词、阈值统一管理
- 易于维护和扩展

### 2. **减少硬编码**
- 大幅减少硬编码
- 提高代码可维护性

### 3. **增强语义理解**
- 优先使用语义理解
- 提高系统准确性

### 4. **灵活配置**
- 支持动态配置
- 易于调整和优化

### 5. **向后兼容**
- 支持逐步迁移
- 不破坏现有功能

## 八、总结

统一规则管理中心将：
1. 统一管理所有规则、模式、关键词、阈值
2. 优先使用语义理解，减少硬编码依赖
3. 支持灵活配置，易于调整和优化
4. 提高代码可维护性和可扩展性

这将大大改善系统的架构，减少硬编码，提高系统的通用性和可维护性。

