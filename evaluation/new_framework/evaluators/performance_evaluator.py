"""
性能评估器 - 评估系统性能指标

测量延迟、吞吐量、并发能力等
"""

import time
import requests
import asyncio
import statistics
from typing import Dict, Any, List, Optional
from base_evaluator import BaseEvaluator, EvaluationResult, EvaluationStatus


class PerformanceEvaluator(BaseEvaluator):
    """性能指标评估"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.test_query = self.config.get("test_query", "你好，请介绍一下自己")
        self.test_iterations = self.config.get("test_iterations", 10)
    
    @property
    def dimension_name(self) -> str:
        return "performance"
    
    @property
    def weight(self) -> float:
        return 0.20
    
    async def evaluate(self) -> EvaluationResult:
        try:
            results = {
                "latency": await self._measure_latency(),
                "throughput": await self._measure_throughput(),
                "availability": await self._check_availability()
            }
            
            latency_p50 = results["latency"].get("p50_ms")
            latency_score = self._score_latency(latency_p50)
            throughput_score = self._score_throughput(results["throughput"].get("qps", 0))
            availability_score = results["availability"].get("score", 0)
            
            overall_score = (latency_score * 0.4 + throughput_score * 0.3 + availability_score * 0.3)
            
            latency_str = f"{latency_p50:.0f}ms" if latency_p50 else "N/A"
            
            return {
                "dimension": self.dimension_name,
                "score": self._safe_score(overall_score),
                "status": EvaluationStatus.COMPLETED,
                "metrics": results,
                "details": f"延迟: {latency_str}, 吞吐量: {results['throughput'].get('qps', 0):.1f} QPS"
            }
        except Exception as e:
            return {
                "dimension": self.dimension_name,
                "score": 0.5,
                "status": EvaluationStatus.SKIPPED,
                "error": str(e),
                "details": "无法测量性能"
            }
    
    async def _measure_latency(self) -> Dict[str, Any]:
        latencies = []
        
        for _ in range(self.test_iterations):
            start = time.time()
            try:
                resp = requests.post(
                    f"{self.system_url}/chat",
                    json={"query": self.test_query},
                    timeout=30
                )
                elapsed = (time.time() - start) * 1000
                if resp.status_code == 200:
                    latencies.append(elapsed)
            except Exception:
                latencies.append(30000)
        
        if not latencies:
            return {"p50_ms": None, "p95_ms": None, "p99_ms": None}
        
        latencies.sort()
        n = len(latencies)
        
        return {
            "p50_ms": statistics.median(latencies),
            "p95_ms": latencies[int(n * 0.95)] if n > 0 else None,
            "p99_ms": latencies[int(n * 0.99)] if n > 0 else None,
            "avg_ms": statistics.mean(latencies),
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "samples": n
        }
    
    async def _measure_throughput(self) -> Dict[str, Any]:
        duration = 5
        start = time.time()
        count = 0
        
        while time.time() - start < duration:
            try:
                resp = requests.post(
                    f"{self.system_url}/chat",
                    json={"query": self.test_query},
                    timeout=30
                )
                if resp.status_code == 200:
                    count += 1
            except Exception:
                pass
        
        elapsed = time.time() - start
        qps = count / elapsed if elapsed > 0 else 0
        
        return {"qps": qps, "total_requests": count, "duration_sec": elapsed}
    
    async def _check_availability(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/health", timeout=5)
            available = resp.status_code == 200
            return {"score": 1.0 if available else 0.0, "available": available}
        except Exception:
            return {"score": 0.0, "available": False}
    
    def _score_latency(self, p50_ms) -> float:
        if p50_ms is None:
            return 0.5
        if p50_ms < 1000:
            return 1.0
        if p50_ms < 3000:
            return 0.7
        if p50_ms < 5000:
            return 0.4
        return 0.1
    
    def _score_throughput(self, qps: float) -> float:
        if qps > 100:
            return 1.0
        if qps > 50:
            return 0.8
        if qps > 20:
            return 0.6
        if qps > 10:
            return 0.4
        return 0.2


class ResourceUsageEvaluator(BaseEvaluator):
    """资源使用评估"""
    
    @property
    def dimension_name(self) -> str:
        return "resource_usage"
    
    @property
    def weight(self) -> float:
        return 0.10
    
    async def evaluate(self) -> EvaluationResult:
        try:
            resp = requests.get(f"{self.system_url}/health/resource", timeout=5)
            if resp.status_code == 200:
                data = resp.json().get("resources", {})
                memory = data.get("memory", {}).get("system_percent", 100)
                cpu = data.get("cpu", {}).get("system_percent", 100)
                
                memory_score = max(0, 1 - memory / 100)
                cpu_score = max(0, 1 - cpu / 100)
                score = (memory_score + cpu_score) / 2
                
                return {
                    "dimension": self.dimension_name,
                    "score": score,
                    "status": EvaluationStatus.COMPLETED,
                    "metrics": {"memory_percent": memory, "cpu_percent": cpu},
                    "details": f"内存: {memory:.0f}%, CPU: {cpu:.0f}%"
                }
        except Exception as e:
            pass
        
        return {
            "dimension": self.dimension_name,
            "score": 0.5,
            "status": EvaluationStatus.SKIPPED,
            "details": "无法获取资源数据"
        }
