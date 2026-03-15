# RANGEN V2 架构改进使用指南

## 📋 概述

本文档介绍RANGEN V2系统最新架构改进功能的使用方法，包括：
- 🔒 **安全加固系统**: 统一认证、输入验证、输出编码、审计日志
- 📊 **可观测性栈**: OpenTelemetry分布式追踪、结构化日志、性能指标
- ⚡ **自动扩缩容**: 基于系统指标的动态资源调整
- 🏗️ **依赖注入**: 现代化服务管理和模块解耦

## 🚀 快速开始

### 1. 启动新版API服务器（依赖注入版本）

```bash
# 使用依赖注入的新版服务器
python src/api/server_di.py

# 或者使用原有服务器（兼容模式）
python src/api/server.py
```

### 2. 配置环境变量

```bash
# 安全配置
export JWT_SECRET_KEY="your-secret-key-here"
export RANGEN_API_KEY="your-default-api-key"
export ENABLE_STRICT_VALIDATION="true"

# 可观测性配置
export ENABLE_OPENTELEMETRY_TRACING="true"
export ENABLE_OPENTELEMETRY_METRICS="true"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"

# 自动扩缩容配置
export ENABLE_AUTOSCALING="true"
export AUTOSCALING_MONITORING_INTERVAL="30"
```

### 3. 验证系统状态

```bash
# 健康检查
curl http://localhost:8000/health

# 认证健康检查（需要API密钥）
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/health/auth

# 系统诊断（需要管理员权限）
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/diag
```

## 🔒 安全加固系统

### 统一认证系统

RANGEN V2提供了三种认证方式：

#### 1. API密钥认证（推荐）
```python
from src.api.auth_service import AuthService

auth_service = AuthService()

# 创建API密钥
api_key = auth_service.generate_api_key()
name = "test-user"
permissions = ["read", "write"]
auth_service.register_api_key(api_key, name, permissions)

# 验证API密钥
is_valid = auth_service.verify_api_key(api_key)
user_info = auth_service.get_api_key_info(api_key)
```

#### 2. JWT令牌认证
```python
# 创建JWT令牌
user_data = {"user_id": "123", "username": "test"}
token = auth_service.create_access_token(user_data)

# 验证JWT令牌
payload = auth_service.verify_access_token(token)
```

#### 3. OAuth2集成
```python
# 配置OAuth2客户端
oauth_config = {
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "authorization_url": "https://auth.example.com/oauth/authorize",
    "token_url": "https://auth.example.com/oauth/token"
}

auth_service.configure_oauth2(oauth_config)

# 获取OAuth2访问令牌
oauth_token = auth_service.get_oauth2_token("authorization_code", "code123")
```

### 输入验证系统

系统提供三级输入验证：

```python
from src.middleware.validation import create_validation_middleware
from src.utils.input_validator import ValidationLevel

# 宽松验证（仅基本验证）
loose_middleware = create_validation_middleware(ValidationLevel.LOOSE)

# 适中验证（推荐级别）
moderate_middleware = create_validation_middleware(ValidationLevel.MODERATE)

# 严格验证（完全验证）
strict_middleware = create_validation_middleware(ValidationLevel.STRICT)
```

验证功能包括：
- 请求体格式验证
- SQL注入检测
- XSS攻击检测
- 路径遍历攻击检测
- 文件上传验证
- 数据大小限制

### 输出编码防护

防御XSS攻击的输出编码：

```python
from src.utils.output_encoder import OutputEncoder

encoder = OutputEncoder()

# HTML编码（防御XSS）
html_input = '<script>alert("xss")</script>'
safe_html = encoder.encode_html(html_input)
# 输出: &lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;

# URL编码
url_input = 'https://example.com/test?param=<script>'
safe_url = encoder.encode_url(url_input)
# 输出: https%3A%2F%2Fexample.com%2Ftest%3Fparam%3D%3Cscript%3E

# JavaScript编码
js_input = 'alert("xss");'
safe_js = encoder.encode_javascript(js_input)

# JSON编码
json_input = {"key": "<script>alert('xss')</script>"}
safe_json = encoder.encode_json(json_input)
```

### 审计日志和安全监控

```python
from src.services.audit_log_service import AuditLogger, AuditEventType

audit_logger = AuditLogger.get_instance()

# 记录安全事件
event = audit_logger.create_event(
    event_type=AuditEventType.LOGIN_SUCCESS,
    user_id="user123",
    username="testuser",
    action="login",
    success=True,
    action_details="用户登录成功"
)

# 保存事件
audit_logger.log_event(event)

# 查询事件
events = audit_logger.query_events(
    start_time="2024-01-01T00:00:00",
    end_time="2024-01-02T00:00:00",
    event_type=AuditEventType.LOGIN_ATTEMPT
)

# 导出事件
audit_logger.export_events_to_json("audit_logs.json")
```

