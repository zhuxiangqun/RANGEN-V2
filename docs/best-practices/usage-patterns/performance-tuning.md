# ⚡ 性能调优建议

> RANGEN 系统性能优化的方法和实践指南

## 🎯 概述

RANGEN 系统是一个复杂的多智能体系统，性能优化涉及多个层面：从单个请求的响应时间到整个系统的吞吐量，从内存使用效率到并发处理能力。本指南提供全面的性能调优建议，帮助您优化系统性能。

### 1.1 性能优化的核心价值
- **用户体验提升**: 减少响应时间，提高系统响应性
- **资源效率优化**: 提高硬件资源利用率，降低运营成本
- **系统扩展性增强**: 支持更高的并发和更大的负载
- **业务连续性保障**: 通过性能优化提高系统稳定性

### 1.2 目标读者
- 系统管理员和运维工程师
- 性能优化专家和架构师
- 开发团队和技术负责人
- 希望提升系统性能的所有用户

## 📊 性能指标体系

### 2.1 关键性能指标 (KPIs)

#### 2.1.1 响应时间指标
```python
from src.services.metrics_service import MetricsCollector, MetricDefinition, MetricCategory, MetricUnit

# 定义性能指标
response_time_metrics = [
    MetricDefinition(
        name="request_latency_p95",
        category=MetricCategory.PERFORMANCE,
        unit=MetricUnit.MS,
        description="95%请求的响应时间",
        v3_target=1000.0,  # 目标：< 1秒
        v3_baseline=2000.0  # 基准：2秒
    ),
    MetricDefinition(
        name="request_latency_p99",
        category=MetricCategory.PERFORMANCE,
        unit=MetricUnit.MS,
        description="99%请求的响应时间",
        v3_target=2000.0,  # 目标：< 2秒
        v3_baseline=5000.0  # 基准：5秒
    ),
    MetricDefinition(
        name="first_token_latency",
        category=MetricCategory.PERFORMANCE,
        unit=MetricUnit.MS,
        description="首Token响应时间",
        v3_target=500.0,    # 目标：< 500ms
        v3_baseline=1000.0  # 基准：1秒
    )
]
```

#### 2.1.2 吞吐量指标
```python
throughput_metrics = [
    MetricDefinition(
        name="requests_per_second",
        category=MetricCategory.PERFORMANCE,
        unit=MetricUnit.COUNT,
        description="每秒请求数",
        v3_target=100.0,    # 目标：100 RPS
        v3_baseline=50.0    # 基准：50 RPS
    ),
    MetricDefinition(
        name="tokens_per_second",
        category=MetricCategory.PERFORMANCE,
        unit=MetricUnit.COUNT,
        description="每秒处理Token数",
        v3_target=50000.0,  # 目标：50K tokens/s
        v3_baseline=20000.0  # 基准：20K tokens/s
    ),
    MetricDefinition(
        name="concurrent_sessions",
        category=MetricCategory.PERFORMANCE,
        unit=MetricUnit.COUNT,
        description="并发会话数",
        v3_target=1000.0,   # 目标：1000并发
        v3_baseline=500.0   # 基准：500并发
    )
]
```

#### 2.1.3 资源利用率指标
```python
resource_metrics = [
    MetricDefinition(
        name="cpu_utilization",
        category=MetricCategory.SYSTEM_HEALTH,
        unit=MetricUnit.PERCENT,
        description="CPU利用率",
        v3_target=70.0,     # 目标：< 70%
        v3_baseline=90.0    # 基准：90%
    ),
    MetricDefinition(
        name="memory_utilization",
        category=MetricCategory.SYSTEM_HEALTH,
        unit=MetricUnit.PERCENT,
        description="内存利用率",
        v3_target=80.0,     # 目标：< 80%
        v3_baseline=95.0    # 基准：95%
    ),
    MetricDefinition(
        name="gpu_utilization",
        category=MetricCategory.SYSTEM_HEALTH,
        unit=MetricUnit.PERCENT,
        description="GPU利用率",
        v3_target=85.0,     # 目标：< 85%
        v3_baseline=100.0   # 基准：100%
    )
]
```

### 2.2 性能基准参考值

| 指标 | 优秀 | 良好 | 需要优化 | 严重问题 |
|------|------|------|----------|----------|
| P95响应时间 | < 1秒 | 1-3秒 | 3-5秒 | > 5秒 |
| P99响应时间 | < 2秒 | 2-5秒 | 5-10秒 | > 10秒 |
| 首Token延迟 | < 500ms | 500ms-1s | 1-2秒 | > 2秒 |
| 请求成功率 | > 99.9% | 99-99.9% | 95-99% | < 95% |
| 系统可用性 | > 99.99% | 99.9-99.99% | 99-99.9% | < 99% |
| CPU利用率 | < 70% | 70-85% | 85-95% | > 95% |
| 内存利用率 | < 80% | 80-90% | 90-95% | > 95% |

## 🚀 核心优化策略

### 3.1 智能模型路由优化

#### 3.1.1 基于性能预测的路由
```python
from src.services.intelligent_model_router import IntelligentModelRouter, TaskContext, TaskType

class PerformanceOptimizedRouter:
    def __init__(self):
        self.router = IntelligentModelRouter()
        self.performance_history = {}
        self.fallback_strategy = self.create_fallback_strategy()
    
    async def route_for_performance(self, task: Dict) -> str:
        """基于性能预测的路由决策"""
        # 分析任务特征
        task_context = self.analyze_task_context(task)
        
        # 获取可用模型
        available_models = self.get_available_models()
        
        # 预测各模型性能
        predictions = []
        for model in available_models:
            prediction = await self.router.predict_performance(model, task_context)
            predictions.append((model, prediction))
        
        # 选择性能最优的模型
        predictions.sort(key=lambda x: x[1].predicted_latency_ms)
        best_model = predictions[0][0]
        
        # 记录路由决策
        self.record_routing_decision(task, best_model, predictions)
        
        return best_model
    
    def analyze_task_context(self, task: Dict) -> TaskContext:
        """分析任务上下文"""
        return TaskContext(
            task_type=self.detect_task_type(task),
            estimated_tokens=self.estimate_token_count(task),
            priority=task.get('priority', 5),
            deadline_ms=task.get('deadline'),
            metadata=task.get('metadata', {})
        )
    
    def detect_task_type(self, task: Dict) -> TaskType:
        """检测任务类型"""
        content = task.get('content', '').lower()
        
        if 'reason' in content or 'why' in content or 'explain' in content:
            return TaskType.REASONING
        elif 'code' in content or 'program' in content or 'function' in content:
            return TaskType.CODE_GENERATION
        elif 'summar' in content or 'brief' in content:
            return TaskType.SUMMARIZATION
        elif 'translate' in content or '语言' in content:
            return TaskType.TRANSLATION
        elif 'analyze' in content or '分析' in content:
            return TaskType.ANALYTICAL
        else:
            return TaskType.GENERAL
```

#### 3.1.2 负载均衡策略
```python
class LoadBalancedRouter:
    """负载均衡路由器"""
    
    def __init__(self, models: List[str]):
        self.models = models
        self.model_load = {model: 0 for model in models}
        self.model_capacity = {model: 100 for model in models}  # 默认容量
        self.model_performance = {model: 1.0 for model in models}
        self.lock = threading.RLock()
    
    def select_model(self, task_complexity: float = 1.0) -> str:
        """选择负载最低的模型"""
        with self.lock:
            # 计算各模型的综合分数
            scores = {}
            for model in self.models:
                # 负载分数（越低越好）
                load_score = self.model_load[model] / self.model_capacity[model]
                
                # 性能分数（越高越好）
                perf_score = 1.0 / self.model_performance[model]
                
                # 综合分数 = 负载权重 * 负载分数 + 性能权重 * 性能分数
                total_score = 0.7 * load_score + 0.3 * perf_score
                
                # 考虑任务复杂度
                if task_complexity > 1.5:
                    # 复杂任务偏向高性能模型
                    total_score *= 0.8
                
                scores[model] = total_score
            
            # 选择综合分数最低的模型
            selected = min(scores.items(), key=lambda x: x[1])[0]
            
            # 更新负载
            self.model_load[selected] += task_complexity
            
            return selected
    
    def update_model_performance(self, model: str, latency_ms: float, success: bool):
        """更新模型性能数据"""
        with self.lock:
            # 更新性能指标（滑动平均）
            if success:
                new_perf = min(latency_ms, 10000)  # 限制最大值
                old_perf = self.model_performance[model]
                self.model_performance[model] = 0.9 * old_perf + 0.1 * new_perf
            else:
                # 失败时性能下降
                self.model_performance[model] *= 1.2
    
    def release_model_load(self, model: str, task_complexity: float):
        """释放模型负载"""
        with self.lock:
            if model in self.model_load:
                self.model_load[model] = max(0, self.model_load[model] - task_complexity)
```

