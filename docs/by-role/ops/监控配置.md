# 监控面板配置指南

## 📖 概述

RANGEN系统提供全面的监控面板配置，支持实时系统监控、性能指标收集、告警管理和健康检查。系统内置多层监控架构，包括基础监控仪表板、增强版监控仪表板和运维监控系统。

## 🎯 监控架构

### 三层监控架构

```
┌─────────────────────────────────────────────┐
│           增强版监控仪表板                    │
│  (EnhancedMonitoringDashboard)              │
├─────────────────────────────────────────────┤
│           基础监控仪表板                      │
│  (SystemMonitoringDashboard)                │
├─────────────────────────────────────────────┤
│           运维监控系统                        │
│  (OperationsMonitoringSystem)               │
└─────────────────────────────────────────────┘
```

### 组件说明

#### 1. 基础监控仪表板 (SystemMonitoringDashboard)
- **位置**: `system_monitoring_dashboard.py`
- **功能**: 实时系统状态监控、性能指标收集、健康检查
- **特性**: 控制台界面、历史数据记录、定时更新

#### 2. 增强版监控仪表板 (EnhancedMonitoringDashboard)
- **位置**: `enhanced_monitoring_dashboard.py`
- **功能**: 集成运维监控系统和报警规则管理
- **特性**: 报警管理、系统健康检查、多系统集成

#### 3. 运维监控系统 (OperationsMonitoringSystem)
- **位置**: `src/monitoring/operations_monitoring_system.py`
- **功能**: 专业级运维监控、告警规则管理、系统健康检查
- **特性**: 自定义告警规则、多级告警、通知集成

## 🚀 快速开始

### 启动基础监控面板
```bash
# 直接运行监控面板
python system_monitoring_dashboard.py

# 或通过脚本启动
python scripts/monitoring_dashboard.py

# 或使用测试脚本
python test_monitoring_system.py
```

### 启动增强版监控面板
```bash
# 启动增强版监控
python enhanced_monitoring_dashboard.py

# 带参数启动
python enhanced_monitoring_dashboard.py --interval 10 --log-level INFO
```

### 集成到统一服务器
```bash
# 启动统一服务器（包含监控功能）
python scripts/start_unified_server.py --enable-monitoring

# 或使用快速启动
python scripts/quick_start.py --monitoring
```

## ⚙️ 配置选项

### 环境变量配置
```bash
# 监控配置
export RANGEN_MONITORING_ENABLED=true
export RANGEN_MONITORING_INTERVAL=5
export RANGEN_ALERTING_ENABLED=true
export RANGEN_HEALTH_CHECK_INTERVAL=60

# 日志配置
export RANGEN_MONITORING_LOG_LEVEL=INFO
export RANGEN_MONITORING_LOG_FILE=/var/log/rangen/monitoring.log

# 告警配置
export RANGEN_ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/...
export RANGEN_ALERT_EMAIL_RECIPIENTS=admin@example.com
```

### 配置文件配置
创建 `config/monitoring.yaml`:

```yaml
# monitoring.yaml
version: "1.0"

dashboard:
  enabled: true
  update_interval: 5  # 秒
  max_history: 1000
  console_output: true
  web_interface: true
  web_port: 8082

metrics:
  collection:
    system: true
    performance: true
    agents: true
    llm: true
    cost: true
  
  retention:
    in_memory: 1000  # 内存中保留的记录数
    persist_to_db: true
    db_retention_days: 30

alerting:
  enabled: true
  rules:
    - name: "high_cpu_usage"
      metric: "system.cpu_percent"
      condition: ">"
      threshold: 80
      severity: "warning"
      cooldown: 300  # 秒
      
    - name: "high_memory_usage"
      metric: "system.memory_percent"
      condition: ">"
      threshold: 85
      severity: "warning"
      cooldown: 300
      
    - name: "agent_failure"
      metric: "agents.failure_rate"
      condition: ">"
      threshold: 10
      severity: "critical"
      cooldown: 60
      
    - name: "llm_latency_high"
      metric: "llm.response_time_p95"
      condition: ">"
      threshold: 10  # 秒
      severity: "warning"
      cooldown: 300

  notifications:
    - type: "console"
      enabled: true
      
    - type: "slack"
      enabled: false
      webhook: "https://hooks.slack.com/services/..."
      channel: "#alerts"
      
    - type: "email"
      enabled: false
      smtp_server: "smtp.gmail.com"
      smtp_port: 587
      username: "alerts@example.com"
      password_env: "ALERT_EMAIL_PASSWORD"
      recipients: ["admin@example.com", "ops@example.com"]

health_check:
  enabled: true
  interval: 60  # 秒
  checks:
    - name: "api_server"
      type: "http"
      endpoint: "http://localhost:8000/health"
      timeout: 5
      expected_status: 200
      
    - name: "database"
      type: "database"
      connection_string_env: "DATABASE_URL"
      timeout: 10
      
    - name: "vector_store"
      type: "service"
      service_name: "chromadb"
      port: 8000
      timeout: 5
```

