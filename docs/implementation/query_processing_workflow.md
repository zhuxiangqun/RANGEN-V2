# 系统查询处理流程文档

## 概述

本文档详细说明整个系统对于查询问题的处理流程。系统采用 LangGraph 工作流架构，通过多智能体协调机制处理所有查询。

> **重要说明**：LangGraph 工作流**完全保留了原有系统的处理流程**。LangGraph 只是作为一个**编排框架**，将原有的处理流程组织成节点和边的形式，使其可可视化、可追踪、可恢复。所有原有的 Agent（知识检索、推理、答案生成、引用生成）和优化（ML/RL调度、并行执行等）都会被完整调用。详见：[LangGraph 保留原有流程说明](./langgraph_preserves_original_flow.md)

## 完整工作流结构

```
Entry → Route Query → Context Engineering → RAG Retrieval → Prompt Engineering → 
       Query Analysis → Scheduling Optimization → [条件路由]
                                                                                ├─ Simple Query → Knowledge Retrieval (Detailed) → 
                                                                                │                  Reasoning Analysis (Detailed) → 
                                                                                │                  Answer Generation (Detailed) → 
                                                                                │                  Citation Generation (Detailed) → 
                                                                                │                  Synthesize → Format → END
                                                                                ├─ Complex Query → Knowledge Retrieval (Detailed) → 
                                                                                │                  Reasoning Analysis (Detailed) → 
                                                                                │                  Answer Generation (Detailed) → 
                                                                                │                  Citation Generation (Detailed) → 
                                                                                │                  Synthesize → Format → END
                                                                                ├─ Reasoning → generate_steps → execute_step → gather_evidence → 
                                                                                │                extract_step_answer → synthesize_reasoning_answer → Format → END
                                                                                └─ Multi-Agent → multi_agent_coordinate → Synthesize → Format → END
```

### 详细处理节点（新增）⭐

在查询路径中，系统会显式展示所有主要处理步骤：

1. **Query Analysis（查询分析）**：分析查询类型和复杂度
2. **Scheduling Optimization（调度优化）**：使用 ML/RL 选择最优调度策略
3. **Knowledge Retrieval (Detailed)（知识检索详细）**：显式展示知识检索过程
4. **Reasoning Analysis (Detailed)（推理分析详细）**：显式展示推理分析过程
5. **Answer Generation (Detailed)（答案生成详细）**：显式展示答案生成过程
6. **Citation Generation (Detailed)（引用生成详细）**：显式展示引用生成过程

这些节点确保您能够清楚地看到系统如何处理查询问题，包括：
- ✅ 查询分析和复杂度评估
- ✅ ML/RL 调度优化决策
- ✅ 知识检索过程（包括并发处理）
- ✅ 推理分析过程（包括推理链）
- ✅ 答案生成过程
- ✅ 引用生成过程

### 核心功能节点（新增）⭐

在路由决策之前，系统会执行以下核心功能节点，为所有路径提供增强的上下文、知识和提示词：

1. **Context Engineering（上下文工程）**：增强和管理上下文信息
2. **RAG Retrieval（RAG检索）**：从知识库中检索相关知识
3. **Prompt Engineering（提示词工程）**：生成和优化提示词
4. **Query Analysis（查询分析）**：分析查询类型和复杂度
5. **Scheduling Optimization（调度优化）**：使用 ML/RL 选择最优调度策略

这些节点确保所有路径都能获得：
- 增强的上下文信息（`enhanced_context`）
- 检索到的知识（`evidence`, `knowledge`, `citations`）
- 优化的提示词（`generated_prompt`）
- 查询分析结果（`query_type`, `query_complexity`）
- 调度策略（`scheduling_strategy`）

## 详细流程说明

### 1. 入口节点 (Entry)

**功能**：初始化查询状态

**执行内容**：
- 初始化状态字典（context, evidence, knowledge, citations 等）
- 设置 `task_complete = False`
- 记录开始时间戳
- 初始化节点执行时间追踪

