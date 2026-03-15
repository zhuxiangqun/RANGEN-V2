# 多智能体系统（MAS）架构设计 - 认知伙伴/导师级别

**设计时间**: 2025-11-30  
**目标**: 将核心系统设计为多智能体系统，达到认知伙伴/导师的能力水平

---

## 📋 设计目标

### 核心愿景

**核心系统是一个多智能体系统（MAS），由首席Agent协调多个专家Agent，达到认知伙伴/导师的能力水平。**

### 能力层级

| 层级 | 能力 | 核心特征 |
|------|------|----------|
| **基础** | 工具/程序 | 执行预设流程 |
| **当前** | Agent（智能体） | 感知-决策-行动循环 |
| **目标** | **多智能体系统** | 多个Agent协作、竞争、协商 |
| **目标** | **认知伙伴/导师** | 主动协作、引导、教育、赋能 |

---

## 🏗️ 多智能体系统架构

### 1. 整体架构

```
UnifiedResearchSystem (多智能体系统 - MAS)
│
├── 首席Agent (Chief Agent / Coordinator Agent)
│   ├── 角色: 任务分解、团队组建、协调管理
│   ├── 能力: 战略规划、资源分配、冲突解决
│   └── 循环: Agent级别的思考-规划-协调-观察
│
├── 专家Agent团队 (Expert Agent Team)
│   ├── KnowledgeRetrievalAgent (知识检索专家)
│   ├── ReasoningAgent (推理专家)
│   ├── AnswerGenerationAgent (答案生成专家)
│   ├── CitationAgent (引用专家)
│   ├── AnalysisAgent (分析专家)
│   ├── VerificationAgent (验证专家)
│   └── LearningAgent (学习专家)
│
├── 工具系统 (Tool System)
│   ├── Agent Tools (封装服务)
│   └── Utility Tools (通用工具)
│
└── 通信与协作层 (Communication & Collaboration Layer)
    ├── Agent通信协议
    ├── 任务分配机制
    ├── 结果聚合机制
    └── 冲突解决机制
```

### 2. 首席Agent架构

```
ChiefAgent (首席Agent - 标准Agent)
├── 模型（大脑）: LLM Integration (高级推理模型)
├── 工具注册表: ToolRegistry
│   ├── Expert Agent Tools (专家Agent作为工具)
│   └── Utility Tools (通用工具)
├── 上下文/记忆:
│   ├── observations: List[Dict]  # 观察结果
│   ├── thoughts: List[str]       # 思考过程
│   ├── actions: List[Action]     # 执行的动作
│   ├── agent_team: Dict[str, ExpertAgent]  # 专家Agent团队
│   └── task_decomposition: List[SubTask]   # 任务分解
└── 循环（生命周期）: while循环
    ├── 思考（Think）: 分析任务，制定策略
    ├── 任务分解（Decompose）: 将复杂任务分解为子任务
    ├── 团队组建（Assemble Team）: 选择合适的专家Agent
    ├── 任务分配（Assign Tasks）: 将子任务分配给专家Agent
    ├── 协调执行（Coordinate）: 协调Agent间的协作
    ├── 结果聚合（Aggregate）: 聚合各Agent的结果
    └── 观察（Observe）: 观察执行结果，继续循环
```

### 3. 专家Agent架构

```
ExpertAgent (专家Agent - 标准Agent)
├── 模型（大脑）: LLM Integration (专业模型)
├── 工具注册表: ToolRegistry
│   └── 专业工具 (领域特定工具)
├── 上下文/记忆:
│   ├── observations: List[Dict]
│   ├── thoughts: List[str]
│   └── actions: List[Action]
├── 专业能力:
│   ├── domain_expertise: str  # 专业领域
│   ├── capability_level: float  # 能力水平
│   └── collaboration_style: str  # 协作风格
└── 循环（生命周期）: while循环
    ├── 思考（Think）: 分析子任务
    ├── 规划行动（Plan Action）: 制定执行计划
    ├── 执行工具（Act）: 调用专业工具
    ├── 协作（Collaborate）: 与其他Agent协作
    └── 观察（Observe）: 观察结果，继续循环
```