## 📊 监控指标

### 系统指标
| 指标 | 描述 | 单位 | 采集频率 | 告警阈值 |
|------|------|------|----------|----------|
| `system.cpu_percent` | CPU使用率 | % | 5秒 | >80% (警告), >90% (严重) |
| `system.memory_percent` | 内存使用率 | % | 5秒 | >85% (警告), >95% (严重) |
| `system.disk_usage` | 磁盘使用率 | % | 60秒 | >90% (警告) |
| `system.network_io` | 网络IO | bytes/sec | 5秒 | - |
| `system.process_count` | 进程数 | count | 5秒 | >500 (警告) |

### 性能指标
| 指标 | 描述 | 单位 | 采集频率 | 告警阈值 |
|------|------|------|----------|----------|
| `performance.request_latency_p50` | 请求延迟(P50) | 毫秒 | 实时 | >1000ms (警告) |
| `performance.request_latency_p95` | 请求延迟(P95) | 毫秒 | 实时 | >3000ms (警告) |
| `performance.throughput` | 吞吐量 | 请求/秒 | 实时 | <10 (警告) |
| `performance.success_rate` | 成功率 | % | 实时 | <95% (警告) |
| `performance.error_rate` | 错误率 | % | 实时 | >5% (警告) |

### 智能体指标
| 指标 | 描述 | 单位 | 采集频率 | 告警阈值 |
|------|------|------|----------|----------|
| `agents.total_count` | 智能体总数 | count | 30秒 | - |
| `agents.active_count` | 活跃智能体数 | count | 5秒 | 0 (警告) |
| `agents.failure_rate` | 智能体失败率 | % | 实时 | >10% (警告) |
| `agents.avg_processing_time` | 平均处理时间 | 毫秒 | 实时 | >5000ms (警告) |
| `agents.queue_size` | 任务队列大小 | count | 5秒 | >100 (警告) |

### LLM指标
| 指标 | 描述 | 单位 | 采集频率 | 告警阈值 |
|------|------|------|----------|----------|
| `llm.total_requests` | 总请求数 | count | 实时 | - |
| `llm.success_rate` | 成功率 | % | 实时 | <90% (警告) |
| `llm.response_time_avg` | 平均响应时间 | 秒 | 实时 | >5s (警告) |
| `llm.response_time_p95` | P95响应时间 | 秒 | 实时 | >10s (警告) |
| `llm.tokens_per_minute` | 每分钟令牌数 | tokens/min | 实时 | - |
| `llm.cost_per_hour` | 每小时成本 | 美元 | 实时 | >$10 (警告) |

### 成本指标
| 指标 | 描述 | 单位 | 采集频率 | 告警阈值 |
|------|------|------|----------|----------|
| `cost.total_today` | 今日总成本 | 美元 | 5分钟 | >$50 (警告) |
| `cost.avg_per_request` | 平均每请求成本 | 美元 | 实时 | >$0.10 (警告) |
| `cost.model_breakdown` | 模型成本分布 | % | 5分钟 | - |
| `cost.projected_monthly` | 预计月度成本 | 美元 | 每小时 | >$1000 (警告) |

## 🔧 告警配置

### 告警规则配置示例
```python
from src.monitoring.operations_monitoring_system import AlertRule, AlertSeverity

# 创建CPU使用率告警规则
cpu_rule = AlertRule(
    name="high_cpu_usage",
    description="CPU使用率过高",
    metric="system.cpu_percent",
    condition=">",
    threshold=80.0,
    severity=AlertSeverity.WARNING,
    cooldown_seconds=300,
    notification_channels=["console", "slack"]
)

# 创建内存使用率告警规则
memory_rule = AlertRule(
    name="high_memory_usage",
    description="内存使用率过高",
    metric="system.memory_percent",
    condition=">",
    threshold=85.0,
    severity=AlertSeverity.WARNING,
    cooldown_seconds=300,
    notification_channels=["console", "email"]
)

# 创建智能体失败告警规则
agent_rule = AlertRule(
    name="agent_failure_rate_high",
    description="智能体失败率过高",
    metric="agents.failure_rate",
    condition=">",
    threshold=10.0,
    severity=AlertSeverity.CRITICAL,
    cooldown_seconds=60,
    notification_channels=["console", "slack", "email"]
)
```