#### 安全检测规则
系统自动检测以下安全事件：
- ✅ **暴力破解攻击**: 短时间内多次登录失败
- ✅ **异常访问模式**: 非常规时间或地点的访问
- ✅ **可疑API调用**: 异常参数或路径的API调用
- ✅ **权限提升尝试**: 尝试访问未授权资源
- ✅ **数据泄露尝试**: 尝试访问敏感数据

## 📊 可观测性栈

### OpenTelemetry分布式追踪

```python
from src.observability.tracing import OpenTelemetryConfig

# 配置分布式追踪
tracing_config = OpenTelemetryConfig()

# 检查追踪状态
print(f"追踪已启用: {tracing_config.enabled}")
print(f"导出器: {tracing_config.exporters}")
print(f"采样率: {tracing_config.sampling_rate}")

# 手动创建追踪span
with tracing_config.tracer.start_as_current_span("custom-operation") as span:
    span.set_attribute("operation.type", "data-processing")
    span.set_attribute("user.id", "user123")
    
    # 执行操作
    result = process_data()
    
    span.set_attribute("result.size", len(result))
```

#### 支持的导出器
- **Console**: 控制台输出（开发环境）
- **Jaeger**: 分布式追踪系统（`http://localhost:14250`）
- **OTLP**: OpenTelemetry协议（`http://localhost:4317`）
- **Zipkin**: 兼容模式（`http://localhost:9411`）

#### 自动检测
系统自动检测以下组件：
- ✅ **FastAPI**: HTTP请求追踪
- ✅ **数据库**: SQL查询追踪
- ✅ **外部API调用**: HTTP客户端追踪
- ✅ **异步任务**: 异步操作追踪

### 结构化日志系统

```python
from src.observability.structured_logging import StructuredLogger, LogLevel

# 创建结构化日志器
logger = StructuredLogger("my-service", level=LogLevel.INFO)

# 记录日志（自动包含trace_id和span_id）
logger.info("用户请求处理开始", 
            extra={"user_id": "123", "endpoint": "/api/data"})

logger.warning("数据库查询缓慢",
              extra={"query_time": 2.5, "threshold": 1.0})

logger.error("API调用失败",
            extra={"status_code": 500, "url": "https://api.example.com"},
            exc_info=True)

# 设置请求日志中间件（自动记录HTTP请求）
from src.observability.structured_logging import request_logging_middleware
app.add_middleware(request_logging_middleware)
```

#### 日志格式
```json
{
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "level": "INFO",
  "logger": "my-service",
  "message": "用户请求处理开始",
  "user_id": "123",
  "endpoint": "/api/data",
  "trace_id": "abc123def456",
  "span_id": "xyz789",
  "service": "RANGEN",
  "environment": "production"
}
```

### 性能指标收集

```python
from src.observability.metrics import MetricsCollector, OpenTelemetryMetrics

# 基础指标收集器
collector = MetricsCollector()

# 记录指标
collector.record_counter("http_requests_total", 1.0, {"method": "GET", "path": "/api/data"})
collector.record_gauge("active_users", 150.0)
collector.record_histogram("request_duration_seconds", 0.25, {"endpoint": "/api/process"})

# OpenTelemetry指标
otel_metrics = OpenTelemetryMetrics()

if otel_metrics.enabled:
    # 记录OpenTelemetry指标
    otel_metrics.record_http_request("GET", "/api/data", 200, 0.15)
    otel_metrics.record_api_call("external_api", "GET", True, 0.5)
```

#### 支持的指标类型
| 类型 | 用途 | 示例 |
|------|------|------|
| **计数器** | 累计计数 | HTTP请求数、API调用数 |
| **直方图** | 值分布统计 | 请求延迟、响应时间分布 |
| **仪表** | 瞬时值 | 活跃用户数、内存使用率 |
| **摘要** | 分位数计算 | P95延迟、P99延迟 |

#### 指标导出
- **Prometheus**: `http://localhost:9090/metrics`
- **OTLP**: OpenTelemetry协议导出
- **控制台**: 开发环境调试

## ⚡ 自动扩缩容系统

### 基础配置

