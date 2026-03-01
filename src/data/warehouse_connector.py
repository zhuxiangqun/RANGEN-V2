#!/usr/bin/env python3
"""
数据仓库连接器 - 实现数据仓库对接导出
"""

import logging
import time
import json
import csv
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import pandas as pd
import os


class DataFormat(Enum):
    """数据格式"""
    JSON = "json"
    CSV = "csv"
    SQLITE = "sqlite"
    PARQUET = "parquet"
    EXCEL = "excel"


class ExportType(Enum):
    """导出类型"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DELTA = "delta"
    SNAPSHOT = "snapshot"


@dataclass
class DataSchema:
    """数据模式"""
    schema_id: str
    name: str
    version: str
    fields: List[Dict[str, Any]]
    primary_key: List[str]
    indexes: List[str]
    constraints: List[Dict[str, Any]]
    created_at: float


@dataclass
class ExportJob:
    """导出任务"""
    job_id: str
    schema_id: str
    export_type: ExportType
    data_format: DataFormat
    destination: str
    filters: Dict[str, Any]
    status: str
    created_at: float
    started_at: Optional[float]
    completed_at: Optional[float]
    progress: float
    error_message: Optional[str]
    metadata: Dict[str, Any]


class WarehouseConnector:
    """数据仓库连接器"""
    
    def __init__(self, warehouse_path: str = "warehouse"):
        self.warehouse_path = warehouse_path
        self.logger = logging.getLogger(__name__)
        self.schemas: Dict[str, DataSchema] = {}
        self.export_jobs: Dict[str, ExportJob] = {}
        self.connections: Dict[str, Any] = {}
        
        # 创建仓库目录
        os.makedirs(warehouse_path, exist_ok=True)
        
        # 初始化默认模式
        self._initialize_default_schemas()
    
    def _initialize_default_schemas(self):
        """初始化默认模式"""
        try:
            # 用户行为数据模式
            user_behavior_schema = DataSchema(
                schema_id="user_behavior",
                name="用户行为数据",
                version="1.0",
                fields=[
                    {"name": "user_id", "type": "string", "required": True},
                    {"name": "session_id", "type": "string", "required": True},
                    {"name": "action_type", "type": "string", "required": True},
                    {"name": "timestamp", "type": "datetime", "required": True},
                    {"name": "duration", "type": "float", "required": False},
                    {"name": "success", "type": "boolean", "required": False},
                    {"name": "data", "type": "json", "required": False},
                    {"name": "context", "type": "json", "required": False}
                ],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={"description": "用户行为跟踪数据"}
            )
            self.schemas["user_behavior"] = user_behavior_schema
            
            # 系统性能数据模式
            performance_schema = DataSchema(
                schema_id="system_performance",
                name="系统性能数据",
                version="1.0",
                fields=[
                    {"name": "metric_name", "type": "string", "required": True},
                    {"name": "value", "type": "float", "required": True},
                    {"name": "timestamp", "type": "datetime", "required": True},
                    {"name": "component", "type": "string", "required": False},
                    {"name": "metadata", "type": "json", "required": False}
                ],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={"description": "系统性能监控数据"}
            )
            self.schemas["system_performance"] = performance_schema
            
            # 业务数据模式
            business_schema = DataSchema(
                schema_id="business_data",
                name="业务数据",
                version="1.0",
                fields=[
                    {"name": "entity_id", "type": "string", "required": True},
                    {"name": "entity_type", "type": "string", "required": True},
                    {"name": "status", "type": "string", "required": True},
                    {"name": "created_at", "type": "datetime", "required": True},
                    {"name": "updated_at", "type": "datetime", "required": True},
                    {"name": "attributes", "type": "json", "required": False}
                ],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={"description": "业务实体数据"}
            )
            self.schemas["business_data"] = business_schema
            
            self.logger.info(f"初始化了 {len(self.schemas)} 个默认数据模式")
            
        except Exception as e:
            self.logger.error(f"初始化默认模式失败: {e}")
    
    def create_schema(self, schema: DataSchema) -> bool:
        """创建数据模式"""
        try:
            # 验证模式
            if not self._validate_schema(schema):
                return False
            
            # 检查模式ID是否已存在
            if schema.schema_id in self.schemas:
                self.logger.warning(f"模式 {schema.schema_id} 已存在")
                return False
            
            # 添加模式
            self.schemas[schema.schema_id] = schema
            
            # 保存到文件
            self._save_schema_to_file(schema)
            
            self.logger.info(f"创建数据模式成功: {schema.schema_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建数据模式失败: {e}")
            return False
    
    def _validate_schema(self, schema: DataSchema) -> bool:
        """验证数据模式"""
        if not schema.schema_id or not schema.schema_id.strip():
            return False
        
        if not schema.name or not schema.name.strip():
            return False
        
        if not schema.fields or len(schema.fields) == 0:
            return False
        
        # 验证字段定义
        for field in schema.fields:
            if not field.get("name") or not field.get("type"):
                return False
        
        return True
    
    def _save_schema_to_file(self, schema: DataSchema):
        """保存模式到文件"""
        try:
            schema_dir = os.path.join(self.warehouse_path, "schemas")
            os.makedirs(schema_dir, exist_ok=True)
            
            schema_file = os.path.join(schema_dir, f"{schema.schema_id}.json")
            schema_data = {
                "schema_id": schema.schema_id,
                "name": schema.name,
                "version": schema.version,
                "fields": schema.fields,
                "created_at": schema.created_at.isoformat(),
                "updated_at": schema.updated_at.isoformat(),
                "metadata": schema.metadata
            }
            
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"保存模式文件失败: {e}")
    
    def create_component(self, schema_id: str, name: str, fields: List[Dict[str, Any]],
                     primary_key: Optional[List[str]] = None, indexes: Optional[List[str]] = None) -> bool:
        """创建数据模式"""
        if primary_key is None:
            primary_key = []
        if indexes is None:
            indexes = []
        try:
            schema = DataSchema(
                schema_id=schema_id,
                name=name,
                version="1.0",
                fields=fields,
                primary_key=primary_key or [],
                indexes=indexes or [],
                constraints=[],
                created_at=time.time()
            )
            
            self.schemas[schema_id] = schema
            self.logger.info(f"创建数据模式: {schema_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建数据模式失败: {e}")
            return False
    
    def create_export_job(self, schema_id: str, export_type: ExportType,
                         data_format: DataFormat, destination: str,
                         filters: Optional[Dict[str, Any]] = None) -> str:
        """创建导出任务"""
        try:
            job_id = f"value"
            
            job = ExportJob(
                job_id=job_id,
                schema_id=schema_id,
                export_type=export_type,
                data_format=data_format,
                destination=destination,
                filters=filters or {},
                status="pending",
                created_at=time.time(),
                started_at=None,
                completed_at=None,
                progress=0.0,
                error_message=None,
                metadata={}
            )
            
            self.export_jobs[job_id] = job
            self.logger.info(f"创建导出任务: {job_id}")
            return job_id
            
        except Exception as e:
            self.logger.error(f"创建导出任务失败: {e}")
            return job_id
    
    def execute_export_job(self, job_id: str, data: List[Dict[str, Any]]) -> bool:
        """执行导出任务"""
        try:
            job = self.export_jobs.get(job_id)
            if not job:
                self.logger.error(f"导出任务不存在: {job_id}")
                return False
            
            job.status = "running"
            job.started_at = time.time()
            job.progress = 0.0
            
            self.logger.info(f"开始执行导出任务: {job_id}")
            
            # 根据数据格式执行导出
            if job.data_format == DataFormat.JSON:
                success = self._export_to_json(job, data)
            elif job.data_format == DataFormat.CSV:
                success = self._export_to_csv(job, data)
            elif job.data_format == DataFormat.SQLITE:
                success = self._export_to_sqlite(job, data)
            elif job.data_format == DataFormat.PARQUET:
                success = self._export_to_parquet(job, data)
            elif job.data_format == DataFormat.EXCEL:
                success = self._export_to_excel(job, data)
            else:
                self.logger.error(f"不支持的数据格式: {job.data_format.value}")
                success = False
            
            if success:
                job.status = "completed"
                self.logger.info(f"导出任务完成: {job_id}")
            else:
                job.status = "failed"
                job.error_message = "导出失败"
                self.logger.error(f"导出任务失败: {job_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"执行导出任务失败: {e}")
            if job:
                job.status = "failed"
                job.error_message = str(e)
            return False
    
    def _export_to_json(self, job: ExportJob, data: List[Dict[str, Any]]) -> bool:
        """导出为JSON格式"""
        try:
            export_data = {
                "schema_id": job.schema_id,
                "export_type": job.export_type.value,
                "created_at": job.created_at,
                "data": data,
                "metadata": job.metadata
            }
            
            file_path = f"export_{job.job_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"JSON导出完成: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"JSON导出失败: {e}")
            return False
    
    def _export_to_csv(self, job: ExportJob, data: List[Dict[str, Any]]) -> bool:
        """导出为CSV格式"""
        try:
            if not data:
                self.logger.warning("没有数据可导出")
                return False
            
            # 获取所有字段名
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            
            file_path = f"{job.destination}/export_{job.job_id}.csv"
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=list(fieldnames))
                writer.writeheader()
                writer.writerows(data)
            
            self.logger.info(f"CSV导出完成: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"CSV导出失败: {e}")
            return False
    
    def _export_to_sqlite(self, job: ExportJob, data: List[Dict[str, Any]]) -> bool:
        """导出为SQLite格式"""
        try:
            file_path = os.path.join(self.warehouse_path, f"{job.job_id}.db")
            
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            
            # 获取模式信息
            schema = self.schemas.get(job.schema_id)
            if not schema:
                self.logger.error(f"模式不存在: {job.schema_id}")
                return False
            
            # 创建表
            table_name = schema.schema_id
            create_table_sql = self._generate_create_table_sql(schema)
            cursor.execute(create_table_sql)
            
            # 插入数据
            if data:
                insert_sql = self._generate_insert_sql(schema, data[0])
                cursor.executemany(insert_sql, [tuple(row.values()) for row in data])
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"SQLite导出完成: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"SQLite导出失败: {e}")
            return False
    
    def _export_to_parquet(self, job: ExportJob, data: List[Dict[str, Any]]) -> bool:
        """导出为Parquet格式"""
        try:
            file_path = os.path.join(self.warehouse_path, f"{job.job_id}.parquet")
            
            if not data:
                return True
            
            df = pd.DataFrame(data)
            df.to_parquet(file_path, index=False)
            
            self.logger.info(f"Parquet导出完成: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Parquet导出失败: {e}")
            return False
    
    def _export_to_excel(self, job: ExportJob, data: List[Dict[str, Any]]) -> bool:
        """导出为Excel格式"""
        try:
            file_path = os.path.join(self.warehouse_path, f"{job.job_id}.xlsx")
            
            if not data:
                return True
            
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            
            self.logger.info(f"Excel导出完成: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Excel导出失败: {e}")
            return False
    
    def _generate_create_table_sql(self, schema: DataSchema) -> str:
        """生成创建表SQL"""
        fields = []
        for field in schema.fields:
            field_name = field["name"]
            field_type = self._convert_field_type(field["type"])
            required = "NOT NULL" if field.get("type", False) else ""
            fields.append(f"{field_name} {field_type} {required}")
        
        sql = f"CREATE TABLE {schema.schema_id} ({', '.join(fields)}"
        
        if schema.primary_key:
            sql += f", PRIMARY KEY ({', '.join(schema.primary_key)})"
        
        sql += ")"
        return sql
    
    def _convert_field_type(self, field_type: str) -> str:
        """转换字段类型"""
        type_mapping = {
            "string": "TEXT",
            "integer": "INTEGER",
            "float": "REAL",
            "boolean": "BOOLEAN",
            "datetime": "DATETIME",
            "json": "TEXT"
        }
        return type_mapping.get(field_type, "TEXT")
    
    def _generate_insert_sql(self, schema: DataSchema, sample_data: Dict[str, Any]) -> str:
        """生成插入SQL"""
        fields = list(sample_data.keys())
        placeholders = ", ".join(["?" for _ in fields])
        return f"INSERT INTO {schema.schema_id} ({', '.join(fields)}) VALUES ({placeholders})"
    
    def get_export_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取导出任务状态"""
        job = self.export_jobs.get(job_id)
        if not job:
            return None
        
        return {
            "job_id": job.job_id,
            "schema_id": job.schema_id,
            "export_type": job.export_type.value,
            "data_format": job.data_format.value,
            "status": job.status,
            "progress": job.progress,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "error_message": job.error_message
        }
    
    def list_export_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出导出任务"""
        jobs = []
        for job in self.export_jobs.values():
            if status is None or job.status == status:
                job_status = self.get_export_job_status(job.job_id)
                if job_status is not None:
                    jobs.append(job_status)
        return jobs
    
    def get_schema(self, schema_id: str) -> Optional[Dict[str, Any]]:
        """获取数据模式"""
        schema = self.schemas.get(schema_id)
        if not schema:
            return None
        
        return {
            "schema_id": schema.schema_id,
            "name": schema.name,
            "version": schema.version,
            "fields": schema.fields,
            "primary_key": schema.primary_key,
            "indexes": schema.indexes,
            "constraints": schema.constraints,
            "created_at": schema.created_at
        }
    
    def list_schemas(self) -> List[Dict[str, Any]]:
        """列出数据模式"""
        schemas = []
        for schema_id in self.schemas.keys():
            schema = self.get_schema(schema_id)
            if schema is not None:
                schemas.append(schema)
        return schemas


# 全局实例
warehouse_connector = WarehouseConnector()
