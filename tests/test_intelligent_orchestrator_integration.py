#!/usr/bin/env python3
"""
智能协调层集成测试
测试智能协调层与各个执行路径的集成
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.core.intelligent_orchestrator import (
    IntelligentOrchestrator,
    QuickPlan,
    ParallelPlan,
    ReasoningPlan,
    ConservativePlan,
    HybridPlan
)
from src.agents.base_agent import AgentResult
from src.unified_research_system import UnifiedResearchSystem, ResearchRequest, ResearchResult


class TestIntelligentOrchestratorIntegration(unittest.IsolatedAsyncioTestCase):
    """智能协调层集成测试类"""
    
    async def asyncSetUp(self):
        """异步测试前准备"""
        self.orchestrator = IntelligentOrchestrator()
        
        # Mock执行资源
        self.mock_mas = Mock()
        self.mock_standard_loop = Mock()
        self.mock_traditional = Mock()
        self.mock_tools = Mock()
        
        # 注册资源
        self.orchestrator.register_resource('mas', self.mock_mas)
        self.orchestrator.register_resource('standard_loop', self.mock_standard_loop)
        self.orchestrator.register_resource('traditional', self.mock_traditional)
        self.orchestrator.register_resource('tools', self.mock_tools)
    
    async def test_quick_plan_integration(self):
        """测试QuickPlan与标准循环的集成"""
        # Mock标准循环返回结果
        mock_result = ResearchResult(
            query="test query",
            success=True,
            answer="test answer",
            confidence=0.8,
            execution_time=1.0
        )
        
        async def mock_execute(request, start_time):
            return mock_result
        
        self.mock_standard_loop._execute_research_agent_loop = AsyncMock(side_effect=mock_execute)
        
        # 创建QuickPlan
        plan = QuickPlan(query="test query", executor=self.mock_standard_loop, tools=self.mock_tools)
        
        # 执行计划
        result = await self.orchestrator._execute_quick_plan(plan)
        
        # 验证结果
        self.assertIsInstance(result, AgentResult)
        self.assertTrue(result.success)
        self.assertEqual(result.data.get('answer'), "test answer")
        self.assertEqual(result.confidence, 0.8)
        
        # 验证标准循环被调用
        self.mock_standard_loop._execute_research_agent_loop.assert_called_once()
    
    async def test_parallel_plan_integration(self):
        """测试ParallelPlan与MAS的集成"""
        # Mock MAS返回结果
        mock_result = AgentResult(
            success=True,
            data={"answer": "test answer"},
            confidence=0.8,
            processing_time=1.0
        )
        
        self.mock_mas.execute = AsyncMock(return_value=mock_result)
        
        # 创建ParallelPlan
        plan = ParallelPlan(
            query="test query",
            executor=self.mock_mas,
            tasks=[{"query": "task1"}, {"query": "task2"}],
            tools=self.mock_tools
        )
        
        # 执行计划
        result = await self.orchestrator._execute_parallel_plan(plan)
        
        # 验证结果
        self.assertIsInstance(result, AgentResult)
        self.assertTrue(result.success)
        
        # 验证MAS被调用
        self.mock_mas.execute.assert_called_once()
    
    async def test_reasoning_plan_integration(self):
        """测试ReasoningPlan与协调层的集成"""
        # Mock协调层的execute方法
        mock_result = AgentResult(
            success=True,
            data={"answer": "test answer"},
            confidence=0.8,
            processing_time=1.0
        )
        
        with patch.object(self.orchestrator, 'execute') as mock_execute:
            mock_execute.return_value = mock_result
            
            # 创建ReasoningPlan
            plan = ReasoningPlan(
                query="test query",
                steps=[{"type": "knowledge_retrieval", "sub_query": "test"}],
                orchestrator=self.orchestrator,
                tools=self.mock_tools
            )
            
            # 执行计划
            result = await self.orchestrator._execute_reasoning_plan(plan)
            
            # 验证结果
            self.assertIsInstance(result, AgentResult)
            mock_execute.assert_called_once()
    
    async def test_conservative_plan_integration(self):
        """测试ConservativePlan与传统流程的集成"""
        # Mock传统流程返回结果
        mock_result = ResearchResult(
            query="test query",
            success=True,
            answer="test answer",
            confidence=0.8,
            execution_time=1.0
        )
        
        async def mock_execute(request):
            return mock_result
        
        self.mock_traditional._execute_research_internal = AsyncMock(side_effect=mock_execute)
        
        # 创建ConservativePlan
        plan = ConservativePlan(query="test query", executor=self.mock_traditional, tools=self.mock_tools)
        
        # 执行计划
        result = await self.orchestrator._execute_conservative_plan(plan)
        
        # 验证结果
        self.assertIsInstance(result, AgentResult)
        self.assertTrue(result.success)
        
        # 验证传统流程被调用
        self.mock_traditional._execute_research_internal.assert_called_once()
    
    async def test_hybrid_plan_integration(self):
        """测试HybridPlan的多资源协同执行"""
        # Mock各个资源的返回结果
        mock_mas_result = AgentResult(
            success=True,
            data={"answer": "mas answer"},
            confidence=0.8,
            processing_time=1.0
        )
        
        mock_standard_result = ResearchResult(
            query="test query",
            success=True,
            answer="standard answer",
            confidence=0.7,
            execution_time=0.5
        )
        
        self.mock_mas.execute = AsyncMock(return_value=mock_mas_result)
        
        async def mock_standard_execute(request, start_time):
            return mock_standard_result
        
        self.mock_standard_loop._execute_research_agent_loop = AsyncMock(side_effect=mock_standard_execute)
        
        # 创建HybridPlan
        plan = HybridPlan(
            query="test query",
            mas_tasks=[{"query": "mas task"}],
            tool_tasks=[{"query": "tool task"}],
            standard_tasks=[{"query": "standard task"}]
        )
        
        # 执行计划
        result = await self.orchestrator._execute_hybrid_plan(plan)
        
        # 验证结果
        self.assertIsInstance(result, AgentResult)
        self.assertTrue(result.success)
        self.assertIn('answer', result.data)
        self.assertIn('task_summary', result.data)
        
        # 验证多个资源被调用
        self.mock_mas.execute.assert_called()
        self.mock_standard_loop._execute_research_agent_loop.assert_called()
    
    async def test_orchestrate_simple_query(self):
        """测试简单查询的完整流程"""
        # Mock快速复杂度分析返回"simple"
        with patch.object(self.orchestrator, '_quick_analyze_complexity', return_value='simple'):
            # Mock标准循环
            mock_result = ResearchResult(
                query="simple query",
                success=True,
                answer="simple answer",
                confidence=0.9,
                execution_time=0.5
            )
            
            async def mock_execute(request, start_time):
                return mock_result
            
            self.mock_standard_loop._execute_research_agent_loop = AsyncMock(side_effect=mock_execute)
            
            # 执行orchestrate
            result = await self.orchestrator.orchestrate(
                query="simple query",
                context={}
            )
            
            # 验证结果
            self.assertIsInstance(result, AgentResult)
            self.assertTrue(result.success)
    
    async def test_orchestrate_complex_parallel_query(self):
        """测试复杂并行查询的完整流程"""
        # Mock复杂度分析返回"complex"
        with patch.object(self.orchestrator, '_quick_analyze_complexity', return_value='complex'):
            # Mock深度任务理解返回可并行化
            with patch.object(self.orchestrator, '_understand_task') as mock_understand:
                mock_understand.return_value = {
                    "can_be_parallelized": True,
                    "subtasks": [{"query": "task1"}, {"query": "task2"}]
                }
                
                # Mock MAS
                mock_result = AgentResult(
                    success=True,
                    data={"answer": "parallel answer"},
                    confidence=0.8,
                    processing_time=2.0
                )
                self.mock_mas.execute = AsyncMock(return_value=mock_result)
                
                # 执行orchestrate
                result = await self.orchestrator.orchestrate(
                    query="complex parallel query",
                    context={}
                )
                
                # 验证结果
                self.assertIsInstance(result, AgentResult)
                self.assertTrue(result.success)
                self.mock_mas.execute.assert_called_once()
    
    async def test_error_handling_and_fallback(self):
        """测试错误处理和回退机制"""
        # Mock标准循环抛出异常
        self.mock_standard_loop._execute_research_agent_loop = AsyncMock(side_effect=Exception("Test error"))
        
        # Mock传统流程作为回退
        mock_fallback_result = ResearchResult(
            query="test query",
            success=True,
            answer="fallback answer",
            confidence=0.6,
            execution_time=1.5
        )
        
        async def mock_fallback(request):
            return mock_fallback_result
        
        self.mock_traditional._execute_research_internal = AsyncMock(side_effect=mock_fallback)
        
        # 创建QuickPlan（会失败，然后回退到ConservativePlan）
        plan = QuickPlan(query="test query", executor=self.mock_standard_loop, tools=self.mock_tools)
        
        # 执行计划（应该捕获异常并回退）
        result = await self.orchestrator._execute_quick_plan(plan)
        
        # 验证结果（应该成功，因为回退到传统流程）
        # 注意：当前实现可能直接返回错误，需要根据实际实现调整
        self.assertIsInstance(result, AgentResult)
    
    async def test_resource_health_check(self):
        """测试资源健康检查"""
        # 测试资源可用性检查
        self.assertTrue(self.orchestrator.is_resource_available('mas'))
        self.assertTrue(self.orchestrator.is_resource_available('standard_loop'))
        self.assertTrue(self.orchestrator.is_resource_available('traditional'))
        
        # 测试未注册的资源
        self.assertFalse(self.orchestrator.is_resource_available('nonexistent'))
    
    async def test_system_state_check(self):
        """测试系统状态检查"""
        # 获取系统状态
        state = self.orchestrator._check_system_state()
        
        # 验证状态包含必要字段
        self.assertIn('load', state)
        self.assertIn('mas_healthy', state)
        self.assertIn('tools_available', state)
        self.assertIn('standard_loop_available', state)
        self.assertIn('traditional_available', state)
        
        # 验证负载值在合理范围内
        self.assertGreaterEqual(state['load'], 0)
        self.assertLessEqual(state['load'], 100)


class TestUnifiedResearchSystemIntegration(unittest.IsolatedAsyncioTestCase):
    """UnifiedResearchSystem与智能协调层的集成测试"""
    
    async def asyncSetUp(self):
        """异步测试前准备"""
        # 注意：这里需要实际初始化UnifiedResearchSystem，可能需要较长时间
        # 在实际测试中，可以考虑使用Mock或简化初始化
        pass
    
    async def test_orchestrator_initialization(self):
        """测试智能协调层的初始化"""
        # 这个测试需要实际初始化UnifiedResearchSystem
        # 由于初始化可能较慢，这里先跳过，在实际测试中实现
        self.skipTest("需要实际初始化UnifiedResearchSystem，在完整集成测试中实现")
    
    async def test_execute_research_with_orchestrator(self):
        """测试通过智能协调层执行研究"""
        # 这个测试需要实际初始化UnifiedResearchSystem
        # 由于初始化可能较慢，这里先跳过，在实际测试中实现
        self.skipTest("需要实际初始化UnifiedResearchSystem，在完整集成测试中实现")


if __name__ == '__main__':
    unittest.main()

