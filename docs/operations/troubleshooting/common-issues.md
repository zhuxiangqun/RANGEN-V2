# 📋 常见问题解答 (FAQ)

本文档列出了RANGEN系统使用过程中常见的故障和问题，并提供详细的解决方案。

## 🔍 快速索引

| 类别 | 问题 | 快速链接 |
|------|------|----------|
| 启动问题 | 端口被占用 | [🔗](#端口被占用) |
| 启动问题 | 依赖安装失败 | [🔗](#依赖安装失败) |
| 启动问题 | 配置文件缺失 | [🔗](#配置文件缺失) |
| API问题 | API认证失败 | [🔗](#api认证失败) |
| API问题 | 请求超时 | [🔗](#请求超时) |
| 模型问题 | 模型调用失败 | [🔗](#模型调用失败) |
| 模型问题 | Step-3.5-Flash连接失败 | [🔗](#step-35-flash连接失败) |
| 性能问题 | 响应时间过长 | [🔗](#响应时间过长) |
| 性能问题 | 内存使用率过高 | [🔗](#内存使用率过高) |
| 配置问题 | 配置不生效 | [🔗](#配置不生效) |
| 监控问题 | 监控面板无数据 | [🔗](#监控面板无数据) |
| 数据问题 | 知识库检索失败 | [🔗](#知识库检索失败) |

---

## 🚀 启动问题

### 端口被占用

**错误信息**：
```
Error: [Errno 48] Address already in use
Failed to bind to 0.0.0.0:8000
```

**原因分析**：
- 端口8000（默认API端口）或7860（Streamlit UI端口）已被其他进程占用
- 之前的RANGEN进程未正常退出

**解决方案**：

**方案1：查找并终止占用进程**
```bash
# 查找占用8000端口的进程
lsof -i :8000

# 查找占用7860端口的进程  
lsof -i :7860

# 终止进程（将<PID>替换为实际进程ID）
kill -9 <PID>
```

**方案2：使用不同端口启动**
```bash
# 修改端口启动API服务器
export RANGEN_API_PORT=8001
python src/api/server.py

# 或修改Streamlit端口
streamlit run src/ui/app.py --server.port 7861
```

**方案3：配置持久化解决方案**
创建配置文件 `config/ports.yaml`：
```yaml
api:
  port: 8001
  host: "0.0.0.0"
  
ui:
  streamlit_port: 7861
  host: "0.0.0.0"
  
monitoring:
  port: 9090
  host: "localhost"
```

### 依赖安装失败

**错误信息**：
```
ERROR: Could not find a version that satisfies the requirement...
ERROR: No matching distribution found for...
ImportError: No module named '...'
```

**原因分析**：
- Python版本不兼容（需要Python 3.9+）
- pip版本过旧
- 网络问题导致下载失败
- 系统缺少编译依赖

**解决方案**：

**方案1：升级pip和setuptools**
```bash
# 升级pip
python -m pip install --upgrade pip

# 升级setuptools
pip install --upgrade setuptools wheel

# 清除缓存
pip cache purge
```

**方案2：使用镜像源安装**
```bash
# 使用清华镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用阿里云镜像源
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

**方案3：分步安装核心依赖**
```bash
# 先安装基础依赖
pip install fastapi uvicorn pydantic

# 再安装AI相关依赖
pip install langchain langgraph openai

# 最后安装其他依赖
pip install -r requirements.txt --no-deps
```

**方案4：检查Python版本**
```bash
# 检查Python版本
python --version

# 如果版本低于3.9，需要升级
# 推荐使用conda或pyenv管理Python版本

# 使用conda创建Python 3.9环境
conda create -n rangen python=3.9
conda activate rangen

# 使用pyenv
pyenv install 3.9.18
pyenv local 3.9.18
```

### 配置文件缺失

**错误信息**：
```
FileNotFoundError: .env file not found
KeyError: 'RANGEN_API_KEY'
ConfigurationError: Missing required configuration
```

**原因分析**：
- `.env`环境变量文件未创建
- 配置文件模板未复制
- 配置目录权限问题

**解决方案**：

**方案1：创建基础配置文件**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
echo "RANGEN_API_KEY=your-api-key-here" >> .env
echo "DEEPSEEK_API_KEY=your-deepseek-key-here" >> .env
echo "OPENAI_API_KEY=your-openai-key-here" >> .env
echo "STEPSFLASH_API_KEY=your-stepflash-key-here" >> .env

# 设置权限
chmod 600 .env
```

**方案2：生成最小配置**
创建 `config/minimal_config.yaml`：
```yaml
api:
  port: 8000
  host: "0.0.0.0"
  debug: true

models:
  default: "step-3.5-flash"
  enabled:
    - "step-3.5-flash"
    - "deepseek-chat"
    - "local-llama"
  
logging:
  level: "INFO"
  file: "logs/rangen.log"
```

**方案3：验证配置完整性**
```bash
# 运行配置验证脚本
python scripts/validate_config.py

# 输出示例
# ✅ 环境变量检查通过
# ✅ 模型配置检查通过  
# ✅ 数据库配置检查通过
# ⚠️  监控配置部分缺失（不影响启动）
```

---

## 🔌 API问题

### API认证失败

**错误信息**：
```
401 Unauthorized
{"detail":"Invalid API key"}
403 Forbidden  
{"detail":"Insufficient permissions"}
```

**原因分析**：
- API密钥未设置或设置错误
- 密钥权限不足
- 请求头格式错误

**解决方案**：

**方案1：检查API密钥配置**
```bash
# 检查环境变量
echo $RANGEN_API_KEY
echo $DEEPSEEK_API_KEY
echo $STEPSFLASH_API_KEY

# 如果没有设置，重新设置
export RANGEN_API_KEY="your-actual-api-key"
export DEEPSEEK_API_KEY="your-deepseek-key"
export STEPSFLASH_API_KEY="your-stepflash-key"

# 永久保存到.env文件
echo 'RANGEN_API_KEY="your-actual-api-key"' >> .env
```

**方案2：测试API密钥有效性**
```python
# 测试脚本 test_api_keys.py
import os
import requests

def test_api_key(api_key, endpoint="https://api.openai.com/v1/models"):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        if response.status_code == 200:
            return True, "API密钥有效"
        else:
            return False, f"API密钥无效: HTTP {response.status_code}"
    except Exception as e:
        return False, f"API密钥测试失败: {str(e)}"

# 测试各个API密钥
keys_to_test = [
    ("OpenAI", os.getenv("OPENAI_API_KEY")),
    ("DeepSeek", os.getenv("DEEPSEEK_API_KEY")),
    ("Step-3.5-Flash", os.getenv("STEPSFLASH_API_KEY"))
]

for name, key in keys_to_test:
    if key:
        valid, message = test_api_key(key)
        print(f"{name}: {message}")
    else:
        print(f"{name}: 密钥未设置")
```

**方案3：使用正确的认证头格式**
```python
# 正确的请求头格式
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "X-API-Key": api_key,  # 部分服务需要这个头
    "Accept": "application/json"
}

# RANGEN特定的认证头
headers = {
    "X-RANGEN-API-KEY": api_key,
    "Content-Type": "application/json"
}
```

### 请求超时

**错误信息**：
```
TimeoutError: The request timed out
requests.exceptions.Timeout: HTTPConnectionPool...
408 Request Timeout
```

**原因分析**：
- 网络连接不稳定
- 服务器负载过高
- 请求处理时间过长
- 超时设置过短

**解决方案**：

**方案1：调整超时设置**
```python
# 增加请求超时时间
import requests

# 默认超时设置
response = requests.get(
    "http://localhost:8000/api/health",
    timeout=30  # 30秒超时
)

# 分连接超时和读取超时
response = requests.get(
    "http://localhost:8000/api/health",
    timeout=(5, 30)  # 连接超时5秒，读取超时30秒
)
```

**方案2：配置重试机制**
```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置重试策略
retry_strategy = Retry(
    total=3,  # 总重试次数
    backoff_factor=1,  # 退避因子
    status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
)

# 创建会话并配置适配器
session = requests.Session()
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# 使用会话发送请求
response = session.get("http://localhost:8000/api/health", timeout=10)
```

**方案3：优化服务器配置**
```yaml
# config/server_config.yaml
server:
  timeout:
    request: 60  # 请求超时60秒
    keepalive: 5  # 保持连接5秒
    shutdown: 30  # 关闭超时30秒
    
  workers: 4  # 工作进程数
  max_requests: 1000  # 最大请求数
  max_requests_jitter: 100  # 最大请求抖动
```

---

## 🤖 模型问题

### 模型调用失败

**错误信息**：
```
ModelNotAvailableError: Model 'deepseek-chat' is not available
LLMCallError: Failed to call LLM API
RateLimitError: Rate limit exceeded
```

**原因分析**：
- 模型服务不可用
- API配额用尽
- 网络连接问题
- 模型配置错误

**解决方案**：

**方案1：检查模型服务状态**
```bash
# 检查模型API端点
curl -X GET "https://api.deepseek.com/v1/models" \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"

curl -X GET "https://openrouter.ai/api/v1/models" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# 检查本地模型服务
curl http://localhost:8001/v1/models
```

**方案2：启用模型降级策略**
```python
# 配置模型降级策略
from src.services.intelligent_model_router import IntelligentModelRouter

router = IntelligentModelRouter()

# 设置降级策略
router.set_fallback_strategy({
    "primary": "deepseek-chat",      # 首选模型
    "fallback1": "step-3.5-flash",   # 第一备选
    "fallback2": "local-llama",      # 第二备选
    "fallback3": "gpt-3.5-turbo"     # 最终备选
})

# 启用自动降级
router.enable_auto_fallback(True)
```

**方案3：监控模型使用情况**
```python
# 监控模型使用统计
from src.services.token_cost_monitor import TokenCostMonitor

monitor = TokenCostMonitor()

# 获取模型使用统计
stats = monitor.get_model_usage_stats()

print("模型使用统计:")
for model, data in stats.items():
    print(f"{model}:")
    print(f"  调用次数: {data['calls']}")
    print(f"  成功次数: {data['success']}")
    print(f"  失败次数: {data['failures']}")
    print(f"  平均延迟: {data['avg_latency']:.2f}s")
    
# 设置告警阈值
monitor.set_alert_thresholds({
    "deepseek-chat": {
        "daily_limit": 1000,  # 每日1000次
        "cost_limit": 50.0,   # 每日50美元
        "error_rate": 0.1     # 错误率10%
    }
})
```

### Step-3.5-Flash连接失败

**错误信息**：
```
StepFlashConnectionError: Failed to connect to Step-3.5-Flash
OpenRouterError: Invalid API key for Step-3.5-Flash
```

**原因分析**：
- OpenRouter API密钥无效
- NVIDIA NIM服务未启动
- vLLM本地部署配置错误
- 网络防火墙限制

**解决方案**：

**方案1：检查Step-3.5-Flash配置**
```bash
# 检查环境变量
echo $STEPSFLASH_API_KEY
echo $STEPSFLASH_DEPLOYMENT_TYPE

# 验证OpenRouter API密钥
curl -X GET "https://openrouter.ai/api/v1/auth/key" \
  -H "Authorization: Bearer $STEPSFLASH_API_KEY"
```

**方案2：配置多种部署方式**
```python
# config/models/stepflash_config.yaml
stepflash:
  deployment_type: "openrouter"  # openrouter, nvidia_nim, vllm_local
  
  openrouter:
    api_key: "${STEPSFLASH_API_KEY}"
    base_url: "https://openrouter.ai/api/v1"
    model_id: "stepfun/step-3.5-flash"
    
  nvidia_nim:
    base_url: "https://api.nvcf.nvidia.com/v2/nvcf"
    model_id: "stepfun/step-3.5-flash"
    api_key: "${NVIDIA_API_KEY}"
    
  vllm_local:
    base_url: "http://localhost:8000/v1"
    model_id: "stepfun/step-3.5-flash"
```

**方案3：测试不同部署方式**
```python
from src.services.stepflash_adapter import StepFlashAdapter, StepFlashDeploymentType

# 测试OpenRouter连接
adapter1 = StepFlashAdapter(
    deployment_type=StepFlashDeploymentType.OPENROUTER,
    api_key=os.getenv("STEPSFLASH_API_KEY")
)

# 测试本地vLLM连接
adapter2 = StepFlashAdapter(
    deployment_type=StepFlashDeploymentType.VLLM_LOCAL,
    base_url="http://localhost:8000/v1"
)

# 测试连接
for name, adapter in [("OpenRouter", adapter1), ("vLLM Local", adapter2)]:
    try:
        response = adapter.call_llm("Hello, are you working?")
        print(f"{name}: ✅ 连接成功 - {response[:50]}...")
    except Exception as e:
        print(f"{name}: ❌ 连接失败 - {str(e)}")
```

---

## ⚡ 性能问题

### 响应时间过长

**错误信息**：
```
请求处理时间超过10秒
API响应时间P95 > 5秒
用户体验缓慢
```

**原因分析**：
- 模型调用延迟高
- 知识库检索慢
- 系统负载过高
- 网络延迟大

**解决方案**：

**方案1：启用响应缓存**
```python
# 配置缓存策略
from src.core.cache_system import CacheSystem

cache = CacheSystem()

# 启用模型响应缓存
cache.enable_model_response_cache(
    ttl=300,  # 5分钟缓存
    max_size=1000  # 最大1000条缓存
)

# 启用知识库缓存
cache.enable_knowledge_cache(
    ttl=3600,  # 1小时缓存
    max_size=5000  # 最大5000条缓存
)
```

**方案2：优化模型路由**
```python
# 配置智能模型路由
from src.services.intelligent_model_router import IntelligentModelRouter

router = IntelligentModelRouter()

# 基于复杂度路由
router.configure_complexity_based_routing({
    "simple": {
        "model": "step-3.5-flash",
        "max_tokens": 500,
        "timeout": 5
    },
    "medium": {
        "model": "local-llama",
        "max_tokens": 1000,
        "timeout": 10
    },
    "complex": {
        "model": "deepseek-chat",
        "max_tokens": 2000,
        "timeout": 30
    }
})
```

**方案3：实施性能监控**
```bash
# 监控API性能
curl -X GET "http://localhost:8000/api/metrics"

# 使用性能分析工具
python -m cProfile -o profile.stats src/api/server.py

# 分析性能数据
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"
```

### 内存使用率过高

**错误信息**：
```
MemoryError: Out of memory
系统内存使用率 > 80%
频繁的垃圾回收
```

**原因分析**：
- 内存泄漏
- 缓存过大
- 并发请求过多
- 模型加载占用内存

**解决方案**：

**方案1：优化内存配置**
```yaml
# config/memory_config.yaml
memory:
  limits:
    total_mb: 4096  # 总内存限制4GB
    cache_mb: 1024  # 缓存内存限制1GB
    model_mb: 2048  # 模型内存限制2GB
    
  garbage_collection:
    enabled: true
    threshold: 0.7  # 内存使用70%时触发GC
    interval: 300   # 每5分钟检查一次
    
  model_loading:
    lazy_loading: true  # 延迟加载模型
    unload_idle_models: true  # 卸载空闲模型
    idle_timeout: 600  # 10分钟空闲后卸载
```

**方案2：实施内存监控**
```python
# 内存监控脚本
import psutil
import time
import logging

logger = logging.getLogger(__name__)

class MemoryMonitor:
    def __init__(self, threshold=0.8):
        self.threshold = threshold
        self.alert_count = 0
        
    def monitor_memory(self):
        memory = psutil.virtual_memory()
        
        if memory.percent > self.threshold * 100:
            self.alert_count += 1
            logger.warning(
                f"内存使用率过高: {memory.percent}% "
                f"(已用: {memory.used/1024/1024:.1f}MB, "
                f"可用: {memory.available/1024/1024:.1f}MB)"
            )
            
            if self.alert_count >= 3:
                self.take_action()
                
        return memory.percent
        
    def take_action(self):
        logger.critical("内存使用持续过高，采取紧急措施")
        
        # 清理缓存
        self.clear_caches()
        
        # 重启服务
        self.restart_service()
        
    def clear_caches(self):
        # 清理各种缓存
        import gc
        gc.collect()
        
        # 清理模型缓存
        from src.core.cache_system import get_cache_system
        cache = get_cache_system()
        cache.clear_expired()
        
    def restart_service(self):
        # 优雅重启服务
        import subprocess
        subprocess.run(["pkill", "-f", "server.py"])
        time.sleep(2)
        subprocess.Popen(["python", "src/api/server.py"])
```

---

## ⚙️ 配置问题

### 配置不生效

**错误信息**：
```
配置修改后无变化
系统仍使用旧配置
配置验证失败
```

**原因分析**：
- 配置未重新加载
- 配置文件格式错误
- 配置优先级问题
- 配置缓存未清除

**解决方案**：

**方案1：强制重新加载配置**
```bash
# 发送配置重载信号
curl -X POST "http://localhost:8000/api/config/reload" \
  -H "X-RANGEN-API-KEY: $RANGEN_API_KEY"

# 重启服务使配置生效
pkill -f "server.py"
sleep 2
python src/api/server.py &
```

**方案2：验证配置文件格式**
```python
# 配置验证脚本
import yaml
import json
import sys

def validate_config(file_path):
    with open(file_path, 'r') as f:
        if file_path.endswith('.yaml') or file_path.endswith('.yml'):
            try:
                config = yaml.safe_load(f)
                print(f"✅ YAML配置文件格式正确: {file_path}")
                return config
            except yaml.YAMLError as e:
                print(f"❌ YAML配置文件格式错误: {file_path}")
                print(f"   错误信息: {e}")
                return None
        elif file_path.endswith('.json'):
            try:
                config = json.load(f)
                print(f"✅ JSON配置文件格式正确: {file_path}")
                return config
            except json.JSONDecodeError as e:
                print(f"❌ JSON配置文件格式错误: {file_path}")
                print(f"   错误信息: {e}")
                return None

# 验证所有配置文件
config_files = [
    ".env",
    "config/models.yaml",
    "config/server.yaml", 
    "config/monitoring.yaml"
]

for config_file in config_files:
    validate_config(config_file)
```

---

## 📊 监控问题

### 监控面板无数据

**错误信息**：
```
监控面板显示"No data"
Prometheus指标为空
Grafana面板无数据
```

**原因分析**：
- 监控服务未启动
- 指标收集配置错误
- 数据源连接失败
- 权限问题

**解决方案**：

**方案1：检查监控服务状态**
```bash
# 检查Prometheus状态
curl http://localhost:9090/-/healthy

# 检查Grafana状态
curl http://localhost:3000/api/health

# 检查指标端点
curl http://localhost:8000/metrics

# 检查OpenTelemetry收集器
curl http://localhost:4318/health
```

**方案2：启用详细监控日志**
```yaml
# config/monitoring.yaml
logging:
  level: "DEBUG"
  format: "json"
  
metrics:
  enabled: true
  port: 9090
  path: "/metrics"
  
tracing:
  enabled: true
  exporter: "jaeger"  # jaeger, zipkin, otlp
  endpoint: "http://localhost:14268/api/traces"
```

---

## 🗃️ 数据问题

### 知识库检索失败

**错误信息**：
```
KnowledgeRetrievalError: Failed to retrieve from knowledge base
VectorDBNotFoundError: Vector database not initialized
RAGPipelineError: Retrieval pipeline failed
```

**原因分析**：
- 向量数据库未启动
- 知识库索引损坏
- 检索参数配置错误
- 网络连接问题

**解决方案**：

**方案1：检查向量数据库状态**
```bash
# 检查ChromaDB状态
curl http://localhost:8000/api/v1/heartbeat

# 检查FAISS索引文件
ls -la data/vector_db/
ls -la data/faiss_index/

# 重建知识库索引
python scripts/rebuild_knowledge_index.py --force
```

**方案2：配置备用检索策略**
```python
# 配置多重检索策略
from src.core.reasoning.retrieval_strategies import (
    DirectRetrievalStrategy,
    HyDERetrievalStrategy,
    CoTRetrievalStrategy
)

# 创建策略链
retrieval_chain = [
    DirectRetrievalStrategy(top_k=5),     # 直接检索
    HyDERetrievalStrategy(top_k=3),       # HyDE检索
    CoTRetrievalStrategy(top_k=2)         # CoT检索
]

# 启用混合检索
from src.core.reasoning.query_orchestrator import QueryOrchestrator
orchestrator = QueryOrchestrator(retrieval_chain)
```

---

## 📞 获取更多帮助

如果上述解决方案无法解决您的问题，请：

1. **收集诊断信息**：
```bash
# 运行系统诊断
python scripts/diagnose_system.py > diagnosis_report.txt

# 收集日志
tail -n 1000 logs/rangen.log > recent_logs.txt
```

2. **提交问题报告**：
   - 访问GitHub Issues页面
   - 提供详细的错误信息和复现步骤
   - 附上诊断报告和日志文件

3. **联系技术支持**：
   - 邮箱：support@rangen.ai
   - 社区论坛：https://community.rangen.ai
   - Discord频道：https://discord.gg/rangen

---

**最后更新**: 2026-03-07  
**文档版本**: 1.0.0  
**维护团队**: RANGEN技术支持组