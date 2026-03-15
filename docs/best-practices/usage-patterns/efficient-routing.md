# 🚀 高效路由策略

> RANGEN 系统智能模型选择和请求路由的最佳实践

## 🎯 概述

RANGEN 系统采用多模型架构，支持 DeepSeek、Step-3.5-Flash、本地开源模型等多种 LLM 提供商。高效的路由策略是平衡性能、成本和可靠性的关键。

### 1.1 路由策略的重要性
- **成本优化**: 合理分配请求，降低 API 成本
- **性能提升**: 为不同任务选择最合适的模型
- **可靠性保障**: 故障转移和降级策略确保服务连续性
- **质量保证**: 复杂任务使用更强模型，简单任务使用经济模型

### 1.2 目标读者
- 系统管理员和运维工程师
- 技术架构师和解决方案工程师
- 成本控制和性能优化专家
- 智能体系统开发者

## 📊 路由策略类型

### 2.1 基于复杂度的路由

#### 2.1.1 复杂度评估标准
```python
# 复杂度评估函数示例
def evaluate_query_complexity(query, context=None):
    """评估查询复杂度"""
    scores = {
        'lexical': _lexical_complexity(query),
        'semantic': _semantic_complexity(query),
        'structural': _structural_complexity(query),
        'contextual': _contextual_complexity(query, context)
    }
    
    # 权重分配
    weights = {
        'lexical': 0.2,      # 词汇复杂度
        'semantic': 0.4,     # 语义复杂度
        'structural': 0.2,   # 结构复杂度
        'contextual': 0.2    # 上下文复杂度
    }
    
    # 计算总分
    total_score = sum(scores[dim] * weights[dim] for dim in scores)
    return total_score
```

#### 2.1.2 复杂度阈值配置
```yaml
# config/routing.yaml
routing_thresholds:
  simple:
    max_complexity: 0.3
    description: "简单查询，适合 Step-3.5-Flash"
    recommended_models:
      - step-3.5-flash
      - local-llama-3b
    
  medium:
    min_complexity: 0.3
    max_complexity: 0.7
    description: "中等复杂度，适合标准模型"
    recommended_models:
      - deepseek-chat
      - step-3.5-flash
    
  complex:
    min_complexity: 0.7
    description: "复杂查询，需要强大推理能力"
    recommended_models:
      - deepseek-reasoner
      - deepseek-chat
      - local-qwen-14b
```

### 2.2 基于成本的路由

#### 2.2.1 成本计算模型
```python
class CostBasedRouter:
    """基于成本的路由器"""
    
    def __init__(self, cost_config):
        self.cost_config = cost_config
        
    def calculate_estimated_cost(self, query, model):
        """估算处理成本"""
        # 估算 token 数量
        estimated_tokens = self._estimate_token_count(query)
        
        # 获取模型成本
        model_cost = self.cost_config.get(model, {}).get('cost_per_token', 0)
        
        # 计算估算成本
        estimated_cost = estimated_tokens * model_cost
        
        return {
            'estimated_tokens': estimated_tokens,
            'model_cost': model_cost,
            'estimated_cost': estimated_cost,
            'model': model
        }
    
    def select_model_by_cost(self, query, candidate_models):
        """基于成本选择模型"""
        cost_estimates = []
        
        for model in candidate_models:
            estimate = self.calculate_estimated_cost(query, model)
            cost_estimates.append(estimate)
        
        # 按成本排序
        cost_estimates.sort(key=lambda x: x['estimated_cost'])
        
        # 选择成本最低的合适模型
        return cost_estimates[0] if cost_estimates else None
```

#### 2.2.2 成本优化配置
```yaml
# config/cost-optimization.yaml
cost_optimization:
  enabled: true
  budget_per_day: 50.0  # 每日预算（美元）
  priority_levels:
    high:
      max_cost_multiplier: 2.0
      description: "高优先级任务，可接受较高成本"
    
    medium:
      max_cost_multiplier: 1.0
      description: "中等优先级任务，平衡成本和质量"
    
    low:
      max_cost_multiplier: 0.5
      description: "低优先级任务，优先考虑成本"
  
  model_costs:
    deepseek-chat:
      cost_per_token: 0.000001
      max_tokens: 8192
      
    step-3.5-flash:
      cost_per_token: 0.0000005
      max_tokens: 4096
      
    local-llama-3b:
      cost_per_token: 0.0
      max_tokens: 2048
```

### 2.3 基于性能的路由

