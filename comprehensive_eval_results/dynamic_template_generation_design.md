# 动态模板生成设计方案

## 核心理念

**只有少量核心模板，其他模板动态生成**

## 核心模板（必需，不可替代）

### 1. 推理类（2个）
- `reasoning_with_evidence` - 基于证据的推理
- `reasoning_without_evidence` - 无证据的推理

### 2. 分类类（1个）
- `query_type_classification` - 查询类型分类

### 3. 基础类（可选，约3-5个）
- `answer_extraction` - 答案提取（可基于推理模板生成）
- `evidence_generation` - 证据生成（可基于推理模板生成）

**总计：约5-8个核心模板**

## 动态生成策略

### 策略1: 基于核心模板的参数化生成

```python
def generate_prompt_dynamically(template_type: str, **params) -> str:
    """动态生成提示词"""
    if template_type == "fallback_reasoning_with_evidence":
        # 基于 reasoning_with_evidence 生成简化版
        base = get_core_template("reasoning_with_evidence")
        return simplify_template(base, **params)
    
    elif template_type == "answer_validation":
        # 基于推理模板生成验证提示词
        base = get_core_template("reasoning_with_evidence")
        return generate_validation_from_reasoning(base, **params)
    
    # ...
```

### 策略2: 模板组合

```python
def generate_prompt_by_combination(base_template: str, modifiers: List[str]) -> str:
    """通过组合生成提示词"""
    base = get_core_template(base_template)
    
    # 应用修饰符
    for modifier in modifiers:
        if modifier == "simplified":
            base = simplify(base)
        elif modifier == "validation":
            base = add_validation_requirements(base)
        # ...
    
    return base
```

### 策略3: 模板片段组合

```python
# 定义可复用的模板片段
TEMPLATE_FRAGMENTS = {
    "answer_format_requirement": "...",
    "evidence_usage_guideline": "...",
    "reasoning_steps": "...",
}

def generate_prompt_from_fragments(fragments: List[str], **params) -> str:
    """从片段组合生成提示词"""
    content = "\n\n".join([TEMPLATE_FRAGMENTS[f] for f in fragments])
    return content.format(**params)
```

## 实施计划

### 阶段1: 识别核心模板（当前）
- ✅ 已识别：3个核心模板
- 🔄 需要确认：其他5-8个是否必需

### 阶段2: 实现动态生成器
```python
class DynamicTemplateGenerator:
    """动态模板生成器"""
    
    def generate(self, template_name: str, **kwargs) -> str:
        """生成模板"""
        # 1. 检查是否是核心模板
        if self.is_core_template(template_name):
            return self.get_core_template(template_name, **kwargs)
        
        # 2. 检查是否是fallback模板
        if template_name.startswith("fallback_"):
            return self.generate_fallback(template_name, **kwargs)
        
        # 3. 检查是否是组合模板
        if self.is_composite_template(template_name):
            return self.generate_composite(template_name, **kwargs)
        
        # 4. 默认：基于核心模板生成
        return self.generate_from_core(template_name, **kwargs)
    
    def generate_fallback(self, template_name: str, **kwargs) -> str:
        """生成fallback模板"""
        base_name = template_name.replace("fallback_", "")
        base = self.get_core_template(base_name, **kwargs)
        return self.simplify_template(base)
    
    def simplify_template(self, template: str) -> str:
        """简化模板（生成fallback版本）"""
        # 移除详细指导，保留核心要求
        # 缩短长度，保留关键信息
        # ...
```

### 阶段3: 重构PromptEngine
```python
class PromptEngine:
    def generate_prompt(self, template_name: str, **kwargs) -> Optional[str]:
        """生成提示词（支持动态生成）"""
        # 1. 尝试从存储的模板加载
        template = self.templates.get(template_name)
        if template:
            return self._format_template(template, **kwargs)
        
        # 2. 尝试动态生成
        dynamic_generator = DynamicTemplateGenerator(self.templates)
        generated = dynamic_generator.generate(template_name, **kwargs)
        if generated:
            return generated
        
        # 3. 最后的fallback
        return self._get_emergency_fallback(template_name, **kwargs)
```

## 优化效果

### 模板数量
- **当前**: 35个模板
- **优化后**: 5-8个核心模板 + 动态生成
- **减少**: 约77-86%

### 维护成本
- **当前**: 需要维护35个模板
- **优化后**: 只需维护5-8个核心模板 + 生成逻辑
- **降低**: 约80%

### 灵活性
- **当前**: 添加新功能需要添加新模板
- **优化后**: 通过参数化或组合即可生成新模板
- **提升**: 显著提升

## 实施建议

### 短期（1周）
1. 确认核心模板列表（5-8个）
2. 实现基础的动态生成器
3. 将fallback模板改为动态生成

### 中期（2-3周）
1. 实现模板组合功能
2. 实现模板片段系统
3. 重构PromptEngine集成动态生成

### 长期（1个月）
1. 完全移除冗余模板
2. 建立模板使用统计
3. 优化动态生成算法

## 结论

**您的观点完全正确！**

- 只有少量核心模板（5-8个）
- 其他模板通过动态生成
- 大幅减少维护成本
- 提高系统灵活性

这是一个更优雅、更可维护的设计方案。

