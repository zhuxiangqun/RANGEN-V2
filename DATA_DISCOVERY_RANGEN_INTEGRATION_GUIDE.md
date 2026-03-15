
## 三、部署与配置

### 3.1 环境准备

#### 3.1.1 系统要求

```yaml
# 环境要求配置文件 environment-requirements.yaml
data_discovery_environment:
  # 硬件要求
  hardware:
    minimum:
      cpu: 4 cores
      memory: 8 GB RAM
      disk: 50 GB (SSD recommended)
    recommended:
      cpu: 8 cores
      memory: 16 GB RAM
      disk: 200 GB SSD
    production:
      cpu: 16 cores
      memory: 32 GB RAM
      disk: 500 GB SSD
    
  # 软件要求
  software:
    operating_system: "Ubuntu 20.04+ / CentOS 8+ / RHEL 8+"
    python_version: "3.9+"
    nodejs_version: "18+"
    docker_version: "20.10+"
    docker_compose_version: "2.20+"
    
  # 网络要求
  network:
    internet_access: "Required for AI services and package downloads"
    firewall_ports: "3000 (Web UI), 8000 (API), 5432 (PostgreSQL), 6379 (Redis)"
    vpn_access: "Required for internal system connections"
    
  # 依赖服务
  dependencies:
    database: "PostgreSQL 14+ with JSONB support"
    cache: "Redis 6+"
    message_queue: "Redis Streams or RabbitMQ"
    object_storage: "MinIO or AWS S3 (optional)"
    monitoring: "Prometheus + Grafana (optional)"
```

#### 3.1.2 RANGEN版本兼容性

```python
# 检查RANGEN兼容性脚本
def check_rangen_compatibility():
    """检查RANGEN系统兼容性"""
    compatibility_matrix = {
        "rangen_version": {
            "minimum": "v2.0.0",
            "recommended": "v2.5.0+",
            "tested_with": ["v2.5.0", "v3.0.0-beta"]
        },
        "required_services": {
            "unified_security_center": True,
            "knowledge_graph_service": True,
            "ai_engine": True,
            "autodiscovery_service": True
        },
        "database_compatibility": {
            "postgresql_version": "14+",
            "jsonb_support": True,
            "timescale_extension": False  # Optional
        }
    }
    return compatibility_matrix
```

### 3.2 安装部署

#### 3.2.1 快速部署脚本

```bash
#!/bin/bash
# data-discovery-install.sh
# 快速安装和配置数据发现模块

set -e

echo "开始部署异构系统数据自动发现与标准化模块..."

# 1. 克隆代码库
echo "步骤1: 克隆代码库"
git clone https://github.com/rangen/data-discovery-extension.git
cd data-discovery-extension

# 2. 安装Python依赖
echo "步骤2: 安装Python依赖"
pip install -r requirements.txt

# 3. 配置环境变量
echo "步骤3: 配置环境变量"
cp .env.example .env
# 编辑.env文件配置数据库连接、API密钥等

# 4. 初始化数据库
echo "步骤4: 初始化数据库"
python scripts/setup_database.py

# 5. 导入行业标准模板
echo "步骤5: 导入行业标准模板"
python scripts/import_standards.py --industry financial

# 6. 启动服务
echo "步骤6: 启动服务"
docker-compose up -d

# 7. 运行健康检查
echo "步骤7: 运行健康检查"
python scripts/health_check.py

echo "部署完成！"
echo "访问地址: http://localhost:3000"
echo "API文档: http://localhost:8000/docs"
```

#### 3.2.2 Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 主API服务
  data-discovery-api:
    image: rangen/data-discovery-api:latest
    container_name: data-discovery-api
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/data_discovery
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - RANGEN_API_URL=http://rangen-api:8000
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    networks:
      - data-discovery-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Web控制台
  data-discovery-ui:
    image: rangen/data-discovery-ui:latest
    container_name: data-discovery-ui
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api/v1
    ports:
      - "3000:3000"
    volumes:
      - ./ui-config:/app/config
    depends_on:
      - data-discovery-api
    networks:
      - data-discovery-network
    restart: unless-stopped

  # PostgreSQL数据库
  postgres:
    image: postgres:14-alpine
    container_name: data-discovery-postgres
    environment:
      - POSTGRES_DB=data_discovery
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    networks:
      - data-discovery-network
    restart: unless-stopped

  # Redis缓存
  redis:
    image: redis:6-alpine
    container_name: data-discovery-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - data-discovery-network
    restart: unless-stopped

  # 数据连接器运行时
  connector-runtime:
    image: rangen/data-connector-runtime:latest
    container_name: connector-runtime
    environment:
      - RUNTIME_MODE=docker
      - MAX_WORKERS=4
    volumes:
      - ./connectors:/app/connectors
      - ./data:/app/data
    networks:
      - data-discovery-network
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:

