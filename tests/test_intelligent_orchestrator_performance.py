#!/usr/bin/env python3
"""
智能协调层性能测试
验证新架构的性能表现
"""

import unittest
import asyncio
import time
import statistics
from unittest.mock import Mock, AsyncMock, patch
from src.core.intelligent_orchestrator import (
    IntelligentOrchestrator,
    QuickPlan,
    ParallelPlan,
    ConservativePlan
)
from src.agents.base_agent import AgentResult
from src.unified_research_system import ResearchResult


class TestIntelligentOrchestratorPerformance(unittest.IsolatedAsyncioTestCase):
    """智能协调层性能测试类"""
    
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
    
    async def test_simple_query_response_time(self):
        """测试简单查询的响应时间（应<1秒）"""
        # Mock快速执行（模拟简单查询）
        async def fast_execute(request, start_time):
            await asyncio.sleep(0.1)  # 模拟100ms执行时间
            return ResearchResult(
                query="simple query",
                success=True,
                answer="answer",
                confidence=0.9,
                execution_time=0.1
            )
        
        self.mock_standard_loop._execute_research_agent_loop = AsyncMock(side_effect=fast_execute)
        
        # Mock复杂度分析返回"simple"
        with patch.object(self.orchestrator, '_quick_analyze_complexity', return_value='simple'):
            # 执行多次测试
            response_times = []
            for _ in range(10):
                start_time = time.time()
                result = await self.orchestrator.orchestrate(
                    query="simple query",
                    context={}
                )
                response_time = time.time() - start_time
                response_times.append(response_time)
                self.assertTrue(result.success)
            
            # 计算统计信息
            avg_time = statistics.mean(response_times)
            p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
            
            # 验证平均响应时间<1秒
            self.assertLess(avg_time, 1.0, f"平均响应时间 {avg_time:.3f}秒 超过1秒")
            
            # 验证95%分位响应时间<1.5秒
            self.assertLess(p95_time, 1.5, f"95%分位响应时间 {p95_time:.3f}秒 超过1.5秒")
            
            print(f"\n简单查询性能:")
            print(f"  平均响应时间: {avg_time:.3f}秒")
            print(f"  95%分位响应时间: {p95_time:.3f}秒")
            print(f"  最小响应时间: {min(response_times):.3f}秒")
            print(f"  最大响应时间: {max(response_times):.3f}秒")
    
    async def test_complex_query_response_time(self):
        """测试复杂查询的响应时间（应<10秒）"""
        # Mock较慢执行（模拟复杂查询）
        async def slow_execute(request, start_time):
            await asyncio.sleep(2.0)  # 模拟2秒执行时间
            return ResearchResult(
                query="complex query",
                success=True,
                answer="answer",
                confidence=0.8,
                execution_time=2.0
            )
        
        self.mock_traditional._execute_research_internal = AsyncMock(side_effect=slow_execute)
        
        # Mock复杂度分析返回"complex"
        with patch.object(self.orchestrator, '_quick_analyze_complexity', return_value='complex'):
            # Mock深度任务理解返回需要传统流程
            with patch.object(self.orchestrator, '_understand_task') as mock_understand:
                mock_understand.return_value = {
                    "can_be_parallelized": False,
                    "requires_deep_reasoning": False
                }
                
                # 执行多次测试
                response_times = []
                for _ in range(5):
                    start_time = time.time()
                    result = await self.orchestrator.orchestrate(
                        query="complex query",
                        context={}
                    )
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    self.assertTrue(result.success)
                
                # 计算统计信息
                avg_time = statistics.mean(response_times)
                p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
                
                # 验证平均响应时间<10秒
                self.assertLess(avg_time, 10.0, f"平均响应时间 {avg_time:.3f}秒 超过10秒")
                
                print(f"\n复杂查询性能:")
                print(f"  平均响应时间: {avg_time:.3f}秒")
                print(f"  95%分位响应时间: {p95_time:.3f}秒")
    
    async def test_concurrent_queries(self):
        """测试并发查询的处理能力"""
        # Mock执行资源
        async def concurrent_execute(request, start_time):
            await asyncio.sleep(0.5)  # 模拟500ms执行时间
            return ResearchResult(
                query=request.query,
                success=True,
                answer="answer",
                confidence=0.8,
                execution_time=0.5
            )
        
        self.mock_standard_loop._execute_research_agent_loop = AsyncMock(side_effect=concurrent_execute)
        
        # Mock复杂度分析返回"simple"
        with patch.object(self.orchestrator, '_quick_analyze_complexity', return_value='simple'):
            # 并发执行多个查询
            queries = [f"query_{i}" for i in range(10)]
            
            start_time = time.time()
            tasks = [
                self.orchestrator.orchestrate(query=query, context={})
                for query in queries
            ]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            # 验证所有查询都成功
            for result in results:
                self.assertTrue(result.success)
            
            # 验证并发执行时间小于串行执行时间
            # 串行执行时间约为 10 * 0.5 = 5秒
            # 并发执行时间应该明显小于5秒
            self.assertLess(total_time, 3.0, f"并发执行时间 {total_time:.3f}秒 过长")
            
            print(f"\n并发查询性能:")
            print(f"  查询数量: {len(queries)}")
            print(f"  总执行时间: {total_time:.3f}秒")
            print(f"  平均每个查询: {total_time/len(queries):.3f}秒")
            print(f"  吞吐量: {len(queries)/total_time:.2f} QPS")
    
    async def test_high_load_performance(self):
        """测试系统负载高时的性能表现"""
        # Mock系统负载高（>80%）
        with patch.object(self.orchestrator, '_check_system_state') as mock_state:
            mock_state.return_value = {
                'load': 85.0,
                'mas_healthy': True,
                'tools_available': True,
                'standard_loop_available': True,
                'traditional_available': True
            }
            
            # Mock快速执行（应该使用QuickPlan）
            async def fast_execute(request, start_time):
                await asyncio.sleep(0.1)
                return ResearchResult(
                    query="query",
                    success=True,
                    answer="answer",
                    confidence=0.8,
                    execution_time=0.1
                )
            
            self.mock_standard_loop._execute_research_agent_loop = AsyncMock(side_effect=fast_execute)
            
            # Mock复杂度分析
            with patch.object(self.orchestrator, '_quick_analyze_complexity', return_value='medium'):
                # 执行查询
                start_time = time.time()
                result = await self.orchestrator.orchestrate(
                    query="test query",
                    context={}
                )
                response_time = time.time() - start_time
                
                # 验证结果
                self.assertTrue(result.success)
                
                # 验证在高负载下仍然使用快速路径
                # 应该使用QuickPlan而不是深度规划
                self.assertLess(response_time, 1.0, f"高负载下响应时间 {response_time:.3f}秒 过长")
                
                print(f"\n高负载性能:")
                print(f"  系统负载: 85%")
                print(f"  响应时间: {response_time:.3f}秒")
    
    async def test_resource_utilization(self):
        """测试资源利用率"""
        # 记录资源调用次数
        mas_call_count = 0
        standard_call_count = 0
        traditional_call_count = 0
        
        async def mas_execute(context):
            nonlocal mas_call_count
            mas_call_count += 1
            await asyncio.sleep(0.1)
            return AgentResult(
                success=True,
                data={"answer": "mas answer"},
                confidence=0.8,
                processing_time=0.1
            )
        
        async def standard_execute(request, start_time):
            nonlocal standard_call_count
            standard_call_count += 1
            await asyncio.sleep(0.1)
            return ResearchResult(
                query=request.query,
                success=True,
                answer="standard answer",
                confidence=0.8,
                execution_time=0.1
            )
        
        async def traditional_execute(request):
            nonlocal traditional_call_count
            traditional_call_count += 1
            await asyncio.sleep(0.1)
            return ResearchResult(
                query=request.query,
                success=True,
                answer="traditional answer",
                confidence=0.8,
                execution_time=0.1
            )
        
        self.mock_mas.execute = AsyncMock(side_effect=mas_execute)
        self.mock_standard_loop._execute_research_agent_loop = AsyncMock(side_effect=standard_execute)
        self.mock_traditional._execute_research_internal = AsyncMock(side_effect=traditional_execute)
        
        # 执行不同类型的查询
        queries = [
            ("simple query", "simple"),
            ("complex parallel query", "complex"),
            ("complex reasoning query", "complex"),
        ]
        
        for query, complexity in queries:
            with patch.object(self.orchestrator, '_quick_analyze_complexity', return_value=complexity):
                with patch.object(self.orchestrator, '_understand_task') as mock_understand:
                    if complexity == "simple":
                        # 简单查询使用标准循环
                        pass
                    elif "parallel" in query:
                        # 并行查询使用MAS
                        mock_understand.return_value = {
                            "can_be_parallelized": True,
                            "subtasks": [{"query": "task1"}]
                        }
                    else:
                        # 其他复杂查询使用传统流程
                        mock_understand.return_value = {
                            "can_be_parallelized": False,
                            "requires_deep_reasoning": False
                        }
                    
                    result = await self.orchestrator.orchestrate(query=query, context={})
                    self.assertTrue(result.success)
        
        # 验证资源使用情况
        print(f"\n资源利用率:")
        print(f"  MAS调用次数: {mas_call_count}")
        print(f"  标准循环调用次数: {standard_call_count}")
        print(f"  传统流程调用次数: {traditional_call_count}")
        
        # 验证资源被正确使用
        self.assertGreater(standard_call_count, 0, "标准循环应该被使用")
        self.assertGreater(mas_call_count, 0, "MAS应该被使用（对于并行查询）")
        self.assertGreater(traditional_call_count, 0, "传统流程应该被使用（对于复杂查询）")


if __name__ == '__main__':
    unittest.main()

