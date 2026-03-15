# 完整多智能体系统（MAS）架构方案 - 认知伙伴/导师级别

**设计时间**: 2025-11-30  
**目标**: 将核心系统设计为多智能体系统，达到认知伙伴/导师的能力水平

---

## 📋 方案概述

### 核心愿景

**核心系统是一个多智能体系统（MAS），由首席Agent协调多个专家Agent，达到认知伙伴/导师的能力水平。**

### 能力层级

| 层级 | 名称 | 核心特征 | 当前状态 |
|------|------|----------|----------|
| **基础** | 工具/程序 | 执行预设流程 | ❌ 不符合 |
| **当前** | Agent（智能体） | 感知-决策-行动循环 | ⚠️ 部分符合 |
| **目标** | **多智能体系统** | 多个Agent协作、竞争、协商 | 🎯 **目标** |
| **目标** | **认知伙伴/导师** | 主动协作、引导、教育、赋能 | 🎯 **目标** |

---

## 🏗️ 完整架构设计

### 1. 多智能体系统架构

```
UnifiedResearchSystem (多智能体系统 - MAS)
│
├── 首席Agent (ChiefAgent / Coordinator Agent)
│   ├── 角色: 任务分解、团队组建、协调管理
│   ├── 能力: 战略规划、资源分配、冲突解决
│   ├── 认知能力: 主动协作、引导、教育、赋能
│   └── 循环: Agent级别的思考-规划-协调-观察
│
├── 专家Agent团队 (Expert Agent Team)
│   ├── KnowledgeRetrievalAgent (知识检索专家) ← KnowledgeRetrievalService
│   ├── ReasoningAgent (推理专家) ← ReasoningService
│   ├── AnswerGenerationAgent (答案生成专家) ← AnswerGenerationService
│   ├── CitationAgent (引用专家) ← CitationService
│   ├── AnalysisAgent (分析专家) ← AnalysisService
│   ├── VerificationAgent (验证专家) ← VerificationService
│   └── LearningAgent (学习专家) ← LearningService
│
├── 服务层 (Service Layer)
│   ├── KnowledgeRetrievalService (从EnhancedKnowledgeRetrievalAgent重命名)
│   ├── ReasoningService (从EnhancedReasoningAgent重命名)
│   ├── AnswerGenerationService (从EnhancedAnswerGenerationAgent重命名)
│   ├── CitationService (从EnhancedCitationAgent重命名)
│   └── ... (其他服务)
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

### 2. 组件分类与命名

#### 2.1 真正的Agent（保留命名）

| Agent | 类型 | 说明 |
|-------|------|------|
| **ChiefAgent** | 标准Agent | 首席Agent，协调整个系统 |
| **ExpertAgent** | 标准Agent | 专家Agent基类 |
| **KnowledgeRetrievalAgent** | 标准Agent | 知识检索专家（继承ExpertAgent） |
| **ReasoningAgent** | 标准Agent | 推理专家（继承ExpertAgent） |
| **AnswerGenerationAgent** | 标准Agent | 答案生成专家（继承ExpertAgent） |
| **CitationAgent** | 标准Agent | 引用专家（继承ExpertAgent） |
| **ReActAgent** | 标准Agent | ReAct模式Agent（保留） |

#### 2.2 服务组件（重命名）

| 原名称 | 新名称 | 类型 | 说明 |
|--------|--------|------|------|
| `EnhancedKnowledgeRetrievalAgent` | `KnowledgeRetrievalService` | Service | 知识检索服务（被KnowledgeRetrievalAgent使用） |
| `EnhancedReasoningAgent` | `ReasoningService` | Service | 推理服务（被ReasoningAgent使用） |
| `EnhancedAnswerGenerationAgent` | `AnswerGenerationService` | Service | 答案生成服务（被AnswerGenerationAgent使用） |
| `EnhancedCitationAgent` | `CitationService` | Service | 引用服务（被CitationAgent使用） |

#### 2.3 工具（封装服务）

| 工具名称 | 封装的服务 | 说明 |
|----------|-----------|------|
| `KnowledgeRetrievalTool` | `KnowledgeRetrievalService` | 知识检索工具（可选，用于简单场景） |
| `ReasoningTool` | `ReasoningService` | 推理工具（可选） |
| `AnswerGenerationTool` | `AnswerGenerationService` | 答案生成工具（可选） |
| `CitationTool` | `CitationService` | 引用工具（可选） |

---

## 🎯 首席Agent设计

### ChiefAgent架构

```python
class ChiefAgent(BaseAgent):
    """首席Agent - 协调整个多智能体系统"""
    
    def __init__(self):
        super().__init__(
            agent_id="chief_agent",
            capabilities=["coordination", "task_decomposition", "team_management", 
                         "conflict_resolution", "cognitive_partnership"]
        )
        
        # Agent状态
        self.observations: List[Dict[str, Any]] = []
        self.thoughts: List[str] = []
        self.actions: List[Action] = []
        
        # 专家Agent池
        self.expert_agent_pool: Dict[str, ExpertAgent] = {}
        
        # 工具注册表
        self.tool_registry = get_tool_registry()
        
        # LLM客户端（用于思考和规划）
        self.llm_client = LLMIntegration(...)
        
        # 通信协议
        self.communication_protocol = AgentCommunicationProtocol()
        
        # 认知伙伴能力
        self.cognitive_capabilities = {
            "proactive_collaboration": True,
            "guidance": True,
            "education": True,
            "empowerment": True
        }
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行任务 - 多智能体协作"""
        query = context.get("query", "")
        
        # Agent循环
        iteration = 0
        max_iterations = 15
        task_complete = False
        
        while iteration < max_iterations and not task_complete:
            # 1. 思考（Think）
            thought = await self._think(query, self.observations, self.thoughts)
            self.thoughts.append(thought)
            
            # 2. 任务分解（Decompose）
            if iteration == 0:
                subtasks = await self._decompose_task(query)
                self.observations.append({
                    "type": "task_decomposition",
                    "subtasks": subtasks
                })
            
            # 3. 团队组建（Assemble Team）
            if iteration == 0:
                team = await self._assemble_team(subtasks)
                self.observations.append({
                    "type": "team_assembly",
                    "team": list(team.keys())
                })
            
            # 4. 任务分配（Assign Tasks）
            if iteration == 0:
                task_assignments = await self._assign_tasks(subtasks, team)
                self.observations.append({
                    "type": "task_assignment",
                    "assignments": task_assignments
                })
            
            # 5. 协调执行（Coordinate）
            agent_results = await self._coordinate_execution(task_assignments)
            self.observations.append({
                "type": "coordination",
                "results": agent_results
            })
            
            # 6. 冲突解决（Resolve Conflicts）
            resolved_results = await self._resolve_conflicts(agent_results)
            
            # 7. 结果聚合（Aggregate）
            final_result = await self._aggregate_results(resolved_results)
            
            # 8. 判断是否完成
            task_complete = self._is_task_complete(final_result)
            
            iteration += 1
        
        # 9. 认知伙伴能力
        guidance = await self._guide_user(query, final_result)
        empowerment = await self._empower_user(query, final_result)
        
        return AgentResult(
            success=True,
            data={
                "answer": final_result["answer"],
                "knowledge": final_result["knowledge"],
                "reasoning": final_result["reasoning"],
                "citations": final_result["citations"],
                "guidance": guidance,
                "empowerment": empowerment,
                "agent_collaboration_log": agent_results
            }
        )
```

---

## 🎯 专家Agent设计

### ExpertAgent基类

```python
class ExpertAgent(BaseAgent):
    """专家Agent基类 - 所有专家Agent继承此类"""
    
    def __init__(self, agent_id: str, domain_expertise: str, 
                 capability_level: float = 0.9):
        super().__init__(
            agent_id=agent_id,
            capabilities=[domain_expertise, "collaboration"]
        )
        
        self.domain_expertise = domain_expertise
        self.capability_level = capability_level
        self.collaboration_style = "supportive"
        
        # 对应的Service（封装原有功能）
        self.service = None
        
        # Agent状态
        self.observations: List[Dict[str, Any]] = []
        self.thoughts: List[str] = []
        self.actions: List[Action] = []
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行任务 - 专家Agent循环"""
        query = context.get("query", "")
        dependencies = context.get("dependencies", {})
        
        # Agent循环
        iteration = 0
        max_iterations = 10
        task_complete = False
        
        while iteration < max_iterations and not task_complete:
            # 1. 思考
            thought = await self._think(query, dependencies, self.observations)
            self.thoughts.append(thought)
            
            # 2. 规划行动
            action = await self._plan_action(thought, query, dependencies)
            if not action:
                break
            
            self.actions.append(action)
            
            # 3. 执行（调用Service或工具）
            observation = await self._execute_action(action, dependencies)
            self.observations.append(observation)
            
            # 4. 判断是否完成
            task_complete = self._is_task_complete(observation)
            
            iteration += 1
        
        # 5. 生成结果
        return self._generate_result(self.observations, self.thoughts, self.actions)
    
    async def _execute_action(self, action: Action, dependencies: Dict) -> Dict[str, Any]:
        """执行行动 - 调用Service"""
        if not self.service:
            self.service = self._get_service()
        
        # 准备上下文
        service_context = {
            "query": action.params.get("query", ""),
            **action.params,
            **dependencies
        }
        
        # 调用Service
        result = await self.service.execute(service_context)
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error
        }
    
    def _get_service(self):
        """获取对应的Service - 子类实现"""
        raise NotImplementedError
