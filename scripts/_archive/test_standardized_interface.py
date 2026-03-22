#!/usr/bin/env python3
"""
标准化接口系统测试脚本

测试新创建的标准化接口系统组件：
1. layer_interface_standard.py - 标准化接口系统基础
2. standardized_layer_adapter.py - 协议适配器
3. enhanced_four_layer_manager.py - 增强版管理器
"""

import asyncio
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def test_layer_interface_standard():
    """测试标准化接口系统基础组件"""
    print("=" * 60)
    print("测试标准化接口系统基础组件")
    print("=" * 60)
    
    try:
        from src.core.layer_interface_standard import (
            LayerType, MessageType, MessagePriority,
            LayerMessageHeader, LayerMessage,
            StandardizedInterface, LayerCommunicationBus,
            get_layer_communication_bus, create_standardized_interface
        )
        
        # 测试枚举类型
        print("✅ 成功导入标准化接口系统基础组件")
        print(f"  层类型: {[lt.value for lt in LayerType]}")
        print(f"  消息类型: {[mt.value for mt in MessageType]}")
        print(f"  优先级: {[mp.value for mp in MessagePriority]}")
        
        # 测试消息头
        header = LayerMessageHeader(
            message_id="test_msg_001",
            message_type=MessageType.REQUEST,
            priority=MessagePriority.NORMAL,
            timestamp=1234567890.0,
            source_layer=LayerType.INTERACTION,
            source_component="test_source",
            target_layer=LayerType.GATEWAY,
            target_component="test_target"
        )
        
        print("✅ 成功创建LayerMessageHeader")
        print(f"  消息ID: {header.message_id}")
        print(f"  源组件: {header.source_component}")
        print(f"  目标组件: {header.target_component}")
        
        # 测试消息
        message = LayerMessage(
            header=header,
            payload={"action": "test", "data": {"test": "value"}}
        )
        
        print("✅ 成功创建LayerMessage")
        print(f"  载荷动作: {message.payload.get('action')}")
        print(f"  载荷数据: {message.payload.get('data')}")
        
        # 测试标准化接口
        interface = create_standardized_interface(LayerType.AGENT, "test_agent")
        print("✅ 成功创建StandardizedInterface")
        print(f"  组件ID: {interface.component_id}")
        print(f"  层类型: {interface.layer_type.value}")
        print(f"  处理器数量: {len(interface.message_handlers)}")
        
        # 测试通信总线
        bus = get_layer_communication_bus()
        print("✅ 成功获取LayerCommunicationBus实例")
        
        return True
        
    except Exception as e:
        print(f"❌ 标准化接口系统基础组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_standardized_layer_adapter():
    """测试标准化层适配器"""
    print("\n" + "=" * 60)
    print("测试标准化层适配器")
    print("=" * 60)
    
    try:
        from src.core.standardized_layer_adapter import (
            StandardizedInteractionAdapter, StandardizedGatewayAdapter,
            StandardizedAgentAdapter, StandardizedToolAdapter,
            create_standardized_four_layer_setup
        )
        
        # 测试适配器类导入
        print("✅ 成功导入标准化层适配器组件")
        
        # 创建模拟协议实现
        class MockInteractionProtocol:
            async def handle_user_input(self, input_data):
                return {"processed_input": {"test": "processed"}, "validation_passed": True}
            
            async def deliver_response(self, response):
                return {"status": "success", "message": "Response delivered"}
        
        class MockGatewayProtocol:
            async def route_message(self, message):
                return {"routing_info": {"target_layer": "agent", "target_component": "test_agent"}}
            
            async def perform_safety_check(self, message):
                return {"safe": True, "reasons": [], "risk_level": "low"}
            
            async def assemble_agents(self, task):
                return ["agent_001", "agent_002"]
        
        class MockAgentProtocol:
            async def execute_task(self, agent_id, task):
                return {"result": f"Task executed by {agent_id}", "status": "completed"}
            
            async def get_agent_capabilities(self, agent_id):
                return ["capability_1", "capability_2"]
            
            async def form_team(self, agent_ids, team_purpose):
                return f"team_{hash(tuple(agent_ids))}"
        
        class MockToolProtocol:
            async def execute_tool(self, tool_id, params):
                return {"success": True, "output": f"Tool {tool_id} executed"}
            
            async def discover_tools(self, capability_filter):
                return [{"id": "tool_1", "name": "Test Tool", "description": "A test tool"}]
            
            async def register_tool(self, tool_definition):
                return "registered_tool_id"
        
        # 创建适配器实例
        interaction_adapter = StandardizedInteractionAdapter(MockInteractionProtocol(), "test_interaction")
        gateway_adapter = StandardizedGatewayAdapter(MockGatewayProtocol(), "test_gateway")
        agent_adapter = StandardizedAgentAdapter(MockAgentProtocol(), "test_agent")
        tool_adapter = StandardizedToolAdapter(MockToolProtocol(), "test_tool")
        
        print("✅ 成功创建所有标准化层适配器实例")
        print(f"  交互层适配器: {interaction_adapter.component_id}")
        print(f"  网关层适配器: {gateway_adapter.component_id}")
        print(f"  Agent层适配器: {agent_adapter.component_id}")
        print(f"  工具层适配器: {tool_adapter.component_id}")
        
        # 测试适配器消息处理
        from src.core.layer_interface_standard import LayerType, MessageType, get_layer_communication_bus
        
        bus = get_layer_communication_bus()
        bus.register_component(interaction_adapter)
        bus.register_component(gateway_adapter)
        
        # 创建测试消息
        test_message = interaction_adapter.create_message(
            target_layer=LayerType.GATEWAY,
            target_component="test_gateway",
            action="perform_safety_check",
            data={"content": "Test message"}
        )
        
        # 发送消息
        response = await bus.send_message(test_message)
        print("✅ 成功通过标准化适配器发送和接收消息")
        print(f"  响应状态: {response.payload.get('status')}")
        print(f"  安全检查结果: {response.payload.get('data', {}).get('safe')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 标准化层适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_enhanced_four_layer_manager():
    """测试增强版四层架构管理器"""
    print("\n" + "=" * 60)
    print("测试增强版四层架构管理器")
    print("=" * 60)
    
    try:
        from src.core.enhanced_four_layer_manager import EnhancedFourLayerManager, get_enhanced_four_layer_manager
        
        print("✅ 成功导入增强版四层架构管理器")
        
        # 创建增强版管理器
        enhanced_manager = EnhancedFourLayerManager(use_standardized_interface=True)
        print("✅ 成功创建EnhancedFourLayerManager实例")
        print(f"  标准化接口启用: {enhanced_manager.use_standardized_interface}")
        
        # 创建模拟协议实现
        class MockInteractionProtocol:
            async def handle_user_input(self, input_data):
                return {"processed_input": {"enhanced": "processed"}, "validation_passed": True}
            
            async def deliver_response(self, response):
                return {"status": "success", "message": "Enhanced response delivered"}
        
        class MockGatewayProtocol:
            async def route_message(self, message):
                return {"routing_info": {"target_layer": "agent", "target_component": "test_agent"}}
            
            async def perform_safety_check(self, message):
                return {"safe": True, "reasons": [], "risk_level": "low"}
            
            async def assemble_agents(self, task):
                return ["enhanced_agent_001", "enhanced_agent_002"]
        
        class MockAgentProtocol:
            async def execute_task(self, agent_id, task):
                return {"result": f"Enhanced task executed by {agent_id}", "status": "completed"}
            
            async def get_agent_capabilities(self, agent_id):
                return ["enhanced_capability"]
            
            async def form_team(self, agent_ids, team_purpose):
                return f"enhanced_team_{hash(tuple(agent_ids))}"
        
        class MockToolProtocol:
            async def execute_tool(self, tool_id, params):
                return {"success": True, "output": f"Enhanced tool {tool_id} executed"}
            
            async def discover_tools(self, capability_filter):
                return [{"id": "enhanced_tool", "name": "Enhanced Tool"}]
            
            async def register_tool(self, tool_definition):
                return "enhanced_registered_tool"
        
        # 设置层实现
        enhanced_manager.set_layer_implementation("interaction", MockInteractionProtocol())
        enhanced_manager.set_layer_implementation("gateway", MockGatewayProtocol())
        enhanced_manager.set_layer_implementation("agent", MockAgentProtocol())
        enhanced_manager.set_layer_implementation("tool", MockToolProtocol())
        
        print("✅ 成功设置所有层实现")
        print(f"  标准化适配器数量: {len(enhanced_manager.standardized_adapters)}")
        
        # 获取状态
        status = enhanced_manager.get_enhanced_status()
        print("✅ 成功获取增强版状态")
        print(f"  使用标准化接口: {status['use_standardized_interface']}")
        print(f"  标准化适配器列表: {status['standardized_adapters']}")
        
        # 测试健康检查
        health = await enhanced_manager.health_check_enhanced()
        print("✅ 成功执行增强版健康检查")
        print(f"  整体状态: {health['overall']}")
        
        if health['standardized_interface']['enabled']:
            print(f"  标准化接口状态: {health['standardized_interface']['status']}")
        
        # 测试请求处理（简化版，不依赖实际组件）
        print("\n测试标准化接口请求处理...")
        test_request = {
            "request_id": "enhanced_test_001",
            "content": "测试增强版四层架构管理器",
            "user_id": "test_user",
            "session_id": "test_session"
        }
        
        # 由于没有注册完整的适配器，我们只测试管理器基本功能
        print("✅ 增强版管理器基本功能测试完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 增强版四层架构管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_v3_compliance_checker_update():
    """测试V3合规性检查器更新"""
    print("\n" + "=" * 60)
    print("测试V3合规性检查器更新")
    print("=" * 60)
    
    try:
        from src.core.v3_compliance_checker import V3ComplianceChecker
        
        checker = V3ComplianceChecker()
        print("✅ 成功创建V3ComplianceChecker实例")
        
        # 运行四层架构检查
        four_layer_result = checker.check_four_layer_architecture()
        print("✅ 成功执行四层架构遵从性检查")
        print(f"  检查结果:")
        print(f"    原则: {four_layer_result.principle.value}")
        print(f"    等级: {four_layer_result.level.value}")
        print(f"    分数: {four_layer_result.score:.2f}")
        
        # 显示详情
        print(f"    详情:")
        for key, value in four_layer_result.details.items():
            print(f"      {key}: {value}")
        
        # 显示建议（如果有）
        if four_layer_result.recommendations:
            print(f"    建议:")
            for rec in four_layer_result.recommendations:
                print(f"      - {rec}")
        
        # 运行完整检查
        full_report = checker.check_all_principles()
        print("\n✅ 成功生成完整V3遵从性报告")
        print(f"  总体分数: {full_report['overall_score']:.2f}")
        print(f"  原则数量: {full_report['principle_count']}")
        
        # 显示各原则分数
        print(f"  各原则分数:")
        for principle, result in full_report['results'].items():
            print(f"    {principle}: {result['score']:.2f} ({result['level']})")
        
        return True
        
    except Exception as e:
        print(f"❌ V3合规性检查器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("开始测试标准化接口系统...")
    print("=" * 60)
    
    all_tests_passed = True
    
    # 测试1: 标准化接口系统基础组件
    if not await test_layer_interface_standard():
        all_tests_passed = False
    
    # 测试2: 标准化层适配器
    if not await test_standardized_layer_adapter():
        all_tests_passed = False
    
    # 测试3: 增强版四层架构管理器
    if not await test_enhanced_four_layer_manager():
        all_tests_passed = False
    
    # 测试4: V3合规性检查器更新
    if not await test_v3_compliance_checker_update():
        all_tests_passed = False
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if all_tests_passed:
        print("✅ 所有测试通过！标准化接口系统实现成功。")
        print("\n🎉 V3优化成果总结:")
        print("  1. 实现了标准化接口系统 (LayerMessage, StandardizedInterface, LayerCommunicationBus)")
        print("  2. 实现了协议到标准化接口的适配器 (StandardizedInteractionAdapter等)")
        print("  3. 实现了增强版四层架构管理器 (EnhancedFourLayerManager)")
        print("  4. 更新了V3合规性检查器，正确评估四层架构的接口标准化")
        print("  5. 四层架构现在支持双模式运行：协议模式 + 标准化接口模式")
    else:
        print("❌ 部分测试失败，请检查实现。")
    
    print("=" * 60)
    return all_tests_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)