#### 2.3.1 性能监控和路由
```python
class PerformanceBasedRouter:
    """基于性能的路由器"""
    
    def __init__(self, performance_history):
        self.performance_history = performance_history
        
    def get_model_performance_score(self, model, time_window_minutes=15):
        """获取模型性能评分"""
        recent_performance = self._get_recent_performance(
            model, time_window_minutes
        )
        
        if not recent_performance:
            return 0.0
        
        # 计算综合性能评分
        scores = {
            'success_rate': recent_performance.get('success_rate', 0.0),
            'avg_response_time': 1.0 / (recent_performance.get('avg_response_time_ms', 1000) / 1000),
            'p95_response_time': 1.0 / (recent_performance.get('p95_response_time_ms', 2000) / 2000)
        }
        
        # 权重分配
        weights = {
            'success_rate': 0.5,
            'avg_response_time': 0.3,
            'p95_response_time': 0.2
        }
        
        # 计算总分
        total_score = sum(
            scores[metric] * weights[metric]
            for metric in scores
        )
        
        return total_score
    
    def select_model_by_performance(self, query, candidate_models):
        """基于性能选择模型"""
        performance_scores = []
        
        for model in candidate_models:
            score = self.get_model_performance_score(model)
            performance_scores.append({
                'model': model,
                'performance_score': score
            })
        
        # 按性能评分排序
        performance_scores.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return performance_scores[0] if performance_scores else None
```

## 🔧 路由配置实践

### 3.1 配置多层路由策略

#### 3.1.1 组合路由策略
```python
class MultiStrategyRouter:
    """多策略组合路由器"""
    
    def __init__(self, strategies):
        self.strategies = strategies
        self.weights = {
            'complexity': 0.4,
            'cost': 0.3,
            'performance': 0.3
        }
    
    def route_query(self, query, context=None):
        """多策略路由查询"""
        candidate_models = self._get_candidate_models(query, context)
        
        if len(candidate_models) == 1:
            return candidate_models[0]
        
        # 执行各个策略
        strategy_results = {}
        
        # 1. 复杂度策略
        if 'complexity' in self.strategies:
            complexity_score = self.strategies['complexity'].evaluate(query, context)
            strategy_results['complexity'] = complexity_score
        
        # 2. 成本策略
        if 'cost' in self.strategies:
            cost_scores = {}
            for model in candidate_models:
                cost = self.strategies['cost'].estimate_cost(query, model)
                cost_scores[model] = 1.0 / (cost + 0.000001)  # 成本越低分数越高
            strategy_results['cost'] = cost_scores
        
        # 3. 性能策略
        if 'performance' in self.strategies:
            perf_scores = {}
            for model in candidate_models:
                score = self.strategies['performance'].get_score(model)
                perf_scores[model] = score
            strategy_results['performance'] = perf_scores
        
        # 综合评分
        final_scores = {}
        for model in candidate_models:
            model_score = 0.0
            
            for strategy, scores in strategy_results.items():
                if isinstance(scores, dict):
                    # 策略结果为每个模型的分数
                    model_score += scores.get(model, 0.0) * self.weights[strategy]
                else:
                    # 策略结果为单个分数（如复杂度）
                    model_score += scores * self.weights[strategy]
            
            final_scores[model] = model_score
        
        # 选择分数最高的模型
        best_model = max(final_scores.items(), key=lambda x: x[1])[0]
        
        return best_model
```

#### 3.1.2 动态权重调整
```python
class AdaptiveRouterWeights:
    """自适应路由权重"""
    
    def __init__(self, initial_weights):
        self.current_weights = initial_weights
        self.performance_history = []
        self.max_history = 1000
    
    def adjust_weights(self, routing_result):
        """根据路由结果调整权重"""
        # 记录路由结果
        self.performance_history.append(routing_result)
        
        if len(self.performance_history) > self.max_history:
            self.performance_history.pop(0)
        
        # 分析历史性能
        recent_performance = self.performance_history[-100:] if len(self.performance_history) >= 100 else self.performance_history
        
        if not recent_performance:
            return
        
        # 计算各策略的成功率
        strategy_success = {}
        strategy_counts = {}
        
        for result in recent_performance:
            strategy = result.get('strategy_used')
            success = result.get('success', False)
            
            if strategy:
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
                if success:
                    strategy_success[strategy] = strategy_success.get(strategy, 0) + 1
        
        # 更新权重
        for strategy in self.current_weights:
            count = strategy_counts.get(strategy, 0)
            if count > 10:  # 有足够样本
                success_rate = strategy_success.get(strategy, 0) / count
                
                # 根据成功率调整权重
                # 成功率越高，权重越大（上限不超过0.7）
                new_weight = min(0.7, success_rate * 0.8 + 0.2)
                
                # 平滑调整
                self.current_weights[strategy] = (
                    0.9 * self.current_weights[strategy] + 
                    0.1 * new_weight
                )
        
        # 归一化权重
        total = sum(self.current_weights.values())
        if total > 0:
            for strategy in self.current_weights:
                self.current_weights[strategy] /= total
```

### 3.2 智能体特定路由配置

