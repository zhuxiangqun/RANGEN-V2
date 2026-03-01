# 系统智能体清单

本文档列出了整个系统中所有的智能体模块。

## 智能体分类

### 1. 核心协调智能体（Core Coordination Agents）

#### 1.1 ChiefAgent（首席智能体）
- **位置**: `src/agents/chief_agent.py`
- **继承**: `BaseAgent`
- **职责**: 协调整个多智能体系统，实现任务分解、团队组建、协调执行等功能
- **能力**: 
  - 任务分解（Task Decomposition）
  - 团队管理（Team Management）
  - 冲突解决（Conflict Resolution）
  - 认知伙伴（Cognitive Partnership）
- **协调的专家智能体**:
  - MemoryAgent（记忆管理）
  - KnowledgeRetrievalAgent（知识检索）
  - ReasoningAgent（推理分析）
  - AnswerGenerationAgent（答案生成）
  - CitationAgent（引用生成）
  - MultimodalAgent（多模态处理，可选）
  - PromptEngineeringAgent（提示词工程，可选）
  - ContextEngineeringAgent（上下文工程，可选）

### 2. ReAct模式智能体（ReAct Pattern Agents）

#### 2.1 ReActAgent
- **位置**: `src/agents/react_agent.py`
- **继承**: `BaseAgent`
- **职责**: 实现思考-行动-观察循环（Think-Act-Observe）
- **特点**: 标准ReAct模式，支持工具调用

#### 2.2 LangGraphReActAgent
- **位置**: `src/agents/langgraph_react_agent.py`
- **继承**: `BaseAgent`
- **职责**: 基于LangGraph的ReAct Agent
- **优势**:
  - 可描述：工作流用图结构清晰描述
  - 可治理：状态检查点、条件路由、错误处理
  - 可复用：节点和边可以复用
  - 可恢复：支持检查点和状态恢复

### 3. 专家智能体（Expert Agents）

所有专家智能体都继承自 `ExpertAgent`，实现标准Agent循环（think → plan_action → execute_action → is_task_complete）。

#### 3.1 KnowledgeRetrievalAgent（知识检索专家智能体）
- **位置**: `src/agents/expert_agents.py`
- **继承**: `ExpertAgent`
- **职责**: 知识检索和信息收集
- **能力水平**: 0.9
- **协作风格**: supportive
- **使用的服务**: `KnowledgeRetrievalService`

#### 3.2 ReasoningAgent（推理专家智能体）
- **位置**: `src/agents/expert_agents.py`
- **继承**: `ExpertAgent`
- **职责**: 逻辑推理和问题分析
- **能力水平**: 0.95
- **协作风格**: analytical
- **使用的服务**: `ReasoningService`
- **特殊配置**: 20分钟超时（推理任务可能需要较长时间）

#### 3.3 AnswerGenerationAgent（答案生成专家智能体）
- **位置**: `src/agents/expert_agents.py`
- **继承**: `ExpertAgent`
- **职责**: 答案生成和格式化
- **能力水平**: 0.9
- **协作风格**: supportive
- **使用的服务**: `AnswerGenerationService`

#### 3.4 CitationAgent（引用专家智能体）
- **位置**: `src/agents/expert_agents.py`
- **继承**: `ExpertAgent`
- **职责**: 引用和来源生成
- **能力水平**: 0.85
- **协作风格**: supportive
- **使用的服务**: `CitationService`

#### 3.5 MemoryAgent（记忆专家智能体）
- **位置**: `src/agents/expert_agents.py`
- **继承**: `ExpertAgent`
- **职责**: 上下文工程和记忆管理
- **能力水平**: 0.95
- **协作风格**: supportive
- **使用的服务**: `UnifiedContextEngineeringCenter`
- **特殊说明**: 直接实现 `execute` 方法，不通过ExpertAgent的标准流程

#### 3.6 MultimodalAgent（多模态处理专家智能体）
- **位置**: `src/agents/expert_agents.py`
- **继承**: `ExpertAgent`
- **职责**: 处理图像、音频、视频等多模态内容
- **能力水平**: 0.9
- **协作风格**: supportive
- **使用的服务**: `MultimodalService`

#### 3.7 PromptEngineeringAgent（提示词工程专家智能体）
- **位置**: `src/agents/expert_agents.py` 和 `src/agents/prompt_engineering_agent.py`
- **继承**: `ExpertAgent`
- **职责**: 提示词工程和模板优化
- **能力水平**: 0.95
- **特点**: 自我学习和优化提示词，集成RL/ML、A/B测试、性能监控

#### 3.8 ContextEngineeringAgent（上下文工程专家智能体）
- **位置**: `src/agents/expert_agents.py` 和 `src/agents/context_engineering_agent.py`
- **继承**: `ExpertAgent`
- **职责**: 上下文工程和长期记忆管理
- **能力水平**: 0.95
- **特点**: 管理长期记忆和上下文

#### 3.9 RAGAgent（检索增强生成智能体）
- **位置**: `src/agents/rag_agent.py`
- **继承**: `ExpertAgent`
- **职责**: 检索增强生成，封装知识检索和答案生成功能
- **能力水平**: 0.9
- **协作风格**: supportive
- **内部组件**:
  - KnowledgeRetrievalAgent（知识检索）
  - AnswerGenerationAgent（答案生成）
  - ReasoningEngine（推理引擎）

### 4. 增强智能体（Enhanced Agents）

