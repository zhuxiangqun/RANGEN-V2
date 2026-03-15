# RANGEN AI中台 - 智能需求理解与自动能力构建方案

> **版本**: v1.0  
> **目标**: 将RANGEN打造为纯AI能力中台，支持自然语言需求理解和自动能力生成  
> **参照**: OpenClaw架构

---

## 一、现状分析

### 1.1 已具备能力

| 能力模块 | 现状 | 文件位置 |
|---------|------|----------|
| **Skill触发系统** | ✅ 已实现 - 关键词触发 | `src/agents/skills/skill_trigger.py` |
| **LLM Skill选择** | ✅ 已实现 - AI自动选择 | `src/agents/skills/ai_skill_trigger.py` |
| **Skill自学习** | ✅ 已实现 - 触发词优化 | `src/core/self_learning/skill_trigger_learner.py` |
| **Skill工厂** | ✅ 已实现 - 自动创建Skill | `src/api/skill_factory_routes.py` |
| **自动工作流** | ⚠️ 基础实现 - 关键词匹配 | `src/api/auto_create_routes.py` |
| **Agent编排** | ✅ 已实现 - LangGraph | `src/core/execution_coordinator.py` |

### 1.2 核心问题

```
当前 auto_create_routes.py 使用硬编码关键词匹配：
- ❌ 无法理解语义
- ❌ 无法处理复杂需求
- ❌ 无法自动生成缺失的Skill
- ❌ 无法真正"理解"用户意图

示例问题：
输入: "帮我建立一个软件研发团队，能够完成客户的需求并完成交付"
期望: 系统理解这是一个完整的软件研发团队需求
实际: 只能匹配到"开发"、"测试"等关键词
```

---

## 二、目标架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        应用层 (Apps)                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │  聊天应用     │  │  管理平台    │  │  门户入口    │  │  治理面板   ││
│  │ chat_app    │  │management_app│  │  entry_app  │  │governance  ││
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘│
└─────────┼──────────────────┼──────────────────┼─────────────────┼───────┘
          │                  │                  │                  │
          ▼                  ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    RANGEN AI能力中台 (Core)                              │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    自然语言理解层 (NLU)                             ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ ││
│  │  │ 需求解析器   │  │ 意图识别器    │  │ 语义理解引擎             │ ││
│  │  │(Requirement) │  │ (Intent)     │  │ (Semantic)              │ ││
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    能力匹配层 (Capability Matching)                 ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ ││
│  │  │ Skill触发器   │  │ 能力检查器    │  │ Skill工厂               │ ││
│  │  │(Trigger)     │  │ (Checker)    │  │ (Factory)              │ ││
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    执行编排层 (Orchestration)                       ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ ││
│  │  │ Agent协调器   │  │ 工作流引擎    │  │ 工具系统                │ ││
│  │  │(Coordinator) │  │ (LangGraph)  │  │ (15+ Tools)            │ ││
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心流程

