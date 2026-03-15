#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能评测器

专门用于评测系统性能，包括响应时间、吞吐量、资源使用等指标。
"""

import asyncio
import time
import logging
import psutil
import gc
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..interfaces import (
    ResearchSystemInterface, 
    DatasetInterface, 
    MetricsInterface,
    EvaluationRequest, 
    EvaluationResult, 
    EvaluationReport
)

class PerformanceDatasetLoader(DatasetInterface):
    """性能评测数据集加载器"""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path
        self.logger = logging.getLogger(__name__)
    
    def load_samples(self, count: int = None) -> List[Dict[str, Any]]:
        """加载性能评测样本"""
        try:
            if not self.data_path or not os.path.exists(self.data_path):
                # 生成性能测试样本
                return self._generate_performance_samples(count or 20)
            
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("数据集格式错误：应为列表格式")
            
            # 限制样本数量
            if count and count < len(data):
                data = data[:count]
            
            self.logger.info(f"成功加载 {len(data)} 个性能评测样本")
            return data
            
        except Exception as e:
            self.logger.error(f"加载性能评测数据集失败: {e}")
            return self._generate_performance_samples(count or 20)
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """获取数据集信息"""
        try:
            if self.data_path and os.path.exists(self.data_path):
                file_size = os.path.getsize(self.data_path)
                return {
                    "name": "Performance Test Dataset",
                    "path": self.data_path,
                    "file_size": file_size,
                    "file_size_mb": file_size / (1024 * 1024)
                }
        except Exception as e:
            self.logger.error(f"获取数据集信息失败: {e}")
        
        return {"name": "Performance Test Dataset", "path": self.data_path}
    
    def _generate_performance_samples(self, count: int) -> List[Dict[str, Any]]:
        """生成性能测试样本"""
        # 不同复杂度的查询样本
        sample_templates = [
            {
                "query": "What is the weather today?",
                "complexity": "simple",
                "expected_response_time": 1.0
            },
            {
                "query": "Explain the theory of relativity in detail",
                "complexity": "medium",
                "expected_response_time": 5.0
            },
            {
                "query": "Analyze the economic impact of climate change on global markets",
                "complexity": "complex",
                "expected_response_time": 10.0
            },
            {
                "query": "What are the latest developments in artificial intelligence?",
                "complexity": "medium",
                "expected_response_time": 3.0
            },
            {
                "query": "How does quantum computing work?",
                "complexity": "complex",
                "expected_response_time": 8.0
            }
        ]
        
        samples = []
        for i in range(count):
            template = sample_templates[i % len(sample_templates)]
            sample = template.copy()
            sample["query"] = f"{template['query']} (Test {i+1})"
            sample["expected_answer"] = f"Performance test response for: {sample['query']}"
            samples.append(sample)
        
        return samples

class PerformanceMetricsCalculator(MetricsInterface):
    """性能评测指标计算器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.process = psutil.Process()
    
    def calculate_accuracy(self, result: EvaluationResult, expected: str) -> float:
        """计算准确率（性能评测中简化处理）"""
        try:
            if not result.success:
                return 0.0
            
            # 性能评测中，只要成功响应就算准确
            return 1.0 if result.answer else 0.0
            
        except Exception as e:
            self.logger.error(f"计算准确率失败: {e}")
            return 0.0
    
    def calculate_quality_score(self, result: EvaluationResult) -> float:
        """计算质量分数（基于性能指标）"""
        try:
            if not result.success:
                return 0.0
            
            # 基于响应时间和置信度的质量分数
            response_time_score = max(0, 1 - result.execution_time / 30.0)  # 30秒为满分
            confidence_score = result.confidence
            
            quality_score = (response_time_score * 0.6 + confidence_score * 0.4)
            return min(1.0, max(0.0, quality_score))
            
        except Exception as e:
            self.logger.error(f"计算质量分数失败: {e}")
            return 0.0
    
    def calculate_performance_metrics(self, results: List[EvaluationResult]) -> Dict[str, float]:
        """计算性能指标"""
        try:
            if not results:
                return {}
            
            successful_results = [r for r in results if r.success]
            execution_times = [r.execution_time for r in successful_results]
            
            # 基本性能指标
            metrics = {
                "total_queries": len(results),
                "successful_queries": len(successful_results),
                "success_rate": len(successful_results) / len(results) if results else 0.0,
                "average_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0.0,
                "min_execution_time": min(execution_times) if execution_times else 0.0,
                "max_execution_time": max(execution_times) if execution_times else 0.0
            }
            
            # 吞吐量指标
            if execution_times:
                total_time = sum(execution_times)
                metrics["queries_per_second"] = len(execution_times) / total_time if total_time > 0 else 0.0
                metrics["average_throughput"] = 1.0 / metrics["average_execution_time"] if metrics["average_execution_time"] > 0 else 0.0
            
            # 响应时间分布
            if execution_times:
                sorted_times = sorted(execution_times)
                n = len(sorted_times)
                metrics["p50_response_time"] = sorted_times[n//2] if n > 0 else 0.0
                metrics["p90_response_time"] = sorted_times[int(n*0.9)] if n > 0 else 0.0
                metrics["p95_response_time"] = sorted_times[int(n*0.95)] if n > 0 else 0.0
                metrics["p99_response_time"] = sorted_times[int(n*0.99)] if n > 0 else 0.0
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"计算性能指标失败: {e}")
            return {}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            process_memory = self.process.memory_info()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_percent": memory.percent,
                "process_memory_rss": process_memory.rss,
                "process_memory_vms": process_memory.vms,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_percent": disk.percent
            }
            
        except Exception as e:
            self.logger.error(f"获取系统指标失败: {e}")
            return {}

