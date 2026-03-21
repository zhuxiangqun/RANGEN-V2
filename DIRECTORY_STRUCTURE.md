# RANGEN AI 中台系统目录结构

## 概述

RANGEN 系统已从"研究系统"重构为 **AI 基盘** 系统，采用标准的 AI 中台架构分层。

> ⚠️ **重大更新 (2026-03-21)**: 已完成真正的目录重组，旧的 `src/core/`, `src/api/`, `src/ui/`, `src/tools/` 目录已被删除，所有代码已迁移到新的分层目录结构。

> ⚠️ **核心模块整合 (2026-03-21)**: 已将 `skill_factory/`, `ml_dl_persistence/`, `mlops/` 从根目录移动到 `src/` 下，统一核心代码结构。

> ⚠️ **KMS 独立化 (2026-03-21)**: `knowledge_management_system/` 已分离为独立仓库。`src/kms/` 现在是 KMS 服务的 API 客户端集成层。

> ⚠️ **RPA 工具整合 (2026-03-21)**: `rpa_system/` 已整合到 `src/tools/rpa/`，作为辅助工具模块。

> ⚠️ **Skills 系统整理 (2026-03-21)**: Skills 已统一使用 SKILL.md 格式，包含 26 个内置 Skills，分布在 `src/skills/` 目录下。