```
用户输入: "帮我建立一个软件研发团队，能够完成客户的需求并完成交付"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  步骤1: 需求理解 (Natural Language Understanding)                   │
├─────────────────────────────────────────────────────────────────────┤
│  • 语义解析: 识别出这是一个"软件研发团队"需求                         │
│  • 意图分类: [创建团队] + [完整交付流程]                            │
│  • 实体提取: 角色(产品经理、开发者、QA、架构师...)                   │
│  • 流程推理: 需求→设计→开发→测试→交付                              │
│  • 输出: 结构化需求JSON                                             │
└─────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  步骤2: 能力匹配 (Capability Matching)                              │
├─────────────────────────────────────────────────────────────────────┤
│  检查现有Skills:                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ ✓ code_executor  - 可用                                        ││
│  │ ✓ file_manager   - 可用                                        ││
│  │ ✓ search         - 可用                                        ││
│  │ ✓ rag-retrieval - 可用                                        ││
│  │ ✗ requirement_analysis - 缺失 → 需要创建                      ││
│  │ ✗ team_collaboration - 缺失 → 需要创建                         ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  步骤3: 自动构建 (Auto-Build)                                        │
├─────────────────────────────────────────────────────────────────────┤
│  对于缺失的能力，调用Skill工厂自动创建:                               │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 3.1 创建 Skill: requirement_analysis                            ││
│  │     - 工具: search + file_manager                               ││
│  │     - 提示词: [自动生成]                                        ││
│  │                                                                  ││
│  │ 3.2 创建 Skill: team_collaboration                             ││
│  │     - 工具: message_bus + state_manager                        ││
│  │     - 提示词: [自动生成]                                        ││
│  │                                                                  ││
│  │ 3.3 创建 Agent: 软件研发团队                                     ││
│  │     - 包含: PM + Dev + QA + Architect                          ││
│  │     - 工作流: 需求分析 → 技术设计 → 开发 → 测试 → 交付           ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  步骤4: 执行与反馈 (Execution & Feedback)                           │
├─────────────────────────────────────────────────────────────────────┤
│  • 自动执行工作流                                                    │
│  • 实时推送执行状态                                                  │
│  • 学习用户反馈，优化触发词                                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、关键技术实现

### 3.1 需求理解引擎 (NLU Engine)

**文件**: `src/core/nlu/requirement_understanding.py` (新建)

```python
class RequirementUnderstandingEngine:
    """需求理解引擎 - 替代硬编码关键词匹配"""
    
    def __init__(self, llm_service):
        self.llm = llm_service
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.flow_reasoner = FlowReasoner()
    
    async def understand(self, user_input: str) -> RequirementAnalysis:
        """
        理解用户自然语言需求
        
        输入: "帮我建立一个软件研发团队，能够完成客户的需求并完成交付"
        输出:
        {
            "intent": "create_team",
            "domain": "software_development",
            "roles": ["product_manager", "architect", "developer", "qa"],
            "workflow": ["需求分析", "技术设计", "开发", "测试", "交付"],
            "complexity": "high",
            "required_skills": ["requirement_analysis", "code_generation", "testing"],
            "missing_skills": ["team_collaboration"]
        }
        """
        # 1. 意图分类
        intent = await self.intent_classifier.classify(user_input)
        
        # 2. 实体提取
        entities = await self.entity_extractor.extract(user_input)
        
        # 3. 流程推理
        workflow = await self.flow_reasoner.reason(user_input, entities)
        
        # 4. 能力分析
        capability_analysis = await self._analyze_capabilities(entities, workflow)
        
        return RequirementAnalysis(
            intent=intent,
            entities=entities,
            workflow=workflow,
            capability_analysis=capability_analysis
        )
```

### 3.2 意图分类器 (Intent Classifier)

```python
class IntentClassifier:
    """意图分类 - 使用LLM理解用户真正意图"""
    
    PROMPT_TEMPLATE = """
    你是一个需求分析师。请分析用户的自然语言输入，识别其核心意图。
    
    用户输入: {user_input}
    
    请从以下意图类型中选择最合适的:
    - create_team: 创建协作团队
    - execute_task: 执行特定任务
    - build_system: 构建系统/应用
    - analyze_problem: 分析问题
    - improve_code: 改进代码
    - create_knowledge: 创建知识库
    - train_model: 训练/微调模型
    - general_chat: 一般对话
    
    同时评估:
    - 复杂度 (low/medium/high)
    - 是否需要多角色协作
    - 期望的输出形式
    
    输出JSON格式:
    """
    
    async def classify(self, user_input: str) -> IntentResult:
        # 调用LLM进行意图识别
        response = await self.llm.agenerate(
            prompt=self.PROMPT_TEMPLATE.format(user_input=user_input)
        )
        return IntentResult.parse_json(response)
```

### 3.3 能力检查与自动构建

**文件**: `src/core/capability/capability_checker.py` (扩展现有)

```python
class CapabilityMatcher:
    """能力匹配器 - 检查并自动构建缺失能力"""
    
    def __init__(self):
        self.skill_registry = get_skill_registry()
        self.skill_factory = get_skill_factory()
        self.agent_builder = get_agent_builder()
    
    async def match(self, requirement: RequirementAnalysis) -> CapabilityMatchResult:
        """匹配需求与现有能力，识别缺失部分"""
        
        required_skills = requirement.capability_analysis.required_skills
        
        # 检查现有Skills
        available_skills = []
        missing_skills = []
        
        for skill_name in required_skills:
            if self.skill_registry.exists(skill_name):
                available_skills.append(skill_name)
            else:
                missing_skills.append(skill_name)
        
        # 检查现有Agents
        required_roles = requirement.entities.roles
        available_agents = []
        missing_agents = []
        
        for role in required_roles:
            if self.agent_registry.exists(role):
                available_agents.append(role)
            else:
                missing_agents.append(role)
        
        return CapabilityMatchResult(
            available_skills=available_skills,
            missing_skills=missing_skills,
            available_agents=available_agents,
            missing_agents=missing_agents,
            can_use_existing=len(missing_skills) == 0 and len(missing_agents) == 0
        )
    
    async def auto_build(self, match_result: CapabilityMatchResult) -> BuildResult:
        """自动构建缺失的能力"""
        
        built_items = []
        
        # 1. 创建缺失的Skills
        for skill_name in match_result.missing_skills:
            skill_def = await self._generate_skill_definition(skill_name)
            skill = await self.skill_factory.create_skill(skill_def)
            built_items.append(f"Skill: {skill_name}")
        
        # 2. 创建缺失的Agents
        for agent_name in match_result.missing_agents:
            agent_def = await self._generate_agent_definition(agent_name)
            agent = await self.agent_builder.build(agent_def)
            built_items.append(f"Agent: {agent_name}")
        
        return BuildResult(
            success=True,
            built_items=built_items,
            message=f"已自动构建: {', '.join(built_items)}"
        )
