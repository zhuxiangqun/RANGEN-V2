"""
V2能力评估运行器

整合24个评估维度，提供完整的系统评估
"""

import asyncio
import json
import logging
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

# 加载 .env 文件中的环境变量
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

from .base import EVALUATION_CONFIG

# 导入v2评估器
from .evaluators.v2_evaluators import (
    OrchestrationEvaluator,
    AgentCompletenessEvaluator,
    PromptEngineeringEvaluator,
    ContextEngineeringEvaluator,
    ResponseQualityEvaluator,
    RoutingEvaluator,
    ReasoningEvaluator,
    KnowledgeRecallEvaluator,
    ToolCallingEvaluator,
    MultiTurnEvaluator,
    SelfLearningEvaluator,
    HarnessEvaluator,
    ArchitectureEvaluator,
    ObservabilityEvaluator,
    MonitoringEvaluator,
    SelfHealingEvaluator,
    RolloutEvaluator,
    DataSourceEvaluator,
    KnowledgeMgmtEvaluator,
    VectorMgmtEvaluator,
    DataLineageEvaluator,
    AppSupportEvaluator,
    CostControlEvaluator,
    IntegrationEvaluator,
    SecurityEvaluator,
    CodeQualityEvaluator,
    DimensionResult,
    SubItemResult
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# V2评估器列表
V2_EVALUATORS = [
    # A. 基础能力 (25%)
    OrchestrationEvaluator,
    AgentCompletenessEvaluator,
    PromptEngineeringEvaluator,
    ContextEngineeringEvaluator,
    # B. 智能能力 (30%)
    ResponseQualityEvaluator,
    RoutingEvaluator,
    ReasoningEvaluator,
    KnowledgeRecallEvaluator,
    ToolCallingEvaluator,
    MultiTurnEvaluator,
    SelfLearningEvaluator,
    # C. 架构能力 (28%)
    HarnessEvaluator,
    ArchitectureEvaluator,
    ObservabilityEvaluator,
    MonitoringEvaluator,
    SelfHealingEvaluator,
    RolloutEvaluator,
    # D. 数据能力 (10%)
    DataSourceEvaluator,
    KnowledgeMgmtEvaluator,
    VectorMgmtEvaluator,
    DataLineageEvaluator,
    # E. 平台能力 (7%)
    AppSupportEvaluator,
    CostControlEvaluator,
    IntegrationEvaluator,
    # S. 安全能力 (独立)
    SecurityEvaluator,
    # Q. 代码质量 (独立)
    CodeQualityEvaluator,
]

# 分类信息
CATEGORY_INFO = {
    "A": {"name": "基础能力", "weight": 0.25},
    "B": {"name": "智能能力", "weight": 0.30},
    "C": {"name": "架构能力", "weight": 0.28},
    "D": {"name": "数据能力", "weight": 0.10},
    "E": {"name": "平台能力", "weight": 0.07},
}


class RANGENEvaluator:
    """RANGEN系统统一评估器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**EVALUATION_CONFIG, **(config or {})}
        self.evaluators = self._create_evaluators()
    
    def _create_evaluators(self) -> List:
        import importlib.util
        import os
        
        current_file = os.path.abspath(__file__)
        v2_capability_dir = os.path.dirname(current_file)
        evaluation_dir = os.path.dirname(v2_capability_dir)
        organized_evaluator_path = os.path.join(
            evaluation_dir, 'v1_capability', 'evaluators', 'organized_evaluator.py'
        )
        
        spec = importlib.util.spec_from_file_location("organized_evaluator", organized_evaluator_path)
        organized_evaluator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(organized_evaluator)
        
        return [
            organized_evaluator.CoreCapabilityEvaluator(self.config),
            organized_evaluator.PerformanceEvaluator(self.config),
            organized_evaluator.ReliabilityEvaluator(self.config),
            organized_evaluator.SecurityEvaluator(self.config),
            organized_evaluator.CodeQualityEvaluator(self.config),
            organized_evaluator.PlatformFeatureEvaluator(self.config),
            organized_evaluator.IntegrationEvaluator(self.config),
        ]
    
    async def run_full_evaluation(self) -> Dict[str, Any]:
        logger.info("=" * 50)
        logger.info("开始RANGEN系统全面评估")
        logger.info("=" * 50)
        
        results = {}
        overall_score = 0.0
        total_weight = 0.0
        
        for evaluator in self.evaluators:
            logger.info(f"开始评估: {evaluator.dimension_name}")
            start_time = time.time()
            
            try:
                result = await evaluator.evaluate()
                result["execution_time_ms"] = (time.time() - start_time) * 1000
                
                if "status" in result and hasattr(result["status"], "value"):
                    result["status"] = result["status"].value
                
                results[evaluator.dimension_name] = result
                
                weight = getattr(evaluator, 'weight', 0.1)
                score = result.get("score", 0)
                overall_score += score * weight
                total_weight += weight
                
            except Exception as e:
                logger.error(f"评估 {evaluator.dimension_name} 失败: {e}")
                results[evaluator.dimension_name] = {
                    "dimension": evaluator.dimension_name,
                    "score": 0.0,
                    "status": "failed",
                    "error": str(e)
                }
        
        if total_weight > 0:
            overall_score /= total_weight
        
        self._print_results(overall_score, results)
        self._save_results(overall_score, results)
        
        return {
            "overall_score": overall_score,
            "dimensions": results,
            "timestamp": datetime.now().isoformat(),
            "evaluator_count": len(self.evaluators),
            "completed_count": sum(
                1 for r in results.values() 
                if r.get("status") == "completed"
            )
        }
    
    async def run_specific(self, dimension: str):
        for evaluator in self.evaluators:
            if evaluator.dimension_name == dimension:
                return await evaluator.evaluate()
        
        raise ValueError(f"未知评估维度: {dimension}")
    
    def _print_results(self, overall_score: float, results: Dict[str, Any]):
        print("\n" + "=" * 60)
        print("📊 RANGEN 系统评估报告 (全面版)")
        print("=" * 60)
        print(f"综合评分: {overall_score:.1%}")
        print(f"评估维度: {len(results)}")
        print("-" * 60)
        
        for dim_name, dim_result in results.items():
            score = dim_result.get("score", 0)
            status = dim_result.get("status", "unknown")
            details = dim_result.get("details", "")
            
            status_icon = {
                "completed": "✅",
                "failed": "❌",
                "skipped": "⏭️",
                "running": "🔄"
            }.get(status, "❓")
            
            print(f"{status_icon} {dim_name:20s} {score:6.1%} - {details}")
        
        print("=" * 60)
    
    def _save_results(self, overall_score: float, results: Dict[str, Any], filepath: str = None):
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"evaluation/v1_capability/results/v1_framework_{timestamp}.json"
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        full_results = {
            "overall_score": overall_score,
            "dimensions": results,
            "timestamp": datetime.now().isoformat(),
            "evaluator_count": len(self.evaluators),
            "completed_count": sum(
                1 for r in results.values() 
                if r.get("status") == "completed"
            )
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(full_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"评估结果已保存到: {filepath}")


class RANGENEvaluatorV2:
    """RANGEN系统V2统一评估器 - 26维度全面评估"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**EVALUATION_CONFIG, **(config or {})}
        self.evaluators = self._create_evaluators()
    
    def _create_evaluators(self):
        return [evaluator_class(self.config) for evaluator_class in V2_EVALUATORS]
    
    async def run_full_evaluation_v2(self) -> Dict[str, Any]:
        logger.info("=" * 60)
        logger.info("开始RANGEN系统V2全面评估 (26维度)")
        logger.info("=" * 60)
        
        results = {}
        category_scores = {cat: {"score": 0, "weight": 0, "count": 0} for cat in "ABCDEQS"}
        overall_score = 0.0
        total_weight = 0.0
        
        max_concurrent = self.config.get("max_concurrent", 4)
        logger.info(f"使用并发数: {max_concurrent}")
        
        async def evaluate_with_timing(evaluator):
            logger.info(f"评估中: {evaluator.dimension_cn} ({evaluator.dimension_name})")
            start_time = time.time()
            try:
                result = await evaluator.evaluate()
                execution_time_ms = (time.time() - start_time) * 1000
                logger.info(f"  {evaluator.dimension_name} 完成，耗时: {execution_time_ms:.0f}ms")
                return evaluator, result, execution_time_ms, None
            except Exception as e:
                logger.error(f"评估 {evaluator.dimension_name} 失败: {e}")
                return evaluator, None, 0, str(e)
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_evaluate(evaluator):
            async with semaphore:
                return await evaluate_with_timing(evaluator)
        
        tasks = [bounded_evaluate(e) for e in self.evaluators]
        eval_results = await asyncio.gather(*tasks)
        
        for evaluator, result, execution_time_ms, error in eval_results:
            if error:
                results[evaluator.dimension_name] = {
                    "dimension": evaluator.dimension_name,
                    "name": evaluator.dimension_cn,
                    "category": evaluator.category,
                    "weight": evaluator.weight,
                    "score": 0.0,
                    "status": "failed",
                    "error": error,
                    "subitems": []
                }
            elif isinstance(result, DimensionResult):
                dim_data = asdict(result)
                dim_data["execution_time_ms"] = execution_time_ms
                results[evaluator.dimension_name] = dim_data
                
                category = evaluator.category
                category_scores[category]["score"] += result.score * result.weight
                category_scores[category]["weight"] += result.weight
                category_scores[category]["count"] += 1
                
                overall_score += result.score * result.weight
                total_weight += result.weight
                
                status_icon = {
                    "excellent": "✅",
                    "good": "👍",
                    "fair": "⚠️",
                    "poor": "❌"
                }.get(result.status, "❓")
                
                logger.info(f"  {status_icon} {evaluator.dimension_name}: {result.score:.1%}")
            else:
                results[evaluator.dimension_name] = result
                logger.warning(f"  ⚠️ {evaluator.dimension_name} 返回格式异常")
        
        for cat in "ABCDE":
            if category_scores[cat]["weight"] > 0:
                category_scores[cat]["avg_score"] = (
                    category_scores[cat]["score"] / category_scores[cat]["weight"]
                )
            else:
                category_scores[cat]["avg_score"] = 0.0
        
        if total_weight > 0:
            overall_score /= total_weight
        
        self._print_results_v2(overall_score, category_scores, results)
        self._save_results_v2(overall_score, category_scores, results)
        
        return {
            "overall_score": overall_score,
            "categories": category_scores,
            "dimensions": results,
            "timestamp": datetime.now().isoformat(),
            "evaluator_count": len(self.evaluators),
            "completed_count": sum(
                1 for r in results.values() 
                if r.get("status") not in ["failed", "skipped"]
            )
        }
    
    def _print_results_v2(self, overall_score: float, category_scores: Dict, results: Dict):
        print("\n" + "=" * 70)
        print("📊 RANGEN AI中台核心能力评估报告 (V2 - 26维度)")
        print("=" * 70)
        print(f"综合评分: {overall_score:.1%}")
        print("-" * 70)
        
        for cat, info in CATEGORY_INFO.items():
            cat_data = category_scores.get(cat, {})
            cat_score = cat_data.get("avg_score", 0)
            cat_weight = info["weight"]
            count = cat_data.get("count", 0)
            
            print(f"\n【{cat}】{info['name']} (权重{cat_weight:.0%}) - 评分: {cat_score:.1%}")
            print(f"  已评估维度: {count}")
            
            for dim_name, dim_result in results.items():
                if dim_result.get("category") == cat:
                    score = dim_result.get("score", 0)
                    status = dim_result.get("status", "unknown")
                    status_icon = {
                        "excellent": "🌟",
                        "good": "✅",
                        "fair": "⚠️",
                        "poor": "❌"
                    }.get(status, "❓")
                    name = dim_result.get("name", dim_name)
                    print(f"    {status_icon} {name:16s} {score:6.1%}")
        
        print("\n" + "=" * 70)
    
    def _save_results_v2(self, overall_score: float, category_scores: Dict, results: Dict, filepath: str = None):
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"evaluation/v2_capability/results/v2_framework_{timestamp}.json"
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        full_results = {
            "overall_score": overall_score,
            "categories": {
                cat: {
                    "name": CATEGORY_INFO[cat]["name"],
                    "weight": CATEGORY_INFO[cat]["weight"],
                    "score": category_scores[cat].get("avg_score", 0),
                    "count": category_scores[cat].get("count", 0)
                }
                for cat in "ABCDE"
            },
            "dimensions": results,
            "timestamp": datetime.now().isoformat(),
            "evaluator_count": len(self.evaluators),
            "completed_count": sum(
                1 for r in results.values() 
                if r.get("status") not in ["failed", "skipped"]
            )
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(full_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"V2评估结果已保存到: {filepath}")


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="RANGEN V2能力评估系统")
    parser.add_argument("--sample-count", type=int, default=10, help="每个维度的测试样本数 (默认: 10)")
    parser.add_argument("--max-concurrent", type=int, default=4, help="最大并发评估数 (默认: 4)")
    parser.add_argument("--v2", action="store_true", help="使用V2评估框架 (26维度)")
    parser.add_argument("--real", action="store_true", help="使用真实API测试模式 (调用DeepSeek API)")
    parser.add_argument("--code", action="store_true", help="使用代码扫描模式 (默认)")
    parser.add_argument("--quick", action="store_true", help="快速模式: 仅测试前 4 个维度")
    return parser.parse_args()


async def main():
    args = parse_args()
    
    use_real_api = not args.code
    
    if use_real_api:
        from .real_api_tester import RealCapabilityEvaluator
        
        print(f"🤖 智能能力评估 (7维度) - 样本数: {args.sample_count}, 并发数: {args.max_concurrent}")
        evaluator = RealCapabilityEvaluator({
            "max_sample_count": args.sample_count,
            "max_concurrent": args.max_concurrent,
            "quick_mode": args.quick
        })
        results = await evaluator.run_full_evaluation_v2()
    else:
        print(f"📋 代码扫描评估 - 样本数: {args.sample_count}, 并发数: {args.max_concurrent}")
        evaluator = RANGENEvaluatorV2()
        evaluator.config["max_sample_count"] = args.sample_count
        evaluator.config["max_concurrent"] = args.max_concurrent
        results = await evaluator.run_full_evaluation_v2()
    
    return results


async def main_v2():
    evaluator = RANGENEvaluatorV2()
    results = await evaluator.run_full_evaluation_v2()
    return results


if __name__ == "__main__":
    asyncio.run(main())
