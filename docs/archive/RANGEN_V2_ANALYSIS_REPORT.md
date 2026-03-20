# RANGEN V2 系统分析报告

**生成日期**: 2026-03-01  
**系统版本**: V2  
**文档说明**: 基于全库扫描与关键模块阅读整理，供架构决策与接入参考。

---

## 一、系统定性

### 1.1 总体定位

**RANGEN V2** 是一个**企业级多智能体研究系统 (Multi-Agent Research System)**，旨在通过人工智能代理实现复杂的知识检索、任务分解和协作推理。系统同时向「研究平台」与「个人助理/控制平面」双形态演进（Gateway 控制平面、多渠道接入）。

### 1.2 核心特征

| 特征 | 描述 |
| ------ | ------ |
| **架构模式** | 模块化微内核 + 统一中心架构 (Unified Centers) |
| **智能化水平** | ReAct 推理-行动循环、分层战略-战术-执行、LLM 推理工作流 |
| **协作模式** | 多智能体协作 (Chief/ReAct/Expert/Audit/Citation/Retrieval/Validation 等) |
| **部署方式** | FastAPI、Streamlit、Gateway 服务、CLI、可选 DI 容器 |
| **学习能力** | 自进化 (反思/多轨迹/模式学习)、SOP 学习、参数学习、进化引擎 |

### 1.3 技术栈

```text
├── LLM: DeepSeek, OpenAI, Mock (推理/验证/引用模型可配置)
├── Workflow: LangGraph (多套工作流: 分层/简化/推理/ReAct)
├── API: FastAPI (chat, health, auth, SOP CRUD, 可选 DI 版)
├── UI: Streamlit, Vue.js (frontend_monitor)
├── Gateway: 控制平面、多渠道 (WebChat/Telegram/Slack/WhatsApp)、EventBus、沙箱
├── Vector Store: FAISS, Chroma (KMS)
├── Embedding: Jina, Sentence-Transformers (all-mpnet-base-v2 / MiniLM)
├── Re-rank: cross-encoder/ms-marco-MiniLM-L-6-v2 (本地)
└── 配置: YAML/JSON (rangen_v2.yaml, rules.yaml, system_config.json 等)
```

### 1.4 规模与边界

| 维度 | 数量/说明 |
| ------ | ------ |
| **源码** | 约 718 个 Python 文件 (src/) |
| **测试** | 约 85 个测试文件 (tests/) |
| **脚本** | 238+ 脚本 (scripts/)：迁移、监控、验证、性能、KMS、节点检查等 |
| **配置** | 50+ 配置文件 (config/)：环境、规则、评估、数据模板、章节化配置 |
| **知识库** | knowledge_management_system 独立子工程：向量/图谱/多模态/混合检索 |

---

## 二、技术特点

### 2.1 六大核心系统

#### 1. **智能体系统** (src/agents/)

- **基类与协调**: `BaseAgent`, `SimpleAgent`, `ChiefAgent`, `MultiAgentCoordinator`, `Level3Agent`
- **推理与执行**: `ReActAgent`, `EnhancedReActAgent`, `ExpertAgent`
- **能力型**: `AuditAgent`, `CitationAgent`, `ReasoningAgent`, `ValidationAgent`, `RetrievalAgent`
- **包装与技能**: `ContextEngineeringAgentWrapper`, `PromptEngineeringAgentWrapper`, `SkillsAwareAgent`, `SimpleSkillsAgent`
- **市场与领域**: `JapanMarketAgent` / `ChinaMarketAgent`（及 HR/财务/法务/研发/客户/规划等专家）, `JapanAgentFactory` / `ChinaAgentFactory`
- **工具注册**: ToolRegistry、ToolInitializer；11+ 内置工具 (rag, knowledge_retrieval, search, web_search, real_search, reasoning, answer_generation, citation, calculator, multimodal, browser)

#### 2. **核心引擎** (src/core/)