```python
from src.services.autoscaling_service import AutoscalingService

# 创建自动扩缩容服务
autoscaling = AutoscalingService({
    "enabled": True,
    "initial_agent_instances": 2,
    "monitoring_interval": 30,  # 秒
    "max_history_size": 1000
})

# 启动监控
await autoscaling.start_monitoring()

# 获取当前状态
state = autoscaling.get_current_state()
print(f"当前实例数: {state['current_agent_instances']}")
print(f"监控间隔: {state['monitoring_interval']}秒")
print(f"扩缩容规则数: {state['scaling_rules_count']}")
```

### 预定义扩缩容规则

系统包含8条预定义规则：

#### 1. CPU使用率规则
```python
# CPU使用率超过80%时扩容
# CPU使用率低于20%时缩容
```

#### 2. 内存使用率规则
```python
# 内存使用率超过85%时扩容  
# 内存使用率低于30%时缩容
```

#### 3. 请求率规则
```python
# 请求率超过100 RPS时扩容（增加2个实例）
# 请求率低于10 RPS时缩容（减少1个实例）
```

#### 4. 延迟规则
```python
# P95延迟超过500ms时扩容
# P95延迟低于100ms时缩容
```

### 自定义扩缩容规则

```python
from src.services.autoscaling_service import ScalingRule, ScalingDecision, ScalingTarget

# 创建自定义规则
custom_rule = ScalingRule(
    name="custom_error_rate_rule",
    target=ScalingTarget.AGENT_INSTANCES,
    metric_name="error_rate",
    operator=">",
    threshold=5.0,  # 5%错误率
    action=ScalingDecision.SCALE_OUT,
    cooldown_seconds=300,
    min_instances=1,
    max_instances=20,
    adjustment_step=1,
    description="错误率超过5%时扩容"
)

# 添加规则
autoscaling.add_scaling_rule(custom_rule)

# 移除规则
autoscaling.remove_scaling_rule("custom_error_rate_rule")
```

### 扩缩容历史查询

```python
# 获取扩缩容历史
history = autoscaling.get_scaling_history(limit=10)

for entry in history:
    print(f"时间: {entry.timestamp}")
    print(f"决策: {entry.decision.value}")
    print(f"目标: {entry.target.value}")
    print(f"原因: {entry.reason}")
    print(f"成功: {entry.success}")
    print("---")
```

### 冷却期管理

```python
# 清除所有冷却期（慎用）
autoscaling.clear_cooldown()

# 启用/禁用自动扩缩容
autoscaling.enable()   # 启用
autoscaling.disable()  # 禁用
```

## 🏗️ 依赖注入系统

### 统一依赖注入容器

```python
from src.di.unified_container import UnifiedDIContainer, ServiceLifetime
from src.di.bootstrap import bootstrap_application

# 方法1：使用全局容器
container = UnifiedDIContainer()

# 注册服务
container.register_singleton(MyService, MyService)
container.register_transient(MyTransientService, MyTransientService)
container.register_scoped(MyScopedService, MyScopedService)

# 获取服务
service = container.get_service(MyService)

# 方法2：使用引导程序（推荐）
bootstrap = bootstrap_application()
service = bootstrap.get_service(MyService)
```

### 服务生命周期

| 生命周期 | 描述 | 适用场景 |
|----------|------|----------|
| **单例** | 整个应用生命周期内只有一个实例 | 配置服务、日志服务、数据库连接 |
| **瞬态** | 每次请求都创建新实例 | 轻量级服务、无状态服务 |
| **作用域** | 同一作用域内使用相同实例 | HTTP请求作用域、会话作用域 |

### 服务注册器

```python
from src.di.service_registrar import ServiceRegistrar
from src.di.unified_container import UnifiedDIContainer

# 创建服务注册器
container = UnifiedDIContainer()
registrar = ServiceRegistrar(container)

# 注册核心服务
registrar.register_core_services()

# 注册自定义服务
class MyCustomService:
    def __init__(self, config_service):
        self.config = config_service
    
    def do_something(self):
        return "Hello from custom service"

registrar.register_custom_service(MyCustomService, MyCustomService, ServiceLifetime.SINGLETON)
```

### 依赖注入API服务器

新版API服务器（`server_di.py`）完全使用依赖注入：

```python
from src.api.server_di import app, get_service, get_service_async
from src.core.interfaces import IConfigurationService

# 在路由处理函数中使用依赖注入
@app.get("/api/data")
async def get_data():
    # 获取配置服务
    config_service = await get_service_async(IConfigurationService)
    
    # 使用服务
    config_value = config_service.get("my_setting")
    
    return {"data": config_value}

# 在中间件中使用依赖注入
async def di_middleware(request: Request, call_next):
    # 获取日志服务
    logger = await get_service_async(ILoggingService)
    
    logger.info(f"请求: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    return response
```

### 查看已注册的服务

```bash
# API端点查看服务列表（需要管理员权限）
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/di/services
```

