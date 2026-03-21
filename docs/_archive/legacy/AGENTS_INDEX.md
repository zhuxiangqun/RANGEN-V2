# RANGEN Agents Index

> 最后更新: 2026-03-21
> 
> 本文档是 RANGEN 所有 Agent 的索引，帮助快速定位功能。

---

## Agent 分类

### 1. 核心推理 Agent (Core Reasoning)

| Agent | 文件位置 | 用途 | 状态 |
|-------|----------|------|------|
| **ReasoningAgent** | `agents/reasoning_agent.py` | 核心推理引擎，ReAct 循环 | 🟢 生产 |
| **ChiefAgent** | `agents/chief_agent.py` | 团队协调，主控 Agent | 🟢 生产 |
| **MultiAgentCoordinator** | `agents/multi_agent_coordinator.py` | 多 Agent 协调 | 🟢 生产 |

**使用示例**:
```python
from src.agents.reasoning_agent import ReasoningAgent

agent = ReasoningAgent(tool_registry=registry)
result = await agent.execute(task="分析这个问题")
```

---

### 2. 质量保证 Agent (Quality Assurance)

| Agent | 文件位置 | 用途 | 状态 |
|-------|----------|------|------|
| **ValidationAgent** | `agents/validation_agent.py` | 结果质量验证 | 🟢 生产 |
| **CitationAgent** | `agents/citation_agent.py` | 引用生成与溯源 | 🟢 生产 |
| **EnhancedValidationAgent** | `agents/enhanced_validation_agent.py` | 增强验证 | 🟡 实验 |

---

### 3. 知识增强 Agent (Knowledge Enhancement)

| Agent | 文件位置 | 用途 | 状态 |
|-------|----------|------|------|
| **RAGAgent** | `agents/rag_agent.py` | 检索增强生成 | 🟢 生产 |
| **RetrievalAgent** | `agents/retrieval_agent.py` | 知识检索 | 🟢 生产 |
| **ExpertAgent** | `agents/expert_agent.py` | 专家知识 | 🟡 实验 |

---

### 4. 反思与学习 Agent (Reflection & Learning)

| Agent | 文件位置 | 用途 | 状态 |
|-------|----------|------|------|
| **ReflectionAgent** | `core/reflection.py` | 反思机制 | 🟢 生产 |
| **ReflexionAgent** | `core/reflection.py` | 自我反思 | 🟢 生产 |
| **SelfLearningAgent** | `agents/self_learning_agent.py` | 自学习 | 🟡 实验 |
| **AdaptiveRetryAgent** | `core/reasoning/ml_framework/adaptive_retry_agent.py` | 自适应重试 | 🟢 生产 |

---

### 5. 专业团队 Agent (Professional Teams)

| Agent | 文件位置 | 用途 | 状态 |
|-------|----------|------|------|
| **EngineeringAgent** | `agents/professional_teams/engineering_agent.py` | 工程开发 | 🟢 生产 |
| **DesignAgent** | `agents/professional_teams/design_agent.py` | 设计 | 🟢 生产 |
| **MarketingAgent** | `agents/professional_teams/marketing_agent.py` | 市场营销 | 🟢 生产 |
| **TestingAgent** | `agents/professional_teams/testing_agent.py` | 测试 | 🟢 生产 |

---

### 6. 市场细分 Agent (Market-Specific)

#### 日本市场

| Agent | 文件位置 | 用途 | 状态 |
|-------|----------|------|------|
| **HRSpecialist** | `agents/japan_market/hr_specialist.py` | 人力资源 | 🟡 实验 |
| **FinancialExpert** | `agents/japan_market/financial_expert.py` | 金融 | 🟡 实验 |
| **LegalAdvisor** | `agents/japan_market/legal_advisor.py` | 法律 | 🟡 实验 |
| **CustomerManager** | `agents/japan_market/customer_manager.py` | 客户管理 | 🟡 实验 |

#### 中国市场

| Agent | 文件位置 | 用途 | 状态 |
|-------|----------|------|------|
| **ChinaMarketAgent** | `agents/china_market/base.py` | 中国市场基础 | 🟡 实验 |

---

### 7. 其他 Agent (Miscellaneous)

| Agent | 文件位置 | 用途 | 状态 |
|-------|----------|------|------|
| **AuditAgent** | `agents/audit_agent.py` | 审计 | 🟡 实验 |
| **SmartConversationAgent** | `agents/smart_conversation_agent.py` | 智能对话 | 🟡 实验 |
| **OpsDiagnosisAgent** | `agents/ops_diagnosis_agent.py` | 运维诊断 | 🟡 实验 |
| **RequirementAnalyzerAgent** | `agents/requirement_analyzer_agent.py` | 需求分析 | 🟡 实验 |

---

## Agent 工厂

使用 `AgentBuilder` 创建 Agent：

```python
from src.agents.agent_builder import AgentBuilder

builder = AgentBuilder()
builder.set_id("my_agent")
builder.set_type("react")
builder.add_capability("reasoning")
builder.add_capability("tool_use")
agent = builder.build()
```

---

## Agent 选择决策

当需要创建新 Agent 时，使用决策树：

```
需要创建 Agent?
│
├─ 是
│   ├─ 核心推理 → ReasoningAgent
│   ├─ 多 Agent 协调 → MultiAgentCoordinator
│   ├─ 质量验证 → ValidationAgent
│   ├─ 知识检索 → RAGAgent / RetrievalAgent
│   ├─ 专业领域 → Japan/China Market Agents
│   └─ 团队协作 → Professional Teams
│
└─ 否
    └─ 使用现有 Skill 或 Tool
```

---

## 工具关系说明

| 工具类型 | 关系 | 推荐 |
|----------|------|------|
| 搜索 | SearchTool → WebSearchTool → RealSearchTool | RealSearchTool |
| 提取 | query_extraction → answer_extraction → content_extractor | ContentExtractor |
| 浏览器 | BrowserTool (agents) ↔ GatewayBrowserTool (gateway) | 并存，按需使用 |

---

## 状态说明

| 状态 | 说明 |
|------|------|
| 🟢 生产 | 已在生产环境使用，稳定性高 |
| 🟡 实验 | 可用但功能可能变化 |
| 🔴 废弃 | 不推荐使用，会在未来移除 |

---

## 决策记录

- 2026-03-21: 创建 Agent 索引文档
- 2026-03-21: 标注生产 Agent (8个) 和实验 Agent (11个)