#### 3.2.1 智能体路由偏好
```yaml
# config/agent_routing.yaml
agent_routing_preferences:
  research_assistant:
    default_model: deepseek-chat
    fallback_models:
      - step-3.5-flash
      - local-qwen-14b
    routing_strategy: "complexity_based"
    complexity_thresholds:
      simple: 0.3
      medium: 0.6
      complex: 0.8
  
  customer_support:
    default_model: step-3.5-flash
    fallback_models:
      - local-llama-3b
      - deepseek-chat
    routing_strategy: "performance_based"
    performance_requirements:
      max_response_time_ms: 3000
      min_success_rate: 0.95
  
  code_reviewer:
    default_model: deepseek-chat
    fallback_models:
      - step-3.5-flash
    routing_strategy: "hybrid"
    hybrid_weights:
      complexity: 0.6
      cost: 0.2
      performance: 0.2
```

#### 3.2.2 智能体路由覆盖
```python
class AgentSpecificRouter:
    """智能体特定的路由器"""
    
    def __init__(self, agent_config):
        self.agent_config = agent_config
        self.base_router = MultiStrategyRouter(
            strategies={
                'complexity': ComplexityBasedRouter(),
                'cost': CostBasedRouter(),
                'performance': PerformanceBasedRouter()
            }
        )
    
    def route_for_agent(self, agent_id, query, context):
        """为特定智能体路由"""
        agent_config = self.agent_config.get(agent_id, {})
        
        # 检查是否有特定的路由配置
        if 'routing_strategy' in agent_config:
            strategy = agent_config['routing_strategy']
            
            if strategy == "complexity_based":
                # 使用智能体的复杂度阈值
                thresholds = agent_config.get('complexity_thresholds', {})
                router = ComplexityBasedRouter(custom_thresholds=thresholds)
                return router.route(query, context)
            
            elif strategy == "performance_based":
                # 使用智能体的性能要求
                requirements = agent_config.get('performance_requirements', {})
                router = PerformanceBasedRouter(requirements=requirements)
                return router.route(query, context)
        
        # 使用基础路由器
        return self.base_router.route_query(query, context)
```

## 🔄 动态路由调整

### 4.1 实时性能监控和调整

#### 4.1.1 性能指标收集
```python
class RoutingPerformanceMonitor:
    """路由性能监控器"""
    
    def __init__(self):
        self.routing_decisions = []
        self.model_performance = {}
        self.max_records = 5000
    
    def record_routing_decision(self, decision):
        """记录路由决策"""
        self.routing_decisions.append(decision)
        
        if len(self.routing_decisions) > self.max_records:
            self.routing_decisions.pop(0)
        
        # 更新模型性能统计
        model = decision.get('selected_model')
        success = decision.get('success', False)
        response_time = decision.get('response_time_ms', 0)
        
        if model not in self.model_performance:
            self.model_performance[model] = {
                'total_requests': 0,
                'successful_requests': 0,
                'total_response_time': 0,
                'response_times': []
            }
        
        stats = self.model_performance[model]
        stats['total_requests'] += 1
        stats['total_response_time'] += response_time
        stats['response_times'].append(response_time)
        
        if success:
            stats['successful_requests'] += 1
        
        # 保留最近1000个响应时间样本
        if len(stats['response_times']) > 1000:
            stats['response_times'].pop(0)
    
    def get_model_performance_summary(self, model):
        """获取模型性能摘要"""
        if model not in self.model_performance:
            return None
        
        stats = self.model_performance[model]
        
        if stats['total_requests'] == 0:
            return None
        
        success_rate = stats['successful_requests'] / stats['total_requests']
        avg_response_time = stats['total_response_time'] / stats['total_requests']
        
        # 计算百分位数
        response_times = sorted(stats['response_times'])
        if response_times:
            p95_index = int(len(response_times) * 0.95)
            p95_response_time = response_times[p95_index] if p95_index < len(response_times) else response_times[-1]
        else:
            p95_response_time = 0
        
        return {
            'model': model,
            'total_requests': stats['total_requests'],
            'success_rate': success_rate,
            'avg_response_time_ms': avg_response_time,
            'p95_response_time_ms': p95_response_time,
            'timestamp': datetime.now().isoformat()
        }
```

