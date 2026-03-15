# AI中台管理平台方案 (v9.0 - 已实现)

## TL;DR

> **目标**：创建一个管理平台，用于管理RANGEN AI中台

> **核心理念**：
> - **AI已具备的能力尽量组合使用**，不重复造轮子
> - **只有AI不具备的能力才需要扩展**，避免系统膨胀

> **核心功能**：
> 1. **能力组合** - 组合现有Skills/Tools创建新Agent
> 2. **测试验证** - 测试Agent并实时查看运行过程
> 3. **协作团队** - 让AI自动生成协作Agent团队
> 4. **执行控制** - 循环限制、超时控制、手动终止
> 5. **成本控制** - Token统计、费用计算
> 6. **信息安全** - 外发确认、账户保护
> 7. **沙箱安全** - 扩展沙箱到所有执行环节

> **预估工作量**：4-5周

> **当前状态**：✅ 已全部实现 (2026-03-04)
> - **Agent管理**: ✅ 已实现 - CRUD API + Streamlit管理界面
> - **Skill管理**: ✅ 已实现 - 组合Tools创建Skills + API + 界面
> - **Tool管理**: ✅ 已实现 - 浏览/创建/删除 + API
> - **测试验证**: ✅ 已实现 - 实时可视化 + SSE流式推送
> - **协作团队**: ✅ 已实现 - 团队创建 + 执行 + 界面
> - **执行控制**: ✅ 已实现 - 循环限制/超时控制/手动终止
> - **成本控制**: ✅ 已实现 - Token统计/费用计算/预算告警
> - **信息安全**: ✅ 已实现 - 外发确认/白名单/账户保护
> - **沙箱安全**: ✅ 已实现 - Tool/Agent/API/Code沙箱
> - **能力检查**: ✅ 已实现 - 创建前检查现有能力
> - **模型管理**: ✅ 已实现 - 模型市场/微调/训练/切换

---

## 一、设计理念

### 1.1 能力分层（从简单到复杂）

```
┌─────────────────────────────────────────────────────────────┐
│  正确顺序：需求来 → Tool → Skill → Agent → Team          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Level 1: Tool（工具）                                     │
│  ─────────────────────                                     │
│  • 最底层：执行单一操作                                     │
│  • 例：file_reader, code_executor, web_search             │
│  • ✅ 现有15+ Tools可直接使用                              │
│  • 判断：现有Tool能否满足需求？                             │
│                                                             │
│  Level 2: Skill（技能）                                     │
│  ─────────────────────                                     │
│  • 组合多个Tools的能力                                      │
│  • 例：rag-retrieval = search + knowledge_base             │
│  • ✅ 现有Skills可复用                                     │
│  • 判断：现有Skills能否组合满足？                           │
│                                                             │
│  Level 3: Agent（智能体）                                   │
│  ─────────────────────                                     │
│  • 组合Skills + 特定Prompt                                  │
│  • 例：Bug检测助手 = code_analysis + bug_detection         │
│  • ⚠️ 只有复杂需求才创建                                    │
│  • 判断：真的需要多Skills协作？                             │
│                                                             │
│  Level 4: Team（团队）                                      │
│  ─────────────────────                                     │
│  • 多个Agents协作                                           │
│  • ⚠️ 只有需要多角色协作才创建                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 能力检查流程

```
用户需求
    │
    ▼
┌─────────────────┐
│ 1. 检查Tools   │──Yes──▶ 直接使用Tool ──▶ 完成
└────────┬────────┘
         │No
         ▼
┌─────────────────┐
│ 2. 检查Skills   │──Yes──▶ 组合Skills ──▶ 完成
└────────┬────────┘
         │No
         ▼
┌─────────────────┐
│ 3. 检查Agents  │──Yes──▶ 组合Agents ──▶ 完成
└────────┬────────┘
         │No
         ▼
┌─────────────────┐
│ 4. 创建Team     │              ⚠️ 需要时才创建
└─────────────────┘
```

**核心原则**：
- ✅ **能用Tool不用Skill** - Tool最简单
- ✅ **能用Skill不用Agent** - Skill是Tool组合
- ✅ **能用Agent不用Team** - Agent是Skill组合
- ❌ **避免动辄创建高层能力** - 造成系统膨胀

---

## 二、用户场景

### 场景1：我想增加一个新Agent

```
用户操作：
1. 打开管理平台
2. 点击"创建Agent"
3. 填写配置：
   - 名称：Bug检测助手
   - 角色：专业的代码测试工程师
   - 工具：代码执行、文件读取、网页搜索
