#!/usr/bin/env python3
"""
增强版四层架构管理器 - 支持标准化接口系统的FourLayerManager

V3优化：在原有FourLayerManager基础上增加标准化接口支持，实现双模式运行（协议模式+标准化消息模式）。
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Union, Type

from .layer_interface_standard import (
    LayerMessage, LayerType, MessageType, MessagePriority,
    LayerCommunicationBus, get_layer_communication_bus,
    StandardizedInterface, create_standardized_interface
)
from .standardized_layer_adapter import (
    StandardizedInteractionAdapter, StandardizedGatewayAdapter,
    StandardizedAgentAdapter, StandardizedToolAdapter,
    create_standardized_four_layer_setup
)
from .four_layer_manager import (
    FourLayerManager, InteractionLayerProtocol, GatewayLayerProtocol,
    AgentLayerProtocol, ToolLayerProtocol, LayerComponent
)
from .dynamic_layer_extension import (
    get_dynamic_layer_extension_manager, DynamicLayerExtensionManager,
    ComponentStatus, LoadBalancingStrategy
)

logger = logging.getLogger(__name__)


class EnhancedFourLayerManager(FourLayerManager):
    """增强版四层架构管理器 - 支持标准化接口系统"""
    
    def __init__(self, use_standardized_interface: bool = True, enable_dynamic_extension: bool = True):
        """初始化增强版管理器
        
        Args:
            use_standardized_interface: 是否使用标准化接口系统
            enable_dynamic_extension: 是否启用动态层扩展
        """
        super().__init__()
        self.use_standardized_interface = use_standardized_interface
        self.enable_dynamic_extension = enable_dynamic_extension
        
        if use_standardized_interface:
            # 初始化标准化接口系统
            self.communication_bus = get_layer_communication_bus()
            self.standardized_adapters: Dict[str, StandardizedInterface] = {}
            self.standardized_setup: Optional[Dict[str, Any]] = None
            
            # 初始化动态层扩展管理器
            if enable_dynamic_extension:
                self.dynamic_extension_manager = get_dynamic_layer_extension_manager()
                logger.info("增强版四层架构管理器初始化完成（标准化接口模式 + 动态扩展）")
            else:
                self.dynamic_extension_manager = None
                logger.info("增强版四层架构管理器初始化完成（标准化接口模式）")
        else:
            self.dynamic_extension_manager = None
            logger.info("增强版四层架构管理器初始化完成（协议模式）")
    
    def enable_standardized_interface(self, enable: bool = True):
        """启用或禁用标准化接口系统"""
        if enable and not self.use_standardized_interface:
            # 从协议模式切换到标准化接口模式
            self.use_standardized_interface = True
            self.communication_bus = get_layer_communication_bus()
            self.standardized_adapters = {}
            logger.info("已启用标准化接口系统")
        elif not enable and self.use_standardized_interface:
            # 从标准化接口模式切换到协议模式
            self.use_standardized_interface = False
            logger.info("已禁用标准化接口系统，使用协议模式")
    
    def set_layer_implementation(self, layer_type: str, implementation: Any) -> bool:
        """设置层协议实现（增强版，同时注册标准化适配器）"""
        # 先调用父类方法设置协议实现
        success = super().set_layer_implementation(layer_type, implementation)
        
        if success and self.use_standardized_interface:
            # 如果使用标准化接口，创建相应的适配器
            self._create_standardized_adapter(layer_type, implementation)
        
        return success
    
    def _create_standardized_adapter(self, layer_type: str, implementation: Any):
        """创建标准化适配器"""
        component_id = f"enhanced_{layer_type}"
        
        try:
            if layer_type == "interaction" and isinstance(implementation, InteractionLayerProtocol):
                adapter = StandardizedInteractionAdapter(implementation, component_id)
                self.standardized_adapters["interaction"] = adapter
                self.communication_bus.register_component(adapter)
                logger.info(f"创建标准化交互层适配器: {component_id}")
                
            elif layer_type == "gateway" and isinstance(implementation, GatewayLayerProtocol):
                adapter = StandardizedGatewayAdapter(implementation, component_id)
                self.standardized_adapters["gateway"] = adapter
                self.communication_bus.register_component(adapter)
                logger.info(f"创建标准化网关层适配器: {component_id}")
                
            elif layer_type == "agent" and isinstance(implementation, AgentLayerProtocol):
                adapter = StandardizedAgentAdapter(implementation, component_id)
                self.standardized_adapters["agent"] = adapter
                self.communication_bus.register_component(adapter)
                logger.info(f"创建标准化Agent层适配器: {component_id}")
                
            elif layer_type == "tool" and isinstance(implementation, ToolLayerProtocol):
                adapter = StandardizedToolAdapter(implementation, component_id)
                self.standardized_adapters["tool"] = adapter
                self.communication_bus.register_component(adapter)
                logger.info(f"创建标准化工具层适配器: {component_id}")
                
        except Exception as e:
            logger.error(f"创建标准化适配器失败 ({layer_type}): {e}")
    
    def register_dynamic_component(self,
                                 component_id: str,
                                 component_type: str,
                                 layer_type: LayerType,
                                 endpoint: str,
                                 capabilities: List[str],
                                 metadata: Dict[str, Any] = None) -> bool:
        """注册动态组件到动态层扩展管理器"""
        if not self.enable_dynamic_extension or not self.dynamic_extension_manager:
            logger.warning("动态层扩展未启用，无法注册动态组件")
            return False
        
        success = self.dynamic_extension_manager.register_component(
            component_id=component_id,
            component_type=component_type,
            layer_type=layer_type,
            endpoint=endpoint,
            capabilities=capabilities,
            metadata=metadata
        )
        
        if success:
            logger.info(f"成功注册动态组件: {component_id} ({layer_type.value})")
        else:
            logger.warning(f"注册动态组件失败: {component_id}")
        
        return success
    
    def unregister_dynamic_component(self, component_id: str) -> bool:
        """注销动态组件"""
        if not self.enable_dynamic_extension or not self.dynamic_extension_manager:
            logger.warning("动态层扩展未启用，无法注销动态组件")
            return False
        
        success = self.dynamic_extension_manager.unregister_component(component_id)
        
        if success:
            logger.info(f"成功注销动态组件: {component_id}")
        else:
            logger.warning(f"注销动态组件失败: {component_id}")
        
        return success
    
    def start_dynamic_extension_manager(self):
        """启动动态层扩展管理器"""
        if not self.enable_dynamic_extension or not self.dynamic_extension_manager:
            logger.warning("动态层扩展未启用，无法启动管理器")
            return
        
        self.dynamic_extension_manager.start()
        logger.info("动态层扩展管理器已启动")
    
    async def stop_dynamic_extension_manager(self):
        """停止动态层扩展管理器"""
        if not self.enable_dynamic_extension or not self.dynamic_extension_manager:
            logger.warning("动态层扩展未启用，无法停止管理器")
            return
        
        await self.dynamic_extension_manager.stop()
        logger.info("动态层扩展管理器已停止")
    
    def get_dynamic_extension_status(self) -> Dict[str, Any]:
        """获取动态扩展状态报告"""
        if not self.enable_dynamic_extension or not self.dynamic_extension_manager:
            return {
                "enabled": False,
                "status": "disabled",
                "message": "动态层扩展未启用"
            }
        
        status = self.dynamic_extension_manager.get_status_report()
        return {
            "enabled": True,
            "status": "active",
            "report": status
        }
    
    async def process_request_with_standardized_interface(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """使用标准化接口系统处理用户请求"""
        if not self.use_standardized_interface:
            logger.warning("标准化接口系统未启用，回退到协议模式")
            return await self.process_request(user_input)
        
        logger.info(f"开始使用标准化接口处理用户请求: {user_input.get('request_id', 'unknown')}")
        
        request_id = user_input.get("request_id", f"req_{int(time.time())}")
        session_id = user_input.get("session_id", f"session_{int(time.time())}")
        
        try:
            # 1. 交互层：处理用户输入
            interaction_response = await self._send_standardized_message(
                source_layer=LayerType.SYSTEM,
                source_component="enhanced_manager",
                target_layer=LayerType.INTERACTION,
                target_component="enhanced_interaction",
                action="handle_user_input",
                data=user_input,
                correlation_id=request_id,
                session_id=session_id
            )
            
            if interaction_response.payload.get("status") == "error":
                logger.error(f"交互层处理失败: {interaction_response.payload.get('error')}")
                return {
                    "success": False,
                    "error": f"交互层处理失败: {interaction_response.payload.get('error')}",
                    "layer": "interaction"
                }
            
            processed_input = interaction_response.payload.get("data", {}).get("processed_input", {})
            user_input.update(processed_input)
            
            # 2. 网关层：安全检查
            safety_response = await self._send_standardized_message(
                source_layer=LayerType.INTERACTION,
                source_component="enhanced_interaction",
                target_layer=LayerType.GATEWAY,
                target_component="enhanced_gateway",
                action="perform_safety_check",
                data=user_input,
                correlation_id=request_id,
                session_id=session_id
            )
            
            if safety_response.payload.get("status") == "error":
                logger.error(f"安全检查失败: {safety_response.payload.get('error')}")
                return {
                    "success": False,
                    "error": f"安全检查失败: {safety_response.payload.get('error')}",
                    "layer": "gateway"
                }
            
            safety_result = safety_response.payload.get("data", {})
            if not safety_result.get("safe", True):
                return {
                    "success": False,
                    "error": "安全检查未通过",
                    "safety_reasons": safety_result.get("reasons", []),
                    "layer": "gateway"
                }
            
            # 3. 网关层：组装Agent团队
            assembly_response = await self._send_standardized_message(
                source_layer=LayerType.GATEWAY,
                source_component="enhanced_gateway",
                target_layer=LayerType.GATEWAY,
                target_component="enhanced_gateway",
                action="assemble_agents",
                data=user_input,
                correlation_id=request_id,
                session_id=session_id
            )
            
            if assembly_response.payload.get("status") == "error":
                logger.error(f"Agent组装失败: {assembly_response.payload.get('error')}")
                return {
                    "success": False,
                    "error": f"Agent组装失败: {assembly_response.payload.get('error')}",
                    "layer": "gateway"
                }
            
            agent_team = assembly_response.payload.get("data", {}).get("agent_team", [])
            user_input["agent_team"] = agent_team
            logger.debug(f"组装Agent团队: {agent_team}")
            
            # 4. Agent层：执行任务
            task_results = []
            for agent_id in agent_team:
                task_data = {
                    **user_input,
                    "agent_id": agent_id
                }
                
                task_response = await self._send_standardized_message(
                    source_layer=LayerType.GATEWAY,
                    source_component="enhanced_gateway",
                    target_layer=LayerType.AGENT,
                    target_component="enhanced_agent",
                    action="execute_task",
                    data=task_data,
                    correlation_id=request_id,
                    session_id=session_id
                )
                
                if task_response.payload.get("status") == "error":
                    logger.warning(f"Agent {agent_id} 任务执行失败: {task_response.payload.get('error')}")
                    task_results.append({
                        "agent_id": agent_id,
                        "success": False,
                        "error": task_response.payload.get("error")
                    })
                else:
                    task_result = task_response.payload.get("data", {})
                    task_results.append({
                        "agent_id": agent_id,
                        "success": True,
                        "result": task_result.get("task_result", {}),
                        "execution_status": task_result.get("execution_status", "completed")
                    })
            
            user_input["task_results"] = task_results
            
            # 5. 网关层：结果整合
            integration_response = await self._send_standardized_message(
                source_layer=LayerType.AGENT,
                source_component="enhanced_agent",
                target_layer=LayerType.GATEWAY,
                target_component="enhanced_gateway",
                action="route_message",
                data={
                    **user_input,
                    "direction": "response",
                    "source_layer": "agent"
                },
                correlation_id=request_id,
                session_id=session_id
            )
            
            if integration_response.payload.get("status") == "error":
                logger.warning(f"结果整合失败: {integration_response.payload.get('error')}")
                final_result = user_input
            else:
                final_result = integration_response.payload.get("data", {}).get("routing_info", user_input)
            
            # 6. 交互层：响应交付
            delivery_response = await self._send_standardized_message(
                source_layer=LayerType.GATEWAY,
                source_component="enhanced_gateway",
                target_layer=LayerType.INTERACTION,
                target_component="enhanced_interaction",
                action="deliver_response",
                data=final_result,
                correlation_id=request_id,
                session_id=session_id
            )
            
            if delivery_response.payload.get("status") == "error":
                logger.warning(f"响应交付失败: {delivery_response.payload.get('error')}")
                final_result["delivery_status"] = "failed"
                final_result["delivery_error"] = delivery_response.payload.get("error")
            else:
                delivery_result = delivery_response.payload.get("data", {})
                final_result["delivery_status"] = delivery_result.get("delivery_status", "success")
                final_result["delivery_message"] = delivery_result.get("delivery_message", "")
            
            # 7. 返回最终结果
            final_result["success"] = True
            final_result["request_id"] = request_id
            final_result["session_id"] = session_id
            final_result["processing_mode"] = "standardized_interface"
            final_result["processing_timestamp"] = time.time()
            
            logger.info(f"标准化接口请求处理完成: {request_id}")
            return final_result
            
        except Exception as e:
            logger.error(f"标准化接口处理请求失败: {e}")
            return {
                "success": False,
                "error": f"标准化接口处理失败: {str(e)}",
                "request_id": request_id,
                "processing_mode": "standardized_interface"
            }
    
    async def _send_dynamic_message(self,
                                  source_layer: LayerType,
                                  source_component: str,
                                  target_layer: LayerType,
                                  action: str,
                                  data: Dict[str, Any],
                                  correlation_id: Optional[str] = None,
                                  session_id: Optional[str] = None,
                                  capability_filter: Optional[str] = None) -> LayerMessage:
        """发送动态路由消息（使用动态层扩展管理器）"""
        if not self.enable_dynamic_extension or not self.dynamic_extension_manager:
            raise ValueError("动态层扩展未启用或动态层扩展管理器未初始化")
        
        # 使用动态层扩展管理器路由请求
        request_hash = correlation_id or str(hash((source_layer.value, action, str(data))))
        
        try:
            component, response = await self.dynamic_extension_manager.route_request(
                layer_type=target_layer,
                action=action,
                data=data,
                request_hash=request_hash,
                capability_filter=capability_filter
            )
            
            if not component:
                logger.warning(f"动态路由失败: {response.payload.get('error', 'unknown')}")
            
            return response
            
        except Exception as e:
            logger.error(f"动态路由异常: {e}")
            # 创建错误响应
            temp_interface = create_standardized_interface(source_layer, source_component)
            error_message = temp_interface.create_message(
                target_layer=LayerType.SYSTEM,
                target_component="dynamic_extension_manager",
                action="error",
                data={"error": f"动态路由失败: {str(e)}"},
                message_type=MessageType.ERROR,
                correlation_id=correlation_id
            )
            return error_message
    
    async def _send_standardized_message(self, 
                                       source_layer: LayerType,
                                       source_component: str,
                                       target_layer: LayerType,
                                       target_component: str,
                                       action: str,
                                       data: Dict[str, Any],
                                       correlation_id: Optional[str] = None,
                                       session_id: Optional[str] = None) -> LayerMessage:
        """发送标准化消息"""
        # 如果启用了动态扩展且target_component为"dynamic"，则使用动态路由
        if (self.enable_dynamic_extension and self.dynamic_extension_manager and 
            target_component == "dynamic"):
            return await self._send_dynamic_message(
                source_layer=source_layer,
                source_component=source_component,
                target_layer=target_layer,
                action=action,
                data=data,
                correlation_id=correlation_id,
                session_id=session_id
            )
        
        # 否则使用静态组件路由
        # 创建临时标准化接口用于发送消息
        temp_interface = create_standardized_interface(source_layer, source_component)
        
        # 创建消息
        message = temp_interface.create_message(
            target_layer=target_layer,
            target_component=target_component,
            action=action,
            data=data,
            message_type=MessageType.REQUEST,
            correlation_id=correlation_id,
            session_id=session_id
        )
        
        # 发送消息
        response = await self.communication_bus.send_message(message)
        return response
    
    async def process_request(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户请求（智能选择模式）"""
        if self.use_standardized_interface and self.standardized_adapters:
            # 如果启用了标准化接口且有适配器，使用标准化接口
            return await self.process_request_with_standardized_interface(user_input)
        else:
            # 否则使用父类的协议模式
            return await super().process_request(user_input)
    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """获取增强版状态信息"""
        base_status = self.get_layer_status()
        
        enhanced_status = {
            **base_status,
            "use_standardized_interface": self.use_standardized_interface,
            "standardized_interface_enabled": self.use_standardized_interface,
            "dynamic_extension_enabled": self.enable_dynamic_extension,
            "standardized_adapters_count": len(self.standardized_adapters) if hasattr(self, 'standardized_adapters') else 0,
            "standardized_adapters": list(self.standardized_adapters.keys()) if hasattr(self, 'standardized_adapters') else []
        }
        
        if self.use_standardized_interface and hasattr(self, 'communication_bus'):
            bus_status = self.communication_bus.get_component_status()
            enhanced_status["communication_bus"] = {
                "total_components": bus_status["total_components"],
                "component_layers": {
                    layer_type.value: len([c for c in bus_status["components"].values() if c["layer_type"] == layer_type.value])
                    for layer_type in LayerType
                }
            }
        
        # 添加动态扩展状态
        if self.enable_dynamic_extension and hasattr(self, 'dynamic_extension_manager') and self.dynamic_extension_manager:
            dynamic_status = self.get_dynamic_extension_status()
            enhanced_status["dynamic_extension"] = dynamic_status
        
        return enhanced_status
    
    async def send_broadcast_message(self, 
                                   action: str,
                                   data: Dict[str, Any],
                                   target_layer: Optional[LayerType] = None) -> List[Dict[str, Any]]:
        """发送广播消息"""
        if not self.use_standardized_interface or not hasattr(self, 'communication_bus'):
            logger.warning("标准化接口系统未启用，无法发送广播消息")
            return []
        
        # 使用第一个适配器作为源组件
        if not self.standardized_adapters:
            logger.warning("没有可用的标准化适配器，无法发送广播消息")
            return []
        
        source_adapter = list(self.standardized_adapters.values())[0]
        
        # 发送广播
        responses = await self.communication_bus.broadcast_message(
            source_component=source_adapter,
            target_layer=target_layer or LayerType.SYSTEM,
            action=action,
            data=data
        )
        
        # 转换响应格式
        formatted_responses = []
        for response in responses:
            formatted_responses.append({
                "status": response.payload.get("status", "unknown"),
                "data": response.payload.get("data", {}),
                "component_id": response.header.source_component,
                "layer_type": response.header.source_layer.value
            })
        
        return formatted_responses
    
    async def health_check_enhanced(self) -> Dict[str, Any]:
        """增强版健康检查"""
        base_health = await self.health_check()
        
        enhanced_health = {
            **base_health,
            "standardized_interface": {
                "enabled": self.use_standardized_interface,
                "status": "healthy" if self.use_standardized_interface else "disabled"
            }
        }
        
        if self.use_standardized_interface:
            # 检查标准化适配器
            adapter_health = {}
            for layer, adapter in self.standardized_adapters.items():
                # 发送ping消息测试适配器
                try:
                    message = adapter.create_message(
                        target_layer=adapter.layer_type,
                        target_component=adapter.component_id,
                        action="ping",
                        data={"test": "health_check"}
                    )
                    
                    response = await self.communication_bus.send_message(message)
                    adapter_health[layer] = {
                        "status": "healthy" if response.payload.get("status") == "success" else "unhealthy",
                        "response_time": time.time() - message.header.timestamp,
                        "component_id": adapter.component_id
                    }
                except Exception as e:
                    adapter_health[layer] = {
                        "status": "unhealthy",
                        "error": str(e),
                        "component_id": adapter.component_id
                    }
            
            enhanced_health["standardized_interface"]["adapters"] = adapter_health
            
            # 检查通信总线
            bus_status = self.communication_bus.get_component_status()
            enhanced_health["standardized_interface"]["communication_bus"] = {
                "total_components": bus_status["total_components"],
                "status": "healthy" if bus_status["total_components"] > 0 else "warning"
            }
        
        # 检查动态扩展
        if self.enable_dynamic_extension and hasattr(self, 'dynamic_extension_manager') and self.dynamic_extension_manager:
            try:
                dynamic_status = self.get_dynamic_extension_status()
                if dynamic_status["enabled"]:
                    report = dynamic_status.get("report", {})
                    total_components = report.get("total_components", 0)
                    healthy_components = report.get("healthy_components", 0)
                    
                    dynamic_health = {
                        "enabled": True,
                        "total_components": total_components,
                        "healthy_components": healthy_components,
                        "availability": healthy_components / total_components if total_components > 0 else 0,
                        "status": "healthy" if total_components > 0 and healthy_components > 0 else "warning"
                    }
                else:
                    dynamic_health = {
                        "enabled": False,
                        "status": "disabled"
                    }
            except Exception as e:
                dynamic_health = {
                    "enabled": True,
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            enhanced_health["dynamic_extension"] = dynamic_health
        
        return enhanced_health


# 全局增强版管理器实例
_enhanced_four_layer_manager_instance = None

def get_enhanced_four_layer_manager(use_standardized_interface: bool = True, enable_dynamic_extension: bool = True) -> EnhancedFourLayerManager:
    """获取增强版四层架构管理器实例"""
    global _enhanced_four_layer_manager_instance
    if _enhanced_four_layer_manager_instance is None:
        _enhanced_four_layer_manager_instance = EnhancedFourLayerManager(
            use_standardized_interface=use_standardized_interface,
            enable_dynamic_extension=enable_dynamic_extension
        )
    return _enhanced_four_layer_manager_instance


async def test_enhanced_four_layer_manager():
    """测试增强版四层架构管理器（包含动态扩展功能）"""
    from .four_layer_adapters import create_default_four_layer_setup
    
    print("=" * 60)
    print("测试增强版四层架构管理器（包含动态扩展）")
    print("=" * 60)
    
    # 创建默认的四层架构设置
    setup = create_default_four_layer_setup()
    manager = setup["manager"]
    
    # 创建增强版管理器，启用动态扩展
    enhanced_manager = EnhancedFourLayerManager(
        use_standardized_interface=True,
        enable_dynamic_extension=True
    )
    
    # 设置层实现（这会自动创建标准化适配器）
    enhanced_manager.set_layer_implementation("interaction", setup["interaction_adapter"])
    enhanced_manager.set_layer_implementation("gateway", setup["gateway_adapter"])
    enhanced_manager.set_layer_implementation("agent", setup["agent_adapter"])
    enhanced_manager.set_layer_implementation("tool", setup["tool_adapter"])
    
    # 启动动态扩展管理器
    enhanced_manager.start_dynamic_extension_manager()
    
    # 注册一些动态组件用于测试
    print("\n注册动态组件...")
    enhanced_manager.register_dynamic_component(
        component_id="dynamic_agent_001",
        component_type="dynamic_agent",
        layer_type=LayerType.AGENT,
        endpoint="http://localhost:8101",
        capabilities=["task_execution", "reasoning", "knowledge_retrieval"],
        metadata={"version": "1.0", "region": "east"}
    )
    
    enhanced_manager.register_dynamic_component(
        component_id="dynamic_agent_002",
        component_type="dynamic_agent",
        layer_type=LayerType.AGENT,
        endpoint="http://localhost:8102",
        capabilities=["task_execution", "data_analysis", "report_generation"],
        metadata={"version": "1.1", "region": "west"}
    )
    
    enhanced_manager.register_dynamic_component(
        component_id="dynamic_interaction_001",
        component_type="dynamic_web_interface",
        layer_type=LayerType.INTERACTION,
        endpoint="http://localhost:8103",
        capabilities=["user_input_processing", "response_delivery"],
        metadata={"version": "1.0", "ui_type": "web"}
    )
    
    # 等待动态管理器初始化
    await asyncio.sleep(1)
    
    # 获取状态
    status = enhanced_manager.get_enhanced_status()
    print(f"\n增强版管理器状态:")
    print(f"  - 标准化接口启用: {status['use_standardized_interface']}")
    print(f"  - 动态扩展启用: {status['dynamic_extension_enabled']}")
    print(f"  - 标准化适配器数量: {status['standardized_adapters_count']}")
    print(f"  - 适配器列表: {status['standardized_adapters']}")
    
    if status.get("communication_bus"):
        print(f"  - 通信总线组件: {status['communication_bus']['total_components']}")
    
    # 显示动态扩展状态
    if status.get("dynamic_extension"):
        dynamic = status["dynamic_extension"]
        print(f"\n动态扩展状态:")
        print(f"  - 启用: {dynamic['enabled']}")
        print(f"  - 状态: {dynamic['status']}")
        
        if dynamic["enabled"] and "report" in dynamic:
            report = dynamic["report"]
            print(f"  - 总组件数: {report.get('total_components', 0)}")
            print(f"  - 健康组件: {report.get('healthy_components', 0)}")
            print(f"  - 总体可用性: {report.get('overall_availability', 0):.2%}")
            
            if "layer_statistics" in report:
                print(f"\n  按层统计:")
                for layer, stats in report["layer_statistics"].items():
                    print(f"    {layer}: {stats['total']} 个组件, {stats['healthy']} 个健康, 可用性: {stats['availability']:.2%}")
    
    # 健康检查
    health = await enhanced_manager.health_check_enhanced()
    print(f"\n健康检查结果:")
    print(f"  - 整体状态: {health['overall']}")
    
    if health["standardized_interface"]["enabled"]:
        print(f"  - 标准化接口状态: {health['standardized_interface']['status']}")
        
        if "adapters" in health["standardized_interface"]:
            for layer, adapter_health in health["standardized_interface"]["adapters"].items():
                print(f"  - {layer}适配器: {adapter_health['status']}")
    
    # 显示动态扩展健康状态
    if "dynamic_extension" in health:
        dynamic_health = health["dynamic_extension"]
        print(f"  - 动态扩展: {dynamic_health['status']}")
        if dynamic_health.get("enabled"):
            print(f"    * 总组件数: {dynamic_health.get('total_components', 0)}")
            print(f"    * 健康组件: {dynamic_health.get('healthy_components', 0)}")
            print(f"    * 可用性: {dynamic_health.get('availability', 0):.2%}")
    
    # 测试动态路由功能
    print(f"\n测试动态路由功能...")
    try:
        # 使用动态路由发送请求到Agent层
        from .layer_interface_standard import LayerType
        
        dynamic_response = await enhanced_manager._send_dynamic_message(
            source_layer=LayerType.SYSTEM,
            source_component="test_runner",
            target_layer=LayerType.AGENT,
            action="ping",
            data={"test": "dynamic_routing"},
            correlation_id="test_dynamic_001",
            capability_filter="task_execution"
        )
        
        print(f"动态路由响应:")
        print(f"  - 状态: {dynamic_response.payload.get('status', 'unknown')}")
        print(f"  - 目标层: {dynamic_response.header.target_layer.value}")
        
        if dynamic_response.payload.get("status") == "success":
            print(f"  - 成功: ✓")
        else:
            print(f"  - 错误: {dynamic_response.payload.get('error', 'unknown')}")
            
    except Exception as e:
        print(f"动态路由测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试请求处理（标准化接口模式）
    test_request = {
        "request_id": "test_001",
        "content": "测试增强版四层架构管理器的动态扩展功能",
        "user_id": "test_user",
        "session_id": "test_session"
    }
    
    print(f"\n发送测试请求: {test_request['request_id']}")
    result = await enhanced_manager.process_request_with_standardized_interface(test_request)
    
    print(f"处理结果:")
    print(f"  - 成功: {result.get('success', False)}")
    print(f"  - 处理模式: {result.get('processing_mode', 'unknown')}")
    
    if result.get("success"):
        print(f"  - Agent团队大小: {len(result.get('task_results', []))}")
        print(f"  - 交付状态: {result.get('delivery_status', 'unknown')}")
    else:
        print(f"  - 错误: {result.get('error', 'unknown')}")
    
    # 停止动态扩展管理器
    await enhanced_manager.stop_dynamic_extension_manager()
    
    print("=" * 60)
    print("✅ 增强版四层架构管理器测试完成")
    print("=" * 60)
    
    return enhanced_manager


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enhanced_four_layer_manager())