#### 4.1.2 动态阈值调整
```python
class AdaptiveRoutingThresholds:
    """自适应路由阈值"""
    
    def __init__(self, initial_thresholds):
        self.current_thresholds = initial_thresholds
        self.learning_rate = 0.01
        self.min_threshold = 0.1
        self.max_threshold = 0.9
    
    def adjust_thresholds(self, performance_data):
        """根据性能数据调整阈值"""
        # 分析每个复杂度区间的性能
        complexity_ranges = {
            'simple': (0.0, self.current_thresholds['simple_max']),
            'medium': (self.current_thresholds['simple_max'], self.current_thresholds['medium_max']),
            'complex': (self.current_thresholds['medium_max'], 1.0)
        }
        
        for range_name, (min_val, max_val) in complexity_ranges.items():
            # 获取该区间内的请求性能
            range_performance = [
                p for p in performance_data
                if min_val <= p.get('complexity_score', 0) < max_val
            ]
            
            if len(range_performance) < 10:
                continue
            
            # 计算平均性能
            avg_success_rate = sum(p.get('success', 0) for p in range_performance) / len(range_performance)
            avg_response_time = sum(p.get('response_time_ms', 0) for p in range_performance) / len(range_performance)
            
            # 根据性能调整阈值
            if range_name == 'simple':
                # 如果简单区间性能好，可以扩大简单区间
                if avg_success_rate > 0.95 and avg_response_time < 2000:
                    # 扩大简单区间
                    self.current_thresholds['simple_max'] = min(
                        self.max_threshold,
                        self.current_thresholds['simple_max'] + self.learning_rate
                    )
                elif avg_success_rate < 0.8 or avg_response_time > 5000:
                    # 缩小简单区间
                    self.current_thresholds['simple_max'] = max(
                        self.min_threshold,
                        self.current_thresholds['simple_max'] - self.learning_rate
                    )
            
            elif range_name == 'medium':
                # 调整中等区间阈值
                # 类似逻辑...
                pass
            
            elif range_name == 'complex':
                # 调整复杂区间阈值
                # 类似逻辑...
                pass
        
        return self.current_thresholds
```

### 4.2 A/B 测试和实验

#### 4.2.1 路由实验框架
```python
class RoutingExperiment:
    """路由实验框架"""
    
    def __init__(self, experiment_config):
        self.experiment_config = experiment_config
        self.variants = experiment_config.get('variants', {})
        self.assignment_method = experiment_config.get('assignment_method', 'random')
        self.results = {}
    
    def assign_variant(self, request_id, context=None):
        """分配实验变体"""
        if self.assignment_method == 'random':
            # 随机分配
            variant_names = list(self.variants.keys())
            variant = random.choice(variant_names)
            
        elif self.assignment_method == 'hash_based':
            # 基于请求ID哈希的确定性分配
            hash_value = hash(request_id) % 100
            cumulative_percentage = 0
            
            for variant_name, variant_config in self.variants.items():
                traffic_percentage = variant_config.get('traffic_percentage', 0)
                cumulative_percentage += traffic_percentage
                
                if hash_value < cumulative_percentage:
                    variant = variant_name
                    break
        
        elif self.assignment_method == 'context_aware':
            # 基于上下文的分配
            variant = self._assign_by_context(context)
        
        else:
            variant = 'control'
        
        return variant
    
    def record_result(self, request_id, variant, result):
        """记录实验结果"""
        if variant not in self.results:
            self.results[variant] = {
                'total_requests': 0,
                'successful_requests': 0,
                'total_response_time': 0,
                'results': []
            }
        
        stats = self.results[variant]
        stats['total_requests'] += 1
        stats['total_response_time'] += result.get('response_time_ms', 0)
        stats['results'].append(result)
        
        if result.get('success', False):
            stats['successful_requests'] += 1
        
        # 保留最近1000个结果
        if len(stats['results']) > 1000:
            stats['results'].pop(0)
    
    def analyze_results(self):
        """分析实验结果"""
        analysis = {}
        
        for variant, stats in self.results.items():
            if stats['total_requests'] == 0:
                continue
            
            success_rate = stats['successful_requests'] / stats['total_requests']
            avg_response_time = stats['total_response_time'] / stats['total_requests']
            
            # 计算置信区间
            ci = self._calculate_confidence_interval(success_rate, stats['total_requests'])
            
            analysis[variant] = {
                'success_rate': success_rate,
                'success_rate_ci': ci,
                'avg_response_time_ms': avg_response_time,
                'total_requests': stats['total_requests'],
                'sample_size_adequate': stats['total_requests'] >= 100
            }
        
        return analysis
```

#### 4.2.2 实验配置示例
```yaml
# config/routing_experiments.yaml
experiments:
  complexity_threshold_optimization:
    enabled: true
    description: "优化复杂度阈值"
    variants:
      control:
        traffic_percentage: 25
        thresholds:
          simple_max: 0.3
          medium_max: 0.7
      
      variant_a:
        traffic_percentage: 25
        thresholds:
          simple_max: 0.4
          medium_max: 0.8
      
      variant_b:
        traffic_percentage: 25
        thresholds:
          simple_max: 0.25
          medium_max: 0.65
      
      variant_c:
        traffic_percentage: 25
        thresholds:
          simple_max: 0.35
          medium_max: 0.75
    
    metrics:
      primary: "success_rate"
      secondary: ["avg_response_time_ms", "cost_per_request"]
    
    stopping_criteria:
      min_sample_size: 1000
      max_duration_days: 7
      significance_level: 0.05
```

