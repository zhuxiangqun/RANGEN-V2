# 当前核心系统样本处理流程（ReAct Agent架构）

**生成时间**: 2025-11-27  
**架构**: 默认使用ReAct Agent架构

---

## 📊 完整流程概览

```
FRAMES样本输入
    ↓
[1] scripts/run_core_with_frames.py
    ├─ 加载样本数据
    ├─ 创建UnifiedResearchSystem
    └─ 调用 _process_single_sample()
         ↓
[2] UnifiedResearchSystem.execute_research()
    ├─ 检查缓存
    ├─ [默认] 使用ReAct Agent架构
    └─ [回退] 传统流程（如果ReAct Agent失败）
         ↓
[3] ReAct Agent.execute()
    ├─ ReAct循环（思考-行动-观察）
    │   ├─ 思考：分析任务，决定下一步
    │   ├─ 规划：决定调用哪个工具
    │   ├─ 行动：调用工具（如RAG工具）
    │   └─ 观察：接收工具返回结果
    └─ 综合：生成最终答案
         ↓
[4] RAG工具.call()
    ├─ 知识检索（Knowledge Agent）
    └─ 推理生成（Reasoning Engine）
         ↓
[5] 返回最终答案
    └─ ResearchResult
```

---

## 🔍 详细流程分析

### 阶段1: 样本输入和初始化

**文件**: `scripts/run_core_with_frames.py`

**流程**:
```python
# 1. 加载FRAMES数据集
samples = load_frames_dataset(data_path)

# 2. 创建UnifiedResearchSystem
system = await create_unified_research_system()

# 3. 处理单个样本
for item in samples:
    query_text = item.get("query") or item.get("question")
    request = ResearchRequest(
        query=query_text,
        context={
            "dataset": "FRAMES",
            "sample_id": item.get("id"),
            "expected_answer": item.get("answer")
        }
    )
    result = await system.execute_research(request)
```

**关键点**:
- 从FRAMES数据集加载样本
- 创建`ResearchRequest`对象
- 传递样本ID和期望答案（用于评测）

---

### 阶段2: UnifiedResearchSystem入口

**文件**: `src/unified_research_system.py`

**流程**:
```python
async def execute_research(self, request: ResearchRequest):
    # 1. 检查缓存
    cached_result = self._check_cache(request.query)
    if cached_result:
        return cached_result
    
    # 2. [默认] 使用ReAct Agent架构
    if self._use_react_agent and self._react_agent:
        return await self._execute_with_react_agent(request)
    
    # 3. [回退] 传统流程
    return await self._execute_research_internal(request)
```

**关键点**:
- 首先检查缓存，如果命中直接返回
- 默认使用ReAct Agent架构
- 如果ReAct Agent未初始化，回退到传统流程

---

### 阶段3: ReAct Agent执行（核心流程）

**文件**: `src/agents/react_agent.py`

**流程**:
```python
async def execute(self, context: Dict[str, Any]):
    query = context.get('query')
    
    # ReAct循环
    while iteration < max_iterations:
        # 步骤1: 思考（Reason）
        thought = await self._think(query, observations)
        
        # 步骤2: 判断是否完成
        if self._is_task_complete(thought, observations):
            break
        
        # 步骤3: 规划行动（Plan Action）
        action = await self._plan_action(thought, query, observations)
        
        # 步骤4: 行动（Act）- 调用工具
        observation = await self._act(action)
        observations.append(observation)
        
        iteration += 1
    
    # 步骤5: 综合答案
    final_answer = await self._synthesize_answer(query, observations, thoughts)
    return AgentResult(data={"answer": final_answer})
```

**详细步骤**:

#### 3.1 思考阶段（Think）

**功能**: 分析当前任务状态，决定下一步

**实现**:
```python
async def _think(self, query, observations):
    # 构建思考提示词
    think_prompt = f"""
    任务: {query}
    已观察到的信息: {format_observations(observations)}
    可用工具: {list_tools()}
    
    请思考：
    1. 当前任务完成情况如何？
    2. 还需要什么信息？
    3. 下一步应该做什么？
    """
    
    # 调用LLM进行思考
    thought = await self.llm_client._call_llm(think_prompt)
    return thought
```

**输出**: 思考结果（文本描述）

---

#### 3.2 规划行动阶段（Plan Action）

