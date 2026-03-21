# Skills 系统集成方案

## 概述

RANGEN 的 Skills 系统有以下功能模块，但部分模块未集成到中台：

| 模块 | 功能 | 状态 |
|------|------|------|
| `skill_trigger.py` | 基础关键词触发 | ✅ 已使用 |
| `learning_skill_trigger.py` | 学习型触发优化 | ❌ 未集成 |
| `tool_to_skill_map.py` | Tool → Skill 映射 | ❌ 未集成 |

---

## 1. LearningSkillTrigger 集成方案

### 问题分析

```
当前架构:
skill_trigger.py (基础触发器)
    ↓ (不使用)
learning_skill_trigger.py (学习型触发器)
    ↓ (未使用)
skill_trigger_learner.py (学习器) ← src/orchestration/self_learning/
```

### 集成方案

**方案 A: 在 skill_trigger.py 中集成学习型功能**

```python
# skill_trigger.py 修改
class SkillTrigger:
    def __init__(self, registry=None, enable_learning: bool = True):
        self.registry = registry or get_enhanced_skill_registry()
        self._build_trigger_index()
        
        # 集成学习功能
        self.enable_learning = enable_learning
        if enable_learning:
            try:
                from src.orchestration.self_learning import get_skill_trigger_learner
                self.skill_learner = get_skill_trigger_learner()
            except ImportError:
                self.enable_learning = False
    
    def trigger(self, user_input: str) -> SkillTriggerResult:
        # 基础触发
        base_result = self._trigger_by_keywords(user_input)
        
        # 如果启用了学习，增强触发
        if self.enable_learning and self.skill_learner:
            learned_skills = self._trigger_by_learning(user_input)
            # 合并结果
            return self._merge_results(base_result, learned_skills)
        
        return base_result
```

**方案 B: 作为可选组件保持分离**

```python
# skill_trigger.py 保持简单
# 外部使用时可以选择 LearningSkillTrigger
from src.skills.runtime.learning_skill_trigger import LearningSkillTrigger

trigger = LearningSkillTrigger()  # 学习型触发
```

### 推荐方案

**方案 A** - 在 skill_trigger.py 中添加可选的学习增强：

1. 默认启用学习功能
2. 使用 `enable_learning` 参数控制
3. 保持向后兼容

---

## 2. ToolToSkillMap 集成方案

### 问题分析

```
当前架构:
HybridToolExecutor.execute(tool_name, parameters)
    ↓ (不使用映射)
直接执行 tool_name

缺失:
ToolToSkillMap 定义的映射表没有生效
```

### 集成方案

**在 HybridToolExecutor 执行时使用映射**

```python
# hybrid_tool_executor.py 修改
class HybridToolExecutor:
    def __init__(self, ...):
        # ... 现有初始化
        # 添加 Tool → Skill 映射
        try:
            from src.skills.runtime.tool_to_skill_map import get_skill_name
            self.tool_to_skill_mapper = get_skill_name
        except ImportError:
            self.tool_to_skill_mapper = None
    
    async def execute(self, tool_name: str, parameters: Dict, ...):
        # 如果启用了映射，转换工具名
        if self.tool_to_skill_mapper:
            mapped_tool = self.tool_to_skill_mapper(tool_name)
            logger.debug(f"Tool mapped: {tool_name} → {mapped_tool}")
        
        # 继续执行...
```

### 映射表内容

```python
# tool_to_skill_map.py
TOOL_TO_SKILL_MAP = {
    "calculator": "calculator-skill",
    "reasoning": "reasoning-chain",
    "search": "web-search",
    "rag": "rag-retrieval",
    "answer_generation": "answer-generation",
    # ...
}
```

---

## 3. 集成优先级

| 优先级 | 任务 | 工作量 |
|--------|------|--------|
| P1 | 集成 ToolToSkillMap 到 HybridToolExecutor | 小 |
| P2 | 集成 LearningSkillTrigger 到 SkillTrigger | 中 |
| P3 | 测试完整的学习-触发-执行流程 | 大 |

---

## 4. 注意事项

1. **向后兼容**: 集成不能破坏现有功能
2. **可选性**: 学习功能应该是可选的（默认启用）
3. **日志**: 添加足够的日志便于调试
4. **错误处理**: 映射失败时应该 fallback 到原始工具名