4. 点击"保存"

→ 新Agent已创建，可立即使用
```

### 场景2：我想测试新Agent（实时查看运行过程）

```
用户操作：
1. 在管理平台选择"Bug检测助手"
2. 点击"测试"
3. 输入测试任务
4. 实时查看运行过程：
   - Agent的思考过程
   - 调用的工具
   - 中间结果
5. 查看最终结果

→ 验证Agent是否正常工作
```

### 场景3：管理已创建的Agent

```
用户操作：
1. 查看Agent列表
2. 看到已创建的Agent：
   - Bug检测助手 (使用中)
   - 代码审查助手 (使用中)
3. 可以：
   - 复用：作为组件创建新Agent
   - 删除：不需要的Agent移除

→ 已创建的Agent作为能力组件，可复用可删除
```

### 场景4：让AI自动创建协作团队（高级）

```
用户操作：
1. 输入需求：
   "帮我创建3个角色：需求分析员、计划制定员、执行员
    他们要能相互协作完成分析需求、制定计划、实施计划、验证结果"

2. AI中台自动：
   - 分析需求 → 生成3个Agent配置
   - 配置协作流程 → 定义通信协议
   - 创建Agent → 注册到系统
   
3. 用户可以直接使用这个团队
```

---

## 三、架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    AI中台管理平台                             │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Web管理界面                         │   │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │   │
│  │   │Agent管理│  │实时测试  │  │团队创建 │  │能力市场│ │   │
│  │   │(增删改) │  │         │  │         │  │(复用) │ │   │
│  │   └─────────┘  └─────────┘  └─────────┘  └────────┘ │   │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │   │
│  │   │成本控制 │  │安全控制 │  │沙箱监控 │  │系统设置│ │   │
│  │   └─────────┘  └─────────┘  └─────────┘  └────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、核心功能

### 4.1 能力层级管理

所有层级都可以复用和管理：

| 层级 | 复用 | 可管理 |
|------|------|--------|
| **Tool** | 一个Tool可被多个Skill使用 | ✅ 查看、被引用统计、禁用 |
| **Skill** | 一个Skill可被多个Agent使用 | ✅ 查看、复用、编辑、删除 |
| **Agent** | 一个Agent就是一个角色 | ✅ 查看、复用、编辑、删除 |
| **Team** | 团队配置可复用 | ✅ 查看、复用、编辑、删除 |

#### 能力管理界面

```
┌─────────────────────────────────────────────────────────────┐
│  AI中台能力库                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 🔧 Tools (15) │ Skills (20) │ Agents (8) │ Teams(3)│  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  当前层级: Skills                                          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 名称              │ 包含Tools    │ 被引用数 │ 操作   │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │ rag-retrieval     │ search+kbase │ 3        │复用/删 │  │
│  │ code_analysis    │ file_reader  │ 5        │复用/删 │  │
│  │ bug_detection    │ code_exec   │ 2        │复用/删 │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  [+ 新建Skill]  [从Tools组合]                            │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 外部引入

支持从外部引入能力到AI中台：

| 来源 | 引入内容 | 示例 |
|------|---------|------|
| **MCP Server** | Tools | filesystem, git, puppeteer |
| **OpenAI/GitHub** | Agents | GPTs, Copilot Agents |
| **自定义API** | Tools | 外部API封装为Tool |
| **开源项目** | Skills/Tools | LangChain, AutoGPT |
| **导入配置** | Agents | JSON/YAML配置导入 |

