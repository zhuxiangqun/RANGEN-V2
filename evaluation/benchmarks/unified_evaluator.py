#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一评测器

提供通用的评测功能，支持多种评测场景。
"""

import asyncio
import time
import logging
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

class UnifiedDatasetLoader(DatasetInterface):
    """统一数据集加载器"""
    
    def __init__(self, data_path: str = None, dataset_type: str = "unified"):
        self.data_path = data_path
        self.dataset_type = dataset_type
        self.logger = logging.getLogger(__name__)
    
    def load_samples(self, count: int = None) -> List[Dict[str, Any]]:
        """加载数据集样本"""
        try:
            if not self.data_path or not os.path.exists(self.data_path):
                # 生成测试样本
                return self._generate_test_samples(count or 10)
            
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("数据集格式错误：应为列表格式")
            
            # 限制样本数量
            if count and count < len(data):
                data = data[:count]
            
            self.logger.info(f"成功加载 {len(data)} 个{self.dataset_type}样本")
            return data
            
        except Exception as e:
            self.logger.error(f"加载数据集失败: {e}")
            return self._generate_test_samples(count or 10)
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """获取数据集信息"""
        try:
            if self.data_path and os.path.exists(self.data_path):
                file_size = os.path.getsize(self.data_path)
                return {
                    "name": f"{self.dataset_type.title()} Dataset",
                    "path": self.data_path,
                    "file_size": file_size,
                    "file_size_mb": file_size / (1024 * 1024)
                }
        except Exception as e:
            self.logger.error(f"获取数据集信息失败: {e}")
        
        return {"name": f"{self.dataset_type.title()} Dataset", "path": self.data_path}
    
    def _generate_test_samples(self, count: int) -> List[Dict[str, Any]]:
        """生成测试样本"""
        test_samples = [
            {
                "query": "What is the capital of France?",
                "expected_answer": "Paris",
                "category": "geography"
            },
            {
                "query": "Who wrote 'Romeo and Juliet'?",
                "expected_answer": "William Shakespeare",
                "category": "literature"
            },
            {
                "query": "What is 2 + 2?",
                "expected_answer": "4",
                "category": "mathematics"
            },
            {
                "query": "What is the largest planet in our solar system?",
                "expected_answer": "Jupiter",
                "category": "astronomy"
            },
            {
                "query": "When was the Declaration of Independence signed?",
                "expected_answer": "1776",
                "category": "history"
            }
        ]
        
        # 重复样本以达到指定数量
        samples = []
        for i in range(count):
            sample = test_samples[i % len(test_samples)].copy()
            sample["query"] = f"{sample['query']} (Test {i+1})"
            samples.append(sample)
        
        return samples

class UnifiedMetricsCalculator(MetricsInterface):
    """统一评测指标计算器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_accuracy(self, result: EvaluationResult, expected: str) -> float:
        """计算准确率"""
        try:
            if not result.success or not result.answer:
                return 0.0
            
            # 简单的字符串相似度计算
            actual = result.answer.lower().strip()
            expected = expected.lower().strip()
            
            if actual == expected:
                return 1.0
            
            # 计算编辑距离相似度
            similarity = self._calculate_similarity(actual, expected)
            return similarity
            
        except Exception as e:
            self.logger.error(f"计算准确率失败: {e}")
            return 0.0
    
    def calculate_quality_score(self, result: EvaluationResult) -> float:
        """计算质量分数"""
        try:
            if not result.success:
                return 0.0
            
            # 基于置信度和执行时间的质量分数
            confidence_score = result.confidence
            time_score = max(0, 1 - result.execution_time / 30.0)  # 30秒为满分
            
            quality_score = (confidence_score * 0.7 + time_score * 0.3)
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
            
            return {
                "total_queries": len(results),
                "successful_queries": len(successful_results),
                "success_rate": len(successful_results) / len(results) if results else 0.0,
                "average_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0.0,
                "min_execution_time": min(execution_times) if execution_times else 0.0,
                "max_execution_time": max(execution_times) if execution_times else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"计算性能指标失败: {e}")
            return {}
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度"""
        if not s1 or not s2:
            return 0.0
        
        # 简单的Jaccard相似度
        set1 = set(s1.split())
        set2 = set(s2.split())
        
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

class UnifiedEvaluator:
    """统一评测器"""
    
    def __init__(self, 
                 research_system: ResearchSystemInterface,
                 dataset_loader: DatasetInterface = None,
                 metrics_calculator: MetricsInterface = None,
                 timeout: float = 30.0,
                 max_concurrent: int = 3):
        
        self.research_system = research_system
        self.dataset_loader = dataset_loader or UnifiedDatasetLoader()
        self.metrics_calculator = metrics_calculator or UnifiedMetricsCalculator()
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(__name__)
    
    async def evaluate(self, sample_count: int = None) -> EvaluationReport:
        """执行统一评测"""
        self.logger.info("开始统一评测")
        
        # 加载数据集
        samples = self.dataset_loader.load_samples(sample_count)
        if not samples:
            self.logger.error("无法加载数据集")
            return self._create_empty_report()
        
        # 执行评测
        results = []
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def evaluate_sample(sample: Dict[str, Any]) -> EvaluationResult:
            async with semaphore:
                return await self._evaluate_single_sample(sample)
        
        # 并发执行评测
        tasks = [evaluate_sample(sample) for sample in samples]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
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
        report = self._generate_report(processed_results)
        self.logger.info(f"统一评测完成: {report.successful_queries}/{report.total_queries} 成功")
        
        return report
    
    async def _evaluate_single_sample(self, sample: Dict[str, Any]) -> EvaluationResult:
        """评测单个样本"""
        try:
            query = sample.get("query", "")
            expected_answer = sample.get("expected_answer", "")
            
            # 创建评测请求
            request = EvaluationRequest(
                query=query,
                context={
                    "dataset": "unified",
                    "expected_answer": expected_answer,
                    "category": sample.get("category", "general")
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
                    "category": sample.get("category", "general")
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
    
    def _generate_report(self, results: List[EvaluationResult]) -> EvaluationReport:
        """生成评测报告"""
        successful_results = [r for r in results if r.success]
        
        # 计算平均准确率
        accuracies = [r.metadata.get("accuracy", 0.0) for r in successful_results if r.metadata]
        average_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
        
        # 计算平均执行时间
        execution_times = [r.execution_time for r in successful_results]
        average_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        return EvaluationReport(
            total_queries=len(results),
            successful_queries=len(successful_results),
            failed_queries=len(results) - len(successful_results),
            average_accuracy=average_accuracy,
            average_execution_time=average_execution_time,
            results=results,
            metadata={
                "evaluation_type": "unified",
                "dataset_info": self.dataset_loader.get_dataset_info()
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
