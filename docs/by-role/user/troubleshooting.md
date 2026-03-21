# 故障排除指南

## 目录

1. [快速诊断](#快速诊断)
2. [常见问题](#常见问题)
3. [性能问题](#性能问题)
4. [配置问题](#配置问题)
5. [网络问题](#网络问题)
6. [安全问题](#安全问题)
7. [日志分析](#日志分析)
8. [紧急恢复](#紧急恢复)

## 快速诊断

### 系统状态检查

#### 1. 健康检查脚本
```bash
#!/bin/bash
# health_check.sh

echo "=== 动态配置系统健康检查 ==="
echo "检查时间: $(date)"

# 检查进程
echo -e "\n1. 进程状态:"
if pgrep -f "intelligent_router" > /dev/null; then
    echo "✅ 主进程运行正常"
    ps aux | grep intelligent_router | grep -v grep
else
    echo "❌ 主进程未运行"
fi

# 检查端口
echo -e "\n2. 端口状态:"
for port in 8080 8081; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        echo "✅ 端口 $port 正常"
    else
        echo "❌ 端口 $port 未监听"
    fi
done

# 检查配置文件
echo -e "\n3. 配置文件状态:"
config_files=("dynamic_config.json" "routing_config.json")
for config_file in "${config_files[@]}"; do
    if [ -f "$config_file" ]; then
        echo "✅ $config_file 存在"
        # 检查JSON格式
        if jq . "$config_file" >/dev/null 2>&1; then
            echo "   JSON格式正确"
        else
            echo "   ❌ JSON格式错误"
        fi
    else
        echo "❌ $config_file 不存在"
    fi
done

# 检查磁盘空间
echo -e "\n4. 磁盘空间:"
df -h | grep -E "(Filesystem|/$)"

# 检查内存使用
echo -e "\n5. 内存使用:"
free -h

# 检查网络连接
echo -e "\n6. 网络连接:"
ss -tlnp | grep -E ":(8080|8081) "

echo -e "\n=== 检查完成 ==="
```

#### 2. Python诊断脚本
```python
#!/usr/bin/env python3
"""
系统诊断脚本
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def diagnose_system():
    """系统诊断"""
    print("=== 系统诊断报告 ===")
    print(f"诊断时间: {datetime.now()}")

    issues = []

    # 1. 检查配置文件
    print("\n1. 配置文件检查:")
    config_files = ['dynamic_config.json', 'routing_config.json']
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file} 存在")
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                print(f"   JSON格式正确")
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON格式错误: {e}")
                issues.append(f"配置文件格式错误: {config_file}")
        else:
            print(f"❌ {config_file} 不存在")
            issues.append(f"缺少配置文件: {config_file}")

    # 2. 检查API连接
    print("\n2. API连接检查:")
    api_endpoints = [
        ('http://localhost:8080/health', 'API健康检查'),
        ('http://localhost:8081/', 'Web界面')
    ]

    for url, description in api_endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {description}: HTTP {response.status_code}")
            else:
                print(f"⚠️  {description}: HTTP {response.status_code}")
                issues.append(f"API响应异常: {description} - {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {description}: 连接失败 - {e}")
            issues.append(f"API连接失败: {description}")

    # 3. 检查系统资源
    print("\n3. 系统资源检查:")
    try:
        import psutil

        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"CPU使用率: {cpu_percent}%")
        if cpu_percent > 90:
            issues.append(f"CPU使用率过高: {cpu_percent}%")

        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        print(f"内存使用率: {memory_percent}%")
        if memory_percent > 90:
            issues.append(f"内存使用率过高: {memory_percent}%")

        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        print(f"磁盘使用率: {disk_percent}%")
        if disk_percent > 90:
            issues.append(f"磁盘使用率过高: {disk_percent}%")

    except ImportError:
        print("psutil未安装，跳过资源检查")

    # 4. 检查日志文件
    print("\n4. 日志文件检查:")
    log_files = ['config_changes.log', 'security_audit.log']
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file) / 1024  # KB
            print(f"✅ {log_file}: {size:.1f}KB")
            if size > 100*1024:  # 100MB
                issues.append(f"日志文件过大: {log_file} - {size:.1f}KB")
        else:
            print(f"ℹ️  {log_file} 不存在（这是正常的）")

    # 5. 检查Python环境
    print("\n5. Python环境检查:")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")

    # 检查关键模块
    required_modules = ['src.core.intelligent_router', 'src.core.dynamic_config_system']
    for module in required_modules:
        try:
            __import__(module.replace('.', '_'))
            print(f"✅ 模块 {module} 可导入")
        except ImportError as e:
            print(f"❌ 模块 {module} 导入失败: {e}")
            issues.append(f"模块导入失败: {module}")

    # 总结
    print(f"\n=== 诊断完成 ===")
    if issues:
        print(f"发现 {len(issues)} 个问题:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
    else:
        print("✅ 未发现明显问题")

    return issues

if __name__ == '__main__':
    issues = diagnose_system()
    sys.exit(1 if issues else 0)
```

### 运行诊断
```bash
# 运行健康检查
./health_check.sh

# 运行Python诊断
python diagnose_system.py
```

## 常见问题

### 启动失败

#### 问题1: 端口被占用
```
错误: [Errno 48] Address already in use
```

**解决方案**:
```bash
# 检查端口占用
lsof -i :8080
lsof -i :8081

# 杀死占用进程
kill -9 <PID>

# 或者使用不同端口启动
python -c "
from src.core.intelligent_router import IntelligentRouter
router = IntelligentRouter()
# 手动指定端口
"
```

#### 问题2: 模块导入错误
```
ImportError: No module named 'src.core.intelligent_router'
```

**解决方案**:
```bash
# 安装依赖
pip install -r requirements.txt

# 检查Python路径
python -c "import sys; print(sys.path)"

# 添加项目根目录到PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

#### 问题3: 配置文件不存在
```
FileNotFoundError: dynamic_config.json not found
```

**解决方案**:
```bash
# 创建默认配置文件
cat > dynamic_config.json << EOF
{
  "thresholds": {
    "simple_max_complexity": 0.05,
    "medium_max_complexity": 0.25,
    "complex_min_complexity": 0.25
  },
  "keywords": {
    "question_words": ["what", "why", "how"]
  }
}
EOF
```

### 运行时错误

#### 问题1: 配置验证失败
```
配置验证失败: 阈值 simple_max_complexity 超出范围
```

**解决方案**:
```python
# 检查配置值范围
from src.core.dynamic_config_system import ConfigValidator

validator = ConfigValidator()
config = {
    "thresholds": {
        "simple_max_complexity": 0.05,  # 应该是 0.0-1.0
        "medium_max_complexity": 0.25
    }
}

result = validator.validate(config)
if not result.is_valid:
    print("验证错误:", result.errors)
```

#### 问题2: 内存不足
```
MemoryError: Out of memory
```

**解决方案**:
```bash
# 检查内存使用
free -h

# 增加交换空间
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 或减少缓存大小
export CONFIG_CACHE_SIZE=100  # 默认1000
```

#### 问题3: 数据库连接失败
```
ConnectionError: Unable to connect to database
```

**解决方案**:
```bash
# 检查数据库状态
sudo systemctl status postgresql

# 检查连接配置
cat config/database.yml

# 测试连接
psql -h localhost -U config_user -d config_db
```

## 性能问题

### CPU使用率过高

#### 症状
- 系统响应慢
- CPU使用率持续 > 80%

#### 诊断步骤
```python
import psutil
import time

# 监控CPU使用率
for _ in range(10):
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"CPU使用率: {cpu_percent}%")
    if cpu_percent > 80:
        print("⚠️  CPU使用率过高")
```

#### 解决方案

1. **启用性能模式**
```python
# 使用高性能模板
router.apply_config_template('aggressive')

# 或调整阈值降低计算复杂度
router.update_routing_threshold('simple_max_complexity', 0.1)
router.update_routing_threshold('medium_max_complexity', 0.3)
```

2. **优化查询处理**
```python
# 启用查询缓存
from src.core.config_web_interface import ConfigImportExportManager
import_export = ConfigImportExportManager(router)
# 缓存会自动启用

# 减少并发数
router.set_max_concurrency(4)  # 默认8
```

3. **启用异步处理**
```python
# 对于大量查询，使用异步处理
import asyncio

async def process_queries_async(queries):
    # 异步批量处理
    results = await router.process_queries_batch_async(queries)
    return results
```

### 内存使用率过高

#### 症状
- 内存使用率持续 > 80%
- 频繁垃圾回收
- OutOfMemoryError

#### 诊断步骤
```python
import psutil
import gc

# 检查内存使用
memory = psutil.virtual_memory()
print(f"内存使用率: {memory.percent}%")
print(f"可用内存: {memory.available / 1024 / 1024:.1f}MB")

# 强制垃圾回收
gc.collect()
print(f"垃圾回收后内存: {psutil.virtual_memory().available / 1024 / 1024:.1f}MB")
```

#### 解决方案

1. **减少缓存大小**
```python
# 减少配置缓存
export CONFIG_CACHE_SIZE=50

# 清理查询缓存
router.clear_query_cache()
```

2. **启用内存监控**
```python
# 定期清理过期缓存
import threading

def memory_cleanup_worker():
    while True:
        time.sleep(300)  # 5分钟清理一次
        router.clear_expired_cache()
        gc.collect()

threading.Thread(target=memory_cleanup_worker, daemon=True).start()
```

3. **使用内存映射文件**
```python
# 对于大文件配置，使用内存映射
import mmap

def load_large_config(filename):
    with open(filename, 'r') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
            return json.loads(m.read().decode('utf-8'))
```

### 响应时间过长

#### 症状
- API响应时间 > 2秒
- 用户体验差

#### 诊断步骤
```python
import time
import requests

# 测试API响应时间
def test_api_response_time(url, iterations=10):
    times = []
    for _ in range(iterations):
        start_time = time.time()
        response = requests.get(url)
        end_time = time.time()
        times.append(end_time - start_time)

    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)

    print(f"平均响应时间: {avg_time:.3f}秒")
    print(f"最大响应时间: {max_time:.3f}秒")
    print(f"最小响应时间: {min_time:.3f}秒")

    return avg_time, max_time, min_time

# 测试各个端点
test_api_response_time('http://localhost:8080/api/config')
test_api_response_time('http://localhost:8080/api/metrics')
```

#### 解决方案

1. **启用响应缓存**
```python
# 为频繁查询启用缓存
@router.cache_response(ttl=60)  # 60秒缓存
def get_config():
    return router.get_routing_config()
```

2. **优化数据库查询**
```python
# 使用连接池
from src.core.database_pool import DatabasePool

db_pool = DatabasePool(min_connections=5, max_connections=20)
db_pool.optimize_for_read_heavy_workload()
```

3. **启用压缩**
```python
# 启用响应压缩
app.config['COMPRESS'] = True
app.config['COMPRESS_LEVEL'] = 6
```

## 配置问题

### 配置不生效

#### 症状
- 修改配置后没有变化
- 系统仍在使用旧配置

#### 诊断步骤
```python
# 检查当前配置
current_config = router.get_routing_config()
print("当前配置:", json.dumps(current_config, indent=2, ensure_ascii=False))

# 检查配置文件
with open('dynamic_config.json', 'r') as f:
    file_config = json.load(f)
print("文件配置:", json.dumps(file_config, indent=2, ensure_ascii=False))

# 比较差异
import deepdiff
diff = deepdiff.DeepDiff(current_config, file_config)
print("配置差异:", diff)
```

#### 解决方案

1. **触发配置重载**
```python
# 手动重载配置
router.reload_config()

# 或重启服务
router.restart_service()
```

2. **检查配置格式**
```python
# 验证配置格式
validator = ConfigValidator()
result = validator.validate(file_config)
if not result.is_valid:
    print("配置错误:", result.errors)
    # 修复配置错误
```

3. **检查文件权限**
```bash
# 检查文件权限
ls -la dynamic_config.json

# 修复权限
chmod 644 dynamic_config.json
```

### 配置冲突

#### 症状
- 多个配置源冲突
- 模板应用失败

#### 解决方案

1. **配置优先级管理**
```python
# 设置配置源优先级
config_sources = {
    'environment': 1,  # 最高优先级
    'file': 2,
    'database': 3,
    'default': 4       # 最低优先级
}

def merge_configs_with_priority(sources):
    """按优先级合并配置"""
    merged = {}
    for source_name, priority in sorted(config_sources.items(), key=lambda x: x[1]):
        if source_name in sources:
            merged = deep_merge(merged, sources[source_name])
    return merged
```

2. **冲突检测**
```python
def detect_config_conflicts(config1, config2):
    """检测配置冲突"""
    conflicts = []

    def check_conflicts(path, val1, val2):
        if isinstance(val1, dict) and isinstance(val2, dict):
            for key in set(val1.keys()) | set(val2.keys()):
                check_conflicts(f"{path}.{key}", val1.get(key), val2.get(key))
        elif val1 != val2:
            conflicts.append({
                'path': path,
                'value1': val1,
                'value2': val2
            })

    check_conflicts('root', config1, config2)
    return conflicts
```

## 网络问题

### 连接超时

#### 症状
- API调用超时
- Web界面无法访问

#### 诊断步骤
```bash
# 检查网络连接
ping localhost

# 检查端口监听
netstat -tlnp | grep :8080

# 测试连接
curl -v http://localhost:8080/health

# 检查防火墙
sudo ufw status
sudo iptables -L
```

#### 解决方案

1. **调整超时设置**
```python
# 增加超时时间
requests.get('http://localhost:8080/api/config', timeout=30)

# 配置客户端超时
router.set_client_timeout(30)  # 30秒
```

2. **启用连接池**
```python
# 使用连接池复用连接
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    backoff_factor=1
)

adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("http://", adapter)
http.mount("https://", adapter)
```

3. **负载均衡**
```python
# 配置多个后端服务器
backends = [
    'http://server1:8080',
    'http://server2:8080',
    'http://server3:8080'
]

def get_backend():
    """轮询负载均衡"""
    return backends[len(backends) % len(backends)]
```

### DNS解析失败

#### 症状
- 域名解析失败
- 连接建立失败

#### 解决方案

1. **配置DNS服务器**
```bash
# 检查DNS配置
cat /etc/resolv.conf

# 添加DNS服务器
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
echo "nameserver 1.1.1.1" >> /etc/resolv.conf
```

2. **使用IP地址**
```python
# 直接使用IP地址
config = ConfigAPIClient("http://127.0.0.1:8080")
```

3. **配置hosts文件**
```bash
# 添加hosts条目
echo "127.0.0.1 config.example.com" >> /etc/hosts
```

## 安全问题

### 认证失败

#### 症状
- 登录失败
- API访问被拒绝

#### 诊断步骤
```python
# 测试认证
try:
    api_client = ConfigAPIClient()
    result = api_client.login('admin', 'admin')
    print("认证结果:", result)
except Exception as e:
    print("认证错误:", e)

# 检查会话
session_id = api_client.session_id
if session_id:
    print("会话ID:", session_id)
    # 验证会话
    user = api_client.validate_session(session_id)
    print("会话用户:", user)
```

#### 解决方案

1. **重置管理员密码**
```python
# 重置管理员账户
from src.core.advanced_config_features import AccessControlManager

ac_manager = AccessControlManager()
ac_manager.reset_admin_password('new_password')
```

2. **检查账户状态**
```python
# 检查用户状态
user_info = ac_manager.users.get('admin')
if user_info:
    print("用户状态:", user_info.get('status'))
    print("用户角色:", user_info.get('role'))
```

3. **启用调试日志**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 重新尝试认证
result = api_client.login('admin', 'admin')
```

### 权限不足

#### 症状
- 操作被拒绝
- 403 Forbidden错误

#### 解决方案

1. **检查用户权限**
```python
# 检查当前用户权限
has_permission = ac_manager.check_permission('username', 'config.update')
print("有权限:", has_permission)

# 列出用户所有权限
user_permissions = ac_manager.get_user_permissions('username')
print("用户权限:", user_permissions)
```

2. **分配权限**
```python
# 分配角色
ac_manager.assign_role('username', 'operator')

# 或直接添加权限
ac_manager.add_user_permission('username', 'config.update')
```

3. **检查角色定义**
```python
# 验证角色权限
role_permissions = ac_manager.roles['operator']['permissions']
print("操作员权限:", role_permissions)
```

## 日志分析

### 日志级别设置

```python
import logging

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# 只记录错误
logging.basicConfig(level=logging.ERROR)
```

### 日志分析脚本

```python
#!/usr/bin/env python3
"""
日志分析工具
"""

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

def analyze_logs(log_file, hours=24):
    """分析日志文件"""

    # 统计数据
    error_count = 0
    warning_count = 0
    request_count = 0
    response_times = []
    errors_by_type = Counter()
    requests_by_endpoint = Counter()

    # 时间窗口
    cutoff_time = datetime.now() - timedelta(hours=hours)

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                # 解析日志行
                timestamp_str, level, message = parse_log_line(line)

                if not timestamp_str:
                    continue

                timestamp = datetime.fromisoformat(timestamp_str)

                # 检查时间窗口
                if timestamp < cutoff_time:
                    continue

                # 统计错误和警告
                if level == 'ERROR':
                    error_count += 1
                    # 提取错误类型
                    error_type = extract_error_type(message)
                    errors_by_type[error_type] += 1

                elif level == 'WARNING':
                    warning_count += 1

                # 统计API请求
                if 'API request' in message:
                    request_count += 1
                    endpoint = extract_endpoint(message)
                    requests_by_endpoint[endpoint] += 1

                # 提取响应时间
                response_time = extract_response_time(message)
                if response_time:
                    response_times.append(response_time)

            except Exception as e:
                print(f"解析日志行失败: {e}")
                continue

    # 生成报告
    report = {
        'time_window_hours': hours,
        'total_errors': error_count,
        'total_warnings': warning_count,
        'total_requests': request_count,
        'errors_by_type': dict(errors_by_type.most_common(10)),
        'requests_by_endpoint': dict(requests_by_endpoint.most_common(10)),
        'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
        'max_response_time': max(response_times) if response_times else 0,
        'min_response_time': min(response_times) if response_times else 0
    }

    return report

def parse_log_line(line):
    """解析日志行"""
    # 假设日志格式: 2024-01-15 10:30:00,123 - INFO - message
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (.+)'
    match = re.match(pattern, line.strip())

    if match:
        timestamp, level, message = match.groups()
        return timestamp, level, message

    return None, None, None

def extract_error_type(message):
    """提取错误类型"""
    if 'Timeout' in message:
        return 'timeout'
    elif 'Connection' in message:
        return 'connection'
    elif 'Validation' in message:
        return 'validation'
    elif 'Permission' in message:
        return 'permission'
    else:
        return 'unknown'

def extract_endpoint(message):
    """提取API端点"""
    # 从消息中提取端点，如 "GET /api/config"
    match = re.search(r'(GET|POST|PUT|DELETE)\s+(/[^\s]+)', message)
    if match:
        return match.group(2)
    return 'unknown'

def extract_response_time(message):
    """提取响应时间"""
    # 从消息中提取响应时间，如 "response_time=1.23s"
    match = re.search(r'response_time=([\d.]+)s', message)
    if match:
        return float(match.group(1))
    return None

if __name__ == '__main__':
    # 分析最近24小时的日志
    report = analyze_logs('config.log', hours=24)

    print("=== 日志分析报告 ===")
    print(f"时间窗口: {report['time_window_hours']}小时")
    print(f"错误总数: {report['total_errors']}")
    print(f"警告总数: {report['total_warnings']}")
    print(f"请求总数: {report['total_requests']}")
    print(f"平均响应时间: {report['avg_response_time']:.3f}秒")

    print("\n错误类型分布:")
    for error_type, count in report['errors_by_type'].items():
        print(f"  {error_type}: {count}")

    print("\nAPI端点访问分布:")
    for endpoint, count in report['requests_by_endpoint'].items():
        print(f"  {endpoint}: {count}")
```

### 运行日志分析
```bash
# 分析日志
python analyze_logs.py

# 查看最近的错误日志
tail -100 config.log | grep ERROR

# 统计错误类型
grep ERROR config.log | sed 's/.*ERROR//' | sort | uniq -c | sort -nr
```

## 紧急恢复

### 系统崩溃恢复

#### 1. 快速重启
```bash
# 强制重启服务
pkill -9 -f intelligent_router
sleep 2
python -m src.core.intelligent_router &

# 检查服务状态
curl http://localhost:8080/health
```

#### 2. 配置回滚
```python
# 紧急回滚到稳定版本
from src.core.dynamic_config_system import FileConfigStore

store = FileConfigStore('dynamic_config.json')

# 查找最近的稳定标签
stable_versions = [v for v in store.get_config_versions() if 'stable' in v]
if stable_versions:
    store.rollback_to_version(stable_versions[-1])
    print("已回滚到稳定版本")
```

#### 3. 数据恢复
```bash
# 从备份恢复
cp backup_20240115_100000/dynamic_config.json dynamic_config.json

# 验证配置
python -c "
import json
with open('dynamic_config.json') as f:
    config = json.load(f)
print('配置加载成功')
"
```

### 灾难恢复计划

#### 1. 备份策略
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/config_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR/$TIMESTAMP

# 备份配置文件
cp dynamic_config.json $BACKUP_DIR/$TIMESTAMP/
cp routing_config.json $BACKUP_DIR/$TIMESTAMP/

# 备份数据库
pg_dump config_db > $BACKUP_DIR/$TIMESTAMP/database.sql

# 备份日志
cp *.log $BACKUP_DIR/$TIMESTAMP/

# 压缩备份
tar -czf $BACKUP_DIR/backup_$TIMESTAMP.tar.gz -C $BACKUP_DIR $TIMESTAMP

# 清理旧备份（保留7天）
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete

echo "备份完成: backup_$TIMESTAMP.tar.gz"
```

#### 2. 恢复脚本
```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <备份文件>"
    exit 1
fi

# 停止服务
systemctl stop config-service

# 解压备份
tar -xzf $BACKUP_FILE -C /tmp/

# 恢复配置文件
cp /tmp/*/dynamic_config.json .
cp /tmp/*/routing_config.json .

# 恢复数据库
psql config_db < /tmp/*/database.sql

# 启动服务
systemctl start config-service

# 验证恢复
curl http://localhost:8080/health

echo "恢复完成"
```

#### 3. 监控告警集成

```python
# 集成监控告警
def setup_emergency_alerts():
    """设置紧急告警"""

    # CPU使用率告警
    alert_manager.add_alert_rule('high_cpu', {
        'name': 'CPU使用率过高',
        'severity': 'critical',
        'condition': 'cpu_percent > 95',
        'channels': ['email', 'sms'],
        'escalation': {
            'after_5min': 'manager',
            'after_15min': 'director'
        }
    })

    # 内存不足告警
    alert_manager.add_alert_rule('low_memory', {
        'name': '内存不足',
        'severity': 'critical',
        'condition': 'memory_percent > 95',
        'auto_recovery': True,
        'recovery_action': 'restart_service'
    })

    # 服务不可用告警
    alert_manager.add_alert_rule('service_down', {
        'name': '服务不可用',
        'severity': 'critical',
        'condition': 'health_check_failed',
        'channels': ['email', 'sms', 'webhook'],
        'escalation': {
            'after_1min': 'oncall_engineer',
            'after_5min': 'manager'
        }
    })

# 设置告警通道
alert_manager.add_alert_channel('sms', sms_sender)
alert_manager.add_alert_channel('email', email_sender)
alert_manager.add_alert_channel('webhook', webhook_sender)
```

### 联系支持

如果所有故障排除方法都无法解决问题，请：

1. **收集诊断信息**
```bash
# 生成完整诊断报告
./diagnose_system.py > diagnostic_report.txt
./health_check.sh >> diagnostic_report.txt
dmesg | tail -50 >> diagnostic_report.txt
```

2. **准备支持包**
```bash
# 创建支持包
SUPPORT_DIR="support_$(date +%Y%m%d_%H%M%S)"
mkdir $SUPPORT_DIR

# 收集日志和配置
cp *.log $SUPPORT_DIR/
cp *.json $SUPPORT_DIR/
cp diagnostic_report.txt $SUPPORT_DIR/

# 系统信息
uname -a > $SUPPORT_DIR/system_info.txt
python --version >> $SUPPORT_DIR/system_info.txt
pip list >> $SUPPORT_DIR/system_info.txt

# 压缩支持包
tar -czf ${SUPPORT_DIR}.tar.gz $SUPPORT_DIR
echo "支持包已创建: ${SUPPORT_DIR}.tar.gz"
```

3. **联系技术支持**
- 发送支持包到: support@config-system.com
- 提供问题描述和重现步骤
- 说明系统环境和配置

---

**最后更新**: 2024-01-15
**版本**: 1.0.0