networks:
  data-discovery-network:
    driver: bridge
```

### 3.3 与RANGEN主系统集成配置

#### 3.3.1 配置集成点

```yaml
# rangen-integration.yaml
rangen_integration:
  # API网关路由配置
  api_gateway:
    routes:
      - path: "/api/v1/data-discovery/**"
        target_service: "data-discovery-api"
        authentication: true
        rate_limit: "100/minute"
        
      - path: "/data-governance/**"
        target_service: "data-discovery-ui"
        authentication: true
        
      - path: "/api/v1/standards/**"
        target_service: "rangen-standards-service"
        authentication: true
        
  # 统一安全中心集成
  security_integration:
    authentication_provider: "rangen-auth-service"
    authorization_rules:
      - resource: "data-sources"
        permissions: ["read", "write", "delete"]
        roles: ["data-engineer", "data-steward", "admin"]
        
      - resource: "standards"
        permissions: ["read", "write", "approve"]
        roles: ["data-steward", "admin"]
        
      - resource: "reports"
        permissions: ["read"]
        roles: ["business-user", "data-analyst", "admin"]
        
  # 知识图谱集成
  knowledge_graph_integration:
    graph_database_url: "neo4j://neo4j:7687"
    sync_interval: "1h"
    entity_types:
      - "data_source"
      - "data_table"
      - "data_field"
      - "data_standard"
      - "business_entity"
      
  # 事件总线集成
  event_bus_integration:
    provider: "redis-streams"
    topics:
      - "data-discovery.schema-discovered"
      - "data-discovery.standard-created"
      - "data-discovery.mapping-generated"
      - "data-discovery.quality-assessed"
```

#### 3.3.2 配置文件模板

```python
# config/rangen_config.py
from pydantic import BaseSettings, Field
from typing import Optional