```

### 具体专家Agent实现

```python
class KnowledgeRetrievalAgent(ExpertAgent):
    """知识检索专家Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id="knowledge_retrieval_expert",
            domain_expertise="知识检索和信息收集",
            capability_level=0.9
        )
        self.collaboration_style = "supportive"
    
    def _get_service(self):
        """获取知识检索服务"""
        from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
        return KnowledgeRetrievalService()


class ReasoningAgent(ExpertAgent):
    """推理专家Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id="reasoning_expert",
            domain_expertise="逻辑推理和问题分析",
            capability_level=0.95
        )
        self.collaboration_style = "analytical"
    
    def _get_service(self):
        """获取推理服务"""
        from src.services.reasoning_service import ReasoningService
        return ReasoningService()


class AnswerGenerationAgent(ExpertAgent):
    """答案生成专家Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id="answer_generation_expert",
            domain_expertise="答案生成和格式化",
            capability_level=0.9
        )
        self.collaboration_style = "synthesizing"
    
    def _get_service(self):
        """获取答案生成服务"""
        from src.services.answer_generation_service import AnswerGenerationService
        return AnswerGenerationService()


class CitationAgent(ExpertAgent):
    """引用专家Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id="citation_expert",
            domain_expertise="引用和来源生成",
            capability_level=0.85
        )
        self.collaboration_style = "supportive"
    
    def _get_service(self):
        """获取引用服务"""
        from src.services.citation_service import CitationService
        return CitationService()
