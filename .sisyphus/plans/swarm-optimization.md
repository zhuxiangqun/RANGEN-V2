# RANGEN V2 - ClawTeam 蜂群智能优化计划

## TL;DR

> **快速摘要**: 基于 ClawTeam 分析，对 RANGEN V2 进行蜂群智能优化：轻量协调层、团队模板系统、文件系统收件箱、Git Worktree 隔离
>
> **核心理念**: "AI Agent 自己组队干活" - 借鉴 ClawTeam 的极简协调机制
>
> **预计工作量**: Medium
> **并行执行**: YES

---

## Context

### ClawTeam 核心理念

```
传统模式:  1 个人 ↔ 1 个 AI
蜂群模式:  1 个人 ↔ 一支 AI 军团

ClawTeam 核心:
- CLI 驱动自协调 (clawteam spawn, inbox send, task update)
- 文件系统收件箱 (无需 Redis)
- Git Worktree 隔离 (零冲突)
- TOML 模板定义团队
- 自动注入协调提示词
```

### RANGEN 当前状态

**已有组件**:
- `MultiAgentCoordinator` (800行) - 复杂的多Agent协调
- `AgentCoordinator` - 任务路由和调度
- `ExpertAgent` - 专业Agent基类
- `EventBus` - 事件总线通信
- Gateway - 多渠道接入

**痛点**:
- 协调机制偏重 (EventBus/Redis)
- Agent 协作依赖 LangGraph 状态机
- 无轻量级团队模板系统
- 无文件系统级隔离

### 访谈决策
- 优化范围: 蜂群协调层 + 团队模板
- 保留现有架构，向下兼容
- 不破坏现有 FastAPI/Gateway

---

## Work Objectives

### 核心目标
将 RANGEN 升级为支持 **蜂群智能** 的平台，让 Agent 自主组队、分配任务、实时通信。

### 具体交付物

1. **SwarmCoordinator** - 蜂群协调器 (CLI 驱动)
2. **TeamTemplate** - TOML 团队模板系统
3. **FileInbox** - 文件系统收件箱 (替代 Redis)
4. **GitWorktreeIsolation** - Git Worktree 隔离
5. **SwarmBoard** - 终端/Tmux 监控面板

### Definition of Done
- [ ] Agent 可通过 CLI 命令自主创建子 Agent
- [ ] 支持 TOML 模板一键启动专业团队
- [ ] 收件箱支持点对点 + 广播消息
- [ ] 任务支持依赖管理 (blocked-by)
- [ ] 监控面板实时显示团队状态

### Must Have
- 向下兼容现有 Agent 架构
- 保持 FastAPI 服务正常
- 不删除现有功能

### Must NOT
- 不替换现有的 LangGraph 工作流
- 不删除 EventBus/Gateway
- 不破坏现有 API 端点

---

## Execution Strategy

### 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    RANGEN Swarm Architecture                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     ┌─────────────────────────────────┐  │
│  │  SwarmCLI   │     │     SwarmCoordinator             │  │
│  │  (CLI命令)  │────▶│  - spawn() 子Agent              │  │
│  │  - spawn   │     │  - inbox_send() 消息             │  │
│  │  - inbox   │     │  - task_update() 状态            │  │
│  │  - task    │     │  - board_show() 监控            │  │
│  └─────────────┘     └─────────────────────────────────┘  │
│                              │                               │
│         ┌───────────────────┼───────────────────┐           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  TeamStore  │    │  FileInbox  │    │ TaskStore   │    │
│  │  (TOML)    │    │  (文件系统)  │    │  (JSON)    │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────────────────────────────────────────┐     │
│  │           Agent Workspace (Git Worktree)          │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │     │
│  │  │ Agent-1 │  │ Agent-2 │  │ Agent-3 │      │     │
│  │  │ (独立分支) │  │ (独立分支) │  │ (独立分支) │      │     │
│  │  └──────────┘  └──────────┘  └──────────┘      │     │
│  └─────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Wave 1: 核心组件

| 任务 | 说明 | 文件 |
|------|------|------|
| T1 | SwarmCLI 命令行接口 | `src/swarm/cli.py` |
| T2 | SwarmCoordinator 协调器 | `src/swarm/coordinator.py` |
| T3 | FileInbox 文件系统收件箱 | `src/swarm/inbox.py` |
| T4 | TaskStore 任务存储 | `src/swarm/task_store.py` |

### Wave 2: 团队系统

| 任务 | 说明 | 文件 |
|------|------|------|
| T5 | TeamTemplate TOML 模板 | `src/swarm/team_template.py` |
| T6 | GitWorktreeIsolation 隔离 | `src/swarm/worktree.py` |
| T7 | SwarmBoard 监控面板 | `src/swarm/board.py` |
| T8 | CLI 集成到 Agent | `src/agents/swarm_mixin.py` |

### Wave 3: 集成

