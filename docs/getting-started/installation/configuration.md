# ⚙️ 环境配置指南

本文档介绍如何配置RANGEN系统的运行环境，包括环境变量、配置文件、数据库配置和系统参数设置。

## 📋 目录

1. [配置概述](#配置概述)
2. [环境变量配置](#环境变量配置)
3. [配置文件管理](#配置文件管理)
4. [数据库配置](#数据库配置)
5. [模型配置](#模型配置)
6. [安全配置](#安全配置)
7. [性能配置](#性能配置)
8. [监控配置](#监控配置)
9. [配置验证](#配置验证)

## 📊 配置概述

### 配置层次结构

RANGEN系统采用分层配置架构，优先级从高到低：

1. **环境变量**：最高优先级，运行时动态配置
2. **命令行参数**：启动时指定的参数
3. **配置文件**：YAML/JSON格式的配置文件
4. **默认值**：系统内置的默认值

### 配置分类

- **核心配置**：系统运行必需的基础配置
- **模型配置**：LLM提供商和模型参数
- **数据库配置**：数据库连接和存储配置
- **安全配置**：认证、授权和加密配置
- **性能配置**：缓存、并发和资源限制
- **监控配置**：日志、指标和告警配置

## 🔧 环境变量配置

### 必需环境变量

以下环境变量是系统运行必需的：

```bash
# 基础配置
export RANGEN_ENVIRONMENT="development"  # development, testing, production
export RANGEN_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
export RANGEN_API_KEY="your-system-api-key"

# 数据库配置
export DATABASE_URL="postgresql://user:password@localhost:5432/rangen_dev"
export REDIS_URL="redis://localhost:6379/0"

# 模型配置
export DEEPSEEK_API_KEY="sk-..."  # DeepSeek API密钥
export STEPFLASH_API_KEY="sk-..."  # Step-3.5-Flash API密钥
```

### 可选环境变量

```bash
# 性能配置
export MAX_WORKERS=4  # 最大工作线程数
export REQUEST_TIMEOUT=30  # 请求超时时间（秒）
export CACHE_SIZE=1000  # 缓存大小
export ENABLE_CACHING="true"  # 启用缓存

# 本地模型配置
export LOCAL_MODEL_ENABLED="true"
export LOCAL_MODEL_PATH="./models/local-llama"
export LOCAL_MODEL_DEVICE="cuda"  # cpu, cuda, mps

# 监控配置
export ENABLE_METRICS="true"
export ENABLE_TRACING="true"
export ENABLE_PROFILING="false"

# 安全配置
export SSL_ENABLED="false"
export RATE_LIMIT_ENABLED="true"
export MAX_REQUESTS_PER_MINUTE=60
```

### 环境变量管理

#### 创建环境变量文件

```bash
# 复制示例文件
cp .env.example .env

# 编辑环境变量
nano .env

# 或者使用脚本设置
python scripts/set_env_vars.py
```

#### 加载环境变量

```bash
# 手动加载
source .env

# 自动加载（在启动脚本中）
export $(cat .env | grep -v '^#' | xargs)
```

#### 验证环境变量

```bash
# 检查环境变量
python scripts/check_env_variables.py

# 显示当前环境变量
python scripts/show_env_content.py

# 验证API密钥
python scripts/verify_api_keys.py
```

## 📁 配置文件管理

### 配置文件结构

RANGEN支持多种配置文件格式：

```
config/
├── system.yaml           # 系统基础配置
├── models.yaml          # 模型配置
├── database.yaml        # 数据库配置
├── security.yaml        # 安全配置
├── monitoring.yaml      # 监控配置
├── production.yaml      # 生产环境配置
└── development.yaml     # 开发环境配置
```

### 主要配置文件

#### system.yaml - 系统基础配置

```yaml
# config/system.yaml
version: "3.0"
environment: "development"
debug: false

logging:
  level: "INFO"
  format: "json"
  file: "logs/system.log"
  max_size: "100MB"
  backup_count: 10

network:
  host: "0.0.0.0"
  port: 8080
  ssl_enabled: false
  ssl_cert: null
  ssl_key: null

performance:
  max_workers: 4
  max_connections: 100
  request_timeout: 30
  cache_size: 1000
  cache_ttl: 3600
```

#### models.yaml - 模型配置

```yaml
# config/models.yaml
models:
  enabled:
    - "deepseek-chat"
    - "step-3.5-flash"
    - "local-llama"
    - "phi-3-mini"

  providers:
    deepseek:
      api_key: "${DEEPSEEK_API_KEY}"
      base_url: "https://api.deepseek.com/v1"
      default_model: "deepseek-chat"
      timeout: 30
      max_retries: 3

    stepflash:
      api_key: "${STEPFLASH_API_KEY}"
      base_url: "https://api.stepflash.ai/v1"
      default_model: "step-3.5-flash"
      timeout: 30
      max_retries: 3

    local:
      enabled: true
      model_path: "./models/local-llama"
      device: "cuda"
      quantization: "int8"
      context_length: 4096

  routing:
    strategy: "adaptive"
    enable_reflection: true
    fallback_enabled: true
    thresholds:
      simple_max_complexity: 0.08
      complex_min_confidence: 0.75
    keywords:
      question_words: ["what", "how", "why", "explain", "compare"]
```

#### database.yaml - 数据库配置

```yaml
# config/database.yaml
databases:
  postgres:
    url: "${DATABASE_URL}"
    pool_size: 10
    max_overflow: 20
    echo: false
    pool_recycle: 3600

  redis:
    url: "${REDIS_URL}"
    pool_size: 10
    decode_responses: true
    socket_keepalive: true

  vector_db:
    type: "qdrant"
    url: "http://localhost:6333"
    collection: "rangen_knowledge"
    embedding_model: "all-MiniLM-L6-v2"
    distance: "Cosine"
```

### 配置加载机制

#### 配置加载优先级

```python
from src.core.config_manager import ConfigManager

# 创建配置管理器
config_manager = ConfigManager()

# 加载配置（按优先级）
config_manager.load_configs([
    "config/system.yaml",
    "config/models.yaml", 
    "config/database.yaml",
    "config/security.yaml"
])

# 获取配置
config = config_manager.get_config()
```

#### 动态配置更新

```python
from src.core.config_manager import ConfigManager

# 动态更新配置
config_manager.update_config({
    "logging": {"level": "DEBUG"},
    "performance": {"max_workers": 8}
})

# 监听配置变化
config_manager.add_listener(lambda config: print("配置已更新"))

# 保存配置到文件
config_manager.save_config("config/updated.yaml")
```

## 🗄️ 数据库配置

### PostgreSQL配置

#### 基本配置

```bash
# 环境变量方式
export DATABASE_URL="postgresql://rangen:password@localhost:5432/rangen_dev"
export POSTGRES_MAX_CONNECTIONS=100
export POSTGRES_STATEMENT_TIMEOUT=30000

# 或者使用配置文件
# config/database.yaml
databases:
  postgres:
    host: "localhost"
    port: 5432
    database: "rangen_dev"
    username: "rangen"
    password: "password"
    pool_size: 10
    max_overflow: 20
    echo_sql: false
```

#### 性能优化配置

```yaml
# 生产环境数据库配置
databases:
  postgres:
    url: "postgresql://rangen:password@localhost:5432/rangen_prod"
    
    # 连接池配置
    pool_size: 20
    max_overflow: 40
    pool_timeout: 30
    pool_recycle: 3600
    pool_pre_ping: true
    
    # 性能配置
    statement_timeout: 30000  # 30秒
    idle_in_transaction_session_timeout: 60000  # 60秒
    
    # 复制配置（可选）
    read_replica_url: "postgresql://replica:password@replica-host:5432/rangen_prod"
```

#### 初始化数据库

```bash
# 创建数据库
python scripts/init-databases.sh

# 运行迁移
python scripts/migrate.py

# 导入初始数据
python scripts/populate_initial_data.py
```

### Redis配置

#### 基本配置

```bash
# 环境变量方式
export REDIS_URL="redis://localhost:6379/0"
export REDIS_PASSWORD="redis123"
export REDIS_MAX_CONNECTIONS=50

# 或者使用配置文件
# config/database.yaml
databases:
  redis:
    host: "localhost"
    port: 6379
    db: 0
    password: "redis123"
    decode_responses: true
    socket_keepalive: true
    socket_timeout: 5
    retry_on_timeout: true
```

#### 缓存策略配置

```yaml
# 缓存配置
cache:
  default_ttl: 3600  # 默认缓存时间（秒）
  max_size: 10000    # 最大缓存条目数
  
  # 缓存策略
  strategy: "lru"    # LRU, LFU, FIFO
  
  # 分区缓存
  partitions:
    query_results:  # 查询结果缓存
      ttl: 1800
      max_size: 5000
      
    model_responses:  # 模型响应缓存
      ttl: 3600
      max_size: 2000
      
    embeddings:  # 嵌入向量缓存
      ttl: 86400  # 24小时
      max_size: 10000
```

## 🤖 模型配置

### LLM提供商配置

#### DeepSeek配置

```yaml
# config/models.yaml
providers:
  deepseek:
    # 必需配置
    api_key: "${DEEPSEEK_API_KEY}"
    base_url: "https://api.deepseek.com/v1"
    
    # 模型选择
    default_model: "deepseek-chat"
    available_models:
      - "deepseek-chat"
      - "deepseek-coder"
      - "deepseek-reasoner"
    
    # 性能配置
    timeout: 30
    max_retries: 3
    retry_delay: 1.0
    
    # 请求配置
    max_tokens: 4096
    temperature: 0.7
    top_p: 0.9
    frequency_penalty: 0.0
    presence_penalty: 0.0
    
    # 流式响应
    stream: false
    stream_buffer_size: 1024
    
    # 成本控制
    cost_per_token: 0.000002  # $0.002 per 1K tokens
    monthly_budget: 100.0  # 每月预算
    enable_cost_tracking: true
```

#### Step-3.5-Flash配置

```yaml
providers:
  stepflash:
    # 必需配置
    api_key: "${STEPFLASH_API_KEY}"
    base_url: "https://api.stepflash.ai/v1"
    
    # 模型选择
    default_model: "step-3.5-flash"
    available_models:
      - "step-3.5-flash"
      - "step-4"
      - "step-4-turbo"
    
    # 性能配置
    timeout: 60  # StepFlash可能需要更长时间
    max_retries: 2
    retry_delay: 2.0
    
    # 质量配置
    max_tokens: 8192  # 支持更长的上下文
    temperature: 0.8
    top_p: 0.95
    
    # 成本控制
    cost_per_token: 0.000005  # $0.005 per 1K tokens
    monthly_budget: 200.0
```

### 本地模型配置

#### 基础本地模型配置

```yaml
providers:
  local:
    # 启用状态
    enabled: true
    force_local: false  # 是否强制使用本地模型
    
    # 模型文件
    model_path: "./models/local-llama"
    tokenizer_path: "./models/local-llama"
    config_path: "./models/local-llama/config.json"
    
    # 硬件配置
    device: "cuda"  # cpu, cuda, mps
    device_id: 0  # GPU设备ID
    
    # 量化配置
    quantization: "int8"  # int8, int4, fp16, fp32
    load_in_8bit: true
    load_in_4bit: false
    
    # 性能配置
    max_length: 4096
    batch_size: 1
    num_beams: 1
    temperature: 0.7
    top_p: 0.9
    repetition_penalty: 1.1
```

#### 本地模型优化配置

```yaml
# 高级本地模型配置
local_advanced:
  # 内存优化
  use_gradient_checkpointing: true
  use_8bit_optimizer: true
  offload_folder: "./offload"
  
  # 速度优化
  use_flash_attention: true
  use_cuda_graph: false  # 实验性功能
  torch_compile: true
  
  # 精度优化
  use_fp16: true
  use_bf16: false
  torch_dtype: "float16"
  
  # 缓存优化
  use_cache: true
  cache_dir: "./model_cache"
  cache_max_size: "10GB"
  
  # 并行配置
  model_parallel: false
  pipeline_parallel: false
  tensor_parallel: false
```

### 路由和负载均衡配置

```yaml
# 智能路由配置
routing:
  # 路由策略
  strategy: "adaptive"  # adaptive, round_robin, weighted, cost_aware
  enable_reflection: true
  enable_fallback: true
  
  # 阈值配置
  thresholds:
    simple_query_max_complexity: 0.08
    complex_query_min_confidence: 0.75
    fallback_threshold: 0.5
    
  # 关键词路由
  keywords:
    question_words: ["what", "how", "why", "explain", "compare", "分析"]
    command_words: ["execute", "run", "calculate", "generate", "create"]
    code_words: ["code", "program", "function", "class", "algorithm"]
    
  # 负载均衡
  load_balancing:
    enabled: true
    strategy: "least_connections"
    health_check_interval: 30
    failure_threshold: 3
    
  # 成本优化
  cost_optimization:
    enabled: true
    budget_per_month: 100.0
    preferred_model: "step-3.5-flash"
    fallback_model: "deepseek-chat"
    emergency_model: "local-llama"
```

## 🔒 安全配置

### 认证和授权配置

```yaml
# config/security.yaml
security:
  # 认证配置
  authentication:
    enabled: true
    method: "jwt"  # jwt, api_key, oauth2
    jwt_secret: "${JWT_SECRET}"
    jwt_expiry: 86400  # 24小时
    
  # API密钥认证
  api_keys:
    enabled: true
    validation_method: "database"  # database, file, memory
    key_header: "X-API-Key"
    rotation_interval: 30  # 天
    
  # 用户管理
  users:
    default_role: "user"
    roles:
      - name: "admin"
        permissions: ["*"]
      - name: "user"
        permissions: ["read", "execute"]
      - name: "guest"
        permissions: ["read"]
```

### 访问控制配置

```yaml
access_control:
  # IP白名单
  ip_whitelist:
    enabled: true
    allowed_ips:
      - "127.0.0.1"
      - "192.168.1.0/24"
      - "10.0.0.0/8"
    
  # 速率限制
  rate_limiting:
    enabled: true
    strategy: "token_bucket"
    requests_per_minute: 60
    burst_size: 10
    storage_backend: "redis"
    
  # API端点保护
  protected_endpoints:
    - path: "/admin/*"
      methods: ["GET", "POST", "PUT", "DELETE"]
      required_role: "admin"
      
    - path: "/api/v1/*"
      methods: ["POST", "PUT", "DELETE"]
      required_role: "user"
      
    - path: "/api/v1/query"
      methods: ["POST"]
      required_role: "guest"
      rate_limit: 10  # 每分钟10次
```

### 数据安全配置

```yaml
data_security:
  # 数据加密
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
    key_rotation: true
    rotation_interval: 90  # 天
    
  # 敏感数据屏蔽
  data_masking:
    enabled: true
    mask_patterns:
      - pattern: "\\b\\d{4}[ -]?\\d{4}[ -]?\\d{4}[ -]?\\d{4}\\b"  # 信用卡号
        replacement: "****-****-****-****"
        
      - pattern: "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"  # 邮箱
        replacement: "***@***.***"
        
  # 审计日志
  audit_logging:
    enabled: true
    log_file: "logs/audit.log"
    retention_days: 365
    events_to_log:
      - "user_login"
      - "api_call"
      - "data_access"
      - "config_change"
```

## 🚀 性能配置

### 系统性能配置

```yaml
# config/performance.yaml
performance:
  # 并发配置
  concurrency:
    max_workers: 4
    thread_pool_size: 10
    process_pool_size: 2
    max_concurrent_requests: 100
    
  # 内存配置
  memory:
    max_memory_mb: 4096
    gc_threshold: 0.8  # 内存使用达到80%时触发GC
    enable_memory_profiling: false
    
  # CPU配置
  cpu:
    affinity: []  # CPU亲和性，空数组表示使用所有CPU
    priority: "normal"  # low, normal, high
```

### 缓存配置

```yaml
cache:
  # 多级缓存
  levels:
    - name: "l1"
      type: "memory"
      size: "100MB"
      ttl: 300  # 5分钟
      
    - name: "l2"
      type: "redis"
      size: "1GB"
      ttl: 3600  # 1小时
      
    - name: "l3"
      type: "disk"
      size: "10GB"
      ttl: 86400  # 24小时
  
  # 缓存策略
  policies:
    query_cache:
      enabled: true
      ttl: 1800  # 30分钟
      max_size: 10000
      
    model_cache:
      enabled: true
      ttl: 3600  # 1小时
      max_size: 5000
      
    embedding_cache:
      enabled: true
      ttl: 86400  # 24小时
      max_size: 100000
```

### 数据库性能配置

```yaml
database_performance:
  # 连接池优化
  connection_pool:
    size: 20
    max_overflow: 40
    timeout: 30
    recycle: 3600
    pre_ping: true
    
  # 查询优化
  query_optimization:
    statement_timeout: 30000  # 30秒
    idle_timeout: 60000  # 60秒
    enable_query_cache: true
    cache_size: 1000
    
  # 索引优化
  indexing:
    auto_create_indexes: true
    index_maintenance_interval: 3600  # 1小时
    vacuum_interval: 86400  # 24小时
```

## 📊 监控配置

### 日志配置

```yaml
# config/monitoring.yaml
logging:
  # 日志级别
  level: "INFO"
  format: "json"  # json, text
  
  # 日志文件
  file:
    path: "logs/rangen.log"
    max_size: "100MB"
    backup_count: 10
    rotation: "daily"
    
  # 控制台输出
  console:
    enabled: true
    format: "text"
    
  # 结构化日志
  structured:
    enabled: true
    include_fields:
      - "timestamp"
      - "level"
      - "message"
      - "module"
      - "function"
      - "line_number"
      - "correlation_id"
```

### 指标监控配置

```yaml
metrics:
  # 采集配置
  collection:
    enabled: true
    interval: 60  # 秒
    timeout: 10
    
  # 指标类型
  types:
    - name: "request_count"
      type: "counter"
      description: "请求数量"
      
    - name: "request_duration"
      type: "histogram"
      description: "请求耗时"
      buckets: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
      
    - name: "memory_usage"
      type: "gauge"
      description: "内存使用量"
      
    - name: "cpu_usage"
      type: "gauge"
      description: "CPU使用率"
      
  # 导出配置
  export:
    prometheus:
      enabled: true
      port: 9090
      path: "/metrics"
      
    open_telemetry:
      enabled: true
      endpoint: "http://localhost:4317"
```

### 告警配置

```yaml
alerts:
  # 告警规则
  rules:
    - name: "high_error_rate"
      condition: "error_rate > 0.05"
      duration: "5m"
      severity: "warning"
      message: "错误率超过5%"
      
    - name: "high_latency"
      condition: "p95_latency > 5.0"
      duration: "10m"
      severity: "warning"
      message: "P95延迟超过5秒"
      
    - name: "memory_high"
      condition: "memory_usage > 0.8"
      duration: "2m"
      severity: "critical"
      message: "内存使用超过80%"
      
  # 通知渠道
  notifications:
    email:
      enabled: false
      smtp_server: "smtp.example.com"
      recipients: ["admin@example.com"]
      
    slack:
      enabled: true
      webhook_url: "${SLACK_WEBHOOK_URL}"
      channel: "#alerts"
      
    webhook:
      enabled: false
      url: "https://example.com/webhook"
```

## ✅ 配置验证

### 配置验证脚本

```bash
# 验证所有配置
python scripts/verify_config.py

# 验证环境变量
python scripts/check_env_variables.py

# 验证API密钥
python scripts/verify_api_keys.py

# 验证数据库连接
python scripts/check_database_connections.py

# 验证模型连接
python scripts/test_model_connections.py
```

### 配置测试

```python
# 配置测试脚本示例
from src.core.config_manager import ConfigManager
from src.services.config_validator import ConfigValidator

def test_configuration():
    # 加载配置
    config_manager = ConfigManager()
    config_manager.load_all_configs()
    
    # 创建验证器
    validator = ConfigValidator(config_manager)
    
    # 验证配置
    results = validator.validate_all()
    
    # 输出结果
    for category, result in results.items():
        if result.valid:
            print(f"✅ {category}: 配置有效")
        else:
            print(f"❌ {category}: 配置问题")
            for issue in result.issues:
                print(f"   - {issue}")
    
    return all(result.valid for result in results.values())

if __name__ == "__main__":
    success = test_configuration()
    exit(0 if success else 1)
```

### 配置备份和恢复

```bash
# 备份当前配置
python scripts/backup_config.py --output config_backup/

# 恢复配置
python scripts/restore_config.py --input config_backup/

# 比较配置差异
python scripts/compare_configs.py config1.yaml config2.yaml

# 导出配置为环境变量
python scripts/export_config_as_env.py --output config.env
```

## 📚 相关资源

### 配置参考

- [系统架构文档](../../architecture/README.md)
- [API配置参考](../development/api-reference/)
- [部署配置参考](./docker-installation.md)
- [最佳实践配置](../../best-practices/README.md)

### 工具和脚本

- `scripts/check_env_variables.py` - 环境变量检查
- `scripts/verify_config.py` - 配置验证
- `scripts/backup_config.py` - 配置备份
- `scripts/migrate_config.py` - 配置迁移

### 最佳实践

1. **版本控制**：将配置文件纳入版本控制
2. **环境分离**：为不同环境创建独立配置
3. **敏感数据**：使用环境变量存储敏感信息
4. **定期审查**：定期审查和更新配置
5. **备份策略**：实施配置备份策略

## 🎯 下一步

1. **基础配置**：设置必需的环境变量和配置文件
2. **模型配置**：配置LLM提供商和本地模型
3. **安全配置**：设置认证、授权和安全策略
4. **性能调优**：根据您的硬件调整性能配置
5. **监控配置**：设置日志、指标和告警

配置完成后，运行验证脚本来确保所有配置正确有效。如有问题，请查看[故障排除指南](../first-steps/troubleshooting.md)或[提交GitHub Issue](https://github.com/your-repo/RANGEN/issues)。

祝您配置顺利！⚙️