```

---

## 🎯 认知伙伴/导师能力实现

### 1. 主动协作能力

```python
class ChiefAgent:
    async def _think(self, query: str, observations: List[Dict], 
                    thoughts: List[str]) -> str:
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
        
        建议列表（JSON格式）:
        """
        suggestions = await self.llm_client._call_llm(prompt)
        return self._parse_suggestions(suggestions)
```

### 2. 引导与教育能力

```python
class ChiefAgent:
    async def _guide_user(self, query: str, answer: str, 
                         reasoning: Dict) -> Dict[str, Any]:
        """引导用户 - 解释推理过程，教育用户"""
        prompt = f"""
        你是一个导师，需要引导用户理解答案。
        
        用户查询: {query}
        答案: {answer}
        推理过程: {reasoning}
        
        请提供（JSON格式）:
        {{
            "explanation": "答案的解释（为什么是这个答案）",
            "reasoning_breakdown": "推理过程的详细说明",
            "knowledge_education": {{
                "concepts": ["相关概念1", "相关概念2"],
                "principles": ["相关原理1", "相关原理2"],
                "examples": ["示例1", "示例2"]
            }},
            "thinking_guidance": "如何思考类似问题的指导"
        }}
        """
        guidance = await self.llm_client._call_llm(prompt)
        return self._parse_guidance(guidance)
```

### 3. 预测与赋能能力

```python
class ChiefAgent:
    async def _predict_needs(self, query: str, user_history: List[Dict]) -> List[str]:
        """预测需求 - 基于历史行为预测用户需求"""
        prompt = f"""
        基于用户查询: {query}
        历史行为: {user_history}
        
        请预测（JSON格式）:
        {{
            "next_needs": ["可能的下一步需求1", "可能的下一步需求2"],
            "related_info": ["可能需要的相关信息1", "可能需要的相关信息2"],
            "tools_resources": ["可能需要的工具1", "可能需要的工具2"]
        }}
        """
        predictions = await self.llm_client._call_llm(prompt)
        return self._parse_predictions(predictions)
    
    async def _empower_user(self, query: str, answer: str) -> Dict[str, Any]:
        """赋能用户 - 提供工具、资源、方法"""
        prompt = f"""
        基于用户查询: {query}
        答案: {answer}
        
        请提供（JSON格式）:
        {{
            "tools_and_resources": ["工具1", "资源1"],
            "learning_path": {{
                "steps": ["步骤1", "步骤2"],
                "resources": ["资源1", "资源2"]
            }},
            "practice_methods": ["实践方法1", "实践方法2"],
            "advanced_directions": ["进阶方向1", "进阶方向2"]
        }}
        """
        empowerment = await self.llm_client._call_llm(prompt)
        return self._parse_empowerment(empowerment)
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
            if agent_name not in self.expert_agent_pool:
                team[agent_name] = await self._create_expert_agent(agent_name)
                self.expert_agent_pool[agent_name] = team[agent_name]
            else:
                team[agent_name] = self.expert_agent_pool[agent_name]
        
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

### 3. 协调执行机制

```python
class ChiefAgent:
    async def _coordinate_execution(self, task_assignments: Dict) -> Dict[str, Any]:
        """协调执行 - 协调多个Agent的执行"""
        results = {}
        
        # 按依赖关系排序
        sorted_tasks = self._topological_sort(task_assignments.values())
        
        # 并行执行无依赖的任务
        independent_tasks = [t for t in sorted_tasks if not t["task"].dependencies]
        
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
        dependent_tasks = [t for t in sorted_tasks if t["task"].dependencies]
        
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

### 4. Agent间通信机制

```python
class AgentCommunicationProtocol:
    """Agent通信协议"""
    
    def __init__(self):
        self.message_queue = asyncio.Queue()
        self.registered_agents: Dict[str, ExpertAgent] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
    
    async def send_message(self, from_agent: str, to_agent: str, 
                          message: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息"""
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
        for agent_id in self.registered_agents:
            if agent_id != from_agent:
                await self.send_message(from_agent, agent_id, message)