class RANGENIntegrationConfig(BaseSettings):
    """RANGEN集成配置"""
    
    # RANGEN API配置
    rangen_api_url: str = Field(
        default="http://rangen-api:8000",
        description="RANGEN主系统API地址"
    )
    rangen_api_key: str = Field(
        ...,
        description="RANGEN API访问密钥",
        env="RANGEN_API_KEY"
    )
    
    # 安全中心配置
    security_center_url: str = Field(
        default="http://unified-security-center:8080",
        description="统一安全中心地址"
    )
    
    # 知识图谱配置
    knowledge_graph_url: str = Field(
        default="neo4j://neo4j:7687",
        description="知识图谱数据库地址"
    )
    knowledge_graph_user: str = Field(
        default="neo4j",
        description="知识图谱用户名"
    )
    knowledge_graph_password: str = Field(
        ...,
        description="知识图谱密码",
        env="KNOWLEDGE_GRAPH_PASSWORD"
    )
    
    # 事件总线配置
    event_bus_type: str = Field(
        default="redis",
        description="事件总线类型: redis, kafka, rabbitmq"
    )
    event_bus_url: str = Field(
        default="redis://redis:6379/0",
        description="事件总线地址"
    )
    
    # 同步配置
    sync_enabled: bool = Field(
        default=True,
        description="是否启用与RANGEN的自动同步"
    )
    sync_interval_minutes: int = Field(
        default=60,
        description="同步间隔（分钟）"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

---

## 四、测试与验证

### 4.1 测试策略

#### 4.1.1 测试金字塔

```
数据发现模块测试金字塔
├── 单元测试 (70%)
│   ├── 连接器测试
│   ├── Schema发现器测试
│   ├── 质量评估器测试
│   ├── 映射规则生成器测试
│   └── 工具函数测试
├── 集成测试 (20%)
│   ├── 服务间集成测试
│   ├── 数据库集成测试
│   ├── RANGEN集成测试
│   └── 外部系统集成测试
└── 端到端测试 (10%)
    ├── 完整业务流程测试
    ├── 性能测试
    ├── 安全测试
    └── 用户体验测试
```

#### 4.1.2 测试环境配置

```yaml
# test-environment.yaml
test_environments:
  unit_tests:
    database: "sqlite://:memory:"
    cache: "fakeredis"
    external_services: "mocked"
    ai_services: "mocked"
    
  integration_tests:
    database: "postgresql://test:test@localhost:5432/test_data_discovery"
    cache: "redis://localhost:6379/1"
    external_services: "test-doubles"
    ai_services: "mocked"
    
  e2e_tests:
    database: "postgresql://e2e:e2e@localhost:5432/e2e_data_discovery"
    cache: "redis://localhost:6379/2"
    external_services: "real-with-stubs"
    ai_services: "real-with-limits"
    
  performance_tests:
    database: "postgresql://perf:perf@localhost:5432/perf_data_discovery"
    cache: "redis://localhost:6379/3"
    external_services: "real"
    ai_services: "real"
```

### 4.2 测试用例示例

#### 4.2.1 单元测试示例

```python
# tests/unit/test_schema_discoverer.py
import pytest
from unittest.mock import Mock, patch
from src.discovery.schema_discoverer import IntelligentSchemaDiscoverer
from src.models.data_models import DatabaseMetadata, FieldInfo

class TestIntelligentSchemaDiscoverer:
    """Schema发现器单元测试"""
    
    @pytest.fixture
    def schema_discoverer(self):
        """创建测试用的Schema发现器"""
        ai_engine = Mock()
        return IntelligentSchemaDiscoverer(ai_engine)
    
    def test_discover_from_database_basic(self, schema_discoverer):
        """测试基础数据库Schema发现"""
        # 准备测试数据
        db_metadata = DatabaseMetadata(
            host="localhost",
            port=5432,
            database="test_db",
            tables=["customers", "orders"]
        )
        
        # 模拟数据库连接
        with patch('src.connectors.jdbc_connector.JDBCConnector') as mock_connector:
            mock_connector_instance = mock_connector.return_value
            mock_connector_instance.get_tables.return_value = [
                {"name": "customers", "type": "TABLE"},
                {"name": "orders", "type": "TABLE"}
            ]
            mock_connector_instance.get_table_schema.return_value = {
                "fields": [
                    {"name": "id", "type": "integer", "nullable": False},
                    {"name": "name", "type": "varchar", "nullable": True}
                ]
            }
            
            # 执行测试
            result = schema_discoverer.discover_from_database(db_metadata)
            
            # 验证结果
            assert result.tables_discovered == 2
            assert "customers" in [t.name for t in result.tables]
            assert "orders" in [t.name for t in result.tables]
    
    def test_infer_business_meaning(self, schema_discoverer):
        """测试业务含义推断"""
        # 准备测试字段
        field_info = FieldInfo(
            name="cust_name",
            db_type="VARCHAR(100)",
            sample_values=["张三", "李四", "王五"]
        )
        
        # 模拟AI引擎
        schema_discoverer.ai_engine.analyze_field.return_value = {
            "business_meaning": "客户姓名",
            "confidence": 0.95,
            "standard_suggestion": "customer_name"
        }
        
        # 执行测试
        result = schema_discoverer.infer_business_meaning(field_info)
        
        # 验证结果
        assert result.business_meaning == "客户姓名"
        assert result.confidence >= 0.9
        assert result.standard_suggestion == "customer_name"
```

#### 4.2.2 集成测试示例

```python
# tests/integration/test_data_discovery_service.py
import pytest
import asyncio
from httpx import AsyncClient
from src.main import app
from src.database.session import get_db
from tests.conftest import create_test_database

class TestDataDiscoveryServiceIntegration:
    """数据发现服务集成测试"""
    
    @pytest.fixture(autouse=True)
    async def setup_database(self):
        """设置测试数据库"""
        await create_test_database()
        yield
        # 清理测试数据
    
    @pytest.mark.asyncio
    async def test_create_data_source(self, test_client: AsyncClient):
        """测试创建数据源"""
        # 准备测试数据
        data_source_data = {
            "name": "测试ERP数据库",
            "type": "jdbc",
            "connection_config": {
                "driver": "org.postgresql.Driver",
                "url": "jdbc:postgresql://localhost:5432/test_erp",
                "username": "test_user",
                "password": "test_password"
            }
        }
        
        # 执行API调用
        response = await test_client.post(
            "/api/v1/data-sources",
            json=data_source_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # 验证响应
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试ERP数据库"
        assert data["type"] == "jdbc"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_discover_schema(self, test_client: AsyncClient, test_data_source_id: str):
        """测试Schema发现"""
        # 执行Schema发现
        response = await test_client.post(
            f"/api/v1/data-sources/{test_data_source_id}/discover",
            json={
                "discovery_options": {
                    "sample_size": 100,
                    "infer_business_meaning": True
                }
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        # 验证响应
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        
        # 等待任务完成并获取结果
        job_id = data["job_id"]
        await asyncio.sleep(2)  # 等待任务执行
        
        result_response = await test_client.get(
            f"/api/v1/discovery/{job_id}/results",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert result_response.status_code == 200
        result_data = result_response.json()
        assert result_data["status"] == "completed"
        assert "results" in result_data
```

### 4.3 性能测试

#### 4.3.1 性能基准

```python
# tests/performance/test_performance_benchmark.py
import pytest
import asyncio
import time
from typing import Dict, List
from src.discovery.schema_discoverer import IntelligentSchemaDiscoverer

class TestPerformanceBenchmark:
    """性能基准测试"""
    
    @pytest.mark.performance
    @pytest.mark.parametrize("table_count,field_count", [
        (10, 100),    # 小型数据库
        (100, 1000),  # 中型数据库
        (500, 5000),  # 大型数据库
    ])
    def test_schema_discovery_performance(self, table_count: int, field_count: int):
        """Schema发现性能测试"""
        # 创建模拟数据库元数据
        db_metadata = self._create_mock_database_metadata(table_count, field_count)
        
        # 创建Schema发现器
        schema_discoverer = IntelligentSchemaDiscoverer(Mock())
        
        # 执行性能测试
        start_time = time.time()
        
        # 模拟发现过程
        result = schema_discoverer.discover_from_database(db_metadata)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 验证性能要求
        # 小型数据库: < 5秒
        # 中型数据库: < 30秒
        # 大型数据库: < 120秒
        if table_count <= 10:
            assert execution_time < 5, f"小型数据库发现时间过长: {execution_time:.2f}秒"
        elif table_count <= 100:
            assert execution_time < 30, f"中型数据库发现时间过长: {execution_time:.2f}秒"
        else:
            assert execution_time < 120, f"大型数据库发现时间过长: {execution_time:.2f}秒"
        
        print(f"性能测试结果: {table_count}表, {field_count}字段, 耗时: {execution_time:.2f}秒")
    
    def _create_mock_database_metadata(self, table_count: int, field_count: int) -> Dict:
        """创建模拟数据库元数据"""
        tables = []
        for i in range(table_count):
            table = {
                "name": f"table_{i}",
                "type": "TABLE",
                "estimated_rows": 10000
            }
            tables.append(table)
        
        return {
            "host": "localhost",
            "port": 5432,
            "database": "performance_test",
            "tables": tables,
            "total_fields": field_count
        }
```

---

## 五、运维与监控

### 5.1 监控配置

#### 5.1.1 Prometheus指标

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'data-discovery-api'
    static_configs:
      - targets: ['data-discovery-api:8000']
    
  - job_name: 'data-discovery-connectors'
    static_configs:
      - targets: ['connector-runtime:9090']
    
  - job_name: 'data-discovery-database'
    static_configs:
      - targets: ['postgres:9187']  # PostgreSQL exporter
    
  - job_name: 'data-discovery-redis'
    static_configs:
      - targets: ['redis:9121']  # Redis exporter

# 自定义指标定义
rule_files:
  - "data-discovery-rules.yml"
```

#### 5.1.2 Grafana仪表板配置

```json
{
  "dashboard": {
    "title": "数据发现与标准化监控",
    "panels": [
      {
        "title": "API请求统计",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(data_discovery_api_requests_total[5m])",
            "legendFormat": "请求速率"
          }
        ]
      },
      {
        "title": "Schema发现成功率",
        "type": "gauge",
        "targets": [
          {
            "expr": "data_discovery_schema_discovery_success_rate",
            "legendFormat": "成功率"
          }
        ],
        "thresholds": {
          "steps": [
            {"color": "red", "value": 0.9},
            {"color": "yellow", "value": 0.95},
            {"color": "green", "value": 0.98}
          ]
        }
      },
      {
        "title": "数据源连接状态",
        "type": "table",
        "targets": [
          {
            "expr": "data_discovery_data_source_connection_status",
            "legendFormat": "{{data_source}} - {{status}}"
          }
        ]
      },
      {
        "title": "AI服务使用情况",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(data_discovery_ai_requests_total[5m])",
            "legendFormat": "AI请求速率"
          },
          {
            "expr": "data_discovery_ai_token_usage",
            "legendFormat": "Token使用量"
          }
        ]
      }
    ]
  }
}
```

### 5.2 日志与告警

#### 5.2.1 结构化日志配置

```python
# config/logging_config.py
import logging
import structlog
from pythonjsonlogger import jsonlogger