**功能**: 决定调用哪个工具

**实现**:
```python
async def _plan_action(self, thought, query, observations):
    # 构建规划提示词
    plan_prompt = f"""
    思考结果: {thought}
    可用工具: {tools_schema}
    
    请以JSON格式返回行动计划：
    {{
        "tool_name": "工具名称",
        "params": {{"参数名": "参数值"}},
        "reasoning": "选择此工具的原因"
    }}
    """
    
    # 调用LLM规划行动
    action_json = await self.llm_client._call_llm(plan_prompt)
    action = Action.from_json(action_json)
    return action
```

**输出**: 行动计划（包含工具名称和参数）

**默认策略**: 如果LLM规划失败，默认使用RAG工具

---

#### 3.3 行动阶段（Act）

**功能**: 调用工具执行行动

**实现**:
```python
async def _act(self, action: Action):
    # 获取工具
    tool = self.tool_registry.get_tool(action.tool_name)
    
    # 调用工具
    result = await tool.call(**action.params)
    
    # 构建观察结果
    observation = {
        "success": result.success,
        "tool_name": action.tool_name,
        "data": result.data,
        "error": result.error
    }
    return observation
```

**输出**: 观察结果（工具执行结果）

---

#### 3.4 观察阶段（Observe）

**功能**: 接收工具返回的结果

**实现**:
- 工具执行完成后，结果自动添加到`observations`列表
- 观察结果包含：
  - 工具名称
  - 执行是否成功
  - 返回的数据
  - 错误信息（如果有）

---

#### 3.5 综合答案阶段（Synthesize）

**功能**: 基于所有观察和思考生成最终答案

**实现**:
```python
async def _synthesize_answer(self, query, observations, thoughts):
    # 提取所有成功的观察结果
    successful_observations = [obs for obs in observations if obs.get('success')]
    
    # 如果RAG工具返回了答案，直接使用
    for obs in successful_observations:
        if obs.get('tool_name') == 'rag' and obs.get('data'):
            answer = obs['data'].get('answer')
            if answer:
                return answer
    
    # 否则，综合所有观察结果生成答案
    synthesize_prompt = f"""
    问题: {query}
    收集到的信息: {format_observations(successful_observations)}
    请生成一个完整、准确的答案。
    """
    answer = await self.llm_client._call_llm(synthesize_prompt)
    return answer
```

**输出**: 最终答案

---

### 阶段4: RAG工具执行

**文件**: `src/agents/tools/rag_tool.py`

**流程**:
```python
async def call(self, query: str, **kwargs):
    # 步骤1: 知识检索
    knowledge_agent = EnhancedKnowledgeRetrievalAgent()
    knowledge_result = await knowledge_agent.execute({
        "query": query
    })
    evidence = extract_evidence(knowledge_result)
    
    # 步骤2: 推理生成
    reasoning_engine = RealReasoningEngine()
    reasoning_result = await reasoning_engine.reason(
        query,
        {"knowledge": evidence}
    )
    
    # 步骤3: 返回结果
    return ToolResult(
        success=True,
        data={
            "answer": reasoning_result.final_answer,
            "evidence": evidence,
            "reasoning": reasoning_result.reasoning
        }
    )
```

**详细步骤**:

#### 4.1 知识检索（Knowledge Retrieval）

**执行者**: `EnhancedKnowledgeRetrievalAgent`

**流程**:
1. 分析查询类型
2. 确定检索参数（top_k, similarity_threshold）
3. 调用知识库管理系统（KMS）
   - 向量检索（FAISS）
   - 知识图谱检索
   - Rerank重新排序
4. 多维度验证检索结果
5. 返回证据列表

**输出**: 证据列表（evidence）

---

#### 4.2 推理生成（Reasoning Generation）

**执行者**: `RealReasoningEngine`

**流程**:
1. 接收证据和查询
2. 构建增强的Prompt（包含证据）
3. 选择模型（快速模型或推理模型）
4. 调用LLM进行推理
5. 提取和验证答案
6. 返回推理结果

**输出**: 最终答案和推理过程

---

### 阶段5: 结果返回

