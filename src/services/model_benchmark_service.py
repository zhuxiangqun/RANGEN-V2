#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型性能基准测试服务 - 多模型架构的性能评估和比较

提供全面的模型性能评估功能：
1. 标准化测试套件：针对不同模型运行相同的测试用例
2. 多维度评估：性能、成本、质量、可靠性
3. 自动化测试：支持定期自动运行和报告生成
4. 比较分析：生成模型间的对比报告
5. 趋势跟踪：跟踪模型性能随时间的变化

设计原则：
- 标准化：所有模型使用相同的测试方法和指标
- 可重复性：测试结果可重复，消除随机性影响
- 全面性：覆盖性能、成本、质量等多个维度
- 实用性：测试结果直接指导生产环境模型选择
- 自动化：最小化人工干预，支持持续集成
"""

import asyncio
import time
import json
import logging
import threading
import statistics
from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
import concurrent.futures

from .multi_model_config_service import (
    get_multi_model_config_service,
    ModelConfig,
    PerformanceBenchmarkConfig as ConfigPerformanceBenchmark
)
from .fault_tolerance_service import get_fault_tolerance_service

logger = logging.getLogger(__name__)


class BenchmarkMetric(str, Enum):
    """基准测试指标枚举"""
    RESPONSE_TIME = "response_time"          # 响应时间（毫秒）
    SUCCESS_RATE = "success_rate"            # 成功率（百分比）
    TOKEN_USAGE = "token_usage"              # Token使用量
    COST_PER_REQUEST = "cost_per_request"    # 每请求成本（美元）
    QUALITY_SCORE = "quality_score"          # 质量评分（1-10）
    THROUGHPUT = "throughput"                # 吞吐量（请求/秒）
    ERROR_RATE = "error_rate"                # 错误率（百分比）
    TIMEOUT_RATE = "timeout_rate"            # 超时率（百分比）


class TestCategory(str, Enum):
    """测试类别枚举"""
    SIMPLE_QUERY = "simple_query"            # 简单查询
    COMPLEX_REASONING = "complex_reasoning"  # 复杂推理
    CODE_GENERATION = "code_generation"      # 代码生成
    SUMMARIZATION = "summarization"          # 摘要生成
    TRANSLATION = "translation"              # 翻译任务
    CREATIVE_WRITING = "creative_writing"    # 创意写作
    FACT_RETRIEVAL = "fact_retrieval"        # 事实检索
    MULTI_TURN = "multi_turn"                # 多轮对话


@dataclass
class TestPrompt:
    """测试提示词"""
    category: TestCategory                   # 测试类别
    prompt_id: str                          # 提示词ID
    prompt_text: str                        # 提示词文本
    expected_length_min: int = 50           # 期望最小长度
    expected_length_max: int = 500          # 期望最大长度
    expected_keywords: List[str] = field(default_factory=list)  # 期望关键词
    difficulty: str = "medium"              # 难度级别（easy, medium, hard）
    language: str = "en"                    # 语言
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class BenchmarkResult:
    """单个测试结果"""
    model_id: str                          # 模型标识符
    test_category: TestCategory            # 测试类别
    prompt_id: str                         # 提示词ID
    start_time: float                      # 开始时间（Unix时间戳）
    end_time: float                        # 结束时间（Unix时间戳）
    success: bool                          # 是否成功
    response_text: Optional[str] = None    # 响应文本
    error_message: Optional[str] = None    # 错误信息
    response_time_ms: float = 0.0          # 响应时间（毫秒）
    input_tokens: int = 0                  # 输入token数
    output_tokens: int = 0                 # 输出token数
    total_tokens: int = 0                  # 总token数
    cost_usd: float = 0.0                  # 成本（美元）
    quality_score: float = 0.0             # 质量评分（1-10）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        # 转换枚举值为字符串
        result["test_category"] = self.test_category.value
        return result
    
    @property
    def latency_ms(self) -> float:
        """计算延迟（毫秒）"""
        return self.response_time_ms


@dataclass
class ModelBenchmarkSummary:
    """模型基准测试摘要"""
    model_id: str                          # 模型标识符
    total_tests: int = 0                   # 总测试数
    successful_tests: int = 0              # 成功测试数
    failed_tests: int = 0                  # 失败测试数
    avg_response_time_ms: float = 0.0      # 平均响应时间（毫秒）
    min_response_time_ms: float = 0.0      # 最小响应时间（毫秒）
    max_response_time_ms: float = 0.0      # 最大响应时间（毫秒）
    p95_response_time_ms: float = 0.0      # 95分位响应时间（毫秒）
    avg_token_usage: float = 0.0           # 平均token使用量
    avg_cost_per_request_usd: float = 0.0  # 平均每请求成本（美元）
    avg_quality_score: float = 0.0         # 平均质量评分
    success_rate: float = 0.0              # 成功率（百分比）
    total_cost_usd: float = 0.0            # 总成本（美元）
    metrics_by_category: Dict[str, Dict[str, float]] = field(default_factory=dict)  # 按类别指标
    recent_results: List[BenchmarkResult] = field(default_factory=list)  # 最近结果
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        # 转换recent_results
        result["recent_results"] = [r.to_dict() for r in self.recent_results]
        return result
    
    def update_from_results(self, results: List[BenchmarkResult]) -> None:
        """从结果列表更新摘要"""
        if not results:
            return
        
        self.total_tests = len(results)
        self.successful_tests = sum(1 for r in results if r.success)
        self.failed_tests = self.total_tests - self.successful_tests
        self.success_rate = self.successful_tests / self.total_tests if self.total_tests > 0 else 0.0
        
        # 响应时间统计
        successful_results = [r for r in results if r.success]
        if successful_results:
            response_times = [r.response_time_ms for r in successful_results]
            self.avg_response_time_ms = statistics.mean(response_times)
            self.min_response_time_ms = min(response_times)
            self.max_response_time_ms = max(response_times)
            
            # 计算百分位数
            if len(response_times) >= 5:
                sorted_times = sorted(response_times)
                p95_index = int(len(sorted_times) * 0.95)
                self.p95_response_time_ms = sorted_times[p95_index]
            else:
                self.p95_response_time_ms = self.avg_response_time_ms
        
        # Token使用统计
        if successful_results:
            token_usages = [r.total_tokens for r in successful_results]
            self.avg_token_usage = statistics.mean(token_usages)
        
        # 成本统计
        if successful_results:
            costs = [r.cost_usd for r in successful_results]
            self.avg_cost_per_request_usd = statistics.mean(costs)
            self.total_cost_usd = sum(costs)
        
        # 质量评分统计
        quality_scores = [r.quality_score for r in successful_results if r.quality_score > 0]
        if quality_scores:
            self.avg_quality_score = statistics.mean(quality_scores)
        
        # 按类别统计
        self.metrics_by_category = {}
        for category in TestCategory:
            category_results = [r for r in results if r.test_category == category]
            if category_results:
                cat_successful = [r for r in category_results if r.success]
                cat_total = len(category_results)
                cat_success_rate = len(cat_successful) / cat_total if cat_total > 0 else 0.0
                
                if cat_successful:
                    cat_response_times = [r.response_time_ms for r in cat_successful]
                    cat_avg_time = statistics.mean(cat_response_times)
                    cat_avg_tokens = statistics.mean([r.total_tokens for r in cat_successful])
                    cat_avg_cost = statistics.mean([r.cost_usd for r in cat_successful])
                    
                    self.metrics_by_category[category.value] = {
                        "total_tests": cat_total,
                        "success_rate": cat_success_rate,
                        "avg_response_time_ms": cat_avg_time,
                        "avg_token_usage": cat_avg_tokens,
                        "avg_cost_usd": cat_avg_cost
                    }
        
        # 保留最近结果（最多20个）
        self.recent_results = results[-20:] if len(results) > 20 else results.copy()


@dataclass
class ComparativeReport:
    """比较报告"""
    report_id: str                          # 报告ID
    timestamp: datetime                     # 报告时间
    test_config: Dict[str, Any]             # 测试配置
    model_summaries: Dict[str, ModelBenchmarkSummary]  # 模型摘要
    recommendations: List[str]              # 推荐建议
    winner_model: Optional[str] = None      # 优胜模型
    winner_reasons: List[str] = field(default_factory=list)  # 优胜原因
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        result["model_summaries"] = {mid: summary.to_dict() 
                                   for mid, summary in self.model_summaries.items()}
        return result
    
    def save_to_file(self, file_path: str) -> bool:
        """保存到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"比较报告已保存到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存比较报告失败: {e}")
            return False