def setup_structured_logging():
    """设置结构化日志"""
    
    # 配置structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 配置标准logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 控制台输出（开发环境）
    console_handler = logging.StreamHandler()
    console_formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件输出（生产环境）
    file_handler = logging.FileHandler('data-discovery.log')
    file_formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(extra)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return structlog.get_logger()
```

#### 5.2.2 告警规则

```yaml
# alert-rules.yaml
groups:
  - name: data-discovery-alerts
    rules:
      # Schema发现失败告警
      - alert: SchemaDiscoveryFailed
        expr: data_discovery_schema_discovery_failures_total > 0
        for: 5m
        labels:
          severity: warning
          service: data-discovery
        annotations:
          summary: "Schema发现失败"
          description: "过去5分钟内发生了{{ $value }}次Schema发现失败"
          
      # 数据源连接失败告警
      - alert: DataSourceConnectionFailed
        expr: data_discovery_data_source_connection_status == 0
        for: 2m
        labels:
          severity: critical
          service: data-discovery
        annotations:
          summary: "数据源连接失败"
          description: "数据源 {{ $labels.data_source }} 连接失败"
          
      # AI服务响应时间过长告警
      - alert: AIServiceSlowResponse
        expr: histogram_quantile(0.95, rate(data_discovery_ai_response_duration_seconds_bucket[5m])) > 10
        for: 2m
        labels:
          severity: warning
          service: data-discovery
        annotations:
          summary: "AI服务响应时间过长"
          description: "AI服务95%分位响应时间超过10秒"
          
      # 数据库性能告警
      - alert: DatabasePerformanceDegraded
        expr: rate(postgresql_queries_duration_seconds_sum[5m]) / rate(postgresql_queries_duration_seconds_count[5m]) > 1
        for: 5m
        labels:
          severity: warning
          service: data-discovery
        annotations:
          summary: "数据库性能下降"
          description: "数据库查询平均响应时间超过1秒"