**输出**：包含查询和初始状态的状态字典

---

### 2. 路由查询节点 (Route Query)

**功能**：分析查询复杂度并决定路由路径

**执行内容**：
- 调用 `_assess_complexity()` 评估查询复杂度（0-10分）
- 计算复杂度分数（基于关键词、长度、问题数量等）
- 调用 `_route_decision()` 进行路由决策

---

### 2.1 上下文工程节点 (Context Engineering) ⭐ **新增**

**功能**：增强和管理上下文信息

**执行内容**：
- 使用 `ContextEngineeringAgent` 增强上下文
- 获取会话上下文片段（`context_fragments`）
- 合并增强的上下文到状态中
- 记录上下文元数据

**输出**：
- `enhanced_context`：增强的上下文信息
- `context_fragments`：上下文片段列表
- `metadata.context_engineering`：上下文工程元数据

---

### 2.2 RAG 检索节点 (RAG Retrieval) ⭐ **新增**

**功能**：从知识库中检索相关知识

**执行内容**：
- 使用 `EnhancedKnowledgeRetrievalAgent` 或 `RAGAgent` 进行知识检索
- 从知识库管理系统（KMS）检索相关知识
- 应用 Rerank 模型重新排序结果
- 提取证据、知识和引用

**输出**：
- `evidence`：检索到的证据列表
- `knowledge`：知识来源列表
- `citations`：引用列表

---

### 2.3 提示词工程节点 (Prompt Engineering) ⭐ **新增**

**功能**：生成和优化提示词

**执行内容**：
- 使用 `PromptEngineeringAgent` 生成优化的提示词
- 根据查询类型和上下文选择最佳模板
- 支持 RL/ML 优化（如果启用）
- 记录提示词元数据

**输出**：
- `generated_prompt`：生成的提示词
- `prompt_template`：使用的提示词模板
- `metadata.prompt_engineering`：提示词工程元数据

**路由决策逻辑**（优先级从高到低）：

1. **推理路径**（最高优先级）
   - 🚀 **使用统一复杂度判断服务（`UnifiedComplexityModelService`）进行智能判断**
   - 服务会使用 LLM 判断查询是否需要推理链（`needs_reasoning_chain`）
   - 如果 LLM 不可用，会使用规则判断作为 fallback（包含关键词或复杂度 >= 5.0）
   - 路由到：`reasoning` → `generate_steps`

2. **配置驱动路由**（如果启用）
   - 条件：`ENABLE_CONFIGURABLE_ROUTER=true`
   - 使用配置路由器返回的路径

3. **多智能体路径**（默认路径）⭐
   - **核心设计**：整个系统通过多智能体协调工作
   - 默认路由到：`multi_agent` → `multi_agent_coordinate`
   - 这是系统的核心协调机制

**输出**：包含 `route_path` 的状态字典

---

### 3. 路径执行

在完成核心功能节点（上下文工程、RAG检索、提示词工程）后，根据路由决策，系统会进入以下四种路径之一：

**注意**：所有路径都已经获得了：
- 增强的上下文（`enhanced_context`）
- 检索到的知识（`evidence`, `knowledge`）
- 优化的提示词（`generated_prompt`）

#### 3.1 简单查询路径 (Simple Query)

**流程**：`simple_query` → `synthesize` → `format` → END

**执行内容**：
- 直接检索知识库
- 获取简单答案
- 设置证据和知识

**适用场景**：复杂度 < 3.0 的简单查询

---

#### 3.2 复杂查询路径 (Complex Query)

**流程**：`complex_query` → `synthesize` → `format` → END

**执行内容**：
- 使用推理智能体进行复杂推理
- 收集多源证据
- 生成复杂答案

**适用场景**：复杂度 >= 3.0 的复杂查询

---

#### 3.3 推理路径 (Reasoning)

