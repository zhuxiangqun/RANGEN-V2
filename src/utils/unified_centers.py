#!/usr/bin/env python3
"""
统一中心系统
RANGEN系统的核心架构，提供所有中心模块的统一访问接口
"""

import os

import logging
import time
from typing import Dict, Any, Optional, Union, List, Callable
from functools import wraps
from src.core.unified_parameter_learner import get_parameter_learner


# 初始化日志
logger = logging.getLogger(__name__)

# 边缘计算和量子计算支持类
class EdgeNodeManager:
    """边缘节点管理器"""
    
    def __init__(self):
        self.nodes = {}
        self.heartbeat_interval = 30
    
    def register_node(self, node_id: str, node_info: Dict[str, Any]):
        """注册边缘节点"""
        self.nodes[node_id] = {
            'info': node_info,
            'last_heartbeat': time.time(),
            'status': 'active'
        }
    
    def get_active_nodes(self) -> List[str]:
        """获取活跃节点"""
        current_time = time.time()
        active_nodes = []
        
        for node_id, node_info in self.nodes.items():
            if current_time - node_info['last_heartbeat'] < self.heartbeat_interval:
                active_nodes.append(node_id)
        
        return active_nodes

class DistributedProcessor:
    """分布式处理器"""
    
    def __init__(self):
        self.tasks = {}
        self.results = {}
    
    def distribute_task(self, task_id: str, task_data: Any, target_nodes: List[str]) -> Dict[str, Any]:
        """分发任务到边缘节点"""
        self.tasks[task_id] = {
            'data': task_data,
            'target_nodes': target_nodes,
            'status': 'distributed',
            'created_at': time.time()
        }
        
        return {
            'task_id': task_id,
            'status': 'distributed',
            'target_nodes': target_nodes
        }

class LatencyOptimizer:
    """延迟优化器"""
    
    def __init__(self):
        self.optimization_strategies = ['edge_processing', 'caching', 'compression']
    
    def optimize(self, request_data: Any, target_latency: float) -> Dict[str, Any]:
        """优化延迟"""
        return {
            'strategy': 'edge_processing',
            'estimated_latency': 50.0,
            'optimization_applied': True
        }

class EdgeSynchronizer:
    """边缘同步器"""
    
    def __init__(self):
        self.sync_queue = []
        self.sync_status = {}
    
    def sync_data(self, data: Any, target_nodes: List[str]) -> Dict[str, Any]:
        """同步数据到边缘节点"""
        sync_id = f"sync_{int(time.time())}"
        self.sync_queue.append({
            'sync_id': sync_id,
            'data': data,
            'target_nodes': target_nodes,
            'status': 'pending'
        })
        
        return {
            'sync_id': sync_id,
            'status': 'queued',
            'target_nodes': target_nodes
        }

class QuantumAlgorithmManager:
    """量子算法管理器"""
    
    def __init__(self):
        self.algorithms = {}
        self.execution_history = []
    
    def register_algorithm(self, name: str, algorithm_info: Dict[str, Any]):
        """注册量子算法"""
        self.algorithms[name] = algorithm_info
    
    def execute_algorithm(self, name: str, input_data: Any) -> Any:
        """执行量子算法"""
        if name in self.algorithms:
            # 简化的量子算法执行
            return f"Quantum result for {name}: {input_data}"
        return None

class QuantumMLEngine:
    """量子机器学习引擎"""
    
    def __init__(self):
        self.models = {}
        self.training_data = {}
    
    def train_quantum_model(self, model_name: str, data: Any) -> Dict[str, Any]:
        """训练量子机器学习模型"""
        self.models[model_name] = {
            'data': data,
            'trained_at': time.time(),
            'status': 'trained'
        }
        
        return {
            'model_name': model_name,
            'status': 'trained',
            'quantum_advantage': True
        }

class QuantumOptimizer:
    """量子优化器"""
    
    def __init__(self):
        self.optimization_problems = {}
        self.solutions = {}
    
    def optimize(self, problem_id: str, problem_data: Any) -> Dict[str, Any]:
        """量子优化"""
        solution = f"Quantum optimized solution for {problem_id}"
        self.solutions[problem_id] = solution
        
        return {
            'problem_id': problem_id,
            'solution': solution,
            'quantum_advantage': True
        }

class MicroserviceLoadBalancer:
    """微服务负载均衡器"""
    
    def __init__(self, strategy: str = 'round_robin'):
        self.strategy = strategy
        self.current_index = 0
        self.service_instances = {}
    
    def select_instance(self, service_name: str, instances: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """选择服务实例"""
        if not instances:
            return None
        
        if self.strategy == 'round_robin':
            instance = instances[self.current_index % len(instances)]
            self.current_index += 1
            return instance
        elif self.strategy == 'random':
            import random
            return random.choice(instances)
        else:
            return instances[0]
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'strategy': self.strategy,
            'current_index': self.current_index,
            'total_instances': len(self.service_instances)
        }

class ServiceDiscovery:
    """服务发现"""
    
    def __init__(self):
        self.registered_services = {}
        self.service_health = {}
    
    def register_service(self, service_name: str, endpoint: str, metadata: Optional[Dict[str, Any]] = None):
        """注册服务"""
        self.registered_services[service_name] = {
            'endpoint': endpoint,
            'metadata': metadata or {},
            'registered_at': time.time(),
            'status': 'healthy'
        }
        logger.info(f"服务注册成功: {service_name} -> {endpoint}")
    
    def discover_service(self, service_name: str) -> Optional[str]:
        """发现服务"""
        service_info = self.registered_services.get(service_name)
        if service_info and service_info['status'] == 'healthy':
            return service_info['endpoint']
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'registered_services': len(self.registered_services),
            'services': list(self.registered_services.keys())
        }

class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.health_checks = {}
        self.check_interval = 30
    
    def check_health(self, service_name: str) -> str:
        """检查服务健康状态"""
        try:
            # 简化的健康检查
            return 'healthy'
        except Exception as e:
            logger.error(f"健康检查失败 {service_name}: {e}")
            return 'unhealthy'
    
    def register_health_check(self, service_name: str, check_function: Callable):
        """注册健康检查函数"""
        self.health_checks[service_name] = check_function
        logger.info(f"健康检查函数注册成功: {service_name}")