```

---

## 六、故障排除与优化

### 6.1 常见问题排查

#### 6.1.1 连接问题排查

```bash
#!/bin/bash
# troubleshoot-connections.sh
# 数据连接故障排查脚本

echo "开始数据连接故障排查..."

# 1. 检查网络连通性
echo "1. 检查网络连通性"
ping -c 3 $TARGET_HOST

# 2. 检查端口访问
echo "2. 检查端口访问"
nc -zv $TARGET_HOST $TARGET_PORT

# 3. 测试数据库连接
echo "3. 测试数据库连接"
psql "host=$TARGET_HOST port=$TARGET_PORT dbname=$DATABASE user=$USERNAME" -c "SELECT 1"

# 4. 检查防火墙规则
echo "4. 检查防火墙规则"
iptables -L -n | grep $TARGET_PORT

# 5. 检查连接池状态
echo "5. 检查连接池状态"
curl -s http://localhost:8000/metrics | grep connection_pool

# 6. 查看连接日志
echo "6. 查看连接日志"
tail -100 /var/log/data-discovery/connector.log | grep -i "error\|failed\|timeout"

echo "故障排查完成"
```

#### 6.1.2 性能问题排查

```python
# scripts/troubleshoot_performance.py
import time
import psutil
import logging
from typing import Dict, Any
from src.monitoring.performance_monitor import PerformanceMonitor