- **LangGraph 工作流**: 分层 (LayeredArchitectureWorkflow)、简化业务 (SimplifiedBusinessWorkflow)、推理 (LangGraphReasoningWorkflow)、ReAct、统一/动态/能力节点等多套
- **协调与编排**: AgentCoordinator、ConfigurableRouter、ExecutionCoordinator、IntelligentOrchestrator（Plan: QuickPlan/ParallelPlan/ReasoningPlan/ConservativePlan/HybridPlan）
- **SOP 与学习**: SOP 学习 (sop_learning)、LangGraph SOP 节点、SOP 路由与集成
- **推理子体系**: reasoning 子包（LangGraph 推理工作流、learning_manager、strategies、validators、answer_extraction、ml_framework）
- **上下文工程**: context_engineering（autonomous_decision、few_shot、structured_memory、context_compactor、just_in_time_retriever 等）
- **开发审核**: DevWorkflowAudit（执行前审核、危险模式、自定义规则、Linter 集成）
- **依赖与启动**: DI 容器 (di/)、Bootstrap、UnifiedParameterLearner、AdaptiveOptimizer

#### 3. **能力系统** (src/hands/, src/agents/tools/)

- **Hands**: BaseHand、HandRegistry、HandExecutor；api_hand、file_hand、code_hand、database_hand、github_hand、slack_hand、notion_hand、adb_hand、keyboard_mouse_hand、enhanced_executor 等
- **Tools**: 通过 ToolRegistry 注册，支持 RAG、检索、搜索、推理、答案生成、引用、计算器、多模态、浏览器等；与技能映射 (TOOL_SKILL_MAPPING)

#### 4. **知识管理系统** (knowledge_management_system/)

- **核心**: 向量索引 (vector_index_builder)、混合检索 (hybrid_retrieval)、知识管理 (knowledge_manager)、推理检索 (reasoning_retrieval)、树索引 (tree_index_builder)、贝叶斯/强化学习优化器
- **图谱**: graph（entity_manager、relation_manager、graph_builder、graph_query_engine、connectivity_optimizer）
- **多模态**: modalities（text/image/audio/video 处理器、smart_model_manager）
- **工具与集成**: src/kms（unified_retrieval、web_crawler、pageindex、pageindex_rag_integration）

#### 5. **治理与监控**

- **监控**: HeartbeatMonitor (core/monitoring)、PerformanceMonitor (tools/monitoring)
- **安全与审计**: UnifiedSecurityCenter、AuditAgent、三省六部制审核
- **可观测**: observability（metrics、structured_logging、tracing）、hook（recorder、explainer、monitor、transparency）

#### 6. **自进化系统**

- **反思与多轨迹**: ReflexionAgent (reflection.py)、MultiTrajectoryExplorer (multi_trajectory.py)、Ralph Loop (ralph_loop.py)、StopHook (stop_hook.py)
- **混入与完整体**: SelfEvolvingMixin (agents)、SelfEvolvingAgent (core)、与 ChiefAgent/BaseAgent 集成

### 2.2 自进化能力 (核心亮点)

#### 三定律实现

| 定律 | 实现机制 | 文件 |
| ------ | --------- | ------ |
| **Endure (生存)** | StopHook 安全退出 | `stop_hook.py` |
| **Excel (卓越)** | 成功率追踪 + SOP质量分析 | `reflection.py` |
| **Evolve (进化)** | 多轨迹探索 + 策略重组 | `multi_trajectory.py` |

#### 集成架构

```text
BaseAgent / ChiefAgent
    │
    ├── enable_self_evolving()
    ├── execute_with_self_evolving()
    │
    └── SelfEvolvingMixin (组合)
            ├── ReflexionAgent (反思)
            ├── MultiTrajectoryExplorer (多轨迹)
            ├── FeedbackCollector (反馈)
            └── Knowledge Management (模式存储)
```

### 2.3 统一中心 (Unified Centers)

通过 `src/utils/unified_centers.py` 注册，供全局获取：

| 中心 | 职责 |
| ------ | ------ |
| get_unified_config_center | 配置 (YAML/JSON/环境变量)、SmartConfigCenter |
| get_unified_intelligent_center | 智能中心、统一决策 |
| get_unified_context_manager | 上下文管理、动态刷新 |
| get_unified_security_center | 安全、审计、威胁情报、行为分析 |
| get_unified_threshold_manager | 阈值管理 |
| get_unified_dependency_manager | 依赖注册与工厂 |
| get_unified_tokenization_manager | 分词与长度控制 |
| get_unified_model_manager | 模型管理 |
| get_unified_intelligent_processor | 智能处理管道 |
| get_unified_complexity_model_service | 复杂度与评估 |

