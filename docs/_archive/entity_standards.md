# RANGEN 基盘实体标准定义

> 详细说明 Agent、Skill、Tool、Workflow、Team 等实体的标准定义

---

## 目录

1. [Agent 标准](#1-agent-标准)
2. [Skill 标准](#2-skill-标准)
3. [Tool 标准](#3-tool-标准)
4. [Workflow 标准](#4-workflow-标准)
5. [Team 标准](#5-team-标准)
6. [Service 标准](#6-service-标准)

---

## 1. Agent 标准

### 1.1 Agent 能力定义

**文件**: `src/agents/agent_models.py`

```python
class AgentCapability(Enum):
    """Agent 必须具备的能力枚举"""
    
    # 核心能力
    EXTENSIBILITY = "extensibility"           # 可扩展性
    INTELLIGENCE = "intelligence"           # 智能性
    AUTONOMOUS_DECISION = "autonomous_decision"  # 自主决策
    DYNAMIC_STRATEGY = "dynamic_strategy"    # 动态策略
    STRATEGY_LEARNING = "strategy_learning"  # 策略学习
    SELF_LEARNING = "self_learning"          # 自学习
    AUTOMATIC_REASONING = "automatic_reasoning"  # 自动推理
    DYNAMIC_CONFIDENCE = "dynamic_confidence"  # 动态置信度
    LLM_DRIVEN_RECOGNITION = "llm_driven_recognition"  # LLM 驱动识别
    DYNAMIC_CHAIN_OF_THOUGHT = "dynamic_chain_of_thought"  # 动态思维链
    DYNAMIC_CLASSIFICATION = "dynamic_classification"  # 动态分类
```

### 1.2 Agent 配置标准

```python
@dataclass
class AgentConfig:
    """Agent 必须的配置项"""
    
    # 必须字段
    agent_id: str              # 唯一标识
    agent_type: str = "generic"  # 类型
    
    # 可选字段
    enabled: bool = True       # 是否启用
    priority: int = 5          # 优先级 (1-10)
    timeout: float = 30.0       # 超时时间 (秒)
    retry_count: int = 3       # 重试次数
    confidence_threshold: float = 0.7  # 置信度阈值
    max_retries: int = 3       # 最大重试次数
    use_intelligent_config: bool = True  # 使用智能配置
```

### 1.3 Agent 状态定义

```python
@dataclass
class AgentState:
    """Agent 必须维护的状态"""
    
    agent_id: str              # Agent ID
    status: str                # 状态 (initialized/running/idle/error)
    last_activity: float       # 最后活动时间 (timestamp)
    performance_metrics: Dict[str, float]  # 性能指标
    capabilities: List[str]    # 已启用能力列表
```

### 1.4 Agent 实现标准

| 标准项 | 要求 | 文件位置 |
|--------|------|----------|
| **基类** | 必须继承 `BaseAgent` 或实现 `IAgent` | `src/agents/base_agent.py` |
| **执行方法** | 必须实现 `async execute()` | 接口定义 |
| **配置管理** | 使用 `AgentConfigManager` | `src/agents/agent_config_manager.py` |
| **性能追踪** | 使用 `AgentPerformanceTracker` | `src/agents/agent_performance_tracker.py` |
| **历史记录** | 使用 `AgentHistoryManager` | `src/agents/agent_history_manager.py` |

### 1.5 Agent 类型体系

```
Agent 继承层次
==============

BaseAgent (抽象基类)
    │
    ├── ReActAgent (推理 Agent)
    │       │
    │       ├── EnhancedReActAgent (增强推理)
    │       ├── SelfLearningReActAgent (自学习)
    │       └── HookedReActAgent (带钩子)
    │
    ├── ExpertAgent (专家 Agent)
    │       │
    │       ├── ReasoningExpert (推理专家)
    │       ├── RAGExpert (RAG 专家)
    │       ├── SecurityGuardian (安全守护)
    │       └── ... (其他专家)
    │
    └── 特定领域 Agent
            │
            ├── JapanMarketAgent (日本市场)
            │       ├── JapanFinancialExpert
            │       ├── JapanLegalAdvisor
            │       └── ...
            │
            ├── ChinaMarketAgent (中国市场)
            │
            └── ProfessionalAgentBase (专业团队)
                    ├── EngineeringAgent
                    ├── TestingAgent
                    ├── MarketingAgent
                    └── DesignAgent
```

---

## 2. Skill 标准

### 2.1 Skill 作用域

```python
class SkillScope(str, Enum):
    """Skill 作用域定义"""
    
    BUNDLED = "bundled"     # 内置 Skill (系统自带)
    MANAGED = "managed"     # 托管 Skill (用户创建，系统管理)
    WORKSPACE = "workspace" # 工作区 Skill (用户私有)
```

### 2.2 Skill 类别

```python
class SkillCategory(str, Enum):
    """Skill 类别定义"""
    
    CODE = "code"           # 代码生成
    DOCUMENT = "document"   # 文档处理
    ANALYSIS = "analysis"   # 分析
    WRITING = "writing"    # 写作
    REASONING = "reasoning" # 推理
    RETRIEVAL = "retrieval"  # 检索
    TOOL = "tool"          # 工具执行
    WORKFLOW = "workflow"  # 工作流
    GENERAL = "general"    # 通用
```

### 2.3 Skill 元数据标准

```python
@dataclass
class SkillMetadata:
    """Skill 必须的元数据"""
    
    # 必须字段
    name: str               # 名称
    version: str = "1.0.0" # 版本
    
    # 推荐字段
    description: str = ""   # 描述
    author: str = ""       # 作者
    category: SkillCategory = SkillCategory.GENERAL  # 类别
    tags: List[str] = []   # 标签
    scope: SkillScope = SkillScope.BUNDLED  # 作用域
    dependencies: List[str] = []  # 依赖
```

### 2.4 Skill 实现标准

| 标准项 | 要求 | 文件位置 |
|--------|------|----------|
| **基类** | 必须继承 `Skill` 抽象类 | `src/agents/skills/__init__.py` |
| **执行方法** | 必须实现 `async execute(context)` | 接口定义 |
| **Schema** | 必须实现 `get_schemas()` | 接口定义 |
| **工具注册** | 使用 `register_tool()` | 基类提供 |
| **验证** | 实现 `validate()` | 基类提供(可选重写) |

### 2.5 Skill 类型

```
Skill 实现类型
==============

Skill (抽象基类)
    │
    ├── DynamicSkill (动态 Skill - 配置驱动)
    │       └── 通过配置定义行为
    │
    ├── PythonSkill (Python Skill - 代码驱动)
    │       └── 加载 Python 模块
    │
    └── 自定义 Skill
            └── 继承 Skill 实现具体逻辑
```

---

## 3. Tool 标准

### 3.1 Tool 类别

```python
class ToolCategory(Enum):
    """Tool 类别定义"""
    
    RETRIEVAL = "retrieval"   # 检索类
    COMPUTE = "compute"        # 计算类
    UTILITY = "utility"        # 工具类
    API = "api"                # API 调用类
```

### 3.2 Tool 结果标准

```python
@dataclass
class ToolResult:
    """Tool 执行结果标准"""
    
    success: bool           # 是否成功
    data: Any              # 返回数据
    error: Optional[str] = None    # 错误信息
    metadata: Dict = {}    # 元数据
    execution_time: float = 0.0   # 执行时间
    timestamp: datetime = None      # 时间戳
```

### 3.3 Tool 实现标准

| 标准项 | 要求 | 文件位置 |
|--------|------|----------|
| **基类** | 必须继承 `BaseTool` | `src/agents/tools/base_tool.py` |
| **调用方法** | 必须实现 `async call(**kwargs)` | 接口定义 |
| **参数 Schema** | 必须实现 `get_parameters_schema()` | 接口定义 |
| **结果格式** | 返回 `ToolResult` | 接口定义 |

### 3.4 Tool 类型体系

```
Tool 继承层次
=============

BaseTool (抽象基类)
    │
    ├── CalculatorTool (计算器)
    ├── SearchTool (搜索)
    ├── RetrievalTool (检索)
    ├── FileTool (文件操作)
    ├── BrowserTool (浏览器)
    ├── APITool (API 调用)
    └── ReasoningTool (推理)
```

---

## 4. Workflow 标准

### 4.1 生产环境 Workflow

**实际使用的 Workflow**: `ExecutionCoordinator`

```python
class ExecutionCoordinator:
    """生产环境使用的轻量级协调器"""
    
    # 5 个核心节点
    nodes = ["router", "direct_executor", "reasoning_engine", "quality_evaluator", "error_handler"]
    
    # 基于 LangGraph StateGraph
    graph = StateGraph(AgentState)
```

### 4.2 Workflow 状态定义

```python
class AgentState(TypedDict):
    """轻量级状态"""
    query: str
    context: Dict[str, Any]
    route: str
    steps: Annotated[list, operator.add]
    final_answer: str
    error: str
    quality_score: float
    quality_passed: bool
    quality_feedback: str
    retry_count: int
```

### 4.3 Workflow 类型

| 类型 | 文件 | 状态 | 说明 |
|------|------|------|------|
| ExecutionCoordinator | `execution_coordinator.py` | **生产使用** | 轻量级，5 个节点 |
| UnifiedWorkflow | `langgraph_unified_workflow.py` | 未使用 | 完整版，60+ 字段 |
| LayeredWorkflow | `langgraph_layered_workflow.py` | 未使用 | 分层架构 |
| SimplifiedWorkflow | `simplified_*.py` | 未使用 | 简化版 |

### 4.4 Workflow 实现标准

| 标准项 | 要求 |
|--------|------|
| **状态管理** | 使用 `TypedDict` 定义状态 |
| **节点定义** | 明确输入/输出 |
| **边定义** | 清晰的条件分支 |
| **错误处理** | 每个节点有错误处理 |
| **状态合并** | 使用 `Annotated` + `operator.add` |

---

## 5. Team 标准

### 5.1 Team 类型

```python
class TeamType(str, Enum):
    """Team 类型定义"""
    
    TESTING = "testing"       # 测试团队
    ENGINEERING = "engineering"  # 工程团队
    MARKETING = "marketing"   # 市场团队
    DESIGN = "design"         # 设计团队
    GENERAL = "general"       # 通用团队
```

### 5.2 Team 配置

```python
@dataclass
class TeamConfig:
    """Team 配置"""
    
    name: str
    team_type: TeamType
    agents: List[str]          # 包含的 Agent ID
    workflow: str              # 工作流类型
    skills: List[str]          # 具备的 Skills
    tools: List[str]           # 可用的 Tools
```

### 5.3 Team 实现标准

| 标准项 | 要求 |
|--------|------|
| **Agent 组合** | 由多个 Agent 组成 |
| **角色定义** | 每个 Agent 有明确角色 |
| **协作机制** | 通过 `AgentCoordinator` 协调 |
| **工作流** | 定义团队执行流程 |

---

## 6. Service 标准

### 6.1 Service 类型

```python
class ServiceType(str, Enum):
    """Service 类型"""
    
    LLM = "llm"             # LLM 服务
    MODEL = "model"          # 模型服务
    CACHE = "cache"         # 缓存服务
    CONFIG = "config"       # 配置服务
    SKILL = "skill"         # Skill 服务
    METRICS = "metrics"     # 指标服务
    STORAGE = "storage"     # 存储服务
```

### 6.2 Service 实现标准

| 标准项 | 要求 |
|--------|------|
| **单一职责** | 每个 Service 只做一件事 |
| **接口统一** | 使用标准接口 |
| **可配置** | 支持配置管理 |
| **可观测** | 提供指标和日志 |

---

## 附录：标准文件索引

| 实体 | 标准文件 | 关键类 |
|------|----------|--------|
| Agent | `src/agents/base_agent.py` | `BaseAgent`, `AgentCapability` |
| Agent | `src/agents/agent_models.py` | `AgentConfig`, `AgentState`, `AgentResult` |
| Skill | `src/agents/skills/__init__.py` | `Skill`, `SkillMetadata`, `SkillScope` |
| Skill | `src/interfaces/skill.py` | `ISkill`, `SkillCategory` |
| Tool | `src/agents/tools/base_tool.py` | `BaseTool`, `ToolResult` |
| Tool | `src/interfaces/tool.py` | `ITool`, `ToolCategory` |
| Workflow | `src/core/execution_coordinator.py` | `ExecutionCoordinator` |
| Coordinator | `src/interfaces/coordinator.py` | `ICoordinator` |
