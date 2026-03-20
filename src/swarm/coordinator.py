"""
Swarm 协调器

协调 Agent 蜂群工作:
- 启动/停止 Agent
- 任务分配和依赖管理
- Agent 间通信
- 团队生命周期管理
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Literal

from .inbox import FileInbox
from .task_store import TaskStore, TaskStatus
from .team_store import TeamStore, AgentInfo


class SwarmCoordinator:
    """
    Swarm 协调器
    
    统一的协调接口:
    - 团队管理
    - Agent 生命周期
    - 任务管理
    - 消息通信
    """
    
    def __init__(self, base_dir: str = ".swarm"):
        self.base_dir = Path(base_dir)
        self.inbox = FileInbox(str(self.base_dir))
        self.tasks = TaskStore(str(self.base_dir))
        self.teams = TeamStore(str(self.base_dir))
    
    # =========================================================================
    # 团队管理
    # =========================================================================
    
    def create_team(self, name: str, description: str = "") -> Dict[str, Any]:
        """创建团队"""
        config = self.teams.create_team(name, description)
        return {
            "success": True,
            "team": config.name,
            "leader": config.leader,
            "created_at": config.created_at
        }
    
    def delete_team(self, name: str, force: bool = False) -> Dict[str, Any]:
        """删除团队"""
        # 如果有运行中的 Agent，不允许删除
        if not force:
            agents = self.teams.list_agents(name)
            running = [a for a in agents if a.status == "working"]
            if running:
                return {
                    "success": False,
                    "error": f"团队有 {len(running)} 个运行中的 Agent，使用 --force 强制删除"
                }
        
        # 清理所有数据
        self.inbox.cleanup(name)
        self.tasks.cleanup(name)
        self.teams.delete_team(name)
        
        return {"success": True, "team": name}
    
    def list_teams(self) -> List[Dict[str, Any]]:
        """列出所有团队"""
        teams = self.teams.list_teams()
        result = []
        for name in teams:
            status = self.teams.get_team_status(name)
            result.append(status)
        return result
    
    def get_team_status(self, name: str) -> Dict[str, Any]:
        """获取团队状态"""
        return self.teams.get_team_status(name)
    
    # =========================================================================
    # Agent 管理
    # =========================================================================
    
    def spawn_agent(
        self,
        team: str,
        name: str,
        task: str = "",
        agent_type: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """
        启动 Agent
        
        Args:
            team: 团队名
            name: Agent 名
            task: 初始任务
            agent_type: Agent 类型
        """
        # 确保团队存在
        if not self.teams.get_team(team):
            self.create_team(team)
        
        # 检查是否已存在
        existing = self.teams.get_agent(team, name)
        if existing:
            return {
                "success": False,
                "error": f"Agent {name} 已存在"
            }
        
        # 添加 Agent
        agent_info = self.teams.add_agent(
            team=team,
            name=name,
            status="idle",
            task=task,
            metadata={"agent_type": agent_type, **kwargs}
        )
        
        # 如果有初始任务，创建任务
        if task:
            task_obj = self.tasks.create_task(
                team=team,
                title=task,
                owner=name,
                description=f"由 {name} 执行的初始任务"
            )
            self.tasks.update_status(team, task_obj.id, TaskStatus.IN_PROGRESS)
            self.teams.update_agent(team, name, status="working", task=task)
        
        return {
            "success": True,
            "agent": name,
            "team": team,
            "task": task,
            "spawned_at": agent_info.started_at
        }
    
    def stop_agent(self, team: str, name: str) -> Dict[str, Any]:
        """停止 Agent"""
        agent = self.teams.get_agent(team, name)
        if not agent:
            return {"success": False, "error": f"Agent {name} 不存在"}
        
        # 停止进程
        if agent.pid:
            try:
                import os
                os.kill(agent.pid, 9)
            except:
                pass
        
        # 更新状态
        self.teams.update_agent(team, name, status="completed")
        
        # 查找并更新关联任务
        for task in self.tasks.list_tasks(team, owner=name):
            if task.status == TaskStatus.IN_PROGRESS:
                self.tasks.update_status(team, task.id, TaskStatus.COMPLETED)
        
        return {"success": True, "agent": name}
    
    def list_agents(self, team: str) -> List[Dict[str, Any]]:
        """列出团队 Agent"""
        agents = self.teams.list_agents(team)
        return [a.to_dict() for a in agents]
    
    # =========================================================================
    # 任务管理
    # =========================================================================
    
    def create_task(
        self,
        team: str,
        title: str,
        owner: str = "",
        blocked_by: Optional[List[str]] = None,
        priority: int = 0
    ) -> Dict[str, Any]:
        """创建任务"""
        task = self.tasks.create_task(
            team=team,
            title=title,
            owner=owner,
            blocked_by=blocked_by,
            priority=priority
        )
        
        return {
            "success": True,
            "task_id": task.id,
            "title": task.title,
            "status": task.status,
            "blocked_by": task.blocked_by
        }
    
    def update_task_status(
        self,
        team: str,
        task_id: str,
        status: str,
        result: str = ""
    ) -> Dict[str, Any]:
        """更新任务状态"""
        task = self.tasks.update_status(team, task_id, status, result)
        if not task:
            return {"success": False, "error": f"任务 {task_id} 不存在"}
        
        # 如果是 completed，通知负责人
        if status == TaskStatus.COMPLETED:
            self.inbox.send(
                team=team,
                to_agent=task.owner if task.owner else "leader",
                content=f"任务 {task_id} ({task.title}) 已完成: {result}",
                from_agent="system"
            )
        
        return {
            "success": True,
            "task_id": task.id,
            "status": task.status,
            "result": task.result
        }
    
    def list_tasks(
        self,
        team: str,
        status: Optional[str] = None,
        owner: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """列出任务"""
        tasks = self.tasks.list_tasks(team, status=status, owner=owner)
        return [t.to_dict() for t in tasks]
    
    def get_task_stats(self, team: str) -> Dict[str, int]:
        """获取任务统计"""
        return self.tasks.get_stats(team)
    
    # =========================================================================
    # 消息通信
    # =========================================================================
    
    def send_message(
        self,
        team: str,
        to_agent: str,
        content: str,
        from_agent: str = "user"
    ) -> Dict[str, Any]:
        """发送消息"""
        msg_id = self.inbox.send(team, to_agent, content, from_agent)
        return {
            "success": True,
            "message_id": msg_id,
            "to": to_agent,
            "from": from_agent
        }
    
    def receive_messages(
        self,
        team: str,
        agent: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """接收消息 (消费)"""
        messages = self.inbox.receive(team, agent, limit)
        return [m.to_dict() for m in messages]
    
    def peek_messages(
        self,
        team: str,
        agent: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """查看消息 (不消费)"""
        messages = self.inbox.peek(team, agent, limit)
        return [m.to_dict() for m in messages]
    
    def broadcast(
        self,
        team: str,
        content: str,
        from_agent: str = "user"
    ) -> Dict[str, Any]:
        """广播消息"""
        msg_id = self.inbox.broadcast(team, from_agent, content)
        return {
            "success": True,
            "message_id": msg_id,
            "broadcast": True
        }
    
    # =========================================================================
    # 监控面板
    # =========================================================================
    
    def get_board_state(self, team: str) -> Dict[str, Any]:
        """获取看板状态"""
        team_status = self.teams.get_team_status(team)
        task_stats = self.tasks.get_stats(team)
        agents = self.teams.list_agents(team)
        tasks = self.tasks.list_tasks(team)
        
        return {
            "team": team_status,
            "tasks": task_stats,
            "agents": [a.to_dict() for a in agents],
            "recent_tasks": [t.to_dict() for t in tasks[:10]]
        }


# =============================================================================
# 全局单例
# =============================================================================

_coordinator: Optional[SwarmCoordinator] = None


def get_coordinator(base_dir: str = ".swarm") -> SwarmCoordinator:
    """获取协调器实例"""
    global _coordinator
    if _coordinator is None:
        _coordinator = SwarmCoordinator(base_dir)
    return _coordinator


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    coordinator = get_coordinator("/tmp/.swarm-test")
    
    # 清理
    if "demo" in [t["name"] for t in coordinator.list_teams()]:
        coordinator.delete_team("demo", force=True)
    
    # 创建团队
    print("=" * 50)
    print("1. 创建团队")
    result = coordinator.create_team("demo", "演示团队")
    print(f"   {result}")
    
    # 启动 Agent
    print("\n2. 启动 Agent")
    result = coordinator.spawn_agent("demo", "researcher1", "探索模型深度")
    print(f"   {result}")
    result = coordinator.spawn_agent("demo", "researcher2", "探索学习率")
    print(f"   {result}")
    
    # 创建任务链
    print("\n3. 创建任务链")
    t1 = coordinator.create_task("demo", "设计API架构", owner="architect", priority=10)
    print(f"   {t1}")
    t2 = coordinator.create_task("demo", "实现后端", owner="backend", blocked_by=[t1["task_id"]])
    print(f"   {t2}")
    t3 = coordinator.create_task("demo", "编写测试", owner="tester", blocked_by=[t2["task_id"]])
    print(f"   {t3}")
    
    # 发送消息
    print("\n4. 发送消息")
    result = coordinator.send_message("demo", "researcher1", "请优先完成模型深度实验")
    print(f"   {result}")
    result = coordinator.broadcast("demo", "全体注意：下午3点有同步会议")
    print(f"   {result}")
    
    # 查看看板
    print("\n5. 看板状态")
    board = coordinator.get_board_state("demo")
    print(f"   团队: {board['team']['name']}")
    print(f"   Agent 数量: {board['team']['member_count']}")
    print(f"   任务统计: {board['tasks']}")
    
    # 完成第一个任务，触发依赖解除
    print("\n6. 完成 T1，自动解除 T2, T3")
    coordinator.update_task_status("demo", t1["task_id"], TaskStatus.COMPLETED, "API设计完成")
    
    print("\n7. 任务状态:")
    for task in coordinator.list_tasks("demo"):
        status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "blocked": "🚫"}
        print(f"   {status_icon.get(task['status'], '❓')} {task['id']} {task['title']}")
