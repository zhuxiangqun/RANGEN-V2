#!/usr/bin/env python3
"""
动态层扩展支持系统

V3优化：基于标准化接口系统实现动态层扩展支持，包括组件发现、注册、负载均衡、健康检查和自动恢复。
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from enum import Enum
import random
import hashlib

from .layer_interface_standard import (
    LayerType, StandardizedInterface, LayerCommunicationBus,
    get_layer_communication_bus, create_standardized_interface,
    LayerMessage, MessageType
)

logger = logging.getLogger(__name__)


class ComponentStatus(Enum):
    """组件状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    STARTING = "starting"


class LoadBalancingStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_LOADED = "least_loaded"
    LEAST_RESPONSE_TIME = "least_response_time"
    HASH_BASED = "hash_based"


class DynamicComponent:
    """动态组件描述"""
    
    def __init__(self, 
                 component_id: str,
                 component_type: str,
                 layer_type: LayerType,
                 endpoint: str,
                 capabilities: List[str],
                 metadata: Dict[str, Any] = None):
        self.component_id = component_id
        self.component_type = component_type
        self.layer_type = layer_type
        self.endpoint = endpoint
        self.capabilities = capabilities
        self.metadata = metadata or {}
        
        # 状态和性能指标
        self.status = ComponentStatus.STARTING
        self.registration_time = time.time()
        self.last_health_check = None
        self.health_check_failures = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0
        self.current_load = 0  # 当前负载（活跃请求数）
        
    def update_performance_metrics(self, 
                                  success: bool, 
                                  response_time: float):
        """更新性能指标"""
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        # 更新平均响应时间（指数移动平均）
        alpha = 0.1  # 平滑因子
        if self.average_response_time == 0:
            self.average_response_time = response_time
        else:
            self.average_response_time = (alpha * response_time + 
                                         (1 - alpha) * self.average_response_time)
    
    def update_status(self, status: ComponentStatus):
        """更新组件状态"""
        self.status = status
        self.last_health_check = time.time()
        
        if status == ComponentStatus.HEALTHY:
            self.health_check_failures = 0
        elif status in [ComponentStatus.DEGRADED, ComponentStatus.UNHEALTHY]:
            self.health_check_failures += 1
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_requests == 0:
            return 1.0  # 默认100%成功率
        return self.successful_requests / self.total_requests
    
    def is_available(self) -> bool:
        """检查组件是否可用"""
        return (self.status in [ComponentStatus.HEALTHY, ComponentStatus.DEGRADED] and
                self.health_check_failures < 5)  # 最多允许5次健康检查失败
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "component_id": self.component_id,
            "component_type": self.component_type,
            "layer_type": self.layer_type.value,
            "endpoint": self.endpoint,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "registration_time": self.registration_time,
            "last_health_check": self.last_health_check,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.get_success_rate(),
            "average_response_time": self.average_response_time,
            "current_load": self.current_load,
            "health_check_failures": self.health_check_failures,
            "metadata": self.metadata
        }


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.component_indices: Dict[str, int] = {}  # 组件ID -> 轮询索引
        self.last_selection_time: Dict[str, float] = {}  # 组件ID -> 最后选择时间
    
    def select_component(self, 
                        available_components: List[DynamicComponent],
                        request_hash: Optional[str] = None) -> Optional[DynamicComponent]:
        """根据策略选择组件"""
        if not available_components:
            return None
        
        # 过滤可用组件
        available = [comp for comp in available_components if comp.is_available()]
        if not available:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(available)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random_selection(available)
        elif self.strategy == LoadBalancingStrategy.LEAST_LOADED:
            return self._least_loaded_selection(available)
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_selection(available)
        elif self.strategy == LoadBalancingStrategy.HASH_BASED:
            return self._hash_based_selection(available, request_hash)
        else:
            return self._round_robin_selection(available)
    
    def _round_robin_selection(self, components: List[DynamicComponent]) -> DynamicComponent:
        """轮询选择"""
        # 生成组件列表的哈希键
        components_key = ",".join(sorted([c.component_id for c in components]))
        
        if components_key not in self.component_indices:
            self.component_indices[components_key] = 0
        
        idx = self.component_indices[components_key]
        selected = components[idx]
        
        # 更新索引
        self.component_indices[components_key] = (idx + 1) % len(components)
        
        # 记录选择时间
        self.last_selection_time[selected.component_id] = time.time()
        
        return selected
    
    def _random_selection(self, components: List[DynamicComponent]) -> DynamicComponent:
        """随机选择"""
        selected = random.choice(components)
        self.last_selection_time[selected.component_id] = time.time()
        return selected
    
    def _least_loaded_selection(self, components: List[DynamicComponent]) -> DynamicComponent:
        """选择负载最小的组件"""
        selected = min(components, key=lambda c: c.current_load)
        self.last_selection_time[selected.component_id] = time.time()
        return selected
    
    def _least_response_time_selection(self, components: List[DynamicComponent]) -> DynamicComponent:
        """选择响应时间最短的组件"""
        selected = min(components, key=lambda c: c.average_response_time)
        self.last_selection_time[selected.component_id] = time.time()
        return selected
    
    def _hash_based_selection(self, 
                            components: List[DynamicComponent],
                            request_hash: Optional[str]) -> DynamicComponent:
        """基于哈希的选择（确保相同请求路由到相同组件）"""
        if not request_hash:
            return self._random_selection(components)
        
        # 使用请求哈希选择组件
        hash_int = int(hashlib.md5(request_hash.encode()).hexdigest(), 16)
        idx = hash_int % len(components)
        selected = components[idx]
        
        self.last_selection_time[selected.component_id] = time.time()
        return selected


