"""
Swarm 团队管理器

管理团队生命周期:
- 创建/删除团队
- 管理团队成员
- 协调 Agent 协作
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict, field


@dataclass
class TeamConfig:
    """团队配置"""
    name: str
    description: str = ""
    created_at: str = ""
    leader: str = "leader"
    members: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if self.leader not in self.members:
            self.members.insert(0, self.leader)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "TeamConfig":
        return cls(**data)


@dataclass
class AgentInfo:
    """Agent 信息"""
    name: str
    team: str
    status: str = "idle"  # idle, working, completed, failed
    task: str = ""
    worktree_path: str = ""
    pid: int = 0
    started_at: str = ""
    last_active: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
        if not self.last_active:
            self.last_active = self.started_at
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "AgentInfo":
        return cls(**data)


class TeamStore:
    """
    团队存储
    
    存储结构:
    .swarm/
    └── {team}/
        ├── team.json        # 团队配置
        └── agents/
            └── {name}.json  # Agent 信息
    
    使用方式:
        store = TeamStore(".swarm")
        store.create_team("my-team", "开发团队")
        store.add_agent("my-team", "worker1")
    """
    
    def __init__(self, base_dir: str = ".swarm"):
        self.base_dir = Path(base_dir)
    
    def _get_team_path(self, team: str) -> Path:
        """获取团队目录"""
        return self.base_dir / team
    
    def _get_team_config_file(self, team: str) -> Path:
        """获取团队配置文件"""
        return self._get_team_path(team) / "team.json"
    
    def _get_agents_dir(self, team: str) -> Path:
        """获取 Agent 目录"""
        return self._get_team_path(team) / "agents"
    
    def _ensure_team(self, team: str) -> Path:
        """确保团队目录存在"""
        path = self._get_team_path(team)
        path.mkdir(parents=True, exist_ok=True)
        self._get_agents_dir(team).mkdir(parents=True, exist_ok=True)
        return path
    
    # =========================================================================
    # 团队管理
    # =========================================================================
    
    def create_team(self, name: str, description: str = "", leader: str = "leader", metadata: Optional[Dict] = None) -> TeamConfig:
        """
        创建团队
        
        Args:
            name: 团队名
            description: 团队描述
            leader: 领导者名称
            metadata: 额外元数据
            
        Returns:
            团队配置
        """
        self._ensure_team(name)
        
        config = TeamConfig(
            name=name,
            description=description,
            leader=leader,
            members=[leader],
            metadata=metadata or {}
        )
        
        with open(self._get_team_config_file(name), "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
        
        return config
    
    def get_team(self, name: str) -> Optional[TeamConfig]:
        """获取团队配置"""
        config_file = self._get_team_config_file(name)
        
        if not config_file.exists():
            return None
        
        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)
            return TeamConfig.from_dict(data)
    
    def update_team(self, name: str, **kwargs) -> Optional[TeamConfig]:
        """更新团队配置"""
        config = self.get_team(name)
        if not config:
            return None
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        with open(self._get_team_config_file(name), "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
        
        return config
    
    def list_teams(self) -> List[str]:
        """列出所有团队"""
        if not self.base_dir.exists():
            return []
        
        return [p.name for p in self.base_dir.iterdir() if p.is_dir() and (p / "team.json").exists()]
    
    def delete_team(self, name: str) -> bool:
        """删除团队"""
        import shutil
        team_path = self._get_team_path(name)
        
        if not team_path.exists():
            return False
        
        shutil.rmtree(team_path)
        return True
    
    # =========================================================================
    # Agent 管理
    # =========================================================================
    
    def add_agent(
        self,
        team: str,
        name: str,
        status: str = "idle",
        task: str = "",
        worktree_path: str = "",
        pid: int = 0,
        metadata: Optional[Dict] = None
    ) -> AgentInfo:
        """
        添加 Agent 到团队
        
        Args:
            team: 团队名
            name: Agent 名
            status: 状态
            task: 当前任务
            worktree_path: Worktree 路径
            pid: 进程ID
            metadata: 额外元数据
            
        Returns:
            Agent 信息
        """
        self._ensure_team(team)
        
        # 更新团队成员
        config = self.get_team(team)
        if config and name not in config.members:
            config.members.append(name)
            with open(self._get_team_config_file(team), "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
        
        agent_info = AgentInfo(
            name=name,
            team=team,
            status=status,
            task=task,
            worktree_path=worktree_path,
            pid=pid,
            metadata=metadata or {}
        )
        
        agent_file = self._get_agents_dir(team) / f"{name}.json"
        with open(agent_file, "w", encoding="utf-8") as f:
            json.dump(agent_info.to_dict(), f, ensure_ascii=False, indent=2)
        
        return agent_info
    
    def get_agent(self, team: str, name: str) -> Optional[AgentInfo]:
        """获取 Agent 信息"""
        agent_file = self._get_agents_dir(team) / f"{name}.json"
        
        if not agent_file.exists():
            return None
        
        with open(agent_file, encoding="utf-8") as f:
            data = json.load(f)
            return AgentInfo.from_dict(data)
    
    def update_agent(self, team: str, name: str, **kwargs) -> Optional[AgentInfo]:
        """更新 Agent 信息"""
        agent_info = self.get_agent(team, name)
        if not agent_info:
            return None
        
        for key, value in kwargs.items():
            if hasattr(agent_info, key):
                setattr(agent_info, key, value)
        
        agent_info.last_active = datetime.now().isoformat()
        
        agent_file = self._get_agents_dir(team) / f"{name}.json"
        with open(agent_file, "w", encoding="utf-8") as f:
            json.dump(agent_info.to_dict(), f, ensure_ascii=False, indent=2)
        
        return agent_info
    
    def remove_agent(self, team: str, name: str) -> bool:
        """移除 Agent"""
        agent_file = self._get_agents_dir(team) / f"{name}.json"
        
        if not agent_file.exists():
            return False
        
        agent_file.unlink()
        
        # 从团队成员中移除
        config = self.get_team(team)
        if config and name in config.members:
            config.members.remove(name)
            with open(self._get_team_config_file(team), "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
        
        return True
    
    def list_agents(self, team: str) -> List[AgentInfo]:
        """列出团队所有 Agent"""
        agents_dir = self._get_agents_dir(team)
        
        if not agents_dir.exists():
            return []
        
        agents = []
        for agent_file in agents_dir.glob("*.json"):
            try:
                with open(agent_file, encoding="utf-8") as f:
                    data = json.load(f)
                    agents.append(AgentInfo.from_dict(data))
            except Exception:
                continue
        
        return agents
    
    def get_team_status(self, team: str) -> Dict[str, Any]:
        """获取团队状态"""
        config = self.get_team(team)
        if not config:
            return {"exists": False}
        
        agents = self.list_agents(team)
        
        status_counts = {
            "idle": 0,
            "working": 0,
            "completed": 0,
            "failed": 0,
        }
        
        for agent in agents:
            if agent.status in status_counts:
                status_counts[agent.status] += 1
        
        return {
            "exists": True,
            "name": config.name,
            "description": config.description,
            "leader": config.leader,
            "member_count": len(agents),
            "agent_status": status_counts,
            "created_at": config.created_at,
        }


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    store = TeamStore("/tmp/.swarm-test")
    
    # 清理
    if "demo-team" in store.list_teams():
        store.delete_team("demo-team")
    
    # 创建团队
    team = store.create_team("demo-team", "演示团队")
    print(f"创建团队: {team.name} (Leader: {team.leader})")
    
    # 添加 Agent
    leader = store.add_agent("demo-team", "leader", status="working", task="协调工作")
    print(f"添加 Agent: {leader.name} ({leader.status})")
    
    worker1 = store.add_agent("demo-team", "researcher1", status="idle", task="实验调参")
    print(f"添加 Agent: {worker1.name} ({worker1.status})")
    
    worker2 = store.add_agent("demo-team", "coder", status="idle", task="编写代码")
    print(f"添加 Agent: {worker2.name} ({worker2.status})")
    
    # 更新状态
    store.update_agent("demo-team", "researcher1", status="working", task="正在训练模型")
    
    # 查看团队状态
    status = store.get_team_status("demo-team")
    print(f"\n团队状态: {status}")
    
    # 列出所有团队
    print(f"\n所有团队: {store.list_teams()}")
