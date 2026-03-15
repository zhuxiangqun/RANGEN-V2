"""
Agent Service - Business logic for Agent management
"""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.services.database import get_database
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class AgentService:
    """Agent业务逻辑服务"""
    
    def __init__(self):
        self.db = get_database()
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"agent_{uuid.uuid4().hex[:12]}"
    
    def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Agent"""
        agent_id = self._generate_id()
        
        # 构建Agent数据
        data = {
            'id': agent_id,
            'name': agent_data.get('name'),
            'type': agent_data.get('type', 'agent'),
            'description': agent_data.get('description'),
            'config_path': agent_data.get('config', {}).get('config_path'),
            'status': 'active'
        }
        
        # 创建Agent记录
        agent = self.db.create_agent(data)
        
        # 关联Skills
        skills = agent_data.get('skills', [])
        for skill_id in skills:
            self.db.add_skill_to_agent(agent_id, skill_id)
        
        # 关联Tools
        tools = agent_data.get('tools', [])
        for tool_id in tools:
            self.db.add_tool_to_agent(agent_id, tool_id)
        
        logger.info(f"Agent created: {agent_id} - {agent_data.get('name')}")
        
        # 返回完整信息
        return self.get_agent(agent_id)
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取Agent详情"""
        agent = self.db.get_agent(agent_id)
        if not agent:
            return None
        
        # 获取关联的Skills和Tools
        skills = self.db.get_agent_skills(agent_id)
        tools = self.db.get_agent_tools(agent_id)
        
        return {
            'id': agent['id'],
            'name': agent['name'],
            'type': agent['type'],
            'description': agent.get('description'),
            'skills': [s['id'] for s in skills],
            'tools': [t['id'] for t in tools],
            'status': agent['status'],
            'created_at': agent['created_at'],
            'updated_at': agent['updated_at'],
            'reference_count': agent.get('reference_count', 0)
        }
    
    def list_agents(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取Agent列表"""
        agents = self.db.get_all_agents(status)
        
        result = []
        for agent in agents:
            skills = self.db.get_agent_skills(agent['id'])
            tools = self.db.get_agent_tools(agent['id'])
            
            result.append({
                'id': agent['id'],
                'name': agent['name'],
                'type': agent['type'],
                'description': agent.get('description'),
                'skills': [s['id'] for s in skills],
                'tools': [t['id'] for t in tools],
                'status': agent['status'],
                'created_at': agent['created_at'],
                'updated_at': agent['updated_at'],
                'reference_count': agent.get('reference_count', 0)
            })
        
        return result
    
    def update_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新Agent"""
        existing = self.db.get_agent(agent_id)
        if not existing:
            return None
        
        update_data = {
            'name': agent_data.get('name', existing['name']),
            'type': agent_data.get('type', existing['type']),
            'description': agent_data.get('description', existing.get('description')),
            'config_path': agent_data.get('config', {}).get('config_path', existing.get('config_path')),
            'status': agent_data.get('status', existing['status'])
        }
        
        self.db.update_agent(agent_id, update_data)
        
        # 如果有更新skills/tools的请求，更新关联
        if 'skills' in agent_data:
            # 简单处理：直接重新关联
            skills = agent_data['skills']
            for skill_id in skills:
                self.db.add_skill_to_agent(agent_id, skill_id)
        
        if 'tools' in agent_data:
            tools = agent_data['tools']
            for tool_id in tools:
                self.db.add_tool_to_agent(agent_id, tool_id)
        
        logger.info(f"Agent updated: {agent_id}")
        
        return self.get_agent(agent_id)
    
    def delete_agent(self, agent_id: str) -> bool:
        """删除Agent"""
        existing = self.db.get_agent(agent_id)
        if not existing:
            return False
        
        result = self.db.delete_agent(agent_id)
        if result:
            logger.info(f"Agent deleted: {agent_id}")
        
        return result
    
    def check_agent_exists(self, agent_id: str) -> bool:
        """检查Agent是否存在"""
        return self.db.get_agent(agent_id) is not None


def get_agent_service() -> AgentService:
    """获取Agent服务实例"""
    return AgentService()