```

---

## 四、API设计

### 4.1 核心API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/understand` | POST | 理解自然语言需求 |
| `/api/v1/capability/match` | POST | 匹配现有能力 |
| `/api/v1/capability/auto-build` | POST | 自动构建缺失能力 |
| `/api/v1/team/create` | POST | 创建协作团队 |
| `/api/v1/team/execute` | POST | 执行团队任务 |
| `/api/v1/workflow/create` | POST | 从需求创建工作流 |

### 4.2 请求/响应示例

**POST /api/v1/understand**

```json
// Request
{
    "query": "帮我建立一个软件研发团队，能够完成客户的需求并完成交付"
}

// Response
{
    "success": true,
    "analysis": {
        "intent": "create_team",
        "domain": "software_development",
        "complexity": "high",
        "roles": [
            {"name": "product_manager", "confidence": 0.95},
            {"name": "architect", "confidence": 0.92},
            {"name": "developer", "confidence": 0.98},
            {"name": "qa", "confidence": 0.90}
        ],
        "workflow": [
            "需求分析",
            "技术设计", 
            "代码开发",
            "测试验证",
            "交付部署"
        ],
        "required_skills": [
            "requirement_analysis",
            "technical_design",
            "code_generation",
            "testing",
            "deployment"
        ],
        "missing_skills": [
            "requirement_analysis",
            "team_collaboration"
        ]
    }
}
```

**POST /api/v1/team/create**

```json
// Request
{
    "description": "帮我建立一个软件研发团队，能够完成客户的需求并完成交付",
    "auto_execute": true
}

// Response
{
    "success": true,
    "team_id": "team_abc123",
    "team_name": "软件研发团队",
    "members": [
        {
            "name": "product_manager",
            "role": "Product Manager",
            "skills": ["requirement_analysis", "priority_ranking"],
            "tools": ["search", "file_manager"]
        },
        {
            "name": "architect",
            "role": "System Architect", 
            "skills": ["technical_design", "architecture_review"],
            "tools": ["search", "file_manager"]
        },
        {
            "name": "developer",
            "role": "Developer",
            "skills": ["code_generation", "code_review", "refactoring"],
            "tools": ["code_executor", "file_manager", "search"]
        },
        {
            "name": "qa",
            "role": "QA Engineer",
            "skills": ["test_generation", "test_execution", "bug_reporting"],
            "tools": ["code_executor", "file_manager"]
        }
    ],
    "workflow": "需求分析 → 技术设计 → 代码开发 → 测试验证 → 交付部署",
    "execution_id": "exec_xyz789",
    "message": "✅ 已创建软件研发团队，包含4个角色"
}
```

---

## 五、实施计划

### 5.1 阶段划分

| 阶段 | 时间 | 任务 | 产出 |
|------|------|------|------|
| **Phase 1** | 第1周 | 需求理解引擎 | `src/core/nlu/` 模块 |
| **Phase 2** | 第2周 | 能力匹配器 | 增强 `capability_checker.py` |
| **Phase 3** | 第3周 | 自动构建集成 | 打通 Skill工厂 + Agent工厂 |
| **Phase 4** | 第4周 | API整合 | 统一 `/api/v1/understand` 端点 |
| **Phase 5** | 第5周 | 前端集成 | 管理平台界面升级 |
| **Phase 6** | 第6周 | 测试优化 | 全面测试 + 性能优化 |

