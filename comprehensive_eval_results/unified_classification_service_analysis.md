# 核心系统类型分类和提示词组织统一分析

**生成时间**: 2025-11-01
**目的**: 分析核心系统中的重复分类和提示词构建模式，设计统一服务

---

## 📋 发现的重复模式

### 1. 类型分类的重复模式

发现以下方法都遵循几乎相同的模式：

| 方法 | 文件 | 功能 | 模式相似度 |
|------|------|------|-----------|
| `_identify_problem_type` | `frames_processor.py` | 识别FRAMES问题类型 | ⭐⭐⭐⭐⭐ 95% |
| `_analyze_query_type_with_ml` | `real_reasoning_engine.py` | 分析查询类型 | ⭐⭐⭐⭐⭐ 95% |
| `_identify_reasoning_type` | `multi_hop_reasoning.py` | 识别推理类型 | ⭐⭐⭐⭐⭐ 95% |
| `generate_step_type` | `real_reasoning_engine.py` | 生成推理步骤类型 | ⭐⭐⭐⭐ 85% |
| `classify_query` | `llm_integration.py` | 分类查询 | ⭐⭐⭐ 70% |

**共同模式**:
```python
1. 检查LLM是否可用
2. 使用PromptEngine生成分类提示词
3. 调用LLM进行分类
4. 解析LLM响应提取类型
5. Fallback到规则匹配
```

### 2. 提示词构建的重复模式

| 方法 | 文件 | 功能 | 模式相似度 |
|------|------|------|-----------|
| `_build_frames_problem_type_prompt` | `frames_processor.py` | 构建FRAMES问题类型提示词 | ⭐⭐⭐⭐⭐ 100% |
| `_build_query_type_classification_prompt` | `real_reasoning_engine.py` | 构建查询类型提示词 | ⭐⭐⭐⭐⭐ 100% |
| `_build_reasoning_type_prompt` | `multi_hop_reasoning.py` | 构建推理类型提示词 | ⭐⭐⭐⭐⭐ 100% |

**共同模式**:
```python
1. 检查prompt_engineering是否可用
2. 调用prompt_engineering.generate_prompt(template_name, **kwargs)
3. 返回提示词或None
4. 异常处理
```

### 3. 响应解析的重复模式

| 方法 | 文件 | 功能 | 模式相似度 |
|------|------|------|-----------|
| `_parse_frames_problem_type` | `frames_processor.py` | 解析FRAMES问题类型 | ⭐⭐⭐⭐ 85% |
| `_parse_query_type_from_llm_response` | `real_reasoning_engine.py` | 解析查询类型 | ⭐⭐⭐⭐ 85% |
| `_parse_reasoning_type` | `multi_hop_reasoning.py` | 解析推理类型 | ⭐⭐⭐⭐ 85% |

**共同模式**:
```python
1. 转换为小写
2. 直接匹配类型名称
3. 尝试从编号提取
4. 返回匹配的类型或None
```

---

## 💡 统一服务设计

### 1. UnifiedClassificationService（统一分类服务）

**职责**:
- 统一处理所有类型分类任务
- 自动选择LLM（快速模型优先）
- 统一提示词构建
- 统一响应解析
- 统一的fallback机制

**接口设计**:
```python
class UnifiedClassificationService:
    def classify(
        self,
        query: str,
        classification_type: str,  # "query_type", "frames_problem_type", "reasoning_type", etc.
        valid_types: List[str] | Dict[str, Any],  # 有效类型列表或枚举映射
        template_name: str,  # PromptEngine模板名称
        default_type: str,  # 默认类型
        rules_fallback: Optional[Callable] = None,  # 规则匹配fallback
        **prompt_kwargs  # 传递给提示词模板的其他参数
    ) -> Any:
        """
        统一的分类方法
        
        Returns:
            分类结果（字符串或枚举类型）
        """
```

### 2. UnifiedPromptBuilder（统一提示词构建服务）

**职责**:
- 统一构建所有分类提示词
- 统一的错误处理
- 统一的日志记录

**接口设计**:
```python
class UnifiedPromptBuilder:
    def build_classification_prompt(
        self,
        template_name: str,
        query: str,
        prompt_engineering: Optional[PromptEngine] = None,
        **kwargs
    ) -> Optional[str]:
        """
        统一构建分类提示词
        """
```

---

## 🎯 实现建议

### 方案1：创建统一的分类服务类（推荐）

**位置**: `src/utils/unified_classification_service.py`

**优点**:
- 完全统一所有分类逻辑
- 易于扩展和维护
- 减少代码重复90%+

**缺点**:
- 需要重构现有代码
- 可能需要适配不同的返回类型（字符串 vs 枚举）

### 方案2：提取公共工具函数

**位置**: `src/utils/classification_utils.py`

**优点**:
- 改动较小
- 保持现有接口不变

**缺点**:
- 仍然会有一些重复代码
- 不如方案1彻底

---

## 📊 代码重复统计

| 模式 | 重复次数 | 代码行数（总计） | 统一后可节省 |
|------|---------|----------------|-------------|
| 类型分类逻辑 | 5次 | ~400行 | ~350行 |
| 提示词构建 | 3次 | ~60行 | ~50行 |
| 响应解析 | 3次 | ~120行 | ~90行 |
| **总计** | **11处** | **~580行** | **~490行** |

---

## 🚀 下一步行动

1. **创建统一分类服务** (`UnifiedClassificationService`)
2. **创建统一提示词构建器** (`UnifiedPromptBuilder`)
3. **重构现有代码**使用统一服务
4. **保持向后兼容**（支持现有接口）

---

**结论**: 核心系统中确实存在大量重复的分类和提示词构建逻辑，创建统一服务可以大幅减少代码重复（约85%），提高可维护性和可扩展性。