## 🚀 故障转移和降级策略

### 5.1 多级故障转移

#### 5.1.1 故障检测和转移
```python
class FaultTolerantRouter:
    """容错路由器"""
    
    def __init__(self, primary_model, fallback_chain):
        self.primary_model = primary_model
        self.fallback_chain = fallback_chain  # 降级链
        self.failure_counts = {}
        self.circuit_breakers = {}
        
    def route_with_fallback(self, query, context=None):
        """带故障转移的路由"""
        candidates = [self.primary_model] + self.fallback_chain
        
        for i, model in enumerate(candidates):
            # 检查断路器状态
            if self._is_circuit_open(model):
                continue
            
            try:
                # 尝试使用该模型
                result = self._call_model(model, query, context)
                
                if result.get('success', False):
                    # 成功，重置失败计数
                    self._record_success(model)
                    return {
                        'selected_model': model,
                        'result': result,
                        'fallback_level': i
                    }
                else:
                    # 记录失败
                    self._record_failure(model, result.get('error'))
                    
            except Exception as e:
                # 记录异常
                self._record_failure(model, str(e))
        
        # 所有模型都失败
        return {
            'selected_model': None,
            'error': '所有模型都失败',
            'fallback_level': len(candidates)
        }
    
    def _is_circuit_open(self, model):
        """检查断路器是否打开"""
        if model not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[model]
        return breaker.state == CircuitState.OPEN
    
    def _record_failure(self, model, error):
        """记录失败"""
        if model not in self.failure_counts:
            self.failure_counts[model] = {
                'count': 0,
                'last_failure': None,
                'errors': []
            }
        
        stats = self.failure_counts[model]
        stats['count'] += 1
        stats['last_failure'] = datetime.now()
        stats['errors'].append(error)
        
        # 如果连续失败超过阈值，打开断路器
        if stats['count'] >= 5:  # 5次连续失败
            if model not in self.circuit_breakers:
                self.circuit_breakers[model] = CircuitBreaker()
            
            breaker = self.circuit_breakers[model]
            for _ in range(stats['count']):
                breaker._on_failure()
    
    def _record_success(self, model):
        """记录成功"""
        if model in self.failure_counts:
            # 重置失败计数
            self.failure_counts[model]['count'] = 0
            
        # 如果是半开状态，记录成功
        if model in self.circuit_breakers:
            breaker = self.circuit_breakers[model]
            if breaker.state == CircuitState.HALF_OPEN:
                breaker._on_success()
```

#### 5.1.2 智能降级策略
```python
class IntelligentDegradation:
    """智能降级策略"""
    
    def __init__(self, degradation_levels):
        self.degradation_levels = degradation_levels
        self.current_level = 0  # 0 = 正常，数字越大降级越严重
        self.system_metrics = {}
        
    def assess_system_health(self):
        """评估系统健康状况"""
        metrics = self._collect_system_metrics()
        self.system_metrics = metrics
        
        # 计算健康分数
        health_score = 0.0
        
        # 1. 错误率
        error_rate = metrics.get('error_rate', 0.0)
        if error_rate < 0.01:
            health_score += 0.3
        elif error_rate < 0.05:
            health_score += 0.2
        elif error_rate < 0.1:
            health_score += 0.1
        
        # 2. 响应时间
        avg_response_time = metrics.get('avg_response_time_ms', 0)
        if avg_response_time < 2000:
            health_score += 0.3
        elif avg_response_time < 5000:
            health_score += 0.2
        elif avg_response_time < 10000:
            health_score += 0.1
        
        # 3. 资源使用率
        cpu_usage = metrics.get('cpu_usage', 0.0)
        memory_usage = metrics.get('memory_usage', 0.0)
        
        if cpu_usage < 0.5 and memory_usage < 0.7:
            health_score += 0.4
        elif cpu_usage < 0.7 and memory_usage < 0.8:
            health_score += 0.2
        elif cpu_usage < 0.9 and memory_usage < 0.9:
            health_score += 0.1
        
        return health_score
    
    def determine_degradation_level(self):
        """确定降级级别"""
        health_score = self.assess_system_health()
        
        # 根据健康分数选择降级级别
        if health_score >= 0.8:
            new_level = 0  # 正常
        elif health_score >= 0.6:
            new_level = 1  # 轻度降级
        elif health_score >= 0.4:
            new_level = 2  # 中度降级
        elif health_score >= 0.2:
            new_level = 3  # 重度降级
        else:
            new_level = 4  # 紧急降级
        
        # 应用新的降级级别
        if new_level != self.current_level:
            self._apply_degradation_level(new_level)
            self.current_level = new_level
        
        return self.current_level
    
    def _apply_degradation_level(self, level):
        """应用降级级别"""
        if level >= len(self.degradation_levels):
            return
        
        degradation_config = self.degradation_levels[level]
        
        # 应用降级配置
        # 1. 调整路由策略
        if 'routing_strategy' in degradation_config:
            self._update_routing_strategy(degradation_config['routing_strategy'])
        
        # 2. 限制并发数
        if 'max_concurrency' in degradation_config:
            self._limit_concurrency(degradation_config['max_concurrency'])
        
        # 3. 启用缓存
        if 'enable_caching' in degradation_config:
            self._enable_caching(degradation_config['enable_caching'])
        
        # 4. 简化处理
        if 'simplify_processing' in degradation_config:
            self._simplify_processing(degradation_config['simplify_processing'])
```

