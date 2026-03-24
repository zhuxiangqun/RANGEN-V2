"""
AI中台真实能力测试评估器

通过调用真实的 DeepSeek API 来测试 AI中台的各项能力
"""

import asyncio
import time
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# 加载 .env 文件中的环境变量
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

try:
    import openai
except ImportError:
    openai = None

from .base import EVALUATION_CONFIG
from .evaluators.v2_evaluators import (
    BaseEvaluator, 
    DimensionResult, 
    SubItemResult,
    EvaluatorStatus
)


class RealAPITestEvaluator:
    """真实API测试评估器基类"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = {**EVALUATION_CONFIG, **(config or {})}
        self.source_path = self.config.get("source_path", "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/src")
        self.max_sample_count = self.config.get("max_sample_count", 50)
        self.max_concurrent = self.config.get("max_concurrent", 4)
        
        # DeepSeek API 配置
        self.api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.api_base = "https://api.deepseek.com"
        self.model = "deepseek-chat"
        
        # 初始化客户端
        self.client = None
        if openai and self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.api_base)
    
    def _get_client(self):
        """获取或创建 API 客户端"""
        if self.client:
            return self.client
        if openai:
            api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.client = openai.OpenAI(api_key=api_key, base_url=self.api_base)
                return self.client
        return None
    
    async def _call_api(self, messages: List[Dict], timeout: int = 60) -> Dict[str, Any]:
        """调用 DeepSeek API"""
        client = self._get_client()
        
        if not client:
            return {
                "success": False,
                "error": "API client not initialized. Set DEEPSEEK_API_KEY environment variable.",
                "response": None,
                "latency": 0
            }
        
        start_time = time.time()
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    timeout=timeout,
                    temperature=0.7
                )
            )
            latency = time.time() - start_time
            
            return {
                "success": True,
                "error": None,
                "response": response.choices[0].message.content,
                "latency": latency,
                "usage": response.usage.dict() if response.usage else {}
            }
        except Exception as e:
            latency = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "response": None,
                "latency": latency
            }
    
    async def _evaluate_single_test(self, test_case: Dict) -> Dict[str, Any]:
        """评估单个测试用例"""
        test_id = test_case.get("id", "unknown")
        dimension = test_case.get("dimension", "unknown")
        input_text = test_case.get("input", "")
        expected_behavior = test_case.get("expected_behavior", "")
        evaluation_criteria = test_case.get("evaluation_criteria", [])
        difficulty = test_case.get("difficulty", "medium")
        
        # 准备消息
        if "turns" in test_case:
            messages = test_case["turns"]
        else:
            messages = [{"role": "user", "content": input_text}]
        
        # 调用 API
        result = await self._call_api(messages)
        
        # 评估响应质量
        score = self._evaluate_response(result, test_case)
        
        return {
            "test_id": test_id,
            "dimension": dimension,
            "difficulty": difficulty,
            "input": input_text,
            "response": result.get("response"),
            "success": result.get("success", False),
            "latency": result.get("latency", 0),
            "score": score,
            "evaluation_criteria": evaluation_criteria,
            "error": result.get("error")
        }
    
    def _evaluate_response(self, api_result: Dict, test_case: Dict) -> float:
        """评估 API 响应质量
        
        评分策略：
        1. 响应成功性 (20%): API调用是否成功
        2. 响应质量 (30%): 响应长度、结构、完整性
        3. 关键词匹配 (40%): 是否包含预期的关键概念
        4. 难度调整 (10%): 根据难度调整最终分数
        """
        if not api_result.get("success"):
            return 0.0
        
        response = api_result.get("response", "")
        evaluation_criteria = test_case.get("evaluation_criteria", [])
        difficulty = test_case.get("difficulty", "medium")
        
        if not response:
            return 0.0
        
        score = 0.0
        
        # 1. 响应存在且非空 (20%)
        if len(response) > 10:
            score += 0.15
        if len(response) > 50:
            score += 0.05
        
        # 2. 响应质量评分 (30%)
        # 检查响应结构（段落、列表等）
        has_structure = any(marker in response for marker in ['\n', '：', ':', '•', '-', '*', '1.', '2.', '3.'])
        if has_structure:
            score += 0.10
        
        # 检查响应是否完整（有一定长度）
        if len(response) > 100:
            score += 0.10
        elif len(response) > 50:
            score += 0.05
        
        # 检查是否有实质性内容（非纯模板回复）
        substantive_markers = ['。', '，', '.', ',', '是', '可以', '会', '需要', '应该']
        substantive_count = sum(1 for m in substantive_markers if m in response)
        if substantive_count >= 3:
            score += 0.10
        
        # 3. 关键词匹配评分 (40%)
        response_lower = response.lower()
        if evaluation_criteria:
            criteria_count = sum(1 for criterion in evaluation_criteria 
                                if criterion.lower() in response_lower)
            criteria_score = (criteria_count / len(evaluation_criteria)) * 0.40
            score += criteria_score
        else:
            # 如果没有明确的评价标准，只要响应合理就给分
            score += 0.20
        
        # 4. 难度调整 (基于原始分数的调整)
        # 难度越高，期望分数越低（因为任务更难）
        difficulty_bonus = {
            "easy": 0.10,      # 简单任务：奖励10%
            "medium": 0.0,     # 中等难度：正常评分
            "hard": -0.10      # 困难任务：降低10%期望
        }
        
        adjustment = difficulty_bonus.get(difficulty, 0.0)
        score = score * (1.0 + adjustment)
        
        return min(max(score, 0.0), 1.0)
    
    async def evaluate_dimension(self, dimension: str, tests: List[Dict]) -> DimensionResult:
        """评估单个维度"""
        results = []
        
        # 限制测试数量
        tests = tests[:self.max_sample_count]
        
        # 并发执行测试
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def run_with_limit(test):
            async with semaphore:
                return await self._evaluate_single_test(test)
        
        tasks = [run_with_limit(test) for test in tests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        valid_results = [r for r in results if isinstance(r, dict)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        # 计算平均分
        scores = [r.get("score", 0) for r in valid_results]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # 计算延迟
        latencies = [r.get("latency", 0) for r in valid_results if r.get("success")]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # 生成子项结果
        subitems = []
        for r in valid_results:
            status = "good" if r.get("score", 0) >= 0.7 else "fair" if r.get("score", 0) >= 0.5 else "poor"
            subitems.append(SubItemResult(
                name=r.get("test_id", "unknown"),
                description=r.get("input", "")[:100],
                score=r.get("score", 0),
                status=status,
                evidence=[
                    f"延迟: {r.get('latency', 0):.2f}s",
                    f"成功: {r.get('success', False)}"
                ] if r.get("success") else [f"错误: {r.get('error', 'unknown')}"]
            ))
        
        return DimensionResult(
            dimension=dimension,
            name=self._get_dimension_name(dimension),
            category=self._get_dimension_category(dimension),
            weight=self._get_dimension_weight(dimension),
            score=avg_score,
            status=self._status_by_score(avg_score),
            subitems=subitems,
            details=f"测试 {len(valid_results)} 个样本，成功 {sum(1 for r in valid_results if r.get('success'))} 个，平均延迟 {avg_latency:.2f}s"
        )
    
    def _get_dimension_name(self, dimension: str) -> str:
        names = {
            "orchestration": "编排能力",
            "agent_completeness": "Agent完备性",
            "prompt_engineering": "提示词工程",
            "context_engineering": "上下文工程",
            "response_quality": "回答质量",
            "routing": "路由准确率",
            "reasoning": "推理深度",
            "knowledge_recall": "知识召回",
            "tool_calling": "工具调用",
            "multi_turn": "多轮对话",
            "self_learning": "自学习能力",
        }
        return names.get(dimension, dimension)
    
    def _get_dimension_category(self, dimension: str) -> str:
        if dimension in ["orchestration", "agent_completeness", "prompt_engineering", "context_engineering"]:
            return "A"
        elif dimension in ["response_quality", "routing", "reasoning", "knowledge_recall", "tool_calling", "multi_turn", "self_learning"]:
            return "B"
        return "B"
    
    def _get_dimension_weight(self, dimension: str) -> float:
        weights = {
            "orchestration": 0.06,
            "agent_completeness": 0.06,
            "prompt_engineering": 0.06,
            "context_engineering": 0.07,
            "response_quality": 0.18,
            "routing": 0.15,
            "reasoning": 0.17,
            "knowledge_recall": 0.12,
            "tool_calling": 0.10,
            "multi_turn": 0.07,
            "self_learning": 0.06,
        }
        return weights.get(dimension, 0.09)
    
    def _status_by_score(self, score: float) -> str:
        if score >= 0.9:
            return "excellent"
        elif score >= 0.7:
            return "good"
        elif score >= 0.5:
            return "fair"
        else:
            return "poor"


class RealCapabilityEvaluator:
    """真实能力综合评估器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.max_sample_count = self.config.get("max_sample_count", 50)
        self.max_concurrent = self.config.get("max_concurrent", 4)
        self.evaluator = RealAPITestEvaluator(config)
        self.quick_mode = self.config.get("quick_mode", False)
        
        from .test_data.intelligence_tests import ALL_TESTS
        self.all_tests = ALL_TESTS
    
    async def run_full_evaluation_v2(self) -> Dict[str, Any]:
        print("=" * 60)
        print(f"🤖 AI中台智能能力评估 ({len(self.all_tests)}维度)")
        print(f"样本数: {self.max_sample_count}, 并发数: {self.max_concurrent}")
        if self.quick_mode:
            print("⚡ 快速模式: 仅测试前 4 个维度")
        print("=" * 60)
        
        if not self.evaluator._get_client():
            print("⚠️ 警告: 未设置 DEEPSEEK_API_KEY 环境变量")
            print("   将使用模拟数据进行评估（仅用于演示）")
        
        results = {}
        category_scores = {cat: {"score": 0, "weight": 0, "count": 0} for cat in "ABCDE"}
        overall_score = 0.0
        total_weight = 0.0
        
        dimensions_to_test = list(self.all_tests.items())
        if self.quick_mode:
            dimensions_to_test = dimensions_to_test[:4]
        
        async def evaluate_dim(dimension, tests):
            print(f"\n评估维度: {dimension} ({len(tests)} 个测试)")
            try:
                result = await self.evaluator.evaluate_dimension(dimension, tests)
                status_icon = {
                    "excellent": "✅",
                    "good": "👍",
                    "fair": "⚠️",
                    "poor": "❌"
                }.get(result.status, "❓")
                print(f"  {status_icon} {result.score:.1%}")
                return dimension, result, None
            except Exception as e:
                print(f"  ❌ {dimension} 评估失败: {e}")
                return dimension, None, e
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def bounded_evaluate(dimension, tests):
            async with semaphore:
                return await evaluate_dim(dimension, tests)
        
        tasks = [bounded_evaluate(d, t) for d, t in dimensions_to_test]
        eval_results = await asyncio.gather(*tasks)
        
        for dimension, result, error in eval_results:
            if error:
                results[dimension] = DimensionResult(
                    dimension=dimension,
                    name=self.evaluator._get_dimension_name(dimension),
                    category=self.evaluator._get_dimension_category(dimension),
                    weight=self.evaluator._get_dimension_weight(dimension),
                    score=0.0,
                    status="failed",
                    details=str(error)
                )
            else:
                results[dimension] = result
                category = result.category
                category_scores[category]["score"] += result.score * result.weight
                category_scores[category]["weight"] += result.weight
                category_scores[category]["count"] += 1
                
                overall_score += result.score * result.weight
                total_weight += result.weight
        
        if total_weight > 0:
            overall_score = overall_score / total_weight
        
        return {
            "overall_score": overall_score,
            "dimensions": results,
            "categories": category_scores,
            "timestamp": datetime.now().isoformat(),
            "evaluator_count": len(self.all_tests),
            "completed_count": sum(1 for r in results.values() if r.status != "failed"),
            "config": {
                "max_sample_count": self.max_sample_count,
                "max_concurrent": self.max_concurrent,
                "api_key_set": bool(self.evaluator.api_key)
            }
        }
    
    async def run_full_evaluation_v1(self) -> Dict[str, Any]:
        """运行 V1 评估 (7维度) - 基于 V2 结果聚合"""
        print("=" * 60)
        print("RANGEN AI中台能力真实测试评估 (V1 - 7维度)")
        print(f"样本数: {self.max_sample_count}, 并发数: {self.max_concurrent}")
        print("=" * 60)
        
        # 先运行 V2 评估
        v2_results = await self.run_full_evaluation_v2()
        
        # 聚合到 V1 维度
        v1_dimensions = {
            "core_capability": ["orchestration", "agent_completeness", "prompt_engineering", "context_engineering"],
            "performance": ["response_quality", "routing", "reasoning", "knowledge_recall", "tool_calling", "multi_turn", "self_learning"],
            "reliability": ["harness", "architecture", "observability", "monitoring", "self_healing", "rollout"],
            "security": [],
            "code_quality": ["data_source", "knowledge_mgmt", "vector_mgmt", "data_lineage"],
            "platform_features": ["app_support", "cost_control"],
            "integration": ["integration"],
        }
        
        v1_results = {}
        v1_weights = {
            "core_capability": 0.20,
            "performance": 0.30,
            "reliability": 0.20,
            "security": 0.10,
            "code_quality": 0.10,
            "platform_features": 0.05,
            "integration": 0.05,
        }
        
        overall_score = 0.0
        total_weight = 0.0
        
        for v1_dim, v2_dims in v1_dimensions.items():
            if not v2_dims:
                continue
            
            scores = []
            for v2d in v2_dims:
                if v2d in v2_results["dimensions"]:
                    scores.append(v2_results["dimensions"][v2d].score)
            
            if scores:
                avg_score = sum(scores) / len(scores)
                v1_results[v1_dim] = {
                    "score": avg_score,
                    "weight": v1_weights.get(v1_dim, 0.1),
                    "sub_dimensions": v2_dims
                }
                overall_score += avg_score * v1_weights.get(v1_dim, 0.1)
                total_weight += v1_weights.get(v1_dim, 0.1)
        
        if total_weight > 0:
            overall_score = overall_score / total_weight
        
        return {
            "overall_score": overall_score,
            "dimensions": v1_results,
            "timestamp": datetime.now().isoformat(),
            "evaluator_count": 7,
            "completed_count": len(v1_results),
        }
