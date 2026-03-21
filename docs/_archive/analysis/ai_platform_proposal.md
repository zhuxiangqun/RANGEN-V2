# RANGEN → AI 中台改造方案

## 1. 可行性判断：可行

当前系统已经具备了 AI 中台的多项核心基础设施：

- **LLM 统一调用层** — `LLMIntegration` 已封装 DeepSeek，支持 OpenAI 兼容协议
- **Agent 运行时** — `AgentRuntime` 实现了完整的 Reason→Act→Observe 循环
- **Gateway 控制平面** — 多渠道适配(Slack/Telegram/WhatsApp/WebChat)、事件总线、Kill Switch
- **依赖注入容器** — `UnifiedDIContainer` 支持 Singleton/Transient/Scoped 三种生命周期
- **中间件体系** — 输入验证、速率限制、安全头
- **知识管理系统(KMS)** — 向量检索、重排序、知识图谱
- **工具系统** — `ToolRegistry`、`Hands`(API/Webhook/Browser/Code/File/Office/Schedule)
- **可观测性** — 结构化日志、Hook 透明化、监控

主要差距在于：系统目前是一个 **单体研究应用**，缺乏「多应用接入」和「平台化治理」的关键能力。

## 2. 目前缺少什么（Gap 分析）

### 2.1 多租户 / 多应用隔离

- 当前只有一个全局 `coordinator` 和一个 `research_system`，无法区分不同应用
- 没有应用注册、应用级 API Key、应用级配额管理
- 没有数据隔离（知识库、会话记忆等都是全局共享）

### 2.2 LLM Provider 管理

- 当前强制锁死 DeepSeek，中台需要支持多 Provider（DeepSeek/OpenAI/Anthropic/本地模型）
- 缺少 Provider 路由策略（成本/延迟/能力 自动选择）
- 缺少 Token 计量和成本追踪

### 2.3 应用管理 API

- 没有应用 CRUD 接口（注册应用、获取 AppKey、配置应用级参数）
- 没有 App 级别的 Prompt 模板管理
- 缺少应用级别的 Agent 配置覆盖（不同应用使用不同 Agent 组合）

### 2.4 平台治理

- 速率限制是全局的，缺少应用级/用户级细粒度限流
- 缺少用量统计和计费模型（按 Token / 按调用次数）
- 缺少应用健康监控仪表盘

### 2.5 SDK / 接入层

- 只有 REST API（`/chat`），缺少 SDK 封装
- 缺少 Streaming（SSE）支持
- 缺少 Webhook 回调能力（异步任务完成通知）

## 3. 改造方案

整体分为 **4 个阶段**，每个阶段可独立交付。

### Phase 1：平台内核（多应用 + 多 LLM）

目标：让多个应用可以独立接入中台，使用不同的 LLM 配置。

**3.1 应用注册与隔离**

新增 `src/platform/` 目录：

- `src/platform/app_registry.py` — 应用注册表
  - 每个应用拥有 `app_id`、`app_key`、`app_secret`
  - 应用级配置：允许使用的模型列表、最大 Token 配额、速率限制
- `src/platform/app_context.py` — 应用上下文
  - 每次请求携带 `X-App-ID` + `X-App-Key` Header
  - 中间件自动解析并注入 `AppContext` 到请求链路
- `src/platform/quota_manager.py` — 配额管理
  - 按应用统计 Token 消耗、请求次数
  - 超额时返回 429

**3.2 多 LLM Provider 路由**

改造 `src/core/llm_integration.py`：

- 移除「强制重定向到 DeepSeek」的逻辑
- 新增 `LLMRouter`（`src/platform/llm_router.py`）：
  - 支持注册多个 Provider（DeepSeek/OpenAI/Anthropic/本地）
  - 路由策略：直接指定 / 按成本最优 / 按延迟最优 / 按能力匹配
  - 自动 Fallback：主 Provider 失败时切到备用
- 新增 `src/platform/token_tracker.py`：
  - 记录每次 LLM 调用的 input_tokens、output_tokens、cost
  - 关联到 app_id

**3.3 应用级 API 端点**

扩展 `src/api/server.py`：

- `POST /platform/apps` — 注册应用
- `GET /platform/apps/{app_id}` — 获取应用信息
- `PUT /platform/apps/{app_id}` — 更新应用配置
- `GET /platform/apps/{app_id}/usage` — 获取用量统计
- `POST /v1/chat/completions` — OpenAI 兼容接口（应用通过此接口调用 LLM）
- `POST /v1/agents/run` — Agent 执行接口（带工具调用能力）