**流程**:
```python
# ReAct Agent返回AgentResult
agent_result = await react_agent.execute(context)

# 转换为ResearchResult
result = ResearchResult(
    query=request.query,
    answer=agent_result.data["answer"],
    success=agent_result.success,
    confidence=agent_result.confidence,
    execution_time=agent_result.processing_time,
    metadata={
        "method": "react_agent",
        "iterations": agent_result.metadata["react_iterations"],
        "tools_used": agent_result.metadata["tools_used"],
        "thoughts": agent_result.data["thoughts"]
    }
)
```

**输出**: `ResearchResult`对象

---

## 📊 完整流程图

```
┌─────────────────────────────────────────────────────────────┐
│ 阶段1: 样本输入                                              │
│ scripts/run_core_with_frames.py                             │
│   - 加载FRAMES数据集                                         │
│   - 创建UnifiedResearchSystem                                │
│   - 创建ResearchRequest                                      │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 阶段2: UnifiedResearchSystem入口                             │
│ src/unified_research_system.py                              │
│   - 检查缓存                                                 │
│   - [默认] 调用ReAct Agent                                   │
│   - [回退] 传统流程（如果失败）                               │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 阶段3: ReAct Agent执行（核心）                                │
│ src/agents/react_agent.py                                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ReAct循环（最多10次迭代）                              │  │
│  │                                                       │  │
│  │  迭代1:                                               │  │
│  │    [思考] 分析任务，决定需要查询知识库                 │  │
│  │    [规划] 决定调用RAG工具                              │  │
│  │    [行动] 调用RAG工具                                  │  │
│  │    [观察] 接收RAG工具返回的知识和答案                   │  │
│  │                                                       │  │
│  │  迭代2（如果需要）:                                    │  │
│  │    [思考] 分析是否需要更多信息                         │  │
│  │    [规划] 决定调用其他工具（如搜索工具）                │  │
│  │    [行动] 调用工具                                     │  │
│  │    [观察] 接收工具返回结果                             │  │
│  │                                                       │  │
│  │  ...                                                  │  │
│  │                                                       │  │
│  │  [综合] 基于所有观察生成最终答案                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 阶段4: RAG工具执行                                           │
│ src/agents/tools/rag_tool.py                                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 步骤1: 知识检索                                        │  │
│  │   EnhancedKnowledgeRetrievalAgent                     │  │
│  │     - 向量检索（FAISS）                                │  │
│  │     - 知识图谱检索                                     │  │
│  │     - Rerank重新排序                                   │  │
│  │     → 返回证据列表                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                        ↓                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 步骤2: 推理生成                                        │  │
│  │   RealReasoningEngine                                 │  │
│  │     - 构建增强Prompt（包含证据）                       │  │
│  │     - 选择模型（快速/推理）                            │  │
│  │     - 调用LLM推理                                      │  │
│  │     - 提取和验证答案                                   │  │
│  │     → 返回最终答案                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 阶段5: 结果返回                                              │
│   - 转换为ResearchResult                                    │
│   - 包含答案、置信度、元数据等                               │
│   - 返回给调用者                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 ReAct循环详细说明

### 循环条件

- **最大迭代次数**: 10次
- **退出条件**:
  1. 任务完成（`_is_task_complete`返回True）
  2. 达到最大迭代次数
  3. 无法规划行动

### 任务完成判断

**判断逻辑**:
```python
def _is_task_complete(self, thought, observations):
    # 1. 检查思考中是否包含完成关键词
    complete_keywords = ['完成', '足够', '可以生成', '可以回答']
    if any(keyword in thought for keyword in complete_keywords):
        return True
    
    # 2. 检查是否有RAG工具返回了答案
    for obs in observations:
        if (obs.get('tool_name') == 'rag' and 
            obs.get('success') and 
            obs.get('data', {}).get('answer')):
            return True
    
    return False
