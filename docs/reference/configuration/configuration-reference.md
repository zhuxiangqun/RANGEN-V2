# ⚙️ 配置参考文档

## 📖 概述

本文档详细说明RANGEN系统的所有配置选项，包括环境变量、配置文件、运行时配置和最佳实践。正确配置系统对于确保性能、安全性和可靠性至关重要。

## 🔧 配置方式

RANGEN系统支持多种配置方式，按优先级从高到低排列：

1. **环境变量**：最高优先级，适用于敏感信息和部署特定配置
2. **配置文件**：主要配置方式，支持YAML格式
3. **命令行参数**：启动时指定的参数
4. **默认值**：系统内置的合理默认值

### 配置加载顺序
系统按以下顺序加载配置：
1. 加载默认配置值
2. 读取配置文件（如果存在）
3. 应用环境变量（覆盖文件配置）
4. 应用命令行参数（最高优先级）

## 🔐 环境变量配置

### 核心配置

| 环境变量 | 描述 | 默认值 | 必需 | 示例 |
|----------|------|--------|------|------|
| `RANGEN_API_KEY` | 系统API密钥，用于内部认证 | 无 | 是 | `rang_abc123def456...` |
| `RANGEN_ENVIRONMENT` | 运行环境 | `development` | 否 | `production` |
| `RANGEN_LOG_LEVEL` | 日志级别 | `INFO` | 否 | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `RANGEN_SECRET_KEY` | JWT签名密钥 | 自动生成 | 否 | `your-secret-key-here` |
| `RANGEN_CONFIG_PATH` | 配置文件路径 | `config/rangen.yaml` | 否 | `/etc/rangen/config.yaml` |

### 模型配置

| 环境变量 | 描述 | 默认值 | 必需 | 示例 |
|----------|------|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API密钥 | 无 | 否 | `sk-...` |
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | 无 | 是（如果使用） | `sk-...` |
| `STEPSFLASH_API_KEY` | Step-3.5-Flash API密钥 | 无 | 否 | `sk-...` |
| `LOCAL_LLAMA_PATH` | 本地Llama模型路径 | 无 | 否 | `/models/llama-3-8b` |
| `LOCAL_QWEN_PATH` | 本地Qwen模型路径 | 无 | 否 | `/models/qwen-2.5-7b` |

### 数据库配置

| 环境变量 | 描述 | 默认值 | 必需 | 示例 |
|----------|------|--------|------|------|
| `DATABASE_URL` | 数据库连接URL | `sqlite:///data/rangen.db` | 否 | `postgresql://user:pass@localhost/rangen` |
| `VECTOR_STORE_URL` | 向量存储连接URL | `chromadb://localhost:8000` | 否 | `weaviate://localhost:8080` |
| `REDIS_URL` | Redis缓存URL | 无 | 否 | `redis://localhost:6379/0` |
| `CACHE_SIZE` | 内存缓存大小 | `1000` | 否 | `5000` |

### 性能配置

| 环境变量 | 描述 | 默认值 | 必需 | 示例 |
|----------|------|--------|------|------|
| `MAX_WORKERS` | 最大工作线程数 | `4` | 否 | `8` |
| `REQUEST_TIMEOUT` | 请求超时时间（秒） | `30` | 否 | `60` |
| `BATCH_SIZE` | 批处理大小 | `10` | 否 | `50` |
| `CONCURRENT_REQUESTS` | 并发请求数 | `5` | 否 | `20` |
| `MEMORY_LIMIT_MB` | 内存限制（MB） | `2048` | 否 | `4096` |

### 网络配置

| 环境变量 | 描述 | 默认值 | 必需 | 示例 |
|----------|------|--------|------|------|
| `RANGEN_HOST` | 服务监听主机 | `0.0.0.0` | 否 | `127.0.0.1` |
| `RANGEN_PORT` | 服务监听端口 | `8000` | 否 | `8080` |
| `API_BASE_URL` | API基础URL | `http://localhost:8000` | 否 | `https://api.example.com` |
| `CORS_ORIGINS` | CORS允许的来源 | `["http://localhost:3000"]` | 否 | `["https://app.example.com"]` |

## 📁 配置文件格式

RANGEN系统使用YAML格式的配置文件，支持结构化配置和注释。