### Phase 2：能力市场（Agent / 工具 / 知识库 复用）

目标：让不同应用可以组合使用平台提供的各种能力。

**3.4 Agent 模板与编排**

- `src/platform/agent_marketplace.py`
  - 将现有 14 个 Agent 注册为「平台能力」
  - 应用可以选择启用哪些 Agent 的组合
  - 支持自定义 Agent（应用提供 System Prompt + Tool 配置）

**3.5 知识库隔离**

- 改造 KMS，支持 Namespace 隔离
  - 每个应用一个独立的 Namespace（向量空间）
  - 支持「平台公共知识库」+ 「应用私有知识库」两层
- 新增 API：
  - `POST /v1/knowledge/{app_id}/upload` — 上传文档到应用知识库
  - `POST /v1/knowledge/{app_id}/query` — 从应用知识库检索

**3.6 工具注册**

- 扩展现有 `ToolRegistry` 和 `Hands` 系统
  - 平台内置工具：搜索、代码执行、文件管理、日程
  - 应用自定义工具：通过 Webhook/MCP 协议注册外部工具

### Phase 3：接入层增强

目标：降低应用接入门槛，支持多种接入方式。

**3.7 OpenAI 兼容 API**

- 实现标准 OpenAI API 格式（`/v1/chat/completions`）
- 支持 Streaming（SSE）响应
- 现有 OpenAI SDK（Python/JS/Go）可直接接入，只需修改 base_url

**3.8 SDK 封装**

- Python SDK：`rangen-sdk`，封装认证、调用、错误处理
- 提供简单示例：

```python
from rangen import RangenClient
client = RangenClient(app_key="xxx", base_url="http://localhost:8000")
result = client.chat("你好")
result = client.agent_run("帮我查一下最近的论文", tools=["search", "knowledge_base"])
```

**3.9 异步任务**

- 长时间运行的 Agent 任务通过 Webhook 回调通知
- `POST /v1/agents/run` 返回 `task_id`，客户端可轮询或等待回调

### Phase 4：平台治理与运营

**3.10 用量与计费**

- 应用级用量面板（Dashboard）
  - Token 消耗趋势、请求量、平均延迟、错误率
- 计费模型支持：按 Token / 按请求 / 包月配额

**3.11 监控增强**

- 扩展现有 `src/monitoring/` 和 `src/observability/`
  - 应用级 Metrics（Prometheus 格式）
  - 调用链追踪（OpenTelemetry 集成已有框架，需实际启用）
  - 告警规则（错误率突增、配额即将耗尽等）

## 4. 推荐实施顺序

优先级从高到低：

1. **Phase 1**（2-3 周）— 最核心，建立多应用 + 多 LLM 的平台内核
2. **Phase 3.7**（1 周）— OpenAI 兼容 API，让现有生态的应用可以零改动接入
3. **Phase 2.5 知识库隔离**（1 周）— 多应用最常需要的差异化能力
4. **Phase 2.4 Agent 模板**（1-2 周）— 建立能力市场
5. **Phase 3.8-3.9 SDK + 异步**（1 周）— 降低接入成本
6. **Phase 4 治理**（持续）— 随运营需要逐步完善

## 5. 目录结构变化

```
src/
├── platform/              # 🆕 中台核心
│   ├── app_registry.py    # 应用注册与管理
│   ├── app_context.py     # 应用上下文（中间件）
│   ├── llm_router.py      # 多 LLM Provider 路由
│   ├── token_tracker.py   # Token 计量
│   ├── quota_manager.py   # 配额管理
│   └── agent_marketplace.py  # Agent 能力市场
├── api/
│   ├── server.py          # 扩展：应用管理 + OpenAI 兼容端点
│   ├── platform_routes.py # 🆕 平台管理 API
│   └── openai_compat.py   # 🆕 OpenAI 兼容 API
├── core/
│   └── llm_integration.py # 改造：移除强制 DeepSeek，接入 LLMRouter
├── gateway/               # 已有，保持不变
├── di/                    # 已有，保持不变
├── middleware/
│   ├── validation.py      # 已有
│   └── app_auth.py        # 🆕 应用级认证中间件
└── sdk/                   # 🆕 SDK 源码
    └── python/
```

## 6. 小结

当前系统的基础设施（Gateway/DI/Agent Runtime/KMS/工具系统/可观测性）已经相当完整，距离 AI 中台的核心差距是 **多应用隔离** 和 **LLM Provider 路由管理**。Phase 1 完成后，系统就具备了作为 AI 中台的基本能力，后续阶段是在此基础上丰富平台功能。