---

## 🎯 认知伙伴/导师能力设计

### 1. 主动协作能力

**能力描述**: 不仅被动响应，还能主动识别需求、提出建议、协作完成任务

**实现方式**:
```python
class ChiefAgent:
    async def _think(self, query: str, observations: List[Dict], thoughts: List[str]) -> str:
        """思考阶段 - 主动分析需求"""
        prompt = f"""
        你是一个认知伙伴，需要帮助用户完成任务。
        
        当前任务: {query}
        历史观察: {observations}
        思考过程: {thoughts}
        
        请分析：
        1. 用户的核心需求是什么？
        2. 是否有隐含需求？
        3. 是否需要主动提出建议？
        4. 如何更好地协作完成任务？
        
        思考过程:
        """
        return await self.llm_client._call_llm(prompt)
    
    async def _proactive_suggestions(self, query: str, context: Dict) -> List[str]:
        """主动建议 - 识别潜在需求"""
        prompt = f"""
        基于用户查询: {query}
        上下文: {context}
        
        请主动提出：
        1. 可能需要补充的信息
        2. 可能的优化方向
        3. 相关的建议
        
        建议列表:
        """
        suggestions = await self.llm_client._call_llm(prompt)
        return self._parse_suggestions(suggestions)
```

### 2. 引导与教育能力

**能力描述**: 不仅完成任务，还能引导用户思考、教育用户知识

**实现方式**:
```python
class ChiefAgent:
    async def _guide_user(self, query: str, answer: str, reasoning: Dict) -> Dict[str, Any]:
        """引导用户 - 解释推理过程，教育用户"""
        prompt = f"""
        你是一个导师，需要引导用户理解答案。
        
        用户查询: {query}
        答案: {answer}
        推理过程: {reasoning}
        
        请提供：
        1. 答案的解释（为什么是这个答案）
        2. 推理过程的说明（如何得到答案）
        3. 相关知识点的教育（相关概念和原理）
        4. 思考方法的引导（如何思考类似问题）
        
        引导内容:
        """
        guidance = await self.llm_client._call_llm(prompt)
        return {
            "answer": answer,
            "explanation": self._extract_explanation(guidance),
            "reasoning_breakdown": self._extract_reasoning_breakdown(guidance),
            "knowledge_education": self._extract_knowledge_education(guidance),
            "thinking_guidance": self._extract_thinking_guidance(guidance)
        }
```

### 3. 预测与赋能能力

**能力描述**: 预测用户需求，主动提供帮助，赋能用户成长

**实现方式**:
```python
class ChiefAgent:
    async def _predict_needs(self, query: str, user_history: List[Dict]) -> List[str]:
        """预测需求 - 基于历史行为预测用户需求"""
        prompt = f"""
        基于用户查询: {query}
        历史行为: {user_history}
        
        请预测：
        1. 用户可能的下一步需求
        2. 用户可能需要的相关信息
        3. 用户可能需要的工具或资源
        
        预测结果:
        """
        predictions = await self.llm_client._call_llm(prompt)
        return self._parse_predictions(predictions)
    
    async def _empower_user(self, query: str, answer: str) -> Dict[str, Any]:
        """赋能用户 - 提供工具、资源、方法"""
        prompt = f"""
        基于用户查询: {query}
        答案: {answer}
        
        请提供：
        1. 相关的工具和资源
        2. 学习路径建议
        3. 实践方法
        4. 进阶方向
        
        赋能内容:
        """
        empowerment = await self.llm_client._call_llm(prompt)
        return {
            "tools_and_resources": self._extract_tools(empowerment),
            "learning_path": self._extract_learning_path(empowerment),
            "practice_methods": self._extract_practice_methods(empowerment),
            "advanced_directions": self._extract_advanced_directions(empowerment)
        }
```

---

## 🔄 多智能体协作机制

### 1. 任务分解机制

