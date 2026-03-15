"""
Team Service - Multi-Agent collaboration management
"""
import uuid
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.services.database import get_database
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class CollaborationMode(str, Enum):
    """协作模式"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"      # 并行执行
    HIERARCHICAL = "hierarchical"  # 层级协作


class RoleType(str, Enum):
    """角色类型"""
    COORDINATOR = "coordinator"  # 协调者
    EXECUTOR = "executor"      # 执行者
    VALIDATOR = "validator"    # 验证者
    ANALYZER = "analyzer"     # 分析者


@dataclass
class TeamMember:
    """团队成员"""
    agent_id: str
    role: str
    description: str
    input_from: List[str] = field(default_factory=list)  # 从哪些成员获取输入


@dataclass
class TeamConfig:
    """团队配置"""
    id: str
    name: str
    description: str
    members: List[TeamMember]
    mode: CollaborationMode
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "active"


class TeamService:
    """团队服务 - 管理多Agent协作"""
    
    def __init__(self):
        self.db = get_database()
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"team_{uuid.uuid4().hex[:12]}"
    
    def create_team(
        self,
        name: str,
        description: str,
        agent_ids: List[str],
        mode: str = "sequential",
        role_assignments: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """创建团队"""
        team_id = self._generate_id()
        
        # 验证所有Agent存在
        for agent_id in agent_ids:
            agent = self.db.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent不存在: {agent_id}")
        
        # 构建团队成员
        members = []
        role_assignments = role_assignments or {}
        
        for i, agent_id in enumerate(agent_ids):
            agent = self.db.get_agent(agent_id)
            
            # 自动分配角色
            if agent_id in role_assignments:
                role = role_assignments[agent_id]
            elif i == 0:
                role = RoleType.COORDINATOR.value
            elif i == len(agent_ids) - 1:
                role = RoleType.VALIDATOR.value
            else:
                role = RoleType.EXECUTOR.value
            
            # 确定输入来源
            input_from = []
            if i > 0:
                input_from = [agent_ids[i - 1]]
            
            member = TeamMember(
                agent_id=agent_id,
                role=role,
                description=agent.get('description', ''),
                input_from=input_from
            )
            members.append(member)
        
        # 保存到数据库
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                mode TEXT DEFAULT 'sequential',
                members_json TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        members_json = json.dumps([
            {
                'agent_id': m.agent_id,
                'role': m.role,
                'description': m.description,
                'input_from': m.input_from
            }
            for m in members
        ])
        
        cursor.execute("""
            INSERT INTO teams (id, name, description, mode, members_json)
            VALUES (?, ?, ?, ?, ?)
        """, (team_id, name, description, mode, members_json))
        
        conn.commit()
        
        logger.info(f"Team created: {team_id} - {name}")
        
        return self.get_team(team_id)
    
    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """获取团队详情"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        team = dict(row)
        members_json = team.get('members_json', '[]')
        team['members'] = json.loads(members_json)
        del team['members_json']
        
        return team
    
    def list_teams(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取团队列表"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM teams WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM teams ORDER BY created_at DESC")
        
        teams = []
        for row in cursor.fetchall():
            team = dict(row)
            members_json = team.get('members_json', '[]')
            team['members'] = json.loads(members_json)
            del team['members_json']
            teams.append(team)
        
        return teams
    
    def delete_team(self, team_id: str) -> bool:
        """删除团队"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    def suggest_team_from_requirement(self, requirement: str) -> Dict[str, Any]:
        """根据需求建议团队配置"""
        # 简单的关键词匹配逻辑
        agents = self.db.get_all_agents(status='active')
        
        suggested_members = []
        
        # 分析需求关键词
        requirement_lower = requirement.lower()
        
        # 查找相关Agent
        for agent in agents:
            name_lower = agent.get('name', '').lower()
            desc_lower = agent.get('description', '').lower()
            
            if any(kw in name_lower or kw in desc_lower for kw in ['analysis', 'analyze', '分析']):
                suggested_members.append({
                    'agent_id': agent['id'],
                    'role': RoleType.ANALYZER.value,
                    'reason': '需求包含分析相关关键词'
                })
            
            if any(kw in name_lower or kw in desc_lower for kw in ['execute', 'run', '执行']):
                suggested_members.append({
                    'agent_id': agent['id'],
                    'role': RoleType.EXECUTOR.value,
                    'reason': '需求包含执行相关关键词'
                })
            
            if any(kw in name_lower or kw in desc_lower for kw in ['verify', 'check', '验证']):
                suggested_members.append({
                    'agent_id': agent['id'],
                    'role': RoleType.VALIDATOR.value,
                    'reason': '需求包含验证相关关键词'
                })
        
        # 如果没有匹配，添加所有可用Agent
        if not suggested_members:
            for agent in agents[:3]:  # 最多3个
                suggested_members.append({
                    'agent_id': agent['id'],
                    'role': RoleType.EXECUTOR.value,
                    'reason': '默认选择'
                })
        
        return {
            'suggested_members': suggested_members,
            'mode': CollaborationMode.SEQUENTIAL.value,
            'message': f"根据需求 '{requirement}' 建议 {len(suggested_members)} 个团队成员"
        }


def get_team_service() -> TeamService:
    """获取团队服务实例"""
    return TeamService()
