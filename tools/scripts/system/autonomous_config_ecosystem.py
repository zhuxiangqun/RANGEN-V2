#!/usr/bin/env python3
"""
自主配置生态系统 - 阶段6: 构建完全自主的配置生态
实现配置的完全自主发现、学习、优化和进化
"""

import time
import logging
import threading
import asyncio
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
import random
import math

logger = logging.getLogger(__name__)

@dataclass
class ConfigEntity:
    """配置实体"""
    name: str
    value: Any
    data_type: str
    description: str
    constraints: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    last_modified: datetime = field(default_factory=datetime.now)
    version: int = 1
    confidence_score: float = get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'value': self.value,
            'data_type': self.data_type,
            'description': self.description,
            'constraints': self.constraints,
            'dependencies': list(self.dependencies),
            'tags': list(self.tags),
            'last_modified': self.last_modified.isoformat(),
            'version': self.version,
            'confidence_score': self.confidence_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigEntity':
        """从字典创建"""
        return cls(
            name=data['name'],
            value=data['value'],
            data_type=data['data_type'],
            description=data['description'],
            constraints=data['constraints'],
            dependencies=data.get('dependencies', []),
            tags=set(data.get('tags', [])),
            last_modified=datetime.fromisoformat(data['last_modified']),
            version=data.get('version', 1),
            confidence_score=data.get('confidence_score', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
        )

@dataclass
class ConfigEnvironment:
    """配置环境"""
    name: str
    description: str
    context_variables: Dict[str, Any] = field(default_factory=dict)
    active_configs: Dict[str, ConfigEntity] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_evaluated: datetime = field(default_factory=datetime.now)
    
    def calculate_fitness_score(self) -> float:
        """计算适应度评分"""
        if not self.performance_metrics:
            return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
        
        # 基于性能指标计算综合评分
        weights = {
            'response_time': -get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")),  # 负权重，越小越好
            'throughput': get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")),
            'error_rate': -0.2,
            'resource_efficiency': 0.2
        }
        
        score = 0
        total_weight = 0
        
        for metric, weight in weights.items():
            if metric in self.performance_metrics:
                value = self.performance_metrics[metric]
                # 标准化处理
                if metric == 'response_time':
                    normalized_value = max(0, 1 - value / 1000)  # 假设1000ms为基准
                elif metric == 'throughput':
                    normalized_value = min(1, value / 1000)  # 假设1000 req/s为基准
                elif metric == 'error_rate':
                    normalized_value = max(0, 1 - value)
                elif metric == 'resource_efficiency':
                    normalized_value = min(1, value)
                else:
                    normalized_value = get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))
                
                score += weight * normalized_value
                total_weight += abs(weight)
        
        return score / total_weight if total_weight > 0 else get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))

