# 模板统一架构实施方案（方案A）

生成时间: 2025-12-04

## 一、方案A的优势

### 1.1 为什么方案A更好

**方案A（统一架构）的优势**：
1. ✅ **根本性解决**：从架构层面解决所有问题，而不是打补丁
2. ✅ **长期可维护**：建立清晰的架构，便于后续扩展
3. ✅ **系统化**：所有模板遵循统一规范，减少不一致
4. ✅ **可扩展**：新模板可以轻松集成到统一架构中
5. ✅ **可测试**：架构清晰，便于测试和验证

**方案C（代码层面处理）的问题**：
1. ⚠️ **治标不治本**：只是转换格式，没有解决根本问题
2. ⚠️ **维护成本高**：需要在多个地方添加转换逻辑
3. ⚠️ **容易遗漏**：新模板可能忘记添加转换逻辑
4. ⚠️ **技术债务**：长期积累会导致系统复杂

### 1.2 方案A的可行性

**完全可以实施！** 原因：
1. ✅ 模板系统已经模块化（`prompt_generator.py`）
2. ✅ 有统一的模板加载机制（`prompt_engineering.generate_prompt()`）
3. ✅ 可以逐步迁移，不影响现有功能
4. ✅ 可以保留旧模板作为fallback

## 二、方案A实施计划

### 2.1 核心架构设计

```python
# 统一架构核心组件

class UnifiedTemplateArchitecture:
    """统一模板架构"""
    
    def __init__(self):
        self.template_selector = TemplateSelector()
        self.evidence_assessor = EvidenceQualityAssessor()
        self.confidence_calibrator = ConfidenceCalibrator()
        self.output_formatter = UnifiedOutputFormatter()
    
    def process_query(self, query, context, evidence):
        # Phase 1: 问题分析与路由
        analysis = self.analyze_query(query, context)
        
        # Phase 2: 证据质量评估
        if evidence:
            evidence_quality = self.evidence_assessor.assess(evidence, query)
        else:
            evidence_quality = None
        
        # Phase 3: 模板选择
        template = self.template_selector.select(
            query_type=analysis['type'],
            complexity=analysis['complexity'],
            evidence_quality=evidence_quality
        )
        
        # Phase 4: 生成提示词
        prompt = self.generate_prompt(template, query, context, evidence)
        
        # Phase 5: 处理响应
        response = self.call_llm(prompt)
        
        # Phase 6: 统一格式化输出
        formatted_output = self.output_formatter.format(
            response, 
            template_used=template.name,
            evidence_quality=evidence_quality
        )
        
        return formatted_output
```

### 2.2 实施步骤

#### 步骤1：创建统一输出格式器

**文件**：`src/core/reasoning/unified_output_formatter.py`

**功能**：
- 统一处理所有模板的输出格式
- 转换置信度格式
- 提取 final_answer
- 添加 metadata

#### 步骤2：创建模板选择器

**文件**：`src/core/reasoning/template_selector.py`

**功能**：
- 根据问题类型、复杂度、证据质量选择模板
- 实现 fallback 链
- 记录选择逻辑

#### 步骤3：创建证据质量评估器

**文件**：`src/core/reasoning/evidence_quality_assessor.py`

**功能**：
- 评估证据相关性
- 检查证据一致性
- 评估证据完整性
- 返回质量评分

#### 步骤4：创建置信度校准器

**文件**：`src/core/reasoning/confidence_calibrator.py`

**功能**：
- 统一置信度格式（high/medium/low ↔ 0.0-1.0）
- 校准置信度评分
- 跨模板置信度比较

#### 步骤5：更新现有模板

**策略**：
- 保持现有模板不变（向后兼容）
- 添加新字段（metadata, evidence_quality等）
- 逐步迁移

## 三、实施优先级

### 第一阶段（立即实施，1-2天）

1. ✅ 创建统一输出格式器
2. ✅ 创建模板选择器（基础版本）
3. ✅ 更新 `prompt_generator.py` 使用新架构

### 第二阶段（核心功能，2-3天）

4. ✅ 创建证据质量评估器
5. ✅ 创建置信度校准器
6. ✅ 实现 fallback 链

### 第三阶段（优化完善，2-3天）

7. ✅ 更新所有模板使用统一格式
8. ✅ 添加监控和日志
9. ✅ 测试和验证

## 四、风险控制

### 4.1 向后兼容

- ✅ 保留所有现有模板
- ✅ 新架构作为可选功能
- ✅ 可以逐步迁移

### 4.2 渐进式实施

- ✅ 先实现核心功能
- ✅ 测试验证后再扩展
- ✅ 保留 rollback 能力

### 4.3 测试策略

- ✅ 单元测试每个组件
- ✅ 集成测试完整流程
- ✅ 对比测试新旧系统

## 五、预期效果

### 5.1 质量改进指标

| 指标 | 当前 | 目标 | 改进方法 |
|------|------|------|----------|
| 模板间一致性 | 60% | 95% | 统一输出格式 |
| 置信度可比性 | 低 | 高 | 统一为0-1数值 |
| 故障恢复率 | 20% | 80% | 添加fallback链 |
| 证据利用率 | 90%但可能误用 | 90%且智能 | 添加质量评估 |
| 维护复杂度 | 高 | 中 | 统一架构 |

### 5.2 长期收益

1. ✅ **可维护性提升**：架构清晰，易于理解和修改
2. ✅ **可扩展性提升**：新功能可以轻松集成
3. ✅ **可靠性提升**：统一的错误处理和fallback机制
4. ✅ **性能提升**：智能模板选择，减少无效调用

---

**结论**：方案A不仅可行，而且是**最优方案**！我们应该立即开始实施。