class ModelBenchmarkService:
    """模型性能基准测试服务"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化基准测试服务
        
        Args:
            config_file: 配置文件路径（可选）
        """
        self.logger = logging.getLogger(__name__)
        
        # 配置服务
        self.config_service = get_multi_model_config_service()
        self.fault_tolerance_service = get_fault_tolerance_service()
        
        # 测试提示词库
        self.test_prompts = self._load_test_prompts()
        
        # 结果存储
        self.results: Dict[str, List[BenchmarkResult]] = {}  # model_id -> 结果列表
        self.summaries: Dict[str, ModelBenchmarkSummary] = {}  # model_id -> 摘要
        self.comparative_reports: List[ComparativeReport] = []  # 比较报告列表
        
        # 数据目录
        self.data_dir = Path("data/model_benchmarks")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试配置
        self.default_test_config = {
            "num_prompts_per_category": 3,
            "max_concurrent_tests": 5,
            "timeout_per_request": 60.0,
            "include_categories": [cat.value for cat in TestCategory],
            "quality_evaluation_enabled": True,
            "cost_tracking_enabled": True
        }
        
        # 加载历史数据
        self._load_historical_data()
        
        self.logger.info("模型性能基准测试服务初始化完成")
    
    def _load_test_prompts(self) -> List[TestPrompt]:
        """加载测试提示词库"""
        prompts = [
            # 简单查询
            TestPrompt(
                category=TestCategory.SIMPLE_QUERY,
                prompt_id="simple_weather",
                prompt_text="What is the weather like today?",
                difficulty="easy",
                expected_keywords=["weather", "today", "temperature"]
            ),
            TestPrompt(
                category=TestCategory.SIMPLE_QUERY,
                prompt_id="simple_capital",
                prompt_text="What is the capital of France?",
                difficulty="easy",
                expected_keywords=["Paris", "France", "capital"]
            ),
            
            # 复杂推理
            TestPrompt(
                category=TestCategory.COMPLEX_REASONING,
                prompt_id="reasoning_math",
                prompt_text="If a train leaves Station A at 60 mph and another train leaves Station B at 80 mph, and they are 200 miles apart, how long until they meet?",
                difficulty="hard",
                expected_keywords=["hours", "distance", "speed", "meet"]
            ),
            TestPrompt(
                category=TestCategory.COMPLEX_REASONING,
                prompt_id="reasoning_logic",
                prompt_text="All men are mortal. Socrates is a man. Therefore, Socrates is mortal. Is this a valid logical argument?",
                difficulty="medium",
                expected_keywords=["valid", "logical", "syllogism", "mortal"]
            ),
            
            # 代码生成
            TestPrompt(
                category=TestCategory.CODE_GENERATION,
                prompt_id="code_fibonacci",
                prompt_text="Write a Python function to calculate the nth Fibonacci number.",
                difficulty="medium",
                expected_keywords=["def", "fibonacci", "return", "recursive"]
            ),
            TestPrompt(
                category=TestCategory.CODE_GENERATION,
                prompt_id="code_factorial",
                prompt_text="Write a JavaScript function to calculate factorial of a number.",
                difficulty="easy",
                expected_keywords=["function", "factorial", "return", "recursive"]
            ),
            
            # 摘要生成
            TestPrompt(
                category=TestCategory.SUMMARIZATION,
                prompt_id="summary_article",
                prompt_text="Summarize the following article: Artificial intelligence is transforming industries worldwide. Machine learning algorithms can now diagnose diseases, predict market trends, and even create art. However, ethical concerns about AI bias and job displacement remain important considerations.",
                difficulty="medium",
                expected_keywords=["AI", "transforming", "industries", "ethical", "concerns"]
            ),
            
            # 翻译任务
            TestPrompt(
                category=TestCategory.TRANSLATION,
                prompt_id="translation_chinese",
                prompt_text="Translate 'Hello, how are you?' to Chinese.",
                difficulty="easy",
                language="en",
                expected_keywords=["你好", "吗", "怎么样"]
            ),
            
            # 创意写作
            TestPrompt(
                category=TestCategory.CREATIVE_WRITING,
                prompt_id="creative_story",
                prompt_text="Write a short story about a robot who learns to paint.",
                difficulty="medium",
                expected_keywords=["robot", "paint", "learns", "story"]
            ),
            
            # 事实检索
            TestPrompt(
                category=TestCategory.FACT_RETRIEVAL,
                prompt_id="fact_einstein",
                prompt_text="When was Albert Einstein born and what is he most famous for?",
                difficulty="medium",
                expected_keywords=["March 14", "1879", "theory of relativity", "Nobel Prize"]
            ),
            
            # 多轮对话
            TestPrompt(
                category=TestCategory.MULTI_TURN,
                prompt_id="multi_turn_planning",
                prompt_text="Let's plan a trip to Japan. First, what are the must-visit cities?",
                difficulty="hard",
                expected_keywords=["Tokyo", "Kyoto", "Osaka", "itinerary"]
            ),
        ]
        
        self.logger.info(f"加载了 {len(prompts)} 个测试提示词")
        return prompts
    
    def _load_historical_data(self) -> None:
        """加载历史测试数据"""
        history_file = self.data_dir / "benchmark_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 加载结果
                if "results" in data:
                    for model_id, result_list in data["results"].items():
                        self.results[model_id] = []
                        for result_dict in result_list:
                            # 转换字典为BenchmarkResult对象
                            result = BenchmarkResult(**result_dict)
                            self.results[model_id].append(result)
                
                # 加载摘要
                if "summaries" in data:
                    for model_id, summary_dict in data["summaries"].items():
                        summary = ModelBenchmarkSummary(**summary_dict)
                        self.summaries[model_id] = summary
                
                # 加载报告
                if "reports" in data:
                    for report_dict in data["reports"]:
                        # 需要特殊处理timestamp字段
                        if "timestamp" in report_dict:
                            report_dict["timestamp"] = datetime.fromisoformat(report_dict["timestamp"])
                        
                        # 处理model_summaries字段
                        if "model_summaries" in report_dict:
                            model_summaries = {}
                            for mid, summary_dict in report_dict["model_summaries"].items():
                                summary = ModelBenchmarkSummary(**summary_dict)
                                model_summaries[mid] = summary
                            report_dict["model_summaries"] = model_summaries
                        
                        report = ComparativeReport(**report_dict)
                        self.comparative_reports.append(report)
                
                self.logger.info(f"加载了历史数据: {len(self.results)} 个模型, {len(self.comparative_reports)} 个报告")
            except Exception as e:
                self.logger.error(f"加载历史数据失败: {e}")
    
    def _save_historical_data(self) -> None:
        """保存历史测试数据"""
        try:
            data = {
                "results": {},
                "summaries": {},
                "reports": []
            }
            
            # 保存结果
            for model_id, result_list in self.results.items():
                data["results"][model_id] = [r.to_dict() for r in result_list]
            
            # 保存摘要
            for model_id, summary in self.summaries.items():
                data["summaries"][model_id] = summary.to_dict()
            
            # 保存报告
            for report in self.comparative_reports:
                data["reports"].append(report.to_dict())
            
            history_file = self.data_dir / "benchmark_history.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"历史数据已保存到: {history_file}")
        except Exception as e:
            self.logger.error(f"保存历史数据失败: {e}")
    
    def get_test_prompts(
        self, 
        categories: Optional[List[TestCategory]] = None,
        num_prompts_per_category: int = 3,
        difficulty: Optional[str] = None
    ) -> List[TestPrompt]:
        """
        获取测试提示词
        
        Args:
            categories: 测试类别列表（默认全部）
            num_prompts_per_category: 每个类别的提示词数量
            difficulty: 难度级别（可选）
            
        Returns:
            List[TestPrompt]: 测试提示词列表
        """
        if categories is None:
            categories = list(TestCategory)
        
        selected_prompts = []
        
        for category in categories:
            # 筛选该类别的提示词
            category_prompts = [p for p in self.test_prompts if p.category == category]
            
            # 按难度筛选
            if difficulty:
                category_prompts = [p for p in category_prompts if p.difficulty == difficulty]
            
            # 随机选择指定数量的提示词
            import random
            if len(category_prompts) > num_prompts_per_category:
                selected = random.sample(category_prompts, num_prompts_per_category)
            else:
                selected = category_prompts
            
            selected_prompts.extend(selected)
        
        self.logger.info(f"选择了 {len(selected_prompts)} 个测试提示词")
        return selected_prompts
    
    async def run_single_test(
        self,
        model_id: str,
        test_prompt: TestPrompt,
        llm_caller: callable,
        timeout: float = 60.0
    ) -> BenchmarkResult:
        """
        运行单个测试
        
        Args:
            model_id: 模型标识符
            test_prompt: 测试提示词
            llm_caller: LLM调用函数（接受model_id和prompt，返回响应）
            timeout: 超时时间（秒）
            
        Returns:
            BenchmarkResult: 测试结果
        """
        start_time = time.time()
        result = BenchmarkResult(
            model_id=model_id,
            test_category=test_prompt.category,
            prompt_id=test_prompt.prompt_id,
            start_time=start_time,
            end_time=start_time,
            success=False
        )
        
        try:
            # 使用asyncio等待超时
            response = await asyncio.wait_for(
                llm_caller(model_id, test_prompt.prompt_text),
                timeout=timeout
            )
            
            end_time = time.time()
            result.end_time = end_time
            result.response_time_ms = (end_time - start_time) * 1000
            
            if response and isinstance(response, str):
                result.success = True
                result.response_text = response
                
                # 计算token使用量（简化估算）
                # 在实际系统中，这里应该使用实际的token计数
                result.input_tokens = len(test_prompt.prompt_text) // 4  # 近似估算
                result.output_tokens = len(response) // 4  # 近似估算
                result.total_tokens = result.input_tokens + result.output_tokens
                
                # 计算成本（基于模型配置）
                model_config = self.config_service.get_model_config(model_id)
                if model_config:
                    cost_per_token = getattr(model_config, 'cost_per_token', 0.0)
                    result.cost_usd = result.total_tokens * cost_per_token
                
                # 评估质量
                result.quality_score = self._evaluate_response_quality(
                    response, test_prompt
                )
                
                self.logger.info(f"测试成功: {model_id} - {test_prompt.prompt_id} "
                               f"({result.response_time_ms:.0f}ms)")
            else:
                result.error_message = "Empty or invalid response"
                self.logger.warning(f"测试失败（空响应）: {model_id} - {test_prompt.prompt_id}")
        
        except asyncio.TimeoutError:
            result.error_message = f"Timeout after {timeout} seconds"
            self.logger.warning(f"测试超时: {model_id} - {test_prompt.prompt_id}")
        
        except Exception as e:
            result.error_message = str(e)
            self.logger.error(f"测试异常: {model_id} - {test_prompt.prompt_id}: {e}")
        
        finally:
            # 确保结束时间已设置
            if result.end_time == start_time:
                result.end_time = time.time()
                result.response_time_ms = (result.end_time - start_time) * 1000
        
        return result
    
    def _evaluate_response_quality(
        self, 
        response: str, 
        test_prompt: TestPrompt
    ) -> float:
        """
        评估响应质量
        
        Args:
            response: 响应文本
            test_prompt: 测试提示词
            
        Returns:
            float: 质量评分（1-10）
        """
        # 基础评分
        score = 5.0  # 基础分
        
        # 1. 长度检查
        response_length = len(response)
        if test_prompt.expected_length_min <= response_length <= test_prompt.expected_length_max:
            score += 1.0
        elif response_length < test_prompt.expected_length_min:
            score -= 1.0
        elif response_length > test_prompt.expected_length_max:
            score -= 0.5
        
        # 2. 关键词检查
        if test_prompt.expected_keywords:
            found_keywords = 0
            for keyword in test_prompt.expected_keywords:
                if keyword.lower() in response.lower():
                    found_keywords += 1
            
            keyword_ratio = found_keywords / len(test_prompt.expected_keywords)
            score += keyword_ratio * 2.0  # 最多加2分
        
        # 3. 语法和可读性检查（简化）
        # 在实际系统中，这里可以使用更复杂的NLP技术
        import re
        sentences = re.split(r'[.!?]+', response)
        if len(sentences) >= 2:  # 至少有两个句子
            score += 1.0
        
        # 4. 相关性检查（简化）
        # 检查响应是否包含提示词中的关键词
        prompt_words = set(test_prompt.prompt_text.lower().split())
        response_words = set(response.lower().split())
        common_words = prompt_words.intersection(response_words)
        if len(common_words) >= 2:
            score += 1.0
        
        # 确保评分在1-10范围内
        score = max(1.0, min(10.0, score))
        
        return round(score, 1)
    
    async def run_model_benchmark(
        self,
        model_ids: List[str],
        test_config: Optional[Dict[str, Any]] = None,
        llm_caller: Optional[callable] = None,
        save_results: bool = True
    ) -> Dict[str, ModelBenchmarkSummary]:
        """
        运行模型基准测试
        
        Args:
            model_ids: 模型ID列表
            test_config: 测试配置（可选）
            llm_caller: LLM调用函数（可选，默认使用模拟函数）
            save_results: 是否保存结果
            
        Returns:
            Dict[str, ModelBenchmarkSummary]: 模型摘要字典
        """
        if test_config is None:
            test_config = self.default_test_config.copy()
        
        # 使用模拟调用函数（如果没有提供）
        if llm_caller is None:
            llm_caller = self._mock_llm_caller
        
        # 获取测试提示词
        categories = [
            TestCategory(cat) for cat in test_config.get("include_categories", [])
        ]
        num_prompts = test_config.get("num_prompts_per_category", 3)
        
        test_prompts = self.get_test_prompts(
            categories=categories,
            num_prompts_per_category=num_prompts
        )
        
        self.logger.info(f"开始基准测试: {len(model_ids)} 个模型, {len(test_prompts)} 个提示词")
        
        results_by_model = {model_id: [] for model_id in model_ids}
        
        # 并发测试
        max_concurrent = test_config.get("max_concurrent_tests", 5)
        timeout = test_config.get("timeout_per_request", 60.0)
        
        # 为每个模型运行测试
        for model_id in model_ids:
            self.logger.info(f"测试模型: {model_id}")
            
            # 创建测试任务
            tasks = []
            for test_prompt in test_prompts:
                task = self.run_single_test(
                    model_id=model_id,
                    test_prompt=test_prompt,
                    llm_caller=llm_caller,
                    timeout=timeout
                )
                tasks.append(task)
            
            # 分批执行任务（控制并发度）
            batch_size = max_concurrent
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                
                # 处理结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        self.logger.error(f"测试任务异常: {result}")
                    elif isinstance(result, BenchmarkResult):
                        results_by_model[model_id].append(result)
            
            self.logger.info(f"模型 {model_id} 测试完成: {len(results_by_model[model_id])} 个结果")
        
        # 更新摘要
        summaries = {}
        for model_id, results in results_by_model.items():
            # 保存结果
            if model_id not in self.results:
                self.results[model_id] = []
            self.results[model_id].extend(results)
            
            # 更新摘要
            if model_id not in self.summaries:
                self.summaries[model_id] = ModelBenchmarkSummary(model_id=model_id)
            
            self.summaries[model_id].update_from_results(self.results[model_id])
            summaries[model_id] = self.summaries[model_id]
        
        # 生成比较报告
        if len(model_ids) > 1:
            report = self._generate_comparative_report(model_ids, test_config)
            self.comparative_reports.append(report)
            
            # 保存报告
            report_file = self.data_dir / f"report_{report.report_id}.json"
            report.save_to_file(str(report_file))
        
        # 保存历史数据
        if save_results:
            self._save_historical_data()
        
        self.logger.info("基准测试完成")
        return summaries
    
    def _mock_llm_caller(self, model_id: str, prompt: str) -> str:
        """
        模拟LLM调用函数（用于测试）
        
        Args:
            model_id: 模型ID
            prompt: 提示词
            
        Returns:
            str: 模拟响应
        """
        # 模拟延迟（基于模型类型）
        if "deepseek" in model_id:
            time.sleep(0.5)  # 500ms
        elif "stepflash" in model_id:
            time.sleep(0.3)  # 300ms
        elif "local" in model_id:
            time.sleep(1.0)  # 1000ms
        else:
            time.sleep(0.2)  # 200ms
        
        # 生成模拟响应
        responses = {
            "simple_query": f"This is a simulated response from {model_id} to your query: '{prompt[:50]}...'",
            "complex_reasoning": f"After careful analysis, the answer is 42. This response is from {model_id}.",
            "code_generation": f"```python\ndef solution():\n    return 'Hello from {model_id}'\n```",
            "summarization": f"In summary, this is a simulated summary from {model_id}.",
            "translation": f"Translated text from {model_id}.",
            "creative_writing": f"Once upon a time, {model_id} wrote a story...",
            "fact_retrieval": f"The fact is: {model_id} knows the answer.",
            "multi_turn": f"{model_id}: Let's continue the conversation."
        }
        
        # 根据提示词类型返回不同的响应
        prompt_lower = prompt.lower()
        for key, response in responses.items():
            if key in prompt_lower:
                return response
        
        # 默认响应
        return f"This is a default response from {model_id} for: {prompt[:100]}..."
    
    def _generate_comparative_report(
        self,
        model_ids: List[str],
        test_config: Dict) -> Dict[str, Any]:
        """
        生成对比报告
        
        Args:
            model_ids: 模型ID列表
            test_config: 测试配置
            
        Returns:
            对比报告字典
        """
        from typing import Dict, Any, List
        import json
        
        # 简单实现：返回一个模拟报告
        return {
            "summary": f"Comparative report for {len(model_ids)} models",
            "models_tested": model_ids,
            "test_config": test_config,
            "results": {
                "accuracy": {"best": model_ids[0] if model_ids else "N/A", "scores": {}},
                "speed": {"best": model_ids[0] if model_ids else "N/A", "scores": {}},
                "cost": {"best": model_ids[0] if model_ids else "N/A", "scores": {}},
            },
            "recommendations": ["Use the first model for production"],
            "generated_at": "2024-01-01T00:00:00Z"
        }