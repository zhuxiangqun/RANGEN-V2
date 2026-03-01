#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评测系统集成测试

测试评测系统与生产系统的集成。
"""

import unittest
import asyncio
import tempfile
import os
import json
from pathlib import Path

import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from evaluation.benchmarks.frames_evaluator import FramesEvaluator, FramesDatasetLoader, FramesMetricsCalculator
from evaluation.benchmarks.unified_evaluator import UnifiedEvaluator, UnifiedDatasetLoader, UnifiedMetricsCalculator
from evaluation.benchmarks.performance_evaluator import PerformanceEvaluator, PerformanceDatasetLoader, PerformanceMetricsCalculator
from evaluation.adapters.research_system_adapter import ResearchSystemAdapter
from evaluation.reports.report_generator import ReportGenerator

class TestEvaluationIntegration(unittest.TestCase):
    """评测系统集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.research_adapter = ResearchSystemAdapter()
        
        # 检查研究系统是否可用
        system_info = self.research_adapter.get_system_info()
        if system_info.get('status') != 'available':
            self.skipTest("研究系统不可用，跳过集成测试")
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def test_frames_evaluation_integration(self):
        """测试FRAMES评测集成"""
        evaluator = FramesEvaluator(
            research_system=self.research_adapter,
            timeout=10.0,
            max_concurrent=2
        )
        
        # 执行小规模评测
        report = await evaluator.evaluate(sample_count=3)
        
        # 验证报告
        self.assertIsInstance(report, EvaluationReport)
        self.assertGreaterEqual(report.total_queries, 0)
        self.assertGreaterEqual(report.successful_queries, 0)
        self.assertGreaterEqual(report.failed_queries, 0)
    
    async def test_unified_evaluation_integration(self):
        """测试统一评测集成"""
        evaluator = UnifiedEvaluator(
            research_system=self.research_adapter,
            timeout=10.0,
            max_concurrent=2
        )
        
        # 执行小规模评测
        report = await evaluator.evaluate(sample_count=3)
        
        # 验证报告
        self.assertIsInstance(report, EvaluationReport)
        self.assertGreaterEqual(report.total_queries, 0)
        self.assertGreaterEqual(report.successful_queries, 0)
        self.assertGreaterEqual(report.failed_queries, 0)
    
    async def test_performance_evaluation_integration(self):
        """测试性能评测集成"""
        evaluator = PerformanceEvaluator(
            research_system=self.research_adapter,
            timeout=10.0,
            max_concurrent=2
        )
        
        # 执行小规模评测
        report = await evaluator.evaluate(sample_count=3)
        
        # 验证报告
        self.assertIsInstance(report, EvaluationReport)
        self.assertGreaterEqual(report.total_queries, 0)
        self.assertGreaterEqual(report.successful_queries, 0)
        self.assertGreaterEqual(report.failed_queries, 0)
        
        # 验证性能指标
        if report.metadata and 'performance_metrics' in report.metadata:
            perf_metrics = report.metadata['performance_metrics']
            self.assertIn('total_queries', perf_metrics)
            self.assertIn('successful_queries', perf_metrics)
            self.assertIn('success_rate', perf_metrics)
    
    def test_report_generation_integration(self):
        """测试报告生成集成"""
        from evaluation.interfaces import EvaluationReport, EvaluationResult
        from datetime import datetime
        
        # 创建测试报告
        results = [
            EvaluationResult(
                query="test query 1",
                answer="test answer 1",
                confidence=0.8,
                execution_time=1.0,
                success=True
            ),
            EvaluationResult(
                query="test query 2",
                answer="test answer 2",
                confidence=0.9,
                execution_time=2.0,
                success=True
            )
        ]
        
        report = EvaluationReport(
            total_queries=2,
            successful_queries=2,
            failed_queries=0,
            average_accuracy=0.85,
            average_execution_time=1.5,
            results=results
        )
        
        # 测试报告生成器
        report_generator = ReportGenerator()
        
        # 测试Markdown格式
        markdown_content = report_generator.generate_report(report, format="markdown")
        self.assertIn("# ", markdown_content)  # 检查是否有标题
        self.assertIn("总查询数", markdown_content)  # 检查是否有中文内容
        
        # 测试JSON格式
        json_content = report_generator.generate_report(report, format="json")
        json_data = json.loads(json_content)
        self.assertEqual(json_data['summary']['total_queries'], 2)
        self.assertEqual(json_data['summary']['successful_queries'], 2)
        
        # 测试HTML格式
        html_content = report_generator.generate_report(report, format="html")
        self.assertIn("<html", html_content)
        self.assertIn("</html>", html_content)
        
        # 测试保存报告
        report_file = os.path.join(self.temp_dir, "test_report.md")
        report_generator.save_report(report, report_file, format="markdown")
        self.assertTrue(os.path.exists(report_file))
        
        # 验证保存的内容
        with open(report_file, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        self.assertIn("总查询数", saved_content)
    
    def test_dataset_loading_integration(self):
        """测试数据集加载集成"""
        # 测试FRAMES数据集加载
        frames_loader = FramesDatasetLoader()
        frames_samples = frames_loader.load_samples(5)
        self.assertEqual(len(frames_samples), 5)
        
        # 测试统一数据集加载
        unified_loader = UnifiedDatasetLoader()
        unified_samples = unified_loader.load_samples(5)
        self.assertEqual(len(unified_samples), 5)
        
        # 测试性能数据集加载
        perf_loader = PerformanceDatasetLoader()
        perf_samples = perf_loader.load_samples(5)
        self.assertEqual(len(perf_samples), 5)
    
    def test_metrics_calculation_integration(self):
        """测试指标计算集成"""
        from evaluation.interfaces import EvaluationResult
        
        # 测试FRAMES指标计算
        frames_calculator = FramesMetricsCalculator()
        result = EvaluationResult(
            query="test",
            answer="test answer",
            confidence=0.8,
            execution_time=1.0,
            success=True
        )
        
        accuracy = frames_calculator.calculate_accuracy(result, "test answer")
        self.assertEqual(accuracy, 1.0)
        
        quality_score = frames_calculator.calculate_quality_score(result)
        self.assertGreater(quality_score, 0)
        
        # 测试性能指标计算
        perf_calculator = PerformanceMetricsCalculator()
        results = [result]
        metrics = perf_calculator.calculate_performance_metrics(results)
        self.assertIn('total_queries', metrics)
        self.assertIn('successful_queries', metrics)
        self.assertIn('success_rate', metrics)

def run_integration_tests():
    """运行集成测试"""
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEvaluationIntegration)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # 运行集成测试
    success = run_integration_tests()
    exit(0 if success else 1)
