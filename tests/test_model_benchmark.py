"""
模型基准测试服务测试
"""
import pytest
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.model_benchmark_service import (
    ModelBenchmarkService,
    BenchmarkMetric,
    TestCategory,
    TestPrompt,
    BenchmarkResult,
    ModelBenchmarkSummary
)


class TestModelBenchmarkService:
    """测试模型基准测试服务"""

    def setup_method(self):
        """每个测试前设置"""
        self.service = ModelBenchmarkService()

    def test_service_initialization(self):
        """测试服务初始化"""
        assert self.service is not None
        assert len(self.service.test_prompts) > 0

    def test_test_prompts_loaded(self):
        """测试测试提示词已加载"""
        prompts = self.service.test_prompts
        
        assert len(prompts) > 0
        categories = set(p.category for p in prompts)
        assert TestCategory.SIMPLE_QUERY in categories
        assert TestCategory.CODE_GENERATION in categories

    def test_get_test_prompts(self):
        """测试获取测试提示词"""
        prompts = self.service.get_test_prompts(
            categories=[TestCategory.SIMPLE_QUERY],
            num_prompts_per_category=2
        )
        
        assert len(prompts) > 0
        assert all(p.category == TestCategory.SIMPLE_QUERY for p in prompts)

    def test_evaluate_response_quality(self):
        """测试响应质量评估"""
        prompt = TestPrompt(
            category=TestCategory.SIMPLE_QUERY,
            prompt_id='test',
            prompt_text='What is AI?',
            expected_keywords=['artificial', 'intelligence']
        )
        
        response = "Artificial Intelligence is the simulation of human intelligence."
        score = self.service._evaluate_response_quality(response, prompt)
        
        assert 1.0 <= score <= 10.0

    def test_benchmark_result_creation(self):
        """测试基准结果创建"""
        result = BenchmarkResult(
            model_id='test_model',
            test_category=TestCategory.SIMPLE_QUERY,
            prompt_id='test_prompt',
            start_time=0.0,
            end_time=1.0,
            success=True,
            response_text='Test response',
            response_time_ms=1000.0
        )
        
        assert result.success is True
        assert result.response_time_ms == 1000.0

    def test_benchmark_summary_update(self):
        """测试基准摘要更新"""
        summary = ModelBenchmarkSummary(model_id='test_model')
        
        results = [
            BenchmarkResult(
                model_id='test_model',
                test_category=TestCategory.SIMPLE_QUERY,
                prompt_id='test1',
                start_time=0.0,
                end_time=1.0,
                success=True,
                response_time_ms=1000.0,
                total_tokens=100
            ),
            BenchmarkResult(
                model_id='test_model',
                test_category=TestCategory.SIMPLE_QUERY,
                prompt_id='test2',
                start_time=0.0,
                end_time=1.0,
                success=True,
                response_time_ms=2000.0,
                total_tokens=200
            )
        ]
        
        summary.update_from_results(results)
        
        assert summary.total_tests == 2
        assert summary.successful_tests == 2
        assert summary.avg_response_time_ms == 1500.0

    @pytest.mark.asyncio
    async def test_run_single_test(self):
        """测试运行单个测试"""
        prompt = TestPrompt(
            category=TestCategory.SIMPLE_QUERY,
            prompt_id='test',
            prompt_text='What is the capital of France?'
        )
        
        async def mock_caller(model_id, prompt):
            return "Paris is the capital of France."
        
        result = await self.service.run_single_test(
            model_id='test_model',
            test_prompt=prompt,
            llm_caller=mock_caller
        )
        
        assert result.success is True
        assert result.response_text is not None

    @pytest.mark.asyncio
    async def test_run_model_benchmark(self):
        """测试运行模型基准测试"""
        summaries = await self.service.run_model_benchmark(
            model_ids=['model_a', 'model_b'],
            test_config={'num_prompts_per_category': 1}
        )
        
        assert 'model_a' in summaries
        assert 'model_b' in summaries


class TestBenchmarkMetrics:
    """测试基准测试指标"""

    def test_benchmark_metric_enum(self):
        """测试基准测试指标枚举"""
        assert BenchmarkMetric.RESPONSE_TIME.value == 'response_time'
        assert BenchmarkMetric.SUCCESS_RATE.value == 'success_rate'
        assert BenchmarkMetric.COST_PER_REQUEST.value == 'cost_per_request'

    def test_test_category_enum(self):
        """测试测试类别枚举"""
        assert TestCategory.SIMPLE_QUERY.value == 'simple_query'
        assert TestCategory.CODE_GENERATION.value == 'code_generation'
        assert TestCategory.FACT_RETRIEVAL.value == 'fact_retrieval'

    def test_test_prompt_to_dict(self):
        """测试测试提示词转字典"""
        prompt = TestPrompt(
            category=TestCategory.SIMPLE_QUERY,
            prompt_id='test',
            prompt_text='Test prompt'
        )
        
        d = prompt.to_dict()
        assert d['category'] == TestCategory.SIMPLE_QUERY
        assert d['prompt_id'] == 'test'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
