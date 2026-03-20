# Agent 架构优化建议

> 创建日期: 2026-03-20

---

## 当前问题

### 1. 两个 IAgent 接口冲突

| 文件 | IAgent 定义 |
|------|------------|
| `src/interfaces/agent.py` | `execute(inputs, context) -> AgentResult` |
| `src/interfaces/core_interfaces.py` | `process(query, context) -> Dict` |

### 2. Agent 继承体系混乱

```
BaseAgent (base_agent.py)
├── ExpertAgent (继承 BaseAgent)
│   ├── AgentCoordinator
│   ├── MultiAgentCoordinator
│   └── ... 50+ 子类
├── ReActAgent (继承 BaseAgent)
│   ├── SelfLearningReActAgent
│   └── EnhancedReActAgent
└── IAgent (接口)
    ├── CitationAgent
    ├── ValidationAgent
    ├── ReasoningAgent
    └── ... 10+ 实现
```

### 3. 84 个 Agent 类

这使得维护和理解变得困难。

---

## 优化建议

### 方案 A: 统一接口（推荐）

```python
# 统一的 IAgent 接口
class IAgent(ABC):
    @abstractmethod
    async def execute(self, query: str, context: Optional[Dict] = None) -> AgentResult:
        """执行任务"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """获取能力列表"""
        pass
```

### 方案 B: 保持现状，文档化

记录当前架构，允许渐进式重构。

---

## 推荐行动计划

| 阶段 | 任务 | 优先级 |
|------|------|--------|
| P0 | 创建统一的 IAgent 接口 | 高 |
| P0 | 更新所有 IAgent 实现 | 高 |
| P1 | 文档化 Agent 继承体系 | 中 |
| P2 | 合并重复的基类 | 低 |

---

## 当前状态

由于 84 个 Agent 类的高度复杂性，建议：
1. **不要进行破坏性重构**
2. **文档化当前架构**
3. **新 Agent 使用统一接口**

---

## 已采取的行动

1. ✅ BaseAgent 遵循三大原则
2. ✅ AgentBuilder 建造者模式
3. ✅ AgentFactory 工厂模式
