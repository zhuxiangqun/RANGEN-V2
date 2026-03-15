#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RANGEN Gateway控制平面测试
测试基于OpenClaw Gateway架构的Gateway控制平面功能
"""

import os
import sys
import asyncio
import unittest
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_framework import RANGENTestCase
from src.core.gateway import (
    get_global_gateway,
    RANGENGateway,
    MessageChannel,
    MessagePriority,
    GatewayMessage,
    TaskStatus
)


class TestGatewayControlPlane(RANGENTestCase):
    """Gateway控制平面测试类"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        # 确保每次测试使用新的Gateway实例
        self.gateway = RANGENGateway()
    
    def tearDown(self):
        """测试后清理"""
        # 清理Gateway资源
        if hasattr(self, 'gateway'):
            # 检查Gateway是否已启动
            if hasattr(self.gateway, '_task_processor_task') and self.gateway._task_processor_task:
                try:
                    # 使用asyncio.run()来停止Gateway，它会创建一个新的事件循环
                    asyncio.run(self.gateway.stop())
                except RuntimeError:
                    # 如果已有事件循环在运行，则忽略
                    pass
        super().tearDown()
    
    def test_gateway_initialization(self):
        """测试Gateway初始化"""
        self.assertIsNotNone(self.gateway)
        self.assertIsNotNone(self.gateway.state_manager)
        self.assertIsNotNone(self.gateway.tool_system)
        self.assertIsNotNone(self.gateway.cost_controller)
        self.assertIsInstance(self.gateway.routing_rules, list)
        self.assertGreater(len(self.gateway.routing_rules), 0)
        
        # 检查任务队列（在start()之前应为空）
        self.assertIsInstance(self.gateway.task_queues, dict)
        self.assertEqual(len(self.gateway.task_queues), 0)
        
        # 检查车道管理器
        self.assertIsNotNone(self.gateway.lane_manager)
    
    def test_message_conversion(self):
        """测试消息格式转换"""
        raw_message = {
            "message_id": "test_msg_001",
            "sender": {"id": "user_001", "permissions": ["user"]},
            "content": {"query": "Hello world", "task_type": "general"},
            "metadata": {"project_id": "test_project"},
            "priority": "normal"
        }
        
        gateway_message = self.gateway._convert_to_gateway_format(
            MessageChannel.HTTP_API, raw_message
        )
        
        self.assertIsInstance(gateway_message, GatewayMessage)
        self.assertEqual(gateway_message.message_id, "test_msg_001")
        self.assertEqual(gateway_message.channel, MessageChannel.HTTP_API)
        self.assertEqual(gateway_message.sender["id"], "user_001")
        self.assertEqual(gateway_message.content["query"], "Hello world")
        self.assertEqual(gateway_message.priority, MessagePriority.NORMAL)
    
    @patch('src.core.gateway.RANGENGateway._get_or_create_session')
    def test_message_routing(self, mock_get_session):
        """测试消息路由"""
        mock_get_session.return_value = "session_test_001"
        
        # 测试代码生成任务路由
        message = GatewayMessage(
            message_id="test_001",
            channel=MessageChannel.HTTP_API,
            sender={"id": "user_001"},
            content={"task_type": "code_generation", "query": "写一个Python函数"},
            priority=MessagePriority.NORMAL
        )
        
        routing_result = asyncio.run(self.gateway._route_message(message))
        
        self.assertIsNotNone(routing_result)
        self.assertEqual(routing_result["agent_type"], "code_agent")
        self.assertEqual(routing_result["session_id"], "session_test_001")
        
        # 测试分析任务路由
        message.content["task_type"] = "analysis"
        routing_result = asyncio.run(self.gateway._route_message(message))
        self.assertEqual(routing_result["agent_type"], "analysis_agent")
        
        # 测试默认路由
        message.content["task_type"] = "unknown"
        routing_result = asyncio.run(self.gateway._route_message(message))
        self.assertEqual(routing_result["agent_type"], "general_agent")
    
    @patch('src.core.gateway.RANGENGateway._get_session_state')
    @patch('src.core.gateway.RANGENGateway._get_available_tools')
    async def test_agent_assembly(self, mock_get_tools, mock_get_state):
        """测试Agent装备"""
        mock_get_state.return_value = {
            "session_id": "session_test_001",
            "user_id": "user_001",
            "created_at": "2024-01-01T00:00:00",
            "message_count": 0,
            "total_cost": 0.0
        }
        
        mock_get_tools.return_value = ["tool1", "tool2", "tool3"]
        
        message = GatewayMessage(
            message_id="test_001",
            channel=MessageChannel.HTTP_API,
            sender={"id": "user_001", "permissions": ["user"]},
            content={"task_type": "code_generation"},
            metadata={"max_cost": 0.5, "timeout_seconds": 30.0},
            priority=MessagePriority.NORMAL
        )
        
        routing_result = {"agent_type": "code_agent", "session_id": "session_test_001"}
        safety_result = Mock()
        safety_result.warnings = []
        
        assembly_context = await self.gateway._assemble_agent_context(
            message, routing_result, safety_result
        )
        
        self.assertIsNotNone(assembly_context)
        self.assertEqual(assembly_context.agent_type, "code_agent")
        self.assertEqual(assembly_context.session_state["session_id"], "session_test_001")
        self.assertIn("tool1", assembly_context.available_tools)
        self.assertEqual(assembly_context.user_context["user_id"], "user_001")
        self.assertEqual(assembly_context.constraints["max_cost"], 0.5)
        self.assertEqual(assembly_context.constraints["timeout_seconds"], 30.0)
    
    def test_safety_checks(self):
        """测试安全前置检查"""
        message = GatewayMessage(
            message_id="test_001",
            channel=MessageChannel.HTTP_API,
            sender={"id": "user_001", "permissions": ["user"]},
            content={"query": "这是一个普通请求"},
            metadata={"project_id": "test_project"},
            priority=MessagePriority.NORMAL
        )
        
        routing_result = {"agent_type": "general_agent", "session_id": "session_test_001"}
        
        safety_result = asyncio.run(self.gateway._perform_safety_checks(message, routing_result))
        
        self.assertIsNotNone(safety_result)
        self.assertTrue(safety_result.allowed)
        self.assertEqual(safety_result.message, "安全前置检查通过")
        
        # 测试权限不足的情况
        routing_result["agent_type"] = "admin_agent"
        safety_result = asyncio.run(self.gateway._perform_safety_checks(message, routing_result))
        self.assertFalse(safety_result.allowed)
        self.assertIn("权限不足", safety_result.message)
    
    @patch('src.core.gateway.OuterSessionLoop')
    async def test_task_execution(self, mock_outer_loop):
        """测试任务执行"""
        # 模拟外层循环
        mock_loop_instance = AsyncMock()
        mock_loop_instance.run_session.return_value = {
            "success": True,
            "response": "任务执行成功",
            "iterations": 3
        }
        mock_outer_loop.return_value = mock_loop_instance
        
        message = GatewayMessage(
            message_id="test_001",
            channel=MessageChannel.HTTP_API,
            sender={"id": "user_001"},
            content={"query": "执行一个测试任务", "task_type": "general"},
            priority=MessagePriority.NORMAL
        )
        
        routing_result = {"agent_type": "general_agent", "session_id": "session_test_001"}
        
        assembly_context = Mock()
        assembly_context.session_state = {"session_id": "session_test_001"}
        assembly_context.user_context = {"user_id": "user_001"}
        assembly_context.available_tools = ["tool1", "tool2"]
        assembly_context.constraints = {
            "max_cost": 1.0,
            "timeout_seconds": 60.0,
            "max_iterations": 10
        }
        assembly_context.agent_type = "general_agent"
        
        task_id = "task_test_001"
        execution_result = await self.gateway._execute_agent_task(
            task_id, message, routing_result, assembly_context
        )
        
        self.assertIsNotNone(execution_result)
        self.assertEqual(execution_result.task_id, task_id)
        self.assertEqual(execution_result.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(execution_result.result)
        self.assertGreater(execution_result.execution_time, 0.0)
        
        # 验证外层循环被调用
        mock_outer_loop.assert_called_once()
        mock_loop_instance.run_session.assert_called_once()
    
    def test_lane_queue_manager(self):
        """测试车道式队列管理器"""
        lane_manager = self.gateway.lane_manager
        
        # 创建测试车道
        lane_id = lane_manager.create_lane("test_lane", lambda task: task.get("type") == "test")
        self.assertIn(lane_id, lane_manager.lanes)
        
        # 测试路由
        task_data = {"type": "test", "data": "test_data"}
        routed_lane = lane_manager.route_to_lane(task_data)
        self.assertEqual(routed_lane, lane_id)
        
        # 测试非匹配任务
        non_matching_task = {"type": "other", "data": "other_data"}
        routed_lane = lane_manager.route_to_lane(non_matching_task)
        self.assertIsNone(routed_lane)
    
    @patch('src.core.gateway.RANGENGateway._process_tasks')
    async def test_gateway_lifecycle(self, mock_process_tasks):
        """测试Gateway生命周期"""
        # 模拟任务处理器
        mock_process_tasks.return_value = None
        
        # 测试启动
        await self.gateway.start()
        
        # 测试接收消息
        raw_message = {
            "message_id": "test_lifecycle_001",
            "sender": {"id": "user_001"},
            "content": {"query": "生命周期测试", "task_type": "general"},
            "priority": "normal"
        }
        
        task_id = await self.gateway.receive_message(MessageChannel.HTTP_API, raw_message)
        self.assertIsNotNone(task_id)
        self.assertIn(task_id, self.gateway.active_tasks)
        
        # 测试获取任务状态
        task_status = await self.gateway.get_task_status(task_id)
        self.assertIsNotNone(task_status)
        self.assertEqual(task_status.get("task_id"), task_id)
        
        # 测试获取统计信息
        stats = self.gateway.get_gateway_stats()
        self.assertIsNotNone(stats)
        self.assertIn("active_tasks", stats)
        self.assertIn("completed_tasks", stats)
        
        # 测试停止
        await self.gateway.stop()


class TestGatewayIntegration(RANGENTestCase):
    """Gateway集成测试"""
    
    async def test_end_to_end_flow(self):
        """测试端到端流程"""
        gateway = RANGENGateway()
        
        try:
            await gateway.start()
            
            # 发送测试消息
            raw_message = {
                "message_id": "e2e_test_001",
                "sender": {"id": "user_001", "permissions": ["user"]},
                "content": {
                    "query": "请分析这个需求：创建一个用户登录系统",
                    "task_type": "analysis"
                },
                "metadata": {
                    "project_id": "test_project",
                    "max_cost": 0.8,
                    "timeout_seconds": 45.0
                },
                "priority": "high"
            }
            
            task_id = await gateway.receive_message(MessageChannel.HTTP_API, raw_message)
            self.assertIsNotNone(task_id)
            
            # 等待任务处理（简化：检查任务状态）
            await asyncio.sleep(0.1)
            
            task_status = await gateway.get_task_status(task_id)
            self.assertIsNotNone(task_status)
            
            # 验证统计信息
            stats = gateway.get_gateway_stats()
            self.assertGreaterEqual(stats["active_tasks"], 0)
            
        finally:
            await gateway.stop()


if __name__ == "__main__":
    unittest.main()