class UnifiedCentersRegistry:
    """统一中心注册表 - 微服务架构增强版"""
    
    def __init__(self):
        self._centers = {}
        self._center_instances = {}  # 缓存中心实例
        self._center_metadata = {}   # 中心元数据
        self._initialized = False
        self._performance_metrics = {
            'center_access_count': {},
            'center_creation_time': {},
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # 微服务架构支持
        self._microservices = {
            'services': {},  # 微服务注册表
            'service_instances': {},  # 服务实例缓存
            'load_balancer': None,  # 负载均衡器
            'service_discovery': None,  # 服务发现
            'circuit_breaker': {},  # 熔断器
            'health_checker': None  # 健康检查器
        }
        
        # 云原生支持
        self._cloud_native = {
            'containerized': False,
            'kubernetes_ready': False,
            'service_mesh': False,
            'auto_scaling': False,
            'config_maps': {},
            'secrets': {}
        }
        
        # 边缘计算支持
        self._edge_computing = {
            'edge_nodes': {},  # 边缘节点注册表
            'edge_services': {},  # 边缘服务
            'latency_optimization': True,  # 延迟优化
            'distributed_processing': True,  # 分布式处理
            'edge_sync': True,  # 边缘同步
            'offline_capability': True  # 离线能力
        }
        
        # 量子计算支持
        self._quantum_computing = {
            'quantum_algorithms': {},  # 量子算法
            'quantum_ml': {},  # 量子机器学习
            'quantum_optimization': {},  # 量子优化
            'quantum_simulator': False,  # 量子模拟器
            'quantum_hardware': False  # 量子硬件
        }
        
        # 初始化微服务组件
        self._initialize_microservices()
        
        # 初始化边缘计算组件
        self._initialize_edge_computing()
        
        # 初始化量子计算组件
        self._initialize_quantum_computing()
    
    def register_center(self, name: str, center_class, metadata: Optional[Dict[str, Any]] = None):
        """注册中心 - 增强版"""
        self._centers[name] = center_class
        self._center_metadata[name] = metadata or {}
        self._performance_metrics['center_access_count'][name] = 0
        logger.info(f"Registered center: {name}")
    
    def get_center(self, name: str, use_cache: bool = True):
        """获取中心实例 - 增强版，支持缓存和性能监控"""
        start_time = time.time()
        
        # 更新访问计数
        self._performance_metrics['center_access_count'][name] = \
            self._performance_metrics['center_access_count'].get(name, 0) + 1
        
        # 检查缓存
        if use_cache and name in self._center_instances:
            self._performance_metrics['cache_hits'] += 1
            return self._center_instances[name]
        
        # 创建新实例
        if name not in self._centers:
            logger.warning(f"Center {name} not found")
            self._performance_metrics['cache_misses'] += 1
            return None
        
        try:
            center_class = self._centers[name]
            instance = center_class()
            self._center_instances[name] = instance
            
            # 记录创建时间
            creation_time = time.time() - start_time
            self._performance_metrics['center_creation_time'][name] = creation_time
            
            self._performance_metrics['cache_misses'] += 1
            logger.debug(f"Created center instance: {name} (took {creation_time:.3f}s)")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create center instance {name}: {e}")
            self._performance_metrics['cache_misses'] += 1
            return None
    
    def list_centers(self):
        """列出所有中心"""
        return list(self._centers.keys())
    
    def get_center_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """获取中心元数据"""
        return self._center_metadata.get(name)
    
    def clear_cache(self):
        """清除中心实例缓存"""
        self._center_instances.clear()
        logger.info("Center instances cache cleared")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        total_access = sum(self._performance_metrics['center_access_count'].values())
        cache_hit_rate = (self._performance_metrics['cache_hits'] / 
                         (self._performance_metrics['cache_hits'] + self._performance_metrics['cache_misses'])
                         if (self._performance_metrics['cache_hits'] + self._performance_metrics['cache_misses']) > 0 else 0)
        
        return {
            'total_centers': len(self._centers),
            'cached_instances': len(self._center_instances),
            'total_access_count': total_access,
            'cache_hit_rate': cache_hit_rate,
            'center_access_counts': self._performance_metrics['center_access_count'],
            'average_creation_times': {
                name: time for name, time in self._performance_metrics['center_creation_time'].items()
            }
        }
    
    def _initialize_microservices(self):
        """初始化微服务组件"""
        try:
            # 初始化负载均衡器
            self._microservices['load_balancer'] = MicroserviceLoadBalancer()
            
            # 初始化服务发现
            self._microservices['service_discovery'] = ServiceDiscovery()
            
            # 初始化健康检查器
            self._microservices['health_checker'] = HealthChecker()
            
            logger.info("微服务组件初始化完成")
            
        except Exception as e:
            logger.error(f"微服务组件初始化失败: {e}")
    
    def register_microservice(self, service_name: str, service_class, metadata: Optional[Dict[str, Any]] = None):
        """注册微服务"""
        try:
            self._microservices['services'][service_name] = {
                'class': service_class,
                'metadata': metadata or {},
                'instances': [],
                'health_status': 'unknown',
                'last_health_check': None
            }
            
            logger.info(f"微服务注册成功: {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"微服务注册失败 {service_name}: {e}")
            return False
    
    def discover_service(self, service_name: str) -> Optional[Any]:
        """服务发现"""
        try:
            if service_name not in self._microservices['services']:
                logger.warning(f"微服务未找到: {service_name}")
                return None
            
            service_info = self._microservices['services'][service_name]
            
            # 检查健康状态
            if not self._check_service_health(service_name):
                logger.warning(f"微服务健康检查失败: {service_name}")
                return None
            
            # 负载均衡选择实例
            instance = self._microservices['load_balancer'].select_instance(service_info['instances'])
            
            if not instance:
                # 创建新实例
                instance = self._create_service_instance(service_name)
                if instance:
                    service_info['instances'].append(instance)
            
            return instance
            
        except Exception as e:
            logger.error(f"服务发现失败 {service_name}: {e}")
            return None
    
    def _check_service_health(self, service_name: str) -> bool:
        """检查服务健康状态"""
        try:
            service_info = self._microservices['services'][service_name]
            
            # 使用健康检查器
            health_status = self._microservices['health_checker'].check_health(service_name)
            service_info['health_status'] = health_status
            service_info['last_health_check'] = time.time()
            
            return health_status == 'healthy'
            
        except Exception as e:
            logger.error(f"健康检查失败 {service_name}: {e}")
            return False
    
    def _create_service_instance(self, service_name: str) -> Optional[Any]:
        """创建服务实例"""
        try:
            service_info = self._microservices['services'][service_name]
            service_class = service_info['class']
            
            # 创建实例
            instance = service_class()
            
            # 添加到实例缓存
            self._microservices['service_instances'][f"{service_name}_{id(instance)}"] = instance
            
            logger.info(f"服务实例创建成功: {service_name}")
            return instance
            
        except Exception as e:
            logger.error(f"服务实例创建失败 {service_name}: {e}")
            return None
    
    def get_microservices_status(self) -> Dict[str, Any]:
        """获取微服务状态"""
        try:
            services_status = {}
            
            for service_name, service_info in self._microservices['services'].items():
                services_status[service_name] = {
                    'health_status': service_info['health_status'],
                    'instance_count': len(service_info['instances']),
                    'last_health_check': service_info['last_health_check'],
                    'metadata': service_info['metadata']
                }
            
            return {
                'total_services': len(self._microservices['services']),
                'total_instances': len(self._microservices['service_instances']),
                'services': services_status,
                'load_balancer': self._microservices['load_balancer'].get_status() if self._microservices['load_balancer'] else None,
                'service_discovery': self._microservices['service_discovery'].get_status() if self._microservices['service_discovery'] else None
            }
            
        except Exception as e:
            logger.error(f"微服务状态获取失败: {e}")
            return {'error': str(e)}
    
    def enable_cloud_native(self, containerized: bool = True, kubernetes_ready: bool = True):
        """启用云原生支持"""
        try:
            self._cloud_native['containerized'] = containerized
            self._cloud_native['kubernetes_ready'] = kubernetes_ready
            
            if kubernetes_ready:
                # 初始化Kubernetes相关配置
                self._initialize_kubernetes_support()
            
            logger.info("云原生支持已启用")
            return True
            
        except Exception as e:
            logger.error(f"云原生支持启用失败: {e}")
            return False
    
    def _initialize_kubernetes_support(self):
        """初始化Kubernetes支持"""
        try:
            # 这里可以添加Kubernetes相关的初始化逻辑
            # 例如：ConfigMap、Secret、Service等资源的创建
            logger.info("Kubernetes支持初始化完成")
            
        except Exception as e:
            logger.error(f"Kubernetes支持初始化失败: {e}")
    
    def get_cloud_native_status(self) -> Dict[str, Any]:
        """获取云原生状态"""
        return {
            'containerized': self._cloud_native['containerized'],
            'kubernetes_ready': self._cloud_native['kubernetes_ready'],
            'service_mesh': self._cloud_native['service_mesh'],
            'auto_scaling': self._cloud_native['auto_scaling'],
            'config_maps_count': len(self._cloud_native['config_maps']),
            'secrets_count': len(self._cloud_native['secrets'])
        }
    
    def _initialize_edge_computing(self):
        """初始化边缘计算组件"""
        try:
            # 边缘节点管理器
            self._edge_computing['edge_manager'] = EdgeNodeManager()
            
            # 分布式处理器
            self._edge_computing['distributed_processor'] = DistributedProcessor()
            
            # 延迟优化器
            self._edge_computing['latency_optimizer'] = LatencyOptimizer()
            
            # 边缘同步器
            self._edge_computing['edge_synchronizer'] = EdgeSynchronizer()
            
            logger.info("边缘计算组件初始化完成")
            
        except Exception as e:
            logger.error(f"边缘计算组件初始化失败: {e}")
    
    def _initialize_quantum_computing(self):
        """初始化量子计算组件"""
        try:
            # 量子算法管理器
            self._quantum_computing['quantum_manager'] = QuantumAlgorithmManager()
            
            # 量子机器学习引擎
            self._quantum_computing['quantum_ml_engine'] = QuantumMLEngine()
            
            # 量子优化器
            self._quantum_computing['quantum_optimizer'] = QuantumOptimizer()
            
            logger.info("量子计算组件初始化完成")
            
        except Exception as e:
            logger.error(f"量子计算组件初始化失败: {e}")
    
    def register_edge_node(self, node_id: str, node_info: Dict[str, Any]) -> Dict[str, Any]:
        """注册边缘节点"""
        try:
            self._edge_computing['edge_nodes'][node_id] = {
                'info': node_info,
                'status': 'active',
                'registered_at': time.time(),
                'last_heartbeat': time.time(),
                'capabilities': node_info.get('capabilities', []),
                'location': node_info.get('location', {}),
                'resources': node_info.get('resources', {})
            }
            
            logger.info(f"边缘节点注册成功: {node_id}")
            return {
                'node_id': node_id,
                'status': 'registered',
                'registered_at': time.time()
            }
            
        except Exception as e:
            logger.error(f"边缘节点注册失败: {e}")
            return {'error': str(e)}
    
    def discover_edge_nodes(self, criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """发现边缘节点"""
        try:
            nodes = []
            criteria = criteria or {}
            
            for node_id, node_info in self._edge_computing['edge_nodes'].items():
                # 检查节点状态
                if node_info['status'] != 'active':
                    continue
                
                # 检查匹配条件
                if self._matches_edge_criteria(node_info, criteria):
                    nodes.append({
                        'node_id': node_id,
                        'info': node_info['info'],
                        'capabilities': node_info['capabilities'],
                        'location': node_info['location'],
                        'resources': node_info['resources']
                    })
            
            return nodes
            
        except Exception as e:
            logger.error(f"边缘节点发现失败: {e}")
            return []
    
    def _matches_edge_criteria(self, node_info: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """检查节点是否匹配条件"""
        try:
            # 检查位置条件
            if 'location' in criteria:
                required_location = criteria['location']
                node_location = node_info.get('location', {})
                if not self._location_matches(node_location, required_location):
                    return False
            
            # 检查能力条件
            if 'capabilities' in criteria:
                required_capabilities = criteria['capabilities']
                node_capabilities = node_info.get('capabilities', [])
                if not all(cap in node_capabilities for cap in required_capabilities):
                    return False
            
            # 检查资源条件
            if 'resources' in criteria:
                required_resources = criteria['resources']
                node_resources = node_info.get('resources', {})
                for resource, min_value in required_resources.items():
                    if node_resources.get(resource, 0) < min_value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"边缘节点条件匹配失败: {e}")
            return False
    
    def _location_matches(self, node_location: Dict[str, Any], required_location: Dict[str, Any]) -> bool:
        """检查位置是否匹配"""
        try:
            # 简化的位置匹配逻辑
            if 'region' in required_location:
                return node_location.get('region') == required_location['region']
            if 'zone' in required_location:
                return node_location.get('zone') == required_location['zone']
            return True
            
        except Exception as e:
            logger.error(f"位置匹配失败: {e}")
            return False
    
    def optimize_latency(self, request_data: Any, target_latency: float = 100.0) -> Dict[str, Any]:
        """优化延迟"""
        try:
            # 选择最优边缘节点
            optimal_node = self._select_optimal_edge_node(request_data, target_latency)
            
            if optimal_node:
                return {
                    'status': 'optimized',
                    'selected_node': optimal_node['node_id'],
                    'estimated_latency': optimal_node['estimated_latency'],
                    'optimization_strategy': 'edge_processing'
                }
            else:
                return {
                    'status': 'fallback',
                    'strategy': 'central_processing',
                    'reason': 'no_suitable_edge_node'
                }
            
        except Exception as e:
            logger.error(f"延迟优化失败: {e}")
            return {'error': str(e)}
    
    def _select_optimal_edge_node(self, request_data: Any, target_latency: float) -> Optional[Dict[str, Any]]:
        """选择最优边缘节点"""
        try:
            best_node = None
            best_latency = float('inf')
            
            for node_id, node_info in self._edge_computing['edge_nodes'].items():
                if node_info['status'] != 'active':
                    continue
                
                # 计算预估延迟
                estimated_latency = self._calculate_estimated_latency(node_info, request_data)
                
                if estimated_latency < target_latency and estimated_latency < best_latency:
                    best_latency = estimated_latency
                    best_node = {
                        'node_id': node_id,
                        'estimated_latency': estimated_latency,
                        'node_info': node_info
                    }
            
            return best_node
            
        except Exception as e:
            logger.error(f"最优边缘节点选择失败: {e}")
            return None
    
    def _calculate_estimated_latency(self, node_info: Dict[str, Any], request_data: Any) -> float:
        """计算预估延迟"""
        try:
            # 简化的延迟计算
            base_latency = 10.0  # 基础延迟
            processing_latency = len(str(request_data)) * 0.01  # 处理延迟
            network_latency = 5.0  # 网络延迟
            
            return base_latency + processing_latency + network_latency
            
        except Exception as e:
            logger.error(f"延迟计算失败: {e}")
            return 100.0
    
    def get_edge_computing_status(self) -> Dict[str, Any]:
        """获取边缘计算状态"""
        try:
            active_nodes = sum(1 for node in self._edge_computing['edge_nodes'].values() 
                              if node['status'] == 'active')
            
            return {
                'total_nodes': len(self._edge_computing['edge_nodes']),
                'active_nodes': active_nodes,
                'latency_optimization': self._edge_computing['latency_optimization'],
                'distributed_processing': self._edge_computing['distributed_processing'],
                'edge_sync': self._edge_computing['edge_sync'],
                'offline_capability': self._edge_computing['offline_capability']
            }
            
        except Exception as e:
            logger.error(f"边缘计算状态获取失败: {e}")
            return {'error': str(e)}
    
    def register_quantum_algorithm(self, algorithm_name: str, algorithm_info: Dict[str, Any]) -> Dict[str, Any]:
        """注册量子算法"""
        try:
            self._quantum_computing['quantum_algorithms'][algorithm_name] = {
                'info': algorithm_info,
                'status': 'registered',
                'registered_at': time.time(),
                'qubits_required': algorithm_info.get('qubits_required', 0),
                'complexity': algorithm_info.get('complexity', 'unknown'),
                'applications': algorithm_info.get('applications', [])
            }
            
            logger.info(f"量子算法注册成功: {algorithm_name}")
            return {
                'algorithm_name': algorithm_name,
                'status': 'registered',
                'registered_at': time.time()
            }
            
        except Exception as e:
            logger.error(f"量子算法注册失败: {e}")
            return {'error': str(e)}
    
    def execute_quantum_algorithm(self, algorithm_name: str, input_data: Any) -> Dict[str, Any]:
        """执行量子算法"""
        try:
            if algorithm_name not in self._quantum_computing['quantum_algorithms']:
                return {'error': f'量子算法不存在: {algorithm_name}'}
            
            algorithm_info = self._quantum_computing['quantum_algorithms'][algorithm_name]
            
            # 简化的量子算法执行
            result = self._simulate_quantum_execution(algorithm_name, input_data, algorithm_info)
            
            return {
                'algorithm_name': algorithm_name,
                'result': result,
                'execution_time': time.time(),
                'qubits_used': algorithm_info['qubits_required'],
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"量子算法执行失败: {e}")
            return {'error': str(e)}
    
    def _simulate_quantum_execution(self, algorithm_name: str, input_data: Any, algorithm_info: Dict[str, Any]) -> Any:
        """模拟量子算法执行"""
        try:
            # 简化的量子算法模拟
            if 'grover' in algorithm_name.lower():
                # Grover搜索算法模拟
                return self._simulate_grover_search(input_data)
            elif 'shor' in algorithm_name.lower():
                # Shor因式分解算法模拟
                return self._simulate_shor_factorization(input_data)
            elif 'vqe' in algorithm_name.lower():
                # 变分量子本征求解器模拟
                return self._simulate_vqe(input_data)
            else:
                # 通用量子算法模拟
                return self._simulate_general_quantum(input_data)
            
        except Exception as e:
            logger.error(f"量子算法模拟失败: {e}")
            return None
    
    def _simulate_grover_search(self, input_data: Any) -> Dict[str, Any]:
        """模拟Grover搜索算法"""
        try:
            # 简化的Grover搜索模拟
            search_space = len(str(input_data)) if isinstance(input_data, (str, list)) else 10
            iterations = int(search_space ** 0.5)
            
            return {
                'algorithm': 'grover_search',
                'search_space_size': search_space,
                'iterations': iterations,
                'success_probability': 0.9,
                'result': f'Found in {iterations} iterations'
            }
            
        except Exception as e:
            logger.error(f"Grover搜索模拟失败: {e}")
            return {'error': str(e)}
    
    def _simulate_shor_factorization(self, input_data: Any) -> Dict[str, Any]:
        """模拟Shor因式分解算法"""
        try:
            # 简化的Shor因式分解模拟
            number = int(input_data) if isinstance(input_data, (int, str)) else 15
            
            # 简单的因式分解
            factors = []
            for i in range(2, int(number ** 0.5) + 1):
                if number % i == 0:
                    factors.extend([i, number // i])
                    break
            
            return {
                'algorithm': 'shor_factorization',
                'input_number': number,
                'factors': factors,
                'quantum_advantage': True
            }
            
        except Exception as e:
            logger.error(f"Shor因式分解模拟失败: {e}")
            return {'error': str(e)}
    
    def _simulate_vqe(self, input_data: Any) -> Dict[str, Any]:
        """模拟变分量子本征求解器"""
        try:
            # 简化的VQE模拟
            return {
                'algorithm': 'vqe',
                'ground_state_energy': -2.0,
                'optimization_steps': 100,
                'convergence': True,
                'quantum_circuit_depth': 10
            }
            
        except Exception as e:
            logger.error(f"VQE模拟失败: {e}")
            return {'error': str(e)}
    
    def _simulate_general_quantum(self, input_data: Any) -> Dict[str, Any]:
        """模拟通用量子算法"""
        try:
            return {
                'algorithm': 'general_quantum',
                'quantum_state': 'superposition',
                'entanglement': True,
                'measurement_result': 'quantum_result',
                'probability': 0.8
            }
            
        except Exception as e:
            logger.error(f"通用量子算法模拟失败: {e}")
            return {'error': str(e)}
    
    def get_quantum_computing_status(self) -> Dict[str, Any]:
        """获取量子计算状态"""
        try:
            return {
                'total_algorithms': len(self._quantum_computing['quantum_algorithms']),
                'quantum_simulator': self._quantum_computing['quantum_simulator'],
                'quantum_hardware': self._quantum_computing['quantum_hardware'],
                'quantum_ml_models': len(self._quantum_computing['quantum_ml']),
                'quantum_optimizations': len(self._quantum_computing['quantum_optimization'])
            }
            
        except Exception as e:
            logger.error(f"量子计算状态获取失败: {e}")
            return {'error': str(e)}

# 全局注册表
_registry = UnifiedCentersRegistry()

def get_unified_center(center_name: str):
    """获取统一中心实例"""
    return _registry.get_center(center_name)

def register_unified_center(name: str, center_class):
    """注册统一中心"""
    _registry.register_center(name, center_class)

# 统一配置中心 - 标准接口实现
class UnifiedConfigCenter:
    """统一配置中心 - 提供标准配置管理接口"""
    
    def __init__(self):
        # 🚀 修复：首先加载 .env 文件
        self._load_env_file()
        
        self.configs = {}
        self.config_sections = {}
        self.config_validators = {}
        self.config_change_listeners = {}
        self.cache_enabled = True
        self.cache_ttl = 300  # 5分钟
        self.cache_timestamps = {}
        
        # 默认配置
        self.default_configs = {
            "agent": {
                "timeout": 30.0,
                "retry_count": 3,
                "confidence_threshold": 0.7,
                "max_retries": 3,
                "enabled": True,
                "priority": 5
            },
            "system": {
                "medium_threshold": 0.7,
                "low_threshold": 0.3,
                "high_threshold": 0.8,
                "default_limit": 10,
                "large_limit": 1000,
                "medium_buffer": 4096
            },
            "ai": {
                "DEFAULT_ZERO_VALUE": 0.0,
                "DEFAULT_ONE_VALUE": 1.0,
                "DEFAULT_CONFIDENCE": 0.5,
                "MAX_CONFIDENCE": 1.0,
                "MIN_CONFIDENCE": 0.0
            }
        }
        
        # 统一环境变量配置管理
        self._load_environment_configs()
        
        # 🚀 修复：加载 YAML/JSON 配置文件
        self._load_yaml_configs()
        
        logger.info("统一配置中心初始化完成")

    def _load_yaml_configs(self):
        """加载 YAML/JSON 配置文件"""
        try:
            import yaml
            import json
            from pathlib import Path
            
            # 定位 config 目录
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            config_dir = project_root / 'config'
            
            if not config_dir.exists():
                logger.warning(f"Config directory not found: {config_dir}")
                return

            # 加载 rules.yaml
            rules_path = config_dir / 'rules.yaml'
            if rules_path.exists():
                with open(rules_path, 'r', encoding='utf-8') as f:
                    rules_config = yaml.safe_load(f)
                    if rules_config:
                        # 将 rules.yaml 中的顶级键（如 rules, patterns, thresholds, timeouts）合并到 self.config_sections
                        for key, value in rules_config.items():
                            self.config_sections[key] = value
                            # 同时也为了 get_config_value 能直接获取顶级对象
                            self.configs[key] = value
                        logger.info(f"✅ 已加载 rules.yaml: {list(rules_config.keys())}")
            
            # 加载 system_config.json
            system_config_path = config_dir / 'system_config.json'
            if system_config_path.exists():
                with open(system_config_path, 'r', encoding='utf-8') as f:
                    system_config = json.load(f)
                    if system_config:
                         for key, value in system_config.items():
                            # 如果键已存在，进行合并而不是覆盖
                            if key in self.config_sections and isinstance(self.config_sections[key], dict) and isinstance(value, dict):
                                self.config_sections[key].update(value)
                            else:
                                self.config_sections[key] = value
                            
                            self.configs[key] = self.config_sections[key]
                         logger.info(f"✅ 已加载 system_config.json: {list(system_config.keys())}")

        except ImportError:
            logger.warning("yaml 模块未安装，无法加载 YAML 配置文件")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")

    
    def _load_env_file(self):
        """加载 .env 文件"""
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # 查找项目根目录的 .env 文件
            # 从当前文件位置向上查找
            current_file = Path(__file__)
            # src/utils/unified_centers.py -> src/utils -> src -> 项目根目录
            project_root = current_file.parent.parent.parent
            env_path = project_root / '.env'
            
            if env_path.exists():
                load_dotenv(env_path, override=False)  # override=False 表示不覆盖已存在的环境变量
                logger.debug(f"✅ 已从 .env 文件加载环境变量: {env_path}")
            else:
                # 如果没有找到，尝试当前工作目录
                env_path = Path.cwd() / '.env'
                if env_path.exists():
                    load_dotenv(env_path, override=False)
                    logger.debug(f"✅ 已从当前目录 .env 文件加载环境变量: {env_path}")
        except ImportError:
            # python-dotenv 未安装，跳过
            logger.debug("python-dotenv 未安装，跳过 .env 文件加载")
        except Exception as e:
            logger.warning(f"加载 .env 文件失败: {e}")
    
    def _load_environment_configs(self):
        """加载环境变量配置 - 统一管理所有环境变量"""
        import os
        
        # 系统级环境变量配置
        self.environment_configs = {
            "system": {
                # 样本和评估配置
                "MAX_EVALUATION_ITEMS": int(os.getenv('MAX_EVALUATION_ITEMS', '50')),
                "MAX_CONCURRENT_QUERIES": int(os.getenv('MAX_CONCURRENT_QUERIES', '3')),
                "REQUEST_TIMEOUT": int(os.getenv('REQUEST_TIMEOUT', '30')),
                "MAX_CACHE_SIZE": int(os.getenv('MAX_CACHE_SIZE', '100')),
                
                # 系统配置
                "SESSION_TIMEOUT": int(os.getenv('SESSION_TIMEOUT', '3600')),
                "MAX_THREADS": int(os.getenv('MAX_THREADS', '4')),
                "MAX_CONNECTIONS": int(os.getenv('MAX_CONNECTIONS', '100')),
                "MAX_QUEUE_SIZE": int(os.getenv('MAX_QUEUE_SIZE', '1000')),
                "MAX_QUERY_LENGTH": int(os.getenv('MAX_QUERY_LENGTH', '100')),
                "DEFAULT_PORT": int(os.getenv('DEFAULT_PORT', '8000')),
                "DEFAULT_LOG_LEVEL": os.getenv('DEFAULT_LOG_LEVEL', 'INFO'),
                "CHUNK_SIZE": int(os.getenv('CHUNK_SIZE', '1024')),
                "CONNECTION_TIMEOUT": int(os.getenv('CONNECTION_TIMEOUT', '10')),
                "METRICS_INTERVAL": int(os.getenv('METRICS_INTERVAL', '60')),
                "CACHE_TTL_SECONDS": int(os.getenv('CACHE_TTL_SECONDS', '3600'))
            },
            "ai_ml": {
                # AI/ML配置
                "BATCH_SIZE": int(os.getenv('BATCH_SIZE', '32')),
                "LEARNING_RATE": float(os.getenv('LEARNING_RATE', '0.001')),
                "EPOCHS": int(os.getenv('EPOCHS', '100')),
                "MODEL_MAX_LENGTH": int(os.getenv('MODEL_MAX_LENGTH', '256')),
                "MODEL_EMBEDDING_DIM": int(os.getenv('MODEL_EMBEDDING_DIM', '384')),
                "VECTOR_DIMENSION": int(os.getenv('VECTOR_DIMENSION', '384')),
                "NPROBE": int(os.getenv('NPROBE', '10')),
                "SIMILARITY_THRESHOLD": float(os.getenv('SIMILARITY_THRESHOLD', '0.6')),
                "ALERT_THRESHOLD": float(os.getenv('ALERT_THRESHOLD', '0.95'))
            },
            "paths": {
                # 路径配置
                "FAISS_INDEX_PATH": os.getenv('FAISS_INDEX_PATH', 'data/faiss_memory/faiss_index.bin'),
                "DATA_DIRECTORY": os.getenv('DATA_DIRECTORY', 'data'),
                "LOG_DIRECTORY": os.getenv('LOG_DIRECTORY', 'logs'),
                "CONFIG_DIRECTORY": os.getenv('CONFIG_DIRECTORY', 'config'),
                "CACHE_DIRECTORY": os.getenv('CACHE_DIRECTORY', 'cache'),
                "FRAMES_DATASET_PATH": os.getenv('FRAMES_DATASET_PATH', 'frames_dataset.json')
            },
            "urls": {
                # URL配置
                "API_BASE_URL": os.getenv('API_BASE_URL', 'http://localhost:8000'),
                "LLM_API_URL": os.getenv('LLM_API_URL', 'https://api.openai.com/v1'),
                "LLM_API_KEY": os.getenv('LLM_API_KEY', ''),
                "VECTOR_DB_URL": os.getenv('VECTOR_DB_URL', 'http://localhost:8080'),
                "MONITORING_URL": os.getenv('MONITORING_URL', 'http://localhost:9090'),
                "FRAMES_DATASET_URL": os.getenv('FRAMES_DATASET_URL', 'https://huggingface.co/datasets/google/frames-benchmark')
            },
            "llm": {
                # LLM配置（DeepSeek等）- 使用智能配置加载器解决沙箱环境问题
                "LLM_PROVIDER": self._load_config_value('LLM_PROVIDER', 'deepseek'),
                "DEEPSEEK_API_KEY": self._load_config_value('DEEPSEEK_API_KEY', ''),
                "DEEPSEEK_BASE_URL": self._load_config_value('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1'),
                "DEEPSEEK_MODEL": self._load_config_value('DEEPSEEK_MODEL', 'deepseek-reasoner'),
                "FAST_MODEL": self._load_config_value('FAST_MODEL', 'deepseek-chat')
            }
        }
        
        logger.info("环境变量配置加载完成")

    def _load_config_value(self, key: str, default: Any = None) -> Any:
        """
        智能配置加载器，解决沙箱环境.env文件访问限制

        优先级：
        1. 环境变量 (最高优先级)
        2. .env文件 (标准方式)
        3. 默认值 (兜底方案)
        """
        # 1. 优先检查环境变量
        env_value = os.getenv(key)
        if env_value is not None:
            logger.debug(f"✅ 从环境变量获取 {key}")
            return env_value

        # 2. 尝试从.env文件读取
        file_value = self._load_from_env_file(key)
        if file_value is not None:
            logger.debug(f"✅ 从.env文件获取 {key}")
            return file_value

        # 3. 使用默认值
        logger.debug(f"⚠️ 使用默认值获取 {key}: {default}")
        return default

    def _load_from_env_file(self, key: str) -> Optional[str]:
        """从.env文件加载配置，带错误处理"""
        try:
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent
            env_path = project_root / '.env'

            if not env_path.exists():
                return None

            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f'{key}='):
                        value = line.split('=', 1)[1].strip()
                        # 处理引号包围的值
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        return value

        except Exception as e:
            logger.debug(f"无法从.env文件读取 {key}: {e}")
            return None

        return None

    def get_env_config(self, section: str, key: str, default: Any = None) -> Any:
        """获取环境变量配置值"""
        try:
            if section in self.environment_configs and key in self.environment_configs[section]:
                return self.environment_configs[section][key]
            return default
        except Exception as e:
            logger.warning(f"获取环境变量配置失败 [{section}][{key}]: {e}")
            return default

    def get_agent_config(self, agent_name: str, default_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """获取Agent配置"""
        if default_config is None:
            default_config = {}
        
        try:
            # 1. 尝试从configs中获取
            agent_config = self.configs.get(agent_name, {})
            
            # 2. 如果configs中没有，尝试从default_configs.agent中获取通用配置
            if not agent_config and 'agent' in self.default_configs:
                agent_config = self.default_configs['agent']
            
            # 3. 合并配置 (default_config作为基础，agent_config覆盖)
            merged_config = default_config.copy()
            if agent_config:
                merged_config.update(agent_config)
            
            return merged_config
        except Exception as e:
            logger.warning(f"获取Agent配置失败 [{agent_name}]: {e}")
            return default_config
    
    def get_learning_rate_with_persistence(self, default_value: float = 0.001) -> float:
        """获取学习率（优先使用持久化的动态调整值）"""
        try:
            from src.config.learning_state_manager import get_current_learning_rate
            return get_current_learning_rate(default_value)
        except Exception as e:
            logger.warning(f"获取持久化学习率失败，使用默认值: {e}")
            return self.get_env_config('ai_ml', 'LEARNING_RATE', default_value)
    
    def update_learning_rate(self, new_rate: float, reason: str = "dynamic_adjustment", 
                           performance_metrics: Optional[Dict[str, Any]] = None):
        """更新学习率并持久化"""
        try:
            from src.config.learning_state_manager import update_learning_rate
            update_learning_rate(new_rate, reason, performance_metrics)
        except Exception as e:
            logger.error(f"更新学习率失败: {e}")
    
    def get_all_env_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有环境变量配置"""
        return self.environment_configs.copy()
    
    def get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """获取配置值 - 增强版，支持智能缓存和性能优化"""
        try:
            cache_key = f"{section}.{key}"
            current_time = time.time()
            
            # 检查缓存 - 增强版
            if self.cache_enabled:
                if cache_key in self.cache_timestamps:
                    cache_age = current_time - self.cache_timestamps[cache_key]
                    if cache_age < self.cache_ttl:
                        # 缓存命中，更新访问时间
                        self.cache_timestamps[cache_key] = current_time
                        return self.configs.get(cache_key, default)
                    else:
                        # 缓存过期，清除
                        self._remove_expired_cache(cache_key)
            
            # 从配置中获取 - 优化查找顺序（环境变量优先）
            value = None
            
            # 1. 优先从环境变量配置中查找
            if section in self.environment_configs and key in self.environment_configs[section]:
                value = self.environment_configs[section][key]
            # 2. 从用户配置中查找
            elif section in self.config_sections and key in self.config_sections[section]:
                value = self.config_sections[section][key]
            # 3. 从默认配置中查找
            elif section in self.default_configs and key in self.default_configs[section]:
                value = self.default_configs[section][key]
            # 4. 使用提供的默认值
            else:
                value = default
            
            # 更新缓存 - 智能缓存策略
            if self.cache_enabled and value is not None:
                self.configs[cache_key] = value
                self.cache_timestamps[cache_key] = current_time
                
                # 清理过期缓存（每100次访问清理一次）
                if len(self.configs) % 100 == 0:
                    self._cleanup_expired_cache()
            
            return value
            
        except Exception as e:
            logger.warning(f"获取配置值失败 {section}.{key}: {e}")
            return default
    
    def get_timeout(self, timeout_type: str, complexity: Optional[str] = None, default: Optional[float] = None) -> float:
        """获取超时配置 - 🚀 统一超时配置读取
        
        Args:
            timeout_type: 超时类型，如 'query_complexity', 'reasoning_steps', 'evidence_retrieval' 等
            complexity: 查询复杂度（simple/medium/complex），用于动态调整超时
            default: 默认超时值（秒）
            
        Returns:
            超时值（秒）
        """
        try:
            # 优先从配置中心直接获取 timeouts 部分
            timeouts_config = self.get_config_section('timeouts')
            if timeouts_config:
                if timeout_type == 'query_complexity' and complexity:
                    # 获取 query_complexity 字典
                    qc_config = timeouts_config.get('query_complexity', {})
                    if isinstance(qc_config, dict) and complexity in qc_config:
                        return float(qc_config[complexity])
                        
                elif timeout_type == 'reasoning_steps':
                    rs_config = timeouts_config.get('reasoning_steps', {})
                    if isinstance(rs_config, dict):
                        # 默认返回 default
                        val = rs_config.get('default')
                        if val is not None:
                            return float(val)

                elif timeout_type == 'evidence_retrieval':
                    er_config = timeouts_config.get('evidence_retrieval', {})
                    if isinstance(er_config, dict):
                         val = er_config.get('default')
                         if val is not None:
                             return float(val)

                elif timeout_type == 'initialization':
                    init_config = timeouts_config.get('initialization', {})
                    if isinstance(init_config, dict):
                         val = init_config.get('default')
                         if val is not None:
                             return float(val)

                elif timeout_type == 'task_wait':
                    tw_config = timeouts_config.get('task_wait', {})
                    if isinstance(tw_config, dict):
                         val = tw_config.get('default')
                         if val is not None:
                             return float(val)

                elif timeout_type == 'complex_reasoning':
                    cr_config = timeouts_config.get('complex_reasoning', {})
                    if isinstance(cr_config, dict):
                         val = cr_config.get('default')
                         if val is not None:
                             return float(val)

            # 旧逻辑保留作为 Fallback (以防万一)
            from src.utils.unified_rule_manager import get_unified_rule_manager
            rule_manager = get_unified_rule_manager()
            
            if rule_manager:
                # 从rules.yaml读取超时配置
                if timeout_type == 'query_complexity' and complexity:
                    timeout_key = f"timeouts.query_complexity.{complexity}"
                    timeout = rule_manager.get_threshold(timeout_key, context={})
                    if timeout is not None and timeout != 0.5: # 0.5 is default threshold fallback
                        return float(timeout)
            
            # Fallback: 使用默认值
            if default is not None:
                return float(default)
            
            # 最终fallback
            return 30.0
            
        except Exception as e:
            logger.warning(f"获取超时配置失败 {timeout_type}: {e}，使用默认值")
            return float(default) if default is not None else 30.0
            
        except Exception as e:
            logger.warning(f"获取配置值失败 {section}.{key}: {e}")
            return default
    

    
    def _remove_expired_cache(self, cache_key: str):
        """移除过期缓存"""
        if cache_key in self.configs:
            del self.configs[cache_key]
        if cache_key in self.cache_timestamps:
            del self.cache_timestamps[cache_key]
    
    def _cleanup_expired_cache(self):
        """清理所有过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for cache_key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp >= self.cache_ttl:
                expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            self._remove_expired_cache(cache_key)
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def set_config_value(self, section: str, key: str, value: Any) -> bool:
        """设置配置值 - 标准接口"""
        try:
            # 验证配置值
            if section in self.config_validators and key in self.config_validators[section]:
                if not self.config_validators[section][key](value):
                    logger.error(f"配置值验证失败 {section}.{key}: {value}")
                    return False
            
            # 设置配置
            if section not in self.config_sections:
                self.config_sections[section] = {}
            self.config_sections[section][key] = value
            
            # 清除缓存
            if self.cache_enabled:
                cache_key = f"{section}.{key}"
                if cache_key in self.configs:
                    del self.configs[cache_key]
                if cache_key in self.cache_timestamps:
                    del self.cache_timestamps[cache_key]
            
            # 通知监听器
            self._notify_config_change(section, key, value)
            
            logger.info(f"配置值设置成功 {section}.{key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"设置配置值失败 {section}.{key}: {e}")
            return False
    
    def get_config_section(self, section: str) -> Optional[Dict[str, Any]]:
        """获取配置节 - 标准接口"""
        try:
            result = {}
            
            # 合并默认配置和用户配置
            if section in self.default_configs:
                result.update(self.default_configs[section])
            if section in self.config_sections:
                result.update(self.config_sections[section])
            
            return result if result else None
            
        except Exception as e:
            logger.warning(f"获取配置节失败 {section}: {e}")
            return None
    
    def register_config_validator(self, section: str, key: str, validator: Callable) -> None:
        """注册配置验证器"""
        if section not in self.config_validators:
            self.config_validators[section] = {}
        self.config_validators[section][key] = validator
    
    def register_config_change_listener(self, section: str, listener: Callable) -> None:
        """注册配置变更监听器"""
        if section not in self.config_change_listeners:
            self.config_change_listeners[section] = []
        self.config_change_listeners[section].append(listener)
    
    def _notify_config_change(self, section: str, key: str, value: Any) -> None:
        """通知配置变更"""
        if section in self.config_change_listeners:
            for listener in self.config_change_listeners[section]:
                try:
                    listener(section, key, value)
                except Exception as e:
                    logger.warning(f"配置变更监听器执行失败: {e}")
    
    def clear_cache(self) -> None:
        """清除配置缓存"""
        self.configs.clear()
        self.cache_timestamps.clear()
        logger.info("配置缓存已清除")
    
    def get_status(self) -> Dict[str, Any]:
        """获取配置中心状态"""
        return {
            "status": "active",
            "cache_enabled": self.cache_enabled,
            "cached_configs": len(self.configs),
            "config_sections": len(self.config_sections),
            "validators": sum(len(v) for v in self.config_validators.values()),
            "listeners": sum(len(l) for l in self.config_change_listeners.values())
        }


# 智能配置中心 - 增强版，继承统一配置中心
class SmartConfigCenter(UnifiedConfigCenter):
    """智能配置中心 - 提供上下文感知的智能配置"""
    
    def __init__(self):
        super().__init__()  # 调用父类初始化
        self.context_history = []
        self.learning_enabled = True
        self.parameter_learner = get_parameter_learner()

    
    def get_smart_config(self, key: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """获取智能配置 - 支持上下文感知和学习"""
        if context is None:
            context = {}
        
        # 记录上下文历史用于学习
        if self.learning_enabled:
            self.context_history.append({
                "key": key,
                "context": context.copy(),
                "timestamp": time.time()
            })
        
        # 智能配置逻辑 - 优先使用父类的标准接口
        # 尝试从不同配置节中查找
        for section in ["agent", "system", "ai"]:
            value = self.get_config_value(section, key)
            if value is not None:
                # 基于上下文调整配置值
                return self._adjust_value_by_context(key, value, context)
        
        # 如果都没有，返回合理的默认值
        return self._get_intelligent_default(key, context)
    
    def _adjust_value_by_context(self, key: str, base_value: Any, context: Dict[str, Any]) -> Any:
        """基于上下文调整配置值"""
        if isinstance(base_value, (int, float)):
            # 数值类型的智能调整
            if "complexity" in context:
                complexity = context["complexity"]
                if isinstance(complexity, (int, float)):
                    # 根据复杂度调整阈值
                    if "threshold" in key.lower():
                        return max(0.0, min(1.0, base_value + (complexity - 0.5) * 0.2))
            
            if "query_length" in context:
                query_length = context["query_length"]
                if isinstance(query_length, int):
                    # 根据查询长度调整
                    if "limit" in key.lower():
                        return max(10, min(10000, base_value + query_length // 10))
        
        return base_value
    
    def _get_intelligent_default(self, key: str, context: Dict[str, Any]) -> Any:
        """获取智能默认值"""
        # 基于键名推断类型和默认值
        if "threshold" in key.lower():
            return 0.5
        elif "limit" in key.lower():
            return 100
        elif "timeout" in key.lower():
            return 30
        elif "confidence" in key.lower():
            return 0.7
        elif "retry" in key.lower():
            return 3
        else:
            return None
    
    def set_config(self, key: str, value: Any):
        """设置配置"""
        self.configs[key] = value
        logger.info(f"Set smart config {key} = {value}")
    
    def learn_from_context(self, key: str, context: Dict[str, Any], result: Any):
        """从上下文学习，优化配置 - 增强版"""
        if not self.learning_enabled:
            return
        
        # 记录学习数据
        learning_data = {
            "key": key,
            "context": context,
            "result": result,
            "timestamp": time.time()
        }
        
        # 添加到学习历史
        self.context_history.append(learning_data)
        
        # 保持历史记录在合理范围内
        if len(self.context_history) > 1000:
            self.context_history = self.context_history[-500:]  # 保留最近500条
        
        # 智能学习算法 - 基于模式识别
        self._analyze_patterns(key, context, result)
        
        logger.debug(f"Learning from context: {learning_data}")
        
        # Integrate with UnifiedParameterLearner
        try:
            if isinstance(result, (int, float)):
                self.parameter_learner.learn_parameter(
                    param_type=key,
                    query_type=context.get('query_type', 'default'),
                    value=float(result),
                    success=context.get('success', True),
                    metrics=context
                )
        except Exception as e:
            logger.debug(f"Failed to learn parameter: {e}")

    
    def _analyze_patterns(self, key: str, context: Dict[str, Any], result: Any):
        """分析上下文模式，优化配置建议"""
        try:
            # 分析相似上下文的结果模式
            similar_contexts = [
                h for h in self.context_history[-100:]  # 最近100条记录
                if h["key"] == key and self._contexts_similar(context, h["context"])
            ]
            
            if len(similar_contexts) >= 3:  # 至少3个相似上下文
                # 计算结果的平均值
                if isinstance(result, (int, float)):
                    avg_result = sum(h["result"] for h in similar_contexts if isinstance(h["result"], (int, float))) / len(similar_contexts)
                    
                    # 如果当前结果与平均值差异较大，可能需要调整配置
                    if abs(result - avg_result) > avg_result * 0.2:  # 差异超过20%
                        logger.info(f"Pattern detected for {key}: current={result}, average={avg_result:.2f}")
                        
                        # 可以在这里实现自动配置调整
                        # self._suggest_config_adjustment(key, context, result, avg_result)
        
        except Exception as e:
            logger.warning(f"Pattern analysis failed: {e}")
    
    def _contexts_similar(self, ctx1: Dict[str, Any], ctx2: Dict[str, Any], threshold: float = 0.7) -> bool:
        """判断两个上下文是否相似"""
        try:
            common_keys = set(ctx1.keys()) & set(ctx2.keys())
            if not common_keys:
                return False
            
            similar_count = 0
            for key in common_keys:
                if key in ['timestamp', 'user_id']:  # 忽略时间戳和用户ID
                    continue
                
                val1, val2 = ctx1[key], ctx2[key]
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    # 数值类型：计算相对差异
                    if val1 == 0 and val2 == 0:
                        similar_count += 1
                    else:
                        diff = abs(val1 - val2) / max(abs(val1), abs(val2), 1)
                        if diff < 0.3:  # 差异小于30%认为相似
                            similar_count += 1
                elif val1 == val2:  # 其他类型：完全匹配
                    similar_count += 1
            
            similarity = similar_count / len(common_keys) if common_keys else 0
            return similarity >= threshold
        
        except Exception:
            return False
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """获取学习洞察"""
        if not self.context_history:
            return {"message": "No learning data available"}
        
        recent_history = self.context_history[-100:]  # 最近100条
        
        # 分析最常用的配置键
        key_usage = {}
        for record in recent_history:
            key = record["key"]
            key_usage[key] = key_usage.get(key, 0) + 1
        
        most_used_keys = sorted(key_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 分析上下文模式
        context_patterns = {}
        for record in recent_history:
            context_keys = tuple(sorted(record["context"].keys()))
            context_patterns[context_keys] = context_patterns.get(context_keys, 0) + 1
        
        most_common_patterns = sorted(context_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "total_learning_records": len(self.context_history),
            "recent_records": len(recent_history),
            "most_used_config_keys": most_used_keys,
            "most_common_context_patterns": most_common_patterns,
            "learning_enabled": self.learning_enabled
        }

# 全局智能配置中心实例
smart_config_center = SmartConfigCenter()

# 全局函数，保持向后兼容
def get_smart_config(key: str, context: Optional[Dict[str, Any]] = None) -> Any:
    """全局智能配置函数"""
    return smart_config_center.get_smart_config(key, context)

def create_query_context(query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """创建查询上下文"""
    import time
    return {
        "query": query,
        "user_id": user_id,
        "timestamp": time.time()
    }

# 注册统一智能中心
from .unified_intelligent_center import UnifiedIntelligentCenter
intelligent_center = UnifiedIntelligentCenter()
register_unified_center('get_unified_intelligent_center', intelligent_center)

# 注册智能配置中心（替代原来的unified_config_center）
register_unified_center('get_unified_config_center', SmartConfigCenter)

# 注册增强性能监控器


from src.tools.monitoring.performance_monitor import PerformanceMonitor, get_performance_monitor
performance_monitor = get_performance_monitor()
register_unified_center('get_performance_monitor', performance_monitor)

# 注册增强上下文管理器
from .unified_context import UnifiedContextManager
context_manager = UnifiedContextManager()
register_unified_center('get_unified_context_manager', context_manager)

# 注册安全中心
from .unified_security_center import get_unified_security_center
security_center = get_unified_security_center()
register_unified_center('get_unified_security_center', security_center)

# 注册新恢复的核心模块
try:
    from .unified_dependency_manager import UnifiedDependencyManager
    dependency_manager = UnifiedDependencyManager()
    register_unified_center('get_unified_dependency_manager', dependency_manager)
    logger.info("Registered center: get_unified_dependency_manager")
except ImportError as e:
    logger.warning(f"Failed to import unified_dependency_manager: {e}")

try:
    from .unified_tokenization_manager import UnifiedTokenizationManager
    tokenization_manager = UnifiedTokenizationManager()
    register_unified_center('get_unified_tokenization_manager', tokenization_manager)
    logger.info("Registered center: get_unified_tokenization_manager")
except ImportError as e:
    logger.warning(f"Failed to import unified_tokenization_manager: {e}")

try:
    from .unified_threshold_manager import UnifiedThresholdManager
    threshold_manager = UnifiedThresholdManager()
    register_unified_center('get_unified_threshold_manager', threshold_manager)
    logger.info("Registered center: get_unified_threshold_manager")
except ImportError as e:
    logger.warning(f"Failed to import unified_threshold_manager: {e}")

try:
    from .unified_model_manager import ModelLifecycleManager
    model_manager = ModelLifecycleManager()
    register_unified_center('get_unified_model_manager', model_manager)
    logger.info("Registered center: get_unified_model_manager")
except ImportError as e:
    logger.warning(f"Failed to import unified_model_manager: {e}")

try:
    from .unified_intelligent_processor import UnifiedIntelligentProcessor
    intelligent_processor = UnifiedIntelligentProcessor()
    register_unified_center('get_unified_intelligent_processor', intelligent_processor)
    logger.info("Registered center: get_unified_intelligent_processor")
except ImportError as e:
    logger.warning(f"Failed to import unified_intelligent_processor: {e}")

try:
    from .unified_complexity_model_service import get_unified_complexity_model_service
    complexity_model_service = get_unified_complexity_model_service()
    register_unified_center('get_unified_complexity_model_service', complexity_model_service)
    logger.info("Registered center: get_unified_complexity_model_service")
except ImportError as e:
    logger.warning(f"Failed to import unified_complexity_model_service: {e}")

# 微服务架构增强方法
def _initialize_microservices(self):
    """初始化微服务组件"""
    try:
        # 初始化负载均衡器
        self._microservices['load_balancer'] = MicroserviceLoadBalancer()
        
        # 初始化服务发现
        self._microservices['service_discovery'] = ServiceDiscovery()
        
        # 初始化健康检查器
        self._microservices['health_checker'] = HealthChecker()
        
        logger.info("微服务组件初始化完成")
        
    except Exception as e:
        logger.error(f"微服务组件初始化失败: {e}")

def register_microservice(self, service_name: str, service_class, metadata: Optional[Dict[str, Any]] = None):
    """注册微服务"""
    try:
        self._microservices['services'][service_name] = {
            'class': service_class,
            'metadata': metadata or {},
            'instances': [],
            'health_status': 'unknown',
            'last_health_check': None
        }
        
        logger.info(f"微服务注册成功: {service_name}")
        return True
        
    except Exception as e:
        logger.error(f"微服务注册失败 {service_name}: {e}")
        return False

def discover_service(self, service_name: str) -> Optional[Any]:
    """服务发现"""
    try:
        if service_name not in self._microservices['services']:
            logger.warning(f"微服务未找到: {service_name}")
            return None
        
        service_info = self._microservices['services'][service_name]
        
        # 检查健康状态
        if not self._check_service_health(service_name):
            logger.warning(f"微服务健康检查失败: {service_name}")
            return None
        
        # 负载均衡选择实例
        instance = self._microservices['load_balancer'].select_instance(service_info['instances'])
        
        if not instance:
            # 创建新实例
            instance = self._create_service_instance(service_name)
            if instance:
                service_info['instances'].append(instance)
        
        return instance
        
    except Exception as e:
        logger.error(f"服务发现失败 {service_name}: {e}")
        return None

def _check_service_health(self, service_name: str) -> bool:
    """检查服务健康状态"""
    try:
        service_info = self._microservices['services'][service_name]
        
        # 使用健康检查器
        health_status = self._microservices['health_checker'].check_health(service_name)
        service_info['health_status'] = health_status
        service_info['last_health_check'] = time.time()
        
        return health_status == 'healthy'
        
    except Exception as e:
        logger.error(f"健康检查失败 {service_name}: {e}")
        return False

def _create_service_instance(self, service_name: str) -> Optional[Any]:
    """创建服务实例"""
    try:
        service_info = self._microservices['services'][service_name]
        service_class = service_info['class']
        
        # 创建实例
        instance = service_class()
        
        # 添加到实例缓存
        self._microservices['service_instances'][f"{service_name}_{id(instance)}"] = instance
        
        logger.info(f"服务实例创建成功: {service_name}")
        return instance
        
    except Exception as e:
        logger.error(f"服务实例创建失败 {service_name}: {e}")
        return None

def get_microservices_status(self) -> Dict[str, Any]:
    """获取微服务状态"""
    try:
        services_status = {}
        
        for service_name, service_info in self._microservices['services'].items():
            services_status[service_name] = {
                'health_status': service_info['health_status'],
                'instance_count': len(service_info['instances']),
                'last_health_check': service_info['last_health_check'],
                'metadata': service_info['metadata']
            }
        
        return {
            'total_services': len(self._microservices['services']),
            'total_instances': len(self._microservices['service_instances']),
            'services': services_status,
            'load_balancer': self._microservices['load_balancer'].get_status() if self._microservices['load_balancer'] else None,
            'service_discovery': self._microservices['service_discovery'].get_status() if self._microservices['service_discovery'] else None
        }
        
    except Exception as e:
        logger.error(f"微服务状态获取失败: {e}")
        return {'error': str(e)}

def enable_cloud_native(self, containerized: bool = True, kubernetes_ready: bool = True):
    """启用云原生支持"""
    try:
        self._cloud_native['containerized'] = containerized
        self._cloud_native['kubernetes_ready'] = kubernetes_ready
        
        if kubernetes_ready:
            # 初始化Kubernetes相关配置
            self._initialize_kubernetes_support()
        
        logger.info("云原生支持已启用")
        return True
        
    except Exception as e:
        logger.error(f"云原生支持启用失败: {e}")
        return False

def _initialize_kubernetes_support(self):
    """初始化Kubernetes支持"""
    try:
        # 这里可以添加Kubernetes相关的初始化逻辑
        # 例如：ConfigMap、Secret、Service等资源的创建
        logger.info("Kubernetes支持初始化完成")
        
    except Exception as e:
        logger.error(f"Kubernetes支持初始化失败: {e}")

def get_cloud_native_status(self) -> Dict[str, Any]:
    """获取云原生状态"""
    return {
        'containerized': self._cloud_native['containerized'],
        'kubernetes_ready': self._cloud_native['kubernetes_ready'],
        'service_mesh': self._cloud_native['service_mesh'],
        'auto_scaling': self._cloud_native['auto_scaling'],
        'config_maps_count': len(self._cloud_native['config_maps']),
        'secrets_count': len(self._cloud_native['secrets']),
        'services_count': len(self._cloud_native['services'])
    }


# 全局实例和便捷函数
_config_center = None

def get_unified_config_center() -> UnifiedConfigCenter:
    """获取统一配置中心实例"""
    global _config_center
    if _config_center is None:
        _config_center = UnifiedConfigCenter()
    return _config_center

# 便捷函数：获取环境变量配置
def get_env_config(section: str, key: str, default: Any = None) -> Any:
    """便捷函数：获取环境变量配置"""
    return get_unified_config_center().get_env_config(section, key, default)

def get_max_evaluation_items() -> int:
    """获取最大评估项目数"""
    return get_env_config("system", "MAX_EVALUATION_ITEMS", 1000)

def get_batch_size() -> int:
    """获取批次大小"""
    return get_env_config("ai_ml", "BATCH_SIZE", 32)

def get_learning_rate() -> float:
    """获取学习率（优先使用持久化的动态调整值）"""
    config_center = get_unified_config_center()
    return config_center.get_learning_rate_with_persistence(0.001)

def get_max_concurrent_queries() -> int:
    """获取最大并发查询数"""
    return get_env_config("system", "MAX_CONCURRENT_QUERIES", 3)

def get_request_timeout() -> int:
    """获取请求超时时间"""
    return get_env_config("system", "REQUEST_TIMEOUT", 30)

def get_max_cache_size() -> int:
    """获取最大缓存大小"""
    return get_env_config("system", "MAX_CACHE_SIZE", 100)

def get_unified_intelligent_center() -> UnifiedIntelligentCenter:
    """获取统一智能中心实例"""
    return intelligent_center