class AutonomousConfigLearner:
    """自主配置学习器"""
    
    def __init__(self):
        self.config_entities: Dict[str, ConfigEntity] = {}
        self.environments: Dict[str, ConfigEnvironment] = {}
        self.learning_history = []
        self.discovery_rules = self._load_discovery_rules()
        self.evolution_rules = self._load_evolution_rules()
        
        # 学习线程
        self.learning_thread = threading.Thread(target=self._continuous_learning)
        self.learning_thread.daemon = True
        self.learning_thread.start()
    
    def _load_discovery_rules(self) -> Dict[str, Any]:
        """加载发现规则"""
        return {
            'performance_based_discovery': {
                'trigger_metrics': ['response_time', 'throughput', 'error_rate'],
                'thresholds': {'response_time': 500, 'error_rate': 0.05},
                'discovery_actions': ['analyze_dependencies', 'find_optimal_values', 'create_new_configs']
            },
            'context_based_discovery': {
                'context_triggers': ['time_of_day', 'user_load', 'system_load'],
                'discovery_actions': ['adapt_to_context', 'predict_future_needs', 'optimize_for_scenario']
            },
            'pattern_based_discovery': {
                'patterns': ['seasonal', 'trend', 'anomaly'],
                'discovery_actions': ['learn_patterns', 'create_adaptive_rules', 'evolve_configurations']
            }
        }
    
    def _load_evolution_rules(self) -> Dict[str, Any]:
        """加载进化规则"""
        return {
            'mutation_rules': {
                'numeric_mutation': {'range': 0.1, 'probability': get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold"))},
                'categorical_mutation': {'probability': 0.2},
                'structure_mutation': {'probability': 0.1}
            },
            'crossover_rules': {
                'config_crossover': {'probability': 0.4},
                'environment_crossover': {'probability': 0.2}
            },
            'selection_rules': {
                'fitness_based_selection': {'top_percentile': 0.2},
                'diversity_based_selection': {'diversity_threshold': get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold"))}
            }
        }
    
    def discover_new_config(self, context: Dict[str, Any], 
                          performance_data: Dict[str, Any]) -> Optional[ConfigEntity]:
        """发现新的配置项"""
        
        # 1. 基于性能数据发现
        if self._should_discover_from_performance(performance_data):
            new_config = self._discover_performance_based_config(context, performance_data)
            if new_config:
                return new_config
        
        # 2. 基于上下文发现
        if self._should_discover_from_context(context):
            new_config = self._discover_context_based_config(context)
            if new_config:
                return new_config
        
        # 3. 基于模式发现
        if self._should_discover_from_patterns():
            new_config = self._discover_pattern_based_config()
            if new_config:
                return new_config
        
        return None
    
    def _should_discover_from_performance(self, performance_data: Dict[str, Any]) -> bool:
        """判断是否应该基于性能发现"""
        thresholds = self.discovery_rules['performance_based_discovery']['thresholds']
        
        return (
            performance_data.get('response_time', 0) > thresholds.get('response_time', 500) or
            performance_data.get('error_rate', 0) > thresholds.get('error_rate', 0.05)
        )
    
    def _should_discover_from_context(self, context: Dict[str, Any]) -> bool:
        """判断是否应该基于上下文发现"""
        context_triggers = self.discovery_rules['context_based_discovery']['context_triggers']
        
        return any(trigger in context for trigger in context_triggers)
    
    def _should_discover_from_patterns(self) -> bool:
        """判断是否应该基于模式发现"""
        # 简化实现，随机决定是否发现
        return random.random() < 0.1  # get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))%概率
    
    def _discover_performance_based_config(self, context: Dict[str, Any], 
                                         performance_data: Dict[str, Any]) -> Optional[ConfigEntity]:
        """基于性能发现配置"""
        
        # 如果响应时间过长，建议调整超时时间
        if performance_data.get('response_time', 0) > 1000:
            config_name = f"adaptive_timeout_{int(time.time())}"
            suggested_timeout = min(300, int(performance_data['response_time'] / 1000) + get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")))
            
            return ConfigEntity(
                name=config_name,
                value=suggested_timeout,
                data_type='int',
                description=f'基于性能自动发现的超时配置 (响应时间: {performance_data["response_time"]}ms)',
                constraints={'min': 5, 'max': 300},
                tags={'performance_based', 'timeout', 'auto_discovered'},
                confidence_score=0.7
            )
        
        return None
    
    def _discover_context_based_config(self, context: Dict[str, Any]) -> Optional[ConfigEntity]:
        """基于上下文发现配置"""
        
        # 如果是高峰时段，建议调整工作线程
        if context.get('is_peak_hours', False) and context.get('cpu_usage', 0) > 70:
            config_name = f"peak_workers_{int(time.time())}"
            suggested_workers = min(20, int(context.get('cpu_usage', 50) / 5))
            
            return ConfigEntity(
                name=config_name,
                value=suggested_workers,
                data_type='int',
                description=f'基于高峰时段自动发现的工作线程配置 (CPU: {context["cpu_usage"]}%)',
                constraints={'min': 1, 'max': 20},
                tags={'context_based', 'workers', 'peak_hours', 'auto_discovered'},
                confidence_score=get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold"))
            )
        
        return None
    
    def _discover_pattern_based_config(self) -> Optional[ConfigEntity]:
        """基于模式发现配置"""
        
        # 随机生成一个创新配置
        config_types = ['cache_strategy', 'load_balancing', 'retry_policy']
        selected_type = random.choice(config_types)
        
        config_name = f"innovative_{selected_type}_{int(time.time())}"
        
        if selected_type == 'cache_strategy':
            return ConfigEntity(
                name=config_name,
                value='adaptive_lru',
                data_type='str',
                description='基于模式发现的创新缓存策略',
                tags={'pattern_based', 'cache', 'innovative', 'auto_discovered'},
                confidence_score=0.6
            )
        
        return None
    
    def evolve_configurations(self, current_configs: Dict[str, ConfigEntity], 
                            performance_data: Dict[str, Any]) -> Dict[str, ConfigEntity]:
        """进化配置"""
        
        evolved_configs = current_configs.copy()
        
        # 1. 变异操作
        mutated_configs = self._apply_mutations(current_configs)
        evolved_configs.update(mutated_configs)
        
        # 2. 交叉操作
        crossover_configs = self._apply_crossover(current_configs)
        evolved_configs.update(crossover_configs)
        
        # 3. 选择操作
        selected_configs = self._apply_selection(evolved_configs, performance_data)
        
        return selected_configs
    
    def _apply_mutations(self, configs: Dict[str, ConfigEntity]) -> Dict[str, ConfigEntity]:
        """应用变异操作"""
        
        mutated = {}
        mutation_rules = self.evolution_rules['mutation_rules']
        
        for name, config in configs.items():
            if random.random() < mutation_rules['numeric_mutation']['probability']:
                if config.data_type in ['int', 'float']:
                    # 数值变异
                    mutation_range = mutation_rules['numeric_mutation']['range']
                    current_value = config.value
                    
                    if isinstance(current_value, (int, float)):
                        # 在约束范围内变异
                        min_val = config.constraints.get('min', current_value * get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
                        max_val = config.constraints.get('max', current_value * 1.5)
                        
                        mutation_amount = current_value * mutation_range * (random.random() - get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))) * 2
                        new_value = current_value + mutation_amount
                        new_value = max(min_val, min(max_val, new_value))
                        
                        mutated_config = ConfigEntity(
                            name=f"{name}_mutated_{int(time.time())}",
                            value=new_value,
                            data_type=config.data_type,
                            description=f'变异进化: {config.description}',
                            constraints=config.constraints,
                            dependencies=config.dependencies,
                            tags=config.tags | {'mutated', 'evolved'},
                            version=config.version + 1,
                            confidence_score=config.confidence_score * 0.9
                        )
                        mutated[mutated_config.name] = mutated_config
        
        return mutated
    
    def _apply_crossover(self, configs: Dict[str, ConfigEntity]) -> Dict[str, ConfigEntity]:
        """应用交叉操作"""
        
        crossover = {}
        crossover_rules = self.evolution_rules['crossover_rules']
        
        if len(configs) < 2:
            return crossover
        
        config_list = list(configs.values())
        
        for i in range(0, len(config_list) - 1, 2):
            if random.random() < crossover_rules['config_crossover']['probability']:
                parent1 = config_list[i]
                parent2 = config_list[i + 1]
                
                # 创建交叉后代
                if parent1.data_type == parent2.data_type and parent1.data_type in ['int', 'float']:
                    # 数值交叉
                    crossover_value = (parent1.value + parent2.value) / 2
                    
                    crossover_config = ConfigEntity(
                        name=f"crossover_{parent1.name}_{parent2.name}_{int(time.time())}",
                        value=crossover_value,
                        data_type=parent1.data_type,
                        description=f'交叉进化: {parent1.name} × {parent2.name}',
                        constraints={
                            'min': max(parent1.constraints.get('min', 0), parent2.constraints.get('min', 0)),
                            'max': min(parent1.constraints.get('max', float('inf')), parent2.constraints.get('max', float('inf')))
                        },
                        dependencies=list(set(parent1.dependencies + parent2.dependencies)),
                        tags=(parent1.tags & parent2.tags) | {'crossover', 'evolved'},
                        version=max(parent1.version, parent2.version) + 1,
                        confidence_score=(parent1.confidence_score + parent2.confidence_score) / 2
                    )
                    crossover[crossover_config.name] = crossover_config
        
        return crossover
    
    def _apply_selection(self, configs: Dict[str, ConfigEntity], 
                        performance_data: Dict[str, Any]) -> Dict[str, ConfigEntity]:
        """应用选择操作"""
        
        selection_rules = self.evolution_rules['selection_rules']
        
        # 基于适应度评分排序
        scored_configs = []
        for name, config in configs.items():
            # 计算配置的适应度评分（简化版）
            fitness_score = self._calculate_config_fitness(config, performance_data)
            scored_configs.append((name, config, fitness_score))
        
        # 按适应度排序
        scored_configs.sort(key=lambda x: x[2], reverse=True)
        
        # 选择前N%的配置
        top_percentile = selection_rules['fitness_based_selection']['top_percentile']
        selected_count = max(1, int(len(scored_configs) * top_percentile))
        
        selected_configs = {}
        for name, config, score in scored_configs[:selected_count]:
            selected_configs[name] = config
        
        return selected_configs
    
    def _calculate_config_fitness(self, config: ConfigEntity, 
                                performance_data: Dict[str, Any]) -> float:
        """计算配置适应度"""
        
        fitness = config.confidence_score
        
        # 基于性能数据的适应度调整
        if config.name.lower().find('timeout') >= 0:
            response_time = performance_data.get('response_time', 500)
            if response_time < 200:
                fitness += 0.2  # 响应快，超时配置合适
            elif response_time > 1000:
                fitness -= 0.2  # 响应慢，可能超时配置不合适
        
        elif config.name.lower().find('worker') >= 0:
            throughput = performance_data.get('throughput', get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")))
            if throughput > 500:
                fitness += 0.2  # 高吞吐量，工作线程配置合适
            elif throughput < 50:
                fitness -= 0.2  # 低吞吐量，可能工作线程不足
        
        return max(0, min(1, fitness))
    
    def _continuous_learning(self):
        """持续学习"""
        while True:
            try:
                # 模拟学习过程
                self._simulate_learning_cycle()
                time.sleep(300)  # 每5分钟进行一次学习周期
                
            except Exception as e:
                logger.error(f"持续学习异常: {e}")
                time.sleep(60)
    
    def _simulate_learning_cycle(self):
        """模拟学习周期"""
        
        # 记录学习历史
        learning_record = {
            'timestamp': datetime.now(),
            'discovered_configs': len([c for c in self.config_entities.values() if 'auto_discovered' in c.tags]),
            'evolved_configs': len([c for c in self.config_entities.values() if 'evolved' in c.tags]),
            'total_configs': len(self.config_entities),
            'active_environments': len(self.environments)
        }
        
        self.learning_history.append(learning_record)
        
        # 清理旧的学习历史
        if len(self.learning_history) > 1000:
            self.learning_history = self.learning_history[-500:]
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """获取学习统计"""
        return {
            'total_configs': len(self.config_entities),
            'auto_discovered_configs': len([c for c in self.config_entities.values() if 'auto_discovered' in c.tags]),
            'evolved_configs': len([c for c in self.config_entities.values() if 'evolved' in c.tags]),
            'active_environments': len(self.environments),
            'learning_cycles': len(self.learning_history),
            'avg_learning_cycle_duration': 300  # 模拟值
        }

class AutonomousConfigEcosystem:
    """自主配置生态系统"""
    
    def __init__(self):
        self.learner = AutonomousConfigLearner()
        self.active_environments: Dict[str, ConfigEnvironment] = {}
        self.ecosystem_rules = self._load_ecosystem_rules()
        self.evolution_thread = threading.Thread(target=self._continuous_evolution)
        self.evolution_thread.daemon = True
        self.evolution_thread.start()
        
        # 异步事件循环
        self.event_loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self._run_async_loop)
        self.async_thread.daemon = True
        self.async_thread.start()
    
    def _load_ecosystem_rules(self) -> Dict[str, Any]:
        """加载生态系统规则"""
        return {
            'environment_creation': {
                'auto_create_environments': True,
                'max_environments': get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")),
                'environment_lifetime': 3600  # 1小时
            },
            'config_lifecycle': {
                'max_config_age': 86400,  # 24小时
                'min_confidence_threshold': get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")),
                'auto_cleanup_enabled': True
            },
            'evolution_policies': {
                'evolution_interval': 600,  # 10分钟
                'max_generations': get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")),
                'convergence_threshold': 0.01
            }
        }
    
    def create_environment(self, name: str, context: Dict[str, Any], 
                          initial_configs: Dict[str, Any]) -> str:
        """创建配置环境"""
        
        environment = ConfigEnvironment(
            name=name,
            description=f"自主创建的环境: {name}",
            context_variables=context
        )
        
        # 初始化配置
        for config_name, config_value in initial_configs.items():
            config_entity = ConfigEntity(
                name=config_name,
                value=config_value,
                data_type=type(config_value).__name__,
                description=f"环境 {name} 的初始配置",
                tags={'environment_initial', 'auto_managed'}
            )
            environment.active_configs[config_name] = config_entity
        
        self.active_environments[name] = environment
        
        logger.info(f"✅ 创建自主配置环境: {name}")
        return name
    
    def get_optimal_config_for_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取针对上下文的最优配置"""
        
        # 1. 发现新的配置
        performance_data = self._simulate_performance_data(context)
        new_config = self.learner.discover_new_config(context, performance_data)
        
        if new_config:
            self.learner.config_entities[new_config.name] = new_config
            logger.info(f"🔍 发现新配置: {new_config.name} = {new_config.value}")
        
        # 2. 选择最适合的环境
        best_environment = self._select_best_environment(context)
        
        if best_environment:
            return {name: config.value for name, config in best_environment.active_configs.items()}
        
        # 3. 创建新的环境
        env_name = f"auto_env_{int(time.time())}"
        initial_configs = self._generate_initial_configs(context)
        
        self.create_environment(env_name, context, initial_configs)
        
        return initial_configs
    
    def _simulate_performance_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """模拟性能数据"""
        return {
            'response_time': 200 + (context.get('cpu_usage', 50) * 2),
            'throughput': get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")) - (context.get('memory_usage', 60) * get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))),
            'error_rate': max(0, (context.get('cpu_usage', 50) - 70) * 0.01),
            'resource_efficiency': get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")) - (context.get('memory_usage', 60) / get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))) * get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold"))
        }
    
    def _select_best_environment(self, context: Dict[str, Any]) -> Optional[ConfigEnvironment]:
        """选择最适合的环境"""
        
        if not self.active_environments:
            return None
        
        best_env = None
        best_score = -1
        
        for env in self.active_environments.values():
            # 计算环境与上下文的匹配度
            match_score = self._calculate_environment_match(env, context)
            
            if match_score > best_score:
                best_score = match_score
                best_env = env
        
        return best_env if best_score > get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")) else None
    
    def _calculate_environment_match(self, environment: ConfigEnvironment, 
                                   context: Dict[str, Any]) -> float:
        """计算环境匹配度"""
        
        match_score = 0
        factors = 0
        
        # 比较上下文变量
        for key, value in context.items():
            if key in environment.context_variables:
                env_value = environment.context_variables[key]
                
                if isinstance(value, (int, float)) and isinstance(env_value, (int, float)):
                    # 数值匹配度
                    if env_value != 0:
                        diff_ratio = abs(value - env_value) / env_value
                        match_score += max(0, 1 - diff_ratio)
                    else:
                        match_score += 1 if value == 0 else 0
                else:
                    # 类别匹配度
                    match_score += 1 if value == env_value else 0
                
                factors += 1
        
        return match_score / max(1, factors)
    
    def _generate_initial_configs(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成初始配置"""
        
        configs = {}
        
        # 基于上下文生成合理的初始配置
        cpu_usage = context.get('cpu_usage', 50)
        memory_usage = context.get('memory_usage', 60)
        
        # 超时时间配置
        if cpu_usage > 80:
            configs['timeout'] = 60
        elif cpu_usage < 20:
            configs['timeout'] = 20
        else:
            configs['timeout'] = 30
        
        # 工作线程配置
        configs['max_workers'] = max(1, min(16, int(cpu_usage / get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")))))
        
        # 缓存大小配置
        configs['cache_size'] = max(get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")), int(1000 * (1 - memory_usage / get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")))))
        
        return configs
    
    def _continuous_evolution(self):
        """持续进化"""
        while True:
            try:
                # 进化现有环境
                self._evolve_environments()
                
                # 清理过期配置
                self._cleanup_expired_configs()
                
                time.sleep(self.ecosystem_rules['evolution_policies']['evolution_interval'])
                
            except Exception as e:
                logger.error(f"持续进化异常: {e}")
                time.sleep(60)
    
    def _evolve_environments(self):
        """进化环境"""
        
        for env_name, environment in list(self.active_environments.items()):
            try:
                # 模拟性能数据
                performance_data = {
                    'response_time': 300 + random.randint(-get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")), get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))),
                    'throughput': 150 + random.randint(-50, 50),
                    'error_rate': random.uniform(0, 0.1),
                    'resource_efficiency': random.uniform(get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")), 0.9)
                }
                
                environment.performance_metrics = performance_data
                environment.last_evaluated = datetime.now()
                
                # 进化配置
                evolved_configs = self.learner.evolve_configurations(
                    environment.active_configs, performance_data)
                
                if evolved_configs != environment.active_configs:
                    environment.active_configs = evolved_configs
                    logger.info(f"🔄 环境 {env_name} 配置已进化")
                
            except Exception as e:
                logger.error(f"环境 {env_name} 进化异常: {e}")
    
    def _cleanup_expired_configs(self):
        """清理过期配置"""
        
        current_time = datetime.now()
        max_age = timedelta(seconds=self.ecosystem_rules['config_lifecycle']['max_config_age'])
        
        # 清理过期配置实体
        expired_configs = []
        for name, config in self.learner.config_entities.items():
            if current_time - config.last_modified > max_age:
                expired_configs.append(name)
        
        for name in expired_configs:
            del self.learner.config_entities[name]
        
        # 清理过期环境
        expired_environments = []
        for name, env in self.active_environments.items():
            if current_time - env.created_at > timedelta(seconds=self.ecosystem_rules['environment_creation']['environment_lifetime']):
                expired_environments.append(name)
        
        for name in expired_environments:
            del self.active_environments[name]
        
        if expired_configs or expired_environments:
            logger.info(f"🗑️ 清理了 {len(expired_configs)} 个过期配置和 {len(expired_environments)} 个过期环境")
    
    def _run_async_loop(self):
        """运行异步事件循环"""
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_forever()
    
    def get_ecosystem_stats(self) -> Dict[str, Any]:
        """获取生态系统统计"""
        return {
            'active_environments': len(self.active_environments),
            'total_configs': len(self.learner.config_entities),
            'auto_discovered_configs': len([c for c in self.learner.config_entities.values() if 'auto_discovered' in c.tags]),
            'evolved_configs': len([c for c in self.learner.config_entities.values() if 'evolved' in c.tags]),
            'learning_stats': self.learner.get_learning_stats(),
            'evolution_active': self.evolution_thread.is_alive(),
            'async_loop_active': self.async_thread.is_alive()
        }

# 全局自主配置生态系统实例
_autonomous_config_ecosystem = None

def get_autonomous_config_ecosystem() -> AutonomousConfigEcosystem:
    """获取自主配置生态系统实例"""
    global _autonomous_config_ecosystem
    if _autonomous_config_ecosystem is None:
        _autonomous_config_ecosystem = AutonomousConfigEcosystem()
    return _autonomous_config_ecosystem

def get_autonomous_config(context: Dict[str, Any]) -> Dict[str, Any]:
    """获取自主配置"""
    return get_autonomous_config_ecosystem().get_optimal_config_for_context(context)

def create_autonomous_environment(name: str, context: Dict[str, Any], 
                                initial_configs: Dict[str, Any]) -> str:
    """创建自主环境"""
    return get_autonomous_config_ecosystem().create_environment(name, context, initial_configs)

def get_ecosystem_stats() -> Dict[str, Any]:
    """获取生态系统统计"""
    return get_autonomous_config_ecosystem().get_ecosystem_stats()
