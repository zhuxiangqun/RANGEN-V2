#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评测系统单元测试

测试评测系统的各个组件功能。
"""

import unittest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch
from datetime import datetime

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from evaluation.interfaces import EvaluationRequest, EvaluationResult, EvaluationReport
from evaluation.benchmarks.frames_evaluator import FramesEvaluator, FramesDatasetLoader, FramesMetricsCalculator
from evaluation.benchmarks.unified_evaluator import UnifiedEvaluator, UnifiedDatasetLoader, UnifiedMetricsCalculator
from evaluation.benchmarks.performance_evaluator import PerformanceEvaluator, PerformanceDatasetLoader, PerformanceMetricsCalculator
from evaluation.adapters.research_system_adapter import ResearchSystemAdapter

class TestFramesDatasetLoader(unittest.TestCase):
    """测试FRAMES数据集加载器"""
    
    def setUp(self):
        self.loader = FramesDatasetLoader()
    
    def test_load_test_samples(self):
        """测试加载测试样本"""
        samples = self.loader.load_samples(5)
        self.assertEqual(len(samples), 5)
        self.assertIsInstance(samples[0], dict)
        self.assertIn('query', samples[0])
    
    def test_get_dataset_info(self):
        """测试获取数据集信息"""
        info = self.loader.get_dataset_info()
        self.assertIn('name', info)
        self.assertEqual(info['name'], 'FRAMES Benchmark')

class TestFramesMetricsCalculator(unittest.TestCase):
    """测试FRAMES评测指标计算器"""
    
    def setUp(self):
        self.calculator = FramesMetricsCalculator()
    
    def test_calculate_accuracy_exact_match(self):
        """测试完全匹配的准确率计算"""
        result = EvaluationResult(
            query="test",
            answer="Paris",
            confidence=0.8,
            execution_time=1.0,
            success=True
        )
        accuracy = self.calculator.calculate_accuracy(result, "Paris")
        self.assertEqual(accuracy, 1.0)
    
    def test_calculate_accuracy_no_match(self):
        """测试不匹配的准确率计算"""
        result = EvaluationResult(
            query="test",
            answer="London",
            confidence=0.8,
            execution_time=1.0,
            success=True
        )
        accuracy = self.calculator.calculate_accuracy(result, "Paris")
        self.assertLess(accuracy, 1.0)
    
    def test_calculate_quality_score(self):
        """测试质量分数计算"""
        result = EvaluationResult(
            query="test",
            answer="test answer",
            confidence=0.8,
            execution_time=1.0,
            success=True
        )
        quality_score = self.calculator.calculate_quality_score(result)
        self.assertGreater(quality_score, 0)
        self.assertLessEqual(quality_score, 1.0)
    
    def test_calculate_performance_metrics(self):
        """测试性能指标计算"""
        results = [
            EvaluationResult("q1", "a1", 0.8, 1.0, True),
            EvaluationResult("q2", "a2", 0.9, 2.0, True),
            EvaluationResult("q3", "", 0.0, 0.0, False)
        ]
        metrics = self.calculator.calculate_performance_metrics(results)
        
        self.assertEqual(metrics['total_queries'], 3)
        self.assertEqual(metrics['successful_queries'], 2)
        self.assertEqual(metrics['success_rate'], 2/3)

class TestUnifiedDatasetLoader(unittest.TestCase):
    """测试统一数据集加载器"""
    
    def setUp(self):
        self.loader = UnifiedDatasetLoader()
    
    def test_load_test_samples(self):
        """测试加载测试样本"""
        samples = self.loader.load_samples(3)
        self.assertEqual(len(samples), 3)
        self.assertIn('query', samples[0])
        self.assertIn('expected_answer', samples[0])
    
    def test_generate_test_samples(self):
        """测试生成测试样本"""
        samples = self.loader._generate_test_samples(5)
        self.assertEqual(len(samples), 5)
        
        # 检查样本结构
        for sample in samples:
            self.assertIn('query', sample)
            self.assertIn('expected_answer', sample)
            self.assertIn('category', sample)

class TestPerformanceDatasetLoader(unittest.TestCase):
    """测试性能数据集加载器"""
    
    def setUp(self):
        self.loader = PerformanceDatasetLoader()
    
    def test_load_test_samples(self):
        """测试加载测试样本"""
        samples = self.loader.load_samples(3)
        self.assertEqual(len(samples), 3)
        self.assertIn('query', samples[0])
        self.assertIn('complexity', samples[0])
    
    def test_generate_performance_samples(self):
        """测试生成性能测试样本"""
        samples = self.loader._generate_performance_samples(5)
        self.assertEqual(len(samples), 5)
        
        # 检查样本结构
        for sample in samples:
            self.assertIn('query', sample)
            self.assertIn('complexity', sample)
            self.assertIn('expected_response_time', sample)

class TestResearchSystemAdapter(unittest.TestCase):
    """测试研究系统适配器"""
    
    def setUp(self):
        self.adapter = ResearchSystemAdapter()
    
    def test_get_system_info(self):
        """测试获取系统信息"""
        info = self.adapter.get_system_info()
        self.assertIn('status', info)
        self.assertIn('timestamp', info)
    
    @patch('evaluation.adapters.research_system_adapter.asyncio.get_event_loop')
    def test_research_success(self, mock_get_event_loop):
        """测试研究请求成功"""
        # 模拟研究系统
        mock_system = Mock()
        mock_result = Mock()
        mock_result.result = "test answer"
        mock_result.confidence = 0.8
        mock_system.research.return_value = mock_result
        
        self.adapter.research_system = mock_system
        
        # 模拟事件循环
        mock_loop = Mock()
        mock_loop.run_in_executor.return_value = asyncio.Future()
        mock_loop.run_in_executor.return_value.set_result(mock_result)
        mock_get_event_loop.return_value = mock_loop
        
        # 创建测试请求
        request = EvaluationRequest(
            query="test query",
            context={"test": "context"},
            timeout=30.0
        )
        
        # 运行测试
        async def run_test():
            result = await self.adapter.research(request)
            self.assertEqual(result.query, "test query")
            self.assertEqual(result.answer, "test answer")
            self.assertEqual(result.confidence, 0.8)
            self.assertTrue(result.success)
        
        asyncio.run(run_test())

class TestEvaluationReport(unittest.TestCase):
    """测试评测报告"""
    
    def test_evaluation_report_creation(self):
        """测试评测报告创建"""
        results = [
            EvaluationResult("q1", "a1", 0.8, 1.0, True),
            EvaluationResult("q2", "a2", 0.9, 2.0, True)
        ]
        
        report = EvaluationReport(
            total_queries=2,
            successful_queries=2,
            failed_queries=0,
            average_accuracy=0.85,
            average_execution_time=1.5,
            results=results
        )
        
        self.assertEqual(report.total_queries, 2)
        self.assertEqual(report.successful_queries, 2)
        self.assertEqual(report.failed_queries, 0)
        self.assertEqual(report.average_accuracy, 0.85)
        self.assertEqual(report.average_execution_time, 1.5)
        self.assertEqual(len(report.results), 2)

if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