### 告警严重级别
| 级别 | 颜色 | 描述 | 响应时间要求 |
|------|------|------|--------------|
| **CRITICAL** | 🔴 红色 | 系统不可用或关键功能故障 | 立即响应 (5分钟内) |
| **WARNING** | 🟡 黄色 | 性能下降或潜在问题 | 尽快响应 (30分钟内) |
| **INFO** | 🔵 蓝色 | 信息性通知，无需立即行动 | 无需立即响应 |

### 告警通知渠道
```python
# 控制台通知
console_notifier = ConsoleNotifier()

# Slack通知
slack_notifier = SlackNotifier(
    webhook_url="https://hooks.slack.com/services/...",
    channel="#alerts",
    username="RANGEN Monitor"
)

# 邮件通知
email_notifier = EmailNotifier(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="alerts@example.com",
    password=os.getenv("ALERT_EMAIL_PASSWORD"),
    recipients=["admin@example.com", "ops@example.com"]
)

# Webhook通知
webhook_notifier = WebhookNotifier(
    url="https://your-webhook.example.com/alerts",
    headers={"Authorization": "Bearer " + os.getenv("WEBHOOK_TOKEN")}
)
```

## 🏥 健康检查

### 内置健康检查项
```python
# API服务器健康检查
api_health_check = HealthCheck(
    name="api_server",
    check_type="http",
    endpoint="http://localhost:8000/health",
    timeout=5,
    expected_status=200,
    interval=30
)

# 数据库健康检查
db_health_check = HealthCheck(
    name="database",
    check_type="database",
    connection_string=os.getenv("DATABASE_URL"),
    timeout=10,
    interval=60
)

# 向量数据库健康检查
vector_db_health_check = HealthCheck(
    name="vector_store",
    check_type="tcp",
    host="localhost",
    port=8000,
    timeout=5,
    interval=60
)

# 文件系统健康检查
fs_health_check = HealthCheck(
    name="file_system",
    check_type="disk_usage",
    path="/",
    threshold=90,  # 使用率超过90%时告警
    interval=300
)
```

### 自定义健康检查
```python
from src.monitoring.health_check import HealthCheck, HealthCheckResult

class CustomHealthCheck(HealthCheck):
    """自定义健康检查示例"""
    
    async def execute(self) -> HealthCheckResult:
        try:
            # 执行自定义检查逻辑
            result = await self._check_custom_service()
            
            if result["status"] == "healthy":
                return HealthCheckResult(
                    name=self.name,
                    status="healthy",
                    message="自定义服务运行正常",
                    details=result
                )
            else:
                return HealthCheckResult(
                    name=self.name,
                    status="unhealthy",
                    message="自定义服务异常",
                    details=result,
                    error=result.get("error")
                )
                
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                message=f"自定义检查失败: {str(e)}",
                error=str(e)
            )
    
    async def _check_custom_service(self) -> Dict[str, Any]:
        # 实现自定义检查逻辑
        pass
```

## 📈 仪表板界面

### 控制台界面
启动监控面板后的控制台界面显示：

```
🚀 RANGEN系统监控仪表板
============================================================
📊 系统状态: ✅ 健康
⏰ 运行时间: 2天 5小时 30分钟
🔄 最后更新: 2026-03-07 14:30:25

📈 性能指标:
  • 请求延迟(P95): 1.2s ✅
  • 吞吐量: 45.3 req/s ✅
  • 成功率: 99.2% ✅
  • 活跃智能体: 12/19 ✅

💻 系统资源:
  • CPU使用率: 45.2% ✅
  • 内存使用率: 62.1% ✅
  • 磁盘使用率: 34.5% ✅

🤖 智能体状态:
  • Chief Agent: ✅ 活跃
  • Expert Agent: ✅ 活跃
  • ReAct Agent: ✅ 活跃
  • RAG Agent: ✅ 活跃

🚨 告警状态:
  • 当前告警: 0
  • 24小时告警: 3
  • 最高级别: INFO

============================================================
命令: (r)刷新 | (a)告警详情 | (h)健康检查 | (q)退出
```

### Web界面
访问 `http://localhost:8082` 查看Web监控界面：

