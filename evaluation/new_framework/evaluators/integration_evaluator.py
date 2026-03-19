"""
集成就绪度评估器 - 评估系统集成能力

检查API完整性、文档、认证等
"""

import requests
from typing import Dict, Any, Optional
from base_evaluator import BaseEvaluator, EvaluationResult, EvaluationStatus


class IntegrationEvaluator(BaseEvaluator):
    """集成就绪度评估"""
    
    @property
    def dimension_name(self) -> str:
        return "integration"
    
    @property
    def weight(self) -> float:
        return 0.15
    
    async def evaluate(self) -> EvaluationResult:
        results = {
            "api_coverage": await self._check_api_coverage(),
            "documentation": await self._check_documentation(),
            "authentication": await self._check_authentication()
        }
        
        scores = [r["score"] for r in results.values() if r.get("score") is not None]
        overall_score = sum(scores) / len(scores) if scores else 0.5
        
        return {
            "dimension": self.dimension_name,
            "score": self._safe_score(overall_score),
            "status": EvaluationStatus.COMPLETED,
            "metrics": results,
            "details": f"API覆盖率: {results['api_coverage'].get('coverage', 0):.0f}%"
        }
    
    async def _check_api_coverage(self) -> Dict[str, Any]:
        endpoints = [
            "/health",
            "/api/v1/agents",
            "/api/v1/skills",
            "/api/v1/tools",
            "/chat"
        ]
        
        available = 0
        for endpoint in endpoints:
            try:
                resp = requests.get(f"{self.system_url}{endpoint}", timeout=3)
                if resp.status_code < 500:
                    available += 1
            except Exception:
                pass
        
        coverage = available / len(endpoints) if endpoints else 0
        return {"score": coverage, "coverage": coverage * 100, "available": available, "total": len(endpoints)}
    
    async def _check_documentation(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/docs", timeout=5)
            has_docs = resp.status_code == 200
            return {"score": 1.0 if has_docs else 0.0, "docs_available": has_docs}
        except Exception:
            return {"score": 0.0, "docs_available": False}
    
    async def _check_authentication(self) -> Dict[str, Any]:
        try:
            resp_no_auth = requests.get(f"{self.system_url}/api/v1/agents", timeout=5)
            if resp_no_auth.status_code == 200:
                return {"score": 0.5, "note": "无认证保护"}
            
            if resp_no_auth.status_code == 401:
                return {"score": 1.0, "auth_required": True}
        except Exception:
            pass
        
        return {"score": 0.5, "auth_unknown": True}


class SecurityEvaluator(BaseEvaluator):
    """安全性评估"""
    
    @property
    def dimension_name(self) -> str:
        return "security"
    
    @property
    def weight(self) -> float:
        return 0.10
    
    async def evaluate(self) -> EvaluationResult:
        results = {
            "api_security": await self._check_api_security(),
            "input_validation": await self._check_input_validation()
        }
        
        scores = [r["score"] for r in results.values() if r.get("score") is not None]
        overall_score = sum(scores) / len(scores) if scores else 0.5
        
        return {
            "dimension": self.dimension_name,
            "score": self._safe_score(overall_score),
            "status": EvaluationStatus.COMPLETED,
            "metrics": results,
            "details": f"安全评估得分: {overall_score:.0%}"
        }
    
    async def _check_api_security(self) -> Dict[str, Any]:
        dangerous_endpoints = [
            "/api/v1/config",
            "/api/v1/execute",
        ]
        
        protected = 0
        for endpoint in dangerous_endpoints:
            try:
                resp = requests.get(f"{self.system_url}{endpoint}", timeout=3)
                if resp.status_code in (401, 403):
                    protected += 1
            except Exception:
                pass
        
        score = protected / len(dangerous_endpoints) if dangerous_endpoints else 0.5
        return {"score": score, "protected": protected}
    
    async def _check_input_validation(self) -> Dict[str, Any]:
        try:
            resp = requests.post(
                f"{self.system_url}/chat",
                json={"query": "<script>alert('xss')</script>"},
                timeout=10
            )
            if resp.status_code == 200:
                return {"score": 0.5, "xss_test": "未防护"}
            return {"score": 1.0, "xss_test": "已防护"}
        except Exception:
            return {"score": 0.5, "xss_test": "未知"}
