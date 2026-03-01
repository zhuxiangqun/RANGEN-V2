# 动态配置管理系统最佳实践

## 目录

1. [配置管理最佳实践](#配置管理最佳实践)
2. [性能优化](#性能优化)
3. [安全加固](#安全加固)
4. [监控告警](#监控告警)
5. [部署运维](#部署运维)
6. [故障恢复](#故障恢复)

## 配置管理最佳实践

### 1. 分层配置策略

#### 环境分离
```python
# 不同环境的配置模板
templates = {
    'development': {
        'extends': 'aggressive',
        'thresholds': {
            'simple_max_complexity': 0.1  # 开发环境更宽松
        }
    },
    'staging': {
        'extends': 'balanced',
        'thresholds': {
            'simple_max_complexity': 0.08  # 预发布环境中等严格
        }
    },
    'production': {
        'extends': 'conservative',
        'thresholds': {
            'simple_max_complexity': 0.05  # 生产环境最严格
        }
    }
}
```

#### 配置继承
```python
# 基础配置 + 环境覆盖
base_config = {
    'thresholds': {
        'medium_min_complexity': 0.1,
        'medium_max_complexity': 0.3
    }
}

# 生产环境覆盖
prod_config = {
    'extends': 'base',
    'thresholds': {
        'medium_max_complexity': 0.25  # 生产环境更保守
    }
}
```

### 2. 渐进式配置更新

#### A/B测试
```python
# 为新配置创建分支
config_store.create_branch('new_thresholds_experiment')

# 在分支上应用新配置
config_store.switch_branch('new_thresholds_experiment')
router.update_routing_threshold('experiment_threshold', 0.15)

# 运行A/B测试
# ... 测试逻辑 ...

# 如果测试通过，合并到主分支
config_store.merge_branch('new_thresholds_experiment', 'main')
```

#### 灰度发布
```python
# 分批次更新配置
def gradual_config_update(new_config, batches=5):
    total_nodes = len(distribution.nodes)

    for batch in range(batches):
        # 计算本次批次的节点
        batch_size = total_nodes // batches
        start_idx = batch * batch_size
        end_idx = start_idx + batch_size

        batch_nodes = list(distribution.nodes.keys())[start_idx:end_idx]

        # 更新这批节点
        for node_id in batch_nodes:
            distribution._push_config_to_node(node_id, distribution.nodes[node_id], new_config)

        # 监控效果
        monitor_batch_effect(batch, batch_nodes)

        # 等待观察期
        time.sleep(3600)  # 1小时观察期
```

### 3. 配置版本控制

#### 语义化版本标签
```python
# 创建版本标签
version_tags = {
    'v1.0.0': '初始稳定版本',
    'v1.1.0': '优化阈值算法',
    'v1.2.0': '添加关键词支持',
    'v2.0.0': '重构路由逻辑'
}

for version, description in version_tags.items():
    config_store.create_tag(version, description=description)
```

#### 回滚策略
```python
def safe_config_rollback(target_version, backup_current=True):
    """安全的配置回滚"""

    if backup_current:
        # 备份当前配置
        current_config = config_store.load_config()
        backup_tag = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        config_store.create_tag(backup_tag, description="自动备份")

    # 验证目标版本存在
    if not config_store.rollback_to_version(target_version):
        raise ValueError(f"版本 {target_version} 不存在")

    # 重新加载配置
    router.config_manager.load_config()

    # 验证系统健康
    health_check = router.get_system_status()
    if health_check['status'] != 'healthy':
        # 自动回滚到备份版本
        if backup_current:
            config_store.checkout_tag(backup_tag)
        raise RuntimeError("回滚后系统不健康，已自动恢复")

    return True
```

## 性能优化

### 1. 缓存策略

#### 配置缓存
```python
from functools import lru_cache
import hashlib

class ConfigCache:
    def __init__(self, ttl_seconds=300):
        self.cache = {}
        self.ttl = ttl_seconds

    @lru_cache(maxsize=100)
    def get_config_hash(self, config_data):
        """缓存配置哈希计算"""
        return hashlib.md5(json.dumps(config_data, sort_keys=True).encode()).hexdigest()

    def get_cached_config(self, key):
        """获取缓存的配置"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['data']
            else:
                del self.cache[key]  # 过期删除
        return None

    def set_cached_config(self, key, data):
        """设置缓存配置"""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
```

#### 查询结果缓存
```python
class QueryResultCache:
    def __init__(self, max_size=1000):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []

    def get(self, query_hash):
        """获取缓存的查询结果"""
        if query_hash in self.cache:
            # 更新访问顺序
            self.access_order.remove(query_hash)
            self.access_order.append(query_hash)
            return self.cache[query_hash]
        return None

    def put(self, query_hash, result):
        """缓存查询结果"""
        if len(self.cache) >= self.max_size:
            # LRU淘汰
            oldest = self.access_order.pop(0)
            del self.cache[oldest]

        self.cache[query_hash] = result
        self.access_order.append(query_hash)
```

### 2. 批量操作优化

#### 批量配置更新
```python
def batch_update_thresholds(updates, batch_size=10):
    """批量更新阈值，减少IO操作"""

    # 分批处理
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i + batch_size]

        # 开始批量事务
        with config_store.transaction():
            for key, value in batch:
                router.update_routing_threshold(key, value)

        # 批量验证
        config = router.get_routing_config()
        for key, value in batch:
            if config['thresholds'].get(key) != value:
                logger.error(f"批量更新失败: {key}")

        # 批量通知
        notify_config_change(batch)
```

#### 并发查询优化
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncQueryProcessor:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers)

    async def process_queries_batch(self, queries):
        """异步批量处理查询"""

        async def process_single_query(query):
            async with self.semaphore:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self.executor,
                    self._process_query_sync,
                    query
                )

        # 并发处理所有查询
        tasks = [process_single_query(query) for query in queries]
        results = await asyncio.gather(*tasks)

        return results

    def _process_query_sync(self, query):
        """同步查询处理"""
        features = router.feature_extractor.extract_features(query)
        decision = router.decide_route(features)
        return {
            'query': query,
            'route': decision.route_type.value,
            'confidence': decision.confidence
        }
```

### 3. 监控指标优化

#### 性能指标收集
```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'query_count': 0,
            'avg_response_time': 0,
            'error_rate': 0,
            'cache_hit_rate': 0
        }
        self.response_times = []
        self.max_samples = 1000

    def record_query(self, response_time, success=True):
        """记录查询性能"""
        self.metrics['query_count'] += 1

        # 记录响应时间
        self.response_times.append(response_time)
        if len(self.response_times) > self.max_samples:
            self.response_times.pop(0)

        # 更新平均响应时间
        self.metrics['avg_response_time'] = sum(self.response_times) / len(self.response_times)

        # 更新错误率
        if not success:
            self.metrics['error_rate'] = (self.metrics.get('error_count', 0) + 1) / self.metrics['query_count']
        else:
            self.metrics['error_count'] = self.metrics.get('error_count', 0)

    def get_performance_report(self):
        """生成性能报告"""
        return {
            'summary': self.metrics,
            'percentiles': {
                'p50': self._calculate_percentile(50),
                'p95': self._calculate_percentile(95),
                'p99': self._calculate_percentile(99)
            },
            'trends': self._analyze_trends()
        }
```

## 安全加固

### 1. 访问控制

#### 细粒度权限
```python
# 定义细粒度权限
fine_grained_permissions = {
    'config.read.basic': '读取基础配置',
    'config.read.sensitive': '读取敏感配置',
    'config.update.thresholds': '更新阈值',
    'config.update.keywords': '更新关键词',
    'config.update.routing_rules': '更新路由规则',
    'config.delete': '删除配置',
    'admin.system_restart': '系统重启',
    'admin.user_management': '用户管理'
}

# 角色权限映射
role_permissions = {
    'viewer': [
        'config.read.basic'
    ],
    'developer': [
        'config.read.basic',
        'config.read.sensitive',
        'config.update.keywords',
        'config.update.routing_rules'
    ],
    'operator': [
        'config.read.basic',
        'config.read.sensitive',
        'config.update.thresholds',
        'config.update.keywords',
        'config.update.routing_rules'
    ],
    'admin': [
        '*'  # 所有权限
    ]
}
```

#### 多因素认证
```python
class MultiFactorAuth:
    def __init__(self):
        self.pending_auth = {}
        self.auth_timeout = 300  # 5分钟

    def initiate_mfa(self, user_id, method='sms'):
        """发起多因素认证"""
        auth_code = self._generate_auth_code()

        self.pending_auth[user_id] = {
            'code': auth_code,
            'timestamp': time.time(),
            'method': method,
            'attempts': 0
        }

        # 发送验证码
        if method == 'sms':
            self._send_sms_code(user_id, auth_code)
        elif method == 'email':
            self._send_email_code(user_id, auth_code)

        return True

    def verify_mfa(self, user_id, code):
        """验证多因素认证"""
        if user_id not in self.pending_auth:
            return False

        auth_data = self.pending_auth[user_id]

        # 检查超时
        if time.time() - auth_data['timestamp'] > self.auth_timeout:
            del self.pending_auth[user_id]
            return False

        # 检查尝试次数
        if auth_data['attempts'] >= 3:
            del self.pending_auth[user_id]
            return False

        # 验证代码
        if auth_data['code'] == code:
            del self.pending_auth[user_id]
            return True
        else:
            auth_data['attempts'] += 1
            return False
```

### 2. 数据加密

#### 配置加密存储
```python
from cryptography.fernet import Fernet
import base64

class ConfigEncryption:
    def __init__(self, key=None):
        if key is None:
            key = Fernet.generate_key()
        self.cipher = Fernet(key)

    def encrypt_config(self, config_data):
        """加密配置数据"""
        json_str = json.dumps(config_data, ensure_ascii=False)
        encrypted = self.cipher.encrypt(json_str.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt_config(self, encrypted_data):
        """解密配置数据"""
        encrypted = base64.b64decode(encrypted_data)
        decrypted = self.cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())

    def rotate_key(self, new_key):
        """密钥轮换"""
        old_cipher = self.cipher
        self.cipher = Fernet(new_key)

        # 重新加密所有配置
        # ... 实现配置重新加密逻辑
```

#### API通信加密
```python
class SecureAPIClient:
    def __init__(self, base_url, cert_file=None, key_file=None):
        self.base_url = base_url
        self.cert_file = cert_file
        self.key_file = key_file

        # 配置HTTPS
        self.session = requests.Session()
        if cert_file and key_file:
            self.session.cert = (cert_file, key_file)

        # 禁用SSL验证（生产环境应该启用）
        self.session.verify = False

    def secure_request(self, method, endpoint, data=None, token=None):
        """安全的API请求"""
        url = f"{self.base_url}{endpoint}"
        headers = {}

        if token:
            headers['Authorization'] = f"Bearer {token}"

        if data:
            headers['Content-Type'] = 'application/json'
            data = json.dumps(data)

        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            timeout=30
        )

        response.raise_for_status()
        return response.json()
```

### 3. 审计日志

#### 完整审计跟踪
```python
class SecurityAuditor:
    def __init__(self, log_file='security_audit.log'):
        self.log_file = log_file
        self.audit_events = []

    def log_security_event(self, event_type, user_id, resource, action,
                          success=True, details=None, ip_address=None):
        """记录安全事件"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'success': success,
            'details': details or {},
            'ip_address': ip_address,
            'session_id': getattr(threading.current_thread(), 'session_id', None)
        }

        self.audit_events.append(event)

        # 写入日志文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            json.dump(event, f, ensure_ascii=False)
            f.write('\n')

        # 实时告警
        if not success:
            self._trigger_security_alert(event)

        # 保留最近10000条记录
        if len(self.audit_events) > 10000:
            self.audit_events = self.audit_events[-10000:]

    def _trigger_security_alert(self, event):
        """触发安全告警"""
        if event['event_type'] in ['authentication_failure', 'unauthorized_access']:
            alert_manager.trigger_alert(
                f"security_{event['event_type']}",
                {
                    'user_id': event['user_id'],
                    'resource': event['resource'],
                    'ip_address': event['ip_address'],
                    'timestamp': event['timestamp']
                }
            )

    def get_security_report(self, days=7):
        """生成安全报告"""
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_events = [
            event for event in self.audit_events
            if datetime.fromisoformat(event['timestamp']) > cutoff_time
        ]

        return {
            'total_events': len(recent_events),
            'failed_auth_attempts': len([
                e for e in recent_events
                if e['event_type'] == 'authentication_failure'
            ]),
            'unauthorized_access': len([
                e for e in recent_events
                if e['event_type'] == 'unauthorized_access'
            ]),
            'top_resources': self._get_top_resources(recent_events),
            'risk_score': self._calculate_risk_score(recent_events)
        }
```

## 监控告警

### 1. 多维度监控

#### 系统健康监控
```python
class SystemHealthMonitor:
    def __init__(self):
        self.health_checks = []
        self.last_check_time = None
        self.health_history = []

    def add_health_check(self, name, check_function, critical=False):
        """添加健康检查"""
        self.health_checks.append({
            'name': name,
            'function': check_function,
            'critical': critical
        })

    def perform_health_checks(self):
        """执行所有健康检查"""
        results = []
        overall_healthy = True

        for check in self.health_checks:
            try:
                result = check['function']()
                healthy = result.get('healthy', True)

                check_result = {
                    'name': check['name'],
                    'healthy': healthy,
                    'details': result,
                    'timestamp': datetime.now().isoformat()
                }

                results.append(check_result)

                if not healthy and check['critical']:
                    overall_healthy = False

            except Exception as e:
                results.append({
                    'name': check['name'],
                    'healthy': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                if check['critical']:
                    overall_healthy = False

        self.last_check_time = datetime.now()
        self.health_history.append({
            'timestamp': self.last_check_time.isoformat(),
            'overall_healthy': overall_healthy,
            'checks': results
        })

        # 保留最近100次检查记录
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]

        return {
            'overall_healthy': overall_healthy,
            'checks': results
        }
```

#### 配置漂移检测
```python
class ConfigurationDriftDetector:
    def __init__(self):
        self.baseline_configs = {}
        self.drift_threshold = 0.1  # 10%变化阈值

    def set_baseline(self, config_name, config_data):
        """设置基准配置"""
        self.baseline_configs[config_name] = {
            'data': config_data,
            'timestamp': datetime.now().isoformat(),
            'hash': self._calculate_config_hash(config_data)
        }

    def detect_drift(self, config_name, current_config):
        """检测配置漂移"""
        if config_name not in self.baseline_configs:
            return None

        baseline = self.baseline_configs[config_name]
        current_hash = self._calculate_config_hash(current_config)

        if baseline['hash'] == current_hash:
            return {
                'drifted': False,
                'similarity': 1.0,
                'changes': []
            }

        # 计算相似度
        similarity = self._calculate_similarity(baseline['data'], current_config)
        drifted = similarity < (1 - self.drift_threshold)

        changes = []
        if drifted:
            changes = self._identify_changes(baseline['data'], current_config)

        return {
            'drifted': drifted,
            'similarity': similarity,
            'changes': changes,
            'baseline_timestamp': baseline['timestamp']
        }
```

### 2. 智能告警

#### 告警聚合
```python
class AlertAggregator:
    def __init__(self, aggregation_window=300):  # 5分钟窗口
        self.aggregation_window = aggregation_window
        self.pending_alerts = {}
        self.aggregated_alerts = []

    def add_alert(self, alert_id, alert_data):
        """添加告警进行聚合"""
        current_time = time.time()

        # 检查是否已有相似告警
        similar_alert = self._find_similar_alert(alert_id, current_time)

        if similar_alert:
            # 聚合到现有告警
            similar_alert['count'] += 1
            similar_alert['last_occurrence'] = current_time
            similar_alert['samples'].append(alert_data)
        else:
            # 创建新聚合告警
            self.pending_alerts[alert_id] = {
                'id': alert_id,
                'first_occurrence': current_time,
                'last_occurrence': current_time,
                'count': 1,
                'samples': [alert_data],
                'data': alert_data
            }

    def process_aggregated_alerts(self):
        """处理聚合的告警"""
        current_time = time.time()
        ready_alerts = []

        for alert_id, alert in list(self.pending_alerts.items()):
            # 检查是否超过聚合窗口
            if current_time - alert['first_occurrence'] >= self.aggregation_window:
                # 生成聚合告警
                aggregated = self._create_aggregated_alert(alert)
                ready_alerts.append(aggregated)
                del self.pending_alerts[alert_id]

        # 发送聚合告警
        for alert in ready_alerts:
            alert_manager.trigger_alert(
                f"aggregated_{alert['id']}",
                alert
            )

        return ready_alerts
```

## 部署运维

### 1. 容器化部署

#### Dockerfile
```dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY config/ ./config/

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8080 8081

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 启动命令
CMD ["python", "-m", "src.core.intelligent_router"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  config-service:
    build: .
    ports:
      - "8080:8080"  # API端口
      - "8081:8081"  # Web界面端口
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
    restart: unless-stopped
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: config_db
      POSTGRES_USER: config_user
      POSTGRES_PASSWORD: config_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

### 2. Kubernetes部署

#### Deployment配置
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: config-service
  labels:
    app: config-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: config-service
  template:
    metadata:
      labels:
        app: config-service
    spec:
      containers:
      - name: config-service
        image: config-service:latest
        ports:
        - containerPort: 8080
          name: api
        - containerPort: 8081
          name: web
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service配置
```yaml
apiVersion: v1
kind: Service
metadata:
  name: config-service
spec:
  selector:
    app: config-service
  ports:
  - name: api
    port: 8080
    targetPort: 8080
  - name: web
    port: 8081
    targetPort: 8081
  type: ClusterIP
```

#### Ingress配置
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: config-service-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: config.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: config-service
            port:
              number: 8080
      - path: /
        pathType: Prefix
        backend:
          service:
            name: config-service
            port:
              number: 8081
```

### 3. 配置管理

#### ConfigMap配置
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: config-service-config
data:
  app-config.yaml: |
    server:
      port: 8080
      web_port: 8081
    database:
      host: postgres-service
      port: 5432
    redis:
      host: redis-service
      port: 6379
    logging:
      level: INFO
      format: json
```

#### Secret配置
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: config-service-secrets
type: Opaque
data:
  # base64编码的敏感数据
  db-password: cGFzc3dvcmQ=  # password
  api-key: YXBpX2tleQ==     # api_key
  jwt-secret: c2VjcmV0     # secret
```

## 故障恢复

### 1. 自动故障恢复

#### 健康检查和自愈
```python
class AutoRecoveryManager:
    def __init__(self, system):
        self.system = system
        self.recovery_actions = {
            'config_validation_failed': self._recover_config_validation,
            'service_unavailable': self._recover_service_unavailable,
            'high_error_rate': self._recover_high_error_rate,
            'memory_leak': self._recover_memory_leak
        }

    def execute_recovery(self, failure_type, context):
        """执行故障恢复"""
        if failure_type in self.recovery_actions:
            try:
                logger.info(f"开始执行故障恢复: {failure_type}")
                result = self.recovery_actions[failure_type](context)

                if result['success']:
                    logger.info(f"故障恢复成功: {failure_type}")
                    self._notify_recovery_success(failure_type, result)
                else:
                    logger.error(f"故障恢复失败: {failure_type}")
                    self._escalate_to_human(result)

            except Exception as e:
                logger.error(f"故障恢复执行失败: {failure_type}, 错误: {e}")
                self._escalate_to_human({'error': str(e)})

    def _recover_config_validation(self, context):
        """恢复配置验证失败"""
        # 尝试修复配置
        config = self.system.get_routing_config()
        validation = self.system.config_manager.config_validator.validate(config)

        if validation.errors:
            # 回滚到上一个有效配置
            if hasattr(self.system.config_manager, 'rollback_to_previous'):
                self.system.config_manager.rollback_to_previous()

        return {'success': True, 'action': 'config_rollback'}

    def _recover_service_unavailable(self, context):
        """恢复服务不可用"""
        # 重启相关服务
        if hasattr(self.system, 'restart_services'):
            self.system.restart_services()

        # 检查依赖服务
        dependencies_ok = self._check_dependencies()

        return {
            'success': dependencies_ok,
            'action': 'service_restart',
            'dependencies_status': dependencies_ok
        }

    def _recover_high_error_rate(self, context):
        """恢复高错误率"""
        # 启用降级模式
        self.system.enable_degraded_mode()

        # 清理缓存
        if hasattr(self.system, 'clear_caches'):
            self.system.clear_caches()

        # 减少并发数
        self.system.reduce_concurrency()

        return {'success': True, 'action': 'degraded_mode_enabled'}

    def _recover_memory_leak(self, context):
        """恢复内存泄漏"""
        # 强制垃圾回收
        import gc
        gc.collect()

        # 重启工作进程
        self.system.restart_worker_processes()

        # 监控内存使用
        memory_usage = self._get_memory_usage()
        if memory_usage > 0.8:  # 80%内存使用率
            # 启用内存限制
            self.system.enable_memory_limits()

        return {
            'success': True,
            'action': 'memory_cleanup',
            'memory_usage': memory_usage
        }
```

### 2. 备份和恢复

#### 自动备份策略
```python
class BackupManager:
    def __init__(self, system, backup_dir='backups'):
        self.system = system
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

        # 备份策略
        self.backup_schedule = {
            'hourly': 24,    # 保留24小时
            'daily': 7,      # 保留7天
            'weekly': 4,     # 保留4周
            'monthly': 12    # 保留12个月
        }

    def create_backup(self, backup_type='full'):
        """创建备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{backup_type}_{timestamp}"

        backup_path = self.backup_dir / backup_name
        backup_path.mkdir()

        try:
            # 备份配置
            config_backup = self._backup_config()
            with open(backup_path / 'config.json', 'w') as f:
                json.dump(config_backup, f, ensure_ascii=False, indent=2)

            # 备份数据库（如有）
            if hasattr(self.system, 'backup_database'):
                self.system.backup_database(backup_path / 'database.sql')

            # 备份日志
            self._backup_logs(backup_path)

            # 创建备份元数据
            metadata = {
                'backup_type': backup_type,
                'timestamp': timestamp,
                'version': self._get_system_version(),
                'files': list(backup_path.glob('*'))
            }

            with open(backup_path / 'metadata.json', 'w') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 压缩备份
            self._compress_backup(backup_path)

            logger.info(f"备份创建成功: {backup_name}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"备份创建失败: {e}")
            # 清理失败的备份
            import shutil
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise

    def restore_backup(self, backup_path, restore_type='full'):
        """恢复备份"""
        backup_path = Path(backup_path)

        if not backup_path.exists():
            raise ValueError(f"备份路径不存在: {backup_path}")

        try:
            # 读取元数据
            with open(backup_path / 'metadata.json', 'r') as f:
                metadata = json.load(f)

            # 验证备份兼容性
            self._validate_backup_compatibility(metadata)

            # 执行恢复
            if restore_type == 'config' or restore_type == 'full':
                self._restore_config(backup_path)

            if restore_type == 'database' or restore_type == 'full':
                if hasattr(self.system, 'restore_database'):
                    self.system.restore_database(backup_path / 'database.sql')

            logger.info(f"备份恢复成功: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"备份恢复失败: {e}")
            raise

    def cleanup_old_backups(self):
        """清理旧备份"""
        current_time = datetime.now()

        for backup_type, retention_days in self.backup_schedule.items():
            pattern = f"backup_{backup_type}_*.tar.gz"
            backup_files = list(self.backup_dir.glob(pattern))

            # 按时间排序
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # 删除过期备份
            for backup_file in backup_files[retention_days:]:
                backup_file.unlink()
                logger.info(f"删除过期备份: {backup_file.name}")
```

---

**注意**: 这些最佳实践应根据具体的使用场景和需求进行调整。建议在实施前进行充分的测试和评估。