### 3.2 并发处理优化

#### 3.2.1 异步处理架构
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

class AsyncPerformanceOptimizer:
    """异步性能优化器"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or (os.cpu_count() * 2)
        self.thread_executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=min(4, os.cpu_count()))
        self.semaphore = asyncio.Semaphore(self.max_workers)
        self.metrics_collector = MetricsCollector()
    
    async def process_requests_concurrently(self, requests: List[Dict]) -> List[Dict]:
        """并发处理多个请求"""
        # 分组请求：IO密集型 vs CPU密集型
        io_bound, cpu_bound = self.classify_requests(requests)
        
        # 并行处理IO密集型任务
        io_tasks = []
        for request in io_bound:
            task = asyncio.create_task(
                self.process_io_bound_request(request, self.semaphore)
            )
            io_tasks.append(task)
        
        # 并行处理CPU密集型任务
        cpu_tasks = []
        for request in cpu_bound:
            task = asyncio.create_task(
                self.run_in_process_pool(self.process_cpu_bound_request, request)
            )
            cpu_tasks.append(task)
        
        # 等待所有任务完成
        io_results = await asyncio.gather(*io_tasks, return_exceptions=True)
        cpu_results = await asyncio.gather(*cpu_tasks, return_exceptions=True)
        
        # 合并结果
        results = self.merge_results(io_results, cpu_results, requests)
        
        # 收集性能指标
        await self.collect_performance_metrics(results)
        
        return results
    
    def classify_requests(self, requests: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """分类请求类型"""
        io_bound = []
        cpu_bound = []
        
        for request in requests:
            if self.is_io_bound(request):
                io_bound.append(request)
            else:
                cpu_bound.append(request)
        
        return io_bound, cpu_bound
    
    def is_io_bound(self, request: Dict) -> bool:
        """判断是否为IO密集型请求"""
        content = request.get('content', '')
        
        # IO密集型特征
        io_indicators = [
            'search', 'query', 'fetch', 'retrieve', 'read',
            'lookup', 'find', 'get', 'load'
        ]
        
        for indicator in io_indicators:
            if indicator in content.lower():
                return True
        
        # CPU密集型特征
        cpu_indicators = [
            'calculate', 'compute', 'process', 'analyze',
            'generate', 'create', 'build', 'train'
        ]
        
        for indicator in cpu_indicators:
            if indicator in content.lower():
                return False
        
        # 默认视为IO密集型
        return True
    
    async def process_io_bound_request(self, request: Dict, semaphore: asyncio.Semaphore) -> Dict:
        """处理IO密集型请求"""
        async with semaphore:
            start_time = time.time()
            
            try:
                # 模拟IO操作
                await asyncio.sleep(0.01)  # 模拟网络延迟
                
                # 处理请求
                result = await self.handle_io_request(request)
                
                # 记录性能指标
                latency = (time.time() - start_time) * 1000
                self.metrics_collector.record_metric(
                    'io_request_latency', latency, {'request_type': 'io_bound'}
                )
                
                return result
            except Exception as e:
                logger.error(f"IO请求处理失败: {e}")
                return {'error': str(e), 'success': False}
    
    async def run_in_process_pool(self, func, *args):
        """在进程池中运行CPU密集型函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.process_executor, func, *args)
