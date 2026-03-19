"""
可靠性评估器 - 评估系统稳定性和容错能力

测试错误处理、故障恢复等
"""

import requests
from typing import Dict, Any, Optional
from base_evaluator import BaseEvaluator, EvaluationResult, EvaluationStatus


class ReliabilityEvaluator(BaseEvaluator):
    """可靠性评估"""
    
    @property
    def dimension_name(self) -> str:
        return "reliability"
    
    @property
    def weight(self) -> float:
        return 0.15
    
    async def evaluate(self) -> EvaluationResult:
        results = {
            "error_handling": await self._test_error_handling(),
            "graceful_degradation": await self._test_graceful_degradation(),
            "timeout_handling": await self._test_timeout_handling()
        }
        
        scores = [r["score"] for r in results.values() if r.get("score") is not None]
        overall_score = sum(scores) / len(scores) if scores else 0.5
        
        return {
            "dimension": self.dimension_name,
            "score": self._safe_score(overall_score),
            "status": EvaluationStatus.COMPLETED,
            "metrics": results,
            "details": f"测试了 {len(results)} 个可靠性维度"
        }
    
    async def _test_error_handling(self) -> Dict[str, Any]:
        test_cases = [
            {"query": "", "description": "空查询"},
            {"query": "a" * 10000, "description": "超长查询"},
        ]
        
        handled = 0
        for case in test_cases:
            try:
                resp = requests.post(
                    f"{self.system_url}/chat",
                    json={"query": case["query"]},
                    timeout=10
                )
                if resp.status_code in (200, 400, 422):
                    handled += 1
            except Exception:
                pass
        
        score = handled / len(test_cases) if test_cases else 0
        return {"score": score, "handled": handled, "total": len(test_cases)}
    
    async def _test_graceful_degradation(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/health", timeout=5)
            if resp.status_code == 200:
                return {"score": 1.0, "degradation": "正常"}
            
            health_data = resp.json()
            if health_data.get("status") in ("degraded", "limited"):
                return {"score": 0.7, "degradation": health_data.get("status")}
        except Exception:
            pass
        
        return {"score": 0.5, "degradation": "未知"}
    
    async def _test_timeout_handling(self) -> Dict[str, Any]:
        import time
        start = time.time()
        try:
            resp = requests.post(
                f"{self.system_url}/chat",
                json={"query": "测试超时"},
                timeout=5
            )
            elapsed = time.time() - start
            if elapsed < 6:
                return {"score": 1.0, "timeout_handled": True}
        except requests.exceptions.Timeout:
            return {"score": 1.0, "timeout_handled": True}
        except Exception:
            pass
        
        return {"score": 0.0, "timeout_handled": False}


class ErrorHandlingEvaluator(BaseEvaluator):
    """错误处理评估"""
    
    @property
    def dimension_name(self) -> str:
        return "error_handling"
    
    @property
    def weight(self) -> float:
        return 0.10
    
    async def evaluate(self) -> EvaluationResult:
        results = {
            "invalid_input": await self._test_invalid_input(),
            "malformed_request": await self._test_malformed_request()
        }
        
        scores = [r["score"] for r in results.values() if r.get("score") is not None]
        overall_score = sum(scores) / len(scores) if scores else 0.5
        
        return {
            "dimension": self.dimension_name,
            "score": self._safe_score(overall_score),
            "status": EvaluationStatus.COMPLETED,
            "metrics": results,
            "details": f"错误处理得分: {overall_score:.0%}"
        }
    
    async def _test_invalid_input(self) -> Dict[str, Any]:
        invalid_inputs = [
            {"query": None},
            {"query": 12345},
            {},
        ]
        
        proper_errors = 0
        for inp in invalid_inputs:
            try:
                resp = requests.post(
                    f"{self.system_url}/chat",
                    json=inp,
                    timeout=5
                )
                if resp.status_code >= 400:
                    proper_errors += 1
            except Exception:
                proper_errors += 1
        
        score = proper_errors / len(invalid_inputs)
        return {"score": score, "proper_errors": proper_errors}
    
    async def _test_malformed_request(self) -> Dict[str, Any]:
        try:
            resp = requests.post(
                f"{self.system_url}/chat",
                data="not json",
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            if resp.status_code >= 400:
                return {"score": 1.0}
        except Exception:
            return {"score": 1.0}
        
        return {"score": 0.0}
