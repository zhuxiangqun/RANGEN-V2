# 🏗️ 高可用配置指南

本文档详细介绍了如何为RANGEN系统配置高可用（High Availability, HA）架构，确保系统在组件故障时仍能持续提供服务。

## 📋 目录

- [架构概述](#架构概述)
- [部署模式](#部署模式)
- [负载均衡配置](#负载均衡配置)
- [数据高可用](#数据高可用)
- [故障转移策略](#故障转移策略)
- [监控与告警](#监控与告警)
- [性能考虑](#性能考虑)
- [安全考虑](#安全考虑)
- [成本估算](#成本估算)
- [部署步骤](#部署步骤)

---

## 🏗️ 架构概述

### 设计原则

RANGEN高可用架构遵循以下核心原则：

1. **冗余性**：关键组件都有冗余备份
2. **隔离性**：故障域隔离，避免单点故障
3. **自动恢复**：故障自动检测和恢复
4. **数据一致性**：确保数据在多个副本间一致
5. **渐进式升级**：支持无停机升级和维护

### 高可用架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     负载均衡层 (Load Balancer)               │
│                    ┌─────────────┐                         │
│                    │  Nginx/HAProxy  │                         │
│                    │  或云负载均衡器  │                         │
│                    └─────────────┘                         │
│                              │                              │
│        ┌─────────────────────┼─────────────────────┐        │
│        │                     │                     │        │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐  │
│  │  应用服务器  │      │  应用服务器  │      │  应用服务器  │  │
│  │   节点 A     │      │   节点 B     │      │   节点 C     │  │
│  │  (Active)   │      │  (Hot Standby)│      │  (Hot Standby)│  │
│  └─────────────┘      └─────────────┘      └─────────────┘  │
│        │                     │                     │        │
│  ┌─────┴─────┐        ┌─────┴─────┐        ┌─────┴─────┐  │
│  │  本地缓存  │        │  本地缓存  │        │  本地缓存  │  │
│  │  Redis    │        │  Redis    │        │  Redis    │  │
│  └─────┬─────┘        └─────┬─────┘        └─────┬─────┘  │
│        │                     │                     │        │
│        └─────────────────────┼─────────────────────┘        │
│                              │                              │
│                    ┌─────────┴─────────┐                    │
│                    │   共享存储层        │                    │
│                    │  ┌─────────────┐  │                    │
│                    │  │  数据库集群  │  │                    │
│                    │  │  (主从复制)  │  │                    │
│                    │  └─────────────┘  │                    │
│                    │  ┌─────────────┐  │                    │
│                    │  │  向量数据库  │  │                    │
│                    │  │  (副本集)    │  │                    │
│                    │  └─────────────┘  │                    │
│                    │  ┌─────────────┐  │                    │
│                    │  │  对象存储    │  │                    │
│                    │  │  (S3兼容)    │  │                    │
│                    │  └─────────────┘  │                    │
│                    └───────────────────┘                    │
│                              │                              │
│                    ┌─────────┴─────────┐                    │
│                    │   监控与告警层      │                    │
│                    │  ┌─────────────┐  │                    │
│                    │  │  Prometheus │  │                    │
│                    │  └─────────────┘  │                    │
│                    │  ┌─────────────┐  │                    │
│                    │  │   Grafana   │  │                    │
│                    │  └─────────────┘  │                    │
│                    │  ┌─────────────┐  │                    │
│                    │  │   Alertmanager│  │                    │
│                    │  └─────────────┐  │                    │
│                    └───────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### 组件说明

| 组件 | 高可用方案 | 故障恢复时间目标 (RTO) | 数据恢复点目标 (RPO) |
|------|-----------|----------------------|-------------------|
| 应用服务器 | 多实例负载均衡 | < 30秒 | 0 (无状态) |
| 数据库 | 主从复制 + 自动故障转移 | < 60秒 | < 1秒 |
| 向量数据库 | 副本集 | < 90秒 | < 5秒 |
| 缓存 | Redis Sentinel/Cluster | < 10秒 | 0-5分钟(可配置) |
| 负载均衡器 | 主备模式 | < 10秒 | 不适用 |
| 监控系统 | 冗余部署 | < 5分钟 | 不适用 |

---

## 🚀 部署模式

### 模式1：基础高可用 (2节点)

适合中小型部署，提供基本的故障转移能力。

**架构特点**：
- 2个应用服务器节点（主备模式）
- 数据库主从复制
- 共享存储
- 基础负载均衡

**配置示例**：
```yaml
# config/ha-basic.yaml
high_availability:
  mode: "basic"
  nodes:
    - name: "node-a"
      role: "primary"
      ip: "10.0.1.10"
      weight: 100
      
    - name: "node-b" 
      role: "standby"
      ip: "10.0.1.11"
      weight: 0  # 平时不接收流量
      
  database:
    type: "postgresql"
    primary: "db-primary:5432"
    replicas:
      - "db-replica:5432"
      
  load_balancer:
    type: "nginx"
    health_check:
      interval: "10s"
      timeout: "5s"
      fail_threshold: 3
      pass_threshold: 2
```

### 模式2：生产级高可用 (3+节点)

适合生产环境，提供全面的高可用保障。

**架构特点**：
- 3个或以上应用服务器节点（多活模式）
- 数据库集群（如PostgreSQL Patroni、MySQL Group Replication）
- 分布式缓存（Redis Cluster）
- 多可用区部署
- 自动故障转移和恢复

**配置示例**：
```yaml
# config/ha-production.yaml
high_availability:
  mode: "production"
  nodes:
    - name: "node-1"
      role: "active"
      zone: "zone-a"
      ip: "10.0.1.10"
      weight: 50
      
    - name: "node-2"
      role: "active" 
      zone: "zone-b"
      ip: "10.0.1.11"
      weight: 50
      
    - name: "node-3"
      role: "active"
      zone: "zone-c"
      ip: "10.0.1.12"
      weight: 50
      
  database:
    type: "postgresql-patroni"
    cluster_name: "rangen-db-cluster"
    nodes:
      - "db-1:5432"
      - "db-2:5432"
      - "db-3:5432"
    synchronous_replication: true
    max_lag: 1048576  # 1MB
    
  cache:
    type: "redis-cluster"
    nodes:
      - "redis-1:6379"
      - "redis-2:6379"
      - "redis-3:6379"
      - "redis-4:6379"
      - "redis-5:6379"
      - "redis-6:6379"
```

### 模式3：云原生高可用 (Kubernetes)

适合云原生环境，利用Kubernetes原生高可用特性。

**架构特点**：
- Kubernetes部署（StatefulSet + Deployment）
- 服务网格（如Istio）流量管理
- 自动扩缩容（HPA）
- 基于Pod Disruption Budget的优雅驱逐
- 多集群联邦

**配置示例**：
```yaml
# k8s/rangen-ha.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rangen-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rangen-api
  template:
    metadata:
      labels:
        app: rangen-api
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - rangen-api
            topologyKey: kubernetes.io/hostname
      containers:
      - name: rangen-api
        image: rangen/rangen-api:latest
        ports:
        - containerPort: 8000
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: rangen-api
spec:
  selector:
    app: rangen-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rangen-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rangen-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## ⚖️ 负载均衡配置

### Nginx配置示例

```nginx
# nginx/rangen-ha.conf
upstream rangen_backend {
    # 最少连接负载均衡
    least_conn;
    
    # 健康检查配置
    server 10.0.1.10:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8000 max_fails=3 fail_timeout=30s;
    
    # 会话保持（可选）
    sticky cookie srv_id expires=1h domain=.rangen.ai path=/;
    
    # 备份服务器
    server 10.0.1.13:8000 backup;
}

server {
    listen 80;
    server_name rangen.ai;
    
    # 连接限制
    limit_conn_zone $binary_remote_addr zone=addr:10m;
    limit_conn addr 100;
    
    location / {
        proxy_pass http://rangen_backend;
        
        # 代理设置
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
        
        # 重试逻辑
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        proxy_next_upstream_tries 3;
        proxy_next_upstream_timeout 10s;
    }
    
    # 健康检查端点
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # 状态页面
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 10.0.0.0/8;
        deny all;
    }
}
```

### HAProxy配置示例

```haproxy
# haproxy/rangen.cfg
global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon
    maxconn 5000
    
defaults
    log global
    mode http
    option httplog
    option dontlognull
    option http-server-close
    option forwardfor
    timeout connect 10s
    timeout client 30s
    timeout server 30s
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http
    
frontend rangen_frontend
    bind *:80
    mode http
    
    # ACL规则
    acl is_health_check path -i /health
    acl is_api path_beg -i /api/
    
    # 路由规则
    use_backend rangen_health if is_health_check
    default_backend rangen_backend
    
backend rangen_backend
    mode http
    balance roundrobin
    option httpchk GET /health HTTP/1.1\r\nHost:\ rangen.ai
    
    # 服务器定义
    server rangen-1 10.0.1.10:8000 check inter 5s rise 2 fall 3
    server rangen-2 10.0.1.11:8000 check inter 5s rise 2 fall 3
    server rangen-3 10.0.1.12:8000 check inter 5s rise 2 fall 3
    server rangen-backup 10.0.1.13:8000 check inter 5s rise 2 fall 3 backup
    
    # 健康检查配置
    http-check expect status 200
    
backend rangen_health
    mode http
    server local 127.0.0.1:8080
    
listen stats
    bind *:1936
    mode http
    stats enable
    stats hide-version
    stats realm Haproxy\ Statistics
    stats uri /
    stats auth admin:secure_password
```

---

## 💾 数据高可用

### 数据库高可用

#### PostgreSQL Patroni集群

```yaml
# patroni/config.yml
scope: rangen-db-cluster
name: rangen-db-1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 10.0.2.10:8008

etcd:
  hosts:
    - 10.0.2.20:2379
    - 10.0.2.21:2379
    - 10.0.2.22:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      use_slots: true
      parameters:
        wal_level: replica
        hot_standby: "on"
        max_wal_senders: 10
        max_replication_slots: 10
        wal_keep_segments: 32
        max_connections: 100
        shared_buffers: 128MB
        effective_cache_size: 4GB
        
  initdb:
    - encoding: UTF8
    - data-checksums

  pg_hba:
    - host replication replicator 10.0.2.0/24 md5
    - host all all 0.0.0.0/0 md5

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 10.0.2.10:5432
  data_dir: /var/lib/postgresql/14/main
  pgpass: /tmp/pgpass
  authentication:
    replication:
      username: replicator
      password: replication_password
    superuser:
      username: postgres
      password: postgres_password
  parameters:
    unix_socket_directories: '/var/run/postgresql'

tags:
  nofailover: false
  noloadbalance: false
  clonefrom: false
  nosync: false
```

#### 数据库连接配置

```python
# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

class HighAvailabilityDatabase:
    def __init__(self):
        self.primary_url = "postgresql://user:pass@db-primary:5432/rangen"
        self.replica_urls = [
            "postgresql://user:pass@db-replica-1:5432/rangen",
            "postgresql://user:pass@db-replica-2:5432/rangen"
        ]
        
        # 创建主数据库引擎
        self.primary_engine = create_engine(
            self.primary_url,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,  # 连接前ping检查
            pool_recycle=3600,   # 1小时后回收连接
            echo=False
        )
        
        # 创建只读副本引擎
        self.replica_engines = []
        for replica_url in self.replica_urls:
            engine = create_engine(
                replica_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=15,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            self.replica_engines.append(engine)
        
        # 会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.primary_engine
        )
        
        self.Base = declarative_base()
        
    def get_read_session(self):
        """获取只读会话（负载均衡到副本）"""
        import random
        replica_engine = random.choice(self.replica_engines)
        return sessionmaker(bind=replica_engine)()
        
    def get_write_session(self):
        """获取写会话（总是使用主库）"""
        return self.SessionLocal()
        
    def check_health(self):
        """检查数据库健康状态"""
        health_status = {
            "primary": self._check_engine_health(self.primary_engine),
            "replicas": []
        }
        
        for i, engine in enumerate(self.replica_engines):
            health_status["replicas"].append({
                f"replica_{i}": self._check_engine_health(engine)
            })
            
        return health_status
        
    def _check_engine_health(self, engine):
        try:
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                return {"status": "healthy", "latency": "ok"}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
```

### 向量数据库高可用

#### ChromaDB副本集配置

```python
# config/vector_db.py
import chromadb
from chromadb.config import Settings
import logging

logger = logging.getLogger(__name__)

class HighAvailabilityVectorDB:
    def __init__(self):
        # 主节点
        self.primary_client = chromadb.Client(
            Settings(
                chroma_api_impl="rest",
                chroma_server_host="vector-db-primary",
                chroma_server_http_port=8000,
                chroma_server_ssl=False
            )
        )
        
        # 副本节点
        self.replica_clients = [
            chromadb.Client(
                Settings(
                    chroma_api_impl="rest",
                    chroma_server_host="vector-db-replica-1",
                    chroma_server_http_port=8000,
                    chroma_server_ssl=False
                )
            ),
            chromadb.Client(
                Settings(
                    chroma_api_impl="rest",
                    chroma_server_host="vector-db-replica-2",
                    chroma_server_http_port=8000,
                    chroma_server_ssl=False
                )
            )
        ]
        
        # 当前使用的客户端索引
        self.current_replica_index = 0
        
    def get_collection(self, name):
        """获取集合（负载均衡到副本）"""
        try:
            # 尝试使用主节点
            return self.primary_client.get_collection(name)
        except Exception as e:
            logger.warning(f"Primary vector DB failed, trying replica: {e}")
            # 主节点失败，尝试副本
            return self._get_from_replica(name)
            
    def _get_from_replica(self, name):
        """从副本获取集合（轮询）"""
        replica_client = self.replica_clients[self.current_replica_index]
        self.current_replica_index = (self.current_replica_index + 1) % len(self.replica_clients)
        
        try:
            return replica_client.get_collection(name)
        except Exception as e:
            logger.error(f"Replica vector DB failed: {e}")
            # 如果所有副本都失败，尝试下一个副本
            return self._get_from_replica(name)
            
    def add_documents(self, collection_name, documents, metadatas=None, ids=None):
        """添加文档到向量数据库（只写到主节点）"""
        collection = self.primary_client.get_or_create_collection(collection_name)
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        # 异步同步到副本（实际生产环境需要更复杂的同步机制）
        self._async_sync_to_replicas(collection_name, documents, metadatas, ids)
        
    def _async_sync_to_replicas(self, collection_name, documents, metadatas, ids):
        """异步同步到副本"""
        import threading
        
        def sync_to_replica(client):
            try:
                collection = client.get_or_create_collection(collection_name)
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            except Exception as e:
                logger.error(f"Failed to sync to replica: {e}")
                
        # 异步同步到所有副本
        for replica_client in self.replica_clients:
            thread = threading.Thread(target=sync_to_replica, args=(replica_client,))
            thread.daemon = True
            thread.start()
```plica(self, name):
        """从副本获取集合（轮询负载均衡）"""
        replicas_to_try = len(self.replica_clients)
        
        for i in range(replicas_to_try):
            try:
                # 轮询选择副本
                replica_index = (self.current_replica_index + i) % replicas_to_try
                replica = self.replica_clients[replica_index]
                collection = replica.get_collection(name)
                
                # 更新当前索引
                self.current_replica_index = replica_index
                logger.info(f"Successfully connected to replica {replica_index}")
                return collection
                
            except Exception as e:
                logger.warning(f"Replica {replica_index} failed: {e}")
                continue
                
        # 所有副本都失败
        raise Exception(f"All vector database replicas failed for collection: {name}")
        
    def add_documents(self, collection_name, documents, metadata=None, ids=None):
        """添加文档到向量数据库（写入主节点）"""
        try:
            collection = self.primary_client.get_or_create_collection(collection_name)
            result = collection.add(
                documents=documents,
                metadatas=metadata,
                ids=ids
            )
            
            # 异步复制到副本（实际生产环境应有更复杂的复制机制）
            self._async_replicate_to_replicas(collection_name, documents, metadata, ids)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to add documents to vector DB: {e}")
            raise
            
    def _async_replicate_to_replicas(self, collection_name, documents, metadata, ids):
        """异步复制数据到副本"""
        import threading
        
        def replicate_to_replica(replica_client, collection_name, documents, metadata, ids):
            try:
                collection = replica_client.get_or_create_collection(collection_name)
                collection.add(
                    documents=documents,
                    metadatas=metadata,
                    ids=ids
                )
                logger.debug(f"Replicated to replica successfully")
            except Exception as e:
                logger.warning(f"Failed to replicate to replica: {e}")
                
        # 异步复制到所有副本
        for replica_client in self.replica_clients:
            thread = threading.Thread(
                target=replicate_to_replica,
                args=(replica_client, collection_name, documents, metadata, ids)
            )
            thread.daemon = True
            thread.start()
            
    def check_health(self):
        """检查向量数据库健康状态"""
        health_status = {
            "primary": self._check_client_health(self.primary_client),
            "replicas": []
        }
        
        for i, replica in enumerate(self.replica_clients):
            health_status["replicas"].append({
                f"replica_{i}": self._check_client_health(replica)
            })
            
        return health_status
        
    def _check_client_health(self, client):
        try:
            # 尝试列出集合来检查连接
            collections = client.list_collections()
            return {"status": "healthy", "collections": len(collections)}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
```

---

## 🔄 故障转移策略

### 自动故障检测

RANGEN系统实现了多层故障检测机制：

```python
# src/core/fault_detection.py
import time
import logging
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ComponentType(Enum):
    """组件类型枚举"""
    API_SERVER = "api_server"
    DATABASE = "database"
    VECTOR_DB = "vector_db"
    CACHE = "cache"
    MODEL_SERVICE = "model_service"
    LOAD_BALANCER = "load_balancer"

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ComponentHealth:
    """组件健康状态"""
    component_type: ComponentType
    component_id: str
    status: HealthStatus
    last_check: float
    response_time: float
    error_count: int = 0
    details: Optional[Dict] = None

class FaultDetector:
    """故障检测器"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.health_status: Dict[str, ComponentHealth] = {}
        self.failure_thresholds = {
            ComponentType.API_SERVER: 3,      # 3次失败
            ComponentType.DATABASE: 2,        # 2次失败
            ComponentType.VECTOR_DB: 2,       # 2次失败
            ComponentType.CACHE: 3,           # 3次失败
            ComponentType.MODEL_SERVICE: 2,   # 2次失败
            ComponentType.LOAD_BALANCER: 1    # 1次失败
        }
        
    def check_component_health(self, component_type: ComponentType, component_id: str) -> ComponentHealth:
        """检查组件健康状态"""
        start_time = time.time()
        
        try:
            if component_type == ComponentType.API_SERVER:
                status = self._check_api_server(component_id)
            elif component_type == ComponentType.DATABASE:
                status = self._check_database(component_id)
            elif component_type == ComponentType.VECTOR_DB:
                status = self._check_vector_db(component_id)
            elif component_type == ComponentType.CACHE:
                status = self._check_cache(component_id)
            elif component_type == ComponentType.MODEL_SERVICE:
                status = self._check_model_service(component_id)
            elif component_type == ComponentType.LOAD_BALANCER:
                status = self._check_load_balancer(component_id)
            else:
                status = HealthStatus.UNKNOWN
                
            response_time = time.time() - start_time
            
            # 更新健康状态
            health = ComponentHealth(
                component_type=component_type,
                component_id=component_id,
                status=status,
                last_check=start_time,
                response_time=response_time
            )
            
            self.health_status[f"{component_type.value}_{component_id}"] = health
            
            # 检查是否需要触发故障转移
            if status == HealthStatus.UNHEALTHY:
                self._check_failover_condition(component_type, component_id)
                
            return health
            
        except Exception as e:
            logger.error(f"Health check failed for {component_type.value}/{component_id}: {e}")
            
            health = ComponentHealth(
                component_type=component_type,
                component_id=component_id,
                status=HealthStatus.UNHEALTHY,
                last_check=start_time,
                response_time=time.time() - start_time,
                error_count=1,
                details={"error": str(e)}
            )
            
            self.health_status[f"{component_type.value}_{component_id}"] = health
            self._check_failover_condition(component_type, component_id)
            
            return health
    
    def _check_api_server(self, server_id: str) -> HealthStatus:
        """检查API服务器健康状态"""
        import requests
        
        try:
            response = requests.get(f"http://{server_id}/health", timeout=5)
            if response.status_code == 200:
                return HealthStatus.HEALTHY
            elif response.status_code == 503:
                return HealthStatus.DEGRADED
            else:
                return HealthStatus.UNHEALTHY
        except requests.exceptions.Timeout:
            return HealthStatus.UNHEALTHY
        except Exception:
            return HealthStatus.UNHEALTHY
    
    def _check_database(self, db_endpoint: str) -> HealthStatus:
        """检查数据库健康状态"""
        # 简化的数据库检查
        try:
            # 实际实现中会使用数据库客户端进行检查
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNHEALTHY
    
    def _check_failover_condition(self, component_type: ComponentType, component_id: str):
        """检查是否满足故障转移条件"""
        key = f"{component_type.value}_{component_id}"
        
        if key in self.health_status:
            health = self.health_status[key]
            threshold = self.failure_thresholds.get(component_type, 3)
            
            # 如果错误计数达到阈值，触发故障转移
            if health.error_count >= threshold:
                self._trigger_failover(component_type, component_id)
    
    def _trigger_failover(self, component_type: ComponentType, component_id: str):
        """触发故障转移"""
        logger.critical(f"触发故障转移: {component_type.value}/{component_id}")
        
        # 通知故障转移管理器
        from src.services.failover_manager import FailoverManager
        failover_manager = FailoverManager()
        failover_manager.initiate_failover(component_type, component_id)
```

### 智能故障转移决策

```python
# src/services/failover_manager.py
import logging
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

class FailoverStrategy(Enum):
    """故障转移策略枚举"""
    AUTOMATIC = "automatic"      # 自动故障转移
    MANUAL = "manual"           # 手动故障转移
    SEMI_AUTOMATIC = "semi_automatic"  # 半自动故障转移

class FailoverPriority(Enum):
    """故障转移优先级"""
    CRITICAL = "critical"       # 关键组件，立即转移
    HIGH = "high"              # 重要组件，快速转移
    MEDIUM = "medium"          # 一般组件，延迟转移
    LOW = "low"                # 非关键组件，可维护时转移

@dataclass
class FailoverPlan:
    """故障转移计划"""
    component_type: str
    component_id: str
    backup_components: List[str]  # 备用组件列表
    priority: FailoverPriority
    strategy: FailoverStrategy
    estimated_downtime: int  # 预计停机时间（秒）
    data_loss_risk: str      # 数据丢失风险描述

class FailoverManager:
    """故障转移管理器"""
    
    def __init__(self):
        self.failover_plans: Dict[str, FailoverPlan] = {}
        self.failover_history = []
        self.load_balancer_client = None
        self.config_manager = None
        
    def register_failover_plan(self, plan: FailoverPlan):
        """注册故障转移计划"""
        key = f"{plan.component_type}_{plan.component_id}"
        self.failover_plans[key] = plan
        logger.info(f"已注册故障转移计划: {key}")
        
    def initiate_failover(self, component_type: str, component_id: str):
        """发起故障转移"""
        key = f"{component_type}_{component_id}"
        
        if key not in self.failover_plans:
            logger.error(f"未找到故障转移计划: {key}")
            return False
            
        plan = self.failover_plans[key]
        
        logger.info(f"开始执行故障转移: {key}")
        logger.info(f"策略: {plan.strategy.value}, 优先级: {plan.priority.value}")
        
        # 记录故障转移开始
        self.failover_history.append({
            "timestamp": time.time(),
            "component_type": component_type,
            "component_id": component_id,
            "action": "initiate",
            "plan": plan.__dict__
        })
        
        # 根据策略执行故障转移
        if plan.strategy == FailoverStrategy.AUTOMATIC:
            success = self._execute_automatic_failover(plan)
        elif plan.strategy == FailoverStrategy.SEMI_AUTOMATIC:
            success = self._request_manual_approval(plan)
        else:
            success = False
            
        # 记录结果
        self.failover_history.append({
            "timestamp": time.time(),
            "component_type": component_type,
            "component_id": component_id,
            "action": "complete",
            "success": success
        })
        
        return success
    
    def _execute_automatic_failover(self, plan: FailoverPlan) -> bool:
        """执行自动故障转移"""
        try:
            # 1. 健康检查备用组件
            healthy_backups = []
            for backup in plan.backup_components:
                if self._check_component_health(backup):
                    healthy_backups.append(backup)
                    
            if not healthy_backups:
                logger.error("没有可用的健康备用组件")
                return False
                
            # 2. 选择最佳备用组件
            selected_backup = self._select_best_backup(healthy_backups, plan)
            
            # 3. 更新负载均衡配置
            if self.load_balancer_client:
                self.load_balancer_client.update_backend(
                    target=plan.component_id,
                    new_backend=selected_backup,
                    weight=100
                )
                
            # 4. 更新配置中心
            if self.config_manager:
                self.config_manager.update_component_mapping(
                    component_type=plan.component_type,
                    old_id=plan.component_id,
                    new_id=selected_backup
                )
                
            # 5. 发送通知
            self._send_failover_notification(plan, selected_backup)
            
            logger.info(f"故障转移完成: {plan.component_id} -> {selected_backup}")
            return True
            
        except Exception as e:
            logger.error(f"自动故障转移失败: {e}")
            return False
    
    def _select_best_backup(self, backups: List[str], plan: FailoverPlan) -> str:
        """选择最佳备用组件"""
        # 基于以下因素选择：
        # 1. 当前负载
        # 2. 地理位置（如果有多区域部署）
        # 3. 性能指标
        # 4. 历史可靠性
        
        # 简化的选择逻辑：选择第一个健康备用
        return backups[0]
```

---

## 📊 监控与告警

### 多级监控体系

RANGEN系统实现三级监控体系：

```yaml
# config/monitoring/ha-monitoring.yaml
monitoring:
  layers:
    - name: "基础监控"
      components:
        - system_metrics
        - application_metrics
        - database_metrics
      frequency: "30s"
      retention: "7d"
      
    - name: "业务监控"
      components:
        - user_sessions
        - api_throughput
        - error_rates
        - response_times
      frequency: "1m"
      retention: "30d"
      
    - name: "预测性监控"
      components:
        - anomaly_detection
        - capacity_forecasting
        - trend_analysis
      frequency: "5m"
      retention: "90d"

alerting:
  channels:
    - type: "email"
      recipients:
        - "admin@rangen.ai"
        - "ops@rangen.ai"
      priority: "high"
      
    - type: "slack"
      webhook: "https://hooks.slack.com/services/..."
      channel: "#alerts-rangen"
      priority: "medium"
      
    - type: "sms"
      phone_numbers:
        - "+8613800138000"
      priority: "critical"
      
    - type: "webhook"
      url: "https://ops.rangen.ai/api/alerts"
      priority: "all"

  rules:
    - name: "api_server_down"
      condition: "up{job='rangen-api'} == 0"
      duration: "1m"
      severity: "critical"
      summary: "API服务器宕机"
      description: "API服务器 {{ $labels.instance }} 已宕机超过1分钟"
      
    - name: "high_response_time"
      condition: "histogram_quantile(0.95, rate(rangen_api_request_duration_seconds_bucket[5m])) > 2"
      duration: "5m"
      severity: "warning"
      summary: "API响应时间过高"
      description: "API 95分位响应时间超过2秒"
      
    - name: "database_connection_high"
      condition: "pg_stat_database_numbackends{datname='rangen'} > 100"
      duration: "2m"
      severity: "warning"
      summary: "数据库连接数过高"
      description: "数据库连接数超过100"
      
    - name: "memory_usage_high"
      condition: "node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.2"
      duration: "3m"
      severity: "warning"
      summary: "内存使用率过高"
      description: "可用内存低于20%"
```

### 智能告警抑制

```python
# src/monitoring/alert_suppression.py
import time
import logging
from typing import Dict, List, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Alert:
    alert_id: str
    name: str
    severity: AlertSeverity
    instance: str
    summary: str
    description: str
    timestamp: float
    labels: Dict[str, str]

class AlertSuppressionEngine:
    """智能告警抑制引擎"""
    
    def __init__(self):
        self.suppression_rules = self._load_suppression_rules()
        self.alert_history: Dict[str, List[Alert]] = {}
        self.suppressed_alerts: Set[str] = set()
        
    def should_suppress_alert(self, alert: Alert) -> bool:
        """判断是否应该抑制告警"""
        # 1. 检查基于规则的抑制
        if self._check_rule_based_suppression(alert):
            return True
            
        # 2. 检查基于时间的抑制（频繁告警）
        if self._check_time_based_suppression(alert):
            return True
            
        # 3. 检查相关性抑制（相关组件告警）
        if self._check_correlation_suppression(alert):
            return True
            
        return False
    
    def _check_rule_based_suppression(self, alert: Alert) -> bool:
        """基于规则的抑制检查"""
        for rule in self.suppression_rules:
            if self._match_alert_to_rule(alert, rule):
                logger.info(f"告警被规则抑制: {alert.alert_id}, 规则: {rule['name']}")
                return True
        return False
    
    def _check_time_based_suppression(self, alert: Alert) -> bool:
        """基于时间的抑制检查（防止告警风暴）"""
        alert_key = f"{alert.name}_{alert.instance}"
        
        # 获取最近5分钟内的相同告警
        current_time = time.time()
        recent_alerts = []
        
        if alert_key in self.alert_history:
            for historical_alert in self.alert_history[alert_key]:
                if current_time - historical_alert.timestamp < 300:  # 5分钟
                    recent_alerts.append(historical_alert)
        
        # 如果5分钟内已经有3个相同告警，抑制新的告警
        if len(recent_alerts) >= 3:
            logger.info(f"告警被时间抑制: {alert.alert_id}, 5分钟内已有{len(recent_alerts)}个相同告警")
            return True
            
        # 添加到历史记录
        if alert_key not in self.alert_history:
            self.alert_history[alert_key] = []
        self.alert_history[alert_key].append(alert)
        
        # 清理旧的历史记录（保留24小时）
        self._cleanup_alert_history()
        
        return False
        
    def _check_correlation_suppression(self, alert: Alert) -> bool:
        """基于相关性的抑制检查"""
        # 如果底层组件已经告警，抑制上层组件告警
        # 例如：如果数据库宕机，抑制依赖数据库的API告警
        
        correlation_rules = [
            # (底层组件模式, 上层组件模式)
            ("database_.*", "api_.*"),
            ("redis_.*", "cache_.*"),
            ("vector_db_.*", "rag_.*")
        ]
        
        for underlying_pattern, dependent_pattern in correlation_rules:
            import re
            if re.match(dependent_pattern, alert.name):
                # 检查是否有匹配的底层组件告警
                for alert_key, alerts in self.alert_history.items():
                    for historical_alert in alerts:
                        if (re.match(underlying_pattern, historical_alert.name) and 
                            current_time - historical_alert.timestamp < 600):  # 10分钟内
                            logger.info(f"告警被相关性抑制: {alert.alert_id}, 由于底层组件 {historical_alert.name} 已告警")
                            return True
        
        return False
        
    def _match_alert_to_rule(self, alert: Alert, rule: Dict) -> bool:
        """匹配告警到抑制规则"""
        # 简化的规则匹配逻辑
        if "name_pattern" in rule:
            import re
            if not re.match(rule["name_pattern"], alert.name):
                return False
                
        if "severity" in rule:
            if alert.severity.value != rule["severity"]:
                return False
                
        if "instance_pattern" in rule:
            import re
            if not re.match(rule["instance_pattern"], alert.instance):
                return False
                
        return True
        
    def _load_suppression_rules(self) -> List[Dict]:
        """加载抑制规则"""
        return [
            {
                "name": "夜间维护抑制",
                "name_pattern": ".*",
                "time_range": "00:00-06:00",  # 夜间维护时段
                "enabled": True
            },
            {
                "name": "测试环境抑制",
                "instance_pattern": "test-.*",
                "severity": "info",
                "enabled": True
            }
        ]
        
    def _cleanup_alert_history(self):
        """清理告警历史记录"""
        current_time = time.time()
        for alert_key in list(self.alert_history.keys()):
            # 保留24小时内的告警
            self.alert_history[alert_key] = [
                alert for alert in self.alert_history[alert_key]
                if current_time - alert.timestamp < 86400
            ]
            
            # 如果列表为空，删除键
            if not self.alert_history[alert_key]:
                del self.alert_history[alert_key]
```

---

## ⚡ 性能考虑

### 高可用架构的性能影响

实施高可用架构会对系统性能产生一定影响，主要体现在以下几个方面：

| 性能影响维度 | 影响程度 | 优化建议 |
|-------------|---------|---------|
| 网络延迟 | 中-高 | 使用低延迟网络、部署在同一可用区、启用连接池 |
| 数据一致性延迟 | 低-中 | 使用异步复制、最终一致性、读写分离 |
| 资源开销 | 中-高 | 合理配置副本数量、使用资源共享、自动扩缩容 |
| 故障检测延迟 | 低 | 优化健康检查频率、使用多级检测机制 |
| 故障恢复时间 | 中 | 预置备用资源、优化故障转移逻辑 |

### 性能优化策略

#### 1. 连接池优化

```yaml
# config/performance/connection_pools.yaml
connection_pools:
  database:
    max_size: 50
    min_size: 10
    overflow: 20
    timeout: 30s
    recycle: 3600  # 1小时回收
    
  redis:
    max_connections: 100
    min_connections: 20
    timeout: 10s
    
  api_client:
    max_connections_per_host: 100
    keep_alive: 300s
    retries: 3
```

#### 2. 缓存策略优化

```python
# src/core/cache_optimizer.py
import time
import logging
from typing import Any, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class CacheTier(Enum):
    L1 = "l1"  # 内存缓存 (最快, 容量最小)
    L2 = "l2"  # Redis缓存 (较快, 容量中等)
    L3 = "l3"  # 分布式缓存 (较慢, 容量大)

class CacheOptimizer:
    def __init__(self):
        self.cache_hierarchy = {
            CacheTier.L1: {"ttl": 60, "max_items": 1000},      # 1分钟
            CacheTier.L2: {"ttl": 300, "max_items": 10000},    # 5分钟
            CacheTier.L3: {"ttl": 3600, "max_items": 100000}   # 1小时
        }
        
    def get_with_cache(self, key: str, fetch_func, tier: CacheTier = CacheTier.L2) -> Any:
        """智能缓存获取"""
        # 1. 尝试从高层级缓存获取
        for cache_tier in [CacheTier.L1, CacheTier.L2, CacheTier.L3]:
            if cache_tier.value <= tier.value:
                value = self._get_from_tier(key, cache_tier)
                if value is not None:
                    # 缓存命中，更新低层级缓存
                    self._propagate_to_lower_tiers(key, value, cache_tier)
                    return value
        
        # 2. 缓存未命中，从源获取
        value = fetch_func()
        
        # 3. 写入缓存
        self._set_to_tier(key, value, tier)
        
        return value
        
    def _get_from_tier(self, key: str, tier: CacheTier) -> Optional[Any]:
        """从指定层级获取缓存"""
        # 实际实现中会调用对应的缓存客户端
        pass
        
    def _set_to_tier(self, key: str, value: Any, tier: CacheTier):
        """设置缓存到指定层级"""
        pass
        
    def _propagate_to_lower_tiers(self, key: str, value: Any, from_tier: CacheTier):
        """向低层级缓存传播"""
        # 将数据传播到更快的缓存层级
        pass
```

#### 3. 数据库读写分离

```python
# config/database/read_write_splitting.yaml
database:
  read_write_splitting:
    enabled: true
    
    write:
      nodes:
        - "db-primary:5432"
      load_balance: "round_robin"
      
    read:
      nodes:
        - "db-replica-1:5432"
        - "db-replica-2:5432"
        - "db-replica-3:5432"
      load_balance: "least_connections"
      weights:
        - 40  # 副本1权重
        - 30  # 副本2权重
        - 30  # 副本3权重
        
    routing_rules:
      - pattern: "SELECT.*"
        target: "read"
        
      - pattern: "INSERT.*|UPDATE.*|DELETE.*"
        target: "write"
        
      - pattern: ".*FOR UPDATE.*"
        target: "write"
        
    consistency_level: "eventual"  # eventual, strong, causal
```

#### 4. 负载均衡算法优化

```yaml
# config/load_balancer/advanced.yaml
load_balancing:
  algorithms:
    - name: "weighted_least_connections"
      description: "加权最少连接数"
      parameters:
        weight_by_cpu: true
        weight_by_memory: false
        dynamic_weight_adjustment: true
        
    - name: "latency_aware"
      description: "延迟感知"
      parameters:
        latency_window: "5m"
        exclude_outliers: true
        min_samples: 100
        
    - name: "predictive"
      description: "预测性负载均衡"
      parameters:
        forecast_horizon: "15m"
        model_type: "arima"
        update_interval: "1m"
        
  adaptive_routing:
    enabled: true
    metrics:
      - "response_time_p95"
      - "error_rate"
      - "throughput"
    adjustment_interval: "30s"
    max_adjustment: 20  # 最大权重调整百分比
```

### 性能基准测试

为了确保高可用架构的性能满足要求，需要定期进行性能基准测试：

```bash
# 性能基准测试脚本
#!/bin/bash

# 1. 单节点基准测试
python scripts/benchmark_single_node.py \
  --concurrent-users 100 \
  --duration 300 \
  --endpoint "http://node-1:8000"

# 2. 高可用集群基准测试
python scripts/benchmark_ha_cluster.py \
  --concurrent-users 1000 \
  --duration 600 \
  --endpoints "http://node-1:8000,http://node-2:8000,http://node-3:8000" \
  --load-balancer "http://lb.rangen.ai"

# 3. 故障转移性能测试
python scripts/benchmark_failover.py \
  --scenarios "node_failure,network_partition,database_failure" \
  --iterations 10 \
  --metrics "recovery_time,data_loss,throughput_drop"

# 4. 生成性能报告
python scripts/generate_performance_report.py \
  --output "reports/performance/ha_benchmark_$(date +%Y%m%d).html"
```

### 性能监控指标

在高可用架构中，需要监控以下关键性能指标：

```yaml
# config/monitoring/performance_metrics.yaml
performance_metrics:
  # 系统级别指标
  system:
    - "cpu_utilization_percent"
    - "memory_utilization_percent"
    - "disk_io_ops"
    - "network_throughput_bytes"
    
  # 应用级别指标
  application:
    - "request_latency_seconds{p95,p99}"
    - "request_throughput_rps"
    - "error_rate_percent"
    - "concurrent_users"
    
  # 高可用特定指标
  high_availability:
    - "failover_duration_seconds"
    - "replica_lag_seconds"
    - "health_check_success_rate"
    - "load_balancer_efficiency"
    
  # 业务级别指标
  business:
    - "user_session_duration"
    - "api_success_rate"
    - "feature_usage_count"
    - "conversion_rate"
    
  alerting_thresholds:
    critical:
      cpu_utilization: 90
      memory_utilization: 85
      error_rate: 5
      failover_duration: 60  # 秒
      
    warning:
      cpu_utilization: 75
      memory_utilization: 70
      error_rate: 2
      replica_lag: 10  # 秒
```

---

## 🔒 安全考虑

### 高可用架构的安全挑战

实施高可用架构会引入新的安全考虑：

1. **攻击面扩大**：更多的节点意味着更大的攻击面
2. **数据同步安全**：副本间数据同步需要加密
3. **故障转移安全**：故障转移过程可能被恶意利用
4. **配置管理安全**：多节点配置管理复杂度增加
5. **监控数据安全**：监控数据可能包含敏感信息

### 安全加固措施

#### 1. 网络隔离与分段

```yaml
# config/security/network_segmentation.yaml
network_segmentation:
  zones:
    - name: "public_zone"
      cidr: "0.0.0.0/0"
      services: ["load_balancer", "api_gateway"]
      security_groups:
        - allow_http_https
        - deny_all_other
        
    - name: "application_zone"
      cidr: "10.0.1.0/24"
      services: ["api_servers", "background_workers"]
      security_groups:
        - allow_from_public_zone
        - allow_internal_communication
        - deny_external_direct
        
    - name: "data_zone"
      cidr: "10.0.2.0/24"
      services: ["databases", "caches", "vector_dbs"]
      security_groups:
        - allow_from_application_zone
        - deny_all_external
        - encrypt_all_traffic
```

#### 2. 传输层加密

```python
# src/core/security/tls_manager.py
import ssl
import OpenSSL
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class TLSManager:
    def __init__(self):
        self.certificates = {}
        self.ssl_contexts = {}
        
    def configure_tls_for_service(self, service_name: str, config: Dict):
        """为服务配置TLS"""
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
        # 加载证书
        context.load_cert_chain(
            certfile=config["certificate_path"],
            keyfile=config["private_key_path"]
        )
        
        # 配置加密套件
        context.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")
        
        # 启用OCSP装订
        if config.get("enable_ocsp_stapling", True):
            context.set_ocsp_client_callback(self._ocsp_callback)
            
        # 证书轮换配置
        if config.get("enable_certificate_rotation", True):
            self._setup_certificate_rotation(service_name, config)
            
        self.ssl_contexts[service_name] = context
        return context
        
    def _ocsp_callback(self, conn, ocsp_data, user_data):
        """OCSP装订回调"""
        # 验证OCSP响应
        pass
        
    def _setup_certificate_rotation(self, service_name: str, config: Dict):
        """设置证书轮换"""
        rotation_interval = config.get("rotation_interval", 30)  # 天
        
        # 定期检查证书过期时间
        # 在证书过期前自动续期
        pass
```

#### 3. 身份验证与授权

```yaml
# config/security/authentication.yaml
authentication:
  # 服务间认证
  service_to_service:
    method: "mTLS"  # 双向TLS
    certificate_authority: "internal_ca"
    rotation_policy: "30d"
    
  # 节点间认证
  node_authentication:
    method: "ssh_keys"
    authorized_keys_file: "/etc/ssh/authorized_keys_ha"
    key_rotation: "90d"
    
  # API认证
  api_authentication:
    methods:
      - "api_key"
      - "jwt"
      - "oauth2"
    rate_limiting:
      requests_per_minute: 1000
      burst_limit: 2000
      
authorization:
  # 基于角色的访问控制
  rbac:
    enabled: true
    roles:
      - name: "ha_admin"
        permissions: ["failover_trigger", "node_management", "config_update"]
        
      - name: "ha_operator"
        permissions: ["monitoring_view", "log_view", "health_check"]
        
      - name: "ha_viewer"
        permissions: ["dashboard_view", "metrics_view"]
        
  # 基于属性的访问控制
  abac:
    enabled: true
    policies:
      - name: "emergency_failover"
        condition: "time_of_day in ['00:00-06:00'] and maintenance_mode = true"
        action: "allow"
```

#### 4. 安全监控与审计

```python
# src/core/security/security_monitor.py
import time
import logging
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    AUTHENTICATION_FAILURE = "authentication_failure"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    CONFIGURATION_CHANGE = "configuration_change"
    FAILOVER_TRIGGERED = "failover_triggered"
    NETWORK_ANOMALY = "network_anomaly"

@dataclass
class SecurityEvent:
    event_type: SecurityEventType
    timestamp: float
    source: str
    target: str
    severity: str
    details: Dict
    user: str = "system"

class SecurityMonitor:
    def __init__(self):
        self.event_log: List[SecurityEvent] = []
        self.alert_rules = self._load_alert_rules()
        
    def log_security_event(self, event: SecurityEvent):
        """记录安全事件"""
        self.event_log.append(event)
        logger.info(f"安全事件: {event.event_type.value} - {event.source} -> {event.target}")
        
        # 检查是否需要触发告警
        self._check_alert_rules(event)
        
        # 归档旧事件
        self._archive_old_events()
        
    def _check_alert_rules(self, event: SecurityEvent):
        """检查告警规则"""
        for rule in self.alert_rules:
            if self._match_event_to_rule(event, rule):
                self._trigger_alert(event, rule)
                
    def _match_event_to_rule(self, event: SecurityEvent, rule: Dict) -> bool:
        """匹配事件到规则"""
        # 规则匹配逻辑
        pass
        
    def _trigger_alert(self, event: SecurityEvent, rule: Dict):
        """触发告警"""
        alert_message = f"安全告警: {event.event_type.value} - 规则: {rule['name']}"
        logger.warning(alert_message)
        
        # 发送告警通知
        self._send_alert_notification(alert_message, event, rule)
        
    def _send_alert_notification(self, message: str, event: SecurityEvent, rule: Dict):
        """发送告警通知"""
        # 实现通知发送逻辑
        pass
        
    def _load_alert_rules(self) -> List[Dict]:
        """加载告警规则"""
        return [
            {
                "name": "频繁认证失败",
                "event_type": "authentication_failure",
                "threshold": 10,  # 10次/分钟
                "window": 60,     # 60秒窗口
                "severity": "high"
            },
            {
                "name": "非工作时间配置变更",
                "event_type": "configuration_change",
                "time_range": "18:00-08:00",  # 非工作时间
                "severity": "medium"
            }
        ]
```

---

## 💰 成本估算

### 高可用架构成本组成

高可用架构的成本主要包括以下几个部分：

| 成本类别 | 描述 | 估算公式 |
|---------|------|---------|
| 基础设施成本 | 服务器、网络、存储等硬件资源 | (主节点成本 + 副本节点成本) × 节点数量 |
| 软件许可成本 | 商业软件、中间件许可 | 按节点计费或按容量计费 |
| 运维成本 | 监控、备份、维护等人力成本 | (工程师小时费率 × 预估工时) |
| 数据同步成本 | 跨区域数据复制产生的网络费用 | 数据量 × 传输单价 × 复制频率 |
| 故障恢复成本 | 故障期间的业务损失 | (平均每小时收入 × 故障时间) |

### 成本优化策略

#### 1. 混合部署模式

```yaml
# config/cost_optimization/hybrid_deployment.yaml
deployment_strategy:
  mode: "hybrid"
  
  critical_components:
    deployment: "multi_zone"  # 多可用区部署
    replication: "synchronous"  # 同步复制
    nodes: 3
    instance_type: "large"
    
  non_critical_components:
    deployment: "single_zone"  # 单可用区部署
    replication: "asynchronous"  # 异步复制
    nodes: 2
    instance_type: "medium"
    
  cost_saving_features:
    - "spot_instances_for_testing"
    - "reserved_instances_for_production"
    - "auto_scaling_based_on_load"
    - "storage_tiering"
```

#### 2. 自动扩缩容策略

```python
# src/core/cost/auto_scaling_manager.py
import time
import logging
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ScalingMetric(Enum):
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_UTILIZATION = "memory_utilization"
    REQUEST_RATE = "request_rate"
    RESPONSE_TIME = "response_time"
    COST_PER_REQUEST = "cost_per_request"

@dataclass
class ScalingDecision:
    action: str  # "scale_up", "scale_down", "maintain"
    target_count: int
    reason: str
    estimated_cost_impact: float

class AutoScalingManager:
    def __init__(self):
        self.scaling_policies = self._load_scaling_policies()
        self.metrics_history = {}
        
    def make_scaling_decision(self, component: str, current_metrics: Dict) -> ScalingDecision:
        """做出扩缩容决策"""
        policy = self.scaling_policies.get(component)
        if not policy:
            return ScalingDecision("maintain", 0, "No policy found", 0)
            
        # 分析历史指标
        self._update_metrics_history(component, current_metrics)
        
        # 应用扩缩容策略
        decision = self._apply_scaling_policy(component, policy, current_metrics)
        
        # 成本效益分析
        cost_impact = self._calculate_cost_impact(decision, component)
        decision.estimated_cost_impact = cost_impact
        
        return decision
        
    def _apply_scaling_policy(self, component: str, policy: Dict, metrics: Dict) -> ScalingDecision:
        """应用扩缩容策略"""
        current_count = metrics.get("instance_count", 1)
        
        # 检查是否需要扩容
        for metric_name, threshold in policy.get("scale_up_thresholds", {}).items():
            if metrics.get(metric_name, 0) > threshold:
                target_count = min(
                    current_count + policy.get("scale_up_step", 1),
                    policy.get("max_instances", 10)
                )
                return ScalingDecision(
                    "scale_up", 
                    target_count,
                    f"Metric {metric_name} exceeds threshold: {metrics[metric_name]} > {threshold}",
                    0
                )
                
        # 检查是否需要缩容
        for metric_name, threshold in policy.get("scale_down_thresholds", {}).items():
            if metrics.get(metric_name, 0) < threshold:
                target_count = max(
                    current_count - policy.get("scale_down_step", 1),
                    policy.get("min_instances", 1)
                )
                return ScalingDecision(
                    "scale_down",
                    target_count,
                    f"Metric {metric_name} below threshold: {metrics[metric_name]} < {threshold}",
                    0
                )
                
        return ScalingDecision("maintain", current_count, "All metrics within thresholds", 0)
```

#### 3. 成本监控与报告

```bash
# 成本监控脚本
#!/bin/bash

# 生成成本报告
python scripts/generate_cost_report.py \
  --period "monthly" \
  --breakdown "by_service,by_zone,by_instance_type" \
  --output "reports/cost/$(date +%Y%m)_cost_report.pdf"

# 成本优化建议
python scripts/analyze_cost_optimization.py \
  --input "reports/cost/$(date +%Y%m)_cost_report.pdf" \
  --output "reports/cost/optimization_suggestions_$(date +%Y%m%d).md"

# 预算监控
python scripts/monitor_budget.py \
  --budget 10000 \
  --alert-threshold 80 \
  --notification-email "finance@rangen.ai"
```

### 投资回报率(ROI)分析

实施高可用架构的投资回报主要来自以下几个方面：

1. **业务连续性收益**：减少停机时间带来的收入损失
2. **运维效率提升**：自动化运维减少人力成本
3. **客户满意度提升**：稳定服务提升客户忠诚度
4. **合规性收益**：满足行业合规要求避免罚款

ROI计算公式：
```
ROI = (总收益 - 总成本) / 总成本 × 100%

总收益 = ∑(收益项_i × 权重_i)
总成本 = 基础设施成本 + 软件成本 + 运维成本 + 机会成本
```

---

## 🚀 部署步骤

### 部署前准备

#### 1. 环境检查清单

```bash
# 环境检查脚本
#!/bin/bash

echo "=== RANGEN高可用部署环境检查 ==="
echo ""

# 1. 系统要求检查
echo "1. 系统要求检查:"
python -c "import sys; print(f'Python版本: {sys.version}')"
docker --version
kubectl version --client 2>/dev/null || echo "kubectl未安装"

# 2. 网络检查
echo -e "\n2. 网络检查:"
ping -c 3 google.com > /dev/null && echo "外网连接: ✓" || echo "外网连接: ✗"
ping -c 3 10.0.1.10 > /dev/null && echo "内网节点连通性: ✓" || echo "内网节点连通性: ✗"

# 3. 存储检查
echo -e "\n3. 存储检查:"
df -h / | grep -v Filesystem
lsblk 2>/dev/null || echo "块设备信息不可用"

# 4. 安全配置检查
echo -e "\n4. 安全配置检查:"
if [ -f "/etc/ssh/sshd_config" ]; then
  grep "PasswordAuthentication no" /etc/ssh/sshd_config && echo "SSH密码登录已禁用: ✓" || echo "SSH密码登录未禁用: ✗"
fi

# 5. 依赖检查
echo -e "\n5. 依赖检查:"
which python3 && echo "Python3: ✓" || echo "Python3: ✗"
which pip3 && echo "pip3: ✓" || echo "pip3: ✗"
which docker && echo "Docker: ✓" || echo "Docker: ✗"

echo -e "\n=== 检查完成 ==="
```

#### 2. 资源配置规划

```yaml
# deployment/planning/resource_plan.yaml
resource_planning:
  # 计算资源
  compute:
    api_servers:
      count: 3
      instance_type: "c5.2xlarge"
      cpu: 8
      memory_gb: 16
      storage_gb: 100
      
    database_nodes:
      count: 3
      instance_type: "r5.2xlarge"
      cpu: 8
      memory_gb: 64
      storage_gb: 500
      
    cache_nodes:
      count: 3
      instance_type: "cache.r5.large"
      cpu: 2
      memory_gb: 13.5
      
  # 网络资源
  network:
    vpc_cidr: "10.0.0.0/16"
    subnets:
      - zone: "us-east-1a"
        cidr: "10.0.1.0/24"
        type: "public"
        
      - zone: "us-east-1b"
        cidr: "10.0.2.0/24"
        type: "private"
        
      - zone: "us-east-1c"
        cidr: "10.0.3.0/24"
        type: "private"
        
    load_balancers:
      - name: "api-lb"
        type: "application"
        ports: [80, 443]
        
  # 存储资源
  storage:
    databases:
      type: "gp3"
      size_gb: 500
      iops: 3000
      throughput: 125
      
    backups:
      type: "s3"
      retention_days: 30
      encryption: true
```

### 分步部署指南

#### 阶段1：基础架构部署

```bash
# 1. 初始化基础设施
terraform init
terraform plan -var-file="environments/production.tfvars"
terraform apply -var-file="environments/production.tfvars" -auto-approve

# 2. 配置网络
python scripts/configure_network.py \
  --vpc-id "$(terraform output -raw vpc_id)" \
  --subnets "$(terraform output -json subnet_ids)" \
  --security-groups "$(terraform output -json security_group_ids)"

# 3. 部署负载均衡器
python scripts/deploy_load_balancer.py \
  --name "rangen-ha-lb" \
  --scheme "internet-facing" \
  --listeners "HTTP:80,HTTPS:443" \
  --health-check-path "/health"
```

#### 阶段2：数据层部署

```bash
# 1. 部署数据库集群
python scripts/deploy_database_cluster.py \
  --engine "postgresql" \
  --version "14" \
  --instance-class "db.r5.2xlarge" \
  --nodes 3 \
  --multi-az true \
  --backup-retention 7

# 2. 部署缓存集群
python scripts/deploy_cache_cluster.py \
  --engine "redis" \
  --version "6.x" \
  --node-type "cache.r5.large" \
  --nodes 3 \
  --replication-group-id "rangen-cache"

# 3. 部署向量数据库
python scripts/deploy_vector_database.py \
  --type "chromadb" \
  --replicas 3 \
  --storage-size "100Gi" \
  --persistence "true"
```

#### 阶段3：应用层部署

```bash
# 1. 构建Docker镜像
docker build -t rangen/rangen-api:latest -f Dockerfile.api .
docker build -t rangen/rangen-worker:latest -f Dockerfile.worker .
docker build -t rangen/rangen-monitor:latest -f Dockerfile.monitor .

# 2. 推送镜像到仓库
docker tag rangen/rangen-api:latest registry.rangen.ai/rangen/api:latest
docker push registry.rangen.ai/rangen/api:latest

# 3. 部署应用服务
# 使用Kubernetes部署
kubectl apply -f k8s/deployments/api-deployment.yaml
kubectl apply -f k8s/deployments/worker-deployment.yaml
kubectl apply -f k8s/deployments/monitor-deployment.yaml

# 或者使用Docker Compose部署
docker-compose -f docker-compose.ha.yaml up -d
```

#### 阶段4：配置与集成

```bash
# 1. 配置服务发现
python scripts/configure_service_discovery.py \
  --service "rangen-api" \
  --instances "api-1:8000,api-2:8000,api-3:8000" \
  --health-check "/health"

# 2. 配置监控
python scripts/configure_monitoring.py \
  --prometheus-url "http://prometheus:9090" \
  --grafana-url "http://grafana:3000" \
  --alertmanager-url "http://alertmanager:9093"

# 3. 配置日志聚合
python scripts/configure_logging.py \
  --loki-url "http://loki:3100" \
  --elasticsearch-url "http://elasticsearch:9200" \
  --kibana-url "http://kibana:5601"
```

#### 阶段5：验证与测试

```bash
# 1. 健康检查
python scripts/verify_deployment.py \
  --endpoints "http://api-1:8000/health,http://api-2:8000/health,http://api-3:8000/health" \
  --timeout 30 \
  --retries 3

# 2. 功能测试
pytest tests/integration/ha_tests.py \
  --api-endpoint "http://lb.rangen.ai" \
  --concurrent-users 10 \
  --duration 300

# 3. 故障转移测试
python scripts/test_failover.py \
  --scenario "node_failure" \
  --target-node "api-2" \
  --expected-recovery-time 60 \
  --validate-data-consistency true

# 4. 性能基准测试
python scripts/run_benchmarks.py \
  --scenarios "normal_load,peak_load,failover" \
  --metrics "response_time,throughput,error_rate" \
  --output "reports/benchmarks/initial_deployment.json"
```

### 部署后维护

#### 1. 日常维护任务

```yaml
# maintenance/daily_tasks.yaml
daily_maintenance:
  tasks:
    - name: "健康检查"
      schedule: "*/5 * * * *"  # 每5分钟
      script: "scripts/health_check.py"
      timeout: 300
      
    - name: "备份验证"
      schedule: "0 2 * * *"    # 每天凌晨2点
      script: "scripts/verify_backups.py"
      timeout: 1800
      
    - name: "日志清理"
      schedule: "0 0 * * *"    # 每天凌晨0点
      script: "scripts/cleanup_logs.py"
      retention_days: 30
      
    - name: "监控数据清理"
      schedule: "0 1 * * 0"    # 每周日凌晨1点
      script: "scripts/cleanup_metrics.py"
      retention_days: 90
```

#### 2. 定期维护任务

```yaml
# maintenance/periodic_tasks.yaml
periodic_maintenance:
  weekly:
    - name: "安全补丁更新"
      day: "sunday"
      time: "03:00"
      script: "scripts/apply_security_patches.py"
      maintenance_window: "4h"
      
    - name: "性能优化分析"
      day: "monday"
      time: "04:00"
      script: "scripts/analyze_performance.py"
      
  monthly:
    - name: "证书更新检查"
      day: "first"
      time: "02:00"
      script: "scripts/check_certificates.py"
      alert_days_before_expiry: 30
      
    - name: "容量规划分析"
      day: "15"
      time: "05:00"
      script: "scripts/analyze_capacity.py"
      
  quarterly:
    - name: "灾难恢复演练"
      script: "scripts/run_disaster_recovery_drill.py"
      duration: "8h"
      notification: "1_week_before"
      
    - name: "安全审计"
      script: "scripts/run_security_audit.py"
      scope: "full"
      report_format: "pdf"
```

### 故障排除指南

#### 常见部署问题

| 问题 | 症状 | 解决方案 |
|------|------|---------|
| 节点无法加入集群 | 节点状态为"pending"或"unhealthy" | 检查网络连通性、防火墙规则、时间同步 |
| 数据同步失败 | 副本延迟持续增加 | 检查网络带宽、磁盘IO、数据库配置 |
| 负载均衡不工作 | 流量只分发到部分节点 | 检查健康检查配置、会话保持设置 |
| 监控数据缺失 | Grafana面板显示"No data" | 检查Prometheus配置、服务发现、数据保留策略 |
| 证书验证失败 | TLS握手失败 | 检查证书有效期、证书链、私钥匹配 |

#### 紧急恢复步骤

```bash
# 紧急恢复脚本
#!/bin/bash

# 1. 评估情况
python scripts/assess_situation.py --mode "emergency"

# 2. 隔离故障组件
python scripts/isolate_failed_component.py \
  --component "$FAILED_COMPONENT" \
  --reason "紧急隔离"

# 3. 启用备用资源
python scripts/activate_backup_resources.py \
  --type "hot_standby" \
  --component "$FAILED_COMPONENT_TYPE"

# 4. 恢复服务
python scripts/restore_service.py \
  --service "rangen-api" \
  --priority "critical"

# 5. 通知相关人员
python scripts/send_emergency_notification.py \
  --incident "$INCIDENT_ID" \
  --severity "critical" \
  --channels "sms,email,slack"

# 6. 记录事件
python scripts/log_incident.py \
  --incident "$INCIDENT_ID" \
  --action-taken "$(cat /tmp/actions_taken.txt)" \
  --root-cause "$ROOT_CAUSE"
```

---

## 📝 总结

RANGEN系统的高可用配置是一个系统工程，需要综合考虑架构设计、性能优化、安全加固、成本控制和运维管理。本文档提供了全面的指导，帮助您成功部署和维护高可用的RANGEN系统。

### 关键成功因素

1. **规划设计先行**：充分的规划和设计是高可用实施的基础
2. **渐进式部署**：采用分阶段部署，逐步验证每个环节
3. **自动化运维**：尽可能自动化部署、监控和恢复过程
4. **持续优化**：定期评估和优化高可用架构
5. **团队培训**：确保运维团队熟悉高可用架构和故障处理流程

### 后续步骤

1. **验证环境测试**：先在验证环境中测试所有配置
2. **生产环境小规模部署**：在生产环境中先部署小规模集群
3. **全面监控建立**：确保监控系统全面覆盖高可用组件
4. **故障演练定期进行**：定期进行故障转移和恢复演练
5. **文档持续更新**：根据实际运维经验持续更新本文档

### 获取帮助

如果在部署或维护过程中遇到问题，可以通过以下方式获取帮助：

- **官方文档**：[https://docs.rangen.ai](https://docs.rangen.ai)
- **社区论坛**：[https://community.rangen.ai](https://community.rangen.ai)
- **技术支持**：support@rangen.ai
- **紧急联络**：emergency@rangen.ai (仅限生产环境紧急情况)

---

**最后更新**: 2026-03-07  
**文档版本**: 2.0.0  
**维护团队**: RANGEN高可用架构组  
**审阅状态**: ✅ 已审阅  
**适用版本**: RANGEN V2.5+