```

---

## 📊 核心系统实现

### UnifiedResearchSystem as MAS

```python
class UnifiedResearchSystem:
    """统一研究系统 - 多智能体系统（MAS）"""
    
    def __init__(self, max_concurrent_queries: int = 3):
        # 首席Agent
        self.chief_agent = ChiefAgent()
        
        # 专家Agent池（由ChiefAgent管理）
        # self.chief_agent.expert_agent_pool
        
        # 通信协议
        self.communication_protocol = AgentCommunicationProtocol()
        
        # 任务管理器
        self.task_manager = TaskManager()
        
        # 并发控制
        self._semaphore = asyncio.Semaphore(max_concurrent_queries)
    
    async def execute_research(self, request: ResearchRequest) -> ResearchResult:
        """执行研究任务 - 多智能体协作"""
        async with self._semaphore:
            # 构建上下文
            context = {
                "query": request.query,
                "context": request.context or {}
            }
            
            # 调用首席Agent执行任务
            agent_result = await self.chief_agent.execute(context)
            
            # 转换为ResearchResult
            if agent_result.success:
                data = agent_result.data
                return ResearchResult(
                    query=request.query,
                    success=True,
                    answer=data.get("answer", ""),
                    knowledge=data.get("knowledge", []),
                    reasoning=data.get("reasoning"),
                    citations=data.get("citations", []),
                    guidance=data.get("guidance"),  # 引导内容
                    empowerment=data.get("empowerment"),  # 赋能内容
                    agent_collaboration_log=data.get("agent_collaboration_log", []),
                    execution_time=agent_result.processing_time
                )
            else:
                return ResearchResult(
                    query=request.query,
                    success=False,
                    error=agent_result.error,
                    execution_time=agent_result.processing_time
                )