| 任务 | 说明 | 文件 |
|------|------|------|
| T9 | 集成到 SmartConversationAgent | `src/agents/smart_conversation_agent.py` |
| T10 | 文档和使用示例 | `docs/swarm/README.md` |
| T11 | 测试用例 | `tests/swarm/` |

---

## Task Details

### T1: SwarmCLI 命令行接口

**What to do**:
- 创建 `src/swarm/cli.py`
- 实现 Typer CLI 命令
- 命令: `spawn`, `inbox`, `task`, `board`, `launch`

**CLI 命令设计**:
```bash
# 创建团队
rangenswarm team create my-team --description "开发团队"

# 启动 Agent
rangenswarm spawn --team my-team --agent-name worker1 --task "实现认证模块"

# 消息通信
rangenswarm inbox send my-team leader "认证完成"
rangenswarm inbox broadcast my-team "会议通知"

# 任务管理
rangenswarm task create my-team "设计API" --blocked-by T1
rangenswarm task update my-team T2 --status completed

# 监控面板
rangenswarm board show my-team
rangenswarm board attach my-team  # tmux 分屏

# 启动团队模板
rangenswarm launch research --team auto-research --goal "优化LLM训练"
```

**Must NOT do**:
- 不使用 Click/Typer 以外的框架
- 不破坏现有命令行工具

---

### T2: SwarmCoordinator 协调器

**What to do**:
- 创建 `src/swarm/coordinator.py`
- 实现 Agent 生命周期管理
- 实现任务分配和依赖跟踪

**核心方法**:
```python
class SwarmCoordinator:
    def spawn_agent(self, team: str, name: str, task: str) -> AgentInfo:
        """启动子 Agent"""
        
    def inbox_send(self, team: str, to: str, message: str) -> bool:
        """发送消息"""
        
    def task_update(self, team: str, task_id: str, status: str) -> bool:
        """更新任务状态 (触发依赖解除)"""
        
    def board_show(self, team: str) -> BoardState:
        """获取团队看板状态"""
```

---

### T3: FileInbox 文件系统收件箱

**What to do**:
- 创建 `src/swarm/inbox.py`
- 基于文件系统实现消息传递
- 支持点对点和广播

**存储结构**:
```
.swarm/
  └── {team}/
      └── inbox/
          ├── leader/
          │   ├── 001.json  # 消息
          │   └── 002.json
          ├── worker1/
          └── broadcast/
```

**核心方法**:
```python
class FileInbox:
    def send(self, team: str, to: str, message: str) -> str:
        """发送消息到收件箱"""
        
    def receive(self, team: str, agent: str) -> List[Message]:
        """接收并消费消息"""
        
    def peek(self, team: str, agent: str) -> List[Message]:
        """查看消息 (不消费)"""
        
    def broadcast(self, team: str, message: str) -> None:
        """广播给所有成员"""
```

---

### T4: TaskStore 任务存储

**What to do**:
- 创建 `src/swarm/task_store.py`
- 实现任务 CRUD + 依赖管理
- 支持 blocked-by 自动解除

**存储结构**:
```json
{
  "tasks": [
    {
      "id": "T1",
      "title": "设计API",
      "owner": "architect",
      "status": "completed",
      "blocked_by": []
    },
    {
      "id": "T2", 
      "title": "实现认证",
      "owner": "backend",
      "status": "in_progress",
      "blocked_by": ["T1"]  // T1 完成后自动解除
    }
  ]
}
```

---

### T5: TeamTemplate TOML 模板

**What to do**:
- 创建 `src/swarm/team_template.py`
- 定义 TOML 模板格式
- 实现 `launch` 命令

**模板格式**:
```toml
# research_team.toml
[team]
name = "research"
description = "AI 研究团队"

[leader]
agent_type = "chief"
prompt = "你是一个研究团队的Leader，负责协调团队工作"

[[members]]
name = "researcher1"
agent_type = "reasoning"
prompt = "你是一个深度学习研究员，专注于模型优化"
specialization = "model_optimization"

[[members]]
name = "researcher2" 
agent_type = "reasoning"
prompt = "你是一个数据科学家，专注于数据分析"
specialization = "data_analysis"

[[members]]
name = "coder"
agent_type = "engineering"
prompt = "你是一个全栈工程师，负责实现实验代码"
specialization = "code_implementation"
```

**使用方式**:
```bash
rangenswarm launch research_team.toml --team my-research --goal "优化transformer架构"
```

---

### T6: GitWorktreeIsolation 工作区隔离

**What to do**:
- 创建 `src/swarm/worktree.py`
- 为每个 Agent 创建独立 Git Worktree
- 支持分支隔离和合并

**工作流程**:
```bash
# Leader 创建团队时
git worktree add .swarm/{team}/{agent} refs/heads/clawteam/{team}/{agent}

# Agent 在独立分支工作
git checkout clawteam/{team}/{agent}

# 完成时 Leader 合并
git checkout main
git merge clawteam/{team}/{agent}
```