### 5.2 降级配置示例

#### 5.2.1 降级级别定义
```yaml
# config/degradation_levels.yaml
degradation_levels:
  - level: 0
    name: "normal"
    description: "正常模式"
    routing_strategy: "optimized"
    max_concurrency: 100
    enable_caching: true
    simplify_processing: false
  
  - level: 1
    name: "light_degradation"
    description: "轻度降级"
    routing_strategy: "cost_optimized"
    max_concurrency: 50
    enable_caching: true
    simplify_processing: false
  
  - level: 2
    name: "medium_degradation"
    description: "中度降级"
    routing_strategy: "performance_optimized"
    max_concurrency: 20
    enable_caching: true
    simplify_processing: true
    simplified_models:
      - step-3.5-flash
      - local-llama-3b
  
  - level: 3
    name: "heavy_degradation"
    description: "重度降级"
    routing_strategy: "failover"
    max_concurrency: 10
    enable_caching: true
    simplify_processing: true
    simplified_models:
      - local-llama-3b
    max_response_length: 500
  
  - level: 4
    name: "emergency"
    description: "紧急模式"
    routing_strategy: "minimal"
    max_concurrency: 5
    enable_caching: true
    simplify_processing: true
    simplified_models:
      - local-llama-3b
    max_response_length: 200
    disable_features:
      - complex_reasoning
      - multi_step_processing
      - external_api_calls
```

## 📈 监控和优化

### 6.1 路由性能监控

#### 6.1.1 关键性能指标
```python
class RoutingMetricsDashboard:
    """路由指标仪表板"""
    
    def __init__(self):
        self.metrics_store = {}
        self.alert_manager = AlertManager()
    
    def collect_metrics(self):
        """收集路由指标"""
        metrics = {
            # 总体指标
            'total_requests': self._get_total_requests(),
            'success_rate': self._get_success_rate(),
            'avg_response_time': self._get_avg_response_time(),
            
            # 模型特定指标
            'model_performance': self._get_model_performance(),
            
            # 路由策略指标
            'strategy_effectiveness': self._get_strategy_effectiveness(),
            
            # 成本指标
            'cost_metrics': self._get_cost_metrics(),
            
            # 错误分析
            'error_analysis': self._get_error_analysis(),
            
            # 降级状态
            'degradation_status': self._get_degradation_status()
        }
        
        return metrics
    
    def generate_report(self, time_range='1h'):
        """生成路由性能报告"""
        metrics = self.collect_metrics()
        
        report = {
            'summary': {
                'time_range': time_range,
                'overall_performance': self._calculate_overall_performance(metrics),
                'key_insights': self._extract_key_insights(metrics)
            },
            
            'detailed_analysis': {
                'model_comparison': self._compare_models(metrics),
                'strategy_comparison': self._compare_strategies(metrics),
                'cost_analysis': self._analyze_costs(metrics),
                'error_patterns': self._identify_error_patterns(metrics)
            },
            
            'recommendations': self._generate_recommendations(metrics),
            
            'alerts': self.alert_manager.get_active_alerts()
        }
        
        return report
    
    def _calculate_overall_performance(self, metrics):
        """计算总体性能"""
        # 加权计算总体性能分数
        weights = {
            'success_rate': 0.4,
            'avg_response_time': 0.3,
            'cost_efficiency': 0.2,
            'error_rate': 0.1
        }
        
        scores = {
            'success_rate': metrics.get('success_rate', 0.0),
            'avg_response_time': 1.0 / (metrics.get('avg_response_time', 1.0) / 1000),
            'cost_efficiency': self._calculate_cost_efficiency(metrics),
            'error_rate': 1.0 - metrics.get('error_rate', 0.0)
        }
        
        # 归一化分数
        for key in scores:
            if key == 'avg_response_time':
                # 响应时间越低越好
                scores[key] = min(1.0, 3000 / (scores[key] * 1000))
        
        # 计算总分
        total_score = sum(scores[key] * weights[key] for key in weights)
        
        return {
            'score': total_score,
            'grade': self._score_to_grade(total_score),
            'components': scores
        }
    
    def _score_to_grade(self, score):
        """分数转换为等级"""
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B"
        elif score >= 0.6:
            return "C"
        elif score >= 0.5:
            return "D"
        else:
            return "F"
```

