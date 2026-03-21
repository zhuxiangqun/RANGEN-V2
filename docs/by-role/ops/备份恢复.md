# 💾 备份与恢复策略

本文档详细介绍了RANGEN系统的备份与恢复策略，确保在数据丢失或系统故障时能够快速恢复业务。

## 📋 目录

- [备份策略概述](#备份策略概述)
- [数据分类与保护级别](#数据分类与保护级别)
- [备份架构设计](#备份架构设计)
- [备份实施方案](#备份实施方案)
- [恢复流程](#恢复流程)
- [测试与验证](#测试与验证)
- [监控与告警](#监控与验证)
- [合规性要求](#合规性要求)
- [成本优化](#成本优化)
- [最佳实践](#最佳实践)

---

## 📊 备份策略概述

### 设计原则

RANGEN备份策略遵循以下核心原则：

1. **3-2-1规则**：3份数据副本，2种不同介质，1份异地备份
2. **最小数据丢失**：通过持续备份和日志归档实现最小RPO（恢复点目标）
3. **快速恢复**：优化恢复流程，实现最小RTO（恢复时间目标）
4. **自动化管理**：自动化备份、验证和清理流程
5. **安全加密**：所有备份数据在传输和存储时加密

### 备份策略矩阵

| 数据类别 | 备份频率 | 保留策略 | 恢复目标 | 存储位置 |
|---------|---------|---------|---------|---------|
| 配置数据 | 实时同步 | 永久保留 | RTO < 1分钟 | 配置中心 + Git |
| 业务数据 | 每小时增量 + 每日全量 | 30天增量 + 1年全量 | RTO < 15分钟 | 本地 + 云存储 |
| 日志数据 | 实时流式备份 | 90天热存储 + 1年冷存储 | RTO < 5分钟 | 对象存储 |
| 向量数据 | 每日增量 + 每周全量 | 7天增量 + 30天全量 | RTO < 30分钟 | 专用存储 |
| 模型数据 | 版本化备份 | 永久保留主要版本 | RTO < 1小时 | 模型仓库 |
| 监控数据 | 每小时快照 | 30天热存储 + 1年冷存储 | RTO < 10分钟 | 时间序列数据库 |

---

## 🔢 数据分类与保护级别

### 数据分类

#### 1. 关键数据（Tier 1）
- **定义**：系统运行必需，丢失会导致业务中断
- **示例**：数据库主数据、用户凭证、API密钥
- **保护级别**：最高级别，多副本实时同步

#### 2. 重要数据（Tier 2）
- **定义**：业务重要数据，丢失会影响用户体验
- **示例**：用户会话、知识库数据、对话历史
- **保护级别**：高频率备份，快速恢复

#### 3. 一般数据（Tier 3）
- **定义**：辅助性数据，丢失影响有限
- **示例**：日志文件、监控数据、临时文件
- **保护级别**：定期备份，标准恢复

#### 4. 归档数据（Tier 4）
- **定义**：历史数据，用于合规和审计
- **示例**：审计日志、合规记录、历史报表
- **保护级别**：长期归档，按需恢复

### 保护级别定义

```yaml
# config/backup/protection_levels.yaml
protection_levels:
  platinum:
    description: "最高级别保护 - 关键业务数据"
    backup_frequency: "continuous"  # 持续备份
    recovery_point_objective: "0"   # RPO = 0 (无数据丢失)
    recovery_time_objective: "1m"   # RTO < 1分钟
    replication_factor: 3
    geographic_redundancy: true
    encryption: "aes-256-gcm"
    
  gold:
    description: "高级别保护 - 重要业务数据"
    backup_frequency: "15m"         # 每15分钟
    recovery_point_objective: "15m" # RPO < 15分钟
    recovery_time_objective: "15m"  # RTO < 15分钟
    replication_factor: 2
    geographic_redundancy: true
    encryption: "aes-256-gcm"
    
  silver:
    description: "标准保护 - 一般业务数据"
    backup_frequency: "1h"          # 每小时
    recovery_point_objective: "1h"  # RPO < 1小时
    recovery_time_objective: "1h"   # RTO < 1小时
    replication_factor: 2
    geographic_redundancy: false
    encryption: "aes-256-cbc"
    
  bronze:
    description: "基本保护 - 归档数据"
    backup_frequency: "1d"          # 每天
    recovery_point_objective: "24h" # RPO < 24小时
    recovery_time_objective: "24h"  # RTO < 24小时
    replication_factor: 1
    geographic_redundancy: false
    encryption: "aes-128-cbc"
```

---

## 🏗️ 备份架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    生产环境 (Production)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  数据库集群  │  │  向量数据库  │  │  对象存储    │       │
│  │  PostgreSQL │  │   ChromaDB  │  │    S3      │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│         │                │                │               │
│  ┌──────┴────────────────┴────────────────┴──────┐       │
│  │             备份代理 (Backup Agent)              │       │
│  │  ┌────────────────────────────────────────┐  │       │
│  │  │  数据采集 → 压缩加密 → 分块传输 → 验证   │  │       │
│  │  └────────────────────────────────────────┘  │       │
│  └─────────────────────┬────────────────────────┘       │
│                        │                                 │
│        ┌───────────────┼───────────────┐               │
│        │               │               │               │
│  ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐       │
│  │  本地备份  │  │  同城备份  │  │  异地备份  │       │
│  │  存储中心  │  │  存储中心  │  │  存储中心  │       │
│  │  (SSD)    │  │  (HDD)    │  │  (云存储)  │       │
│  └───────────┘  └───────────┘  └───────────┘       │
│        │               │               │               │
│  ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐       │
│  │  备份索引  │  │  备份索引  │  │  备份索引  │       │
│  │  数据库    │  │  数据库    │  │  数据库    │       │
│  └───────────┘  └───────────┘  └───────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 组件说明

#### 1. 备份代理 (Backup Agent)

```python
# src/services/backup_agent.py
import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class BackupType(Enum):
    FULL = "full"        # 全量备份
    INCREMENTAL = "incremental"  # 增量备份
    DIFFERENTIAL = "differential"  # 差异备份
    CONTINUOUS = "continuous"    # 持续备份

class CompressionType(Enum):
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"
    ZSTD = "zstd"

@dataclass
class BackupJob:
    job_id: str
    data_source: str
    backup_type: BackupType
    compression: CompressionType
    encryption_key: Optional[str]
    destination: List[str]
    retention_days: int
    metadata: Dict

class BackupAgent:
    def __init__(self):
        self.active_jobs: Dict[str, BackupJob] = {}
        self.backup_history: List[Dict] = []
        
    async def start_backup_job(self, job_config: Dict) -> str:
        """启动备份任务"""
        job_id = self._generate_job_id()
        
        job = BackupJob(
            job_id=job_id,
            data_source=job_config["data_source"],
            backup_type=BackupType(job_config.get("type", "incremental")),
            compression=CompressionType(job_config.get("compression", "zstd")),
            encryption_key=job_config.get("encryption_key"),
            destination=job_config["destination"],
            retention_days=job_config.get("retention_days", 30),
            metadata=job_config.get("metadata", {})
        )
        
        self.active_jobs[job_id] = job
        
        # 异步执行备份
        asyncio.create_task(self._execute_backup_job(job))
        
        logger.info(f"备份任务已启动: {job_id}")
        return job_id
        
    async def _execute_backup_job(self, job: BackupJob):
        """执行备份任务"""
        try:
            # 1. 数据采集
            data = await self._collect_data(job.data_source, job.backup_type)
            
            # 2. 数据压缩
            compressed_data = await self._compress_data(data, job.compression)
            
            # 3. 数据加密
            if job.encryption_key:
                encrypted_data = await self._encrypt_data(compressed_data, job.encryption_key)
            else:
                encrypted_data = compressed_data
                
            # 4. 计算校验和
            checksum = self._calculate_checksum(encrypted_data)
            
            # 5. 分块传输到多个目的地
            transfer_tasks = []
            for destination in job.destination:
                task = asyncio.create_task(
                    self._transfer_to_destination(encrypted_data, destination, job)
                )
                transfer_tasks.append(task)
                
            # 等待所有传输完成
            transfer_results = await asyncio.gather(*transfer_tasks, return_exceptions=True)
            
            # 6. 验证备份
            verification_results = await self._verify_backup(job, checksum, transfer_results)
            
            # 7. 记录备份历史
            self._record_backup_history(job, checksum, verification_results)
            
            logger.info(f"备份任务完成: {job.job_id}")
            
        except Exception as e:
            logger.error(f"备份任务失败: {job.job_id}, 错误: {e}")
            self._record_backup_failure(job, str(e))
            
        finally:
            # 清理活动任务
            self.active_jobs.pop(job.job_id, None)
            
    async def _collect_data(self, data_source: str, backup_type: BackupType):
        """采集数据"""
        if data_source.startswith("postgresql://"):
            return await self._collect_database_data(data_source, backup_type)
        elif data_source.startswith("redis://"):
            return await self._collect_cache_data(data_source, backup_type)
        elif data_source.startswith("s3://"):
            return await self._collect_object_storage_data(data_source, backup_type)
        else:
            raise ValueError(f"不支持的数据源: {data_source}")
            
    async def _compress_data(self, data: bytes, compression: CompressionType) -> bytes:
        """压缩数据"""
        if compression == CompressionType.NONE:
            return data
        elif compression == CompressionType.GZIP:
            import gzip
            return gzip.compress(data)
        elif compression == CompressionType.LZ4:
            import lz4.frame
            return lz4.frame.compress(data)
        elif compression == CompressionType.ZSTD:
            import zstandard as zstd
            return zstd.compress(data)
        else:
            raise ValueError(f"不支持的压缩类型: {compression}")
            
    def _calculate_checksum(self, data: bytes) -> str:
        """计算校验和"""
        return hashlib.sha256(data).hexdigest()
        
    def _generate_job_id(self) -> str:
        """生成任务ID"""
        import uuid
        return f"backup_{uuid.uuid4().hex[:8]}"
```

#### 2. 备份存储中心

```yaml
# config/backup/storage_centers.yaml
storage_centers:
  local:
    name: "本地备份中心"
    type: "nas"
    protocol: "nfs"
    path: "/mnt/backup/rangen"
    capacity_gb: 10000
    available_gb: 7500
    performance_tier: "high"
    encryption: true
    retention_policy: "30d_hot"
    
  same_city:
    name: "同城备份中心"
    type: "object_storage"
    provider: "aws_s3"
    bucket: "rangen-backup-same-city"
    region: "us-east-1"
    storage_class: "standard_ia"
    encryption: "sse-s3"
    retention_policy: "90d_warm"
    
  cross_region:
    name: "跨区域备份中心"
    type: "object_storage"
    provider: "aws_s3"
    bucket: "rangen-backup-cross-region"
    region: "us-west-2"
    storage_class: "glacier_ir"
    encryption: "sse-kms"
    retention_policy: "365d_cold"
    
  archival:
    name: "归档存储中心"
    type: "tape_library"
    provider: "aws_glacier"
    vault: "rangen-archival-vault"
    retrieval_tier: "expedited"
    encryption: true
    retention_policy: "7y_archival"
```

---

## 🚀 备份实施方案

### 数据库备份方案

#### PostgreSQL备份配置

```yaml
# config/backup/postgresql_backup.yaml
postgresql_backup:
  # 基础配置
  enabled: true
  schedule: "cron"
  
  # 备份计划
  schedules:
    continuous:
      type: "wal"  # Write-Ahead Logging
      enabled: true
      retention: "7d"
      archive_command: "test ! -f /mnt/wal_archive/%f && cp %p /mnt/wal_archive/%f"
      
    incremental:
      type: "basebackup"
      schedule: "0 */6 * * *"  # 每6小时
      retention: "7d"
      compression: "zstd"
      
    full:
      type: "pg_dumpall"
      schedule: "0 2 * * *"    # 每天凌晨2点
      retention: "30d"
      compression: "gzip"
      format: "custom"
      
    monthly:
      type: "logical"
      schedule: "0 3 1 * *"    # 每月1号凌晨3点
      retention: "365d"
      
  # 存储目的地
  destinations:
    - name: "local_nas"
      path: "/mnt/backup/postgresql"
      retention: "30d"
      
    - name: "s3_same_city"
      s3_bucket: "rangen-db-backup"
      s3_prefix: "postgresql/"
      retention: "90d"
      
    - name: "s3_cross_region"
      s3_bucket: "rangen-dr-backup"
      s3_prefix: "postgresql/"
      retention: "365d"
      
  # 验证配置
  verification:
    enabled: true
    schedule: "0 4 * * *"  # 每天凌晨4点
    methods:
      - "checksum_validation"
      - "restore_test"
      - "consistency_check"
      
  # 监控配置
  monitoring:
    metrics:
      - "backup_size_bytes"
      - "backup_duration_seconds"
      - "backup_success_rate"
      - "restore_test_success_rate"
    alerts:
      - "backup_failed"
      - "backup_duration_exceeded"
      - "verification_failed"
```

#### 备份执行脚本

```bash
#!/bin/bash
# scripts/backup_postgresql.sh

set -euo pipefail

# 配置参数
BACKUP_TYPE=${1:-"incremental"}
BACKUP_NAME="postgresql_${BACKUP_TYPE}_$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="/mnt/backup/postgresql/${BACKUP_NAME}"
LOG_FILE="/var/log/rangen/backup_postgresql_$(date +%Y%m%d).log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 错误处理函数
error_exit() {
    log "ERROR: $1"
    # 发送告警
    python /opt/rangen/scripts/send_alert.py \
        --severity "critical" \
        --message "PostgreSQL备份失败: $1" \
        --component "backup" \
        --action "check_logs"
    exit 1
}

# 创建备份目录
mkdir -p "$BACKUP_DIR"
log "开始PostgreSQL ${BACKUP_TYPE}备份: ${BACKUP_NAME}"

# 根据备份类型执行不同的备份策略
case "$BACKUP_TYPE" in
    "full")
        # 全量备份
        log "执行全量备份..."
        pg_dumpall \
            --host=localhost \
            --port=5432 \
            --username=postgres \
            --file="${BACKUP_DIR}/full_backup.sql" \
            --verbose 2>> "$LOG_FILE" || error_exit "全量备份失败"
        
        # 压缩备份文件
        gzip "${BACKUP_DIR}/full_backup.sql"
        ;;
        
    "incremental")
        # 增量备份（基于WAL）
        log "执行增量备份..."
        
        # 1. 创建基础备份
        pg_basebackup \
            --host=localhost \
            --port=5432 \
            --username=replicator \
            --pgdata="${BACKUP_DIR}/base" \
            --format=plain \
            --write-recovery-conf \
            --progress \
            --verbose 2>> "$LOG_FILE" || error_exit "基础备份失败"
            
        # 2. 归档WAL日志
        log "归档WAL日志..."
        pg_archivecleanup "${BACKUP_DIR}/base" "$(psql -t -c "SELECT pg_current_wal_lsn()")" 2>> "$LOG_FILE"
        ;;
        
    "continuous")
        # 持续备份（WAL流式传输）
        log "配置WAL流式备份..."
        
        # 配置archive_command
        cat > "${BACKUP_DIR}/recovery.conf" << EOF
restore_command = 'cp /mnt/wal_archive/%f %p'
recovery_target_timeline = 'latest'
EOF
        
        # 启动WAL接收器
        pg_receivewal \
            --directory="${BACKUP_DIR}/wal" \
            --verbose \
            --no-loop \
            --synchronous &
        WAL_PID=$!
        
        # 等待WAL传输完成
        sleep 30
        kill $WAL_PID
        ;;
        
    *)
        error_exit "不支持的备份类型: $BACKUP_TYPE"
        ;;
esac

# 计算校验和
log "计算备份文件校验和..."
find "$BACKUP_DIR" -type f -name "*.gz" -o -name "*.sql" -o -name "*.wal" | while read -r file; do
    sha256sum "$file" >> "${BACKUP_DIR}/checksums.txt"
done

# 同步到远程存储
log "同步备份到远程存储..."
python /opt/rangen/scripts/sync_backup.py \
    --source "$BACKUP_DIR" \
    --destinations "s3://rangen-db-backup/postgresql/${BACKUP_NAME},s3://rangen-dr-backup/postgresql/${BACKUP_NAME}" \
    --retention "30d" \
    --log "$LOG_FILE" || error_exit "远程同步失败"

# 清理旧备份
log "清理过期备份..."
find /mnt/backup/postgresql -type d -name "postgresql_*" -mtime +30 -exec rm -rf {} \; 2>/dev/null || true

# 记录备份完成
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "备份完成: ${BACKUP_NAME}, 大小: ${BACKUP_SIZE}, 耗时: ${SECONDS}秒"

# 发送成功通知
python /opt/rangen/scripts/send_notification.py \
    --title "PostgreSQL备份成功" \
    --message "备份名称: ${BACKUP_NAME}\n大小: ${BACKUP_SIZE}\n耗时: ${SECONDS}秒" \
    --level "info"
```

### 向量数据库备份方案

#### ChromaDB备份配置

```yaml
# config/backup/chromadb_backup.yaml
chromadb_backup:
  enabled: true
  mode: "distributed"  # distributed, centralized
  
  # 备份策略
  strategy:
    incremental:
      enabled: true
      schedule: "*/30 * * * *"  # 每30分钟
      max_incremental_backups: 48  # 保留24小时
      
    full:
      enabled: true
      schedule: "0 1 * * *"  # 每天凌晨1点
      retention: "7d"
      
    snapshot:
      enabled: true
      trigger: "collection_size > 1000000"  # 集合大小超过100万条
      retention: "30d"
      
  # 数据导出格式
  export_format:
    primary: "parquet"  # 主格式
    secondary: "jsonl"  # 备用格式
    compression: "snappy"
    
  # 存储配置
  storage:
    local:
      path: "/mnt/backup/chromadb"
      quota_gb: 500
      
    s3:
      bucket: "rangen-vector-backup"
      prefix: "chromadb/"
      storage_class: "intelligent_tiering"
      
    glacier:
      enabled: true
      vault: "rangen-vector-archive"
      retrieval_days: 365
      
  # 验证配置
  verification:
    data_integrity:
      enabled: true
      method: "checksum_validation"
      
    restore_test:
      enabled: true
      frequency: "weekly"
      environment: "staging"
      
  # 性能配置
  performance:
    max_concurrent_backups: 3
    chunk_size_mb: 256
    compression_level: 6
```

#### 向量数据库备份脚本

```python
# scripts/backup_chromadb.py
#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import chromadb
from chromadb.config import Settings
import boto3
from botocore.exceptions import ClientError
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/rangen/chromadb_backup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ChromaDBBackup:
    def __init__(self, config_path: str = "/etc/rangen/backup/chromadb_config.yaml"):
        self.config = self._load_config(config_path)
        self.client = self._initialize_chromadb_client()
        self.s3_client = boto3.client('s3') if self.config.get('s3', {}).get('enabled') else None
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
            
    def _initialize_chromadb_client(self):
        """初始化ChromaDB客户端"""
        settings = Settings(
            chroma_api_impl="rest",
            chroma_server_host=self.config['chromadb']['host'],
            chroma_server_http_port=self.config['chromadb']['port'],
            chroma_server_ssl=self.config['chromadb'].get('ssl', False)
        )
        return chromadb.Client(settings)
        
    async def backup_collection(self, collection_name: str, backup_type: str = "incremental"):
        """备份指定集合"""
        logger.info(f"开始备份集合: {collection_name}, 类型: {backup_type}")
        
        try:
            # 获取集合
            collection = self.client.get_collection(collection_name)
            
            # 创建备份目录
            backup_dir = self._create_backup_directory(collection_name, backup_type)
            
            # 根据备份类型执行备份
            if backup_type == "full":
                await self._full_backup(collection, backup_dir)
            elif backup_type == "incremental":
                await self._incremental_backup(collection, backup_dir)
            elif backup_type == "snapshot":
                await self._snapshot_backup(collection, backup_dir)
            else:
                raise ValueError(f"不支持的备份类型: {backup_type}")
                
            # 生成元数据
            metadata = self._generate_metadata(collection, backup_type, backup_dir)
            
            # 保存元数据
            self._save_metadata(metadata, backup_dir)
            
            # 计算校验和
            checksum = self._calculate_checksum(backup_dir)
            
            # 上传到远程存储
            if self.s3_client:
                await self._upload_to_s3(backup_dir, collection_name, backup_type)
                
            # 清理旧备份
            self._cleanup_old_backups(collection_name)
            
            logger.info(f"集合备份完成: {collection_name}, 校验和: {checksum}")
            return {
                "success": True,
                "collection": collection_name,
                "backup_type": backup_type,
                "backup_dir": str(backup_dir),
                "checksum": checksum,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"备份集合失败: {collection_name}, 错误: {e}")
            return {
                "success": False,
                "collection": collection_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    async def _full_backup(self, collection, backup_dir: Path):
        """执行全量备份"""
        logger.info("执行全量备份...")
        
        # 获取所有数据
        results = collection.get(
            include=["embeddings", "documents", "metadatas", "ids"]
        )
        
        # 转换为DataFrame
        df = pd.DataFrame({
            "id": results["ids"],
            "document": results["documents"],
            "metadata": [json.dumps(m) if m else "" for m in results["metadatas"]],
            "embedding": [json.dumps(e.tolist()) if e is not None else "" for e in results["embeddings"]]
        })
        
        # 保存为Parquet格式
        parquet_path = backup_dir / "data.parquet"
        df.to_parquet(parquet_path, compression="snappy")
        
        # 保存为JSONL格式（备份）
        jsonl_path = backup_dir / "data.jsonl"
        df.to_json(jsonl_path, orient="records", lines=True)
        
        logger.info(f"全量备份完成, 文件大小: {parquet_path.stat().st_size / 1024 / 1024:.2f}MB")
        
    async def _incremental_backup(self, collection, backup_dir: Path):
        """执行增量备份"""
        logger.info("执行增量备份...")
        
        # 获取上次备份后的变化
        # 这里需要实现增量检测逻辑
        # 暂时简化为全量备份
        await self._full_backup(collection, backup_dir)
        
    def _create_backup_directory(self, collection_name: str, backup_type: str) -> Path:
        """创建备份目录"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(self.config['storage']['local']['path']) / \
                    collection_name / \
                    backup_type / \
                    timestamp
                    
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
        
    def _generate_metadata(self, collection, backup_type: str, backup_dir: Path) -> Dict:
        """生成备份元数据"""
        collection_metadata = collection.metadata or {}
        
        return {
            "collection_name": collection.name,
            "backup_type": backup_type,
            "timestamp": datetime.now().isoformat(),
            "collection_metadata": collection_metadata,
            "item_count": collection.count(),
            "backup_dir": str(backup_dir),
            "system": {
                "chromadb_version": "1.0.0",  # 实际应从客户端获取
                "backup_version": "1.0.0"
            }
        }
        
    def _save_metadata(self, metadata: Dict, backup_dir: Path):
        """保存元数据"""
        metadata_path = backup_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
    def _calculate_checksum(self, backup_dir: Path) -> str:
        """计算备份目录的校验和"""
        import hashlib
        
        sha256_hash = hashlib.sha256()
        
        # 按文件路径排序，确保一致性
        files = sorted(backup_dir.glob("**/*"))
        
        for file_path in files:
            if file_path.is_file():
                # 添加文件路径
                relative_path = file_path.relative_to(backup_dir)
                sha256_hash.update(str(relative_path).encode('utf-8'))
                
                # 添加文件内容
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(chunk)
                        
        return sha256_hash.hexdigest()
        
    async def _upload_to_s3(self, backup_dir: Path, collection_name: str, backup_type: str):
        """上传到S3"""
        if not self.s3_client:
            return
            
        s3_config = self.config.get('s3', {})
        bucket = s3_config.get('bucket')
        prefix = s3_config.get('prefix', '')
        
        if not bucket:
            logger.warning("S3配置不完整，跳过上传")
            return
            
        # 上传所有文件
        for file_path in backup_dir.glob("**/*"):
            if file_path.is_file():
                s3_key = f"{prefix}{collection_name}/{backup_type}/{backup_dir.name}/{file_path.relative_to(backup_dir)}"
                
                try:
                    self.s3_client.upload_file(
                        str(file_path),
                        bucket,
                        s3_key,
                        ExtraArgs={
                            'StorageClass': s3_config.get('storage_class', 'STANDARD'),
                            'ServerSideEncryption': 'AES256' if s3_config.get('encryption') else None
                        }
                    )
                    logger.debug(f"文件已上传到S3: {s3_key}")
                except ClientError as e:
                    logger.error(f"上传文件到S3失败: {file_path}, 错误: {e}")
                    
    def _cleanup_old_backups(self, collection_name: str):
        """清理旧备份"""
        local_path = Path(self.config['storage']['local']['path']) / collection_name
        
        if not local_path.exists():
            return
            
        # 清理策略
        retention_days = {
            'full': self.config['strategy']['full'].get('retention_days', 7),
            'incremental': self.config['strategy']['incremental'].get('retention_days', 1),
            'snapshot': self.config['strategy']['snapshot'].get('retention_days', 30)
        }
        
        for backup_type in ['full', 'incremental', 'snapshot']:
            type_path = local_path / backup_type
            if not type_path.exists():
                continue
                
            days = retention_days[backup_type]
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for backup_dir in type_path.iterdir():
                if backup_dir.is_dir():
                    try:
                        dir_time = os.path.getmtime(backup_dir)
                        if dir_time < cutoff_time:
                            import shutil
                            shutil.rmtree(backup_dir)
                            logger.info(f"删除过期备份: {backup_dir}")
                    except Exception as e:
                        logger.error(f"删除备份目录失败: {backup_dir}, 错误: {e}")

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ChromaDB备份工具')
    parser.add_argument('--collection', type=str, required=True, help='要备份的集合名称')
    parser.add_argument('--type', type=str, default='incremental', 
                       choices=['full', 'incremental', 'snapshot'],
                       help='备份类型')
    parser.add_argument('--config', type=str, 
                       default='/etc/rangen/backup/chromadb_config.yaml',
                       help='配置文件路径')
    
    args = parser.parse_args()
    
    # 创建备份实例
    backup = ChromaDBBackup(args.config)
    
    # 执行备份
    result = await backup.backup_collection(args.collection, args.type)
    
    # 输出结果
    if result['success']:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📝 文档总结

### 文档概述

本文档提供了RANGEN系统的完整备份与恢复策略，涵盖了以下关键领域：

1. **备份策略**：详细的数据备份方法和最佳实践
2. **恢复流程**：各种故障场景下的恢复步骤和操作指南  
3. **测试验证**：备份恢复的测试框架和验证方法
4. **监控告警**：全面的监控指标和告警配置
5. **最佳实践**：备份恢复的实施建议和优化策略

### 关键要点

1. **3-2-1备份规则**：至少3份副本，2种介质，1份异地
2. **自动化优先**：所有备份恢复操作应自动化实施
3. **定期验证**：备份必须通过恢复测试验证有效性
4. **分层保护**：根据数据重要性实施差异化保护策略

### 后续步骤

1. **立即执行**：根据文档配置基础备份和监控
2. **定期测试**：建立备份恢复的定期测试机制
3. **持续优化**：基于监控数据不断优化备份恢复策略

### 获取帮助

如需进一步帮助，请参考：
- [RANGEN高可用配置指南](file:///Users/apple/workdata/person/zy/RANGEN-main(syu-python)/docs/operations/deployment/high-availability.md)
- [常见问题解答](file:///Users/apple/workdata/person/zy/RANGEN-main(syu-python)/docs/operations/troubleshooting/common-issues.md)
- 技术支持：support@rangen.ai

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-08  
**文档状态**: ✅ 内容完成（结构待优化）  
**维护团队**: RANGEN运维文档组  

> **注意**: 本文档包含详细的备份恢复策略，但由于编辑过程中的重复，文档结构需要进一步整理。核心内容完整，建议在实施前进行结构整理。

---

## 📝 总结与最佳实践

### 核心原则

1. **3-2-1备份规则**
   - 至少3份数据副本
   - 存储在2种不同的介质上
   - 1份副本存储在异地

2. **自动化优先**
   - 所有备份恢复操作应自动化
   - 减少人为操作错误
   - 提高恢复速度和一致性

3. **定期验证**
   - 备份不等于恢复
   - 定期测试恢复流程
   - 验证数据完整性

4. **分层保护**
   - 根据数据重要性分层保护
   - 关键数据更频繁的备份
   - 不同级别的恢复目标

### 最佳实践清单

#### 备份策略最佳实践

| 实践项目 | 推荐配置 | 检查方法 |
|---------|---------|---------|
| 备份频率 | 关键数据: 每小时<br>重要数据: 每天<br>普通数据: 每周 | 检查备份时间戳 |
| 保留策略 | 最近7天每天备份<br>最近4周每周备份<br>最近12月每月备份 | 检查备份目录结构 |
| 加密要求 | 传输加密: TLS 1.2+<br>存储加密: AES-256 | 检查配置文件 |
| 压缩要求 | 文本数据: gzip<br>二进制数据: lz4 | 检查备份文件大小 |

#### 恢复流程最佳实践

1. **事前准备**
   ```yaml
   # 恢复检查清单
   recovery_checklist:
     pre_recovery:
       - "确认故障范围和影响"
       - "通知相关团队和用户"
       - "备份当前状态（如果需要）"
       - "准备恢复环境"
       
     during_recovery:
       - "遵循标准操作流程"
       - "记录所有操作步骤"
       - "验证每一步的结果"
       
     post_recovery:
       - "验证数据完整性"
       - "验证业务功能"
       - "更新事件报告"
       - "进行事后分析"
   ```

2. **文档要求**
   - 每个恢复流程必须有详细的运行手册
   - 包含故障场景、恢复步骤、验证方法
   - 定期更新和维护

#### 测试验证最佳实践

1. **测试频率**
   ```yaml
   testing_frequency:
     integrity_tests: "daily"      # 完整性测试每天
     recovery_tests: "weekly"      # 恢复测试每周
     disaster_drills: "quarterly"  # 灾难演练每季度
     full_scale_tests: "annually"  # 全规模测试每年
   ```

2. **测试环境**
   - 使用与生产环境相似的测试环境
   - 测试数据量至少为生产环境的10%
   - 测试环境与生产环境隔离

### 常见陷阱与避免方法

| 陷阱 | 症状 | 避免方法 |
|------|------|---------|
| 备份成功但无法恢复 | 恢复测试失败 | 定期进行恢复演练 |
| 备份空间不足 | 备份失败，存储使用率高 | 监控存储使用，自动清理旧备份 |
| 备份性能影响生产 | 生产系统性能下降 | 错峰备份，使用增量备份 |
| 加密密钥丢失 | 无法解密备份数据 | 密钥安全管理，多重备份 |
| 人为操作错误 | 误删除或覆盖备份 | 权限控制，操作审计 |

### 性能优化建议

#### 备份性能优化

```yaml
# config/backup/performance_optimization.yaml
performance_optimization:
  compression:
    algorithm: "zstd"  # 比gzip更快，压缩率相似
    level: 3           # 平衡速度和压缩率
    
  parallelism:
    max_concurrent_backups: 3
    max_concurrent_streams: 5
    
  throttling:
    enabled: true
    max_io_bandwidth_mbps: 100
    max_cpu_percent: 30
    
  incremental_optimization:
    block_size: "64KB"
    checksum_type: "xxhash"
```

#### 恢复性能优化

```python
# 并行恢复优化
import concurrent.futures

class ParallelRecovery:
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        
    def recover_multiple_databases(self, databases):
        """并行恢复多个数据库"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for db in databases:
                future = executor.submit(self._recover_database, db)
                futures[future] = db
                
            results = {}
            for future in concurrent.futures.as_completed(futures):
                db = futures[future]
                try:
                    results[db] = future.result()
                except Exception as e:
                    results[db] = {"success": False, "error": str(e)}
                    
            return results
            
    def _recover_database(self, database_config):
        """恢复单个数据库"""
        # 恢复逻辑
        pass
```

### 安全注意事项

1. **访问控制**
   - 备份数据应严格限制访问权限
   - 恢复操作需要多因素认证
   - 所有操作应有审计日志

2. **加密管理**
   - 备份数据必须加密存储
   - 加密密钥需要安全保管
   - 定期轮换加密密钥

3. **网络隔离**
   - 备份网络与生产网络隔离
   - 恢复环境与生产环境隔离
   - 限制备份数据的外部访问

### 成本优化策略

#### 存储成本优化

```yaml
# config/backup/cost_optimization.yaml
cost_optimization:
  storage_tiering:
    hot_storage:  # 最近7天备份
      type: "ssd"
      retention: "7d"
      
    warm_storage:  # 7-30天备份
      type: "hdd"
      retention: "30d"
      
    cold_storage:  # 30天以上备份
      type: "object_storage"
      retention: "365d"
      
  compression_optimization:
    enabled: true
    algorithm: "zstd"
    target_ratio: 0.3  # 目标压缩比30%
    
  deduplication:
    enabled: true
    block_size: "4KB"
    hash_algorithm: "sha256"
```

#### 网络成本优化

1. **增量备份**：减少数据传输量
2. **压缩传输**：减少带宽使用
3. **智能调度**：在低峰时段进行备份
4. **CDN加速**：对于多地备份使用CDN

---

## 📚 附录

### A. 术语表

| 术语 | 解释 |
|------|------|
| RTO (恢复时间目标) | 从故障发生到业务恢复的时间目标 |
| RPO (恢复点目标) | 可接受的数据丢失时间窗口 |
| 全量备份 | 备份所有数据的完整副本 |
| 增量备份 | 只备份自上次备份以来更改的数据 |
| 差异备份 | 备份自上次全量备份以来更改的数据 |
| 快照 | 数据在某一时间点的瞬时副本 |
| 灾备 | 在灾难情况下保持业务连续性的能力 |
| 备份窗口 | 执行备份操作的时间段 |
| 恢复点 | 可以恢复到的时间点 |

### B. 常用命令参考

#### PostgreSQL备份恢复命令

```bash
# 创建基础备份
pg_basebackup -D /backup/postgresql -Ft -z -P

# 创建逻辑备份
pg_dump -Fc -f /backup/postgresql.dump rangen

# 恢复逻辑备份
pg_restore -d rangen /backup/postgresql.dump

# 创建WAL归档
archive_command = 'cp %p /wal_archive/%f'
```

#### Redis备份恢复命令

```bash
# 创建RDB备份
redis-cli SAVE  # 同步保存
redis-cli BGSAVE # 后台保存

# 创建AOF备份
redis-cli BGREWRITEAOF

# 恢复RDB备份
cp /backup/redis/dump.rdb /var/lib/redis/
redis-server --appendonly yes
```

#### S3备份操作命令

```bash
# 上传备份到S3
aws s3 cp backup.tar.gz s3://rangen-backup/database/

# 从S3下载备份
aws s3 cp s3://rangen-backup/database/backup.tar.gz .

# 列出备份文件
aws s3 ls s3://rangen-backup/database/

# 删除旧备份
aws s3 rm s3://rangen-backup/database/ --recursive --exclude "*" --include "backup_2023*"
```

### C. 配置参考模板

#### 完整备份配置模板

```yaml
# config/backup/full_config_template.yaml
backup:
  strategy:
    type: "hybrid"  # full + incremental
    schedule:
      full: "0 2 * * 0"      # 每周日凌晨2点
      incremental: "0 */6 * * *"  # 每6小时
      
  retention:
    full_backups: 4           # 保留4个完整备份
    incremental_backups: 24   # 保留24个增量备份
    days: 30                  # 保留30天
    
  storage:
    local:
      path: "/backup/rangen"
      quota_gb: 1000
      
    s3:
      enabled: true
      bucket: "rangen-backup"
      region: "us-east-1"
      encryption: true
      
  encryption:
    enabled: true
    algorithm: "aes-256-gcm"
    key_rotation_days: 90
    
  monitoring:
    enabled: true
    metrics_endpoint: "http://localhost:9090/metrics"
    alert_rules: "/etc/rangen/backup/alerts.yaml"
```

### D. 故障排除指南

#### 常见问题与解决方案

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 备份失败 | 存储空间不足 | 清理旧备份，增加存储空间 |
| 备份缓慢 | 网络带宽不足 | 调整备份时间，增加带宽 |
| 恢复失败 | 备份文件损坏 | 使用其他备份点，验证备份完整性 |
| 加密错误 | 密钥错误或过期 | 检查密钥配置，更新密钥 |
| 权限错误 | 权限配置错误 | 检查用户权限，调整权限配置 |

#### 诊断命令

```bash
# 检查备份状态
systemctl status rangen-backup

# 查看备份日志
journalctl -u rangen-backup -f

# 检查存储使用
df -h /backup
du -sh /backup/*

# 验证备份完整性
python scripts/verify_backup_integrity.py --config /etc/rangen/backup/config.yaml

# 测试恢复
python scripts/test_recovery.py --dry-run --scope database
```

### E. 相关文档链接

1. **系统文档**
   - [RANGEN系统架构](file:///Users/apple/workdata/person/zy/RANGEN-main(syu-python)/docs/architecture/diagrams/system-architecture.md)
   - [高可用配置指南](file:///Users/apple/workdata/person/zy/RANGEN-main(syu-python)/docs/operations/deployment/high-availability.md)
   - [监控面板配置](file:///Users/apple/workdata/person/zy/RANGEN-main(syu-python)/docs/operations/monitoring/metrics-dashboard.md)

2. **外部资源**
   - [PostgreSQL官方备份文档](https://www.postgresql.org/docs/current/backup.html)
   - [Redis持久化文档](https://redis.io/docs/management/persistence/)
   - [AWS S3备份最佳实践](https://docs.aws.amazon.com/whitepapers/latest/backup-recovery/backup-recovery.html)

3. **工具参考**
   - [pgBackRest](https://pgbackrest.org/) - PostgreSQL备份工具
   - [BorgBackup](https://www.borgbackup.org/) - 去重备份工具
   - [Restic](https://restic.net/) - 快速安全的备份工具

### F. 更新日志

| 版本 | 日期 | 修改内容 | 修改人 |
|------|------|---------|--------|
| 1.0.0 | 2026-03-07 | 初始版本创建 | RANGEN文档团队 |
| 1.1.0 | 2026-03-08 | 增加测试验证章节 | RANGEN文档团队 |
| 1.2.0 | 2026-03-08 | 补充最佳实践和附录 | RANGEN文档团队 |
| 2.0.0 | 2026-03-08 | 完整重构，增加详细配置示例 | RANGEN文档团队 |

---

## 🎯 后续步骤

### 立即行动项

1. **评估当前备份状态**
   ```bash
   # 运行备份评估
   python scripts/assess_backup_status.py --full-report
   ```

2. **配置基础备份**
   ```bash
   # 配置数据库备份
   python scripts/configure_database_backup.py --apply
   
   # 配置向量数据库备份
   python scripts/configure_chromadb_backup.py --apply
   ```

3. **测试恢复流程**
   ```bash
   # 运行恢复测试
   python scripts/run_recovery_drill.py --type basic --scope database
   ```

4. **设置监控告警**
   ```bash
   # 部署备份监控
   python scripts/deploy_backup_monitoring.py --enable-alerts
   ```

### 长期计划

1. **季度审查**
   - 审查备份策略的有效性
   - 更新恢复运行手册
   - 进行灾难恢复演练

2. **年度评估**
   - 评估备份恢复的RTO/RPO目标
   - 更新技术架构和工具
   - 进行全规模恢复测试

3. **持续改进**
   - 收集备份恢复指标
   - 分析故障和成功案例
   - 优化流程和配置

### 获取帮助

如果在实施备份恢复策略过程中遇到问题，可以通过以下方式获取帮助：

1. **内部资源**
   - 查看本文档的相关章节
   - 参考配置模板和示例
   - 运行诊断脚本

2. **社区支持**
   - RANGEN用户社区: https://community.rangen.ai
   - GitHub Issues: https://github.com/rangen/rangen/issues

3. **专业支持**
   - 技术支持邮箱: support@rangen.ai
   - 紧急联系: emergency@rangen.ai
   - 企业客户: enterprise-support@rangen.ai

---

**文档版本**: 2.0.0  
**最后更新**: 2026-03-08  
**适用版本**: RANGEN V2.5+  
**文档状态**: ✅ 已完成  
**维护团队**: RANGEN运维文档组  

> **重要提示**: 备份恢复策略应根据实际业务需求和技术环境进行调整。建议在生产环境部署前，在测试环境中充分验证所有配置和流程。
```

---

## 🧪 测试与验证

备份恢复策略的有效性必须通过定期测试来验证。本节介绍备份恢复的测试框架和验证方法。

### 测试框架

```yaml
# config/backup/testing_framework.yaml
testing_framework:
  schedules:
    daily:
      - name: "备份完整性检查"
        time: "03:00"
        script: "scripts/test_backup_integrity.py"
        timeout: 1800
        
      - name: "恢复点验证"
        time: "04:00"
        script: "scripts/test_recovery_points.py"
        timeout: 3600
        
    weekly:
      - name: "完整恢复测试"
        day: "sunday"
        time: "02:00"
        script: "scripts/test_full_recovery.py"
        duration: "4h"
        
      - name: "性能基准测试"
        day: "saturday"
        time: "03:00"
        script: "scripts/test_recovery_performance.py"
        metrics: ["rto", "rpo", "throughput"]
        
    monthly:
      - name: "灾难恢复演练"
        day: "first"
        time: "00:00"
        script: "scripts/test_disaster_recovery.py"
        scope: "full"
        notification: "all_stakeholders"
        
  environments:
    - name: "dev"
      purpose: "功能测试"
      resources: "minimal"
      data_size: "10%"
      
    - name: "staging"
      purpose: "集成测试"
      resources: "production-like"
      data_size: "50%"
      
    - name: "dr"
      purpose: "灾难恢复测试"
      resources: "production-ready"
      data_size: "100%"
      
  success_criteria:
    - "备份完整性 >= 99.9%"
    - "恢复成功率 >= 99.5%"
    - "RTO <= 目标值的120%"
    - "RPO <= 目标值的150%"
    - "数据一致性 >= 99.99%"
```

### 备份完整性测试

```python
# scripts/test_backup_integrity.py
#!/usr/bin/env python3
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import hashlib
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupIntegrityTester:
    def __init__(self, config_path: str = "/etc/rangen/backup/integrity_config.yaml"):
        self.config = self._load_config(config_path)
        self.test_results = []
        
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
            
    def run_all_tests(self) -> Dict:
        """运行所有完整性测试"""
        tests = [
            self.test_backup_existence,
            self.test_backup_freshness,
            self.test_backup_checksums,
            self.test_backup_metadata,
            self.test_backup_accessibility
        ]
        
        results = {}
        for test_func in tests:
            test_name = test_func.__name__
            logger.info(f"运行测试: {test_name}")
            
            try:
                result = test_func()
                results[test_name] = result
                self.test_results.append({
                    "test": test_name,
                    "timestamp": datetime.now().isoformat(),
                    "result": "passed" if result["success"] else "failed",
                    "details": result
                })
            except Exception as e:
                logger.error(f"测试失败: {test_name}, 错误: {e}")
                results[test_name] = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
        overall_success = all(r["success"] for r in results.values())
        
        return {
            "overall_success": overall_success,
            "test_count": len(tests),
            "passed_count": sum(1 for r in results.values() if r["success"]),
            "failed_count": sum(1 for r in results.values() if not r["success"]),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    def test_backup_existence(self) -> Dict:
        """测试备份是否存在"""
        backup_dirs = self.config["backup_locations"]
        results = {}
        
        for location_name, location_config in backup_dirs.items():
            path = Path(location_config["path"])
            required_patterns = location_config.get("required_patterns", [])
            
            location_results = []
            for pattern in required_patterns:
                files = list(path.glob(pattern))
                exists = len(files) > 0
                location_results.append({
                    "pattern": pattern,
                    "exists": exists,
                    "file_count": len(files),
                    "files": [str(f) for f in files[:10]]  # 限制输出
                })
                
            all_exist = all(r["exists"] for r in location_results)
            results[location_name] = {
                "success": all_exist,
                "details": location_results
            }
            
        overall_success = all(r["success"] for r in results.values())
        
        return {
            "success": overall_success,
            "details": results,
            "timestamp": datetime.now().isoformat()
        }
        
    def test_backup_freshness(self) -> Dict:
        """测试备份新鲜度"""
        freshness_thresholds = self.config["freshness_thresholds"]
        results = {}
        
        for backup_type, threshold in freshness_thresholds.items():
            max_age_hours = threshold["max_age_hours"]
            
            # 查找最新备份
            latest_backup = self._find_latest_backup(backup_type)
            
            if latest_backup:
                backup_time = datetime.fromtimestamp(latest_backup["timestamp"])
                age_hours = (datetime.now() - backup_time).total_seconds() / 3600
                
                is_fresh = age_hours <= max_age_hours
                results[backup_type] = {
                    "success": is_fresh,
                    "age_hours": age_hours,
                    "max_age_hours": max_age_hours,
                    "backup_path": latest_backup["path"],
                    "backup_time": backup_time.isoformat()
                }
            else:
                results[backup_type] = {
                    "success": False,
                    "error": "No backup found",
                    "max_age_hours": max_age_hours
                }
                
        overall_success = all(r["success"] for r in results.values())
        
        return {
            "success": overall_success,
            "details": results,
            "timestamp": datetime.now().isoformat()
        }
        
    def test_backup_checksums(self) -> Dict:
        """测试备份校验和"""
        checksum_config = self.config["checksum_validation"]
        results = {}
        
        for backup_type, config in checksum_config.items():
            backup_path = Path(config["path"])
            checksum_file = backup_path / config["checksum_file"]
            
            if not checksum_file.exists():
                results[backup_type] = {
                    "success": False,
                    "error": f"Checksum file not found: {checksum_file}"
                }
                continue
                
            # 读取校验和文件
            checksums = {}
            with open(checksum_file, 'r') as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            checksums[parts[1]] = parts[0]
                            
            # 验证文件校验和
            verified_files = []
            failed_files = []
            
            for filename, expected_hash in checksums.items():
                file_path = backup_path / filename
                
                if not file_path.exists():
                    failed_files.append({
                        "file": filename,
                        "error": "File not found"
                    })
                    continue
                    
                # 计算实际校验和
                actual_hash = self._calculate_file_hash(file_path, config["algorithm"])
                
                if actual_hash == expected_hash:
                    verified_files.append(filename)
                else:
                    failed_files.append({
                        "file": filename,
                        "expected": expected_hash,
                        "actual": actual_hash
                    })
                    
            success = len(failed_files) == 0
            
            results[backup_type] = {
                "success": success,
                "verified_files": len(verified_files),
                "failed_files": len(failed_files),
                "failed_details": failed_files[:10]  # 限制输出
            }
            
        overall_success = all(r["success"] for r in results.values())
        
        return {
            "success": overall_success,
            "details": results,
            "timestamp": datetime.now().isoformat()
        }
        
    def _calculate_file_hash(self, file_path: Path, algorithm: str = "sha256") -> str:
        """计算文件哈希值"""
        hash_func = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
                
        return hash_func.hexdigest()
        
    def _find_latest_backup(self, backup_type: str) -> Dict:
        """查找最新备份"""
        # 简化的查找逻辑
        backup_config = self.config["backup_locations"].get(backup_type, {})
        if not backup_config:
            return None
            
        backup_path = Path(backup_config["path"])
        pattern = backup_config.get("pattern", "*")
        
        backups = list(backup_path.glob(pattern))
        if not backups:
            return None
            
        latest_backup = max(backups, key=lambda x: x.stat().st_mtime)
        
        return {
            "path": str(latest_backup),
            "timestamp": latest_backup.stat().st_mtime
        }

def main():
    """主函数"""
    config_path = sys.argv[1] if len(sys.argv) > 1 else "/etc/rangen/backup/integrity_config.yaml"
    
    tester = BackupIntegrityTester(config_path)
    results = tester.run_all_tests()
    
    # 输出结果
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    # 发送告警（如果有失败）
    if not results["overall_success"]:
        failed_tests = [name for name, result in results["results"].items() if not result["success"]]
        
        # 发送告警
        import subprocess
        subprocess.run([
            "python", "/opt/rangen/scripts/send_alert.py",
            "--severity", "warning",
            "--message", f"备份完整性测试失败: {', '.join(failed_tests)}",
            "--component", "backup_integrity",
            "--action", "investigate"
        ])
        
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### 恢复演练脚本

```bash
#!/bin/bash
# scripts/run_recovery_drill.sh

set -euo pipefail

# 配置参数
DRILL_TYPE=${1:-"basic"}
DRILL_SCOPE=${2:-"database"}
ENVIRONMENT=${3:-"staging"}
REPORT_DIR="/var/log/rangen/dr_drills"

# 创建报告目录
mkdir -p "$REPORT_DIR"
DRILL_ID="drill_$(date +%Y%m%d_%H%M%S)_${DRILL_TYPE}_${DRILL_SCOPE}"
REPORT_FILE="$REPORT_DIR/${DRILL_ID}.json"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$REPORT_FILE.log"
}

# 开始演练
log "开始恢复演练: ID=$DRILL_ID, 类型=$DRILL_TYPE, 范围=$DRILL_SCOPE, 环境=$ENVIRONMENT"

# 演练步骤
case "$DRILL_TYPE" in
    "basic")
        log "执行基础恢复演练..."
        # 1. 验证备份
        python /opt/rangen/scripts/verify_backups.py \
            --scope "$DRILL_SCOPE" \
            --environment "$ENVIRONMENT" \
            --output "$REPORT_DIR/verify_${DRILL_ID}.json"
            
        # 2. 测试恢复
        python /opt/rangen/scripts/test_recovery.py \
            --scope "$DRILL_SCOPE" \
            --environment "$ENVIRONMENT" \
            --mode "validation" \
            --output "$REPORT_DIR/recovery_${DRILL_ID}.json"
        ;;
        
    "advanced")
        log "执行高级恢复演练..."
        # 1. 模拟故障
        python /opt/rangen/scripts/simulate_failure.py \
            --type "$DRILL_SCOPE" \
            --environment "$ENVIRONMENT"
            
        # 2. 执行恢复
        python /opt/rangen/scripts/execute_recovery.py \
            --scope "$DRILL_SCOPE" \
            --environment "$ENVIRONMENT" \
            --mode "full" \
            --timeout 3600
            
        # 3. 验证恢复
        python /opt/rangen/scripts/verify_recovery.py \
            --scope "$DRILL_SCOPE" \
            --environment "$ENVIRONMENT" \
            --criteria "all"
        ;;
        
    "disaster")
        log "执行灾难恢复演练..."
        # 1. 启动灾备环境
        python /opt/rangen/scripts/activate_dr_site.py \
            --environment "$ENVIRONMENT" \
            --full-activation
        
        # 2. 恢复关键业务
        python /opt/rangen/scripts/recover_critical_services.py \
            --priority "P0,P1" \
            --timeout 7200
            
        # 3. 业务验证
        python /opt/rangen/scripts/validate_business_continuity.py \
            --services "all" \
            --duration 3600
        ;;
        
    *)
        log "未知演练类型: $DRILL_TYPE"
        exit 1
        ;;
esac

# 生成演练报告
log "生成演练报告..."
python /opt/rangen/scripts/generate_drill_report.py \
    --drill-id "$DRILL_ID" \
    --type "$DRILL_TYPE" \
    --scope "$DRILL_SCOPE" \
    --environment "$ENVIRONMENT" \
    --output "$REPORT_FILE"

# 发送通知
log "发送演练完成通知..."
python /opt/rangen/scripts/send_notification.py \
    --title "恢复演练完成: $DRILL_ID" \
    --message "类型: $DRILL_TYPE\n范围: $DRILL_SCOPE\n环境: $ENVIRONMENT\n报告: $REPORT_FILE" \
    --level "info" \
    --attachments "$REPORT_FILE"

log "恢复演练完成: $DRILL_ID"
exit 0
```

### 测试自动化流水线

```yaml
# .github/workflows/backup-recovery-tests.yml
name: Backup Recovery Tests

on:
  schedule:
    # 每天凌晨3点运行
    - cron: '0 3 * * *'
    
  # 手动触发
  workflow_dispatch:
    inputs:
      test_type:
        description: '测试类型'
        required: true
        default: 'all'
        type: choice
        options:
        - all
        - integrity
        - recovery
        - performance
      environment:
        description: '测试环境'
        required: true
        default: 'staging'
        type: choice
        options:
        - dev
        - staging
        - dr

jobs:
  backup-integrity-tests:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment || 'staging' }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-backup.txt
        
    - name: Run backup integrity tests
      run: |
        python scripts/test_backup_integrity.py \
          --config config/backup/integrity_config.yaml \
          --output test-results/integrity.json
          
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: backup-integrity-results
        path: test-results/integrity.json
        
  recovery-tests:
    runs-on: ubuntu-latest
    needs: backup-integrity-tests
    environment: ${{ github.event.inputs.environment || 'staging' }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Setup test environment
      run: |
        python scripts/setup_test_environment.py \
          --environment ${{ github.event.inputs.environment || 'staging' }}
          
    - name: Run recovery tests
      run: |
        python scripts/test_recovery.py \
          --type ${{ github.event.inputs.test_type || 'all' }} \
          --environment ${{ github.event.inputs.environment || 'staging' }} \
          --output test-results/recovery.json
          
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: recovery-test-results
        path: test-results/recovery.json
        
  performance-benchmarks:
    runs-on: ubuntu-latest
    needs: recovery-tests
    environment: ${{ github.event.inputs.environment || 'staging' }}
    
    steps:
    - name: Run performance benchmarks
      run: |
        python scripts/benchmark_recovery_performance.py \
          --scenarios "full,partial,point_in_time" \
          --iterations 3 \
          --output test-results/performance.json
          
    - name: Upload benchmark results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: performance-benchmark-results
        path: test-results/performance.json
        
  generate-report:
    runs-on: ubuntu-latest
    needs: [backup-integrity-tests, recovery-tests, performance-benchmarks]
    
    steps:
    - name: Download all test results
      uses: actions/download-artifact@v3
      
    - name: Generate comprehensive report
      run: |
        python scripts/generate_test_report.py \
          --integrity backup-integrity-results/integrity.json \
          --recovery recovery-test-results/recovery.json \
          --performance performance-benchmark-results/performance.json \
          --output test-report-$(date +%Y%m%d).html
          
    - name: Upload test report
      uses: actions/upload-artifact@v3
      with:
        name: test-report
        path: test-report-*.html
        
    - name: Send notification
      if: always()
      run: |
        python scripts/send_test_notification.py \
          --report test-report-*.html \
          --workflow-run-url https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

---

## 📊 监控与告警

有效的备份恢复策略需要全面的监控和及时的告警机制。

### 监控指标

```yaml
# config/monitoring/backup_metrics.yaml
backup_metrics:
  # 备份成功率指标
  success_rate:
    - name: "backup_success_rate"
      description: "备份成功率"
      type: "gauge"
      labels: ["backup_type", "component", "environment"]
      alert_threshold: 0.95
      
    - name: "backup_duration_seconds"
      description: "备份持续时间"
      type: "histogram"
      buckets: [30, 60, 120, 300, 600]
      labels: ["backup_type", "component"]
      
  # 备份完整性指标
  integrity:
    - name: "backup_integrity_score"
      description: "备份完整性评分"
      type: "gauge"
      range: [0, 1]
      alert_threshold: 0.9
      
    - name: "backup_checksum_errors"
      description: "备份校验和错误数"
      type: "counter"
      labels: ["component", "backup_type"]
      
  # 恢复相关指标
  recovery:
    - name: "recovery_success_rate"
      description: "恢复成功率"
      type: "gauge"
      alert_threshold: 0.98
      
    - name: "recovery_time_objective_seconds"
      description: "恢复时间目标(RTO)"
      type: "gauge"
      labels: ["recovery_type", "component"]
      
    - name: "recovery_point_objective_seconds"
      description: "恢复点目标(RPO)"
      type: "gauge"
      labels: ["component"]
      
  # 存储相关指标
  storage:
    - name: "backup_storage_usage_bytes"
      description: "备份存储使用量"
      type: "gauge"
      labels: ["storage_type", "component"]
      
    - name: "backup_retention_days_remaining"
      description: "备份保留剩余天数"
      type: "gauge"
      labels: ["backup_type"]
      alert_threshold: 7
```

### 告警规则

```yaml
# config/alerts/backup_alerts.yaml
backup_alerts:
  critical:
    - alert: "BackupFailed"
      expr: "rate(backup_failures_total[5m]) > 0"
      for: "5m"
      labels:
        severity: "critical"
        component: "backup"
      annotations:
        summary: "备份失败"
        description: "{{ $labels.component }}的备份在5分钟内失败{{ $value }}次"
        runbook: "https://docs.rangen.ai/runbooks/backup-failure"
        
    - alert: "BackupStorageFull"
      expr: "backup_storage_usage_bytes / backup_storage_capacity_bytes > 0.9"
      for: "10m"
      labels:
        severity: "critical"
        component: "storage"
      annotations:
        summary: "备份存储即将满"
        description: "{{ $labels.storage_type }}存储使用率超过90%"
        runbook: "https://docs.rangen.ai/runbooks/storage-cleanup"
        
  warning:
    - alert: "BackupSuccessRateLow"
      expr: "backup_success_rate < 0.95"
      for: "1h"
      labels:
        severity: "warning"
        component: "backup"
      annotations:
        summary: "备份成功率低"
        description: "{{ $labels.component }}的备份成功率低于95%"
        runbook: "https://docs.rangen.ai/runbooks/backup-optimization"
        
    - alert: "BackupAgeExceeded"
      expr: "time() - backup_last_success_timestamp > 86400"
      for: "30m"
      labels:
        severity: "warning"
        component: "backup"
      annotations:
        summary: "备份过期"
        description: "{{ $labels.component }}的备份已超过24小时未更新"
        runbook: "https://docs.rangen.ai/runbooks/backup-schedule"
        
    - alert: "RecoveryTestMissing"
      expr: "time() - recovery_last_test_timestamp > 604800"
      for: "1h"
      labels:
        severity: "warning"
        component: "recovery"
      annotations:
        summary: "恢复测试缺失"
        description: "{{ $labels.component }}已超过7天未进行恢复测试"
        runbook: "https://docs.rangen.ai/runbooks/recovery-testing"
```

### 监控仪表板

备份恢复监控仪表板应包含以下关键面板：

1. **概览面板**：显示整体备份健康状况
2. **成功率面板**：按组件显示备份成功率和趋势
3. **性能面板**：显示备份和恢复的性能指标
4. **存储面板**：显示备份存储使用情况和趋势
5. **告警面板**：显示当前活跃的备份相关告警
6. **恢复测试面板**：显示恢复测试结果和历史

```json
{
  "dashboard": {
    "title": "RANGEN备份恢复监控",
    "panels": [
      {
        "title": "备份成功率",
        "type": "stat",
        "targets": [
          {
            "expr": "avg(backup_success_rate) by (component)",
            "legendFormat": "{{component}}"
          }
        ],
        "thresholds": {
          "steps": [
            {"color": "red", "value": null},
            {"color": "orange", "value": 0.95},
            {"color": "green", "value": 0.99}
          ]
        }
      },
      {
        "title": "备份存储使用率",
        "type": "gauge",
        "targets": [
          {
            "expr": "backup_storage_usage_bytes / backup_storage_capacity_bytes",
            "legendFormat": "使用率"
          }
        ],
        "thresholds": {
          "steps": [
            {"color": "green", "value": null},
            {"color": "orange", "value": 0.7},
            {"color": "red", "value": 0.9}
          ]
        }
      }
    ]
  }
}
```





# 停止数据库服务
log "停止PostgreSQL服务..."
systemctl stop postgresql-14 || error_exit "停止数据库服务失败"

# 根据恢复类型选择恢复策略
case "$RESTORE_TYPE" in
    "latest")
        log "恢复最新备份..."
        LATEST_BACKUP=$(find /mnt/backup/postgresql -name "postgresql_full_*" -type d | sort -r | head -1)
        if [ -z "$LATEST_BACKUP" ]; then
            error_exit "未找到可用的备份"
        fi
        BACKUP_PATH="$LATEST_BACKUP"
        ;;
        
    "point_in_time")
        if [ -z "$TARGET_TIME" ]; then
            error_exit "时间点恢复需要指定目标时间"
        fi
        log "恢复时间点: $TARGET_TIME"
        # 查找最近的完整备份
        BASE_BACKUP=$(find /mnt/backup/postgresql -name "postgresql_full_*" -type d -newermt "$(date -d "$TARGET_TIME -1 day" '+%Y%m%d')" | sort | head -1)
        if [ -z "$BASE_BACKUP" ]; then
            error_exit "未找到合适的基础备份"
        fi
        BACKUP_PATH="$BASE_BACKUP"
        ;;
        
    "specific")
        if [ -z "$TARGET_TIME" ]; then
            error_exit "指定备份恢复需要提供备份名称"
        fi
        BACKUP_PATH="/mnt/backup/postgresql/$TARGET_TIME"
        if [ ! -d "$BACKUP_PATH" ]; then
            error_exit "备份不存在: $BACKUP_PATH"
        fi
        ;;
        
    *)
        error_exit "不支持的恢复类型: $RESTORE_TYPE"
        ;;
esac

log "使用备份: $BACKUP_PATH"

# 清理数据目录
log "清理数据目录..."
rm -rf /var/lib/postgresql/14/main/*
rm -rf /var/lib/postgresql/14/main/.*

# 恢复基础备份
log "恢复基础备份..."
if [ -f "$BACKUP_PATH/full_backup.sql.gz" ]; then
    # 解压并恢复
    gunzip -c "$BACKUP_PATH/full_backup.sql.gz" | psql -U postgres -d postgres 2>> "$LOG_FILE" || error_exit "恢复基础备份失败"
elif [ -d "$BACKUP_PATH/base" ]; then
    # 使用pg_basebackup恢复
    cp -r "$BACKUP_PATH/base"/* /var/lib/postgresql/14/main/
else
    error_exit "备份格式不支持"
fi

# 配置恢复参数
log "配置恢复参数..."
cat > /var/lib/postgresql/14/main/recovery.conf << EOF
restore_command = 'cp /mnt/wal_archive/%f %p'
recovery_target_timeline = 'latest'
EOF

if [ "$RESTORE_TYPE" = "point_in_time" ] && [ -n "$TARGET_TIME" ]; then
    echo "recovery_target_time = '$TARGET_TIME'" >> /var/lib/postgresql/14/main/recovery.conf
fi

# 启动数据库服务
log "启动PostgreSQL服务..."
systemctl start postgresql-14 || error_exit "启动数据库服务失败"

# 等待恢复完成
log "等待恢复完成..."
sleep 30

# 检查恢复状态
RECOVERY_STATUS=$(psql -U postgres -t -c "SELECT pg_is_in_recovery();" 2>/dev/null || echo "t")
if [ "$RECOVERY_STATUS" = "t" ]; then
    log "数据库仍在恢复中，等待完成..."
    # 等待恢复完成
    while true; do
        RECOVERY_STATUS=$(psql -U postgres -t -c "SELECT pg_is_in_recovery();" 2>/dev/null || echo "t")
        if [ "$RECOVERY_STATUS" = "f" ]; then
            break
        fi
        sleep 10
        log "恢复进行中..."
    done
fi

# 验证数据完整性
log "验证数据完整性..."
python /opt/rangen/scripts/verify_database.py \
    --database "$DATABASE_NAME" \
    --checksum-file "$BACKUP_PATH/checksums.txt" \
    --log "$LOG_FILE" || error_exit "数据完整性验证失败"

# 执行健康检查
log "执行数据库健康检查..."
psql -U postgres -d "$DATABASE_NAME" -c "SELECT 1;" >/dev/null 2>&1 || error_exit "数据库健康检查失败"

# 清理恢复目录
log "清理临时文件..."
rm -rf "$RESTORE_DIR"

# 记录恢复完成
log "PostgreSQL恢复完成: 备份=$BACKUP_PATH, 类型=$RESTORE_TYPE, 耗时=${SECONDS}秒"

# 发送恢复成功通知
python /opt/rangen/scripts/send_notification.py \
    --title "PostgreSQL恢复成功" \
    --message "恢复类型: $RESTORE_TYPE\n备份路径: $BACKUP_PATH\n耗时: ${SECONDS}秒" \
    --level "info"

exit 0
```

### 向量数据库恢复流程

```python
# scripts/recover_chromadb.py
#!/usr/bin/env python3
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import chromadb
from chromadb.config import Settings
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromaDBRecovery:
    def __init__(self, config_path: str = "/etc/rangen/backup/chromadb_config.yaml"):
        self.config = self._load_config(config_path)
        self.client = self._initialize_chromadb_client()
        self.s3_client = boto3.client('s3') if self.config.get('s3', {}).get('enabled') else None
        
    def _load_config(self, config_path: str) -> Dict:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
            
    def _initialize_chromadb_client(self):
        settings = Settings(
            chroma_api_impl="rest",
            chroma_server_host=self.config['chromadb']['host'],
            chroma_server_http_port=self.config['chromadb']['port'],
            chroma_server_ssl=self.config['chromadb'].get('ssl', False)
        )
        return chromadb.Client(settings)
        
    async def recover_collection(self, collection_name: str, backup_path: Optional[str] = None, 
                                backup_date: Optional[str] = None, source: str = "local"):
        """恢复集合"""
        logger.info(f"开始恢复集合: {collection_name}")
        
        try:
            # 1. 查找备份
            backup_info = await self._find_backup(collection_name, backup_path, backup_date, source)
            if not backup_info:
                raise ValueError(f"未找到符合条件的备份: {collection_name}")
                
            logger.info(f"使用备份: {backup_info['path']}")
            
            # 2. 下载备份（如果需要）
            backup_data = await self._download_backup(backup_info, source)
            
            # 3. 删除现有集合（如果存在）
            existing_collections = self.client.list_collections()
            if collection_name in [c.name for c in existing_collections]:
                logger.warning(f"集合已存在, 删除: {collection_name}")
                self.client.delete_collection(collection_name)
                
            # 4. 创建新集合
            collection = self.client.create_collection(collection_name)
            
            # 5. 恢复数据
            documents = backup_data.get('documents', [])
            metadatas = backup_data.get('metadatas', [])
            ids = backup_data.get('ids', [])
            
            if documents:
                collection.add(
                    documents=documents,
                    metadatas=metadatas if metadatas else None,
                    ids=ids if ids else None
                )
                
            # 6. 验证恢复
            count = collection.count()
            logger.info(f"恢复完成: {collection_name}, 文档数量: {count}")
            
            return {
                "success": True,
                "collection": collection_name,
                "document_count": count,
                "backup_path": backup_info['path'],
                "recovery_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"恢复集合失败: {collection_name}, 错误: {e}")
            return {
                "success": False,
                "collection": collection_name,
                "error": str(e),
                "recovery_time": datetime.now().isoformat()
            }
            
    async def _find_backup(self, collection_name: str, backup_path: Optional[str], 
                          backup_date: Optional[str], source: str) -> Optional[Dict]:
        """查找备份"""
        if backup_path:
            return {"path": backup_path, "type": "specific"}
            
        if source == "local":
            base_path = Path(self.config['storage']['local']['path']) / collection_name
            
            if backup_date:
                # 查找指定日期的备份
                backup_dir = base_path / "full" / backup_date
                if backup_dir.exists():
                    return {"path": str(backup_dir), "type": "full", "date": backup_date}
                    
                # 查找最近的完整备份
                full_backups = list((base_path / "full").glob("*"))
                if full_backups:
                    latest = max(full_backups, key=lambda x: x.stat().st_mtime)
                    return {"path": str(latest), "type": "full", "date": latest.name}
            else:
                # 查找最新备份
                for backup_type in ["full", "incremental", "snapshot"]:
                    type_path = base_path / backup_type
                    if type_path.exists():
                        backups = list(type_path.glob("*"))
                        if backups:
                            latest = max(backups, key=lambda x: x.stat().st_mtime)
                            return {"path": str(latest), "type": backup_type, "date": latest.name}
                            
        elif source == "s3" and self.s3_client:
            bucket = self.config['s3']['bucket']
            prefix = f"chromadb/{collection_name}/"
            
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=bucket,
                    Prefix=prefix,
                    Delimiter='/'
                )
                
                if 'CommonPrefixes' in response:
                    prefixes = [p['Prefix'] for p in response['CommonPrefixes']]
                    if prefixes:
                        if backup_date:
                            matching = [p for p in prefixes if backup_date in p]
                            if matching:
                                return {"path": matching[0], "type": "s3", "date": backup_date}
                        else:
                            # 取最新的前缀
                            latest = sorted(prefixes)[-1]
                            return {"path": latest, "type": "s3", "date": latest.split('/')[-2]}
            except ClientError as e:
                logger.error(f"查找S3备份失败: {e}")
                
        return None
        
    async def _download_backup(self, backup_info: Dict, source: str) -> Dict:
        """下载备份"""
        if source == "local":
            backup_path = Path(backup_info['path'])
            data_file = backup_path / "data.json"
            
            if data_file.exists():
                with open(data_file, 'r') as f:
                    return json.load(f)
                    
        elif source == "s3" and self.s3_client:
            import tempfile
            
            bucket = self.config['s3']['bucket']
            key = backup_info['path'] + "data.json"
            
            try:
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
                    self.s3_client.download_file(bucket, key, tmp.name)
                    
                    with open(tmp.name, 'r') as f:
                        data = json.load(f)
                        
                    # 清理临时文件
                    import os
                    os.unlink(tmp.name)
                    
                    return data
                    
            except ClientError as e:
                logger.error(f"下载S3备份失败: {e}")
                raise
                
        raise ValueError(f"无法下载备份: {backup_info['path']}")

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ChromaDB恢复工具')
    parser.add_argument('--collection', type=str, required=True, help='要恢复的集合名称')
    parser.add_argument('--backup-path', type=str, help='备份路径')
    parser.add_argument('--backup-date', type=str, help='备份日期 (YYYYMMDD)')
    parser.add_argument('--source', type=str, default='local', choices=['local', 's3'],
                       help='备份来源')
    parser.add_argument('--config', type=str, 
                       default='/etc/rangen/backup/chromadb_config.yaml',
                       help='配置文件路径')
    
    args = parser.parse_args()
    
    # 创建恢复实例
    recovery = ChromaDBRecovery(args.config)
    
    # 执行恢复
    result = await recovery.recover_collection(
        args.collection, 
        args.backup_path, 
        args.backup_date,
        args.source
    )
    
    # 输出结果
    if result['success']:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```