### 2.4 Gateway 控制平面

- **定位**: 将 RANGEN 从研究系统扩展为个人助理/控制平面 (参考 OpenClaw Gateway)。
- **核心**: `src/gateway/gateway.py` — Gateway、GatewayConfig、连接管理、任务分发、Kill Switch。
- **渠道**: channels — WebChat、Telegram、Slack、WhatsApp、ChannelAdapter。
- **运行时**: agents/agent_runtime、AgentConfig、prompt_builder、rangen_adapter；memory/session_memory；events/event_bus。
- **工具与安全**: gateway/tools（browser、code_executor、file_manager、office、schedule）、sandbox、MCP。

### 2.5 工作流引擎选型

| 工作流 | 用途 |
| ------ | ------ |
| LayeredArchitectureWorkflow | 分层：query_analysis → strategic_decision → tactical_optimization → execution_coordination → result_processing |
| SimplifiedBusinessWorkflow | 简化业务：route_query → smart_collaborator → intelligent_processor → format_output |
| LangGraphReasoningWorkflow | 推理链：generate_steps → execute_step → gather_evidence → extract_answer → synthesize |
| react_workflow | ReAct 循环与工具调用 |
| langgraph_unified / dynamic / capability_nodes | 统一与动态编排、能力节点 |

### 2.6 进化与自修改 (src/evolution/)

- **EvolutionEngine**: 进化驱动。
- **SelfModification / CodeModification / CodeAnalysis**: 代码自修改与分析。
- **ConstitutionChecker**: 进化宪法约束。
- **BackgroundConsciousness / Reflection / Thought / KnowledgePattern**: 意识与反思抽象。
- **MultiModelReview**: 多模型评审（ReviewIssue、ReviewSeverity）。
- **GitIntegration**: 与 Git 集成。
- **UsageAnalytics**: 使用统计与优化建议。

---

## 三、适用场景

### 3.1 最佳场景

| 场景 | 适用性 | 说明 |
| ------ | -------- | ------ |
| **企业知识管理** | ⭐⭐⭐⭐⭐ | 智能问答、知识检索、多源整合 |
| **研究助手** | ⭐⭐⭐⭐⭐ | 文献分析、假设生成、实验设计 |
| **代码审查** | ⭐⭐⭐⭐ | 自动审计、性能优化建议 |
| **多系统协调** | ⭐⭐⭐⭐ | 跨平台任务编排 |
| **数据分析** | ⭐⭐⭐ | 复杂查询、多维分析 |

### 3.2 不推荐场景

| 场景 | 原因 |
| ------ | ------ |
| 实时控制 | 需要物理设备接口 |
| 极简需求 | 架构偏重 |
| 无LLM环境 | 依赖大语言模型 |

### 3.3 部署要求

```text
✅ 最低配置:
   - Python 3.9+
   - 4GB RAM
   - LLM API Key (DeepSeek/OpenAI)

✅ 推荐配置:
   - Python 3.10+
   - 8GB+ RAM
   - GPU (可选,用于本地embedding)
```

---

## 四、使用方法

### 4.1 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境
cp .env.example .env
# 编辑 .env: LLM_PROVIDER, DEEPSEEK_API_KEY / OPENAI_API_KEY 等
# 主配置: config/rangen_v2.yaml, config/rules.yaml

# 3. 启动服务
python src/api/server.py              # API (chat/health/auth, localhost:8000)
streamlit run src/ui/app.py           # Streamlit Web UI (localhost:8500)
python src/gateway/server.py           # Gateway 控制平面 (若需多渠道/助理形态)

# 4. 质量与节点检查 (可选)
pylint src/
python scripts/check_node_docstrings.py   # LangGraph 节点 docstring 校验
pytest
```

### 4.2 自进化能力使用

```python
from src.agents.chief_agent import ChiefAgent
from src.agents.self_evolving_mixin import SelfEvolvingConfig

# ChiefAgent 已内置自进化
agent = ChiefAgent()

# 检查状态
print(agent.is_self_evolving_enabled())  # True