**流程**：
```
generate_steps → execute_step → gather_evidence → extract_step_answer
    ↓ (条件路由)
    ├─ continue → execute_step (继续执行步骤)
    ├─ synthesize → synthesize_reasoning_answer → format → END
    └─ end → format → END (错误情况)
```

**节点说明**：

1. **generate_steps**：生成推理步骤
   - 使用 `RealReasoningEngine` 生成推理步骤
   - 将复杂查询分解为多个推理步骤

2. **execute_step**：执行单个推理步骤
   - 执行当前步骤的推理逻辑

3. **gather_evidence**：收集证据
   - 为当前步骤收集相关证据

4. **extract_step_answer**：提取步骤答案
   - 从证据中提取当前步骤的答案

5. **synthesize_reasoning_answer**：合成推理答案
   - 将所有步骤的答案合成为最终答案

**条件路由**：`_should_continue_reasoning()`
- `continue`：继续执行下一个推理步骤
- `synthesize`：所有步骤完成，进入合成阶段
- `end`：出现错误，直接结束

**适用场景**：包含推理关键词或复杂度 >= 5.0 的查询

---

#### 3.4 多智能体协调路径 (Multi-Agent) ⭐ **默认路径**

**流程**：`multi_agent_coordinate` → `synthesize` → `format` → END

**节点说明**：

**multi_agent_coordinate**：多智能体协调节点
- **核心机制**：使用 `ChiefAgent` 协调多个智能体执行任务
- **执行内容**：
  1. 构建上下文（query, knowledge, evidence, user_context）
  2. 调用 `ChiefAgent.execute()` 进行协调
  3. 提取协调结果（answer, final_answer, knowledge, evidence, confidence）
  4. 设置 `task_complete = True`
  5. 记录协调元数据

**降级策略**：
- 如果 `ChiefAgent` 不可用，降级使用 `ReActAgent`
- 如果 `ReActAgent` 也不可用，返回错误

**适用场景**：**所有查询（默认路径）**

---

### 4. 综合节点 (Synthesize)

**功能**：综合所有路径的结果

**执行内容**：
- 优先使用已有答案（`state['answer']`）
- 如果没有答案，从证据中提取答案
- 尝试使用答案生成工具（如果可用）
- 降级：从证据中提取简单答案
- 设置 `final_answer`

**输入**：来自各个路径的状态（包含 answer, evidence, knowledge 等）

**输出**：包含 `final_answer` 的状态

---

### 5. 格式化节点 (Format)

**功能**：格式化最终结果

**执行内容**：
- 计算总执行时间
- 确保 `final_answer` 存在
- 确保 `confidence` 存在（默认 0.5）
- 设置 `task_complete = True`
- 记录节点执行时间

**输出**：包含完整结果的状态字典

---

### 6. 结束 (END)

**功能**：工作流执行完成

**返回结果**：
```python
{
    "success": task_complete and not error,
    "answer": final_answer,
    "confidence": confidence,
    "knowledge": knowledge,
    "citations": citations,
    "route_path": route_path,
    "execution_time": execution_time,
    "error": error,
    "errors": errors,
    "node_times": node_times
}
```

---

## 核心设计理念

### 1. 多智能体协调为核心 ⭐

- **默认路径**：所有查询默认通过 `multi_agent_coordinate` 节点处理
- **协调机制**：使用 `ChiefAgent` 协调多个智能体
- **系统架构**：整个系统通过多智能体协调工作

### 2. 智能路由决策

- **优先级**：推理路径 > 配置驱动路由 > 多智能体路径（默认）
- **动态判断**：基于查询内容、复杂度分数、系统状态
- **降级策略**：如果首选路径不可用，自动降级

### 3. 流式执行与实时追踪

- **LangGraph 流式执行**：使用 `astream()` 实时推送节点执行状态
- **可视化同步**：Workflow Graph、Execution Timeline、Execution Status 实时更新
- **编排追踪**：追踪 Agent 执行、工具调用、提示词工程等