```
仪表板布局:
┌─────────────────┬─────────────────┬─────────────────┐
│   系统概览       │   性能指标      │   资源使用       │
├─────────────────┼─────────────────┼─────────────────┤
│   智能体状态     │   LLM指标       │   成本分析       │
├─────────────────┼─────────────────┼─────────────────┤
│   告警中心       │   健康检查      │   历史数据       │
└─────────────────┴─────────────────┴─────────────────┘
```

### Grafana集成
系统支持Grafana监控面板，配置示例：

```yaml
# grafana/dashboards/rangen.yaml
apiVersion: 1

providers:
  - name: 'RANGEN'
    orgId: 1
    folder: 'RANGEN'
    type: 'file'
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /var/lib/grafana/dashboards
```

导入Grafana仪表板JSON文件到 `grafana/dashboards/` 目录。

## 🔍 故障排查

### 常见问题

#### 问题1: 监控面板无法启动
**症状**: 启动时出现导入错误或连接错误
**解决方案**:
```bash
# 检查Python路径
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# 检查依赖
pip install -r requirements-monitoring.txt

# 检查配置文件
python -c "import yaml; yaml.safe_load(open('config/monitoring.yaml'))"
```

#### 问题2: 指标数据不更新
**症状**: 仪表板显示静态数据或无数据
**解决方案**:
```bash
# 检查监控服务是否运行
ps aux | grep monitoring

# 检查日志
tail -f /var/log/rangen/monitoring.log

# 手动触发指标收集
python -c "from src.monitoring.metrics_collector import collect_metrics; print(collect_metrics())"
```

#### 问题3: 告警不触发
**症状**: 达到阈值但无告警
**解决方案**:
```bash
# 检查告警规则配置
python scripts/check_alert_rules.py

# 测试告警触发
python scripts/test_alert_trigger.py --metric system.cpu_percent --value 90

# 检查通知渠道配置
python scripts/test_notifications.py
```

#### 问题4: 健康检查失败
**症状**: 健康检查显示服务不可用
**解决方案**:
```bash
# 手动运行健康检查
python scripts/run_health_check.py --all

# 检查服务状态
curl http://localhost:8000/health
nc -zv localhost 8000

# 查看详细错误
python scripts/debug_health_check.py --name api_server
```

### 诊断工具

#### 监控诊断脚本
```bash
# 检查监控系统状态
python scripts/check_monitoring_status.py

# 查看指标数据
python scripts/view_metrics.py --last 1h --metric system.cpu_percent

# 分析性能趋势
python scripts/analyze_performance_trends.py --days 7

# 导出监控数据
python scripts/export_monitoring_data.py --format csv --output monitoring_data.csv
```

#### 告警诊断工具
```bash
# 查看当前告警
python scripts/list_alerts.py --active

# 查看告警历史
python scripts/alert_history.py --days 3 --severity critical

# 测试告警规则
python scripts/test_alert_rule.py --rule high_cpu_usage --value 85
```

## 🛠️ 高级配置

### 自定义指标收集器
```python
from src.monitoring.metrics_collector import BaseMetricsCollector
from typing import Dict, Any
import time

class CustomMetricsCollector(BaseMetricsCollector):
    """自定义指标收集器示例"""
    
    def collect(self) -> Dict[str, Any]:
        metrics = {}
        
        # 收集自定义业务指标
        metrics["business.active_users"] = self._get_active_users_count()
        metrics["business.transaction_rate"] = self._get_transaction_rate()
        metrics["business.revenue_per_hour"] = self._get_revenue_metrics()
        
        # 添加元数据
        metrics["_timestamp"] = time.time()
        metrics["_collector"] = "custom_collector"
        
        return metrics
    
    def _get_active_users_count(self) -> int:
        # 实现获取活跃用户数逻辑
        return 42
    
    def _get_transaction_rate(self) -> float:
        # 实现获取交易率逻辑
        return 15.7
    
    def _get_revenue_metrics(self) -> Dict[str, float]:
        # 实现获取收入指标逻辑
        return {"hourly": 1250.50, "daily": 30012.00, "monthly": 900360.00}
```

