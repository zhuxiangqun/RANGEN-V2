# RANGEN Agents Index

> 最后更新: 2026-03-22
> 
> 本文档是 RANGEN 所有 Agent 的索引，帮助快速定位功能。

---

## Agent 分类

### 1. 核心推理 Agent (Core Reasoning)

| Agent | 文件位置 | 用途 | 状态 |
|-------|----------|------|------|
| **ReasoningAgent** | `src/agents/core/reasoning_agent.py` | 核心推理引擎，ReAct 循环 | 🟢 生产 |
| **ReactAgent** | `src/agents/core/react_agent.py` | ReAct 模式执行 | 🟢 生产 |
| **RetrievalAgent** | `src/agents/core/retrieval_agent.py` | 知识检索 | 🟢 生产 |
| **ChiefAgent** | `src/agents/chief_agent.py` | 团队协调，主控 Agent | 🟢 生产 |

**使用示例**:
```python
from src.agents.core.reasoning_agent import ReasoningAgent

agent = ReasoningAgent(tool_registry=registry)
result = await agent.execute(task="分析这个问题")
```

---

### 2. 专业 Agent (Specialized)

| Agent | 文件位置 | 用途 | 状态 |
|-------|----------|------|------|
| **ExpertAgent** | `src/agents/specialized/expert_agent.py` | 领域专家 | 🟢 生产 |
| **RAGAgent** | `src/agents/specialized/rag_agent.py` | RAG检索增强 | 🟢 生产 |
| **CitationAgent** | `src/agents/specialized/citation_agent.py` | 引用生成 | 🟢 生产 |
| **AuditAgent** | `src/agents/specialized/audit_agent.py` | 审核检查 | 🟢 生产 |
| **RequirementAnalyzerAgent** | `src/agents/specialized/requirement_analyzer_agent.py` | 需求分析 | 🟢 生产 |

---

### 3. 质量保证 Agent (Quality Assurance)

| Agent | 文件位置 | 用途 | 状态 |
|-------|----------|------|------|
| **ValidationAgent** | `src/agents/quality/validation_agent.py` | 结果验证 | 🟢 生产 |
| **EnhancedValidationAgent** | `src/agents/enhanced_validation_agent.py` | 增强验证 | 🟡 实验 |

---

### 4. 学习 Agent (Learning)

| Agent | 文件位置 | 用途 | 状态 |
|-------|----------|------|------|
| **SelfLearningAgent** | `src/agents/learning/self_learning_agent.py` | 自我学习 | 🟡 实验 |

---

### 5. 包装器 Agent (Wrappers)

| Agent | 文件位置 | 用途 | 状态 |
|-------|----------|------|------|
| **ChiefAgentWrapper** | `src/agents/wrappers/chief_agent_wrapper.py` | Chief包装器 | 🟢 生产 |
| **ContextEngineeringAgentWrapper** | `src/agents/wrappers/context_engineering_agent_wrapper.py` | 上下文工程 | 🟢 生产 |
| **PromptEngineeringAgentWrapper** | `src/agents/wrappers/prompt_engineering_agent_wrapper.py` | 提示词工程 | 🟢 生产 |

---

## 目录结构

```
src/agents/
├── core/                    # 核心Agent
│   ├── base_agent.py       # 基类
│   ├── reasoning_agent.py   # 推理Agent
│   ├── react_agent.py      # ReAct Agent
│   └── retrieval_agent.py   # 检索Agent
├── specialized/             # 专业Agent
│   ├── expert_agent.py
│   ├── rag_agent.py
│   ├── citation_agent.py
│   └── audit_agent.py
├── quality/                # 质量保证
│   └── validation_agent.py
├── learning/               # 学习Agent
│   └── self_learning_agent.py
├── wrappers/               # 包装器
│   ├── chief_agent_wrapper.py
│   └── ...
├── chief_agent.py          # 主控Agent
└── enhanced_validation_agent.py
```

---

*最后更新: 2026-03-22*