```

#### 3.2.2 连接池管理
```python
class ConnectionPoolManager:
    """连接池管理器"""
    
    def __init__(self, max_connections: int = 100, max_idle_time: int = 300):
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.pools = {}
        self.metrics = {}
        self.cleanup_task = None
        
    async def initialize(self):
        """初始化连接池"""
        # 创建各服务的连接池
        services = ['llm_service', 'vector_db', 'cache_service', 'metrics_service']
        
        for service in services:
            pool = await self.create_connection_pool(service)
            self.pools[service] = pool
            self.metrics[service] = {
                'total_connections': 0,
                'active_connections': 0,
                'idle_connections': 0,
                'connection_errors': 0,
                'avg_wait_time': 0
            }
        
        # 启动连接清理任务
        self.cleanup_task = asyncio.create_task(self.cleanup_idle_connections())
    
    async def create_connection_pool(self, service: str) -> Dict:
        """创建连接池"""
        if service == 'llm_service':
            return await self.create_llm_connection_pool()
        elif service == 'vector_db':
            return await self.create_vector_db_pool()
        elif service == 'cache_service':
            return await self.create_cache_pool()
        else:
            return await self.create_generic_pool(service)
    
    async def get_connection(self, service: str, timeout: float = 5.0) -> Any:
        """获取连接"""
        if service not in self.pools:
            raise ValueError(f"未知的服务: {service}")
        
        pool = self.pools[service]
        start_time = time.time()
        
        try:
            # 尝试从池中获取连接
            connection = await asyncio.wait_for(
                self.acquire_from_pool(pool),
                timeout=timeout
            )
            
            # 更新指标
            wait_time = (time.time() - start_time) * 1000
            self.update_metrics(service, 'acquire', wait_time, success=True)
            
            return connection
        except asyncio.TimeoutError:
            self.update_metrics(service, 'acquire', timeout*1000, success=False)
            raise ConnectionError(f"获取{service}连接超时")
        except Exception as e:
            self.update_metrics(service, 'acquire', 0, success=False)
            raise
    
    async def release_connection(self, service: str, connection: Any):
        """释放连接"""
        if service not in self.pools:
            return
        
        pool = self.pools[service]
        
        try:
            # 检查连接是否健康
            if await self.is_connection_healthy(connection):
                await self.release_to_pool(pool, connection)
                self.update_metrics(service, 'release', 0, success=True)
            else:
                # 不健康的连接，关闭并创建新的
                await self.close_connection(connection)
                self.update_metrics(service, 'release', 0, success=False)
        except Exception as e:
            logger.error(f"释放连接失败: {e}")
            self.update_metrics(service, 'release', 0, success=False)
    
    async def cleanup_idle_connections(self):
        """清理空闲连接"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                
                for service, pool in self.pools.items():
                    await self.cleanup_pool_idle_connections(pool, service)
            except Exception as e:
                logger.error(f"清理空闲连接失败: {e}")
    
    def update_metrics(self, service: str, operation: str, value: float, success: bool):
        """更新性能指标"""
        if service not in self.metrics:
            self.metrics[service] = {}
        
        metrics = self.metrics[service]
        
        if operation == 'acquire':
            if success:
                metrics['avg_wait_time'] = 0.9 * metrics.get('avg_wait_time', 0) + 0.1 * value
            else:
                metrics['connection_errors'] = metrics.get('connection_errors', 0) + 1
        elif operation == 'release':
            if not success:
                metrics['connection_errors'] = metrics.get('connection_errors', 0) + 1
```

### 3.3 缓存策略优化

#### 3.3.1 多级缓存架构
```python
from src.services.explicit_cache_service import ExplicitCacheService, CacheLevel

class MultiLevelCacheOptimizer:
    """多级缓存优化器"""
    
    def __init__(self):
        # 内存缓存（L1）
        self.memory_cache = ExplicitCacheService({
            'ttl_seconds': 60,      # 1分钟
            'max_size': 1000,       # 1000个条目
            'level': CacheLevel.MEMORY
        })
        
        # 磁盘缓存（L2）
        self.disk_cache = ExplicitCacheService({
            'ttl_seconds': 300,     # 5分钟
            'max_size': 10000,      # 10000个条目
            'level': CacheLevel.DISK,
            'storage_path': '/tmp/rangen_cache'
        })
        
        # 分布式缓存（L3）- Redis/Memcached
        self.distributed_cache = None
        self.init_distributed_cache()
        
        # 缓存统计
        self.cache_stats = {
            'memory_hits': 0,
            'memory_misses': 0,
            'disk_hits': 0,
            'disk_misses': 0,
            'distributed_hits': 0,
            'distributed_misses': 0,
            'total_requests': 0
        }
    
    def init_distributed_cache(self):
        """初始化分布式缓存"""
        try:
            import redis
            self.distributed_cache = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True
            )
            logger.info("分布式缓存连接成功")
        except Exception as e:
            logger.warning(f"分布式缓存不可用: {e}")
            self.distributed_cache = None
    
    async def get(self, key: str, default=None):
        """多级缓存获取"""
        self.cache_stats['total_requests'] += 1
        
        # 1. 检查内存缓存
        value = self.memory_cache.get(key)
        if value is not None:
            self.cache_stats['memory_hits'] += 1
            return value
        
        self.cache_stats['memory_misses'] += 1
        
        # 2. 检查磁盘缓存
        value = self.disk_cache.get(key)
        if value is not None:
            self.cache_stats['disk_hits'] += 1
            # 回写到内存缓存
            self.memory_cache.set(key, value, ttl=60)
            return value
        
        self.cache_stats['disk_misses'] += 1
        
        # 3. 检查分布式缓存
        if self.distributed_cache:
            try:
                value = self.distributed_cache.get(key)
                if value is not None:
                    self.cache_stats['distributed_hits'] += 1
                    # 回写到内存和磁盘缓存
                    self.memory_cache.set(key, value, ttl=60)
                    self.disk_cache.set(key, value, ttl=300)
                    return value
                self.cache_stats['distributed_misses'] += 1
            except Exception as e:
                logger.error(f"分布式缓存获取失败: {e}")
        
        # 4. 缓存未命中
        return default
    
    async def set(self, key: str, value: Any, ttl: int = None, level: str = 'all'):
        """多级缓存设置"""
        ttl = ttl or 300
        
        # 设置内存缓存
        if level in ['all', 'memory']:
            self.memory_cache.set(key, value, ttl=min(ttl, 60))
        
        # 设置磁盘缓存
        if level in ['all', 'disk']:
            self.disk_cache.set(key, value, ttl=min(ttl, 300))
        
        # 设置分布式缓存
        if level in ['all', 'distributed'] and self.distributed_cache:
            try:
                self.distributed_cache.setex(key, min(ttl, 3600), value)
            except Exception as e:
                logger.error(f"分布式缓存设置失败: {e}")
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        stats = self.cache_stats.copy()
        
        # 计算命中率
        total_hits = (
            stats['memory_hits'] + 
            stats['disk_hits'] + 
            stats['distributed_hits']
        )
        
        stats['overall_hit_rate'] = (
            total_hits / stats['total_requests'] 
            if stats['total_requests'] > 0 else 0
        )
        
        stats['memory_hit_rate'] = (
            stats['memory_hits'] / stats['total_requests']
            if stats['total_requests'] > 0 else 0
        )
        
        return stats
    
    def optimize_cache_config(self, stats: Dict):
        """基于统计优化缓存配置"""
        # 如果内存缓存命中率低，考虑增加容量
        if stats['memory_hit_rate'] < 0.3 and stats['total_requests'] > 1000:
            new_size = min(self.memory_cache.max_size * 2, 10000)
            logger.info(f"增加内存缓存容量: {self.memory_cache.max_size} -> {new_size}")
            self.memory_cache.max_size = new_size
        
        # 如果整体命中率低，考虑调整TTL
        if stats['overall_hit_rate'] < 0.4:
            logger.info("缓存命中率低，考虑优化缓存策略")
            # 可以在这里实现更复杂的优化逻辑
```

#### 3.3.2 预测性缓存预热
```python
class PredictiveCacheWarmer:
    """预测性缓存预热器"""
    
    def __init__(self, access_pattern_analyzer):
        self.analyzer = access_pattern_analyzer
        self.warming_queue = asyncio.Queue()
        self.warming_tasks = set()
        self.warmed_keys = set()
    
    async def analyze_and_warm(self):
        """分析访问模式并预热缓存"""
        while True:
            try:
                # 分析历史访问模式
                patterns = await self.analyzer.analyze_access_patterns(hours=24)
                
                # 预测热门内容
                hot_items = self.predict_hot_items(patterns)
                
                # 预热缓存
                await self.warm_cache(hot_items)
                
                # 休眠一段时间再继续
                await asyncio.sleep(300)  # 5分钟
            except Exception as e:
                logger.error(f"缓存预热失败: {e}")
                await asyncio.sleep(60)
    
    def predict_hot_items(self, patterns: Dict) -> List[Dict]:
        """预测热门缓存项"""
        hot_items = []
        
        # 基于时间模式预测
        current_hour = datetime.now().hour
        time_based = patterns.get('hourly_pattern', {}).get(current_hour, [])
        hot_items.extend(time_based[:10])  # 取前10个
        
        # 基于用户模式预测
        active_users = patterns.get('active_users', [])
        for user in active_users[:5]:  # 前5个活跃用户
            user_items = patterns.get('user_patterns', {}).get(user, [])
            hot_items.extend(user_items[:5])
        
        # 基于内容关联预测
        recent_items = patterns.get('recent_items', [])
        for item in recent_items[:10]:
            related = self.find_related_items(item, patterns.get('item_relations', {}))
            hot_items.extend(related[:3])
        
        # 去重
        seen = set()
        unique_items = []
        for item in hot_items:
            item_id = item.get('id')
            if item_id and item_id not in seen:
                seen.add(item_id)
                unique_items.append(item)
        
        return unique_items[:50]  # 最多预热50个项
    
    async def warm_cache(self, items: List[Dict]):
        """预热缓存"""
        for item in items:
            if item['id'] in self.warmed_keys:
                continue
            
            # 添加到预热队列
            await self.warming_queue.put(item)
            
            # 限制并发预热任务数
            if len(self.warming_tasks) < 10:
                task = asyncio.create_task(self.process_warming_item())
                self.warming_tasks.add(task)
                task.add_done_callback(self.warming_tasks.discard)
    
    async def process_warming_item(self):
        """处理缓存预热项"""
        while not self.warming_queue.empty():
            try:
                item = await self.warming_queue.get()
                
                # 预加载内容到缓存
                await self.preload_to_cache(item)
                
                self.warmed_keys.add(item['id'])
                self.warming_queue.task_done()
            except Exception as e:
                logger.error(f"缓存预加载失败: {e}")
    
    async def preload_to_cache(self, item: Dict):
        """预加载内容到缓存"""
        # 根据内容类型选择预加载策略
        content_type = item.get('type', 'unknown')
        
        if content_type == 'llm_response':
            await self.preload_llm_response(item)
        elif content_type == 'vector_embedding':
            await self.preload_vector_embedding(item)
        elif content_type == 'processed_data':
            await self.preload_processed_data(item)
        else:
            await self.preload_generic_content(item)
```

### 3.4 内存管理优化

#### 3.4.1 智能内存管理
```python
import psutil
import gc

class IntelligentMemoryManager:
    """智能内存管理器"""
    
    def __init__(self, memory_limit_mb: int = 4096):
        self.memory_limit = memory_limit_mb * 1024 * 1024  # 转换为字节
        self.memory_usage = 0
        self.allocated_objects = {}
        self.memory_pressure_levels = {
            'low': 0.6,      # 60%内存使用
            'medium': 0.75,   # 75%内存使用
            'high': 0.85,     # 85%内存使用
            'critical': 0.95  # 95%内存使用
        }
        self.cleanup_strategies = {
            'low': self.low_memory_cleanup,
            'medium': self.medium_memory_cleanup,
            'high': self.high_memory_cleanup,
            'critical': self.critical_memory_cleanup
        }
        
    def allocate(self, obj_id: str, obj: Any, estimated_size: int = None):
        """分配内存并跟踪对象"""
        if estimated_size is None:
            estimated_size = self.estimate_object_size(obj)
        
        self.allocated_objects[obj_id] = {
            'object': obj,
            'size': estimated_size,
            'timestamp': time.time(),
            'access_count': 0,
            'last_accessed': time.time(),
            'importance': self.calculate_object_importance(obj)
        }
        
        self.memory_usage += estimated_size
        
        # 检查内存压力
        self.check_memory_pressure()
        
        return obj_id
    
    def estimate_object_size(self, obj: Any) -> int:
        """估计对象大小"""
        if isinstance(obj, str):
            return len(obj.encode('utf-8'))
        elif isinstance(obj, bytes):
            return len(obj)
        elif isinstance(obj, (list, tuple, set)):
            return sum(self.estimate_object_size(item) for item in obj)
        elif isinstance(obj, dict):
            total = 0
            for key, value in obj.items():
                total += self.estimate_object_size(key)
                total += self.estimate_object_size(value)
            return total
        else:
            # 使用sys.getsizeof作为默认估计
            import sys
            return sys.getsizeof(obj)
    
    def calculate_object_importance(self, obj: Any) -> float:
        """计算对象重要性"""
        importance = 0.5  # 基础重要性
        
        # 根据对象类型调整重要性
        if hasattr(obj, '__class__'):
            class_name = obj.__class__.__name__
            if 'Cache' in class_name:
                importance = 0.3  # 缓存对象重要性较低
            elif 'Model' in class_name:
                importance = 0.8  # 模型对象重要性较高
            elif 'Session' in class_name:
                importance = 0.7  # 会话对象重要性中等
        
        return importance
    
    def check_memory_pressure(self):
        """检查内存压力"""
        # 获取系统内存使用情况
        system_memory = psutil.virtual_memory()
        process_memory = psutil.Process().memory_info().rss
        
        # 计算内存使用率
        system_usage = system_memory.percent / 100
        process_usage = process_memory / self.memory_limit
        
        # 确定压力级别
        usage = max(system_usage, process_usage)
        
        if usage >= self.memory_pressure_levels['critical']:
            pressure_level = 'critical'
        elif usage >= self.memory_pressure_levels['high']:
            pressure_level = 'high'
        elif usage >= self.memory_pressure_levels['medium']:
            pressure_level = 'medium'
        elif usage >= self.memory_pressure_levels['low']:
            pressure_level = 'low'
        else:
            return  # 无压力
        
        # 执行清理策略
        logger.warning(f"内存压力级别: {pressure_level}, 使用率: {usage:.1%}")
        self.cleanup_strategies[pressure_level]()
    
    def low_memory_cleanup(self):
        """低内存压力清理"""
        # 清理长时间未访问的不重要对象
        current_time = time.time()
        to_remove = []
        
        for obj_id, info in self.allocated_objects.items():
            if (info['importance'] < 0.4 and 
                current_time - info['last_accessed'] > 3600):  # 1小时未访问
                to_remove.append(obj_id)
        
        self.remove_objects(to_remove[:10])  # 最多清理10个对象
    
    def medium_memory_cleanup(self):
        """中等内存压力清理"""
        # 清理更多对象，包括一些中等重要性对象
        current_time = time.time()
        to_remove = []
        
        for obj_id, info in self.allocated_objects.items():
            age = current_time - info['timestamp']
            last_access = current_time - info['last_accessed']
            
            # 评分公式：重要性低 + 年龄大 + 长时间未访问 = 优先清理
            score = (1 - info['importance']) * 0.4 + (age / 3600) * 0.3 + (last_access / 1800) * 0.3
            
            if score > 0.5:
                to_remove.append((obj_id, score))
        
        # 按评分排序，清理评分最高的对象
        to_remove.sort(key=lambda x: x[1], reverse=True)
        self.remove_objects([obj_id for obj_id, _ in to_remove[:20]])
        
        # 触发垃圾回收
        gc.collect()
    
    def high_memory_cleanup(self):
        """高内存压力清理"""
        # 更激进的清理策略
        self.medium_memory_cleanup()
        
        # 清理缓存
        self.clear_caches()
        
        # 强制垃圾回收多次
        for _ in range(3):
            gc.collect()
    
    def critical_memory_cleanup(self):
        """临界内存压力清理"""
        # 最激进的清理策略
        self.high_memory_cleanup()
        
        # 清理所有非关键对象
        to_keep = []
        for obj_id, info in self.allocated_objects.items():
            if info['importance'] >= 0.8:  # 只保留重要性>=0.8的对象
                to_keep.append(obj_id)
        
        # 清理其他所有对象
        to_remove = [obj_id for obj_id in self.allocated_objects if obj_id not in to_keep]
        self.remove_objects(to_remove)
        
        # 记录紧急情况
        logger.critical("执行临界内存清理，释放了{}个对象".format(len(to_remove)))
    
    def remove_objects(self, obj_ids: List[str]):
        """移除指定对象"""
        for obj_id in obj_ids:
            if obj_id in self.allocated_objects:
                info = self.allocated_objects[obj_id]
                self.memory_usage -= info['size']
                del self.allocated_objects[obj_id]
                
                # 帮助垃圾回收
                if hasattr(info['object'], '__del__'):
                    try:
                        info['object'].__del__()
                    except:
                        pass
    
    def clear_caches(self):
        """清理缓存"""
        # 这里可以调用各个缓存服务的清理方法
        # 例如：cache_service.clear_old_entries()
        pass
```

## 🔧 系统配置优化

### 4.1 硬件配置优化

#### 4.1.1 服务器规格建议
```yaml
# 推荐服务器配置
server_configurations:
  development:
    cpu: "4 cores"
    memory: "16GB"
    storage: "100GB SSD"
    gpu: "Optional"
    network: "1Gbps"
    
  production_small:
    cpu: "8 cores"
    memory: "32GB"
    storage: "500GB SSD"
    gpu: "1x NVIDIA T4"
    network: "10Gbps"
    
  production_medium:
    cpu: "16 cores"
    memory: "64GB"
    storage: "1TB NVMe"
    gpu: "2x NVIDIA A10"
    network: "10Gbps"
    
  production_large:
    cpu: "32 cores"
    memory: "128GB"
    storage: "2TB NVMe"
    gpu: "4x NVIDIA A100"
    network: "25Gbps"
```

#### 4.1.2 系统参数调优
```bash
# Linux系统参数优化
# /etc/sysctl.conf
vm.swappiness = 10
vm.vfs_cache_pressure = 50
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30

# 文件描述符限制
# /etc/security/limits.conf
* soft nofile 65536
* hard nofile 131072
```

### 4.2 软件配置优化

#### 4.2.1 Python运行时优化
```python
# 环境变量配置
os.environ.update({
    'PYTHONUNBUFFERED': '1',           # 立即输出日志
    'PYTHONASYNCIODEBUG': '0',         # 关闭异步调试（生产环境）
    'PYTHONFAULTHANDLER': '1',         # 启用故障处理
    'PYTHONHASHSEED': 'random',        # 随机化哈希种子
    'PYTHONMALLOC': 'malloc',          # 使用系统malloc
})

# 垃圾回收配置
import gc
gc.set_threshold(700, 10, 10)  # 优化垃圾回收阈值
gc.enable()  # 确保启用

# 内存分配器优化
try:
    import jemalloc
    # 使用jemalloc作为内存分配器
    os.environ['LD_PRELOAD'] = jemalloc.__file__
except ImportError:
    logger.info("jemalloc未安装，使用系统默认分配器")
```

#### 4.2.2 数据库连接优化
```python
# PostgreSQL连接池配置
postgres_config = {
    'pool_size': 20,           # 连接池大小
    'max_overflow': 10,        # 最大溢出连接数
    'pool_timeout': 30,        # 获取连接超时时间
    'pool_recycle': 3600,      # 连接回收时间
    'pool_pre_ping': True,     # 连接前检查
    'echo': False,             # 不输出SQL日志
    'connect_args': {
        'connect_timeout': 10,
        'application_name': 'rangen_app'
    }
}

# Redis连接配置
redis_config = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'password': os.getenv('REDIS_PASSWORD'),
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True,
    'max_connections': 100,
    'decode_responses': True
}
```

## 📈 监控与诊断

### 5.1 性能监控体系

#### 5.1.1 实时性能仪表板
```python
class PerformanceDashboard:
    """性能监控仪表板"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.dashboard_data = {}
        self.update_interval = 5  # 5秒更新一次
        
    async def start_monitoring(self):
        """启动性能监控"""
        # 启动数据收集
        asyncio.create_task(self.collect_performance_data())
        
        # 启动实时分析
        asyncio.create_task(self.analyze_performance_trends())
        
        # 启动仪表板更新
        asyncio.create_task(self.update_dashboard())
        
        logger.info("性能监控已启动")
    
    async def collect_performance_data(self):
        """收集性能数据"""
        while True:
            try:
                # 收集系统指标
                system_metrics = await self.collect_system_metrics()
                
                # 收集应用指标
                app_metrics = await self.collect_application_metrics()
                
                # 收集业务指标
                business_metrics = await self.collect_business_metrics()
                
                # 存储数据
                await self.store_metrics({
                    'system': system_metrics,
                    'application': app_metrics,
                    'business': business_metrics,
                    'timestamp': time.time()
                })
                
                await asyncio.sleep(1)  # 每秒收集一次
            except Exception as e:
                logger.error(f"性能数据收集失败: {e}")
                await asyncio.sleep(5)
    
    async def collect_system_metrics(self) -> Dict:
        """收集系统指标"""
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict(),
            'process_count': len(psutil.pids())
        }
    
    async def collect_application_metrics(self) -> Dict:
        """收集应用指标"""
        return {
            'active_requests': self.get_active_request_count(),
            'request_latency_p95': self.get_latency_percentile(95),
            'request_latency_p99': self.get_latency_percentile(99),
            'error_rate': self.get_error_rate(),
            'cache_hit_rate': self.get_cache_hit_rate(),
            'queue_length': self.get_queue_length()
        }
    
    async def analyze_performance_trends(self):
        """分析性能趋势"""
        while True:
            try:
                # 获取历史数据
                historical_data = await self.get_historical_data(minutes=30)
                
                # 分析趋势
                trends = self.analyze_trends(historical_data)
                
                # 检测异常
                anomalies = self.detect_anomalies(trends)
                
                # 触发告警
                for anomaly in anomalies:
                    await self.alert_manager.send_alert(anomaly)
                
                # 生成优化建议
                recommendations = self.generate_recommendations(trends)
                
                # 更新仪表板数据
                self.dashboard_data['trends'] = trends
                self.dashboard_data['anomalies'] = anomalies
                self.dashboard_data['recommendations'] = recommendations
                
                await asyncio.sleep(30)  # 每30秒分析一次
            except Exception as e:
                logger.error(f"性能趋势分析失败: {e}")
                await asyncio.sleep(60)
    
    async def update_dashboard(self):
        """更新仪表板"""
        while True:
            try:
                # 获取最新数据
                latest_data = await self.get_latest_data()
                
                # 计算关键指标
                kpis = self.calculate_kpis(latest_data)
                
                # 生成可视化数据
                visualizations = self.generate_visualizations(latest_data)
                
                # 更新前端
                await self.update_frontend({
                    'kpis': kpis,
                    'visualizations': visualizations,
                    'trends': self.dashboard_data.get('trends', {}),
                    'alerts': self.alert_manager.get_active_alerts()
                })
                
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"仪表板更新失败: {e}")
                await asyncio.sleep(10)
