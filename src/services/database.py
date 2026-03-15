"""
Database Service - SQLite connection and CRUD operations for AI中台管理平台
"""
import os
import sqlite3
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class DatabaseService:
    """数据库服务 - SQLite连接管理和CRUD操作"""
    
    _instance = None
    _connection: Optional[sqlite3.Connection] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance
    
    def _get_db_path(self) -> str:
        """获取数据库文件路径"""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, 'ai_platform.db')
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._connection is None:
            db_path = self._get_db_path()
            self._connection = sqlite3.connect(db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            logger.info(f"Database connected: {db_path}")
        return self._connection
    
    def initialize(self) -> None:
        """初始化数据库 - 创建表结构"""
        conn = self.get_connection()
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'migrations', 'v1.0_create_tables.sql'
        )
        
        if os.path.exists(migration_path):
            with open(migration_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            conn.executescript(sql_content)
            conn.commit()
            logger.info("Database initialized successfully")
            
            # 确保skills表有extension_reason列（向后兼容）
            try:
                cursor = conn.cursor()
                cursor.execute("ALTER TABLE skills ADD COLUMN extension_reason TEXT")
                conn.commit()
                logger.info("Added extension_reason column to skills table")
            except Exception as e:
                # 列可能已存在
                logger.debug(f"Extension reason column may already exist: {e}")
            
            # 确保skills表有source和priority列（新功能）
            for column_def in [
                ("ALTER TABLE skills ADD COLUMN source TEXT", "source"),
                ("ALTER TABLE skills ADD COLUMN priority INTEGER DEFAULT 100", "priority")
            ]:
                try:
                    cursor = conn.cursor()
                    cursor.execute(column_def[0])
                    conn.commit()
                    logger.info(f"Added {column_def[1]} column to skills table")
                except Exception as e:
                    logger.debug(f"{column_def[1]} column may already exist: {e}")
            
            # 确保tools表有source和priority列（新功能）
            for column_def in [
                ("ALTER TABLE tools ADD COLUMN source TEXT", "source"),
                ("ALTER TABLE tools ADD COLUMN priority INTEGER DEFAULT 100", "priority")
            ]:
                try:
                    cursor = conn.cursor()
                    cursor.execute(column_def[0])
                    conn.commit()
                    logger.info(f"Added {column_def[1]} column to tools table")
                except Exception as e:
                    logger.debug(f"{column_def[1]} column may already exist: {e}")
        else:
            logger.warning(f"Migration file not found: {migration_path}")
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")
    
    # ========== Agent CRUD ==========
    
    def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Agent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO agents (id, name, type, description, config_path, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            agent_data.get('id'),
            agent_data.get('name'),
            agent_data.get('type', 'agent'),
            agent_data.get('description'),
            agent_data.get('config_path'),
            agent_data.get('status', 'active')
        ))
        conn.commit()
        
        return self.get_agent(agent_data['id'])
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取单个Agent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_all_agents(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有Agent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM agents WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM agents ORDER BY created_at DESC")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def update_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新Agent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE agents 
            SET name = ?, type = ?, description = ?, config_path = ?, status = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            agent_data.get('name'),
            agent_data.get('type'),
            agent_data.get('description'),
            agent_data.get('config_path'),
            agent_data.get('status'),
            agent_id
        ))
        conn.commit()
        
        return self.get_agent(agent_id)
    
    def delete_agent(self, agent_id: str) -> bool:
        """删除Agent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    # ========== Skill CRUD ==========
    
    def create_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Skill"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        tools_json = json.dumps(skill_data.get('tools', [])) if skill_data.get('tools') else None
        
        cursor.execute("""
            INSERT INTO skills (id, name, description, tools, source, priority, config_path, status, extension_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            skill_data.get('id'),
            skill_data.get('name'),
            skill_data.get('description'),
            tools_json,
            skill_data.get('source'),
            skill_data.get('priority', 100),
            skill_data.get('config_path'),
            skill_data.get('status', 'active'),
            skill_data.get('extension_reason')
        ))
        conn.commit()
        
        return self.get_skill(skill_data['id'])
    
    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取单个Skill"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM skills WHERE id = ?", (skill_id,))
        row = cursor.fetchone()
        
        if row:
            result = dict(row)
            if result.get('tools'):
                result['tools'] = json.loads(result['tools'])
            return result
        return None
    
    def get_all_skills(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有Skill"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM skills WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM skills ORDER BY created_at DESC")
        
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result.get('tools'):
                result['tools'] = json.loads(result['tools'])
            results.append(result)
        
        return results
    
    def delete_skill(self, skill_id: str) -> bool:
        """删除Skill"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    # ========== Tool CRUD ==========
    
    def create_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Tool"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tools (id, name, description, type, source, priority, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            tool_data.get('id'),
            tool_data.get('name'),
            tool_data.get('description'),
            tool_data.get('type'),
            tool_data.get('source'),
            tool_data.get('priority', 100),
            tool_data.get('status', 'active')
        ))
        conn.commit()
        
        return self.get_tool(tool_data['id'])
    
    def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """获取单个Tool"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tools WHERE id = ?", (tool_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_all_tools(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有Tool"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM tools WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM tools ORDER BY created_at DESC")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_tool(self, tool_id: str) -> bool:
        """删除Tool"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    # ========== 关联表操作 ==========
    
    def add_skill_to_agent(self, agent_id: str, skill_id: str) -> bool:
        """为Agent添加Skill"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO agent_skills (agent_id, skill_id)
                VALUES (?, ?)
            """, (agent_id, skill_id))
            conn.commit()
            
            # 更新引用计数
            cursor.execute("UPDATE skills SET reference_count = reference_count + 1 WHERE id = ?", (skill_id,))
            cursor.execute("UPDATE agents SET reference_count = reference_count + 1 WHERE id = ?", (agent_id,))
            conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error adding skill to agent: {e}")
            return False
    
    def add_tool_to_agent(self, agent_id: str, tool_id: str) -> bool:
        """为Agent添加Tool"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO agent_tools (agent_id, tool_id)
                VALUES (?, ?)
            """, (agent_id, tool_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding tool to agent: {e}")
            return False
    
    def get_agent_skills(self, agent_id: str) -> List[Dict[str, Any]]:
        """获取Agent的所有Skill"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.* FROM skills s
            JOIN agent_skills a ON s.id = a.skill_id
            WHERE a.agent_id = ?
        """, (agent_id,))
        
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result.get('tools'):
                result['tools'] = json.loads(result['tools'])
            results.append(result)
        
        return results
    
    def get_agent_tools(self, agent_id: str) -> List[Dict[str, Any]]:
        """获取Agent的所有Tool"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.* FROM tools t
            JOIN agent_tools a ON t.id = a.tool_id
            WHERE a.agent_id = ?
        """, (agent_id,))
        
        return [dict(row) for row in cursor.fetchall()]


def get_database() -> DatabaseService:
    """获取数据库服务单例"""
    return DatabaseService()


def init_database() -> None:
    """初始化数据库 - 便捷函数"""
    db = DatabaseService()
    db.initialize()