### 4.3 Agent测试（实时可视化）

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent测试界面                              │
├─────────────────────────────────────────────────────────────┤
│  Agent: Bug检测助手                    状态: 🔄 运行中       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🧠 推理过程 (ReAct)                                │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │                                                     │   │
│  │  [1] Reason: "用户要求检测bug，我需要先读取代码"    │   │
│  │       ↓                                             │   │
│  │  [2] Act: 调用 file_reader 读取代码                  │   │
│  │       ↓                                             │   │
│  │  [3] Observe: "代码已读取：def divide(a,b):return│   │
│  │       ↓                                             │   │
│  │  [4] Reason: "发现潜在bug：除零风险，需要验证"      │   │
│  │       ↓                                             │   │
│  │  [5] Act: 调用 code_executor 执行测试              │   │
│  │       ↓                                             │   │
│  │  [6] Observe: "触发ZeroDivisionError!"            │   │
│  │       ↓                                             │   │
│  │  [7] Final: "检测到1个bug，已验证"                 │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🔧 工具调用                                        │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  ✓ file_reader    - 读取代码 (0.2s)                │   │
│  │  ✓ code_executor  - 执行测试 (0.5s)                │   │
│  │  ⏳ web_search     - 搜索CVE...                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  📊 执行结果                                        │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  状态: ✅ 完成    耗时: 2.3s                       │   │
│  │  发现问题: 1个 (严重)                              │   │
│  │  - 除零风险 (line 1)                               │   │
│  │  修复建议: 添加除零检查                             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 协作团队创建（高级）

```
# 用户需求
requirement = """
帮我创建3个分工明确的角色，能够相互协作：
1. 需求分析员 - 分析用户需求，拆解任务
2. 计划制定员 - 制定执行计划，安排步骤
3. 执行员 - 实施计划，验证结果
他们要能完成：分析需求 → 制定计划 → 实施 → 验证
"""

# AI自动生成团队
team = {
    "name": "任务执行团队",
    "members": [
        {
            "name": "需求分析员",
            "role": "分析用户需求，拆解具体任务",
            "outputs_to": ["计划制定员"]
        },
        {
            "name": "计划制定员", 
            "role": "根据任务制定详细执行计划",
            "inputs_from": ["需求分析员"],
            "outputs_to": ["执行员"]
        },
        {
            "name": "执行员",
            "role": "实施计划，验证结果",
            "inputs_from": ["计划制定员"]
        }
    ],
    "workflow": "需求分析员 → 计划制定员 → 执行员 → 验证"
}
```

### 4.5 执行控制

| 任务 | 说明 |
|------|------|
| 循环次数限制 | 设置Agent推理循环上限，防止无限循环 |
| 执行超时控制 | 设置单步超时和总超时时间 |
| 手动终止功能 | 提供终止按钮停止正在执行的Agent |
| 终止后处理 | 终止后保存当前状态，记录终止原因 |

**配置示例**:
```yaml
execution_control:
  max_iterations: 20          # 最大推理循环次数
  step_timeout: 30           # 单步超时(秒)
  total_timeout: 300          # 总超时(秒)
  enable_manual_terminate: true  # 允许手动终止
```

### 4.6 成本控制

| 任务 | 说明 |
|------|------|
| 收费模型显示 | 显示当前使用的LLMProvider及计费方式 |
| Token计数器 | 统计每次请求的输入/输出Token数量 |
| 费用计算 | 根据Token数量和单价计算费用 |
| 成本仪表盘 | 显示累计使用量、日/周/月统计 |
| 成本告警 | 设置预算阈值，超过时提醒 |

**成本控制数据结构**:
```python
class CostRecord:
    """成本记录"""
    session_id: str
    agent_id: str
    llm_provider: str          # deepseek/openai/etc.
    model: str                 # 模型名称
    input_tokens: int          # 输入Token
    output_tokens: int         # 输出Token
    input_cost: float          # 输入费用
    output_cost: float         # 输出费用
    total_cost: float          # 总费用
    timestamp: datetime        # 执行时间
```

**管理平台成本展示**:
```
+--------------------------------------------------+
  💰 成本控制中心                                    |
+--------------------------------------------------+
  当前模型: DeepSeek-V3  (¥1.00/1M input)           |
                                                  |
  本次执行:                                          |
  ├─ 输入Token: 2,450    ¥2.45                     |
  ├─ 输出Token: 8,230    ¥8.23                     |
  └─ 本次费用: ¥10.68                               |
                                                  |
  累计统计:                                          |
  ├─ 今日: ¥156.80 (15次)                           |
  ├─ 本周: ¥892.50 (78次)                           |
  └─ 本月: ¥3,450.25 (312次)                        |
                                                  |
  [设置预算告警]  [查看明细]  [导出报表]              |
+--------------------------------------------------+
```