## 架构分层

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI 中台架构分层 (AI Platform Layering)           │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 1: 接入层 (Access)      - API、UI、SDK                       │
│  Layer 2: 网关层 (Gateway)     - 统一入口                            │
│  Layer 3: 编排层 (Orchestration) - 任务分解、智能路由               │
│  Layer 4: 执行层 (Execution)   - Agent执行、工作流                  │
│  Layer 5: 服务层 (Services)     - LLM、知识、工具                   │
│  Layer 6: 平台层 (Platform)     - 应用管理、配额、计量               │
│  Layer 7: 基础设施层 (Infra)    - 数据库、缓存、存储                │
└─────────────────────────────────────────────────────────────────────┘
```

## 目录结构

```
src/
├── __init__.py                    # 主包入口
├── access/                        # 🎯 Layer 1: 接入层
│   ├── __init__.py
│   ├── api/                       # REST API 端点
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py        # 路由入口 (platform_router)
│   │   │   ├── platform.py        # 平台管理路由 (应用、配额、命名空间)
│   │   │   ├── agents.py
│   │   │   ├── auth.py
│   │   │   ├── conversation_routes.py
│   │   │   ├── skills.py
│   │   │   ├── tools.py
│   │   │   ├── workflows.py
│   │   │   └── ...
│   │   ├── middleware/           # API中间件
│   │   ├── schemas/              # Pydantic模型
│   │   ├── server.py             # API服务器入口
│   │   └── ...
│   └── ui/                        # Web UI
│       ├── __init__.py
│       └── ...
│
├── gateway/                       # 🎯 Layer 2: 网关层
│   ├── __init__.py
│   ├── gateway.py                 # 网关核心
│   ├── agents/                    # Agent网关
│   ├── channels/                  # 通道管理
│   ├── events/                    # 事件处理
│   ├── mcp/                       # MCP协议
│   ├── memory/                    # 内存管理
│   ├── sandbox/                   # 沙箱隔离
│   ├── tools/                     # 工具网关
│   ├── voice/                     # 语音网关
│   ├── fastapi_integration.py
│   └── server.py
│
├── orchestration/                 # 🎯 Layer 3: 编排层
│   ├── __init__.py
│   ├── services.py                # 编排服务
│   ├── intelligent_orchestrator.py # 智能编排器
│   ├── task_decomposition.py      # 任务分解
│   ├── routing/                   # 智能路由
│   ├── workflow/                  # 工作流引擎
│   ├── orchestration/             # 核心编排 (嵌套)
│   │   ├── __init__.py
│   │   └── intelligent_orchestrator.py
│   ├── nodes/                     # 编排节点
│   ├── langgraph_nodes/           # LangGraph节点
│   ├── state/                     # 状态管理
│   ├── events/                    # 编排事件
│   ├── middleware/                # 编排中间件
│   ├── executor/                   # 执行器
│   ├── core_services/             # 核心服务
│   ├── context_engineering/       # 上下文工程
│   ├── adaptive_optimizer.py      # 自适应优化
│   ├── capability_service.py      # 能力服务
│   ├── event_system.py            # 事件系统
│   ├── feedback_loop_mechanism.py # 反馈循环
│   ├── learning/                  # 学习模块
│   ├── multi_trajectory.py        # 多轨迹
│   ├── neural/                    # 神经网络
│   ├── reasoning/                 # 推理引擎
│   ├── retrieval_quality_assessment.py # 检索质量评估
│   ├── self_evolution_engine.py   # 自进化引擎
│   ├── self_evolving_agent.py     # 自进化Agent
│   ├── monitoring/                # 监控模块
│   ├── governance/                # 治理模块
│   ├── evolution/                 # 演进模块
│   └── ...
│
├── agents/                        # 🎯 Layer 4: 执行层 (Agent) - 整理后
│   ├── __init__.py
│   ├── base/                      # Agent基类
│   ├── chief/                     # 首席Agent
│   ├── core/                      # 核心Agent
│   │   ├── react_agent.py        # ReAct Agent
│   │   ├── reasoning_agent.py    # 推理Agent
│   │   ├── retrieval_agent.py    # 检索Agent
│   │   └── base_agent.py        # 基础Agent
│   ├── specialized/              # 专业Agent
│   │   ├── audit_agent.py       # 审计Agent
│   │   ├── rag_agent.py         # RAG Agent
│   │   ├── expert_agent.py      # 专家Agent
│   │   └── citation_agent.py    # 引用Agent
│   ├── orchestration/           # 编排Agent
│   │   ├── agent_coordinator.py # Agent协调器
│   │   ├── agent_selector.py    # Agent选择器
│   │   └── multi_agent_coordinator.py  # 多Agent协调
│   ├── quality/                 # 质量控制Agent
│   │   ├── quality_controller.py
│   │   └── validation_agent.py
│   ├── learning/                 # 学习Agent
│   │   ├── self_learning_agent.py
│   │   └── learning_optimizer.py
│   ├── execution/               # 执行Agent
│   │   ├── tool_orchestrator.py
│   │   └── unified_executor.py
│   ├── execution_tools/         # Agent执行工具 (原 tools/)
│   │   ├── tool_registry.py
│   │   ├── base_tool.py
│   │   └── agents/              # 工具实现
│   ├── wrappers/               # Agent包装器
│   ├── professional_teams/     # 专业团队Agent
│   ├── market/                 # 市场专用Agent
│   │   ├── china_market/
│   │   └── japan_market/
│   ├── factory.py              # Agent工厂
│   ├── capabilities.py          # Agent能力
│   └── ...
│
├── services/                      # 🎯 Layer 5: 服务层
│   ├── __init__.py
│   ├── llm/                       # LLM 服务
│   │   ├── __init__.py
│   │   ├── model_service.py
│   │   ├── local_llm_service.py
│   │   ├── multi_model_config_service.py
│   │   └── multimodal_service.py
│   ├── knowledge/                 # 知识服务
│   │   ├── __init__.py
│   │   ├── knowledge_retrieval_service.py
│   │   ├── knowledge_graph_service.py
│   │   ├── enhanced_knowledge_retrieval.py
│   │   ├── cognitive_retrieval_system.py
│   │   └── ...
│   ├── tool_registry.py           # ⭐ 工具注册表 (主位置)
│   ├── tool/                      # 工具服务
│   │   ├── __init__.py
│   │   ├── tool_call_validator.py
│   │   ├── tool_safety_interceptor.py
│   │   └── ...
│   ├── monitoring/               # 监控服务
│   │   ├── __init__.py
│   │   ├── performance_monitor.py
│   │   ├── metrics_service.py
│   │   ├── monitoring_dashboard_service.py
│   │   └── ...
│   ├── skill/                     # Skill服务
│   │   ├── __init__.py
│   │   ├── skill_service.py
│   │   ├── skill_benchmark_system.py
│   │   ├── skill_quality_evaluator.py
│   │   └── ...
│   ├── model/                     # 模型服务
│   │   ├── model_routing_reflection.py
│   │   ├── intelligent_model_router.py
│   │   ├── model_benchmark_service.py
│   │   └── ...
│   ├── cost.py                    # 成本控制
│   ├── cost_control.py            # 成本控制器
│   ├── security.py                 # 安全服务
│   ├── security_control.py         # 安全控制
│   ├── database.py                 # 数据库服务
│   ├── reasoning.py                # 推理服务
│   ├── reasoning_service.py        # 推理服务
│   ├── routing.py                  # 路由服务
│   ├── autoscaling_service.py      # 自动扩缩容
│   ├── execution_controller.py     # 执行控制
│   ├── fault_tolerance_service.py  # 容错服务
│   ├── context_optimization_service.py # 上下文优化
│   ├── retrieval.py                 # 检索服务
│   ├── error_handler.py            # 错误处理
│   ├── logging_service.py          # 日志服务
│   └── ...
│
├── platform/                      # 🎯 Layer 6: 平台层
│   ├── __init__.py
│   ├── app/                      # 应用管理
│   │   ├── __init__.py
│   │   └── registry.py           # AppRegistry ⭐
│   ├── quota/                     # 配额管理
│   │   ├── __init__.py
│   │   └── manager.py            # QuotaManager ⭐
│   ├── namespace/                 # 命名空间
│   │   ├── __init__.py
│   │   └── manager.py            # NamespaceManager ⭐
│   ├── metering/                  # 计量
│   │   ├── __init__.py
│   │   └── token_tracker.py      # TokenTracker ⭐
│   ├── capability/                # 能力市场
│   │   ├── __init__.py
│   │   ├── agents/               # Agent 市场
│   │   │   ├── __init__.py
│   │   │   └── registry.py       # AgentRegistry ⭐
│   │   ├── skills/               # Skill 市场
│   │   │   ├── __init__.py
│   │   │   └── marketplace.py    # SkillMarketplace ⭐
│   │   └── tools/               # Tool 市场
│   │       ├── __init__.py
│   │       └── registry.py
│   └── middleware/                # 中间件
│       ├── __init__.py
│       └── app_context.py        # AppContextMiddleware ⭐
│
├── infrastructure/                 # 🎯 Layer 7: 基础设施层
│   ├── __init__.py
│   ├── persistence/              # 持久化
│   ├── storage/                  # 存储
│   ├── external/                 # 外部服务
│   └── ...
│
├── skills/                        # ⭐ Skills 系统 (SKILL.md 格式)
│   ├── runtime/                  # 技能运行时
│   │   ├── skill_trigger.py     # 技能触发器
│   │   ├── dynamic_executor.py  # 动态执行器
│   │   ├── hybrid_tool_executor.py  # 混合工具执行
│   │   ├── llm_driven_executor.py  # LLM驱动执行
│   │   ├── dependency_resolver.py # 依赖解析
│   │   ├── enhanced_registry.py  # 增强注册表
│   │   └── bundled/             # 内置 Skills (26个)
│   │       ├── query-analysis/   # 查询分析
│   │       ├── summarization/   # 摘要生成
│   │       ├── citation-generation/  # 引用生成
│   │       ├── rag-retrieval/   # RAG检索
│   │       ├── fact-check/      # 事实核查
│   │       ├── web_search/      # 网页搜索
│   │       ├── reasoning-chain/  # 推理链
│   │       ├── answer-generation/ # 答案生成
│   │       ├── research-workflow/ # 研究工作流
│   │       ├── ml-prediction-expert/  # ML预测
│   │       ├── data-analysis-workflow/ # 数据分析
│   │       └── ... (共26个)
│   └── factory/                  # 技能工厂
│       ├── factory.py            # 主工厂类
│       ├── templates/            # 技能模板
│       ├── quality_checks/       # 质量检查
│       ├── prototypes/           # 原型分类
│       ├── frontend/            # 前端界面
│       └── output/              # 输出目录
│
├── ml_persistence/               # ⭐ ML/DL模型持久化
│   ├── __init__.py
│   ├── models/                   # 模型文件存储
│   │   └── *.json, *.pkl
│   ├── learning/                 # 学习状态存储
│   │   └── *_learning.json
│   ├── agents/                   # Agent状态存储
│   └── synergy/                  # ML/RL协同状态
│
├── mlops/                        # ⭐ MLOps流水线
│   ├── __init__.py
│   ├── pipelines.json            # 流水线配置
│   ├── pipelines/                # 流水线定义
│   ├── tasks/                    # 任务定义
│   └── artifacts/                # 流水线产物
│
├── config/                        # 配置
├── utils/                        # 工具函数
├── data/                         # 数据目录
├── memory/                       # 内存管理
├── monitoring/                   # 监控
├── middleware/                   # 中间件
├── prompts/                      # 提示词模板
├── templates/                    # 模板
├── visualization/                # 可视化
├── adapters/                     # 适配器
├── domain/                       # 领域模型
├── evolution/                    # 演进
├── integrations/                # 集成
├── interfaces/                  # 接口
├── observability/               # 可观测性
├── strategies/                   # 策略
├── swarm/                        # Swarm
├── kms/                         # ⭐ KMS API客户端
│   ├── kms_client.py             # KMS HTTP客户端
│   ├── pageindex_mcp.py         # PageIndex MCP工具
│   ├── pageindex_rag_integration.py  # 混合检索
│   ├── unified_retrieval.py     # 统一检索
│   └── web_crawler.py          # 网页抓取
├── tools/                        # ⭐ 独立工具模块
│   ├── detection/               # 检测工具
│   ├── voice_synthesis/         # 语音合成
│   ├── dev-tools/              # 开发工具
│   ├── math_extensions/         # 数学扩展
│   ├── contact_center/         # 客服中心
│   └── rpa/                    # RPA 自动化工具
│       ├── browser_automation.py  # 浏览器自动化
│       ├── frontend_monitor.py   # 前端监控
│       ├── core_analyzer.py     # 核心分析
│       └── system_improver.py   # 系统改进
├── layers/                      # 分层架构
├── ai/                          # AI核心
├── hands/                       # Hands模块
├── hook/                        # 钩子
├── integration_tests/           # 集成测试
├── prompts/                     # 提示词
├── di/                          # 依赖注入
└── ...
```

## 独立仓库

### Knowledge Management System (KMS)

KMS 已分离为独立仓库，不再作为 RANGEN 的子模块。

```
知识库位置: /Users/apple/workdata/person/zy/knowledge-management-system/
部署端口: 8080
```

**RANGEN 通过 `src/kms/` 模块调用 KMS 服务：**
```python
from src.kms import get_kms_client

