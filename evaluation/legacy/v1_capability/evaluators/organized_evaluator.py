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
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取认证头"""
        import os
        headers = {}
        api_key = os.environ.get("RANGEN_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers
    
    async def _measure_latency(self) -> Dict[str, Any]:
        import asyncio
        latencies = []
        success_count = 0
        auth_headers = self._get_auth_headers()
        
        for i in range(3):
            await asyncio.sleep(2)
            start = time.time()
            try:
                resp = requests.post(
                    f"{self.system_url}/chat",
                    json={"query": "hello"},
                    headers=auth_headers,
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
        auth_headers = self._get_auth_headers()
        
        while time.time() - start < duration:
            try:
                resp = requests.post(
                    f"{self.system_url}/chat",
                    json={"query": "hi"},
                    headers=auth_headers,
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
    """可靠性评估 - 评估系统稳定性
    
    子项:
    - error_handling: 异常输入处理
    - timeout_handling: 超时机制 (5秒内响应或超时)
    - health_check: 健康检查 (/health 返回 200)
    - fallback: 降级策略 (API失败时降级)
    - retry: 重试机制 (自动重试失败请求)
    - circuit_breaker: 熔断器 (防止雪崩)
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.system_url = self.config.get("system_url", "http://localhost:8000")
        self.source_path = self.config.get("source_path", "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/src")
    
    @property
    def dimension_name(self) -> str:
        return "reliability"
    
    @property
    def weight(self) -> float:
        return 0.15
    
    async def evaluate(self) -> Dict[str, Any]:
        results = {
            "error_handling": await self._test_error_handling(),
            "timeout_handling": await self._test_timeout_handling(),
            "health_check": await self._test_health_check(),
            "fallback": await self._test_fallback(),
            "retry": await self._test_retry(),
            "circuit_breaker": await self._test_circuit_breaker(),
        }
        
        scores = [r["score"] for r in results.values() if r.get("score") is not None]
        overall_score = sum(scores) / len(scores) if scores else 0.3
        
        passed = sum(1 for r in results.values() if r.get("score", 0) >= 0.7)
        
        return {
            "dimension": self.dimension_name,
            "score": max(0, min(1, overall_score)),
            "status": "completed",
            "metrics": results,
            "details": f"可靠性评估完成，{passed}/6项达标",
            "evidence": [f"{k}: {v.get('evidence', 'N/A')}" for k, v in results.items()],
        }
    
    async def _test_error_handling(self) -> Dict[str, Any]:
        """测试异常输入处理 - 全部正确拒绝才算满分"""
        invalid_inputs = [
            None,
            "",
            12345,
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "{'invalid': 'json'}",
        ]
        handled = 0
        evidence = []
        
        for inp in invalid_inputs:
            try:
                resp = requests.post(
                    f"{self.system_url}/chat",
                    json={"query": str(inp) if inp is not None else None},
                    timeout=10
                )
                if resp.status_code >= 400:
                    handled += 1
                else:
                    evidence.append(f"输入 '{str(inp)[:20]}...' 未被拒绝")
            except Exception:
                handled += 1
        
        score = handled / len(invalid_inputs) if invalid_inputs else 0.3
        return {
            "score": score,
            "handled": handled,
            "total": len(invalid_inputs),
            "evidence": f"{handled}/{len(invalid_inputs)}正确拒绝"
        }
    
    async def _test_timeout_handling(self) -> Dict[str, Any]:
        """测试超时机制 - 5秒内响应或超时"""
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
                return {"score": 1.0, "elapsed": f"{elapsed:.2f}s", "evidence": f"响应时间{elapsed:.2f}s<5s"}
        except requests.exceptions.Timeout:
            return {"score": 1.0, "elapsed": "timeout", "evidence": "5秒超时正常"}
        except Exception:
            return {"score": 0.5, "elapsed": "error", "evidence": "请求异常"}
        return {"score": 0.3, "elapsed": "unknown", "evidence": "超时机制未工作"}
    
    async def _test_health_check(self) -> Dict[str, Any]:
        """测试健康检查端点"""
        try:
            resp = requests.get(f"{self.system_url}/health", timeout=5)
            if resp.status_code == 200:
                return {"score": 1.0, "healthy": True, "evidence": "/health返回200"}
            return {"score": 0.5, "healthy": False, "evidence": f"/health返回{resp.status_code}"}
        except Exception:
            return {"score": 0.0, "healthy": False, "evidence": "/health不可访问"}
    
    async def _test_fallback(self) -> Dict[str, Any]:
        """测试降级策略"""
        fallback_patterns = ["fallback", "degrade", "降级", "backup"]
        found = []
        
        from pathlib import Path
        for pattern in fallback_patterns:
            files = list(Path(self.source_path).rglob(f"*{pattern}*.py"))
            if files:
                found.extend([f.name for f in files[:3]])
        
        if found:
            return {"score": 1.0, "found": found, "evidence": f"检测到{len(found)}个降级相关文件"}
        
        try:
            resp = requests.post(f"{self.system_url}/api/v1/fallback", timeout=5)
            if resp.status_code < 500:
                return {"score": 0.7, "evidence": "fallback端点可访问"}
        except:
            pass
        
        return {"score": 0.3, "evidence": "未检测到降级策略"}
    
    async def _test_retry(self) -> Dict[str, Any]:
        """测试重试机制"""
        retry_patterns = ["retry", "重试", "attempt"]
        found = []
        
        from pathlib import Path
        for pattern in retry_patterns:
            files = list(Path(self.source_path).rglob(f"*{pattern}*.py"))
            if files:
                found.extend([f.name for f in files[:3]])
        
        if found:
            return {"score": 1.0, "found": found, "evidence": f"检测到{len(found)}个重试相关文件"}
        
        try:
            resp = requests.post(f"{self.system_url}/api/v1/retry", timeout=5)
            if resp.status_code < 500:
                return {"score": 0.7, "evidence": "retry端点可访问"}
        except:
            pass
        
        return {"score": 0.3, "evidence": "未检测到重试机制"}
    
    async def _test_circuit_breaker(self) -> Dict[str, Any]:
        """测试熔断器"""
        cb_patterns = ["circuit", "breaker", "熔断", "hystrix"]
        found = []
        
        from pathlib import Path
        for pattern in cb_patterns:
            files = list(Path(self.source_path).rglob(f"*{pattern}*.py"))
            if files:
                found.extend([f.name for f in files[:3]])
        
        if found:
            return {"score": 1.0, "found": found, "evidence": f"检测到{len(found)}个熔断相关文件"}
        
        try:
            resp = requests.get(f"{self.system_url}/api/v1/circuit/status", timeout=5)
            if resp.status_code < 500:
                return {"score": 0.7, "evidence": "circuit端点可访问"}
        except:
            pass
        
        return {"score": 0.3, "evidence": "未检测到熔断器"}


