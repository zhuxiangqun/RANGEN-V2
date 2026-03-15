"""
Skill Service - Business logic for Skill management
"""
import uuid
from typing import List, Dict, Any, Optional
from src.services.database import get_database
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class SkillService:
    """Skill业务逻辑服务"""
    
    def __init__(self):
        self.db = get_database()
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"skill_{uuid.uuid4().hex[:12]}"
    
    def create_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Skill"""
        skill_id = self._generate_id()
        
        # 构建Skill数据
        data = {
            'id': skill_id,
            'name': skill_data.get('name'),
            'description': skill_data.get('description'),
            'tools': skill_data.get('tools', []),
            'config_path': skill_data.get('config_path'),
            'status': 'active',
            'extension_reason': skill_data.get('extension_reason')
        }
        
        # 创建Skill记录
        skill = self.db.create_skill(data)
        
        # 关联Tools
        tools = skill_data.get('tools', [])
        for tool_id in tools:
            self._add_tool_to_skill(skill_id, tool_id)
        
        logger.info(f"Skill created: {skill_id} - {skill_data.get('name')}")
        
        return self.get_skill(skill_id)
    
    def _add_tool_to_skill(self, skill_id: str, tool_id: str) -> bool:
        """为Skill添加Tool关联"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO skill_tools (skill_id, tool_id)
                VALUES (?, ?)
            """, (skill_id, tool_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding tool to skill: {e}")
            return False
    
    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取Skill详情"""
        skill = self.db.get_skill(skill_id)
        if not skill:
            return None
        
        # 获取关联的Tools
        tools = self._get_skill_tools(skill_id)
        
        return {
            'id': skill['id'],
            'name': skill['name'],
            'description': skill.get('description'),
            'tools': [t['id'] for t in tools],
            'status': skill['status'],
            'created_at': skill['created_at'],
            'reference_count': skill.get('reference_count', 0),
            'extension_reason': skill.get('extension_reason')
        }
    
    def _get_skill_tools(self, skill_id: str) -> List[Dict[str, Any]]:
        """获取Skill的所有Tool"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.* FROM tools t
            JOIN skill_tools s ON t.id = s.tool_id
            WHERE s.skill_id = ?
        """, (skill_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def list_skills(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取Skill列表"""
        skills = self.db.get_all_skills(status)
        
        result = []
        for skill in skills:
            tools = self._get_skill_tools(skill['id'])
            
            result.append({
                'id': skill['id'],
                'name': skill['name'],
                'description': skill.get('description'),
                'tools': [t['id'] for t in tools],
                'status': skill['status'],
                'created_at': skill['created_at'],
                'reference_count': skill.get('reference_count', 0),
                'extension_reason': skill.get('extension_reason')
            })
        
        return result
    
    def delete_skill(self, skill_id: str) -> bool:
        """删除Skill"""
        existing = self.db.get_skill(skill_id)
        if not existing:
            return False
        
        result = self.db.delete_skill(skill_id)
        if result:
            logger.info(f"Skill deleted: {skill_id}")
        
        return result
    
    def check_skill_exists(self, skill_id: str) -> bool:
        """检查Skill是否存在"""
        return self.db.get_skill(skill_id) is not None
    
    def combine_tools_to_skill(self, name: str, description: str, tool_ids: List[str]) -> Dict[str, Any]:
        """从现有Tools组合新Skill"""
        # 验证所有tool_ids存在
        all_tools = self.db.get_all_tools()
        existing_tool_ids = {t['id'] for t in all_tools}
        
        valid_tools = [tid for tid in tool_ids if tid in existing_tool_ids]
        
        if not valid_tools:
            raise ValueError("No valid tools provided")
        
        return self.create_skill({
            'name': name,
            'description': description,
            'tools': valid_tools
        })


def get_skill_service() -> SkillService:
    """获取Skill服务实例"""
    return SkillService()