```python
class ChiefAgent:
    async def _decompose_task(self, query: str) -> List[SubTask]:
        """任务分解 - 将复杂任务分解为子任务"""
        prompt = f"""
        请将以下任务分解为可执行的子任务:
        
        任务: {query}
        
        要求:
        1. 每个子任务应该是独立的、可执行的
        2. 子任务之间可能有依赖关系
        3. 子任务应该分配给合适的专家Agent
        
        子任务列表（JSON格式）:
        [
            {{
                "id": "task_1",
                "description": "子任务描述",
                "expert_agent": "knowledge_retrieval",
                "dependencies": [],
                "priority": 1
            }},
            ...
        ]
        """
        response = await self.llm_client._call_llm(prompt)
        return self._parse_subtasks(response)
```

### 2. 团队组建机制

```python
class ChiefAgent:
    async def _assemble_team(self, subtasks: List[SubTask]) -> Dict[str, ExpertAgent]:
        """团队组建 - 根据任务需求组建专家Agent团队"""
        # 分析需要的专家Agent
        required_agents = set()
        for task in subtasks:
            required_agents.add(task.expert_agent)
        
        # 获取或创建专家Agent
        team = {}
        for agent_name in required_agents:
            if agent_name not in self.agent_pool:
                team[agent_name] = await self._create_expert_agent(agent_name)
            else:
                team[agent_name] = self.agent_pool[agent_name]
        
        return team
    
    async def _create_expert_agent(self, agent_name: str) -> ExpertAgent:
        """创建专家Agent"""
        agent_classes = {
            "knowledge_retrieval": KnowledgeRetrievalAgent,
            "reasoning": ReasoningAgent,
            "answer_generation": AnswerGenerationAgent,
            "citation": CitationAgent,
            "analysis": AnalysisAgent,
            "verification": VerificationAgent,
            "learning": LearningAgent
        }
        
        agent_class = agent_classes.get(agent_name)
        if not agent_class:
            raise ValueError(f"Unknown expert agent: {agent_name}")
        
        return agent_class()
```

### 3. 任务分配机制

```python
class ChiefAgent:
    async def _assign_tasks(self, subtasks: List[SubTask], team: Dict[str, ExpertAgent]):
        """任务分配 - 将子任务分配给专家Agent"""
        # 按依赖关系排序
        sorted_tasks = self._topological_sort(subtasks)
        
        # 分配任务
        task_assignments = {}
        for task in sorted_tasks:
            agent = team[task.expert_agent]
            task_assignments[task.id] = {
                "task": task,
                "agent": agent,
                "status": "pending"
            }
        
        return task_assignments
```

### 4. 协调执行机制

```python
class ChiefAgent:
    async def _coordinate_execution(self, task_assignments: Dict) -> Dict[str, Any]:
        """协调执行 - 协调多个Agent的执行"""
        results = {}
        
        # 并行执行无依赖的任务
        independent_tasks = [t for t in task_assignments.values() 
                            if not t["task"].dependencies]
        
        # 创建执行任务
        execution_tasks = []
        for assignment in independent_tasks:
            task = assignment["task"]
            agent = assignment["agent"]
            execution_tasks.append(
                self._execute_subtask(task, agent, results)
            )
        
        # 等待执行完成
        await asyncio.gather(*execution_tasks)
        
        # 执行有依赖的任务
        dependent_tasks = [t for t in task_assignments.values() 
                          if t["task"].dependencies]
        
        for assignment in dependent_tasks:
            task = assignment["task"]
            agent = assignment["agent"]
            
            # 等待依赖任务完成
            await self._wait_for_dependencies(task, results)
            
            # 执行任务
            result = await self._execute_subtask(task, agent, results)
            results[task.id] = result
        
        return results
    
    async def _execute_subtask(self, task: SubTask, agent: ExpertAgent, 
                               context: Dict) -> Dict[str, Any]:
        """执行子任务"""
        # 准备上下文（包含其他Agent的结果）
        agent_context = {
            "query": task.description,
            "dependencies": {dep_id: context[dep_id] 
                           for dep_id in task.dependencies 
                           if dep_id in context}
        }
        
        # 执行Agent
        result = await agent.execute(agent_context)
        
        return {
            "task_id": task.id,
            "agent": agent.agent_id,
            "result": result,
            "status": "completed" if result.success else "failed"
        }
```