---

### T7: SwarmBoard 监控面板

**What to do**:
- 创建 `src/swarm/board.py`
- 实现终端看板 (rich)
- 支持 tmux 分屏

**终端看板**:
```
┌─────────────────────────────────────────────────────────┐
│  🦞 Team: auto-research                    [8 Agents]   │
├─────────────────────────────────────────────────────────┤
│  📋 Tasks                                             │
│  ┌─────────┬────────────┬──────────┬─────────┐        │
│  │ ID      │ Task       │ Owner    │ Status  │        │
│  ├─────────┼────────────┼──────────┼─────────┤        │
│  │ T1      │ 设计API    │ architect │ ✅ Done │        │
│  │ T2      │ 实现后端   │ backend  │ 🔄 WIP  │        │
│  │ T3      │ 实现前端   │ frontend │ ⏳ Blocked │      │
│  └─────────┴────────────┴──────────┴─────────┘        │
├─────────────────────────────────────────────────────────┤
│  💬 Inbox (leader)                                    │
│  • researcher1: "实验完成，精度提升 2%"                │
│  • coder: "代码已提交，请审查"                         │
├─────────────────────────────────────────────────────────┤
│  🤖 Agents                                            │
│  • leader    🟢 运行中                                │
│  • researcher1 🟢 运行中                              │
│  • backend   🟡 空闲                                  │
└─────────────────────────────────────────────────────────┘
```

---

### T8: SwarmMixin Agent 混入

**What to do**:
- 创建 `src/agents/swarm_mixin.py`
- 让 Agent 支持蜂群协调
- 自动注入协调提示词

**Mixin 使用**:
```python
class ReasoningAgent(SwarmMixin, BaseAgent):
    def __init__(self):
        super().__init__()
        self.inject_swarm_coordination("reasoning_team")
```

**自动注入的提示词**:
```
## Coordination Protocol (auto-injected)

- 📋 查看任务: rangenswarm task list <team> --owner me
- ✅ 完成状态: rangenswarm task update <team> <id> --status completed
- 💬 汇报Leader: rangenswarm inbox send <team> leader "状态更新..."
- 📨 检查收件: rangenswarm inbox receive <team>
```

---

## Verification Strategy

### Test Scenarios

```bash
# 1. 团队生命周期
rangenswarm team create test-team
rangenswarm team status test-team
rangenswarm team cleanup test-team --force

# 2. Agent 启动
rangenswarm spawn --team test-team --agent-name worker1 --task "测试任务"
rangenswarm board show test-team

# 3. 消息通信
rangenswarm inbox send test-team leader "测试消息"
rangenswarm inbox receive test-team leader

# 4. 任务依赖
rangenswarm task create test-team "任务A"
rangenswarm task create test-team "任务B" --blocked-by T1
rangenswarm task update test-team T1 --status completed
# T2 应自动解除 blocked 状态

# 5. 团队模板
rangenswarm launch research --team my-team --goal "测试目标"
```

---

## 优化收益

### 1. 架构简化
| 组件 | 优化前 | 优化后 |
|------|--------|--------|
| 消息队列 | Redis/EventBus | 文件系统 |
| 协调方式 | LangGraph 状态机 | CLI 命令 |
| 部署复杂度 | 高 (多服务) | 低 (文件系统) |

### 2. Agent 自治增强
- Agent 可自主创建子 Agent
- 无需人工编排任务
- 支持动态任务分配

### 3. 隔离性提升
- Git Worktree 完全隔离
- 零冲突并行开发
- 支持独立回滚

### 4. 可观测性
- 终端实时看板
- Tmux 分屏监控
- 任务依赖可视化

### 5. 模板复用
- 一键启动专业团队
- 预定义角色协作
- 自定义模板扩展

---

## Timeline

```
Week 1:
├── T1: SwarmCLI 接口
├── T2: SwarmCoordinator
├── T3: FileInbox
└── T4: TaskStore

Week 2:
├── T5: TeamTemplate
├── T6: GitWorktreeIsolation
├── T7: SwarmBoard
└── T8: SwarmMixin

Week 3:
├── T9: 集成测试
├── T10: 文档
└── T11: 完整测试
```

---

## Success Criteria

- [ ] `rangenswarm --help` 正常显示
- [ ] 可以创建团队并启动 Agent
- [ ] Agent 之间可以收发消息
- [ ] 任务依赖自动解除
- [ ] 终端看板实时更新
- [ ] TOML 模板一键启动团队
- [ ] 现有 API 和 Gateway 不受影响

---

## Commit Strategy

```bash
git commit -m "feat(swarm): add ClawTeam-inspired swarm coordination layer"
git commit -m "feat(swarm): add TOML team template system"
git commit -m "feat(swarm): add GitWorktree isolation"
git commit -m "feat(swarm): add SwarmBoard terminal dashboard"
git commit -m "feat(swarm): integrate with SmartConversationAgent"
```