client = get_kms_client()
results = client.query_knowledge("问题")
```

## 向后兼容性

为了保持现有代码工作，已创建以下兼容层：

| 旧路径 | 新路径 | 状态 |
|--------|--------|------|
| `src.api` | `src.access.api` | ✅ 兼容层已创建 |
| `src.ui` | `src.access.ui` | ✅ 兼容层已创建 |
| `src.core` | `src.orchestration` | ✅ 兼容层已创建 |
| `src.tools` | `src.agents.tools` | ✅ 兼容层已创建 |
| `src.platform` | `src.platform` | ✅ 保持不变 |
| `src.agents.tools.tool_registry` | `src.services.tool_registry` | ✅ 兼容层已创建 |

### 兼容层示例

```python
# 旧代码仍然工作（会显示弃用警告）
from src.core import CoreService
# ⚠️ DeprecationWarning: src.core 已移动到 src.orchestration

# 推荐使用新路径
from src.orchestration import CoreService
```

## 核心组件清单

### 平台层 (Platform) 组件

| 组件 | 文件 | 功能 |
|------|------|------|
| **AppRegistry** | `platform/app/registry.py` | 应用注册、认证 |
| **QuotaManager** | `platform/quota/manager.py` | 配额管理 |
| **NamespaceManager** | `platform/namespace/manager.py` | 命名空间 |
| **TokenTracker** | `platform/metering/token_tracker.py` | Token计量 |
| **AgentRegistry** | `platform/capability/agents/registry.py` | Agent市场 |
| **SkillMarketplace** | `platform/capability/skills/marketplace.py` | Skill市场 |
| **AppContextMiddleware** | `platform/middleware/app_context.py` | 中间件 |

### 服务层 (Services) 组件

| 组件 | 文件 | 功能 |
|------|------|------|
| **ToolRegistry** | `services/tool_registry.py` | 工具注册表 (主位置) |
| **PerformanceMonitor** | `services/monitoring/performance_monitor.py` | 性能监控 |
| **LLMService** | `services/llm/` | LLM服务 |
| **KnowledgeService** | `services/knowledge/` | 知识服务 |
| **SkillService** | `services/skill/skill_service.py` | Skill服务 |

### 接入层 (Access) 组件

| 组件 | 文件 | 功能 |
|------|------|------|
| **PlatformRouter** | `access/api/routes/platform.py` | 平台管理API |
| **APIServer** | `access/api/server.py` | API服务器 |
| **AuthService** | `access/api/auth.py` | 认证服务 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RANGEN_PLATFORM_ENABLED` | `false` | 启用平台功能 |
| `RANGEN_API_PORT` | `8000` | API 端口 |
| `RANGEN_LOG_LEVEL` | `INFO` | 日志级别 |