```

---

## 🎯 关键组件说明

### 1. ReAct Agent

**角色**: 指挥官，负责整体任务规划和执行

**功能**:
- 思考任务状态
- 规划行动步骤
- 调用工具
- 观察结果
- 综合答案

### 2. RAG工具

**角色**: 专业工具，负责知识检索和生成

**功能**:
- 从知识库检索相关信息
- 使用LLM生成答案
- 返回标准化的工具结果

### 3. 工具注册表

**角色**: 工具管理器

**功能**:
- 注册和查找工具
- 管理工具元数据
- 提供工具信息

---

## 📊 数据流

### 输入数据

```python
ResearchRequest(
    query="用户查询文本",
    context={
        "dataset": "FRAMES",
        "sample_id": "样本ID",
        "expected_answer": "期望答案"
    }
)
```

### 中间数据

**ReAct循环中的观察结果**:
```python
observation = {
    "success": True,
    "tool_name": "rag",
    "data": {
        "answer": "答案",
        "evidence": [...],
        "reasoning": "..."
    },
    "execution_time": 10.5
}
```

### 输出数据

```python
ResearchResult(
    query="用户查询文本",
    answer="最终答案",
    success=True,
    confidence=0.8,
    execution_time=15.2,
    metadata={
        "method": "react_agent",
        "iterations": 1,
        "tools_used": ["rag"],
        "thoughts": ["思考过程..."]
    }
)
```

---

## ⚡ 性能特点

### 优势

1. **灵活性**: ReAct循环可以根据任务动态调整执行步骤
2. **可扩展性**: 可以轻松添加新工具
3. **自主决策**: Agent可以自主决定调用哪个工具
4. **多步骤任务**: 支持需要多步操作才能完成的复杂任务

### 性能考虑

1. **循环次数**: 最多10次迭代，避免无限循环
2. **思考时间**: 思考阶段使用快速模型，减少延迟
3. **工具调用**: 工具调用是异步的，可以并行执行
4. **缓存机制**: 查询结果会被缓存，提高重复查询性能

---

## 🔍 与传统流程的对比

### 传统流程（回退路径）

```
用户查询
    ↓
UnifiedResearchSystem
    ├─ Knowledge Agent（知识检索）
    ├─ Reasoning Agent（推理生成）
    ├─ Answer Agent（答案格式化）
    └─ Citation Agent（引用生成）
    ↓
结果
```

**特点**:
- 固定执行顺序
- 所有Agent都会执行
- 没有自主决策能力

### ReAct Agent流程（默认）

```
用户查询
    ↓
ReAct Agent
    ├─ 思考：需要什么？
    ├─ 行动：调用RAG工具
    ├─ 观察：获得结果
    └─ 综合：生成答案
    ↓
结果
```

**特点**:
- 灵活的执行流程
- 根据任务动态调整
- 自主决策能力
- 支持多步骤任务

---

## 📝 示例执行流程

### 示例1: 简单查询

**查询**: "Jane Ballou是谁？"

**执行流程**:
```
迭代1:
  [思考] 需要查询知识库获取Jane Ballou的信息
  [规划] 调用RAG工具
  [行动] RAG工具执行
    - 知识检索：找到Jane Ballou的相关信息
    - 推理生成：生成答案"Jane Ballou是..."
  [观察] 获得答案
  [判断] 任务完成 ✓
  
[综合] 返回答案
```

**迭代次数**: 1次

---

### 示例2: 复杂查询

**查询**: "分析产品A在印尼市场的主要竞争对手"

**执行流程**:
```
迭代1:
  [思考] 需要查询产品A的信息
  [规划] 调用RAG工具查询产品A
  [行动] RAG工具执行
  [观察] 获得产品A的信息
  
迭代2:
  [思考] 需要查询印尼市场的竞争信息
  [规划] 调用RAG工具查询印尼市场
  [行动] RAG工具执行
  [观察] 获得市场信息
  
迭代3:
  [思考] 已有足够信息，可以生成分析报告
  [规划] 不需要调用工具
  [判断] 任务完成 ✓
  
[综合] 综合分析，生成报告
```

**迭代次数**: 2-3次

---

## 🎯 总结

### 当前架构特点

1. **默认使用ReAct Agent架构**
   - 无需配置，自动启用
   - 如果初始化失败，自动回退

2. **ReAct循环机制**
   - 思考-行动-观察循环
   - 最多10次迭代
   - 自主决策工具调用

3. **RAG作为工具**
   - RAG封装为工具
   - 被ReAct Agent调用
   - 返回标准化结果

4. **灵活性和可扩展性**
   - 可以添加新工具
   - 支持复杂多步骤任务
   - 动态调整执行流程

### 处理流程总结

```
样本输入 → UnifiedResearchSystem → ReAct Agent → RAG工具 → 知识检索 + 推理生成 → 最终答案
```

---

**报告生成时间**: 2025-11-27  
**状态**: ✅ 完整流程分析