def troubleshoot_performance_issues():
    """性能问题排查"""
    
    logger = logging.getLogger(__name__)
    
    print("开始性能问题排查...")
    
    # 1. 检查系统资源
    print("1. 检查系统资源")
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    
    print(f"  CPU使用率: {cpu_percent}%")
    print(f"  内存使用率: {memory_info.percent}%")
    print(f"  可用内存: {memory_info.available / 1024**3:.2f} GB")
    
    # 2. 检查数据库性能
    print("2. 检查数据库性能")
    try:
        from src.database.session import get_db
        db = next(get_db())
        
        # 执行简单查询测试性能
        start_time = time.time()
        result = db.execute("SELECT 1").fetchone()
        query_time = time.time() - start_time
        
        print(f"  数据库简单查询时间: {query_time:.3f}秒")
        
        if query_time > 0.1:
            print("  ⚠️  数据库响应时间过长")
            
    except Exception as e:
        print(f"  数据库检查失败: {e}")
    
    # 3. 检查服务性能指标
    print("3. 检查服务性能指标")
    monitor = PerformanceMonitor()
    metrics = monitor.get_current_metrics()
    
    for metric_name, metric_value in metrics.items():
        print(f"  {metric_name}: {metric_value}")
        
        # 检查阈值违规
        if "threshold" in metric_name and metric_value > 0.8:
            print(f"  ⚠️  {metric_name}超过阈值")
    
    # 4. 检查最近错误
    print("4. 检查最近错误")
    try:
        error_logs = monitor.get_recent_errors(minutes=10)
        if error_logs:
            print(f"  发现{len(error_logs)}个最近错误:")
            for error in error_logs[:5]:  # 显示前5个错误
                print(f"    - {error['timestamp']}: {error['message']}")
        else:
            print("  未发现最近错误")
    except Exception as e:
        print(f"  错误日志检查失败: {e}")
    
    print("性能问题排查完成")
```

### 6.2 优化建议

#### 6.2.1 性能优化配置

```yaml
# optimization-config.yaml
performance_optimization:
  # 数据库优化
  database:
    connection_pool:
      max_size: 20
      min_size: 5
      max_overflow: 10
      pool_timeout: 30
      
    query_optimization:
      enable_query_cache: true
      cache_ttl_seconds: 300
      max_query_timeout_seconds: 30
      
    index_optimization:
      enable_auto_indexing: true
      frequently_queried_fields: ["data_source_id", "table_name", "created_at"]
      
  # 缓存优化
  cache:
    redis:
      max_connections: 50
      connection_timeout: 5
      read_timeout: 3
      write_timeout: 3
      
    local_cache:
      enable: true
      max_size_mb: 100
      ttl_seconds: 60
      
  # AI服务优化
  ai_services:
    request_batching:
      enable: true
      batch_size: 10
      batch_timeout_seconds: 2
      
    caching:
      enable: true
      cache_ttl_hours: 24
      max_cache_size_mb: 1000
      
    rate_limiting:
      requests_per_minute: 60
      tokens_per_minute: 60000
      
  # 并发优化
  concurrency:
    max_worker_threads: 10
    max_io_threads: 20
    task_queue_size: 1000
    
  # 内存优化
  memory:
    max_heap_size_mb: 2048
    gc_threshold: 0.8
    object_pooling: true
```

#### 6.2.2 扩展性优化

```python
# scaling-optimization.py
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum

class ScalingStrategy(Enum):
    """扩展策略"""
    VERTICAL = "vertical"      # 垂直扩展（增加资源）
    HORIZONTAL = "horizontal"  # 水平扩展（增加实例）
    HYBRID = "hybrid"          # 混合扩展

