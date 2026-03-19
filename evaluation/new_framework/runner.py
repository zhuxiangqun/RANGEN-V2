"""
统一评估运行器

整合所有评估器，提供完整的系统评估
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from base_evaluator import EVALUATION_CONFIG

from evaluation.new_framework.evaluators.organized_evaluator import (
    CoreCapabilityEvaluator,
    PerformanceEvaluator,
    ReliabilityEvaluator,
    SecurityEvaluator,
    CodeQualityEvaluator,
    PlatformFeatureEvaluator,
    IntegrationEvaluator
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RANGENEvaluator:
    """RANGEN系统统一评估器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**EVALUATION_CONFIG, **(config or {})}
        self.evaluators = self._create_evaluators()
    
    def _create_evaluators(self) -> List:
        return [
            CoreCapabilityEvaluator(self.config),
            PerformanceEvaluator(self.config),
            ReliabilityEvaluator(self.config),
            SecurityEvaluator(self.config),
            CodeQualityEvaluator(self.config),
            PlatformFeatureEvaluator(self.config),
            IntegrationEvaluator(self.config),
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
            filepath = f"evaluation_results/new_framework_{timestamp}.json"
        
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


async def main():
    evaluator = RANGENEvaluator()
    results = await evaluator.run_full_evaluation()
    return results


if __name__ == "__main__":
    asyncio.run(main())