### 配置文件位置
- 默认路径：`config/rangen.yaml`
- 开发环境：`config/development.yaml`
- 生产环境：`config/production.yaml`
- 自定义路径：通过`RANGEN_CONFIG_PATH`环境变量指定

### 配置文件结构

```yaml
# config/rangen.yaml
version: "3.0"
environment: "production"

# 模型配置
models:
  enabled:
    - "deepseek-chat"
    - "step-3.5-flash"
    - "local-llama"
  
  routing:
    strategy: "auto"  # auto, manual, cost_optimized, performance
    enable_reflection: true
    fallback_enabled: true
    reflection_threshold: 0.7
    cost_weight: 0.4
    performance_weight: 0.6

  # 模型特定配置
  deepseek:
    model: "deepseek-chat"
    temperature: 0.7
    max_tokens: 2048
  
  step_flash:
    model: "step-3.5-flash"
    provider: "openrouter"  # openrouter, nvidia_nim, vllm
    temperature: 0.8
    max_tokens: 4096
  
  local_llama:
    model_path: "/models/llama-3-8b"
    device: "cuda"  # cuda, cpu, auto
    quantization: "fp16"  # fp16, int8, int4

# 训练框架配置
training:
  enabled: true
  levels:
    - "quick_finetune"
    - "domain_adaptation"
    - "full_training"
  
  data_collection:
    enabled: true
    buffer_size: 100
    flush_interval: 300  # 秒
    min_samples_for_training: 1000
  
  quick_finetune:
    enabled: true
    max_epochs: 3
    learning_rate: 1e-4
    batch_size: 8
  
  domain_adaptation:
    enabled: false
    max_epochs: 10
    learning_rate: 5e-5
    batch_size: 4

# 监控配置
monitoring:
  enabled: true
  
  metrics:
    - "latency"
    - "success_rate"
    - "cost"
    - "quality"
    - "token_usage"
    - "error_rate"
  
  alerting:
    enabled: true
    channels:
      - "email"
      - "slack"
      - "webhook"
    
    thresholds:
      latency_p95: 5000  # 毫秒
      success_rate: 0.95  # 95%
      error_rate: 0.05  # 5%
  
  logging:
    level: "INFO"
    format: "json"  # json, text
    retention_days: 30

# 安全配置
security:
  authentication:
    enabled: true
    require_api_key: true
    jwt_expiry_hours: 24
    
  encryption:
    enabled: true
    default_algorithm: "aes-256-gcm"
    key_rotation_days: 90
    
  audit:
    enabled: true
    log_all_requests: false
    sensitive_fields:
      - "password"
      - "api_key"
      - "credit_card"

# 性能配置
performance:
  cache:
    enabled: true
    ttl_seconds: 300  # 5分钟
    max_size_mb: 100
    
  rate_limiting:
    enabled: true
    requests_per_minute: 60
    burst_size: 10
    
  optimization:
    enable_compression: true
    enable_batching: true
    max_batch_size: 20
    batch_timeout_ms: 100

# 数据保护配置
data_protection:
  classification:
    enabled: true
    default_classification: "internal"
    
  encryption:
    at_rest: true
    in_transit: true
    algorithms:
      low_sensitivity: "aes-256-cbc"
      medium_sensitivity: "aes-256-gcm"
      high_sensitivity: "chacha20-poly1305"
      critical_sensitivity: "aes-256-gcm"
    
  retention:
    enabled: true
    default_retention_days: 90
    audit_log_retention_days: 365
```

## 🔄 动态配置

### 配置热重载
RANGEN系统支持配置热重载，无需重启服务即可更新配置：

1. **API方式**：通过管理API更新配置
2. **文件监听**：监控配置文件变化自动重载
3. **配置中心**：支持外部配置中心集成

### 配置API端点
系统提供以下配置管理API端点：

- `GET /api/v1/config` - 获取当前配置
- `POST /api/v1/config` - 更新配置（需要管理员权限）
- `GET /api/v1/config/schema` - 获取配置模式
- `POST /api/v1/config/reload` - 重载配置

### 配置版本管理
配置系统支持版本管理：
- 自动保存配置变更历史
- 支持配置回滚到任意版本
- 配置变更审计日志

## 🛡️ 安全配置最佳实践

