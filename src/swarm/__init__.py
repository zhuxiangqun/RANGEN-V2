"""
RANGEN Swarm - Agent 蜂群协调系统

核心组件:
- SmartSwarmRouter: 智能路由 (自动选择 Lite/Full)
- SwarmCoordinator: 协调器 (团队管理、Agent 生命周期)
- FileInbox: 文件系统收件箱 (消息传递)
- TaskStore: 任务存储 (任务管理、依赖跟踪)
- TeamStore: 团队存储 (团队生命周期)
- TeamTemplate: TOML 团队模板 (一键启动团队)
- GitWorktreeManager: Git Worktree 隔离
- SwarmBoard: 终端看板

使用示例:
```python
from src.swarm import get_coordinator, auto_route, launch_team_from_template

# 智能路由
decision = auto_route("做一个完整的电商系统")
# decision.mode == ExecutionMode.FULL

# 协调器
coord = get_coordinator()
coord.create_team("my-team")
coord.spawn_agent("my-team", "worker1", "实现认证模块")

# 从模板启动团队
result = launch_team_from_template(
    "research", "my-research", "优化transformer架构", coord
)

# 看板监控
from src.swarm.board import SwarmBoard
board = SwarmBoard(coord)
board.show("my-team")
board.watch("my-team", interval=3)
```
"""

from .smart_router import SmartSwarmRouter, auto_route, get_router, ExecutionMode, RouteContext, RouteDecision
from .coordinator import SwarmCoordinator, get_coordinator
from .inbox import FileInbox, Message
from .task_store import TaskStore, Task, TaskStatus
from .team_store import TeamStore, TeamConfig, AgentInfo
from .team_template import TeamTemplate, TemplateRegistry, launch_team_from_template
from .worktree import GitWorktreeManager, WorktreeInfo
from .board import SwarmBoard

__all__ = [
    # Smart Router
    "SmartSwarmRouter",
    "auto_route",
    "get_router",
    "ExecutionMode",
    "RouteContext",
    "RouteDecision",
    # Coordinator
    "SwarmCoordinator",
    "get_coordinator",
    # Inbox
    "FileInbox",
    "Message",
    # Task
    "TaskStore",
    "Task",
    "TaskStatus",
    # Team
    "TeamStore",
    "TeamConfig",
    "AgentInfo",
    # Template
    "TeamTemplate",
    "TemplateRegistry",
    "launch_team_from_template",
    # Worktree
    "GitWorktreeManager",
    "WorktreeInfo",
    # Board
    "SwarmBoard",
]