### 扩展告警处理器
```python
from src.monitoring.alert_handler import BaseAlertHandler
from src.monitoring.operations_monitoring_system import Alert

class CustomAlertHandler(BaseAlertHandler):
    """自定义告警处理器示例"""
    
    async def handle_alert(self, alert: Alert) -> bool:
        """处理告警"""
        
        # 自定义告警处理逻辑
        if alert.severity == "CRITICAL":
            # 执行紧急响应
            await self._trigger_emergency_procedure(alert)
            
        elif alert.severity == "WARNING":
            # 记录告警并通知相关人员
            await self._notify_team(alert)
            
        # 记录到自定义系统
        await self._log_to_custom_system(alert)
        
        return True
    
    async def _trigger_emergency_procedure(self, alert: Alert):
        """触发紧急响应流程"""
        # 实现紧急响应逻辑
        pass
    
    async def _notify_team(self, alert: Alert):
        """通知团队"""
        # 实现团队通知逻辑
        pass
    
    async def _log_to_custom_system(self, alert: Alert):
        """记录到自定义系统"""
        # 实现自定义日志记录
        pass
```

### 集成外部监控系统
```python
import requests
from typing import Dict, Any

class ExternalMonitoringIntegration:
    """外部监控系统集成"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.prometheus_url = config.get("prometheus_url", "http://localhost:9090")
        self.grafana_url = config.get("grafana_url", "http://localhost:3000")
    
    async def push_to_prometheus(self, metrics: Dict[str, Any]):
        """推送指标到Prometheus"""
        # 转换指标格式
        prometheus_metrics = self._convert_to_prometheus_format(metrics)
        
        # 推送到Prometheus Pushgateway
        response = requests.post(
            f"{self.prometheus_url}/api/v1/import/prometheus",
            json=prometheus_metrics
        )
        
        if response.status_code != 200:
            raise Exception(f"推送到Prometheus失败: {response.text}")
    
    async def update_grafana_dashboard(self, dashboard_data: Dict[str, Any]):
        """更新Grafana仪表板"""
        # 更新Grafana仪表板
        response = requests.post(
            f"{self.grafana_url}/api/dashboards/db",
            json=dashboard_data,
            headers={
                "Authorization": f"Bearer {self.config['grafana_token']}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"更新Grafana仪表板失败: {response.text}")
    
    def _convert_to_prometheus_format(self, metrics: Dict[str, Any]) -> str:
        """转换指标为Prometheus格式"""
        prometheus_lines = []
        
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                # 基本格式: metric_name{label="value"} metric_value
                prometheus_lines.append(f'rangen_{metric_name} {value}')
        
        return '\n'.join(prometheus_lines)
```

## 🔄 维护和优化

### 监控数据清理
```bash
# 清理旧的历史数据
python scripts/cleanup_monitoring_data.py --older-than 30d

# 压缩指标数据库
python scripts/compact_metrics_db.py

# 备份监控配置
python scripts/backup_monitoring_config.py --output backup/
```

### 性能优化
```yaml
# monitoring-optimization.yaml
optimization:
  metrics_collection:
    batch_size: 1000
    flush_interval: 10  # 秒
    compression: true
    sample_rate: 1.0  # 采样率，1.0表示100%采集
  
  alert_processing:
    parallel_workers: 4
    queue_size: 10000
    deduplication_window: 300  # 秒
  
  storage:
    use_redis_cache: true
    redis_ttl: 86400  # 秒 (24小时)
    database_connection_pool: 10
```

### 容量规划
```python
# 监控系统容量规划工具
python scripts/capacity_planning.py \
  --metrics-per-second 1000 \
  --retention-days 30 \
  --alert-rules 50 \
  --estimated-storage

# 输出示例:
# 估算存储需求: 2.5 GB
# 内存需求: 512 MB
# 建议配置: 4核CPU, 8GB内存
```

## 📚 参考资料

### 相关文档
- [运维部署概述](../README.md)
- [故障排除指南](../troubleshooting/common-issues.md)
- [性能监控配置](../monitoring/performance-monitoring.md)
- [告警配置指南](../monitoring/alerting.md)

### 外部资源
- [Prometheus官方文档](https://prometheus.io/docs/)
- [Grafana官方文档](https://grafana.com/docs/)
- [OpenTelemetry监控标准](https://opentelemetry.io/)
- [监控最佳实践白皮书](https://landing.google.com/sre/sre-book/chapters/monitoring-distributed-systems/)

### 工具和库
- **psutil**: 系统资源监控库
- **prometheus-client**: Prometheus Python客户端
- **grafana-api**: Grafana API客户端
- **requests**: HTTP请求库
- **redis**: 缓存和队列

---

*最后更新：2026-03-07*  
*文档版本：1.0.0*  
*维护团队：RANGEN运维工作组*