### 生产环境配置
1. **使用强API密钥**：生成32字符以上的随机API密钥
2. **启用HTTPS**：配置有效的TLS证书
3. **设置适当权限**：遵循最小权限原则
4. **启用审计日志**：记录所有配置变更
5. **定期轮换密钥**：设置自动密钥轮换策略

### 敏感信息管理
1. **环境变量存储**：将密码、API密钥等存储在环境变量中
2. **加密存储**：确保数据库中的敏感信息加密
3. **访问控制**：限制对配置文件的访问权限
4. **密钥管理服务**：考虑使用专业密钥管理服务

### 合规性配置
根据合规要求配置相应设置：
- **GDPR**：数据保留策略、用户数据访问控制
- **HIPAA**：医疗数据加密、访问审计
- **PCI DSS**：支付信息保护、安全日志
- **ISO 27001**：安全控制、风险评估

## 📊 性能调优配置

### 根据负载调整
根据预期负载调整以下配置：

| 负载级别 | MAX_WORKERS | CACHE_SIZE | REQUEST_TIMEOUT | 建议环境 |
|----------|-------------|------------|-----------------|----------|
| 轻负载 | 2-4 | 500 | 30 | 开发、测试 |
| 中等负载 | 4-8 | 1000 | 30 | 预生产、小型生产 |
| 高负载 | 8-16 | 5000 | 60 | 生产环境 |
| 极高负载 | 16-32 | 10000 | 90 | 大型生产环境 |

### 内存优化
调整内存相关配置优化性能：
- `CACHE_SIZE`：根据可用内存调整
- `BATCH_SIZE`：平衡内存使用和处理效率
- `MEMORY_LIMIT_MB`：防止内存泄漏

### 网络优化
优化网络相关配置：
- `CONCURRENT_REQUESTS`：根据网络带宽调整
- `REQUEST_TIMEOUT`：根据网络延迟调整
- 启用连接池和持久连接

## 🔍 配置验证和测试

### 配置验证
系统启动时自动验证配置：
1. 检查必需配置项是否设置
2. 验证配置值格式和范围
3. 测试外部依赖连接（数据库、模型等）
4. 生成配置验证报告

### 配置测试
建议的配置测试策略：
1. **单元测试**：测试配置加载和验证逻辑
2. **集成测试**：测试配置与系统组件的集成
3. **性能测试**：测试不同配置下的系统性能
4. **安全测试**：测试安全配置的有效性

### 配置文档
保持配置文档与代码同步：
1. 注释所有配置选项
2. 提供配置示例
3. 记录配置变更
4. 维护配置最佳实践指南

## 🚨 故障排除

### 常见配置问题

1. **配置加载失败**
   - 检查配置文件路径和权限
   - 验证配置文件格式（使用YAML验证器）
   - 检查环境变量设置

2. **性能问题**
   - 调整`MAX_WORKERS`和`CACHE_SIZE`
   - 检查网络和数据库连接配置
   - 监控内存使用情况

3. **安全相关问题**
   - 验证API密钥和证书配置
   - 检查访问控制设置
   - 确保敏感信息加密

4. **模型连接问题**
   - 验证模型API密钥和端点配置
   - 检查模型路径和权限
   - 测试模型服务连接

### 配置调试
启用调试模式获取详细配置信息：
```bash
export RANGEN_LOG_LEVEL=DEBUG
export RANGEN_ENVIRONMENT=development
```

检查配置加载日志：
```bash
tail -f logs/rangen.log | grep -i config
```

## 🔄 配置迁移

### 版本升级配置变更
当升级RANGEN版本时，可能需要更新配置：

1. **检查变更日志**：查看配置变更说明
2. **备份现有配置**：备份当前配置文件
3. **逐步迁移**：逐步应用配置变更
4. **测试验证**：测试新配置下的系统功能

### 配置转换工具
系统提供配置转换工具：
```bash
python scripts/convert_config.py --input old_config.yaml --output new_config.yaml
```

### 向后兼容性
系统保持一定程度的配置向后兼容性：
- 自动转换旧格式配置
- 提供默认值替代缺失配置
- 警告不推荐使用的配置选项

## 📝 总结

正确配置RANGEN系统是确保其正常运行的关键。遵循本文档的指导，根据实际需求调整配置，定期审查和优化配置设置，可以显著提高系统的性能、安全性和可靠性。

定期参考官方文档和更新日志，了解新的配置选项和最佳实践。