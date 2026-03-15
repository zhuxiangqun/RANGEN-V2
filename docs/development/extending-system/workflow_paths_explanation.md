# 工作流路径说明

## 核心设计：多智能体协调是所有路径的基础机制

**重要说明**：整个系统通过多智能体协调工作，这是所有路径的基础机制。

在工作流图中，您可能会看到以下节点组：
- **多智能体协调路径** (5个节点) - **所有路径的基础机制**

**关键设计**：
- ✅ **所有路径（simple、complex、multi_agent、reasoning）都通过相同的多智能体协调节点序列执行**
- ✅ 多智能体协调节点序列：`memory_agent` → `knowledge_retrieval_agent` → `reasoning_agent` → `answer_generation_agent` → `citation_agent` → `synthesize`
- ✅ 路由决策只是选择不同的标签（用于日志和追踪），但实际执行路径相同
- ✅ **推理链能力已集成到 `reasoning_agent` 中**，不需要独立的推理链路径

## 路径选择逻辑

### 1. 推理链能力（Reasoning Chain Capability）⭐

**设计理念**：
- 🚀 **推理链是 `reasoning_agent` 的内部能力，不是独立的流程路径**
- 🚀 **所有路径都可以通过 `reasoning_agent` 使用推理链能力**
- 🚀 当 `needs_reasoning_chain=True` 时，`reasoning_agent` 会自动使用推理链模式

**触发条件**：
- 🚀 **使用统一复杂度判断服务（`UnifiedComplexityModelService`）进行智能判断**
- 服务会使用 LLM 判断查询是否需要推理链（`needs_reasoning_chain`）
- 如果 LLM 不可用，会使用规则判断作为 fallback（包含关键词或复杂度 >= 5.0）
- **`needs_reasoning_chain` 标志会被传递到 `reasoning_agent`**，让它在内部选择推理模式

**执行流程**：
```
scheduling_optimization → memory_agent → knowledge_retrieval_agent → 
reasoning_agent (使用推理链能力) → answer_generation_agent → citation_agent → synthesize → format
```

**适用场景**：需要多步骤推理的复杂查询（通过 `reasoning_agent` 内部使用推理链能力）

**关键点**：
- ✅ 推理链能力集成在 `reasoning_agent` 中，不需要独立的推理链路径
- ✅ `reasoning_agent` 会根据 `needs_reasoning_chain` 标志自动选择推理模式
- ✅ 所有路径都可以通过 `reasoning_agent` 使用推理链能力

---

### 2. 多智能体协调路径（所有路径的基础机制）⭐

**触发条件**：
- **所有查询**都通过多智能体协调节点序列执行
- 路由决策只是选择不同的标签（simple/complex/multi_agent）用于日志和追踪

**执行流程**：
```
scheduling_optimization → memory_agent → knowledge_retrieval_agent → reasoning_agent → 
answer_generation_agent → citation_agent → synthesize → format
```

**适用场景**：所有查询（简单、中等、复杂）

**关键点**：
- ✅ 这是系统的基础机制，所有路径都使用相同的多智能体协调节点序列
- ✅ 路由标签（simple/complex/multi_agent）仅用于日志和追踪，不影响实际执行路径
- ✅ 专家智能体节点序列确保所有查询都经过完整的多智能体协调处理

---

### 3. 路径标签说明

虽然路由决策会返回不同的标签（simple、complex、multi_agent），但**所有路径都通过相同的多智能体协调节点序列执行**：

- **simple 标签**：复杂度 < 3.0 的查询（用于日志和追踪）
- **complex 标签**：复杂度 3.0-6.0 的查询（用于日志和追踪）
- **multi_agent 标签**：复杂度 >= 6.0 的查询（用于日志和追踪）

**实际执行路径**：所有标签都路由到 `memory_agent`（多智能体协调节点序列入口）

---

## 路径选择逻辑

路径选择的逻辑：

1. **推理链能力**（集成在 `reasoning_agent` 中）⭐
   - 如果统一复杂度服务判断需要推理链（`needs_reasoning_chain = True`）
   - **`needs_reasoning_chain` 标志会被传递到 `reasoning_agent`**
   - `reasoning_agent` 会根据标志自动选择推理链模式
   - **所有路径都通过多智能体协调节点序列执行**，`reasoning_agent` 会使用推理链能力
   
2. **配置路由器路径**（如果启用）
   - 如果启用了配置路由器，根据配置规则选择路径标签
   - 但实际执行仍然通过多智能体协调节点序列
   
3. **多智能体协调路径**（所有路径的基础机制）⭐
   - **所有查询**都通过多智能体协调节点序列执行
   - 路由决策只是选择不同的标签（simple/complex/multi_agent/reasoning）用于日志和追踪
   - 实际执行路径相同：`memory_agent` → `knowledge_retrieval_agent` → `reasoning_agent` → `answer_generation_agent` → `citation_agent` → `synthesize`
   - **推理链能力集成在 `reasoning_agent` 中**，当需要时会自动使用

## 共享节点

所有路径都会经过以下共享节点：

1. **查询分析阶段**：
   - `query_analysis`（查询分析）
   - `scheduling_optimization`（调度优化）

2. **结果合成**：
   - `synthesize`（综合）
   - `format`（格式化）

## 核心功能集成说明

以下核心功能**不在预处理阶段**，而是在实际执行路径中由专家智能体内部使用：

1. **`context_engineering`（上下文工程）**：
   - 在 `memory_agent` 中集成使用，用于增强和管理上下文信息
   - 在需要上下文时由相关智能体调用

2. **`rag_retrieval`（RAG检索）**：
   - 在 `knowledge_retrieval_agent` 中集成使用，作为知识检索的核心机制
   - 专家智能体内部调用 RAG 功能进行知识检索

3. **`prompt_engineering`（提示词工程）**：
   - 在推理和答案生成时使用，由 `reasoning_agent` 和 `answer_generation_agent` 内部调用
   - 根据查询类型和上下文动态生成优化的提示词

**设计理念**：这些功能是执行路径的一部分，而不是预处理步骤。它们在实际需要时由相应的专家智能体调用，确保：
- 只在需要时执行，提高效率
- 与执行上下文紧密结合
- 在工作流图中显示为专家智能体的内部功能

## 工作流图显示

在工作流图中：
- 这些路径会显示为从 `scheduling_optimization` 节点出发的**条件路由**（虚线边）
- 它们不会同时执行，而是根据查询类型和复杂度选择其中一个
- 所有路径最终都会汇聚到 `synthesize` 节点

## 为什么看起来是并列的？

在工作流图中，这些路径可能看起来是并列的，这是因为：
1. 它们都从同一个路由节点（`scheduling_optimization`）出发
2. 它们通过条件路由（`add_conditional_edges`）互斥选择
3. Mermaid 图会显示所有可能的路径，即使它们不会同时执行

这是**正常的行为**，因为工作流图需要显示所有可能的执行路径，而实际执行时只会选择其中一个路径。

## 如何查看实际执行的路径？

要查看实际执行的路径，可以：
1. 查看执行日志中的路由决策信息
2. 查看工作流图中的节点状态（运行中的节点会高亮显示）
3. 查看执行时间线，了解实际执行的节点序列