### 5.2 详细任务

#### Phase 1: 需求理解引擎 (第1周)

| 任务 | 文件 | 说明 |
|------|------|------|
| T1.1 | 新建 `src/core/nlu/__init__.py` | NLU模块初始化 |
| T1.2 | 新建 `src/core/nlu/requirement_understanding.py` | 需求理解引擎 |
| T1.3 | 新建 `src/core/nlu/intent_classifier.py` | 意图分类器 |
| T1.4 | 新建 `src/core/nlu/entity_extractor.py` | 实体提取器 |
| T1.5 | 新建 `src/core/nlu/flow_reasoner.py` | 流程推理器 |
| T1.6 | 新建 `src/core/nlu/prompts.py` | NLU提示词模板 |

#### Phase 2: 能力匹配器 (第2周)

| 任务 | 文件 | 说明 |
|------|------|------|
| T2.1 | 扩展 `src/core/capability_checker.py` | 支持Skill缺失检测 |
| T2.2 | 新建 `src/core/capability/skill_matcher.py` | Skill匹配逻辑 |
| T2.3 | 新建 `src/core/capability/agent_matcher.py` | Agent匹配逻辑 |
| T2.4 | 新建 `src/core/capability/workflow_builder.py` | 工作流构建器 |

#### Phase 3: 自动构建集成 (第3周)

| 任务 | 文件 | 说明 |
|------|------|------|
| T3.1 | 集成 `src/api/skill_factory_routes.py` | Skill自动创建 |
| T3.2 | 集成 `src/api/agents.py` | Agent自动创建 |
| T3.3 | 新建 `src/core/capability/auto_builder.py` | 自动构建编排器 |
| T3.4 | 新建 `src/core/nlu/skill_template_gen.py` | Skill模板生成 |

#### Phase 4: API整合 (第4周)

| 任务 | 文件 | 说明 |
|------|------|------|
| T4.1 | 新建 `src/api/understand_routes.py` | 理解API |
| T4.2 | 扩展 `src/api/team_routes.py` | 团队API |
| T4.3 | 扩展 `src/api/auto_create_routes.py` | 整合到统一入口 |
| T4.4 | 更新 `src/api/server.py` | 注册新路由 |

#### Phase 5: 前端集成 (第5周)

| 任务 | 文件 | 说明 |
|------|------|------|
| T5.1 | 扩展 `apps/management_app/` | 能力管理界面 |
| T5.2 | 新建 `apps/chat_app/` | 自然语言创建界面 |
| T5.3 | 添加SSE实时反馈 | 执行状态推送 |

#### Phase 6: 测试优化 (第6周)

| 任务 | 说明 |
|------|------|
| T6.1 | 单元测试 - NLU模块 |
| T6.2 | 集成测试 - API端点 |
| T6.3 | E2E测试 - 完整流程 |
| T6.4 | 性能优化 - 缓存/并发 |

---

## 六、代码示例

### 6.1 入口: /api/v1/understand

```python
# src/api/understand_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.core.nlu.requirement_understanding import RequirementUnderstandingEngine
from src.core.capability.capability_matcher import CapabilityMatcher

router = APIRouter(prefix="/api/v1", tags=["understanding"])

class UnderstandRequest(BaseModel):
    query: str
    include_capabilities: bool = True

class UnderstandResponse(BaseModel):
    success: bool
    analysis: dict
    capabilities: dict = None

@router.post("/understand", response_model=UnderstandResponse)
async def understand_requirement(request: UnderstandRequest):
    """理解自然语言需求"""
    
    # 1. 初始化引擎
    nlu_engine = RequirementUnderstandingEngine()
    matcher = CapabilityMatcher()
    
    # 2. 理解需求
    analysis = await nlu_engine.understand(request.query)
    
    response_data = {
        "success": True,
        "analysis": analysis.to_dict()
    }
    
    # 3. 如果需要，分析能力匹配
    if request.include_capabilities:
        match_result = await matcher.match(analysis)
        response_data["capabilities"] = match_result.to_dict()
    
    return response_data
```

### 6.2 入口: /api/v1/team/create