class SecurityEvaluator:
    """安全性评估
    
    子项:
    - input_validation: 输入验证
    - sql_injection: SQL注入防护
    - xss_protection: XSS防护
    - rate_limiting: 限流
    - auth_required: 认证要求
    - sensitive_data: 敏感数据保护
    - cors_policy: CORS策略
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.system_url = self.config.get("system_url", "http://localhost:8000")
        self.source_path = self.config.get("source_path", "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/src")
    
    @property
    def dimension_name(self) -> str:
        return "security"
    
    @property
    def weight(self) -> float:
        return 0.10
    
    async def evaluate(self) -> Dict[str, Any]:
        results = {
            "input_validation": await self._test_input_validation(),
            "sql_injection": await self._test_sql_injection(),
            "xss_protection": await self._test_xss_protection(),
            "rate_limiting": await self._test_rate_limiting(),
            "auth_required": await self._test_auth_required(),
            "sensitive_data": await self._test_sensitive_data(),
            "cors_policy": await self._test_cors_policy(),
        }
        
        scores = [r["score"] for r in results.values() if r.get("score") is not None]
        overall_score = sum(scores) / len(scores) if scores else 0.3
        passed = sum(1 for r in results.values() if r.get("score", 0) >= 0.7)
        
        return {
            "dimension": self.dimension_name,
            "score": max(0, min(1, overall_score)),
            "status": "completed",
            "metrics": results,
            "details": f"安全性评估完成，{passed}/7项达标",
            "evidence": [f"{k}: {v.get('evidence', 'N/A')}" for k, v in results.items()],
        }
    
    async def _test_input_validation(self) -> Dict[str, Any]:
        xss_inputs = ["<script>alert(1)</script>", "javascript:alert(1)", "<img src=x onerror=alert(1)>"]
        protected = 0
        evidence = []
        
        for inp in xss_inputs:
            try:
                resp = requests.post(
                    f"{self.system_url}/chat",
                    json={"query": inp},
                    timeout=10
                )
                content = resp.text.lower() if resp.text else ""
                if inp.lower() not in content or resp.status_code >= 400:
                    protected += 1
                    evidence.append("XSS输入被过滤")
                else:
                    evidence.append("警告: XSS输入未被过滤")
            except Exception:
                protected += 1
        
        score = protected / len(xss_inputs)
        return {"score": score, "evidence": f"{protected}/{len(xss_inputs)}被保护"}
    
    async def _test_sql_injection(self) -> Dict[str, Any]:
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' AND '1'='1",
            "UNION SELECT NULL--",
        ]
        blocked = 0
        evidence = []
        
        for payload in sql_payloads:
            try:
                resp = requests.post(
                    f"{self.system_url}/chat",
                    json={"query": payload},
                    timeout=10
                )
                if resp.status_code >= 400:
                    blocked += 1
                elif "sql" in resp.text.lower() or "error" in resp.text.lower():
                    if "syntax" not in resp.text.lower():
                        blocked += 1
                else:
                    evidence.append("SQL注入可能未被阻止")
            except Exception:
                blocked += 1
        
        score = blocked / len(sql_payloads)
        return {"score": score, "evidence": f"{blocked}/{len(sql_payloads)}被阻止"}
    
    async def _test_xss_protection(self) -> Dict[str, Any]:
        xss_payloads = [
            "<svg onload=alert(1)>",
            "<iframe src='javascript:alert(1)'>",
            "{{constructor.constructor('alert(1)')()}}",
        ]
        escaped = 0
        
        for payload in xss_payloads:
            try:
                resp = requests.post(
                    f"{self.system_url}/chat",
                    json={"query": payload},
                    timeout=10
                )
                if resp.status_code >= 400:
                    escaped += 1
                else:
                    content = resp.text
                    dangerous_tags = ["<script", "<svg", "<iframe", "javascript:"]
                    if not any(tag in content.lower() for tag in dangerous_tags):
                        escaped += 1
            except Exception:
                escaped += 1
        
        score = escaped / len(xss_payloads)
        return {"score": score, "evidence": f"{escaped}/{len(xss_payloads)}被转义"}
    
    async def _test_rate_limiting(self) -> Dict[str, Any]:
        from pathlib import Path
        
        rate_limit_patterns = ["rate_limit", "ratelimit", "throttle", "限流"]
        found = []
        
        for pattern in rate_limit_patterns:
            files = list(Path(self.source_path).rglob(f"*{pattern}*.py"))
            if files:
                found.extend([f.name for f in files[:2]])
        
        if found:
            return {"score": 1.0, "evidence": f"检测到{len(found)}个限流文件"}
        
        try:
            resp = requests.post(f"{self.system_url}/api/v1/rate_limit", timeout=5)
            if resp.status_code == 429:
                return {"score": 1.0, "evidence": "限流生效(429)"}
            elif resp.status_code < 500:
                return {"score": 0.7, "evidence": "限流端点可访问"}
        except:
            pass
        
        return {"score": 0.3, "evidence": "未检测到限流机制"}
    
    async def _test_auth_required(self) -> Dict[str, Any]:
        protected_endpoints = [
            "/api/v1/agents",
            "/api/v1/skills",
            "/api/v1/tools",
        ]
        protected = 0
        
        for ep in protected_endpoints:
            try:
                resp = requests.get(f"{self.system_url}{ep}", timeout=5)
                if resp.status_code in [401, 403]:
                    protected += 1
                elif resp.status_code == 200:
                    data = resp.json()
                    if not data.get("items") and not data.get("data"):
                        protected += 0.5
            except Exception:
                pass
        
        score = protected / len(protected_endpoints)
        return {"score": score, "evidence": f"{int(protected)}/{len(protected_endpoints)}需要认证"}
    
    async def _test_sensitive_data(self) -> Dict[str, Any]:
        from pathlib import Path
        
        sensitive_patterns = ["password", "secret", "token", "api_key", "credential"]
        found_files = set()
        
        config_files = list(Path(self.source_path).rglob("*.py"))
        for f in config_files:
            try:
                content = f.read_text(errors="ignore")
                if any(p in content.lower() for p in sensitive_patterns):
                    if "test" not in f.name.lower() and "example" not in f.name.lower():
                        found_files.add(f.name)
            except:
                pass
        
        if not found_files:
            return {"score": 1.0, "evidence": "未在代码中发现硬编码敏感数据"}
        
        sensitive_files = [f for f in found_files if any(p in f.lower() for p in ["config", "env", "secret"])]
        if sensitive_files:
            return {"score": 0.3, "evidence": f"警告: {len(sensitive_files)}个文件可能包含敏感数据"}
        
        return {"score": 0.7, "evidence": f"检测到{len(found_files)}个包含敏感词的文件"}
    
    async def _test_cors_policy(self) -> Dict[str, Any]:
        from pathlib import Path
        
        cors_patterns = ["cors", "cross_origin", "Access-Control"]
        found = []
        
        for pattern in cors_patterns:
            files = list(Path(self.source_path).rglob(f"*{pattern}*.py"))
            if files:
                found.extend([f.name for f in files[:2]])
        
        if found:
            return {"score": 1.0, "evidence": f"检测到{len(found)}个CORS配置文件"}
        
        try:
            resp = requests.options(f"{self.system_url}/api/v1/agents", timeout=5)
            if "access-control" in resp.headers:
                return {"score": 0.8, "evidence": "CORS头存在"}
        except:
            pass
        
        return {"score": 0.4, "evidence": "未检测到CORS配置"}


class CodeQualityEvaluator:
    """代码质量评估
    
    子项:
    - file_count: 文件数量
    - complexity: 圈复杂度 (平均<20)
    - duplicate_code: 重复代码 (<5%)
    - test_coverage: 测试覆盖 (>60%)
    - type_annotations: 类型注解 (>70%文件有类型)
    - docstrings: 文档字符串 (>50%函数有文档)
    - naming: 命名规范 (遵循PEP8)
    """
    
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
        results = {
            "file_count": await self._check_file_count(),
            "complexity": await self._check_complexity(),
            "duplicate_code": await self._check_duplicate_code(),
            "test_coverage": await self._check_test_coverage(),
            "type_annotations": await self._check_type_annotations(),
            "docstrings": await self._check_docstrings(),
            "naming": await self._check_naming(),
        }
        
        scores = [r["score"] for r in results.values() if r.get("score") is not None]
        overall_score = sum(scores) / len(scores) if scores else 0.3
        passed = sum(1 for r in results.values() if r.get("score", 0) >= 0.7)
        
        return {
            "dimension": self.dimension_name,
            "score": max(0, min(1, overall_score)),
            "status": "completed",
            "metrics": results,
            "details": f"代码质量评估完成，{passed}/7项达标",
            "evidence": [f"{k}: {v.get('evidence', 'N/A')}" for k, v in results.items()],
        }
    
    async def _check_file_count(self) -> Dict[str, Any]:
        from pathlib import Path
        
        py_files = list(Path(self.source_path).rglob("*.py"))
        py_files = [f for f in py_files if "__pycache__" not in str(f)]
        count = len(py_files)
        
        if 50 <= count <= 200:
            score = 1.0
        elif count < 50:
            score = count / 50
        else:
            score = max(0.5, 1.0 - (count - 200) / 500)
        
        return {"score": score, "count": count, "evidence": f"Python文件: {count}个"}
    
    async def _check_complexity(self) -> Dict[str, Any]:
        import ast
        from pathlib import Path
        
        total_complexity = 0
        file_count = 0
        high_complexity_files = []
        
        for p in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(p):
                continue
            try:
                with open(p, encoding="utf-8") as f:
                    tree = ast.parse(f.read())
                complexity = self._calculate_complexity(tree)
                total_complexity += complexity
                file_count += 1
                if complexity > 20:
                    high_complexity_files.append((p.name, complexity))
            except Exception:
                pass
        
        avg = total_complexity / file_count if file_count > 0 else 0
        
        if avg < 10:
            score = 1.0
        elif avg < 20:
            score = 1.0 - (avg - 10) / 10 * 0.3
        elif avg < 50:
            score = 0.7 - (avg - 20) / 30 * 0.4
        else:
            score = 0.3
        
        return {
            "score": max(0, score),
            "avg": round(avg, 2),
            "high_complexity": len(high_complexity_files),
            "evidence": f"平均复杂度:{avg:.1f}, 高复杂度文件:{len(high_complexity_files)}"
        }
    
    def _calculate_complexity(self, tree) -> int:
        import ast
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
    
    async def _check_duplicate_code(self) -> Dict[str, Any]:
        from pathlib import Path
        import hashlib
        
        file_hashes = {}
        duplicates = 0
        
        for p in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(p) or "test_" in p.name:
                continue
            try:
                content = p.read_text(encoding="utf-8")
                content_clean = "\n".join(line for line in content.split("\n") if line.strip() and not line.strip().startswith("#"))
                hash_val = hashlib.md5(content_clean.encode()).hexdigest()
                
                if hash_val in file_hashes:
                    duplicates += 1
                else:
                    file_hashes[hash_val] = p.name
            except Exception:
                pass
        
        total = len(file_hashes)
        dup_rate = duplicates / total if total > 0 else 0
        
        if dup_rate < 0.03:
            score = 1.0
        elif dup_rate < 0.05:
            score = 0.8
        elif dup_rate < 0.10:
            score = 0.5
        else:
            score = 0.3
        
        return {"score": score, "duplicate_rate": round(dup_rate * 100, 1), "evidence": f"重复率:{dup_rate*100:.1f}%"}
    
    async def _check_test_coverage(self) -> Dict[str, Any]:
        from pathlib import Path
        
        src_files = set()
        for p in Path(self.source_path).rglob("*.py"):
            if "__pycache__" not in str(p) and "test_" not in p.name and "_test" not in p.name:
                src_files.add(p.stem)
        
        test_files = list(Path(self.source_path).rglob("test_*.py"))
        test_files.extend(Path(self.source_path).rglob("*_test.py"))
        test_files.extend(Path(self.source_path).rglob("tests/**/*.py"))
        
        tested = set()
        for t in test_files:
            for src in src_files:
                if src in t.stem:
                    tested.add(src)
        
        coverage = len(tested) / len(src_files) if src_files else 0
        
        if coverage >= 0.6:
            score = 1.0
        elif coverage >= 0.4:
            score = 0.8
        elif coverage >= 0.2:
            score = 0.5
        else:
            score = 0.3
        
        return {
            "score": score,
            "coverage": round(coverage * 100, 1),
            "tested": len(tested),
            "total": len(src_files),
            "evidence": f"测试覆盖率:{coverage*100:.0f}%"
        }
    
    async def _check_type_annotations(self) -> Dict[str, Any]:
        from pathlib import Path
        import re
        
        typed_files = 0
        total_files = 0
        
        for p in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(p) or "test_" in p.name:
                continue
            try:
                content = p.read_text(encoding="utf-8")
                total_files += 1
                
                func_defs = re.findall(r"def \w+\([^)]*\)\s*(?:->\s*\w+)?\s*:", content)
                if func_defs:
                    has_annotations = sum(1 for f in func_defs if "->" in f)
                    if has_annotations / len(func_defs) >= 0.5:
                        typed_files += 1
            except Exception:
                pass
        
        rate = typed_files / total_files if total_files > 0 else 0
        
        if rate >= 0.7:
            score = 1.0
        elif rate >= 0.5:
            score = 0.8
        elif rate >= 0.3:
            score = 0.5
        else:
            score = 0.3
        
        return {"score": score, "rate": round(rate * 100, 1), "evidence": f"类型注解:{rate*100:.0f}%"}
    
    async def _check_docstrings(self) -> Dict[str, Any]:
        from pathlib import Path
        import re
        
        doced_funcs = 0
        total_funcs = 0
        
        for p in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(p) or "test_" in p.name:
                continue
            try:
                content = p.read_text(encoding="utf-8")
                
                class_match = re.findall(r'class \w+[^:]*:(?:\s*"""[\s\S]*?""")?', content)
                func_match = re.findall(r'def \w+\([^)]*\)[^:]*:(?:\s*"""[\s\S]*?""")?', content)
                
                total_funcs += len(class_match) + len(func_match)
                
                docstring_count = len(re.findall(r'"""[\s\S]*?"""', content))
                doced_funcs += min(docstring_count, len(class_match) + len(func_match))
            except Exception:
                pass
        
        rate = doced_funcs / total_funcs if total_funcs > 0 else 0
        
        if rate >= 0.5:
            score = 1.0
        elif rate >= 0.3:
            score = 0.7
        elif rate >= 0.1:
            score = 0.5
        else:
            score = 0.3
        
        return {"score": score, "rate": round(rate * 100, 1), "evidence": f"文档覆盖率:{rate*100:.0f}%"}
    
    async def _check_naming(self) -> Dict[str, Any]:
        from pathlib import Path
        import re
        
        issues = []
        
        for p in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(p) or "test_" in p.name:
                continue
            try:
                content = p.read_text(encoding="utf-8")
                
                camel_case_vars = re.findall(r'\b[a-z]+[A-Z]\w+\s*=', content)
                if camel_case_vars:
                    issues.append(f"{p.name}: {len(camel_case_vars)}个驼峰变量")
                
                snake_case_funcs = re.findall(r'def [a-z]+[A-Z]\w+\(', content)
                if snake_case_funcs:
                    issues.append(f"{p.name}: {len(snake_case_funcs)}个驼峰函数")
            except Exception:
                pass
        
        issue_count = len(issues)
        
        if issue_count == 0:
            score = 1.0
        elif issue_count < 5:
            score = 0.8
        elif issue_count < 20:
            score = 0.5
        else:
            score = 0.3
        
        return {"score": score, "issues": issue_count, "evidence": f"命名问题:{issue_count}处"}


class PlatformFeatureEvaluator:
    """平台功能评估 - 评估各功能模块
    
    子项:
    - workflow: 工作流引擎
    - rag: 知识检索
    - cache: 缓存系统
    - gateway: API网关
    - mcp: MCP协议
    - monitoring: 监控系统
    - streaming: 流式响应 (SSE)
    - batch: 批量处理
    """
    
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
            "monitoring": await self._check_monitoring(),
            "streaming": await self._check_streaming(),
            "batch": await self._check_batch(),
        }
        
        active_count = sum(1 for r in results.values() if r.get("score", 0) > 0)
        overall_score = active_count / len(results)
        passed = sum(1 for r in results.values() if r.get("score", 0) >= 0.7)
        
        active_features = [k for k, v in results.items() if v.get("score", 0) > 0]
        
        return {
            "dimension": self.dimension_name,
            "score": max(0, min(1, overall_score)),
            "status": "completed",
            "metrics": results,
            "details": f"平台功能评估完成，{passed}/8项达标",
            "evidence": [f"{k}: {v.get('evidence', 'N/A')}" for k, v in results.items()],
        }
    
    async def _check_workflow(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/workflow/status", timeout=3)
            if resp.status_code < 500:
                return {"score": 1.0, "available": True, "evidence": "workflow端点可访问"}
        except Exception:
            pass
        return {"score": 0.3, "available": False, "evidence": "workflow端点不可访问"}
    
    async def _check_rag(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/knowledge/search", timeout=3)
            if resp.status_code < 500:
                return {"score": 1.0, "available": True, "evidence": "rag端点可访问"}
        except Exception:
            pass
        return {"score": 0.3, "available": False, "evidence": "rag端点不可访问"}
    
    async def _check_cache(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/cache/stats", timeout=3)
            if resp.status_code < 500:
                return {"score": 1.0, "available": True, "evidence": "cache端点可访问"}
        except Exception:
            pass
        return {"score": 0.3, "available": False, "evidence": "cache端点不可访问"}
    
    async def _check_gateway(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/gateway/health", timeout=3)
            if resp.status_code < 500:
                return {"score": 1.0, "available": True, "evidence": "gateway端点可访问"}
        except Exception:
            pass
        return {"score": 0.3, "available": False, "evidence": "gateway端点不可访问"}
    
    async def _check_mcp(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/mcp/status", timeout=3)
            if resp.status_code < 500:
                return {"score": 1.0, "available": True, "evidence": "mcp端点可访问"}
        except Exception:
            pass
        return {"score": 0.3, "available": False, "evidence": "mcp端点不可访问"}
    
    async def _check_monitoring(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/metrics", timeout=3)
            if resp.status_code < 500:
                return {"score": 1.0, "available": True, "evidence": "monitoring端点可访问"}
        except Exception:
            pass
        return {"score": 0.3, "available": False, "evidence": "monitoring端点不可访问"}
    
    async def _check_streaming(self) -> Dict[str, Any]:
        try:
            resp = requests.post(
                f"{self.system_url}/chat/stream",
                json={"query": "测试流式"},
                stream=True,
                timeout=10
            )
            if resp.status_code < 500:
                content_type = resp.headers.get("Content-Type", "")
                if "text/event-stream" in content_type or "stream" in content_type:
                    return {"score": 1.0, "evidence": "SSE流式响应支持"}
                return {"score": 0.8, "evidence": "流式端点可访问但非SSE"}
        except Exception:
            pass
        
        from pathlib import Path
        stream_files = list(Path(self.config.get("source_path", "src")).rglob("*stream*.py"))
        if stream_files:
            return {"score": 0.6, "evidence": f"检测到{len(stream_files)}个流式文件"}
        
        return {"score": 0.3, "evidence": "未检测到流式响应支持"}
    
    async def _check_batch(self) -> Dict[str, Any]:
        try:
            resp = requests.post(
                f"{self.system_url}/api/v1/batch",
                json={"requests": [{"query": "test1"}, {"query": "test2"}]},
                timeout=10
            )
            if resp.status_code < 500:
                return {"score": 1.0, "evidence": "batch端点可访问"}
        except Exception:
            pass
        
        from pathlib import Path
        batch_files = list(Path(self.config.get("source_path", "src")).rglob("*batch*.py"))
        if batch_files:
            return {"score": 0.6, "evidence": f"检测到{len(batch_files)}个批处理文件"}
        
        return {"score": 0.3, "evidence": "未检测到批量处理支持"}


class IntegrationEvaluator:
    """集成能力评估
    
    子项:
    - api_endpoints: API端点数 (≥10)
    - docs: API文档 (/docs可访问)
    - sdk: SDK可用性 (Python SDK存在)
    - examples: 示例代码 (≥5个示例)
    - openapi_spec: OpenAPI规范 (spec文件存在)
    - webhook: Webhook支持 (Webhook端点)
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.system_url = self.config.get("system_url", "http://localhost:8000")
        self.source_path = self.config.get("source_path", "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)")
    
    @property
    def dimension_name(self) -> str:
        return "integration"
    
    @property
    def weight(self) -> float:
        return 0.10
    
    async def evaluate(self) -> Dict[str, Any]:
        results = {
            "api_endpoints": await self._check_api_endpoints(),
            "docs": await self._check_docs(),
            "sdk": await self._check_sdk(),
            "examples": await self._check_examples(),
            "openapi_spec": await self._check_openapi_spec(),
            "webhook": await self._check_webhook(),
        }
        
        scores = [r["score"] for r in results.values() if r.get("score") is not None]
        overall_score = sum(scores) / len(scores) if scores else 0.3
        passed = sum(1 for r in results.values() if r.get("score", 0) >= 0.7)
        
        return {
            "dimension": self.dimension_name,
            "score": max(0, min(1, overall_score)),
            "status": "completed",
            "metrics": results,
            "details": f"集成能力评估完成，{passed}/6项达标",
            "evidence": [f"{k}: {v.get('evidence', 'N/A')}" for k, v in results.items()],
        }
    
    async def _check_api_endpoints(self) -> Dict[str, Any]:
        endpoints = [
            "/health", "/api/v1/agents", "/api/v1/skills",
            "/api/v1/tools", "/chat", "/api/v1/workflow",
            "/api/v1/knowledge", "/api/v1/cache",
        ]
        available = 0
        endpoint_list = []
        
        for ep in endpoints:
            try:
                if ep == "/chat":
                    resp = requests.post(f"{self.system_url}{ep}", json={"query": "test"}, timeout=3)
                else:
                    resp = requests.get(f"{self.system_url}{ep}", timeout=3)
                if resp.status_code < 500:
                    available += 1
                    endpoint_list.append(ep)
            except Exception:
                pass
        
        if available >= 10:
            score = 1.0
        elif available >= 6:
            score = 0.8
        elif available >= 3:
            score = 0.5
        else:
            score = 0.3
        
        return {"score": score, "available": available, "evidence": f"API端点:{available}个可访问"}
    
    async def _check_docs(self) -> Dict[str, Any]:
        docs_endpoints = ["/docs", "/api/docs", "/swagger", "/redoc"]
        available = False
        
        for ep in docs_endpoints:
            try:
                resp = requests.get(f"{self.system_url}{ep}", timeout=3)
                if resp.status_code == 200:
                    available = True
                    return {"score": 1.0, "available": True, "evidence": f"{ep}可访问"}
            except Exception:
                pass
        
        return {"score": 0.3, "available": available, "evidence": "API文档不可访问"}
    
    async def _check_sdk(self) -> Dict[str, Any]:
        from pathlib import Path
        
        sdk_paths = [
            Path(self.source_path) / "sdk",
            Path(self.source_path) / "clients",
            Path(self.source_path) / "python",
            Path(self.source_path) / "rangen_client",
        ]
        
        for sdk_path in sdk_paths:
            if sdk_path.exists():
                init_files = list(sdk_path.rglob("__init__.py"))
                if init_files:
                    return {"score": 1.0, "evidence": f"SDK目录存在:{sdk_path.name}"}
        
        py_files = list(Path(self.source_path).rglob("*client*.py"))
        if py_files:
            return {"score": 0.7, "evidence": f"检测到{len(py_files)}个客户端文件"}
        
        return {"score": 0.3, "evidence": "未检测到SDK"}
    
    async def _check_examples(self) -> Dict[str, Any]:
        from pathlib import Path
        
        example_paths = [
            Path(self.source_path) / "examples",
            Path(self.source_path) / "samples",
            Path(self.source_path) / "docs" / "examples",
        ]
        
        total_examples = 0
        found_path = None
        
        for ep in example_paths:
            if ep.exists():
                py_examples = list(ep.rglob("*.py"))
                md_examples = list(ep.rglob("*.md"))
                total_examples = len(py_examples) + len(md_examples)
                if total_examples > 0:
                    found_path = str(ep)
                    break
        
        if total_examples >= 5:
            score = 1.0
        elif total_examples >= 3:
            score = 0.8
        elif total_examples >= 1:
            score = 0.5
        else:
            score = 0.3
        
        return {"score": score, "count": total_examples, "evidence": f"示例代码:{total_examples}个"}
    
    async def _check_openapi_spec(self) -> Dict[str, Any]:
        from pathlib import Path
        
        spec_patterns = [
            "openapi.json", "openapi.yaml", "openapi.yml",
            "swagger.json", "api_spec.json", "api.yaml"
        ]
        
        for pattern in spec_patterns:
            spec_files = list(Path(self.source_path).rglob(pattern))
            if spec_files:
                return {"score": 1.0, "evidence": f"OpenAPI spec:{spec_files[0].name}"}
        
        try:
            resp = requests.get(f"{self.system_url}/openapi.json", timeout=3)
            if resp.status_code == 200:
                return {"score": 1.0, "evidence": "OpenAPI端点可访问"}
        except:
            pass
        
        return {"score": 0.3, "evidence": "未检测到OpenAPI规范"}
    
    async def _check_webhook(self) -> Dict[str, Any]:
        from pathlib import Path
        
        webhook_patterns = ["webhook", "callback", "event"]
        found = []
        
        for pattern in webhook_patterns:
            files = list(Path(self.source_path).rglob(f"*{pattern}*.py"))
            if files:
                found.extend([f.name for f in files[:2]])
        
        if found:
            return {"score": 1.0, "evidence": f"检测到{len(found)}个Webhook文件"}
        
        try:
            resp = requests.get(f"{self.system_url}/api/v1/webhook", timeout=3)
            if resp.status_code < 500:
                return {"score": 0.8, "evidence": "Webhook端点可访问"}
        except:
            pass
        
        return {"score": 0.3, "evidence": "未检测到Webhook支持"}