# 带自进化的执行
result = await agent.execute_with_self_evolving(
    task="分析这个代码问题",
    context={},
    execute_func=my_execute_function
)

# 获取进化状态
state = agent.get_evolution_state()
patterns = agent.get_learned_patterns()
success_rate = agent.get_success_rate()
```

### 4.3 自定义 Agent 使用自进化

```python
from src.agents.base_agent import BaseAgent
from src.agents.self_evolving_mixin import SelfEvolvingConfig

class MyAgent(BaseAgent):
    def __init__(self, agent_id: str, ...):
        super().__init__(...)
        
        # 启用自进化
        self.enable_self_evolving(
            config=SelfEvolvingConfig(
                enabled=True,
                enable_reflection=True,           # 启用反思
                enable_multi_trajectory=False,   # 可选:多轨迹(计算密集)
                enable_pattern_learning=True,    # 启用模式学习
                pattern_storage_enabled=True     # 存储到KMS
            ),
            llm_provider=your_llm
        )
```

---

## 五、扩展能力及扩展方法

### 5.1 现有扩展点

#### A. 扩展 Agent 能力

```python
# 方式1: 继承 BaseAgent
class CustomAgent(BaseAgent):
    def process_query(self, query: str, context: Dict = None) -> AgentResult:
        # 自定义处理逻辑
        pass

# 方式2: 使用 AgentBuilder
from src.agents.agent_builder import AgentBuilder

agent = AgentBuilder() \
    .set_capabilities(["reasoning", "tool_calling"]) \
    .set_llm_provider(llm) \
    .build()
```

#### B. 扩展 Tools

```python
from src.agents.tools.base_tool import BaseTool

class MyCustomTool(BaseTool):
    name = "my_tool"
    description = "自定义工具"
    
    async def execute(self, **kwargs) -> ToolResult:
        # 工具逻辑
        return ToolResult(success=True, data=result)
```

#### C. 扩展 Hands 能力

```python
from src.hands.base import BaseHand

class CustomHand(BaseHand):
    async def execute(self, **kwargs) -> HandExecutionResult:
        # 能力实现
        pass
```

### 5.2 自进化能力扩展

#### 扩展反思策略

```python
from src.core.reflection import ReflexionAgent

class CustomReflection(ReflexionAgent):
    async def reflect(self, task, output, context):
        # 自定义反思逻辑
        pass
```

#### 扩展探索策略

```python
from src.core.multi_trajectory import TrajectoryStrategy, MultiTrajectoryExplorer

# 添加新的探索策略
class CustomExplorer(MultiTrajectoryExplorer):
    def _select_strategies(self):
        return [TrajectoryStrategy.HYBRID, CustomStrategy.MY_CUSTOM]
```

### 5.3 配置扩展

```yaml
# config/custom_config.yaml
chief_agent:
  self_evolving:
    enabled: true
    multi_trajectory: true
    max_trajectories: 5
    
my_custom_agent:
  capability_level: 0.9
  max_iterations: 20
```

### 5.4 开发工作流审核 (DevWorkflowAudit) ✅ 已集成

代码审核能力已集成到开发流程，支持执行前审核、危险模式检测、自定义规则、**Linter 集成**与自进化学习。

| 能力 | 说明 |
| ------ | ------ |
| **执行前审核** | `audit_code()` / `audit_and_execute()` 在运行前检查代码 |
| **危险模式检测** | 内置 `eval`/`exec`、`rm -rf`、DROP TABLE、`os.system` 等规则 |
| **自定义规则** | `add_custom_rule()` / ChiefAgent `add_dev_audit_rule()` |
| **Linter 集成** | `run_linter_checks(paths)` 运行 pylint/pyright，发现项目中的静态检查错误 |
| **自进化集成** | `learn_from_rejection()` 将拒绝案例写入反思并生成新规则 |

**为何「审核」没扫出项目里的 linter 错误？**

- `audit_code()` 面向**即将执行的代码片段**，只做危险操作 + 简单规范（正则），**不做**整库静态分析。  
- 项目里已有的 pylint/pyright 等 linter 错误需通过 **`run_linter_checks(["src/"])`** 或 CI 中执行 `pylint src/`、`pyright src/` 发现。

**使用示例**（详见 `examples/dev_workflow_audit_example.py`）:

```python
from src.core.dev_workflow_audit import DevWorkflowAudit, AuditLevel, quick_audit