#### 6.1.2 自动优化建议
```python
class RoutingOptimizationAdvisor:
    """路由优化顾问"""
    
    def __init__(self, historical_data):
        self.historical_data = historical_data
        self.optimization_rules = self._load_optimization_rules()
    
    def generate_optimization_suggestions(self, current_metrics):
        """生成优化建议"""
        suggestions = []
        
        # 1. 检查成功率
        success_rate = current_metrics.get('success_rate', 0.0)
        if success_rate < 0.9:
            suggestions.append({
                'type': 'success_rate_low',
                'severity': 'high',
                'description': f'成功率较低: {success_rate:.1%}',
                'recommendations': [
                    '检查高失败率模型，考虑降级或替换',
                    '增加故障转移模型的权重',
                    '优化提示工程和上下文管理'
                ]
            })
        
        # 2. 检查响应时间
        avg_response_time = current_metrics.get('avg_response_time_ms', 0)
        if avg_response_time > 5000:
            suggestions.append({
                'type': 'response_time_high',
                'severity': 'medium',
                'description': f'平均响应时间较高: {avg_response_time:.0f}ms',
                'recommendations': [
                    '考虑为简单查询使用更快的模型',
                    '优化批处理和并发设置',
                    '检查网络延迟和连接问题'
                ]
            })
        
        # 3. 检查成本
        cost_per_request = current_metrics.get('cost_metrics', {}).get('cost_per_request', 0)
        if cost_per_request > 0.01:  # 超过 $0.01
            suggestions.append({
                'type': 'cost_high',
                'severity': 'medium',
                'description': f'单次请求成本较高: ${cost_per_request:.4f}',
                'recommendations': [
                    '增加 Step-3.5-Flash 的使用比例',
                    '优化 token 使用，减少不必要的内容',
                    '启用响应缓存',
                    '考虑批量处理请求'
                ]
            })
        
        # 4. 检查模型利用率
        model_utilization = current_metrics.get('model_performance', {})
        underutilized_models = [
            model for model, stats in model_utilization.items()
            if stats.get('request_count', 0) < 10 and stats.get('success_rate', 0) > 0.8
        ]
        
        if underutilized_models:
            suggestions.append({
                'type': 'models_underutilized',
                'severity': 'low',
                'description': f'以下模型利用率较低: {", ".join(underutilized_models)}',
                'recommendations': [
                    f'考虑在路由策略中增加 {model} 的权重' for model in underutilized_models
                ]
            })
        
        return suggestions
```

### 6.2 持续优化流程

#### 6.2.1 优化工作流
```python
class ContinuousOptimizationWorkflow:
    """持续优化工作流"""
    
    def __init__(self):
        self.optimization_cycles = []
        self.current_cycle = None
    
    def start_optimization_cycle(self, cycle_config):
        """开始优化周期"""
        cycle = {
            'id': f"cycle_{len(self.optimization_cycles) + 1}",
            'config': cycle_config,
            'start_time': datetime.now(),
            'status': 'running',
            'experiments': [],
            'results': None
        }
        
        self.current_cycle = cycle
        self.optimization_cycles.append(cycle)
        
        return cycle['id']
    
    def add_experiment(self, experiment_config):
        """添加实验到当前周期"""
        if not self.current_cycle:
            raise ValueError("没有活动的优化周期")
        
        experiment = {
            'id': f"exp_{len(self.current_cycle['experiments']) + 1}",
            'config': experiment_config,
            'start_time': datetime.now(),
            'status': 'pending',
            'results': None
        }
        
        self.current_cycle['experiments'].append(experiment)
        
        # 执行实验
        self._execute_experiment(experiment)
        
        return experiment['id']
    
    def complete_optimization_cycle(self):
        """完成优化周期"""
        if not self.current_cycle:
            raise ValueError("没有活动的优化周期")
        
        # 收集所有实验结果
        all_results = []
        for experiment in self.current_cycle['experiments']:
            if experiment['results']:
                all_results.append(experiment['results'])
        
        # 分析结果
        analysis = self._analyze_results(all_results)
        
        # 生成优化建议
        recommendations = self._generate_recommendations(analysis)
        
        # 更新周期状态
        self.current_cycle['end_time'] = datetime.now()
        self.current_cycle['status'] = 'completed'
        self.current_cycle['results'] = analysis
        self.current_cycle['recommendations'] = recommendations
        
        # 应用最佳优化
        if recommendations and recommendations.get('should_apply', False):
            self._apply_optimizations(recommendations['optimizations'])
        
        # 生成报告
        report = self._generate_optimization_report(self.current_cycle)
        
        return report
```