响应示例：
```json
{
  "count": 15,
  "services": [
    {
      "name": "ConfigManager",
      "lifetime": "singleton",
      "has_factory": false,
      "is_async": false,
      "dependencies": []
    },
    {
      "name": "StructuredLogger", 
      "lifetime": "singleton",
      "has_factory": false,
      "is_async": false,
      "dependencies": ["StructuredLoggingConfig"]
    },
    {
      "name": "AutoscalingService",
      "lifetime": "singleton", 
      "has_factory": true,
      "is_async": false,
      "dependencies": []
    }
  ]
}
```

## 🔧 配置指南

### 安全配置

```yaml
# config/security.yaml
authentication:
  jwt:
    secret_key: "your-secret-key-here"
    algorithm: "HS256"
    access_token_expire_minutes: 30
    refresh_token_expire_days: 7
  
  api_keys:
    default_key: "your-default-api-key"
    rotation_days: 90
    max_keys_per_user: 5
  
  oauth2:
    enabled: false
    clients:
      google:
        client_id: ""
        client_secret: ""
        redirect_uri: "http://localhost:8000/auth/callback"

validation:
  level: "moderate"  # loose, moderate, strict
  max_request_size: "10MB"
  max_file_size: "5MB"
  allowed_file_types: ["jpg", "png", "pdf", "txt"]

audit_logging:
  enabled: true
  retention_days: 90
  export_path: "/var/log/rangen/audit"
  security_detection:
    brute_force:
      enabled: true
      max_attempts: 5
      window_minutes: 15
    anomaly_detection:
      enabled: true
      learning_period_days: 7
```

### 可观测性配置

```yaml
# config/observability.yaml
tracing:
  enabled: true
  sampling_rate: 0.1  # 10%采样率
  exporters:
    - type: "console"
      verbosity: "detailed"
    - type: "jaeger"
      endpoint: "http://localhost:14250"
    - type: "otlp"
      endpoint: "http://localhost:4317"
  
  instrumentation:
    fastapi: true
    sqlalchemy: true
    httpx: true
    redis: true

logging:
  structured: true
  level: "INFO"  # DEBUG, INFO, WARN, ERROR
  format: "json"
  output:
    - type: "console"
    - type: "file"
      path: "/var/log/rangen/app.log"
      max_size: "100MB"
      backup_count: 10
  
  request_logging:
    enabled: true
    include_headers: false
    include_body: false
    slow_request_threshold_ms: 1000

metrics:
  enabled: true
  collection_interval_seconds: 30
  exporters:
    - type: "prometheus"
      port: 9090
      endpoint: "/metrics"
    - type: "otlp"
      endpoint: "http://localhost:4317"
  
  custom_metrics:
    - name: "business_transactions_total"
      type: "counter"
      description: "业务事务总数"
    - name: "user_sessions_active"
      type: "gauge"
      description: "活跃用户会话数"
```

### 自动扩缩容配置

```yaml
# config/autoscaling.yaml
enabled: true
monitoring_interval_seconds: 30

targets:
  agent_instances:
    min: 1
    max: 20
    default: 2
  
  worker_threads:
    min: 1
    max: 16
    default: 4

rules:
  cpu_high:
    metric: "cpu_percent"
    operator: ">"
    threshold: 80.0
    action: "scale_out"
    cooldown_seconds: 300
    adjustment_step: 1
  
  cpu_low:
    metric: "cpu_percent"
    operator: "<"
    threshold: 20.0
    action: "scale_in"
    cooldown_seconds: 600
    adjustment_step: 1
  
  memory_high:
    metric: "memory_percent"
    operator: ">"
    threshold: 85.0
    action: "scale_out"
    cooldown_seconds: 300
    adjustment_step: 1
  
  request_rate_high:
    metric: "request_rate"
    operator: ">"
    threshold: 100.0
    action: "scale_out"
    cooldown_seconds: 180
    adjustment_step: 2

history:
  max_entries: 1000
  retention_days: 30
```

### 依赖注入配置

```yaml
# config/dependency_injection.yaml
container:
  scan_packages:
    - "src.services"
    - "src.core"
    - "src.agents"
    - "src.tools"
  
  auto_register: true
  validate_on_startup: true

services:
  config_manager:
    type: "src.config.unified_config_system.ConfigManager"
    lifetime: "singleton"
  
  structured_logger:
    type: "src.observability.structured_logging.StructuredLogger"
    lifetime: "singleton"
    args:
      name: "RANGEN"
      level: "INFO"
  
  autoscaling_service:
    type: "src.services.autoscaling_service.AutoscalingService"
    lifetime: "singleton"
    factory: "src.services.autoscaling_service.create_autoscaling_service"
    args:
      enabled: true
      initial_agent_instances: 2

profiles:
  development:
    services:
      tracing:
        enabled: false
      metrics:
        enabled: false
      autoscaling:
        enabled: false
  
  production:
    services:
      tracing:
        enabled: true
        sampling_rate: 0.05
      metrics:
        enabled: true
      autoscaling:
        enabled: true
        monitoring_interval_seconds: 60
```

