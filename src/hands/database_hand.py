#!/usr/bin/env python3
"""
数据库Hand
提供数据库操作能力：连接、查询、插入、更新、删除
支持SQLite、MySQL、PostgreSQL（需要相应驱动）
"""

import sqlite3
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import json

from .base import BaseHand, HandCategory, HandSafetyLevel, HandCapability


class DatabaseHand(BaseHand):
    """数据库操作Hand"""
    
    def __init__(self):
        super().__init__(
            name="database",
            description="数据库操作能力：连接、查询、插入、更新、删除",
            category=HandCategory.DATA_MANAGEMENT,
            safety_level=HandSafetyLevel.MODERATE,
            version="1.0.0"
        )
        self.logger = logging.getLogger(__name__)
        self.connections: Dict[str, Any] = {}  # 连接池
        self.default_db_path = "rangen_system.db"
    
    def get_capability(self) -> HandCapability:
        """获取能力定义"""
        return HandCapability(
            name=self.name,
            description=self.description,
            category=self.category,
            safety_level=self.safety_level,
            version=self.version,
            parameters=[
                {
                    "name": "operation",
                    "type": "string",
                    "required": True,
                    "description": "操作类型：connect, query, execute, insert, update, delete, create_table",
                    "allowed_values": ["connect", "query", "execute", "insert", "update", "delete", "create_table"]
                },
                {
                    "name": "db_type",
                    "type": "string",
                    "required": False,
                    "default": "sqlite",
                    "description": "数据库类型：sqlite, mysql, postgresql",
                    "allowed_values": ["sqlite", "mysql", "postgresql"]
                },
                {
                    "name": "connection_string",
                    "type": "string",
                    "required": False,
                    "description": "数据库连接字符串"
                },
                {
                    "name": "db_path",
                    "type": "string",
                    "required": False,
                    "description": "SQLite数据库文件路径（仅SQLite）"
                },
                {
                    "name": "query",
                    "type": "string",
                    "required": False,
                    "description": "SQL查询语句"
                },
                {
                    "name": "params",
                    "type": "array",
                    "required": False,
                    "description": "查询参数"
                },
                {
                    "name": "table_name",
                    "type": "string",
                    "required": False,
                    "description": "表名"
                },
                {
                    "name": "data",
                    "type": "object",
                    "required": False,
                    "description": "插入或更新的数据"
                },
                {
                    "name": "where",
                    "type": "object",
                    "required": False,
                    "description": "WHERE条件"
                },
                {
                    "name": "schema",
                    "type": "object",
                    "required": False,
                    "description": "表结构定义"
                }
            ],
            examples=[
                {
                    "description": "连接到SQLite数据库",
                    "parameters": {
                        "operation": "connect",
                        "db_type": "sqlite",
                        "db_path": "data.db"
                    }
                },
                {
                    "description": "执行查询",
                    "parameters": {
                        "operation": "query",
                        "query": "SELECT * FROM users WHERE age > ?",
                        "params": [18]
                    }
                },
                {
                    "description": "插入数据",
                    "parameters": {
                        "operation": "insert",
                        "table_name": "users",
                        "data": {
                            "name": "张三",
                            "age": 25,
                            "email": "zhangsan@example.com"
                        }
                    }
                }
            ]
        )
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """执行数据库操作"""
        start_time = datetime.now()
        
        try:
            if operation == "connect":
                result = await self._connect(**kwargs)
            elif operation == "query":
                result = await self._query(**kwargs)
            elif operation == "execute":
                result = await self._execute_sql(**kwargs)
            elif operation == "insert":
                result = await self._insert(**kwargs)
            elif operation == "update":
                result = await self._update(**kwargs)
            elif operation == "delete":
                result = await self._delete(**kwargs)
            elif operation == "create_table":
                result = await self._create_table(**kwargs)
            else:
                raise ValueError(f"不支持的操作: {operation}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 记录Hook事件
            await self._record_hook_event(
                operation=operation,
                success=True,
                execution_time=execution_time,
                result_summary=f"数据库操作成功: {operation}"
            )
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            self.logger.error(f"数据库操作失败: {error_msg}")
            
            # 记录错误事件
            await self._record_hook_event(
                operation=operation,
                success=False,
                execution_time=execution_time,
                error=error_msg
            )
            
            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time
            }
    
    async def _connect(self, db_type: str = "sqlite", **kwargs) -> Dict[str, Any]:
        """连接到数据库"""
        connection_id = kwargs.get("connection_id", "default")
        
        if db_type == "sqlite":
            db_path = kwargs.get("db_path", self.default_db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # 返回字典格式
            self.connections[connection_id] = conn
            
            # 创建系统表（如果不存在）
            self._ensure_system_tables(conn)
            
            return {
                "connection_id": connection_id,
                "db_type": db_type,
                "db_path": db_path,
                "message": "SQLite连接成功"
            }
        
        elif db_type in ["mysql", "postgresql"]:
            # 需要相应驱动，这里仅返回占位符
            connection_string = kwargs.get("connection_string", "")
            
            if not connection_string:
                raise ValueError(f"{db_type} 需要 connection_string 参数")
            
            # 实际应用中这里会使用相应驱动创建连接
            # 例如：mysql.connector.connect() 或 psycopg2.connect()
            
            self.connections[connection_id] = {
                "db_type": db_type,
                "connection_string": connection_string,
                "connected": True
            }
            
            return {
                "connection_id": connection_id,
                "db_type": db_type,
                "message": f"{db_type} 连接配置已保存（需要相应驱动）"
            }
        
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    def _ensure_system_tables(self, conn: sqlite3.Connection):
        """确保系统表存在"""
        cursor = conn.cursor()
        
        # 创建系统日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                source TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # 创建Hand执行记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hand_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hand_name TEXT NOT NULL,
                operation TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                execution_time REAL NOT NULL,
                result_summary TEXT,
                error_message TEXT
            )
        """)
        
        conn.commit()
    
    async def _query(self, query: str, params: Optional[List] = None, **kwargs) -> List[Dict[str, Any]]:
        """执行查询"""
        connection_id = kwargs.get("connection_id", "default")
        
        if connection_id not in self.connections:
            await self._connect(**kwargs)
        
        conn = self.connections[connection_id]
        
        if isinstance(conn, dict):
            raise ValueError(f"数据库类型 {conn.get('db_type')} 需要相应驱动支持")
        
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 获取列名
            column_names = [description[0] for description in cursor.description] if cursor.description else []
            
            # 转换为字典列表
            results = []
            for row in cursor.fetchall():
                if column_names:
                    results.append(dict(zip(column_names, row)))
                else:
                    results.append(row)
            
            return results
            
        except Exception as e:
            self.logger.error(f"查询执行失败: {e}")
            raise
    
    async def _execute_sql(self, query: str, params: Optional[List] = None, **kwargs) -> Dict[str, Any]:
        """执行SQL语句（非查询）"""
        connection_id = kwargs.get("connection_id", "default")
        
        if connection_id not in self.connections:
            await self._connect(**kwargs)
        
        conn = self.connections[connection_id]
        
        if isinstance(conn, dict):
            raise ValueError(f"数据库类型 {conn.get('db_type')} 需要相应驱动支持")
        
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            conn.commit()
            
            return {
                "rowcount": cursor.rowcount,
                "lastrowid": cursor.lastrowid,
                "message": "SQL执行成功"
            }
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"SQL执行失败: {e}")
            raise
    
    async def _insert(self, table_name: str, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """插入数据"""
        if not data:
            raise ValueError("插入数据不能为空")
        
        columns = list(data.keys())
        placeholders = ["?"] * len(columns)
        values = list(data.values())
        
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        result = await self._execute_sql(query, values, **kwargs)
        result["table_name"] = table_name
        result["inserted_data"] = data
        
        return result
    
    async def _update(self, table_name: str, data: Dict[str, Any], where: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """更新数据"""
        if not data:
            raise ValueError("更新数据不能为空")
        
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = list(data.values())
        
        where_clause = ""
        where_values = []
        
        if where:
            where_conditions = []
            for key, value in where.items():
                where_conditions.append(f"{key} = ?")
                where_values.append(value)
            
            where_clause = f" WHERE {' AND '.join(where_conditions)}"
        
        query = f"UPDATE {table_name} SET {set_clause}{where_clause}"
        
        result = await self._execute_sql(query, values + where_values, **kwargs)
        result["table_name"] = table_name
        result["updated_rows"] = result["rowcount"]
        
        return result
    
    async def _delete(self, table_name: str, where: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """删除数据"""
        where_clause = ""
        where_values = []
        
        if where:
            where_conditions = []
            for key, value in where.items():
                where_conditions.append(f"{key} = ?")
                where_values.append(value)
            
            where_clause = f" WHERE {' AND '.join(where_conditions)}"
        else:
            # 安全保护：如果没有WHERE条件，需要明确确认
            confirm = kwargs.get("confirm_all", False)
            if not confirm:
                raise ValueError("删除操作必须指定WHERE条件或明确确认删除所有数据")
        
        query = f"DELETE FROM {table_name}{where_clause}"
        
        result = await self._execute_sql(query, where_values, **kwargs)
        result["table_name"] = table_name
        result["deleted_rows"] = result["rowcount"]
        
        return result
    
    async def _create_table(self, table_name: str, schema: Dict[str, str], **kwargs) -> Dict[str, Any]:
        """创建表"""
        if not schema:
            raise ValueError("表结构定义不能为空")
        
        # 简单的schema处理：列名 -> 类型
        columns = []
        for column_name, column_type in schema.items():
            columns.append(f"{column_name} {column_type}")
        
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        
        result = await self._execute_sql(query, **kwargs)
        result["table_name"] = table_name
        result["schema"] = schema
        
        return result
    
    async def close_all_connections(self):
        """关闭所有数据库连接"""
        for connection_id, conn in self.connections.items():
            try:
                if not isinstance(conn, dict):
                    conn.close()
                self.logger.info(f"关闭数据库连接: {connection_id}")
            except Exception as e:
                self.logger.error(f"关闭连接失败 {connection_id}: {e}")
        
        self.connections.clear()
    
    async def _record_hook_event(self, **kwargs):
        """记录Hook事件（简化实现）"""
        # 实际应用中应该调用Hook系统
        operation = kwargs.get("operation", "unknown")
        success = kwargs.get("success", False)
        
        if not success:
            self.logger.warning(f"数据库操作失败: {operation}")


# 创建默认实例
database_hand = DatabaseHand()