#### 6.2.2 优化周期配置
```yaml
# config/optimization_cycles.yaml
optimization_cycles:
  daily_quick_optimization:
    schedule: "0 2 * * *"  # 每天凌晨2点
    duration_hours: 1
    objectives:
      - "improve_success_rate"
      - "reduce_avg_response_time"
    
    experiments:
      - type: "threshold_tuning"
        parameters: ["simple_max", "medium_max"]
        search_space:
          simple_max: [0.2, 0.3, 0.4]
          medium_max: [0.6, 0.7, 0.8]
      
      - type: "model_weight_adjustment"
        parameters: ["deepseek_weight", "stepflash_weight", "local_weight"]
        search_space:
          deepseek_weight: [0.3, 0.4, 0.5]
          stepflash_weight: [0.3, 0.4, 0.5]
          local_weight: [0.1, 0.2, 0.3]
    
    evaluation_metrics:
      primary: "success_rate"
      secondary: ["avg_response_time_ms", "cost_per_request"]
    
    stopping_criteria:
      min_improvement: 0.01
      max_iterations: 10
  
  weekly_deep_optimization:
    schedule: "0 4 * * 0"  # 每周日凌晨4点
    duration_hours: 4
    objectives:
      - "reduce_cost_by_10_percent"
      - "maintain_success_rate_above_90"
    
    experiments:
      - type: "routing_strategy_comparison"
        strategies: ["complexity_based", "cost_based", "performance_based", "hybrid"]
      
      - type: "degradation_policy_tuning"
        parameters: ["degradation_thresholds", "fallback_chains"]
    
    evaluation_metrics:
      primary: "cost_per_request"
      secondary: ["success_rate", "user_satisfaction_score"]
    
    stopping_criteria:
      min_improvement: 0.05
      max_iterations: 20
```

## 📋 实施指南

### 7.1 分阶段实施计划

#### 7.1.1 阶段1：基础路由
1. **目标**: 实现基本的模型选择功能
2. **时间**: 1-2周
3. **任务**:
   - 配置基础模型连接
   - 实现简单复杂度评估
   - 设置基本的故障转移
4. **成功标准**:
   - 系统能够选择模型处理请求
   - 基础故障转移正常工作

#### 7.1.2 阶段2：智能路由
1. **目标**: 添加智能路由策略
2. **时间**: 2-3周
3. **任务**:
   - 实现多策略路由器
   - 添加性能监控
   - 配置成本优化
4. **成功标准**:
   - 路由策略能够根据复杂度、成本、性能选择模型
   - 成本降低20%以上

#### 7.1.3 阶段3：高级优化
1. **目标**: 实现自动优化和实验
2. **时间**: 3-4周
3. **任务**:
   - 实现A/B测试框架
   - 添加自适应调整
   - 配置智能降级
4. **成功标准**:
   - 系统能够自动优化路由策略
   - 在故障情况下优雅降级

### 7.2 配置检查清单

#### 7.2.1 基础配置
- [ ] 模型API密钥正确配置
- [ ] 基础路由阈值设置合理
- [ ] 故障转移链配置完整
- [ ] 监控系统集成正常

#### 7.2.2 高级配置
- [ ] 多策略路由器权重配置
- [ ] 成本优化参数设置
- [ ] 性能监控阈值配置
- [ ] 降级策略定义完整

#### 7.2.3 优化配置
- [ ] A/B测试框架配置
- [ ] 自适应调整参数设置
- [ ] 优化周期计划配置
- [ ] 告警和通知设置

### 7.3 性能基准测试

#### 7.3.1 测试场景
```yaml
benchmark_scenarios:
  simple_queries:
    description: "简单查询测试"
    queries: 1000
    query_complexity: "low"
    expected_success_rate: >0.95
    expected_avg_response_time: <2000ms
    target_model: "step-3.5-flash"
  
  complex_queries:
    description: "复杂查询测试"
    queries: 500
    query_complexity: "high"
    expected_success_rate: >0.85
    expected_avg_response_time: <5000ms
    target_model: "deepseek-chat"
  
  mixed_workload:
    description: "混合工作负载测试"
    queries: 2000
    query_mix:
      simple: 60%
      medium: 30%
      complex: 10%
    expected_success_rate: >0.90
    expected_avg_response_time: <3000ms
    expected_cost_per_request: <$0.005
```

#### 7.3.2 基准测试脚本
```python
def run_routing_benchmark(scenario_config):
    """运行路由基准测试"""
    results = {
        'scenario': scenario_config['description'],
        'start_time': datetime.now(),
        'metrics': {},
        'detailed_results': []
    }
    
    # 准备测试数据
    test_queries = generate_test_queries(scenario_config)
    
    # 运行测试
    for i, query in enumerate(test_queries):
        start_time = time.time()
        
        # 执行路由和处理
        routing_result = router.route_query(query)
        processing_result = process_with_model(
            routing_result['