## 🚨 故障排除

### 常见问题

#### 1. 认证失败
```bash
# 错误: 401 Unauthorized
# 解决方案:
# 1. 检查API密钥是否正确
# 2. 验证JWT令牌是否过期
# 3. 检查权限配置

export RANGEN_API_KEY="correct-api-key-here"
export JWT_SECRET_KEY="correct-secret-key-here"
```

#### 2. 可观测性组件无法启动
```bash
# 错误: OpenTelemetry依赖缺失
# 解决方案:
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

# 或者禁用OpenTelemetry
export ENABLE_OPENTELEMETRY_TRACING="false"
export ENABLE_OPENTELEMETRY_METRICS="false"
```

#### 3. 自动扩缩容不工作
```bash
# 检查系统指标是否可访问
curl http://localhost:8000/diag

# 检查扩缩容服务状态
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/di/services

# 启用调试日志
export LOG_LEVEL="DEBUG"
```

#### 4. 依赖注入错误
```bash
# 错误: 服务未注册
# 解决方案:
# 1. 检查服务是否在 ServiceRegistrar 中注册
# 2. 检查服务生命周期配置
# 3. 验证依赖关系

# 查看已注册的服务
python -c "from src.di.bootstrap import bootstrap_application; b = bootstrap_application(); print(b.get_registered_services())"
```

### 监控和诊断

#### 系统诊断端点
```bash
# 完整系统诊断（需要管理员权限）
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/diag

# 健康检查
curl http://localhost:8000/health

# 指标端点
curl http://localhost:9090/metrics  # Prometheus指标
```

#### 日志查看
```bash
# 查看应用日志
tail -f /var/log/rangen/app.log

# 查看审计日志
tail -f /var/log/rangen/audit/audit.log

# 结构化日志查询（使用jq）
cat /var/log/rangen/app.log | jq 'select(.level == "ERROR")'
```

## 📚 高级主题

### 自定义安全检测规则

```python
from src.services.audit_log_service import SecurityDetectionRule, SecurityEventType

# 创建自定义安全检测规则
custom_rule = SecurityDetectionRule(
    name="custom_data_access_rule",
    event_type=SecurityEventType.DATA_ACCESS,
    condition=lambda event: (
        event.user_id.startswith("external_") and 
        event.resource_type == "sensitive_data"
    ),
    action="alert_admin",
    severity="high",
    description="外部用户访问敏感数据"
)

# 添加规则
audit_logger.add_security_rule(custom_rule)
```

### 自定义指标导出器

```python
from src.observability.metrics import BaseMetricExporter

class CustomMetricExporter(BaseMetricExporter):
    def export(self, metrics):
        # 自定义导出逻辑
        for metric in metrics:
            print(f"导出指标: {metric.name} = {metric.value}")
            
        # 可以导出到数据库、消息队列等
        self.export_to_database(metrics)
        self.export_to_message_queue(metrics)
```

### 扩缩容策略优化

```python
# 基于机器学习的扩缩容策略
class MLScalingStrategy:
    def predict_required_instances(self, historical_metrics):
        # 使用历史数据预测所需实例数
        # 可以集成时间序列预测模型
        return predicted_instances

# 集成到自动扩缩容服务
autoscaling.set_scaling_strategy(MLScalingStrategy())
```

## 📞 支持

### 获取帮助
- 📖 **文档**: 查看 [docs/](file:///Users/apple/workdata/person/zy/RANGEN-main(syu-python)/docs) 目录
- 🐛 **问题报告**: 使用系统诊断端点收集信息
- 🔧 **技术支持**: 检查日志文件和系统状态

### 更新日志
- **v2.0.0**: 架构改进版本，包含安全加固、可观测性、自动扩缩容、依赖注入
- **v1.x.x**: 基础版本，包含核心智能体功能和API

### 兼容性说明
- ✅ **向后兼容**: 新版API服务器兼容原有API
- ✅ **渐进部署**: 可以逐步启用新功能
- ✅ **配置迁移**: 支持从旧配置迁移到新配置

---

**最后更新**: 2026-02-28  
**版本**: v2.0.0  
**作者**: RANGEN开发团队