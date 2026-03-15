# 核心系统Agent架构设计

**设计时间**: 2025-11-30  
**目标**: 将核心系统改造为符合标准Agent定义的架构

---

## 📋 设计目标

1. **核心系统本身是一个标准的Agent**
   - 有while循环（观察→思考→行动→再观察）
   - 使用LLM进行决策
   - 可以调用工具和其他Agent

2. **其他Agent作为工具使用**
   - KnowledgeRetrievalAgent → KnowledgeRetrievalTool
   - ReasoningAgent → ReasoningTool
   - AnswerGenerationAgent → AnswerGenerationTool
   - CitationAgent → CitationTool

3. **工具系统**
   - RAGTool（RAG工具）
   - SearchTool（搜索工具）
   - CalculatorTool（计算工具）

---

## 🏗️ 架构设计

### 1. 核心系统架构（UnifiedResearchSystem as Agent）

```
UnifiedResearchSystem (标准Agent)
├── 模型（大脑）: LLM Integration
├── 工具注册表: ToolRegistry
│   ├── Agent Tools (将Agent封装为工具)
│   │   ├── KnowledgeRetrievalTool
│   │   ├── ReasoningTool
│   │   ├── AnswerGenerationTool
│   │   └── CitationTool
│   └── Utility Tools (通用工具)
│       ├── RAGTool
│       ├── SearchTool
│       └── CalculatorTool
├── 上下文/记忆: 
│   ├── observations: List[Dict]  # 观察结果
│   ├── thoughts: List[str]       # 思考过程
│   └── actions: List[Action]     # 执行的动作
└── 循环（生命周期）: while循环
    ├── 思考（Think）: 使用LLM分析查询和观察
    ├── 规划行动（Plan Action）: 决定调用哪个工具/Agent
    ├── 执行工具（Act）: 调用工具/Agent
    └── 观察（Observe）: 收集结果，继续循环
```

### 2. Agent循环流程

```python
async def execute_research(self, request: ResearchRequest) -> ResearchResult:
    """执行研究任务 - 标准Agent循环"""
    
    # 初始化状态
    query = request.query
    observations = []
    thoughts = []
    actions = []
    
    # Agent循环
    iteration = 0
    max_iterations = 10
    task_complete = False
    
    while iteration < max_iterations and not task_complete:
        # 1. 思考（Think）
        thought = await self._think(query, observations, thoughts)
        thoughts.append(thought)
        
        # 2. 规划行动（Plan Action）
        action = await self._plan_action(thought, query, observations)
        actions.append(action)
        
        # 3. 执行工具（Act）
        observation = await self._execute_tool(action)
        observations.append(observation)
        
        # 4. 判断是否完成
        task_complete = self._is_task_complete(thought, observations)
        
        iteration += 1
    
    # 5. 生成最终结果
    return self._generate_result(observations, thoughts, actions)
```

---

## 🔧 需要的Agent和工具

### 1. Agent Tools（将Agent封装为工具）

#### 1.1 KnowledgeRetrievalTool

**功能**: 封装`EnhancedKnowledgeRetrievalAgent`，提供知识检索功能

**接口**:
```python
class KnowledgeRetrievalTool(BaseTool):
    """知识检索工具 - 封装EnhancedKnowledgeRetrievalAgent"""
    
    async def call(self, query: str, **kwargs) -> ToolResult:
        """调用知识检索Agent"""
        agent = self._get_knowledge_agent()
        result = await agent.execute({"query": query, **kwargs})
        return ToolResult(
            success=result.success,
            data=result.data,
            error=result.error
        )
```

**工具描述**:
- 名称: `knowledge_retrieval`
- 描述: "从知识库检索相关信息，返回知识条目列表"
- 参数: `query` (必需), `top_k` (可选), `threshold` (可选)

#### 1.2 ReasoningTool

**功能**: 封装`EnhancedReasoningAgent`，提供推理功能

**接口**:
```python
class ReasoningTool(BaseTool):
    """推理工具 - 封装EnhancedReasoningAgent"""
    
    async def call(self, query: str, knowledge: List[Dict] = None, **kwargs) -> ToolResult:
        """调用推理Agent"""
        agent = self._get_reasoning_agent()
        context = {
            "query": query,
            "knowledge": knowledge or [],
            **kwargs
        }
        result = await agent.process_query(query, context)
        return ToolResult(
            success=result.success,
            data=result.data,
            error=result.error
        )
```

**工具描述**:
- 名称: `reasoning`
- 描述: "对查询进行推理分析，生成推理步骤和中间结果"
- 参数: `query` (必需), `knowledge` (可选), `reasoning_type` (可选)

#### 1.3 AnswerGenerationTool

**功能**: 封装`EnhancedAnswerGenerationAgent`，提供答案生成功能