```

---

## 📋 完整实施计划

### 阶段1: 服务重命名（Week 1）

- [ ] 创建`src/services/`目录
- [ ] 创建`KnowledgeRetrievalService`（从`EnhancedKnowledgeRetrievalAgent`迁移）
- [ ] 创建`ReasoningService`（从`EnhancedReasoningAgent`迁移）
- [ ] 创建`AnswerGenerationService`（从`EnhancedAnswerGenerationAgent`迁移）
- [ ] 创建`CitationService`（从`EnhancedCitationAgent`迁移）
- [ ] 在原Agent文件中添加别名（向后兼容）

### 阶段2: 专家Agent实现（Week 2）

- [ ] 创建`ExpertAgent`基类
- [ ] 实现`KnowledgeRetrievalAgent`（使用`KnowledgeRetrievalService`）
- [ ] 实现`ReasoningAgent`（使用`ReasoningService`）
- [ ] 实现`AnswerGenerationAgent`（使用`AnswerGenerationService`）
- [ ] 实现`CitationAgent`（使用`CitationService`）

### 阶段3: 首席Agent实现（Week 3）

- [ ] 创建`ChiefAgent`类
- [ ] 实现任务分解机制
- [ ] 实现团队组建机制
- [ ] 实现任务分配机制
- [ ] 实现协调执行机制
- [ ] 实现冲突解决机制

### 阶段4: 通信与协作（Week 4）

- [ ] 实现`AgentCommunicationProtocol`
- [ ] 实现消息传递机制
- [ ] 实现广播机制
- [ ] 实现Agent注册机制

### 阶段5: 认知伙伴能力（Week 5）

- [ ] 实现主动协作能力
- [ ] 实现引导与教育能力
- [ ] 实现预测与赋能能力

### 阶段6: 集成与测试（Week 6）

- [ ] 集成到`UnifiedResearchSystem`
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能测试
- [ ] 用户体验测试

---

## 🎯 总结

### 核心改进

1. ✅ **多智能体系统架构** - 首席Agent + 专家Agent团队
2. ✅ **服务重命名** - 避免命名混淆
3. ✅ **认知伙伴/导师能力** - 主动协作、引导、教育、赋能
4. ✅ **智能协作机制** - 任务分解、团队组建、协调执行、冲突解决
5. ✅ **Agent间通信** - 消息传递、广播、协商

### 能力层级

- **基础**: 工具/程序
- **当前**: Agent（智能体）
- **目标**: **多智能体系统** + **认知伙伴/导师**

---

**方案完成时间**: 2025-11-30

