# RANGEN 状态定义指南

> 统一状态定义，避免冗余和混乱

---

## 状态定义一览

| 状态 | 文件 | 字段数 | 用途 | 状态 |
|------|------|--------|------|------|
| **AgentState** | execution_coordinator.py | 10 | 生产核心 | ✅ 推荐 |
| ProductionState | production_workflow.py | ~30 | 备用 | 🔶 |
| ReActState | workflows/react_workflow.py | ~15 | ReAct专用 | 🔶 |
| ReasoningState | reasoning/... | ~20 | 推理专用 | 🔶 |
| ReviewDecisionState | review_coordinator.py | ~10 | 评审专用 | 🔶 |
| RANGENState | rangen_state.py | ~50 | 全局状态 | ⚠️ 局部 |

---

## 使用原则

### 1. 默认使用 AgentState

**所有新开发的 Workflow 必须使用 AgentState 或其扩展版本。**

```python
from src.core.execution_coordinator import AgentState

# 扩展 AgentState
class ExtendedAgentState(AgentState, total=False):
    additional_field: str
```

### 2. 专用场景使用专用状态

| 场景 | 推荐状态 |
|------|----------|
| 标准执行流程 | AgentState |
| ReAct 推理循环 | ReActState |
| 复杂推理链 | ReasoningState |
| 代码评审 | ReviewDecisionState |

### 3. 禁止新增状态

- ❌ 禁止创建新的 TypedDict 状态类
- ✅ 如需扩展，继承 AgentState

---

## AgentState 定义

```python
class AgentState(TypedDict):
    query: str                    # 用户查询
    context: Dict[str, Any]        # 上下文
    route: str                     # 路由路径
    steps: Annotated[list, operator.add]  # 执行步骤
    final_answer: str             # 最终答案
    error: str                    # 错误信息
    quality_score: float          # 质量分数
    quality_passed: bool          # 质量是否通过
    quality_feedback: str         # 质量反馈
    retry_count: int              # 重试次数
```

---

## 扩展示例

### 场景：需要添加证据字段

```python
class AgentWithEvidence(AgentState, total=False):
    """扩展 AgentState 添加证据支持"""
    evidence: List[Dict[str, Any]]  # 检索到的证据
    citations: List[Citation]        # 引用
```

---

## 清理记录

| 日期 | 操作 |
|------|------|
| 2026-03-16 | 归档 unified_state.py (ExtendedAgentState) - 未使用 |
| 2026-03-16 | 创建本指南 |

---

## 附录：已归档状态

- `unified_state.py` → ExtendedAgentState (已归档，未使用)