```python
# src/api/team_routes.py
@router.post("/team/create", response_model=TeamCreateResponse)
async def create_team(request: TeamCreateRequest):
    """从自然语言需求创建协作团队"""
    
    # 1. 理解需求
    nlu_engine = RequirementUnderstandingEngine()
    analysis = await nlu_engine.understand(request.description)
    
    # 2. 能力匹配
    matcher = CapabilityMatcher()
    match_result = await matcher.match(analysis)
    
    # 3. 如果有缺失能力，自动构建
    if not match_result.can_use_existing:
        build_result = await matcher.auto_build(match_result)
        # 重新匹配
        match_result = await matcher.match(analysis)
    
    # 4. 创建团队
    team = await team_builder.build(
        name=analysis.entities.team_name,
        roles=analysis.entities.roles,
        workflow=analysis.workflow
    )
    
    # 5. 如果需要，自动执行
    execution_id = None
    if request.auto_execute:
        execution = await team_executor.execute(team, request.task)
        execution_id = execution.id
    
    return TeamCreateResponse(
        success=True,
        team_id=team.id,
        team_name=team.name,
        members=[r.to_dict() for r in team.members],
        workflow=analysis.workflow,
        execution_id=execution_id
    )
```

---

## 七、使用示例

### 7.1 Python SDK 调用

```python
from rangen import RangenClient

client = RangenClient(api_key="your_key")

# 方式1: 理解需求
result = client.understand("帮我建立一个软件研发团队")
print(result["analysis"]["roles"])
# 输出: ["product_manager", "architect", "developer", "qa"]

# 方式2: 直接创建团队
team = client.team.create(
    description="帮我建立一个软件研发团队，能够完成客户的需求并完成交付",
    auto_execute=True
)
print(team["message"])
# 输出: "✅ 已创建软件研发团队，包含4个角色"
```

### 7.2 cURL 调用

```bash
# 理解需求
curl -X POST http://localhost:8000/api/v1/understand \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_key" \
  -d '{"query": "帮我建立一个软件研发团队，能够完成客户的需求并完成交付"}'

# 创建团队
curl -X POST http://localhost:8000/api/v1/team/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_key" \
  -d '{"description": "帮我建立一个软件研发团队", "auto_execute": true}'
```

---

## 八、与现有系统集成

### 8.1 复用现有组件

| 现有组件 | 复用方式 |
|----------|----------|
| `AISkillTrigger` | 用于Skill触发决策 |
| `SkillTriggerLearner` | 用于学习用户反馈，优化触发词 |
| `skill_factory_routes.py` | 直接调用Skill创建 |
| `ExecutionCoordinator` | 用于执行工作流 |
| LangGraph | 用于定义工作流 |

### 8.2 配置修改

```python
# src/core/nlu/requirement_understanding.py
from src.agents.skills.ai_skill_trigger import AISkillTrigger
from src.services.llm_service import get_llm_service

class RequirementUnderstandingEngine:
    def __init__(self):
        self.llm = get_llm_service()
        # 复用现有的LLM服务
```

---

## 九、预期效果

### 9.1 效果对比

| 维度 | 改造前 | 改造后 |
|------|--------|--------|
| **需求理解** | 关键词匹配 | LLM语义理解 |
| **角色识别** | 固定几种 | 动态识别 |
| **流程生成** | 固定模板 | 智能推理 |
| **能力缺失** | 报错退出 | 自动创建 |
| **用户输入** | 需要了解系统 | 自然语言 |

### 9.2 示例对比

**输入**: "帮我建立一个软件研发团队，能够完成客户的需求并完成交付"

| 维度 | 改造前 | 改造后 |
|------|--------|--------|
| 角色识别 | ["developer", "qa"] (关键词匹配) | ["PM", "架构师", "开发者", "QA"] (语义理解) |
| 流程 | ["需求分析", "开发", "测试"] (硬编码) | ["需求分析", "技术设计", "开发", "测试", "交付"] (推理) |
| Skill缺失 | 报错 | 自动创建 |

---

## 十、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| LLM理解错误 | 创建错误的团队 | 增加用户确认环节 |
| 自动创建质量 | Skill/Agent不符合预期 | 提供编辑/删除功能 |
| 执行安全 | 自动执行可能有风险 | 增加沙箱和安全检查 |
| 性能 | NLU增加延迟 | 缓存 + 异步处理 |

---

## 十一、下一步

1. **确认方案** - 请确认以上方案是否符合预期
2. **开始Phase 1** - 需求理解引擎开发
3. **持续迭代** - 根据实际使用反馈优化

---

*方案版本: v1.0*  
*生成时间: 2026-03-15*