#### 4.1 EnhancedAnalysisAgent（增强的分析智能体）
- **位置**: `src/agents/enhanced_analysis_agent.py`
- **继承**: `BaseAgent`
- **职责**: 深度分析和问题诊断

#### 4.2 IntelligentStrategyAgent（智能策略智能体）
- **位置**: `src/agents/intelligent_strategy_agent.py`
- **继承**: `BaseAgent`
- **职责**: 整合策略分析、决策制定和执行功能
- **能力**: 
  - 策略分析
  - 决策制定
  - 策略执行

#### 4.3 LearningSystem（学习系统智能体）
- **位置**: `src/agents/learning_system.py`
- **继承**: `BaseAgent`
- **职责**: 系统学习和优化
- **特点**: 持续改进机制

### 5. 其他智能体（Other Agents）

#### 5.1 FactVerificationAgent（事实验证智能体）
- **位置**: `src/agents/fact_verification_agent.py`
- **职责**: 事实验证

#### 5.2 OptimizedKnowledgeRetrievalAgent（优化的知识检索智能体）
- **位置**: `src/agents/optimized_knowledge_retrieval_agent.py`
- **职责**: 优化的知识检索

#### 5.3 SimpleAgent（简单智能体实现）
- **位置**: `src/agents/base_agent.py`
- **继承**: `BaseAgent`
- **职责**: 简单智能体实现（用于测试或简单场景）

### 6. 智能协调器（Intelligent Coordinator）

#### 6.1 IntelligentOrchestrator（智能协调器）
- **位置**: `src/agents/base_agent.py`（作为ReActAgent的子类）
- **继承**: `ReActAgent`
- **职责**: 智能协调层，协调多个智能体的执行
- **特点**: 使用统一规则管理器，支持RAG工具

## 智能体层次结构

```
BaseAgent（基础智能体抽象类）
├── ExpertAgent（专家智能体基类）
│   ├── KnowledgeRetrievalAgent
│   ├── ReasoningAgent
│   ├── AnswerGenerationAgent
│   ├── CitationAgent
│   ├── MemoryAgent
│   ├── MultimodalAgent
│   ├── PromptEngineeringAgent
│   ├── ContextEngineeringAgent
│   └── RAGAgent
├── ChiefAgent（首席智能体）
├── ReActAgent（ReAct模式智能体）
│   └── IntelligentOrchestrator（智能协调器）
├── LangGraphReActAgent（LangGraph ReAct智能体）
├── EnhancedAnalysisAgent（增强的分析智能体）
├── IntelligentStrategyAgent（智能策略智能体）
├── LearningSystem（学习系统智能体）
└── SimpleAgent（简单智能体实现）
```

## 智能体在工作流中的使用

### LangGraph工作流中的智能体节点

在LangGraph统一工作流中，以下智能体作为独立节点显示：

1. **MemoryAgent** (`memory_agent`) - 记忆管理
2. **KnowledgeRetrievalAgent** (`knowledge_retrieval_agent`) - 知识检索
3. **ReasoningAgent** (`reasoning_agent`) - 推理分析
4. **AnswerGenerationAgent** (`answer_generation_agent`) - 答案生成
5. **CitationAgent** (`citation_agent`) - 引用生成

**执行顺序**:
```
memory_agent → knowledge_retrieval_agent → reasoning_agent → 
answer_generation_agent → citation_agent → synthesize
```

### 核心功能节点中的智能体

1. **RAGAgent** (`rag_retrieval`) - RAG检索节点
2. **PromptEngineeringAgent** (`prompt_engineering`) - 提示词工程节点
3. **ContextEngineeringAgent** (`context_engineering`) - 上下文工程节点

## 智能体能力配置

所有智能体都支持以下能力（通过 `capabilities_dict` 配置）：

- `EXTENSIBILITY`: 可扩展性
- `INTELLIGENCE`: 智能化
- `AUTONOMOUS_DECISION`: 自主决策
- `DYNAMIC_STRATEGY`: 动态策略
- `STRATEGY_LEARNING`: 策略学习
- `SELF_LEARNING`: 自我学习
- `AUTOMATIC_REASONING`: 自动推理
- `DYNAMIC_CONFIDENCE`: 动态置信度
- `LLM_DRIVEN_RECOGNITION`: LLM驱动识别
- `DYNAMIC_CHAIN_OF_THOUGHT`: 动态思维链
- `DYNAMIC_CLASSIFICATION`: 动态分类

## 智能体总数统计

- **核心协调智能体**: 1个（ChiefAgent）
- **ReAct模式智能体**: 2个（ReActAgent, LangGraphReActAgent）
- **专家智能体**: 9个（KnowledgeRetrievalAgent, ReasoningAgent, AnswerGenerationAgent, CitationAgent, MemoryAgent, MultimodalAgent, PromptEngineeringAgent, ContextEngineeringAgent, RAGAgent）
- **增强智能体**: 3个（EnhancedAnalysisAgent, IntelligentStrategyAgent, LearningSystem）
- **其他智能体**: 3个（FactVerificationAgent, OptimizedKnowledgeRetrievalAgent, SimpleAgent）
- **智能协调器**: 1个（IntelligentOrchestrator）

**总计**: 19个智能体类

## 注意事项

1. **ExpertAgent子类**：所有专家智能体都继承自 `ExpertAgent`，实现标准Agent循环
2. **ChiefAgent协调**：ChiefAgent内部动态创建和协调专家智能体
3. **工作流节点**：在LangGraph工作流中，只有系统真正的智能体模块才会显示为节点
4. **智能体池**：ChiefAgent维护专家智能体池，避免重复创建