### 5. Agent间通信机制

```python
class AgentCommunicationProtocol:
    """Agent通信协议"""
    
    async def send_message(self, from_agent: str, to_agent: str, 
                          message: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息"""
        # 消息格式
        message_packet = {
            "from": from_agent,
            "to": to_agent,
            "type": message.get("type", "request"),
            "content": message.get("content"),
            "timestamp": time.time(),
            "message_id": self._generate_message_id()
        }
        
        # 发送到消息队列
        await self.message_queue.put(message_packet)
        
        # 等待响应
        response = await self._wait_for_response(message_packet["message_id"])
        return response
    
    async def broadcast(self, from_agent: str, message: Dict[str, Any]):
        """广播消息"""
        # 广播给所有Agent
        for agent_id in self.registered_agents:
            if agent_id != from_agent:
                await self.send_message(from_agent, agent_id, message)
```

### 6. 冲突解决机制

```python
class ChiefAgent:
    async def _resolve_conflicts(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """冲突解决 - 解决Agent间的冲突"""
        # 检测冲突
        conflicts = self._detect_conflicts(agent_results)
        
        if not conflicts:
            return agent_results
        
        # 解决冲突
        for conflict in conflicts:
            resolution = await self._resolve_conflict(conflict, agent_results)
            agent_results[conflict["key"]] = resolution
        
        return agent_results
    
    async def _resolve_conflict(self, conflict: Dict, 
                               agent_results: Dict) -> Any:
        """解决单个冲突"""
        prompt = f"""
        检测到Agent间的冲突:
        
        冲突描述: {conflict["description"]}
        Agent A的结果: {conflict["result_a"]}
        Agent B的结果: {conflict["result_b"]}
        
        请分析并解决冲突:
        1. 哪个结果更合理？
        2. 是否可以合并两个结果？
        3. 是否需要重新执行任务？
        
        解决方案:
        """
        resolution = await self.llm_client._call_llm(prompt)
        return self._parse_resolution(resolution)
```

---

## 📊 专家Agent设计

### 1. KnowledgeRetrievalAgent (知识检索专家)

```python
class KnowledgeRetrievalAgent(ExpertAgent):
    """知识检索专家Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id="knowledge_retrieval_expert",
            domain_expertise="知识检索和信息收集",
            capability_level=0.9
        )
        self.collaboration_style = "supportive"  # 支持型协作
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行知识检索任务"""
        query = context.get("query", "")
        dependencies = context.get("dependencies", {})
        
        # 利用其他Agent的结果优化检索
        if dependencies:
            query = self._enhance_query_with_context(query, dependencies)
        
        # 执行检索
        result = await self._retrieve_knowledge(query)
        
        return AgentResult(
            success=True,
            data=result,
            confidence=0.9
        )
```

### 2. ReasoningAgent (推理专家)

```python
class ReasoningAgent(ExpertAgent):
    """推理专家Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id="reasoning_expert",
            domain_expertise="逻辑推理和问题分析",
            capability_level=0.95
        )
        self.collaboration_style = "analytical"  # 分析型协作
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行推理任务"""
        query = context.get("query", "")
        dependencies = context.get("dependencies", {})
        
        # 获取知识检索结果
        knowledge = dependencies.get("knowledge_retrieval", {}).get("result", {})
        
        # 执行推理
        result = await self._perform_reasoning(query, knowledge)
        
        return AgentResult(
            success=True,
            data=result,
            confidence=0.95
        )
```

### 3. AnswerGenerationAgent (答案生成专家)

