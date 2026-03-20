# Agent 状态文档

> 最后更新: 2026-03-20

## 生产使用

以下 Agent 在生产环境中实际使用：

| Agent | 文件 | 用途 |
|-------|------|------|
| **ReasoningAgent** | `reasoning_agent.py` | 核心推理引擎 |
| **ValidationAgent** | `validation_agent.py` | 质量校验 |
| **CitationAgent** | `citation_agent.py` | 引用生成 |
| **ChiefAgent** | `chief_agent.py` | 团队协调 |
| **MultiAgentCoordinator** | `multi_agent_coordinator.py` | 多 Agent 协调 |
| **RetrievalAgent** | `retrieval_agent.py` | 知识检索 |
| **ReflectionAgent** | `reflection.py` | 反思机制 |
| **AdaptiveRetryAgent** | `ml_framework/adaptive_retry_agent.py` | 自适应重试 |

## 专业团队 Agent

| Agent | 文件 | 用途 |
|-------|------|------|
| **EngineeringAgent** | `professional_teams/` | 工程开发 |
| **DesignAgent** | `professional_teams/` | 设计 |
| **MarketingAgent** | `professional_teams/` | 市场营销 |
| **TestingAgent** | `professional_teams/` | 测试 |

## Wrapper Agent

这些 Agent 通过 wrapper 使用，保持向后兼容：

| Agent | Wrapper | 原文件 |
|-------|---------|--------|
| RAGAgent | `rag_agent_wrapper.py` | `rag_agent.py` |
| LangGraphReActAgent | - | `langgraph_react_agent.py` |

## 实验性 Agent (库存)

以下 Agent 未在生产中使用，属于"实验性/库存"：

| Agent | 文件 | 说明 |
|-------|------|------|
| ExpertAgent | `expert_agent.py` | 专家系统 (未使用) |
| SmartConversationAgent | `smart_conversation_agent.py` | 智能对话 (未使用) |
| OpsDiagnosisAgent | `ops_diagnosis_agent.py` | 运维诊断 (未使用) |
| RequirementAnalyzerAgent | `requirement_analyzer_agent.py` | 需求分析 (未使用) |
| Level3Agent | `level3_agent.py` | L3 推理 (未使用) |
| ReactAgent | `react_agent.py` | ReAct 基础版 (未使用) |
| EnhancedReactAgent | `enhanced_react_agent.py` | 增强 ReAct (未使用) |
| HookedReActAgent | `hooked_react_agent.py` | Hook 版 (未使用) |
| EnhancedValidationAgent | `enhanced_validation_agent.py` | 增强校验 (未使用) |
| SelfLearningAgent | `self_learning_agent.py` | 自学习 (未使用) |
| AuditAgent | `audit_agent.py` | 审计 (未使用) |

---

## 决策记录

- 2026-03-20: 分析完成，确认 8 个 Agent 在生产中使用
- 2026-03-20: 确认 11 个 Agent 为实验性/库存

## 建议

1. **保持现状** - 这些库存 Agent 虽然未使用，但可以作为参考实现
2. **未来清理** - 如果长期未使用，可以考虑归档或删除
3. **不强制废弃** - 某些 Agent 可能在特定场景下有用途