# 独立审核（执行前安全 + 规范）
audit = DevWorkflowAudit(audit_level=AuditLevel.STANDARD)
result = await audit.audit_code(code)

# 发现项目中的 linter 错误
linter_result = audit.run_linter_checks(["src/"])
print(linter_result["summary"]["total"], "个问题")

# 与 ChiefAgent 集成：审核后执行
chief = ChiefAgent()
run_result = await chief.audit_and_execute(code, execute_func=my_func, context={})
# ChiefAgent 也可跑 linter
chief.run_linter_checks(["src/"])
```

---

## 六、附录

### 6.1 目录结构

```text
RANGEN-main(syu-python)/
├── src/                          # 约 718 个 Python 文件
│   ├── agents/                   # 智能体 (含 tools, japan_market, china_market, skills, workspace)
│   ├── api/                      # FastAPI: server, server_di, main, sop_routes, auth
│   ├── core/                     # 工作流/推理/SOP/上下文/监控/reasoning/context_engineering 等
│   ├── gateway/                  # 控制平面: gateway, server, channels, agents, events, memory, tools, mcp
│   ├── hands/                    # Hands 能力包 (api, file, code, database, github, slack, notion, adb 等)
│   ├── tools/                    # 工具与 monitoring
│   ├── services/                 # 业务服务 (config, logging, security, audit, reasoning 等)
│   ├── utils/                    # 统一中心、安全、编码等
│   ├── ui/                       # Streamlit UI
│   ├── visualization/            # 可视化与 servers
│   ├── di/                       # 依赖注入、bootstrap、unified_container
│   ├── evolution/                # 进化引擎、自修改、宪法、意识、多模型评审、Git
│   ├── hook/                     # recorder, explainer, monitor, transparency
│   ├── integration/              # 工作流/SOP 集成
│   ├── kms/                      # 统一检索、爬虫、pageindex、RAG 集成
│   ├── config/                   # 规则注册、schema、智能配置
│   ├── observability/            # metrics, tracing, structured_logging
│   ├── middleware/               # validation 等
│   └── memory/                   # faiss_utils 等
├── knowledge_management_system/ # KMS: core, graph, modalities, utils, config
├── config/                       # 50+ 配置: rangen_v2.yaml, rules.yaml, environments, sections 等
├── tests/                        # 约 85 个测试文件
├── scripts/                      # 238+ 脚本: 迁移、监控、验证、KMS、check_node_docstrings 等
├── examples/                     # 示例 (basic_usage, dev_workflow_audit_example 等)
└── frontend_monitor/             # Vue.js 监控前端
```

### 6.2 自进化与开发审核模块

| 模块 | 行数 | 功能 |
| ------ | ------ | ------ |
| `agents/self_evolving_mixin.py` | 477 | Agent 自进化混入类 |
| `core/self_evolving_agent.py` | 897 | 完整自进化 Agent |
| `core/reflection.py` | 408 | 反思机制 |
| `core/ralph_loop.py` | 422 | 持续迭代 |
| `core/multi_trajectory.py` | 941 | 多轨迹探索 |
| `core/stop_hook.py` | 509 | 停止钩子 |

### 6.3 开发工作流审核模块

| 模块 | 功能 |
| ------ | ------ |
| `src/core/dev_workflow_audit.py` | DevWorkflowAudit、危险模式、自定义规则、审核级别 |
| `examples/dev_workflow_audit_example.py` | 独立审核、自定义规则、ChiefAgent 集成、自进化示例 |

### 6.4 配置项说明

```python
SelfEvolvingConfig:
  enabled                    # 是否启用
  enable_reflection          # 启用反思
  enable_multi_trajectory    # 启用多轨迹探索
  enable_pattern_learning   # 启用模式学习
  min_success_rate_threshold # 最低成功率阈值
  max_consecutive_failures   # 最大连续失败次数
  pattern_storage_enabled    # 存储到知识库