```python
class AnswerGenerationAgent(ExpertAgent):
    """答案生成专家Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id="answer_generation_expert",
            domain_expertise="答案生成和格式化",
            capability_level=0.9
        )
        self.collaboration_style = "synthesizing"  # 综合型协作
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行答案生成任务"""
        query = context.get("query", "")
        dependencies = context.get("dependencies", {})
        
        # 获取知识检索和推理结果
        knowledge = dependencies.get("knowledge_retrieval", {}).get("result", {})
        reasoning = dependencies.get("reasoning", {}).get("result", {})
        
        # 生成答案
        result = await self._generate_answer(query, knowledge, reasoning)
        
        return AgentResult(
            success=True,
            data=result,
            confidence=0.9
        )
```

---

## 🎯 核心系统实现

### UnifiedResearchSystem as MAS

```python
class UnifiedResearchSystem:
    """统一研究系统 - 多智能体系统（MAS）"""
    
    def __init__(self):
        # 首席Agent
        self.chief_agent = ChiefAgent()
        
        # 专家Agent池
        self.agent_pool: Dict[str, ExpertAgent] = {}
        
        # 通信协议
        self.communication_protocol = AgentCommunicationProtocol()
        
        # 任务管理器
        self.task_manager = TaskManager()
    
    async def execute_research(self, request: ResearchRequest) -> ResearchResult:
        """执行研究任务 - 多智能体协作"""
        # 1. 首席Agent思考和分析
        analysis = await self.chief_agent.think(request.query)
        
        # 2. 任务分解
        subtasks = await self.chief_agent.decompose_task(request.query)
        
        # 3. 团队组建
        team = await self.chief_agent.assemble_team(subtasks)
        
        # 4. 任务分配
        task_assignments = await self.chief_agent.assign_tasks(subtasks, team)
        
        # 5. 协调执行
        agent_results = await self.chief_agent.coordinate_execution(task_assignments)
        
        # 6. 冲突解决
        resolved_results = await self.chief_agent.resolve_conflicts(agent_results)
        
        # 7. 结果聚合
        final_result = await self.chief_agent.aggregate_results(resolved_results)
        
        # 8. 认知伙伴/导师能力
        guidance = await self.chief_agent.guide_user(request.query, final_result)
        empowerment = await self.chief_agent.empower_user(request.query, final_result)
        
        return ResearchResult(
            query=request.query,
            success=True,
            answer=final_result["answer"],
            knowledge=final_result["knowledge"],
            reasoning=final_result["reasoning"],
            citations=final_result["citations"],
            guidance=guidance,  # 引导内容
            empowerment=empowerment,  # 赋能内容
            agent_collaboration_log=agent_results  # Agent协作日志
        )
```

---

## 📋 实施计划

### 阶段1: 基础架构（Week 1-2）

- [ ] 创建`ChiefAgent`类
- [ ] 创建`ExpertAgent`基类
- [ ] 实现Agent通信协议
- [ ] 实现任务分解机制

### 阶段2: 专家Agent（Week 2-3）

- [ ] 实现`KnowledgeRetrievalAgent`
- [ ] 实现`ReasoningAgent`
- [ ] 实现`AnswerGenerationAgent`
- [ ] 实现`CitationAgent`
- [ ] 实现其他专家Agent

### 阶段3: 协作机制（Week 3-4）

- [ ] 实现团队组建机制
- [ ] 实现任务分配机制
- [ ] 实现协调执行机制
- [ ] 实现冲突解决机制

### 阶段4: 认知伙伴能力（Week 4-5）

- [ ] 实现主动协作能力
- [ ] 实现引导与教育能力
- [ ] 实现预测与赋能能力

### 阶段5: 测试和优化（Week 5-6）

- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 用户体验优化

---

## 🎯 总结

### 核心改进

1. ✅ **多智能体系统架构** - 首席Agent + 专家Agent团队
2. ✅ **认知伙伴/导师能力** - 主动协作、引导、教育、赋能
3. ✅ **智能协作机制** - 任务分解、团队组建、协调执行、冲突解决
4. ✅ **Agent间通信** - 消息传递、广播、协商

### 能力层级

- **基础**: 工具/程序
- **当前**: Agent（智能体）
- **目标**: **多智能体系统** + **认知伙伴/导师**

---

**设计完成时间**: 2025-11-30