### 4. 错误处理与恢复

- **节点级错误处理**：每个节点都有 try-except 错误处理
- **错误分类**：`ErrorCategory`（RETRYABLE, PERMANENT, FATAL）
- **降级策略**：多层次的降级机制确保系统可用性

---

## 状态流转

### ResearchSystemState 结构

```python
{
    # 查询信息
    "query": str,
    "context": Dict[str, Any],
    
    # 路由信息
    "route_path": str,  # "simple" | "complex" | "reasoning" | "multi_agent"
    "complexity_score": float,  # 0.0 - 10.0
    
    # 证据和知识
    "evidence": List[Dict],
    "knowledge": List[Dict],
    "citations": List[Dict],
    
    # 答案
    "answer": Optional[str],
    "final_answer": Optional[str],
    "confidence": float,  # 0.0 - 1.0
    
    # 执行状态
    "task_complete": bool,
    "error": Optional[str],
    "errors": List[Dict],
    "execution_time": float,
    
    # 性能监控
    "node_execution_times": Dict[str, float],
    "token_usage": Dict[str, Any],
    "api_calls": Dict[str, Any],
    
    # 元数据
    "metadata": Dict[str, Any],
    "workflow_checkpoint_id": Optional[str]
}
```

---

## 执行示例

### 示例1：默认多智能体协调路径

```
用户查询: "什么是人工智能？"

1. Entry → 初始化状态
2. Route Query → 评估复杂度 → 路由决策
3. Context Engineering → 增强上下文信息
4. RAG Retrieval → 从知识库检索相关知识
5. Prompt Engineering → 生成优化的提示词
6. [路由决策] → multi_agent
7. multi_agent_coordinate → 
   - ChiefAgent 协调多个智能体
   - 使用增强的上下文、检索到的知识和优化的提示词
   - 知识检索智能体获取知识（可能使用已检索的知识）
   - 答案生成智能体生成答案
   - 返回协调结果
8. Synthesize → 综合结果
9. Format → 格式化最终答案
10. END → 返回结果
```

### 示例2：推理路径

```
用户查询: "如果温度升高，那么会发生什么？"

1. Entry → 初始化状态
2. Route Query → 检测到推理关键词 "如果" → reasoning
3. generate_steps → 生成推理步骤
4. execute_step → 执行步骤1
5. gather_evidence → 收集证据
6. extract_step_answer → 提取步骤答案
7. (循环) → 继续执行步骤2, 3...
8. synthesize_reasoning_answer → 合成所有步骤答案
9. Format → 格式化最终答案
10. END → 返回结果
```

---

## 性能优化

### 1. 节点执行时间追踪
- 每个节点记录执行时间
- 存储在 `node_execution_times` 中

### 2. 缓存机制
- 支持工作流缓存（如果启用）
- 减少重复计算

### 3. 并行执行
- 支持并行节点执行（如果启用）
- 优化整体执行时间

---

## 可视化追踪

### 实时状态同步

系统通过 LangGraph 的流式执行机制，实时推送以下信息：

1. **Workflow Graph**：实时高亮当前执行的节点
2. **Execution Timeline**：实时显示节点执行顺序和时间
3. **Execution Status**：实时更新执行状态
4. **Orchestration Process**：实时显示编排事件（Agent 执行、工具调用等）
5. **Final Answer**：执行完成后显示最终答案

### WebSocket 推送

- `node_update`：节点状态更新（running → completed）
- `execution_start`：执行开始
- `execution_end`：执行结束
- `orchestration_event`：编排事件

---

## 总结

整个系统采用**多智能体协调为核心**的设计理念，所有查询默认通过 `multi_agent_coordinate` 节点处理。系统支持四种路径（Simple、Complex、Reasoning、Multi-Agent），通过智能路由决策选择最适合的路径。整个流程通过 LangGraph 流式执行，实现实时状态同步和可视化追踪。

