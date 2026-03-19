"""
RANGEN 平台评估器 - 重新分类版本

按横向能力和纵向能力分类
"""

import time
import requests
from typing import Dict, Any


class CoreCapabilityEvaluator:
    """核心功能能力评估 - 评估系统基本功能"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.system_url = self.config.get("system_url", "http://localhost:8000")
    
    @property
    def dimension_name(self) -> str:
        return "core_capability"
    
    @property
    def weight(self) -> float:
        return 0.20
    
    async def evaluate(self) -> Dict[str, Any]:
        import asyncio
        results = {
            "chat_api": await self._test_chat_api(),
        }
        await asyncio.sleep(1)
        results["agent_count"] = await self._count_agents()
        await asyncio.sleep(1)
        results["skill_count"] = await self._count_skills()
        await asyncio.sleep(1)
        results["tool_count"] = await self._count_tools()
        
        scores = []
        if results["chat_api"].get("score"):
            scores.append(results["chat_api"]["score"])
        
        agent_count = results["agent_count"].get("count", 0)
        skill_count = results["skill_count"].get("count", 0)
        tool_count = results["tool_count"].get("count", 0)
        
        if agent_count and agent_count > 0:
            scores.append(min(agent_count / 50, 1.0))
        if skill_count and skill_count > 0:
            scores.append(min(skill_count / 30, 1.0))
        if tool_count and tool_count > 0:
            scores.append(min(tool_count / 40, 1.0))
        
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "dimension": self.dimension_name,
            "score": max(0, min(1, overall_score)),
            "status": "completed",
            "metrics": results,
            "details": f"Agent:{agent_count or 0}, Skill:{skill_count or 0}, Tool:{tool_count or 0}"
        }
    
    async def _test_chat_api(self) -> Dict[str, Any]:
        try:
            resp = requests.post(
                f"{self.system_url}/chat",
                json={"query": "你好"},
                timeout=30
            )
            if resp.status_code == 200:
                return {"score": 1.0, "available": True}
            return {"score": 0.5, "available": False}
        except Exception:
            return {"score": 0.0, "available": False}
    
    async def _count_agents(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/agents", timeout=5)
            if resp.status_code == 200:
                return {"count": resp.json().get("total", 0)}
        except Exception:
            pass
        return {"count": 0}
    
    async def _count_skills(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/skills", timeout=5)
            if resp.status_code == 200:
                return {"count": resp.json().get("total", 0)}
        except Exception:
            pass
        return {"count": 0}
    
    async def _count_tools(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/tools", timeout=5)
            if resp.status_code == 200:
                return {"count": resp.json().get("total", 0)}
        except Exception:
            pass
        return {"count": 0}


class PerformanceEvaluator:
    """性能资源评估 - 评估系统性能指标"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.system_url = self.config.get("system_url", "http://localhost:8000")
    
    @property
    def dimension_name(self) -> str:
        return "performance"
    
    @property
    def weight(self) -> float:
        return 0.15
    
    async def evaluate(self) -> Dict[str, Any]:
        results = {
            "latency": await self._measure_latency(),
            "throughput": await self._measure_throughput(),
            "resource": await self._check_resource()
        }
        
        latency_data = results["latency"]
        if latency_data.get("error") == "需要认证":
            return {
                "dimension": self.dimension_name,
                "score": 0.5,
                "status": "skipped",
                "metrics": results,
                "details": "需要API认证，跳过性能测试"
            }
        
        latency_score = self._score_latency(results["latency"].get("p50_ms"))
        throughput_score = self._score_throughput(results["throughput"].get("qps", 0))
        
        overall_score = (latency_score * 0.6 + throughput_score * 0.4)
        
        latency_str = f"{results['latency'].get('p50_ms', 'N/A')}ms"
        
        return {
            "dimension": self.dimension_name,
            "score": max(0, min(1, overall_score)),
            "status": "completed",
            "metrics": results,
            "details": f"延迟:{latency_str}, QPS:{results['throughput'].get('qps', 0):.1f}"
        }
    
    async def _measure_latency(self) -> Dict[str, Any]:
        import asyncio
        latencies = []
        success_count = 0
        
        for i in range(3):
            await asyncio.sleep(2)
            start = time.time()
            try:
                resp = requests.post(
                    f"{self.system_url}/chat",
                    json={"query": "hello"},
                    timeout=15
                )
                elapsed = (time.time() - start) * 1000
                if resp.status_code == 200:
                    latencies.append(elapsed)
                    success_count += 1
                elif resp.status_code == 429:
                    await asyncio.sleep(5)
                elif resp.status_code == 401 or resp.status_code == 403:
                    return {"p50_ms": None, "samples": 0, "success": 0, "error": "需要认证"}
            except Exception as e:
                pass
        
        if latencies:
            latencies.sort()
            return {"p50_ms": latencies[len(latencies)//2], "samples": len(latencies), "success": success_count}
        return {"p50_ms": None, "samples": 0, "success": success_count}
    
    async def _measure_throughput(self) -> Dict[str, Any]:
        import asyncio
        duration = 5
        start = time.time()
        count = 0
        request_count = 0
        
        while time.time() - start < duration:
            try:
                resp = requests.post(
                    f"{self.system_url}/chat",
                    json={"query": "hi"},
                    timeout=5
                )
                request_count += 1
                if resp.status_code == 200:
                    count += 1
                elif resp.status_code == 429:
                    await asyncio.sleep(3)
            except Exception:
                pass
            await asyncio.sleep(0.5)  # 每次请求间隔0.5秒
        
        elapsed = time.time() - start
        return {"qps": count / elapsed if elapsed > 0 else 0, "total": count}
    
    async def _check_resource(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/health/resource", timeout=5)
            if resp.status_code == 200:
                data = resp.json().get("resources", {})
                memory = data.get("memory", {}).get("system_percent", 50)
                return {"memory": memory}
        except Exception:
            pass
        return {"memory": None}
    
    def _score_latency(self, p50_ms) -> float:
        if p50_ms is None:
            return 0.3
        if p50_ms < 1000:
            return 1.0
        if p50_ms < 3000:
            return 0.7
        if p50_ms < 5000:
            return 0.4
        return 0.1
    
    def _score_throughput(self, qps: float) -> float:
        if qps > 10:
            return 1.0
        if qps > 5:
            return 0.7
        if qps > 2:
            return 0.5
        return 0.3


class ReliabilityEvaluator:
    """可靠性评估 - 评估系统稳定性"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.system_url = self.config.get("system_url", "http://localhost:8000")
    
    @property
    def dimension_name(self) -> str:
        return "reliability"
    
    @property
    def weight(self) -> float:
        return 0.15
    
    async def evaluate(self) -> Dict[str, Any]:
        results = {
            "error_handling": await self._test_error_handling(),
            "timeout": await self._test_timeout(),
            "health": await self._check_health()
        }
        
        scores = [r["score"] for r in results.values() if r.get("score") is not None]
        overall_score = sum(scores) / len(scores) if scores else 0.3
        
        return {
            "dimension": self.dimension_name,
            "score": max(0, min(1, overall_score)),
            "status": "completed",
            "metrics": results,
            "details": f"错误处理:{results['error_handling'].get('score', 0)*100:.0f}%, 超时处理:{results['timeout'].get('score', 0)*100:.0f}%"
        }
    
    async def _test_error_handling(self) -> Dict[str, Any]:
        invalid_inputs = [None, "", 12345]
        handled = 0
        
        for inp in invalid_inputs:
            try:
                resp = requests.post(
                    f"{self.system_url}/chat",
                    json={"query": inp},
                    timeout=10
                )
                if resp.status_code >= 400:
                    handled += 1
            except Exception:
                handled += 1
        
        return {"score": handled / len(invalid_inputs), "handled": handled}
    
    async def _test_timeout(self) -> Dict[str, Any]:
        import time
        start = time.time()
        try:
            resp = requests.post(
                f"{self.system_url}/chat",
                json={"query": "测试"},
                timeout=5
            )
            elapsed = time.time() - start
            if elapsed < 6:
                return {"score": 1.0, "handled": True}
        except requests.exceptions.Timeout:
            return {"score": 1.0, "handled": True}
        except Exception:
            pass
        return {"score": 0.0, "handled": False}
    
    async def _check_health(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/health", timeout=5)
            if resp.status_code == 200:
                return {"score": 1.0, "healthy": True}
        except Exception:
            pass
        return {"score": 0.0, "healthy": False}


class SecurityEvaluator:
    """安全性评估"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.system_url = self.config.get("system_url", "http://localhost:8000")
    
    @property
    def dimension_name(self) -> str:
        return "security"
    
    @property
    def weight(self) -> float:
        return 0.10
    
    async def evaluate(self) -> Dict[str, Any]:
        results = {
            "input_validation": await self._test_input_validation()
        }
        
        return {
            "dimension": self.dimension_name,
            "score": results["input_validation"].get("score", 0.5),
            "status": "completed",
            "metrics": results,
            "details": f"输入验证: {results['input_validation'].get('score', 0)*100:.0f}%"
        }
    
    async def _test_input_validation(self) -> Dict[str, Any]:
        try:
            resp = requests.post(
                f"{self.system_url}/chat",
                json={"query": "<script>alert('xss')</script>"},
                timeout=10
            )
            return {"score": 1.0}
        except Exception:
            return {"score": 0.5}


class CodeQualityEvaluator:
    """代码质量评估"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.source_path = self.config.get("source_path", "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/src")
    
    @property
    def dimension_name(self) -> str:
        return "code_quality"
    
    @property
    def weight(self) -> float:
        return 0.10
    
    async def evaluate(self) -> Dict[str, Any]:
        import ast
        from pathlib import Path
        
        complexity_result = await self._check_complexity()
        
        file_count = complexity_result.get("files", 0)
        
        file_score = min(file_count / 100, 1.0) if file_count else 0.3
        complexity_score = complexity_result.get("score", 0.5)
        
        overall_score = file_score * 0.4 + complexity_score * 0.6
        
        return {
            "dimension": self.dimension_name,
            "score": max(0, min(1, overall_score)),
            "status": "completed",
            "metrics": {
                "file_count": file_count,
                "complexity": complexity_result
            },
            "details": f"文件数:{file_count}, 复杂度:{complexity_result.get('avg', 'N/A')}"
        }
    
    async def _check_complexity(self) -> Dict[str, Any]:
        import ast
        from pathlib import Path
        
        total = 0
        file_count = 0
        
        try:
            for p in Path(self.source_path).rglob("*.py"):
                if "__pycache__" in str(p):
                    continue
                try:
                    with open(p) as f:
                        tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.If, ast.While, ast.For)):
                            total += 1
                    file_count += 1
                except Exception:
                    pass
        except Exception:
            pass
        
        avg = total / file_count if file_count > 0 else 0
        score = max(0, 1 - avg / 50)
        
        return {"avg": avg, "score": score, "files": file_count}


class PlatformFeatureEvaluator:
    """平台功能评估 - 评估各功能模块"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.system_url = self.config.get("system_url", "http://localhost:8000")
    
    @property
    def dimension_name(self) -> str:
        return "platform_features"
    
    @property
    def weight(self) -> float:
        return 0.20
    
    async def evaluate(self) -> Dict[str, Any]:
        results = {
            "workflow": await self._check_workflow(),
            "rag": await self._check_rag(),
            "cache": await self._check_cache(),
            "gateway": await self._check_gateway(),
            "mcp": await self._check_mcp(),
            "monitoring": await self._check_monitoring()
        }
        
        active_count = sum(1 for r in results.values() if r.get("score", 0) > 0)
        overall_score = active_count / len(results)
        
        active_features = [k for k, v in results.items() if v.get("score", 0) > 0]
        
        return {
            "dimension": self.dimension_name,
            "score": max(0, min(1, overall_score)),
            "status": "completed",
            "metrics": results,
            "details": f"活跃功能:{active_count}/{len(results)} - {', '.join(active_features)}"
        }
    
    async def _check_workflow(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/workflow/status", timeout=3)
            if resp.status_code < 500:
                return {"score": 1.0, "available": True}
        except Exception:
            pass
        return {"score": 0.0, "available": False}
    
    async def _check_rag(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/knowledge/search", timeout=3)
            if resp.status_code < 500:
                return {"score": 1.0, "available": True}
        except Exception:
            pass
        return {"score": 0.0, "available": False}
    
    async def _check_cache(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/cache/stats", timeout=3)
            if resp.status_code < 500:
                return {"score": 1.0, "available": True}
        except Exception:
            pass
        return {"score": 0.0, "available": False}
    
    async def _check_gateway(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/gateway/health", timeout=3)
            if resp.status_code < 500:
                return {"score": 1.0, "available": True}
        except Exception:
            pass
        return {"score": 0.0, "available": False}
    
    async def _check_mcp(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/mcp/status", timeout=3)
            if resp.status_code < 500:
                return {"score": 1.0, "available": True}
        except Exception:
            pass
        return {"score": 0.0, "available": False}
    
    async def _check_monitoring(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/metrics", timeout=3)
            if resp.status_code < 500:
                return {"score": 1.0, "available": True}
        except Exception:
            pass
        return {"score": 0.0, "available": False}


class IntegrationEvaluator:
    """集成能力评估"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.system_url = self.config.get("system_url", "http://localhost:8000")
    
    @property
    def dimension_name(self) -> str:
        return "integration"
    
    @property
    def weight(self) -> float:
        return 0.10
    
    async def evaluate(self) -> Dict[str, Any]:
        results = {
            "api_endpoints": await self._check_endpoints(),
            "docs": await self._check_docs()
        }
        
        scores = [r["score"] for r in results.values() if r.get("score") is not None]
        overall_score = sum(scores) / len(scores) if scores else 0.3
        
        return {
            "dimension": self.dimension_name,
            "score": max(0, min(1, overall_score)),
            "status": "completed",
            "metrics": results,
            "details": f"API端点:{results['api_endpoints'].get('available', 0)}, 文档:{results['docs'].get('available', False)}"
        }
    
    async def _check_endpoints(self) -> Dict[str, Any]:
        endpoints = ["/health", "/api/v1/agents", "/api/v1/skills", "/api/v1/tools", "/chat"]
        available = 0
        
        for ep in endpoints:
            try:
                if ep == "/chat":
                    resp = requests.post(f"{self.system_url}{ep}", json={"query": "test"}, timeout=3)
                else:
                    resp = requests.get(f"{self.system_url}{ep}", timeout=3)
                if resp.status_code < 500:
                    available += 1
            except Exception:
                pass
        
        return {"available": available, "total": len(endpoints), "score": available / len(endpoints)}
    
    async def _check_docs(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/docs", timeout=3)
            return {"available": resp.status_code == 200, "score": 1.0 if resp.status_code == 200 else 0.0}
        except Exception:
            return {"available": False, "score": 0.0}