@dataclass
class ScalingRecommendation:
    """扩展建议"""
    
    strategy: ScalingStrategy
    reason: str
    metrics: Dict[str, Any]
    recommendations: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "reason": self.reason,
            "metrics": self.metrics,
            "recommendations": self.recommendations
        }

class ScalingOptimizer:
    """扩展优化器"""
    
    def analyze_scaling_needs(self, performance_metrics: Dict[str, Any]) -> ScalingRecommendation:
        """分析扩展需求"""
        
        cpu_usage = performance_metrics.get("cpu_usage_percent", 0)
        memory_usage = performance_metrics.get("memory_usage_percent", 0)
        request_rate = performance_metrics.get("requests_per_second", 0)
        response_time = performance_metrics.get("average_response_time_ms", 0)
        
        # 分析扩展需求
        if cpu_usage > 80 and memory_usage > 80:
            # 资源使用率高，需要垂直扩展
            return ScalingRecommendation(
                strategy=ScalingStrategy.VERTICAL,
                reason="高资源使用率",
                metrics={
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage
                },
                recommendations={
                    "increase_cpu": "增加CPU核心数",
                    "increase_memory": "增加内存容量",
                    "optimize_code": "优化代码资源使用"
                }
            )
            
        elif request_rate > 1000 or response_time > 500:
            # 高并发或响应时间长，需要水平扩展
            return ScalingRecommendation(
                strategy=ScalingStrategy.HORIZONTAL,
                reason="高并发或响应时间长",
                metrics={
                    "request_rate": request_rate,
                    "response_time": response_time
                },
                recommendations={
                    "add_instances": "增加服务实例",
                    "load_balancing": "优化负载均衡",
                    "cache_optimization": "优化缓存策略"
                }
            )
            
        else:
            # 当前配置足够，无需扩展
            return ScalingRecommendation(
                strategy=ScalingStrategy.HYBRID,
                reason="当前配置足够",
                metrics=performance_metrics,
                recommendations={
                    "monitor": "持续监控性能指标",
                    "optimize": "优化现有资源配置"
                }
            )
```

---

## 七、总结与后续规划

### 7.1 实施总结

异构系统数据自动发现与标准化模块的集成工作已经完成详细设计和技术规格定义。通过本集成指南，可以实现：

1. **无缝集成**：与RANGEN现有六层架构完美融合
2. **自动发现**：支持多种数据源的Schema自动发现和分析
3. **智能标准化**：基于AI的数据标准推荐和映射生成
4. **全面监控**：完整的运维监控和告警体系
5. **易于扩展**：模块化设计支持后续功能扩展

### 7.2 后续演进路线

```mermaid
gantt
    title 数据发现模块演进路线图
    dateFormat  YYYY-MM
    axisFormat %Y年%m月
    
    section 第一阶段：基础功能
    核心连接器开发         :2024-01, 2M
    Schema发现引擎        :2024-01, 3M
    数据标准管理          :2024-02, 2M
    映射规则生成          :2024-03, 2M
    
    section 第二阶段：智能增强
    AI业务含义推断        :2024-04, 2M
    智能标准推荐          :2024-05, 2M
    自动代码生成          :2024-06, 2M
    质量评估优化          :2024-07, 2M
    
    section 第三阶段：企业级扩展
    多租户支持           :2024-08, 2M
    数据血缘跟踪         :2024-09, 2M
    合规性检查           :2024-10, 2M
    集成数据目录         :2024-11, 2M
    
    section 第四阶段：智能化演进
    自我优化能力         :2025-01, 3M
    联邦学习支持         :2025-04, 3M
    区块链数据治理       :2025-07, 3M
    预测性维护           :2025-10, 3M