## 已知问题

1. **循环导入**: 某些模块之间存在循环依赖，需要重构
2. **弃用警告**: 旧路径导入会显示警告，建议迁移到新路径
3. **Agent导入**: 由于循环依赖，`src.agents` 完整导入可能失败
4. **LSP诊断**: `platform.py` 中条件导入会导致 LSP 显示 "possibly unbound" 警告，这是预期行为

## 迁移指南

### 从旧路径迁移到新路径

```python
# 旧 (已弃用)
from src.api import router
from src.core import CoreService
from src.tools import ToolRegistry

# 新 (推荐)
from src.access.api import router
from src.orchestration import CoreService
from src.services import ToolRegistry
```

### 启用平台功能

```bash
export RANGEN_PLATFORM_ENABLED=true
python -m src.access.api.server
```

## 迁移状态

✅ **已完成迁移**

| 路径类型 | 状态 | 说明 |
|----------|------|------|
| `src.core.*` → `src.orchestration.*` | ✅ 已完成 | 219 个文件已迁移 |
| `src.tools.monitoring.*` → `src.services.*` | ✅ 已完成 | 性能监控已迁移 |
| `src.ui.*` → `src.access.ui.*` | ✅ 已完成 | UI 模块已迁移 |
| `src.api.*` → `src.access.api.*` | ✅ 已完成 | API 模块已迁移 |
| `src.agents.tools.tool_registry` → `src.services.tool_registry` | ✅ 已完成 | 兼容层已创建 |
| 兼容层 | ✅ 已创建 | 旧路径仍可用（显示警告） |

