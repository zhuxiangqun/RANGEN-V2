#!/usr/bin/env python3
"""
智能协调层单元测试
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.core.intelligent_orchestrator import (
    IntelligentOrchestrator,
    Plan,
    QuickPlan,
    ParallelPlan,
    ReasoningPlan,
    ConservativePlan,
    HybridPlan
)
from src.agents.base_agent import AgentResult


class TestIntelligentOrchestrator(unittest.TestCase):
    """智能协调层测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.orchestrator = IntelligentOrchestrator()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.orchestrator)
        self.assertIsNone(self.orchestrator.mas)
        self.assertIsNone(self.orchestrator.standard_loop)
        self.assertIsNone(self.orchestrator.traditional)
        self.assertIsNotNone(self.orchestrator.tools)
    
    def test_register_resource(self):
        """测试资源注册"""
        mock_mas = Mock()
        mock_standard_loop = Mock()
        mock_traditional = Mock()
        mock_tools = Mock()
        
        self.orchestrator.register_resource('mas', mock_mas)
        self.orchestrator.register_resource('standard_loop', mock_standard_loop)
        self.orchestrator.register_resource('traditional', mock_traditional)
        self.orchestrator.register_resource('tools', mock_tools)
        
        self.assertEqual(self.orchestrator.mas, mock_mas)
        self.assertEqual(self.orchestrator.standard_loop, mock_standard_loop)
        self.assertEqual(self.orchestrator.traditional, mock_traditional)
        self.assertEqual(self.orchestrator.tools, mock_tools)
    
    def test_quick_analyze_complexity(self):
        """测试快速复杂度分析"""
        # 简单任务
        simple_query = "What is the capital of France?"
        complexity = self.orchestrator._quick_analyze_complexity(simple_query)
        self.assertIn(complexity, ['simple', 'medium', 'complex'])
        
        # 复杂任务
        complex_query = "Compare the economic policies of France and Germany, and analyze their impact on the European Union."
        complexity = self.orchestrator._quick_analyze_complexity(complex_query)
        self.assertIn(complexity, ['simple', 'medium', 'complex'])
    
    def test_check_system_state(self):
        """测试系统状态检查"""
        state = self.orchestrator._check_system_state()
        self.assertIsInstance(state, dict)
        self.assertIn('load', state)
        self.assertIn('mas_healthy', state)
        self.assertIn('tools_available', state)
        self.assertIn('standard_loop_available', state)
        self.assertIn('traditional_available', state)
    
    def test_is_resource_available(self):
        """测试资源可用性检查"""
        # 未注册的资源应该不可用
        self.assertFalse(self.orchestrator.is_resource_available('mas'))
        
        # 注册资源后应该可用
        mock_mas = Mock()
        mock_mas._is_initialized = True
        self.orchestrator.register_resource('mas', mock_mas)
        self.assertTrue(self.orchestrator.is_resource_available('mas'))
    
    @patch('src.core.intelligent_orchestrator.psutil')
    def test_get_system_load(self, mock_psutil):
        """测试系统负载获取"""
        # Mock psutil
        mock_psutil.cpu_percent.return_value = 50.0
        mock_memory = Mock()
        mock_memory.percent = 60.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        load = self.orchestrator._get_system_load()
        self.assertIsInstance(load, float)
        self.assertGreaterEqual(load, 0)
        self.assertLessEqual(load, 100)
    
    def test_understand_task_by_rules(self):
        """测试基于规则的任务理解"""
        # 可并行化的任务
        parallel_query = "Compare France and Germany"
        understanding = self.orchestrator._understand_task_by_rules(parallel_query)
        self.assertIsInstance(understanding, dict)
        self.assertIn('can_be_parallelized', understanding)
        self.assertIn('requires_deep_reasoning', understanding)
        
        # 需要深度推理的任务
        reasoning_query = "Analyze the causes of World War II"
        understanding = self.orchestrator._understand_task_by_rules(reasoning_query)
        self.assertIsInstance(understanding, dict)
        self.assertIn('requires_deep_reasoning', understanding)