### 4.7 信息安全控制

| 任务 | 说明 |
|------|------|
| 外发信息审查 | 对即将推送的外部信息进行审查 |
| 确认确认机制 | 用户确认后才能对外发送信息 |
| 白名单管理 | 可配置信任的外部接收方，无需确认 |
| 外发日志 | 记录所有外发信息的内容和接收方 |

**信息安全控制流程**:
```
用户请求外发 → 系统拦截 → 
    在白名单中 → 直接发送
    不在白名单 → 弹窗确认 → 用户同意 → 发送 | 拒绝 → 不发送
```

**账户信息安全**:
| 类型 | 保护措施 |
|------|------|
| 用户密码 | 加密存储 (bcrypt)，永不明文传输/显示 |
| 账户凭证 | AccessToken/RefreshToken加密存储 |
| API密钥 | 环境变量管理，不写入代码 |
| 个人信息 | 姓名、邮箱、手机号等脱敏处理 |
| 登录日志 | 记录登录时间/IP，便于审计 |
| 敏感操作 | 改密/删除等操作需二次确认 |

**密码安全策略**:
```yaml
password_policy:
  min_length: 8
  require_uppercase: true
  require_lowercase: true
  require_numbers: true
  require_special: true
  max_age_days: 90
  history_count: 5
```

### 4.8 沙箱安全扩展

> **核心理念**：将沙箱执行扩展到AI中台的所有执行环节

| 当前执行场景 | 当前状态 | 沙箱目标 | 安全等级 |
|------|------|------|-------|
| Python代码执行 | ✅ 已沙箱 | 保持 | 高 |
| Bash命令执行 | ✅ 已沙箱 | 保持 | 高 |
| Tool工具调用 | ❌ 无保护 | 沙箱化 | 高 |
| Agent推理执行 | ❌ 无保护 | 沙箱化 | 中 |
| LLM API调用 | ❌ 无保护 | 网络隔离 | 中 |
| 知识库操作 | ❌ 无保护 | 沙箱化 | 中 |
| 外部API调用 | ❌ 无保护 | 网络隔离 | 低 |

**新增沙箱类型**:
| 沙箱类型 | 功能 | 限制 |
|------|------|------|
| ToolSandbox | 隔离执行第三方Tool | 无网络/文件限制/进程限制 |
| AgentSandbox | 隔离Agent推理过程 | 内存/循环次数/超时限制 |
| APISandbox | 隔离外部API调用 | 仅允许白名单API |
| KnowledgeSandbox | 隔离知识库操作 | 仅允许授权的KB |

**沙箱策略配置**:
```yaml
sandbox_policy:
  enabled: true
  default_mode: strict
  
  components:
    code_executor:
      enabled: true
      mode: strict
      
    tool_executor:
      enabled: true
      mode: strict
      allowed_tools: [search, calculator, file_read]
      blocked_tools: [system_exec, network_request]
    
    agent_executor:
      enabled: true
      mode: moderate
      max_iterations: 50
      max_memory_mb: 512
    
    api_client:
      enabled: true
      mode: strict
      allowed_domains: [api.openai.com, api.deepseek.com]
```

---

## 五、存储方案

### 5.1 数据存储选择

| 数据类型 | 存储方案 | 说明 |
|------|---------|------|
| **Agent/Skill/Team配置** | SQLite + YAML文件 | SQLite存储元数据，YAML存储配置 |
| **执行日志** | SQLite | 轻量级，高效查询 |
| **成本统计** | SQLite | 按日期/Agent聚合统计 |
| **用户账户** | SQLite + bcrypt加密 | 安全存储 |
| **沙箱配置** | YAML文件 | 便于版本控制 |
| **白名单配置** | YAML文件 | 便于管理 |

### 5.2 数据库表设计