**接口**:
```python
class AnswerGenerationTool(BaseTool):
    """答案生成工具 - 封装EnhancedAnswerGenerationAgent"""
    
    async def call(self, query: str, knowledge: List[Dict] = None, 
                   reasoning: Dict = None, **kwargs) -> ToolResult:
        """调用答案生成Agent"""
        agent = self._get_answer_agent()
        context = {
            "query": query,
            "knowledge": knowledge or [],
            "reasoning": reasoning or {},
            **kwargs
        }
        result = await agent.execute(context)
        return ToolResult(
            success=result.success,
            data=result.data,
            error=result.error
        )
```

**工具描述**:
- 名称: `answer_generation`
- 描述: "基于查询、知识和推理结果生成最终答案"
- 参数: `query` (必需), `knowledge` (可选), `reasoning` (可选)

#### 1.4 CitationTool

**功能**: 封装`EnhancedCitationAgent`，提供引用生成功能

**接口**:
```python
class CitationTool(BaseTool):
    """引用工具 - 封装EnhancedCitationAgent"""
    
    async def call(self, answer: str, knowledge: List[Dict] = None, **kwargs) -> ToolResult:
        """调用引用Agent"""
        agent = self._get_citation_agent()
        context = {
            "answer": answer,
            "knowledge": knowledge or [],
            **kwargs
        }
        result = await agent.execute(context)
        return ToolResult(
            success=result.success,
            data=result.data,
            error=result.error
        )
```

**工具描述**:
- 名称: `citation`
- 描述: "为答案生成引用和来源信息"
- 参数: `answer` (必需), `knowledge` (可选)

---

### 2. Utility Tools（通用工具）

#### 2.1 RAGTool（已存在）

**功能**: 检索增强生成，结合知识检索和答案生成

**工具描述**:
- 名称: `rag`
- 描述: "检索增强生成工具：从知识库检索相关信息，然后使用LLM生成答案"
- 参数: `query` (必需)

#### 2.2 SearchTool（已存在）

**功能**: 网络搜索

**工具描述**:
- 名称: `search`
- 描述: "在网络上搜索相关信息"
- 参数: `query` (必需)

#### 2.3 CalculatorTool（已存在）

**功能**: 数学计算

**工具描述**:
- 名称: `calculator`
- 描述: "执行数学计算"
- 参数: `expression` (必需)

---

## 📊 工具调用流程

### 示例1: 简单查询

```
查询: "What is the capital of France?"

循环1:
  思考: "这是一个简单的事实查询，需要检索知识"
  行动: 调用 knowledge_retrieval(query="What is the capital of France?")
  观察: 返回知识条目列表
  判断: 知识已足够，可以生成答案

循环2:
  思考: "已有知识，可以生成答案"
  行动: 调用 answer_generation(query="...", knowledge=[...])
  观察: 返回答案 "Paris"
  判断: 任务完成
```

### 示例2: 复杂查询

```
查询: "If my future wife has the same first name as the 15th first lady's mother..."

循环1:
  思考: "这是一个复杂的多跳查询，需要先检索知识"
  行动: 调用 knowledge_retrieval(query="15th first lady of the United States")
  观察: 返回知识条目

循环2:
  思考: "需要进一步检索关于first lady's mother的信息"
  行动: 调用 knowledge_retrieval(query="Harriet Lane mother")
  观察: 返回知识条目

循环3:
  思考: "需要推理来连接这些信息"
  行动: 调用 reasoning(query="...", knowledge=[...])
  观察: 返回推理步骤

循环4:
  思考: "需要继续检索第二个部分的信息"
  行动: 调用 knowledge_retrieval(query="second assassinated president's mother")
  观察: 返回知识条目

循环5:
  思考: "现在可以生成最终答案"
  行动: 调用 answer_generation(query="...", knowledge=[...], reasoning={...})
  观察: 返回答案 "Jane Ballou"
  判断: 任务完成
```

---

## 🔄 实现步骤

### 步骤1: 创建Agent Tools

1. 创建`KnowledgeRetrievalTool`
2. 创建`ReasoningTool`
3. 创建`AnswerGenerationTool`
4. 创建`CitationTool`

### 步骤2: 改造UnifiedResearchSystem

1. 添加Agent循环（while循环）
2. 实现`_think`方法（使用LLM进行思考）
3. 实现`_plan_action`方法（使用LLM规划行动）
4. 实现`_execute_tool`方法（执行工具）
5. 实现`_is_task_complete`方法（判断任务是否完成）
6. 实现`_generate_result`方法（生成最终结果）

### 步骤3: 注册工具

1. 在初始化时注册所有Agent Tools
2. 注册所有Utility Tools

### 步骤4: 移除传统流程

1. 移除`_execute_research_internal`方法
2. 移除两阶段执行逻辑（证据积累 → 决策承诺）
3. 统一使用Agent循环

---

## 🎯 核心系统Agent循环实现

### 核心方法