class DynamicLayerExtensionManager:
    """动态层扩展管理器"""
    
    def __init__(self):
        self.components: Dict[str, DynamicComponent] = {}  # component_id -> DynamicComponent
        self.components_by_layer: Dict[LayerType, List[DynamicComponent]] = {}
        self.components_by_capability: Dict[str, List[DynamicComponent]] = {}
        
        # 负载均衡器
        self.load_balancers: Dict[LayerType, LoadBalancer] = {}
        self.default_load_balancing_strategy = LoadBalancingStrategy.ROUND_ROBIN
        
        # 通信总线
        self.communication_bus = get_layer_communication_bus()
        
        # 健康检查配置
        self.health_check_interval = 30  # 秒
        self.health_check_timeout = 5    # 秒
        self.max_health_check_failures = 5
        
        # 自动恢复配置
        self.auto_recovery_enabled = True
        self.auto_recovery_attempts = 3
        self.auto_recovery_delay = 10  # 秒
        
        # 组件发现配置
        self.auto_discovery_enabled = True
        self.discovery_interval = 60  # 秒
        
        # 启动后台任务
        self._health_check_task: Optional[asyncio.Task] = None
        self._discovery_task: Optional[asyncio.Task] = None
        
        logger.info("动态层扩展管理器初始化完成")
    
    def start(self):
        """启动管理器"""
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        logger.info("动态层扩展管理器已启动")
    
    async def stop(self):
        """停止管理器"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
        
        logger.info("动态层扩展管理器已停止")
    
    def register_component(self, 
                          component_id: str,
                          component_type: str,
                          layer_type: LayerType,
                          endpoint: str,
                          capabilities: List[str],
                          metadata: Dict[str, Any] = None) -> bool:
        """注册新组件"""
        if component_id in self.components:
            logger.warning(f"组件 {component_id} 已注册，跳过重复注册")
            return False
        
        # 创建动态组件
        component = DynamicComponent(
            component_id=component_id,
            component_type=component_type,
            layer_type=layer_type,
            endpoint=endpoint,
            capabilities=capabilities,
            metadata=metadata
        )
        
        # 添加到注册表
        self.components[component_id] = component
        
        # 按层组织
        if layer_type not in self.components_by_layer:
            self.components_by_layer[layer_type] = []
        self.components_by_layer[layer_type].append(component)
        
        # 按能力组织
        for capability in capabilities:
            if capability not in self.components_by_capability:
                self.components_by_capability[capability] = []
            self.components_by_capability[capability].append(component)
        
        # 初始化该层的负载均衡器（如果还没有）
        if layer_type not in self.load_balancers:
            self.load_balancers[layer_type] = LoadBalancer(self.default_load_balancing_strategy)
        
        logger.info(f"注册动态组件: {component_id} ({layer_type.value})")
        logger.info(f"  端点: {endpoint}")
        logger.info(f"  能力: {capabilities}")
        
        return True
    
    def unregister_component(self, component_id: str) -> bool:
        """注销组件"""
        if component_id not in self.components:
            logger.warning(f"组件 {component_id} 未注册，无法注销")
            return False
        
        component = self.components[component_id]
        layer_type = component.layer_type
        
        # 从所有注册表中移除
        del self.components[component_id]
        
        if layer_type in self.components_by_layer:
            self.components_by_layer[layer_type] = [
                c for c in self.components_by_layer[layer_type]
                if c.component_id != component_id
            ]
        
        for capability in component.capabilities:
            if capability in self.components_by_capability:
                self.components_by_capability[capability] = [
                    c for c in self.components_by_capability[capability]
                    if c.component_id != component_id
                ]
        
        logger.info(f"注销动态组件: {component_id}")
        return True
    
    def get_component(self, component_id: str) -> Optional[DynamicComponent]:
        """获取组件"""
        return self.components.get(component_id)
    
    def find_components_by_layer(self, layer_type: LayerType) -> List[DynamicComponent]:
        """查找指定层的组件"""
        return self.components_by_layer.get(layer_type, [])
    
    def find_components_by_capability(self, capability: str) -> List[DynamicComponent]:
        """查找具有指定能力的组件"""
        return self.components_by_capability.get(capability, [])
    
    async def route_request(self,
                           layer_type: LayerType,
                           action: str,
                           data: Dict[str, Any],
                           request_hash: Optional[str] = None,
                           capability_filter: Optional[str] = None) -> Tuple[Optional[DynamicComponent], LayerMessage]:
        """路由请求到合适的组件"""
        # 查找可用组件
        if capability_filter:
            candidates = self.find_components_by_capability(capability_filter)
        else:
            candidates = self.find_components_by_layer(layer_type)
        
        # 过滤可用组件
        available_candidates = [c for c in candidates if c.is_available()]
        
        if not available_candidates:
            logger.error(f"没有可用的组件来处理请求: layer={layer_type.value}, action={action}")
            
            # 创建错误响应
            error_message = create_standardized_interface(LayerType.SYSTEM, "dynamic_extension_manager").create_message(
                target_layer=LayerType.SYSTEM,
                target_component="dynamic_extension_manager",
                action="error",
                data={
                    "error": f"No available components for layer {layer_type.value}",
                    "layer_type": layer_type.value,
                    "action": action
                },
                message_type=MessageType.ERROR
            )
            
            return None, error_message
        
        # 选择组件
        load_balancer = self.load_balancers.get(layer_type)
        if not load_balancer:
            load_balancer = LoadBalancer(self.default_load_balancing_strategy)
            self.load_balancers[layer_type] = load_balancer
        
        selected_component = load_balancer.select_component(available_candidates, request_hash)
        
        if not selected_component:
            logger.error(f"负载均衡器未能选择组件")
            return None, create_standardized_interface(LayerType.SYSTEM, "dynamic_extension_manager").create_message(
                target_layer=LayerType.SYSTEM,
                target_component="dynamic_extension_manager",
                action="error",
                data={"error": "Load balancer failed to select component"},
                message_type=MessageType.ERROR
            )
        
        # 更新组件负载
        selected_component.current_load += 1
        
        try:
            # 创建发送到组件的消息
            message = create_standardized_interface(LayerType.SYSTEM, "dynamic_extension_manager").create_message(
                target_layer=layer_type,
                target_component=selected_component.component_id,
                action=action,
                data=data,
                message_type=MessageType.REQUEST,
                correlation_id=request_hash
            )
            
            # 记录请求开始时间
            start_time = time.time()
            
            # 发送消息
            response = await self.communication_bus.send_message(message)
            
            # 计算响应时间
            response_time = time.time() - start_time
            
            # 更新组件性能指标
            success = response.payload.get("status") == "success"
            selected_component.update_performance_metrics(success, response_time)
            
            if success:
                selected_component.update_status(ComponentStatus.HEALTHY)
            else:
                selected_component.update_status(ComponentStatus.DEGRADED)
            
            return selected_component, response
            
        except Exception as e:
            logger.error(f"请求路由失败: {e}")
            selected_component.update_performance_metrics(False, 0)
            selected_component.update_status(ComponentStatus.DEGRADED)
            
            error_message = create_standardized_interface(LayerType.SYSTEM, "dynamic_extension_manager").create_message(
                target_layer=LayerType.SYSTEM,
                target_component="dynamic_extension_manager",
                action="error",
                data={"error": f"Request routing failed: {str(e)}"},
                message_type=MessageType.ERROR
            )
            
            return selected_component, error_message
            
        finally:
            # 减少组件负载
            selected_component.current_load = max(0, selected_component.current_load - 1)
    
    async def _health_check_loop(self):
        """健康检查循环"""
        logger.info("启动组件健康检查循环")
        
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # 检查所有组件
                for component_id, component in list(self.components.items()):
                    try:
                        await self._perform_health_check(component)
                    except Exception as e:
                        logger.error(f"组件 {component_id} 健康检查失败: {e}")
                        component.update_status(ComponentStatus.UNHEALTHY)
                        
                        # 尝试自动恢复
                        if self.auto_recovery_enabled:
                            await self._attempt_auto_recovery(component)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查循环异常: {e}")
                await asyncio.sleep(5)  # 短暂等待后重试
    
    async def _perform_health_check(self, component: DynamicComponent):
        """执行健康检查"""
        try:
            # 发送ping消息
            message = create_standardized_interface(LayerType.SYSTEM, "dynamic_extension_manager").create_message(
                target_layer=component.layer_type,
                target_component=component.component_id,
                action="ping",
                data={"health_check": True},
                message_type=MessageType.REQUEST
            )
            
            # 设置超时
            response = await asyncio.wait_for(
                self.communication_bus.send_message(message),
                timeout=self.health_check_timeout
            )
            
            # 检查响应
            if response.payload.get("status") == "success":
                pong_data = response.payload.get("data", {})
                if pong_data.get("pong"):
                    component.update_status(ComponentStatus.HEALTHY)
                    logger.debug(f"组件 {component.component_id} 健康检查通过")
                else:
                    component.update_status(ComponentStatus.DEGRADED)
                    logger.warning(f"组件 {component.component_id} 健康检查响应异常")
            else:
                component.update_status(ComponentStatus.UNHEALTHY)
                logger.warning(f"组件 {component.component_id} 健康检查失败: {response.payload.get('error')}")
                
        except asyncio.TimeoutError:
            component.update_status(ComponentStatus.UNHEALTHY)
            logger.warning(f"组件 {component.component_id} 健康检查超时")
        except Exception as e:
            component.update_status(ComponentStatus.UNHEALTHY)
            logger.warning(f"组件 {component.component_id} 健康检查异常: {e}")
    
    async def _attempt_auto_recovery(self, component: DynamicComponent):
        """尝试自动恢复"""
        logger.info(f"尝试自动恢复组件: {component.component_id}")
        
        for attempt in range(self.auto_recovery_attempts):
            try:
                logger.info(f"自动恢复尝试 {attempt + 1}/{self.auto_recovery_attempts}")
                
                # 等待重试延迟
                if attempt > 0:
                    await asyncio.sleep(self.auto_recovery_delay * attempt)
                
                # 尝试重新连接/恢复
                # 这里可以添加具体的恢复逻辑，比如重新初始化组件
                # 暂时只执行健康检查
                await self._perform_health_check(component)
                
                if component.status == ComponentStatus.HEALTHY:
                    logger.info(f"组件 {component.component_id} 自动恢复成功")
                    return True
                    
            except Exception as e:
                logger.error(f"自动恢复尝试 {attempt + 1} 失败: {e}")
        
        logger.warning(f"组件 {component.component_id} 自动恢复失败，已重试 {self.auto_recovery_attempts} 次")
        return False
    
    async def _discovery_loop(self):
        """组件发现循环"""
        if not self.auto_discovery_enabled:
            return
        
        logger.info("启动组件发现循环")
        
        while True:
            try:
                await asyncio.sleep(self.discovery_interval)
                
                # 这里可以实现自动发现逻辑
                # 例如：扫描网络、查询注册中心、监听事件等
                # 目前作为占位实现
                await self._discover_components()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"组件发现循环异常: {e}")
                await asyncio.sleep(5)  # 短暂等待后重试
    
    async def _discover_components(self):
        """发现新组件"""
        # 这是一个示例实现，实际项目中可以：
        # 1. 扫描网络服务
        # 2. 查询服务注册中心
        # 3. 监听服务注册事件
        # 4. 从配置文件加载
        
        # 目前仅记录日志
        logger.debug("执行组件发现扫描")
        
        # 示例：可以从环境变量或配置文件中发现组件
        # 这里留作扩展点
    
    def get_status_report(self) -> Dict[str, Any]:
        """获取状态报告"""
        total_components = len(self.components)
        healthy_components = len([c for c in self.components.values() if c.status == ComponentStatus.HEALTHY])
        degraded_components = len([c for c in self.components.values() if c.status == ComponentStatus.DEGRADED])
        unhealthy_components = len([c for c in self.components.values() if c.status in [ComponentStatus.UNHEALTHY, ComponentStatus.OFFLINE]])
        
        # 按层统计
        layer_stats = {}
        for layer_type in LayerType:
            components_in_layer = self.find_components_by_layer(layer_type)
            if components_in_layer:
                healthy_in_layer = len([c for c in components_in_layer if c.status == ComponentStatus.HEALTHY])
                layer_stats[layer_type.value] = {
                    "total": len(components_in_layer),
                    "healthy": healthy_in_layer,
                    "availability": healthy_in_layer / len(components_in_layer) if components_in_layer else 0
                }
        
        # 总体指标
        total_requests = sum(c.total_requests for c in self.components.values())
        successful_requests = sum(c.successful_requests for c in self.components.values())
        overall_success_rate = successful_requests / total_requests if total_requests > 0 else 1.0
        
        avg_response_time = sum(c.average_response_time for c in self.components.values()) / total_components if total_components > 0 else 0
        
        return {
            "total_components": total_components,
            "healthy_components": healthy_components,
            "degraded_components": degraded_components,
            "unhealthy_components": unhealthy_components,
            "overall_availability": healthy_components / total_components if total_components > 0 else 0,
            "overall_success_rate": overall_success_rate,
            "average_response_time": avg_response_time,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": total_requests - successful_requests,
            "layer_statistics": layer_stats,
            "components": {
                component_id: component.to_dict()
                for component_id, component in self.components.items()
            }
        }


# 全局管理器实例
_dynamic_layer_extension_manager_instance = None

def get_dynamic_layer_extension_manager() -> DynamicLayerExtensionManager:
    """获取动态层扩展管理器实例"""
    global _dynamic_layer_extension_manager_instance
    if _dynamic_layer_extension_manager_instance is None:
        _dynamic_layer_extension_manager_instance = DynamicLayerExtensionManager()
    return _dynamic_layer_extension_manager_instance


async def test_dynamic_layer_extension():
    """测试动态层扩展系统"""
    print("=" * 60)
    print("测试动态层扩展系统")
    print("=" * 60)
    
    try:
        manager = get_dynamic_layer_extension_manager()
        
        # 注册一些测试组件
        manager.register_component(
            component_id="test_interaction_001",
            component_type="web_interface",
            layer_type=LayerType.INTERACTION,
            endpoint="http://localhost:8001",
            capabilities=["user_input_processing", "response_delivery"]
        )
        
        manager.register_component(
            component_id="test_gateway_001",
            component_type="gateway",
            layer_type=LayerType.GATEWAY,
            endpoint="http://localhost:8002",
            capabilities=["message_routing", "safety_check", "agent_assembly"]
        )
        
        manager.register_component(
            component_id="test_agent_001",
            component_type="agent",
            layer_type=LayerType.AGENT,
            endpoint="http://localhost:8003",
            capabilities=["task_execution", "reasoning"]
        )
        
        manager.register_component(
            component_id="test_agent_002",
            component_type="agent",
            layer_type=LayerType.AGENT,
            endpoint="http://localhost:8004",
            capabilities=["task_execution", "knowledge_retrieval"]
        )
        
        # 启动管理器
        manager.start()
        
        # 等待组件初始化
        await asyncio.sleep(1)
        
        # 获取状态报告
        status = manager.get_status_report()
        print(f"✅ 动态层扩展管理器状态:")
        print(f"  总组件数: {status['total_components']}")
        print(f"  健康组件: {status['healthy_components']}")
        print(f"  降级组件: {status['degraded_components']}")
        print(f"  总体可用性: {status['overall_availability']:.2%}")
        
        # 按层统计
        print(f"\n  按层统计:")
        for layer, stats in status['layer_statistics'].items():
            print(f"    {layer}: {stats['total']} 个组件, {stats['healthy']} 个健康, 可用性: {stats['availability']:.2%}")
        
        # 测试路由
        print(f"\n✅ 测试路由功能...")
        
        # 路由到Agent层的请求
        component, response = await manager.route_request(
            layer_type=LayerType.AGENT,
            action="ping",
            data={"test": "routing"},
            request_hash="test_request_001"
        )
        
        if component:
            print(f"  选择的组件: {component.component_id}")
            print(f"  响应状态: {response.payload.get('status', 'unknown')}")
        else:
            print(f"  路由失败: {response.payload.get('error', 'unknown')}")
        
        # 测试按能力查找
        print(f"\n✅ 测试按能力查找...")
        agents_with_execution = manager.find_components_by_capability("task_execution")
        print(f"  具有'task_execution'能力的组件: {len(agents_with_execution)} 个")
        
        # 显示组件详情
        print(f"\n✅ 组件详情:")
        for comp_id, comp_data in list(status['components'].items())[:3]:  # 显示前3个
            print(f"  {comp_id}:")
            print(f"    类型: {comp_data['component_type']}")
            print(f"    层: {comp_data['layer_type']}")
            print(f"    状态: {comp_data['status']}")
            print(f"    能力: {', '.join(comp_data['capabilities'][:3])}...")
        
        # 停止管理器
        await manager.stop()
        
        print("=" * 60)
        print("✅ 动态层扩展系统测试完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 动态层扩展系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_dynamic_layer_extension())