```sql
-- =============================================================================
-- AI中台管理平台 v1.0 数据库表结构 (实际实现)
-- =============================================================================

-- Agents表 - 存储AI智能体配置 (已实现)
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'agent',
    description TEXT,
    config_path TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reference_count INTEGER DEFAULT 0
);

-- Skills表 - 存储技能组合 (已实现)
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    tools TEXT,
    config_path TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reference_count INTEGER DEFAULT 0
);

-- Tools表 - 存储工具定义 (已实现)
CREATE TABLE IF NOT EXISTS tools (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    type TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent-Skill关联表 (已实现)
CREATE TABLE IF NOT EXISTS agent_skills (
    agent_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (agent_id, skill_id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- Agent-Tool关联表 (已实现)
CREATE TABLE IF NOT EXISTS agent_tools (
    agent_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (agent_id, tool_id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
);

-- Skill-Tool关联表 (已实现)
CREATE TABLE IF NOT EXISTS skill_tools (
    skill_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (skill_id, tool_id),
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
);

-- =============================================================================
-- AI中台模型管理 v2.0 - 模型市场、微调、训练 (已实现)
-- =============================================================================

-- 模型供应商表 (已实现)
CREATE TABLE IF NOT EXISTS model_providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    website TEXT,
    api_type TEXT NOT NULL DEFAULT 'openai_compatible',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 模型表 (已实现)
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    model_type TEXT NOT NULL,
    description TEXT,
    strengths TEXT,
    context_length INTEGER DEFAULT 4096,
    supports_function_calling BOOLEAN DEFAULT 0,
    supports_vision BOOLEAN DEFAULT 0,
    input_price REAL DEFAULT 0,
    output_price REAL DEFAULT 0,
    is_local BOOLEAN DEFAULT 0,
    ollama_model_name TEXT,
    status TEXT DEFAULT 'active',
    is_default BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES model_providers(id) ON DELETE CASCADE
);

-- 微调任务表 (已实现)
CREATE TABLE IF NOT EXISTS fine_tune_tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_model_id TEXT NOT NULL,
    description TEXT,
    data_source_type TEXT NOT NULL,
    data_source_path TEXT,
    data_source_url TEXT,
    data_format TEXT NOT NULL,
    epochs INTEGER DEFAULT 3,
    learning_rate REAL DEFAULT 0.0001,
    batch_size INTEGER DEFAULT 4,
    status TEXT DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    output_model_name TEXT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (base_model_id) REFERENCES models(id) ON DELETE SET NULL
);

-- 训练任务表 (已实现)
CREATE TABLE IF NOT EXISTS training_tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_model_id TEXT,
    description TEXT,
    model_type TEXT NOT NULL,
    training_data_type TEXT NOT NULL,
    data_source_path TEXT,
    data_source_url TEXT,
    data_format TEXT NOT NULL,
    epochs INTEGER DEFAULT 10,
    learning_rate REAL DEFAULT 0.00001,
    batch_size INTEGER DEFAULT 8,
    vocabulary_size INTEGER,
    seq_length INTEGER DEFAULT 512,
    status TEXT DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    current_epoch INTEGER DEFAULT 0,
    current_loss REAL,
    output_model_name TEXT,
    error_message TEXT,
    config_json TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (base_model_id) REFERENCES models(id) ON DELETE SET NULL
);

-- 模型使用记录表 (已实现)
CREATE TABLE IF NOT EXISTS model_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    status TEXT DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
);

-- 训练指标记录表 (已实现)
CREATE TABLE IF NOT EXISTS training_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    epoch INTEGER,
    step INTEGER,
    loss REAL,
    accuracy REAL,
    learning_rate REAL,
    batch_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 计划中但当前在内存中实现的表 (注释)
-- =============================================================================
/*
-- 执行日志 (当前在内存中实现)
CREATE TABLE execution_logs (...);

-- 成本记录 (当前在内存中实现)
CREATE TABLE cost_records (...);

-- 用户账户 (当前使用简单的身份验证，数据库表待实现)
CREATE TABLE users (...);

-- 外发白名单 (当前在内存中实现)
CREATE TABLE whitelist (...);
*/
```

---

## 六、实施计划

### 阶段1：Agent管理基础 ✅ 已完成 (2026-03-04)