class PerformanceEvaluator:
    """性能评测器"""
    
    def __init__(self, 
                 research_system: ResearchSystemInterface,
                 dataset_loader: DatasetInterface = None,
                 metrics_calculator: MetricsInterface = None,
                 timeout: float = 30.0,
                 max_concurrent: int = 5):
        
        self.research_system = research_system
        self.dataset_loader = dataset_loader or PerformanceDatasetLoader()
        self.metrics_calculator = metrics_calculator or PerformanceMetricsCalculator()
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(__name__)
    
    async def evaluate(self, sample_count: int = None) -> EvaluationReport:
        """执行性能评测"""
        self.logger.info("开始性能评测")
        
        # 记录评测开始时的系统状态
        start_system_metrics = self.metrics_calculator.get_system_metrics()
        
        # 加载数据集
        samples = self.dataset_loader.load_samples(sample_count)
        if not samples:
            self.logger.error("无法加载性能评测数据集")
            return self._create_empty_report()
        
        # 执行评测
        results = []
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def evaluate_sample(sample: Dict[str, Any]) -> EvaluationResult:
            async with semaphore:
                return await self._evaluate_single_sample(sample)
        
        # 并发执行评测
        start_time = time.time()
        tasks = [evaluate_sample(sample) for sample in samples]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # 记录评测结束时的系统状态
        end_system_metrics = self.metrics_calculator.get_system_metrics()
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"样本 {i} 评测失败: {result}")
                processed_results.append(EvaluationResult(
                    query=samples[i].get("query", ""),
                    answer="",
                    confidence=0.0,
                    execution_time=0.0,
                    success=False,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        # 生成报告
        report = self._generate_report(processed_results, total_time, start_system_metrics, end_system_metrics)
        self.logger.info(f"性能评测完成: {report.successful_queries}/{report.total_queries} 成功")
        
        return report
    
    async def _evaluate_single_sample(self, sample: Dict[str, Any]) -> EvaluationResult:
        """评测单个样本"""
        try:
            query = sample.get("query", "")
            expected_answer = sample.get("expected_answer", "")
            complexity = sample.get("complexity", "medium")
            
            # 创建评测请求
            request = EvaluationRequest(
                query=query,
                context={
                    "dataset": "performance",
                    "expected_answer": expected_answer,
                    "complexity": complexity,
                    "performance_test": True
                },
                timeout=self.timeout
            )
            
            # 执行研究
            start_time = time.time()
            result = await self.research_system.research(request)
            execution_time = time.time() - start_time
            
            # 计算准确率
            accuracy = self.metrics_calculator.calculate_accuracy(result, expected_answer)
            
            # 计算质量分数
            quality_score = self.metrics_calculator.calculate_quality_score(result)
            
            return EvaluationResult(
                query=query,
                answer=result.answer,
                confidence=result.confidence,
                execution_time=execution_time,
                success=result.success,
                error=result.error,
                metadata={
                    "expected_answer": expected_answer,
                    "accuracy": accuracy,
                    "quality_score": quality_score,
                    "complexity": complexity,
                    "expected_response_time": sample.get("expected_response_time", 5.0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"评测样本失败: {e}")
            return EvaluationResult(
                query=sample.get("query", ""),
                answer="",
                confidence=0.0,
                execution_time=0.0,
                success=False,
                error=str(e)
            )
    
    def _generate_report(self, results: List[EvaluationResult], total_time: float, 
                        start_metrics: Dict[str, Any], end_metrics: Dict[str, Any]) -> EvaluationReport:
        """生成性能评测报告"""
        successful_results = [r for r in results if r.success]
        
        # 计算平均准确率
        accuracies = [r.metadata.get("accuracy", 0.0) for r in successful_results if r.metadata]
        average_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
        
        # 计算平均执行时间
        execution_times = [r.execution_time for r in successful_results]
        average_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        # 计算性能指标
        performance_metrics = self.metrics_calculator.calculate_performance_metrics(results)
        
        return EvaluationReport(
            total_queries=len(results),
            successful_queries=len(successful_results),
            failed_queries=len(results) - len(successful_results),
            average_accuracy=average_accuracy,
            average_execution_time=average_execution_time,
            results=results,
            metadata={
                "evaluation_type": "performance",
                "dataset_info": self.dataset_loader.get_dataset_info(),
                "total_evaluation_time": total_time,
                "performance_metrics": performance_metrics,
                "system_metrics_start": start_metrics,
                "system_metrics_end": end_metrics
            }
        )
    
    def _create_empty_report(self) -> EvaluationReport:
        """创建空报告"""
        return EvaluationReport(
            total_queries=0,
            successful_queries=0,
            failed_queries=0,
            average_accuracy=0.0,
            average_execution_time=0.0,
            results=[]
        )