### 核心模块整合 (2026-03-21)

| 原路径 | 新路径 | 状态 | 说明 |
|--------|--------|------|------|
| `skill_factory/` | `src/skill_factory/` | ✅ 已完成 | AI技能工厂 |
| `ml_dl_persistence/` | `src/ml_persistence/` | ✅ 已完成 | ML/DL持久化 |
| `mlops/` | `src/mlops/` | ✅ 已完成 | MLOps流水线 |

### 迁移验证

```python
import warnings
warnings.filterwarnings('ignore')

from src.platform import AppRegistry  # ✅
from src.orchestration import CoreService  # ✅
from src.services import ToolRegistry  # ✅
from src.agents.base_agent import BaseAgent  # ✅
```

## 目录统计

| 层级 | 目录数 | 说明 |
|------|--------|------|
| Layer 1: 接入层 | 2 | api, ui |
| Layer 2: 网关层 | 8 | gateway及其子模块 |
| Layer 3: 编排层 | 30+ | orchestration及其子模块 |
| Layer 4: 执行层 | 20+ | agents及其子模块 |
| Layer 5: 服务层 | 15+ | services及其子模块 |
| Layer 6: 平台层 | 6 | platform子模块 |
| Layer 7: 基础设施层 | 3 | infrastructure子模块 |
| ⭐ 核心子系统 | 3 | skill_factory, ml_persistence, mlops |

## 版本信息

- 当前版本: 2.1.0
- 架构: AI 中台标准分层
- Python: 3.8+
- 迁移完成: 2026-03-21
- 核心模块整合: 2026-03-21
- 文档更新: 2026-03-21