```

#### 5.1.2 自动化性能测试
```python
class AutomatedPerformanceTester:
    """自动化性能测试器"""
    
    def __init__(self, test_scenarios: List[Dict]):
        self.test_scenarios = test_scenarios
        self.results = []
        self.current_test = None
        self.test_executor = TestExecutor()
        
    async def run_performance_suite(self):
        """运行性能测试套件"""
        logger.info("开始性能测试套件")
        
        for scenario in self.test_scenarios:
            try:
                await self.run_scenario(scenario)
            except Exception as e:
                logger.error(f"场景执行失败: {scenario['name']}, 错误: {e}")
        
        # 生成测试报告
        report = self.generate_test_report()
        
        # 发送通知
        await self.send_test_report(report)
        
        return report
    
    async def run_scenario(self, scenario: Dict):
        """运行单个测试场景"""
        logger.info(f"开始测试场景: {scenario['name']}")
        
        self.current_test = {
            'scenario': scenario,
            'start_time': time.time(),
            'metrics': [],
            'errors': []
        }
        
        # 执行预热
        if scenario.get('warmup', False):
            await self.warmup(scenario)
        
        # 执行测试
        test_results = await self.execute_test(scenario)
        
        # 收集结果
        self.current_test.update({
            'end_time': time.time(),
            'results': test_results,
            'summary': self.analyze_results(test_results, scenario)
        })
        
        # 存储结果
        self.results.append(self.current_test.copy())
        
        # 打印结果摘要
        self.print_scenario_summary(self.current_test['summary'])
        
        return self.current_test
    
    async def warmup(self, scenario: Dict):
        """预热测试"""
        logger.info(f"预热场景: {scenario['name']}")
        
        warmup_config = scenario.get('warmup_config', {
            'iterations': 10,
            'concurrency': 1
        })
        
        for i in range(warmup_config['iterations']):
            try:
                await self.execute_test(scenario, warmup=True)
            except Exception as e:
                logger.debug(f"预热迭代 {i+1} 失败: {e}")
        
        logger.info(f"预热完成: {scenario['name']}")
    
    async def execute_test(self, scenario: Dict, warmup: bool = False) -> List[Dict]:
        """执行测试"""
        test_config = scenario['test_config']
        test_type = test_config['type']
        
        if test_type == 'load_test':
            return await self.run_load_test(test_config, warmup)
        elif test_type == 'stress_test':
            return await self.run_stress_test(test_config, warmup)
        elif test_type == 'soak_test':
            return await self.run_soak_test(test_config, warmup)
        elif test_type == 'spike_test':
            return await self.run_spike_test(test_config, warmup)
        else:
            raise ValueError(f"未知的测试类型: {test_type}")
    
    async def run_load_test(self, config: Dict, warmup: bool = False) -> List[Dict]:
        """运行负载测试"""
        results = []
        duration = config.get('duration', 60)
        users = config.get('users', 10)
        ramp_up = config.get('ramp_up', 10)
        
        logger.info(f"开始负载测试: {users}用户, {duration}秒")
        
        # 创建虚拟用户
        user_tasks = []
        for user_id in range(users):
            task = asyncio.create_task(
                self.simulate_user(user_id, duration, ramp_up, warmup)
            )
            user_tasks.append(task)
        
        # 等待所有用户完成
        user_results = await asyncio.gather(*user_tasks, return_exceptions=True)
        
        # 处理结果
        for i, result in enumerate(user_results):
            if isinstance(result, Exception):
                logger.error(f"用户 {i} 测试失败: {result}")
                results.append({
                    'user_id': i,
                    'success': False,
                    'error': str(result),
                    'latency': 0,
                    'throughput': 0
                })
            else:
                results.extend(result)
        
        return results
    
    def analyze_results(self, results: List[Dict], scenario: Dict) -> Dict:
        """分析测试结果"""
        if not results:
            return {'error': '无测试结果'}
        
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', True)]
        
        latencies = [r.get('latency', 0) for r in successful]
        throughputs = [r.get('throughput', 0) for r in successful]
        
        return {
            'scenario_name': scenario['name'],
            'total_requests': len(results),
            'successful_requests': len(successful),
            'failed_requests': len(failed),
            'success_rate': len(successful) / max(len(results), 1),
            'avg_latency': sum(latencies) / max(len(latencies), 1),
            'p95_latency': self.calculate_percentile(latencies, 95),
            'p99_latency': self.calculate_percentile(latencies, 99),
            'max_latency': max(latencies) if latencies else 0,
            'min_latency': min(latencies) if latencies else 0,
            'avg_throughput': sum(throughputs) / max(len(throughputs), 1),
            'total_duration': scenario.get('test_config', {}).get('duration', 0),
            'recommendations': self.generate_recommendations(results, scenario)
        }
    
    def calculate_percentile(self, values: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = (len(sorted_values) - 1) * percentile / 100
        lower = int(index)
        upper = lower + 1
        
        if upper >= len(sorted_values):
            return sorted_values[lower]
        
        weight = index - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
    
    def generate_recommendations(self, results: List[Dict], scenario: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []
        analysis = self.analyze_results(results, scenario)
        
        # 基于成功率
        if analysis['success_rate'] < 0.95:
            recommendations.append("⚠️ 成功率低于95%，建议检查系统稳定性")
        
        # 基于延迟
        if analysis['p95_latency'] > 3000:  # 3秒
            recommendations.append("🚨 P95延迟超过3秒，需要优化系统性能")
        elif analysis['p95_latency'] > 1000:  # 1秒
            recommendations.append("⚠️ P95延迟超过1秒，建议优化响应时间")
        
        # 基于吞吐量
        expected_throughput = scenario.get('expected_throughput', 0)
        if expected_throughput > 0 and analysis['avg_throughput'] < expected_throughput * 0.8:
            recommendations.append(f"⚠️ 吞吐量低于预期80%，当前{analysis['avg_throughput']:.1f}/s，预期{expected_throughput}/s")
        
        if not recommendations:
            recommendations.append("✅ 性能测试结果良好，无明显问题")
        
        return recommendations
    
    def generate_test_report(self) -> Dict:
        """生成测试报告"""
        if not self.results:
            return {'error': '无测试结果'}
        
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'total_scenarios': len(self.results),
            'scenario_results': [],
            'overall_summary': {
                'total_requests': 0,
                'successful_requests': 0,
                'avg_success_rate': 0,
                'avg_p95_latency': 0,
                'critical_issues': 0,
                'warnings': 0
            }
        }
        
        for result in self.results:
            summary = result.get('summary', {})
            report['scenario_results'].append(summary)
            
            # 更新总体统计
            report['overall_summary']['total_requests'] += summary.get('total_requests', 0)
            report['overall_summary']['successful_requests'] += summary.get('successful_requests', 0)
            
            # 统计问题
            recommendations = summary.get('recommendations', [])
            for rec in recommendations:
                if '🚨' in rec:
                    report['overall_summary']['critical_issues'] += 1
                elif '⚠️' in rec:
                    report['overall_summary']['warnings'] += 1
        
        # 计算平均成功率
        total_scenarios = len(self.results)
        if total_scenarios > 0:
            total_success_rate = sum(r.get('summary', {}).get('success_rate', 0) for r in self.results)
            report['overall_summary']['avg_success_rate'] = total_success_rate / total_scenarios
            
            total_p95 = sum(r.get('summary', {}).get('p95_latency', 0) for r in self.results)
            report['overall_summary']['avg_p95_latency'] = total_p95 / total_scenarios
        
        return report
    
    async def send_test_report(self, report: Dict):
        """发送测试报告"""
        # 这里可以实现邮件、Webhook、Slack等通知方式
        logger.info(f"性能测试报告生成完成")
        logger.info(f"总场景数: {report['overall_summary']['total_scenarios']}")
        logger.info(f"平均成功率: {report['overall_summary']['avg_success_rate']:.1%}")
        logger.info(f"平均P95延迟: {report['overall_summary']['avg_p95_latency']:.0f}ms")
        logger.info(f"严重问题: {report['overall_summary']['critical_issues']}")
        logger.info(f"警告: {report['overall_summary']['warnings']}")
        
        # 保存报告到文件
        report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试报告已保存到: {report_file}")
    
    async def simulate_user(self, user_id: int, duration: int, ramp_up: int, warmup: bool = False) -> List[Dict]:
        """模拟用户行为"""
        results = []
        start_time = time.time()
        
        # 逐步增加负载（ramp up）
        if user_id < ramp_up:
            await asyncio.sleep(user_id)
        
        while time.time() - start_time < duration:
            iteration_start = time.time()
            
            try:
                # 执行测试请求
                result = await self.make_test_request(user_id, warmup)
                result['user_id'] = user_id
                result['timestamp'] = time.time()
                results.append(result)
            except Exception as e:
                results.append({
                    'user_id': user_id,
                    'success': False,
                    'error': str(e),
                    'latency': 0,
                    'throughput': 0,
                    'timestamp': time.time()
                })
            
            # 控制请求频率
            request_interval = 1.0  # 每秒1个请求
            elapsed = time.time() - iteration_start
            if elapsed < request_interval:
                await asyncio.sleep(request_interval - elapsed)
        
        return results
    
    async def make_test_request(self, user_id: int, warmup: bool = False) -> Dict:
        """执行测试请求"""
        start_time = time.time()
        
        try:
            # 这里调用实际的系统API
            # 示例：调用LLM服务
            response = await self.call_llm_service(
                prompt=f"测试用户{user_id}的请求",
                max_tokens=100,
                temperature=0.7
            )
            
            latency = (time.time() - start_time) * 1000  # 转换为毫秒
            
            return {
                'success': True,
                'latency': latency,
                'throughput': len(response.get('text', '')) / (latency / 1000),  # 字符/秒
                'response_length': len(response.get('text', ''))
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'latency': (time.time() - start_time) * 1000,
                'throughput': 0
            }
    
    async def call_llm_service(self, **kwargs):
        """调用LLM服务（示例）"""
        # 这里应该调用实际的LLM服务
        # 示例：模拟API调用
        await asyncio.sleep(0.1)  # 模拟网络延迟
        
        return {
            'text': '这是模拟的LLM响应内容。' * 10,
            'tokens_used': 100,
            'model': 'test-model'
        }
    
    def print_scenario_summary(self, summary: Dict):
        """打印场景摘要"""
        logger.info("=" * 60)
        logger.info(f"场景: {summary.get('scenario_name', '未知')}")
        logger.info(f"总请求数: {summary.get('total_requests', 0)}")
        logger.info(f"成功请求: {summary.get('successful_requests', 0)}")
        logger.info(f"成功率: {summary.get('success_rate', 0):.1%}")
        logger.info(f"平均延迟: {summary.get('avg_latency', 0):.0f}ms")
        logger.info(f"P95延迟: {summary.get('p95_latency', 0):.0f}ms")
        logger.info(f"P99延迟: {summary.get('p99_latency', 0):.0f}ms")
        
        recommendations = summary.get('recommendations', [])
        if recommendations:
            logger.info("优化建议:")
            for rec in recommendations:
                logger.info(f"  - {rec}")
        
        logger.info("=" * 60)


# 使用示例
async def example_performance_test():
    """性能测试示例"""
    test_scenarios = [
        {
            'name': '基础负载测试',
            'description': '10个并发用户持续60秒',
            'warmup': True,
            'expected_throughput': 8,  # 期望8请求/秒
            'test_config': {
                'type': 'load_test',
                'duration': 60,
                'users': 10,
                'ramp_up': 5
            }
        },
        {
            'name': '压力测试',
            'description': '50个并发用户持续30秒',
            'warmup': True,
            'test_config': {
                'type': 'stress_test',
                'duration': 30,
                'users': 50,
                'ramp_up': 10
            }
        }
    ]
    
    tester = AutomatedPerformanceTester(test_scenarios)
    report = await tester.run_performance_suite()
    
    return report


### 5.2 故障诊断指南

#### 5.2.1 常见性能问题诊断

```python
class PerformanceDiagnoser:
    """性能问题诊断器"""
    
    def __init__(self):
        self.symptoms_to_causes = {
            'high_latency': [
                '网络延迟',
                '数据库查询慢',
                'CPU过载',
                '内存不足',
                '磁盘IO瓶颈',
                '外部API响应慢'
            ],
            'low_throughput': [
                '连接池不足',
                '线程池过小',
                '批处理配置不当',
                '缓存未命中率高',
                '序列化/反序列化瓶颈'
            ],
            'high_error_rate': [
                '资源耗尽',
                '超时配置过短',
                '外部服务不可用',
                '内存泄漏',
                '配置错误'
            ],
            'memory_leak': [
                '未释放对象引用',
                '缓存无限增长',
                '循环引用',
                '第三方库内存泄漏'
            ],
            'cpu_spike': [
                '无限循环',
                '递归过深',
                '加密/解密操作',
                '序列化/反序列化',
                '正则表达式匹配'
            ]
        }
        
        self.diagnostic_tools = {
            'profiling': ['cProfile', 'py-spy', 'scalene'],
            'memory': ['memory_profiler', 'objgraph', 'pympler'],
            'network': ['wireshark', 'tcpdump', 'netstat'],
            'system': ['top', 'htop', 'vmstat', 'iostat']
        }
    
    def diagnose(self, symptoms: List[str], metrics: Dict) -> List[Dict]:
        """诊断性能问题"""
        diagnoses = []
        
        for symptom in symptoms:
            possible_causes = self.symptoms_to_causes.get(symptom, [])
            
            for cause in possible_causes:
                confidence = self.calculate_confidence(symptom, cause, metrics)
                
                if confidence > 0.3:  # 置信度阈值
                    diagnosis = {
                        'symptom': symptom,
                        'cause': cause,
                        'confidence': confidence,
                        'recommended_tools': self.recommend_tools(cause),
                        'fix_suggestions': self.suggest_fixes(cause)
                    }
                    diagnoses.append(diagnosis)
        
        # 按置信度排序
        diagnoses.sort(key=lambda x: x['confidence'], reverse=True)
        
        return diagnoses
    
    def calculate_confidence(self, symptom: str, cause: str, metrics: Dict) -> float:
        """计算诊断置信度"""
        confidence = 0.5  # 基础置信度
        
        # 基于指标调整置信度
        if symptom == 'high_latency' and cause == '网络延迟':
            if metrics.get('network_latency', 0) > 100:  # 网络延迟 > 100ms
                confidence += 0.3
        
        elif symptom == 'memory_leak' and cause == '缓存无限增长':
            if metrics.get('cache_size_growth_rate', 0) > 0.1:  # 缓存增长率 > 10%
                confidence += 0.4
        
        elif symptom == 'cpu_spike' and cause == '加密/解密操作':
            if metrics.get('crypto_operations', 0) > 1000:  # 加密操作 > 1000次/秒
                confidence += 0.5
        
        return min(confidence, 1.0)  # 限制最大值为1.0
    
    def recommend_tools(self, cause: str) -> List[str]:
        """推荐诊断工具"""
        tool_mapping = {
            '网络延迟': self.diagnostic_tools['network'],
            '内存不足': self.diagnostic_tools['memory'],
            'CPU过载': self.diagnostic_tools['profiling'] + self.diagnostic_tools['system'],
            '磁盘IO瓶颈': self.diagnostic_tools['system'],
            '数据库查询慢': ['EXPLAIN ANALYZE', 'pg_stat_statements', '慢查询日志']
        }
        
        return tool_mapping.get(cause, ['通用性能分析工具'])
    
    def suggest_fixes(self, cause: str) -> List[str]:
        """提供修复建议"""
        fixes = {
            '网络延迟': [
                '优化网络配置',
                '使用CDN',
                '启用连接复用',
                '增加超时时间',
                '使用更近的服务器区域'
            ],
            '数据库查询慢': [
                '添加索引',
                '优化查询语句',
                '使用查询缓存',
                '增加数据库连接池',
                '数据库分片'
            ],
            'CPU过载': [
                '优化算法复杂度',
                '启用缓存',
                '使用异步处理',
                '增加硬件资源',
                '负载均衡'
            ],
            '内存不足': [
                '增加虚拟内存',
                '优化数据结构',
                '启用内存压缩',
                '使用流式处理',
                '增加物理内存'
            ],
            '缓存未命中率高': [
                '调整缓存策略',
                '增加缓存容量',
                '预热缓存',
                '优化缓存键设计',
                '使用多级缓存'
            ]
        }
        
        return fixes.get(cause, ['请查阅相关文档或咨询专家'])
```

#### 5.2.2 性能问题排查流程

```python
class PerformanceTroubleshootingWorkflow:
    """性能问题排查工作流"""
    
    def __init__(self):
        self.steps = [
            self.step1_identify_symptoms,
            self.step2_collect_metrics,
            self.step3_analyze_data,
            self.step4_hypothesize_causes,
            self.step5_test_hypotheses,
            self.step6_implement_fix,
            self.step7_verify_fix,
            self.step8_document_resolution
        ]
        
        self.current_step = 0
        self.finding_log = []
    
    async def troubleshoot(self, problem_description: str):
        """执行问题排查"""
        logger.info(f"开始排查性能问题: {problem_description}")
        
        context = {
            'problem': problem_description,
            'start_time': time.time(),
            'metrics': {},
            'hypotheses': [],
            'tests': [],
            'fixes': []
        }
        
        for step_func in self.steps:
            self.current_step += 1
            step_name = step_func.__name__.replace('step', '').replace('_', ' ').title()
            
            logger.info(f"步骤 {self.current_step}: {step_name}")
            
            try:
                result = await step_func(context)
                context[f'step_{self.current_step}_result'] = result
                self.finding_log.append({
                    'step': self.current_step,
                    'name': step_name,
                    'result': result,
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"步骤 {self.current_step} 失败: {e}")
                context[f'step_{self.current_step}_error'] = str(e)
        
        logger.info("问题排查完成")
        return self.generate_report(context)
    
    async def step1_identify_symptoms(self, context: Dict) -> List[str]:
        """步骤1: 识别症状"""
        symptoms = []
        
        # 分析问题描述中的关键词
        problem = context['problem'].lower()
        
        symptom_keywords = {
            'slow': 'high_latency',
            '延迟': 'high_latency',
            'timeout': 'high_latency',
            '吞吐量': 'low_throughput',
            'throughput': 'low_throughput',
            '错误': 'high_error_rate',
            'error': 'high_error_rate',
            '内存': 'memory_leak',
            'memory': 'memory_leak',
            'cpu': 'cpu_spike',
            '崩溃': 'crash'
        }
        
        for keyword, symptom in symptom_keywords.items():
            if keyword in problem:
                symptoms.append(symptom)
        
        # 去重
        symptoms = list(set(symptoms))
        
        logger.info(f"识别到的症状: {symptoms}")
        return symptoms
    
    async def step2_collect_metrics(self, context: Dict) -> Dict:
        """步骤2: 收集指标"""
        metrics = {}
        
        # 收集系统指标
        metrics.update(await self.collect_system_metrics())
        
        # 收集应用指标
        metrics.update(await self.collect_application_metrics())
        
        # 收集业务指标
        metrics.update(await self.collect_business_metrics())
        
        context['metrics'] = metrics
        
        logger.info(f"收集到 {len(metrics)} 个指标")
        return metrics
    
    async def step3_analyze_data(self, context: Dict) -> Dict:
        """步骤3: 分析数据"""
        analysis = {}
        metrics = context['metrics']
        symptoms = context.get('step_1_result', [])
        
        # 分析每个症状
        for symptom in symptoms:
            symptom_analysis = self.analyze_symptom(symptom, metrics)
            analysis[symptom] = symptom_analysis
        
        context['analysis'] = analysis
        
        logger.info(f"数据分析完成")
        return analysis
    
    async def step4_hypothesize_causes(self, context: Dict) -> List[Dict]:
        """步骤4: 假设原因"""
        diagnoser = PerformanceDiagnoser()
        symptoms = context.get('step_1_result', [])
        metrics = context['metrics']
        
        hypotheses = diagnoser.diagnose(symptoms, metrics)
        
        # 排序并选择前5个最可能的原因
        top_hypotheses = hypotheses[:5]
        
        context['hypotheses'] = top_hypotheses
        
        logger.info(f"生成 {len(top_hypotheses)} 个假设")
        return top_hypotheses
    
    async def step5_test_hypotheses(self, context: Dict) -> List[Dict]:
        """步骤5: 测试假设"""
        tests = []
        hypotheses = context['hypotheses']
        
        for i, hypothesis in enumerate(hypotheses):
            test_result = await self.test_hypothesis(hypothesis)
            test_result['hypothesis_index'] = i
            tests.append(test_result)
        
        context['tests'] = tests
        
        logger.info(f"完成 {len(tests)} 个测试")
        return tests
    
    async def step6_implement_fix(self, context: Dict) -> List[Dict]:
        """步骤6: 实施修复"""
        fixes = []
        tests = context['tests']
        
        # 选择最可能正确的假设
        validated_hypotheses = [t for t in tests if t.get('validated', False)]
        
        if not validated_hypotheses:
            logger.warning("没有验证通过的假设，无法实施修复")
            return []
        
        # 对每个验证通过的假设实施修复
        for hypothesis_test in validated_hypotheses:
            hypothesis_index = hypothesis_test['hypothesis_index']
            hypothesis = context['hypotheses'][hypothesis_index]
            
            fix_suggestions = hypothesis.get('fix_suggestions', [])
            
            for suggestion in fix_suggestions[:2]:  # 尝试前2个修复建议
                fix_result = await self.implement_fix_suggestion(suggestion)
                fixes.append(fix_result)
                
                if fix_result.get('success', False):
                    logger.info(f"修复成功: {suggestion}")
                    break
                else:
                    logger.warning(f"修复失败: {suggestion}")
        
        context['fixes'] = fixes
        
        return fixes
    
    async def step7_verify_fix(self, context: Dict) -> Dict:
        """步骤7: 验证修复"""
        verification = {}
        fixes = context['fixes']
        
        successful_fixes = [f for f in fixes if f.get('success', False)]
        
        if not successful_fixes:
            verification['status'] = 'failed'
            verification['message'] = '没有成功的修复'
            return verification
        
        # 重新收集指标验证修复效果
        before_metrics = context['metrics']
        after_metrics = await self.collect_application_metrics()
        
        # 比较关键指标
        key_metrics = ['request_latency_p95', 'error_rate', 'throughput']
        
        improvements = {}
        for metric in key_metrics:
            before = before_metrics.get(metric, 0)
            after = after_metrics.get(metric, 0)
            
            if before > 0:
                improvement = (before - after) / before * 100
                improvements[metric] = improvement
        
        verification['status'] = 'success' if any(v > 10 for v in improvements.values()) else 'partial'
        verification['improvements'] = improvements
        verification['message'] = f"修复验证完成，改进情况: {improvements}"
        
        logger.info(f"修复验证结果: {verification['status']}")
        return verification
    
    async def step8_document_resolution(self, context: Dict) -> Dict:
        """步骤8: 记录解决方案"""
        resolution_doc = {
            'problem': context['problem'],
            'start_time': context['start_time'],
            'end_time': time.time(),
            'duration_seconds': time.time() - context['start_time'],
            'symptoms_identified': context.get('step_1_result', []),
            'root_causes': [],
            'fixes_applied': [],
            'verification_result': context.get('step_7_result', {}),
            'lessons_learned': [],
            'preventive_measures': []
        }
        
        # 提取根原因
        tests = context.get('tests', [])
        for test in tests:
            if test.get('validated', False):
                hypothesis_index = test['hypothesis_index']
                hypothesis = context['hypotheses'][hypothesis_index]
                resolution_doc['root_causes'].append(hypothesis['cause'])
        
        # 提取应用的修复
        fixes = context.get('fixes', [])
        for fix in fixes:
            if fix.get('success', False):
                resolution_doc['fixes_applied'].append(fix['description'])
        
        # 保存文档
        doc_file = f"troubleshooting_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(doc_file, 'w') as f:
            json.dump(resolution_doc, f, indent=2, ensure_ascii=False)
        
        logger.info(f"问题解决文档已保存: {doc_file}")
        return resolution_doc
    
    def generate_report(self, context: Dict) -> Dict:
        """生成完整报告"""
        return {
            'summary': {
                'problem': context['problem'],
                'duration': time.time() - context['start_time'],
                'steps_completed': self.current_step,
                'final_status': context.get('step_7_result', {}).get('status', 'unknown')
            },
            'detailed_findings': self.finding_log,
            'resolution': context.get('step_8_result', {})
        }
```

## 📋 性能优化检查清单

### 6.1 基础优化检查清单

- [ ] **系统配置优化**
  - [ ] 调整Linux内核参数（sysctl.conf）
  - [ ] 优化文件描述符限制
  - [ ] 配置合理的交换空间
  - [ ] 调整网络参数
  
- [ ] **应用配置优化**
  - [ ] 优化Python垃圾回收配置
  - [ ] 配置合适的线程池/进程池大小
  - [ ] 调整连接池参数
  - [ ] 配置缓存策略
  
- [ ] **代码级优化**
  - [ ] 消除不必要的循环和递归
  - [ ] 使用适当的数据结构
  - [ ] 优化数据库查询
  - [ ] 减少序列化/反序列化开销

### 6.2 高级优化检查清单

- [ ] **架构优化**
  - [ ] 实施微服务拆分
  - [ ] 引入消息队列
  - [ ] 实现读写分离
  - [ ] 配置负载均衡
  
- [ ] **缓存策略优化**
  - [ ] 实现多级缓存架构
  - [ ] 配置合理的缓存过期策略
  - [ ] 实施缓存预热机制
  - [ ] 监控缓存命中率
  
- [ ] **异步处理优化**
  - [ ] 识别IO密集型任务并异步化
  - [ ] 合理控制并发度
  - [ ] 实现任务队列和重试机制
  - [ ] 监控异步任务状态

### 6.3 监控与告警检查清单

- [ ] **指标监控**
  - [ ] 设置关键性能指标（KPIs）
  - [ ] 配置实时监控仪表板
  - [ ] 实施日志集中管理
  - [ ] 建立性能基线
  
- [ ] **告警配置**
  - [ ] 配置阈值告警
  - [ ] 设置异常检测告警
  - [ ] 实现多级告警通知
  - [ ] 测试告警通道
  
- [ ] **容量规划**
  - [ ] 监控资源使用趋势
  - [ ] 预测容量需求
  - [ ] 制定扩容计划
  - [ ] 实施自动扩缩容

## 🛠️ 实践案例

### 7.1 案例一：电商大促性能优化

#### 7.1.1 问题背景
- **场景**: 电商平台双11大促
- **问题**: 高峰时段系统响应时间从平均200ms增加到2秒以上
- **影响**: 用户体验下降，订单流失率增加15%

#### 7.1.2 优化措施
1. **缓存策略优化**
   ```python
   # 实施多级缓存
   cache_config = {
       'l1_memory': {'ttl': 60, 'size': 10000},
       'l2_redis': {'ttl': 300, 'size': 100000},
       'l3_cdn': {'ttl': 3600, 'prefetch': True}
   }
   ```

2. **数据库优化**
   ```sql
   -- 添加索引
   CREATE INDEX idx_orders_user_id ON orders(user_id);
   CREATE INDEX idx_products_category ON products(category);
   
   -- 优化查询
   EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = ?;
   ```

3. **负载均衡配置**
   ```yaml
   load_balancer:
     algorithm: 'least_connections'
     health_check:
       interval: 10s
       timeout: 5s
     servers:
       - host: 'server1.example.com'
         weight: 1
       - host: 'server2.example.com' 
         weight: 1
   ```

#### 7.1.3 优化效果
- **响应时间**: 从2秒降低到300ms（提升85%）
- **吞吐量**: 从1000 RPS提升到5000 RPS（提升400%）
- **资源利用率**: CPU使用率从95%降低到70%
- **业务影响**: 订单流失率恢复到正常水平

### 7.2 案例二：AI模型服务性能优化

#### 7.2.1 问题背景
- **场景**: 多模型AI推理服务
- **问题**: GPU利用率低（30%），推理延迟不稳定
- **影响**: 服务成本高，用户体验不一致

#### 7.2.2 优化措施
1. **批处理优化**
   ```python
   batch_optimizer = BatchProcessor(
       max_batch_size=32,
       max_wait_time=10,  # 毫秒
       dynamic_batching=True
   )
   ```

2. **模型路由优化**
   ```python
   router = IntelligentModelRouter(
       selection_strategy='performance_based',
       fallback_strategy='degradation'
   )
   ```

3. **资源调度优化**
   ```python
   scheduler = ResourceScheduler(
       gpu_allocation='dynamic',
       memory_management='intelligent',
       priority_queue=True
   )
   ```

#### 7.2.3 优化效果
- **GPU利用率**: 从30%提升到85%（提升183%）
- **推理延迟**: P95延迟从5秒降低到1秒（提升80%）
- **服务成本**: 降低60%
- **服务质量**: 服务可用性从99%提升到99.9%

## 🗺️ 实施路线图

### 8.1 短期优化（1-4周）

```
第1周: 评估与规划
  ├── 性能基准测试
  ├── 瓶颈分析
  ├── 优化目标设定
  └── 实施计划制定

第2周: 基础优化
  ├── 系统参数调优
  ├── 应用配置优化
  ├── 缓存策略实施
  └── 监控体系建立

第3周: 代码级优化
  ├── 性能热点分析
  ├── 算法优化
  ├── 数据库查询优化
  └── 内存管理优化

第4周: 测试与验证
  ├── 性能测试
  ├── 压力测试
  ├── 优化效果验证
  └── 文档编写
```

### 8.2 中期优化（1-3月）

```
第1-2月: 架构优化
  ├── 微服务拆分
  ├── 异步处理改造
  ├── 消息队列引入
  └── 读写分离实施

第2-3月: 高级优化
  ├── 智能负载均衡
  ├── 自适应缓存
  ├── 预测性扩容
  └── 自愈系统建设
```

### 8.3 长期优化（3-6月）

```
第3-4月: 智能化优化
  ├── AI驱动的性能优化
  ├── 自动化调参系统
  ├── 智能告警与自愈
  └── 预测性维护

第5-6月: 平台化建设
  ├── 性能优化平台
  ├── 一站式监控诊断
  ├── 知识库建设
  └── 团队能力培养
```

## 📝 总结

性能优化是一个系统工程，需要从多个层面综合考虑：

### 9.1 核心原则

1. **数据驱动决策**
   - 基于实际数据而非直觉
   - 建立性能基准和监控体系
   - 持续测量和验证

2. **渐进式优化**
   - 从高ROI的优化开始
   - 小步快跑，快速验证
   - 风险可控，影响有限

3. **全链路思维**
   - 考虑整个请求链路的性能
   - 识别瓶颈而非症状
   - 系统化解决方案

### 9.2 关键成功因素

1. **技术因素**
   - 合适的工具和技术栈
   - 完善的监控和诊断能力
   - 自动化测试和部署

2. **组织因素**
   - 跨团队协作
   - 明确的职责和流程
   - 持续学习和改进文化

3. **流程因素**
   - 标准化的优化流程
   - 知识管理和分享
   - 定期审查和迭代

### 9.3 开始优化的第一步

如果您是第一次进行性能优化，建议从以下步骤开始：

1. **建立基线**: 运行性能测试，了解当前状态
2. **识别瓶颈**: 使用 profiling 工具找到性能热点
3. **实施简单优化**: 如调整配置、添加缓存
4. **验证效果**: 重新测试，确认改进
5. **迭代改进**: 重复上述过程，逐步优化

记住：**性能优化不是一次性的项目，而是持续的过程**。随着业务发展和技术演进，需要不断调整和优化。

---
**最后更新**: 2026-03-07  
**文档版本**: 2.0.0  
**维护团队**: RANGEN 性能优化工作组  

> ⚡ **提示**: 性能优化需要平衡多个目标：速度、资源使用、成本、可维护性等。在优化时请考虑整体系统效益，避免过度优化。