```

### 7.3 成功度量指标

| 指标类别 | 具体指标 | 目标值 | 测量方法 |
|---------|----------|--------|----------|
| **技术指标** | 系统可用性 | > 99.5% | Prometheus监控 |
| | API响应时间 | < 200ms (P95) | 性能测试 |
| | Schema发现成功率 | > 98% | 任务成功率统计 |
| | 数据同步延迟 | < 5分钟 | 监控系统记录 |
| **业务指标** | 数据源集成时间 | 减少80% | 实施前后对比 |
| | 标准制定周期 | 减少70% | 项目时间统计 |
| | 数据质量提升 | > 30% | 质量评估分数 |
| | 数据产品上线速度 | 提高50% | 项目周期统计 |
| **运营指标** | 平均故障恢复时间 | < 15分钟 | 运维记录 |
| | 用户满意度 | > 4.5/5.0 | 用户调查问卷 |
| | 运维自动化率 | > 85% | 运维任务统计 |
| | 系统资源利用率 | 60-80% | 监控系统数据 |

### 7.4 实施路线图

#### 7.4.1 短期实施 (1-3个月)
- **阶段1**: 基础连接器开发和集成（JDBC、API、文件）
- **阶段2**: Schema发现引擎核心功能实现
- **阶段3**: 基础数据标准管理和映射生成
- **交付物**: 可用的数据发现MVP版本，支持3-5个典型数据源

#### 7.4.2 中期扩展 (3-6个月)
- **阶段4**: AI增强的业务含义推断和智能标准推荐
- **阶段5**: 完整的数据质量评估和监控体系
- **阶段6**: 自动化代码生成和部署工具
- **交付物**: 企业级数据发现平台，支持所有主要数据源类型

#### 7.4.3 长期演进 (6-12个月)
- **阶段7**: 多租户支持和数据血缘跟踪
- **阶段8**: 智能化自我优化和预测性维护
- **阶段9**: 联邦学习和区块链数据治理集成
- **交付物**: 智能化、自适应的数据治理平台

---

## 八、文档信息

### 8.1 文档版本历史

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0.0 | 2026-03-09 | RANGEN架构团队 | 初始版本，完整技术规格 |
| 1.0.1 | 2026-03-09 | RANGEN架构团队 | 完善数据库设计和集成细节 |
| 1.1.0 | 2026-03-09 | RANGEN架构团队 | 添加故障排除和性能优化章节 |

### 8.2 相关文档

1. **[HETEROGENEOUS_DATA_DISCOVERY_AND_STANDARDIZATION_DESIGN.md](file:///Users/apple/workdata/person/zy/RANGEN-main(syu-python)/HETEROGENEOUS_DATA_DISCOVERY_AND_STANDARDIZATION_DESIGN.md)** - 总体设计方案
2. **[DATA_DISCOVERY_IMPLEMENTATION_GUIDE.md](file:///Users/apple/workdata/person/zy/RANGEN-main(syu-python)/DATA_DISCOVERY_IMPLEMENTATION_GUIDE.md)** - 详细代码实现指南
3. **[HETEROGENEOUS_DATA_DISCOVERY_TECHNICAL_SPECIFICATION.md](file:///Users/apple/workdata/person/zy/RANGEN-main(syu-python)/HETEROGENEOUS_DATA_DISCOVERY_TECHNICAL_SPECIFICATION.md)** - 技术规格说明书
4. **[DATA_GOVERNANCE_CAPABILITY_ANALYSIS.md](file:///Users/apple/workdata/person/zy/RANGEN-main(syu-python)/DATA_GOVERNANCE_CAPABILITY_ANALYSIS.md)** - RANGEN数据治理能力分析

### 8.3 联系信息

- **技术负责人**: RANGEN架构团队
- **项目仓库**: https://github.com/rangen/rangen-data-discovery
- **文档维护**: 定期更新，建议查看最新版本

---

## 总结

本集成指南提供了完整的异构系统数据自动发现与标准化模块与RANGEN系统的集成方案。通过本指南的实施，可以实现：

1. **技术集成**: 与RANGEN六层架构无缝集成，复用现有安全、监控、AI能力
2. **功能完整**: 支持从数据发现、标准制定到映射生成的全流程自动化
3. **运维保障**: 完善的监控、告警、故障排除和性能优化体系
4. **演进路径**: 清晰的短期、中期、长期演进路线图

该模块的集成将显著提升企业在异构系统数据治理方面的能力，加速数据中台实施，实现数据资产的价值最大化。

**文档完成时间**: 2026-03-09  
**文档状态**: 正式发布  
**适用版本**: RANGEN V2.0.0及以上