| 任务 | 说明 | 状态 |
|------|------|------|
| Agent配置存储 | 使用SQLite + YAML文件 | ✅ 已实现 - `migrations/v1.0_create_tables.sql` |
| Agent CRUD API | 创建、读取、更新、删除Agent | ✅ 已实现 - `src/api/agents.py` |
| Skill组合界面 | 选择现有Skills组合成新Agent | ✅ 已实现 - `src/ui/management.py` skill_page() |
| Tool选择界面 | 选择Agent可用的Tools | ✅ 已实现 - `src/ui/management.py` tool_page() |
| 基础管理界面 | Web页面管理Agent | ✅ 已实现 - `src/ui/management.py` Streamlit应用 |
| **能力检查器** | 创建前自动检查现有Skills/Tools是否满足需求 | ✅ 已实现 - `src/ui/management.py` capability_check_page() |

### 阶段2：Agent测试功能 + 实时可视化 ✅ 已完成 (2026-03-04)

| 任务 | 说明 | 状态 |
|------|------|------|
| 测试执行接口 | 调用Agent执行任务 | ✅ 已实现 - `src/api/test_execution.py` |
| SSE实时推送 | Server-Sent Events推送执行过程 | ✅ 已实现 - `src/api/test_execution.py` execute_agent_test_stream() |
| 推理链可视化 | 显示ReAct推理过程 | ✅ 已实现 - `src/ui/management.py` test_page() 推理链展示 |
| 工具调用可视化 | 实时显示工具调用 | ✅ 已实现 - `src/ui/management.py` test_page() 工具调用展示 |
| 执行日志 | 记录每个步骤的输入输出 | ✅ 已实现 - `src/services/test_execution.py` 记录执行步骤 |

### 阶段3：协作团队创建 ✅ 已完成 (2026-03-04)

| 任务 | 说明 | 状态 |
|------|------|------|
| 团队配置模型 | 定义多Agent协作配置 | ✅ 已实现 - `src/api/teams.py` TeamCreateRequest模型 |
| 团队创建API | 根据需求自动生成团队 | ✅ 已实现 - `src/api/teams.py` create_team() 和 suggest_team() |
| 协作执行引擎 | 按流程协调多Agent | ✅ 已实现 - `src/api/teams.py` execute_team_task() 模拟执行 |
| 团队测试可视化 | 显示多Agent协作过程 | ✅ 已实现 - `src/ui/management.py` team_page() 团队测试界面 |

### 阶段4：执行控制 ✅ 已完成 (2026-03-04)

| 任务 | 说明 | 状态 |
|------|------|------|
| 循环次数限制 | 设置Agent推理循环上限 | ✅ 已实现 - `src/api/execution_control.py` ExecutionConfigRequest.max_loops |
| 执行超时控制 | 设置单步超时和总超时时间 | ✅ 已实现 - `src/api/execution_control.py` step_timeout, total_timeout |
| 手动终止功能 | 提供终止按钮停止正在执行的Agent | ✅ 已实现 - `src/api/execution_control.py` terminate_execution() |
| 终止后处理 | 终止后保存当前状态，记录终止原因 | ✅ 已实现 - `src/api/execution_control.py` terminate_execution() 保存终止原因 |

### 阶段5：成本控制 ✅ 已完成 (2026-03-04)

| 任务 | 说明 | 状态 |
|------|------|------|
| 收费模型显示 | 显示当前使用的LLMProvider及计费方式 | ✅ 已实现 - `src/api/cost_control.py` get_providers(), get_current_provider() |
| Token计数器 | 统计每次请求的输入/输出Token数量 | ✅ 已实现 - `src/api/cost_control.py` record_tokens() |
| 费用计算 | 根据Token数量和单价计算费用 | ✅ 已实现 - `src/services/cost_control.py` calculate_cost() |
| 成本仪表盘 | 显示累计使用量、日/周/月统计 | ✅ 已实现 - `src/api/cost_control.py` get_total_cost(), get_period_cost() |
| 成本告警 | 设置预算阈值，超过时提醒 | ✅ 已实现 - `src/api/cost_control.py` set_budget(), check_budget() |

### 阶段6：信息安全控制 ✅ 已完成 (2026-03-04)