```python
class UnifiedResearchSystem:
    """统一研究系统 - 标准Agent实现"""
    
    def __init__(self):
        # 初始化工具注册表
        self.tool_registry = get_tool_registry()
        
        # Agent状态
        self.observations: List[Dict[str, Any]] = []
        self.thoughts: List[str] = []
        self.actions: List[Action] = []
        
        # LLM客户端（用于思考）
        self.llm_client = LLMIntegration(...)
        
        # 初始化Agent和工具
        self._initialize_agents()
        self._register_tools()
    
    async def execute_research(self, request: ResearchRequest) -> ResearchResult:
        """执行研究任务 - 标准Agent循环"""
        query = request.query
        self.observations = []
        self.thoughts = []
        self.actions = []
        
        # Agent循环
        iteration = 0
        max_iterations = 10
        task_complete = False
        
        while iteration < max_iterations and not task_complete:
            # 1. 思考
            thought = await self._think(query, self.observations, self.thoughts)
            self.thoughts.append(thought)
            
            # 2. 规划行动
            action = await self._plan_action(thought, query, self.observations)
            if not action or not action.tool_name:
                break
            
            self.actions.append(action)
            
            # 3. 执行工具
            observation = await self._execute_tool(action)
            self.observations.append(observation)
            
            # 4. 判断是否完成
            task_complete = self._is_task_complete(thought, self.observations)
            
            iteration += 1
        
        # 5. 生成最终结果
        return self._generate_result(self.observations, self.thoughts, self.actions)
    
    async def _think(self, query: str, observations: List[Dict], thoughts: List[str]) -> str:
        """思考阶段 - 使用LLM分析当前状态"""
        # 构建思考提示词
        prompt = self._build_think_prompt(query, observations, thoughts)
        
        # 调用LLM
        response = await self.llm_client._call_llm(prompt)
        
        return response
    
    async def _plan_action(self, thought: str, query: str, observations: List[Dict]) -> Action:
        """规划行动阶段 - 使用LLM决定调用哪个工具"""
        # 获取可用工具列表
        available_tools = self.tool_registry.list_tools()
        tool_descriptions = self._get_tool_descriptions(available_tools)
        
        # 构建行动规划提示词
        prompt = self._build_plan_action_prompt(thought, query, observations, tool_descriptions)
        
        # 调用LLM
        response = await self.llm_client._call_llm(prompt)
        
        # 解析响应，提取工具名称和参数
        action = self._parse_action_response(response)
        
        return action
    
    async def _execute_tool(self, action: Action) -> Dict[str, Any]:
        """执行工具阶段"""
        tool = self.tool_registry.get_tool(action.tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"工具 {action.tool_name} 不存在"
            }
        
        # 调用工具
        result = await tool.call(**action.params)
        
        return {
            "success": result.success,
            "tool_name": action.tool_name,
            "data": result.data,
            "error": result.error
        }
    
    def _is_task_complete(self, thought: str, observations: List[Dict]) -> bool:
        """判断任务是否完成"""
        # 检查是否有最终答案
        for obs in observations:
            if obs.get("tool_name") == "answer_generation" and obs.get("success"):
                answer = obs.get("data", {}).get("answer", "")
                if answer and len(answer) > 0:
                    return True
        
        return False
    
    def _generate_result(self, observations: List[Dict], thoughts: List[str], 
                        actions: List[Action]) -> ResearchResult:
        """生成最终结果"""
        # 从观察中提取答案
        answer = ""
        knowledge = []
        reasoning = None
        citations = []
        
        for obs in observations:
            if obs.get("tool_name") == "answer_generation" and obs.get("success"):
                answer = obs.get("data", {}).get("answer", "")
            elif obs.get("tool_name") == "knowledge_retrieval" and obs.get("success"):
                knowledge.extend(obs.get("data", {}).get("sources", []))
            elif obs.get("tool_name") == "reasoning" and obs.get("success"):
                reasoning = obs.get("data", {})
            elif obs.get("tool_name") == "citation" and obs.get("success"):
                citations.extend(obs.get("data", {}).get("citations", []))
        
        return ResearchResult(
            query=...,  # 从上下文获取
            success=bool(answer),
            answer=answer,
            knowledge=knowledge,
            reasoning=reasoning,
            citations=citations,
            ...
        )
```

---

## 📋 工具列表总结

### Agent Tools（4个）

1. **KnowledgeRetrievalTool** - 知识检索
2. **ReasoningTool** - 推理
3. **AnswerGenerationTool** - 答案生成
4. **CitationTool** - 引用生成

### Utility Tools（3个）

1. **RAGTool** - 检索增强生成（已存在）
2. **SearchTool** - 网络搜索（已存在）
3. **CalculatorTool** - 数学计算（已存在）

**总计**: 7个工具

---

## 🎯 优势

1. **符合标准Agent定义**: 核心系统本身是一个标准的Agent
2. **灵活性**: 可以根据查询动态决定调用哪些工具
3. **可扩展性**: 可以轻松添加新的工具和Agent
4. **可解释性**: 每个步骤都有思考过程和行动记录
5. **智能性**: 使用LLM进行决策，而不是固定流程

---

**设计完成时间**: 2025-11-30