class TestPlanClasses(unittest.TestCase):
    """Plan类测试"""
    
    def test_plan_creation(self):
        """测试Plan类创建"""
        plan = Plan(query="test query")
        self.assertEqual(plan.query, "test query")
        self.assertIsNone(plan.tools)
    
    def test_quick_plan_creation(self):
        """测试QuickPlan创建"""
        executor = Mock()
        plan = QuickPlan(query="test query", executor=executor)
        self.assertEqual(plan.query, "test query")
        self.assertEqual(plan.executor, executor)
    
    def test_parallel_plan_creation(self):
        """测试ParallelPlan创建"""
        executor = Mock()
        tasks = ["task1", "task2"]
        plan = ParallelPlan(query="test query", executor=executor, tasks=tasks)
        self.assertEqual(plan.query, "test query")
        self.assertEqual(plan.executor, executor)
        self.assertEqual(plan.tasks, tasks)
    
    def test_reasoning_plan_creation(self):
        """测试ReasoningPlan创建"""
        orchestrator = Mock()
        steps = ["step1", "step2"]
        plan = ReasoningPlan(query="test query", steps=steps, orchestrator=orchestrator)
        self.assertEqual(plan.query, "test query")
        self.assertEqual(plan.steps, steps)
        self.assertEqual(plan.orchestrator, orchestrator)
    
    def test_conservative_plan_creation(self):
        """测试ConservativePlan创建"""
        executor = Mock()
        plan = ConservativePlan(query="test query", executor=executor)
        self.assertEqual(plan.query, "test query")
        self.assertEqual(plan.executor, executor)
    
    def test_hybrid_plan_creation(self):
        """测试HybridPlan创建"""
        mas_tasks = ["mas_task1"]
        tool_tasks = ["tool_task1"]
        standard_tasks = ["standard_task1"]
        plan = HybridPlan(
            query="test query",
            mas_tasks=mas_tasks,
            tool_tasks=tool_tasks,
            standard_tasks=standard_tasks
        )
        self.assertEqual(plan.query, "test query")
        self.assertEqual(plan.mas_tasks, mas_tasks)
        self.assertEqual(plan.tool_tasks, tool_tasks)
        self.assertEqual(plan.standard_tasks, standard_tasks)


class TestPlanExecution(unittest.IsolatedAsyncioTestCase):
    """Plan执行测试（异步）"""
    
    async def asyncSetUp(self):
        """异步测试前准备"""
        self.orchestrator = IntelligentOrchestrator()
    
    async def test_execute_quick_plan(self):
        """测试QuickPlan执行"""
        # Mock executor
        mock_executor = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.answer = "test answer"
        mock_result.knowledge = []
        mock_result.reasoning = None
        mock_result.citations = []
        mock_result.confidence = 0.8
        mock_result.execution_time = 1.0
        mock_result.error = None
        
        # Mock _execute_research_agent_loop
        async def mock_execute(request, start_time):
            return mock_result
        
        mock_executor._execute_research_agent_loop = AsyncMock(side_effect=mock_execute)
        
        plan = QuickPlan(query="test query", executor=mock_executor)
        result = await self.orchestrator._execute_quick_plan(plan)
        
        self.assertIsInstance(result, AgentResult)
        self.assertTrue(result.success)
    
    async def test_execute_parallel_plan(self):
        """测试ParallelPlan执行"""
        # Mock MAS executor
        mock_mas = Mock()
        mock_result = AgentResult(
            success=True,
            data={"answer": "test answer"},
            confidence=0.8,
            processing_time=1.0
        )
        mock_mas.execute = AsyncMock(return_value=mock_result)
        
        plan = ParallelPlan(query="test query", executor=mock_mas, tasks=[])
        result = await self.orchestrator._execute_parallel_plan(plan)
        
        self.assertIsInstance(result, AgentResult)
        self.assertTrue(result.success)
    
    async def test_execute_reasoning_plan(self):
        """测试ReasoningPlan执行"""
        plan = ReasoningPlan(query="test query", steps=[], orchestrator=self.orchestrator)
        
        # Mock父类的execute方法
        with patch.object(self.orchestrator, 'execute') as mock_execute:
            mock_result = AgentResult(
                success=True,
                data={"answer": "test answer"},
                confidence=0.8,
                processing_time=1.0
            )
            mock_execute.return_value = mock_result
            
            result = await self.orchestrator._execute_reasoning_plan(plan)
            
            self.assertIsInstance(result, AgentResult)
            mock_execute.assert_called_once()


if __name__ == '__main__':
    unittest.main()