```

### 6.5 主要 API 与脚本入口

| 类型 | 路径/命令 | 说明 |
| ------ | ------ | ------ |
| API | `POST /chat`, `GET /health`, `GET /diag` | server.py |
| API | `GET/POST/PUT/DELETE /sop/*` | SOP  CRUD、recall、statistics、export/import |
| API | `POST /auth/api-key`, `GET /auth/info` | 认证 |
| 入口 | `python src/api/server.py` | 主 API 服务 |
| 入口 | `python src/gateway/server.py` | Gateway 控制平面 |
| 入口 | `streamlit run src/ui/app.py` | Streamlit UI |
| 质量 | `pylint src/` | 代码规范 |
| 质量 | `python scripts/check_node_docstrings.py` | LangGraph 节点 docstring 校验 |
| 测试 | `pytest` | 全量测试 |

---

## 七、集成缺口与完善建议

以下为基于代码追踪得出的**能力未充分接入主流程**的缺口，便于排期完善。

### 7.1 多入口与 Chat 后端不统一

| 入口 | Chat 后端 | 说明 |
| ------ | ------ | ------ |
| `src/api/server.py` | ExecutionCoordinator + ConfigurableRouter | 仅注册 RetrievalTool，未用 ChiefAgent/UnifiedResearchSystem |
| `src/api/main.py` | UnifiedResearchSystem | 使用智能协调 + MAS(ChiefAgent) / 标准循环 / 传统流程 |
| Gateway | RANGENAgentAdapter → ChiefAgent / ReActAgent | 使用 ChiefAgent，但专家池见下 |

**建议**: 明确「默认 Chat 能力」由哪条链路提供；若希望 /chat 具备完整多智能体与工具链，可将 server.py 的 chat 委托给 UnifiedResearchSystem，或统一只保留一个主入口。

### 7.2 ChiefAgent 专家池与协调为占位

- `ChiefAgent.expert_agent_pool` 在构造时为空，`_decompose_task` / `_coordinate_execution` 为占位实现（返回固定结构、无真实子任务执行）。
- `register_expert_agent()` 存在但**几乎无调用方**将 RAG/推理/引用等专家注册进 ChiefAgent。
- 实际具备工具调用能力的是 **UnifiedResearchSystem** 内的专家与 **ReActAgent/IntelligentOrchestrator**（通过 tool_registry），而非 ChiefAgent 的池子。

**建议**: 若希望「ChiefAgent 真正做任务分解与专家调度」，需在启动时（或统一 Agent 初始化处）向 ChiefAgent 注册各专家 Agent，并实现 _decompose_task / _coordinate_execution 对真实 Agent 的调用；或明确 ChiefAgent 仅作「轻量协调壳」，主能力由 UnifiedResearchSystem 提供。

### 7.3 Hands 能力仅 SOP 节点使用

- **Hands**（api_hand、file_hand、code_hand、database_hand、github_hand、slack_hand、notion_hand、adb_hand 等）仅在 **langgraph_sop_nodes** 中通过 HandRegistry 调用。
- 主 Chat / 研究流程（ExecutionCoordinator、UnifiedResearchSystem 的常规路径）**未**调用 Hands，浏览器/文件/API 等能力未接入主对话。

**建议**: 若需在主对话中提供「执行脚本、操作文件、调 API、发 Slack」等能力，可在主链路中引入 HandExecutor 或通过工具层封装 Hands，由 ReAct/专家 Agent 按需调用。

### 7.4 进化引擎未接入主请求链路

- **EvolutionEngine**（自修改、宪法检查、UsageAnalytics）仅在 **governance_dashboard**（Streamlit）和 **workflow_integration** 中使用。
- API /chat、Gateway 对话、ChiefAgent 执行路径均**未**调用进化引擎；进化能力目前偏「后台治理与看板」，非请求级。

**建议**: 若希望「请求级自进化」（如根据结果触发反思、写回模式），可在 UnifiedResearchSystem 或 ChiefAgent 执行完成后挂接 EvolutionEngine 的轻量钩子；否则保持现状，仅治理侧使用即可。

### 7.5 代码中的 TODO / 未完成集成

| 位置 | 说明 |
| ------ | ------ |
| `evolution/engine.py` | 性能监控、代码质量分析、用户反馈、健康检查、重大修改/架构变更流程等为 TODO |
| `evolution/self_modification.py` | 市场分析、机会评估、具体验证逻辑为 TODO |
| `kms/unified_retrieval.py` | 向量索引、向量库文档列表为 TODO，需进一步集成 |
| `kms/pageindex_rag_integration.py` | 同时创建向量索引为 TODO |
| `gateway/mcp/__init__.py` | HTTP transport 为 TODO |
| `gateway/voice/__init__.py` | 调用 LLM/Agent 处理为 TODO |
| `core/langgraph_unified_workflow.py` | 阶段5 协作节点路由「目前未集成到主流程」 |
| `agents/tools/rerank_tool.py` | 实际 Cross-Encoder/KMS 集成为 TODO |
| `agents/tools/search_tool.py` | 实际搜索 API（Google/Bing 等）为 TODO |
| `core/reasoning/cognitive_answer_extractor.py` | LLM 未集成时无法认知提取 |

**建议**: 按优先级（如先 KMS 检索与 rerank、再搜索 API、再 Gateway/MCP/Voice）逐步补齐上述集成，并在文档中标注「已集成 / 未集成」状态。

### 7.6 已完成的集成改进（近期落地）

| 改进项 | 说明 |
| ------ | ------ |
| **统一 Chat 后端可选** | `server.py`：设置 `RANGEN_USE_UNIFIED_RESEARCH=1` 后，`/chat` 使用 UnifiedResearchSystem（多智能体+完整工具链）；未设置则仍用 ExecutionCoordinator。`/health/auth`、`/diag` 返回当前 chat_backend。 |
| **ChiefAgent 默认专家** | 设置 `RANGEN_CHIEF_REGISTER_DEFAULT_EXPERTS=1` 或在构造时传入 `register_default_experts=True`，ChiefAgent 会注册一名 general_expert（ExpertAgent），并实现真实的 `_coordinate_execution`（调用专家 execute）。Gateway 等单独使用 ChiefAgent 时即可具备基础执行能力。 |
| **Hands 进主工具链** | 新增 `FileReadHandTool`（`src/agents/tools/file_hand_tool.py`），封装 FileReadHand，并在 `tool_initializer.get_all_tools()` 中注册为 `file_read`。凡使用统一 ToolRegistry / get_all_tools 的链路（如 ReAct、UnifiedResearchSystem 内专家）均可调用「读取文件」能力。 |

### 7.7 小结

- **已较好集成**: 自进化与 ChiefAgent（配置与混入）、DevWorkflowAudit 与 Linter、审核与质量、UnifiedResearchSystem 内专家与工具、SOP 与 Hands、Gateway 与 RANGEN 适配器、KMS 在检索/RAG 链路的使用；以及 7.6 中的 Chat 后端可选（ExecutionCoordinator / UnifiedResearchSystem 切换）、ChiefAgent 默认专家、Hands(file_read) 工具入链。
- **待加强**:
  - **进化引擎挂载点**: 在 UnifiedResearchSystem / ChiefAgent 的执行结束处增加可选 EvolutionEngine 钩子（如成功/失败后进行轻量反思、记录模式），并通过配置开关控制开关与频率。
  - **KMS 深度集成**: 完成 `kms/unified_retrieval.py` 与 `pageindex_rag_integration.py` 中关于向量索引/文档列表的 TODO，使统一检索在所有工作流路径上行为一致且可观测。
  - **Gateway 能力扩展**: 补齐 MCP HTTP、Voice 通道调用 LLM/Agent 的 TODO，并在 Gateway→RANGENAdapter 路径上复用统一工作流与知识库能力。
  - **质量与规则落地**: 7.5 中 evolution/自修改/安全等 TODO 项分批转为具体迭代（如先错误模式学习→架构变更流程→市场分析），并在 AGENTS.md / 本文档中维护「已完成/进行中/规划中」状态。

完善时建议：主入口与主能力链路已可通过环境变量切换；Gateway 使用 ChiefAgent 时建议设置 `RANGEN_CHIEF_REGISTER_DEFAULT_EXPERTS=1`；需完整多智能体时设置 `RANGEN_USE_UNIFIED_RESEARCH=1`。

---

### 报告完成

本文档基于对全库的扫描与关键模块阅读整理，若某子模块有独立文档或版本变更，以实际代码与配置为准。如需更详细的某个部分，可指定模块或章节再展开。