| 任务 | 说明 | 状态 |
|------|------|------|
| 外发信息审查 | 对即将推送的外部信息进行审查 | ✅ 已实现 - `src/api/security_control.py` check_outbound() 敏感词检测 |
| 确认确认机制 | 用户确认后才能对外发送信息 | ✅ 已实现 - `src/api/security_control.py` confirm_outbound() 用户确认 |
| 白名单管理 | 可配置信任的外部接收方 | ✅ 已实现 - `src/api/security_control.py` add_whitelist(), get_whitelist() |
| 账户安全 | 密码加密、登录审计 | ✅ 已实现 - `src/api/auth.py` 密码加密和登录审计 |
| 外发日志 | 记录所有外发信息 | ✅ 已实现 - `src/services/security_control.py` 记录外发请求日志 |

### 阶段7：沙箱安全扩展 ✅ 已完成 (2026-03-04)

| 任务 | 说明 | 状态 |
|------|------|------|
| ToolSandbox | 隔离执行第三方Tool | ✅ 已实现 - `src/api/sandbox.py` execute_tool_sandboxed() |
| AgentSandbox | 隔离Agent推理过程 | ✅ 已实现 - `src/services/sandbox_service.py` Agent沙箱执行 |
| APISandbox | 隔离外部API调用 | ✅ 已实现 - `src/api/sandbox.py` execute_api_sandboxed() |
| KnowledgeSandbox | 隔离知识库操作 | ✅ 已实现 - `src/services/sandbox_service.py` 知识库操作隔离 |
| 沙箱监控界面 | 实时显示沙箱状态 | ✅ 已实现 - `src/api/sandbox.py` get_sandbox_status() |

---

## 七、技术实现

### 7.1 实时推送 (SSE)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sse_starlette.sse as sse

@app.get("/api/v1/agents/{agent_id}/test/stream")
async def test_agent_stream(agent_id: str, task: str):
    """测试Agent并实时推送执行过程"""
    
    async def event_generator():
        agent = get_agent(agent_id)
        
        # 逐步推送执行过程
        async for step in agent.execute_with_steps(task):
            yield {
                "event": "step",
                "data": {
                    "step": step.number,
                    "type": step.type,  # reason/act/observe
                    "content": step.content,
                    "tool": step.tool_name,
                    "tool_result": step.tool_result,
                }
            }
        
        # 最终结果
        yield {
            "event": "complete",
            "data": final_result
        }
    
    return sse.EventSourceResponse(event_generator())
```

### 7.2 前端显示

```javascript
const eventSource = new EventSource(`/api/v1/agents/${agentId}/test/stream?task=${task}`);

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.event === 'step') {
        addReasoningStep(data.data);
        if (data.data.tool) {
            updateToolStatus(data.data.tool, 'running');
        }
    } else if (data.event === 'complete') {
        showFinalResult(data.data);
    }
};
```

---

## 八、版本规划

| 版本 | 功能 | 状态 | 实际完成时间 |
|------|------|------|------|
| v1.0 | Agent CRUD + Skill组合 + 能力检查 + 管理界面 | ✅ 已实现 | 2026-03-02 |
| v1.1 | Agent测试 + 实时可视化 | ✅ 已实现 | 2026-03-02 |
| v1.2 | 协作团队创建 + 可视化 | ✅ 已实现 | 2026-03-02 |
| v1.3 | 执行控制 (循环限制/超时/终止) | ✅ 已实现 | 2026-03-02 |
| v1.4 | 成本控制 (Token统计/费用计算) | ✅ 已实现 | 2026-03-02 |
| v1.5 | 信息安全控制 (外发确认/白名单/账户安全) | ✅ 已实现 | 2026-03-02 |
| v1.6 | 沙箱安全扩展 (Tool/Agent/API沙箱) | ✅ 已实现 | 2026-03-02 |
| v9.0 | 完整AI中台管理平台 (所有功能集成) | ✅ 已实现 | 2026-03-04 |

---

## 九、设计原则

1. **能力检查优先**
   - 创建新Agent前，先检查现有Skills/Tools是否满足
   - 如果满足，引导用户使用现有能力组合

2. **谨慎扩展**
   - 只有现有能力完全无法满足时才扩展
   - 扩展需要用户确认，避免过度膨胀

3. **保持精简**
   - 通过组合现有能力满足大部分需求
   - 只在真正必要时才编写新代码

---

## 十、下一步

确认方案后开始实施。

---

*方案版本: v9.0 (已实现)*
*生成时间: 2026-03-02*
*最后同步时间: 2026-03-04*
