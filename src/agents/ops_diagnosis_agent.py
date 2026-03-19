"""
Ops Diagnosis Agent - 运维诊断智能体

专门负责系统问题诊断和修复的Agent
"""
from typing import Dict, Any, Optional, List
import time
import asyncio
import subprocess
from src.interfaces.agent import IAgent, AgentConfig, AgentResult, ExecutionStatus
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class OpsDiagnosisAgent(IAgent):
    """
    运维诊断Agent - 专门处理系统问题诊断和修复
    
    能力：
    1. 健康检查 - 检查系统各组件状态
    2. 问题诊断 - 分析错误原因
    3. 自动修复 - 执行修复操作
    4. 状态报告 - 生成诊断报告
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="ops_diagnosis_agent",
                description="系统运维诊断Agent，负责健康检查、问题诊断和自动修复",
                version="1.0.0"
            )
        super().__init__(config)
        
        self.diagnosis_tools = {
            "check_health": self._check_health,
            "check_endpoint": self._check_endpoint,
            "restart_service": self._restart_service,
            "clear_cache": self._clear_cache,
            "check_logs": self._check_logs,
            "get_system_metrics": self._get_system_metrics,
        }
        
        logger.info("OpsDiagnosisAgent initialized")
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        if "query" not in inputs:
            return False
        return True
    
    async def execute(self, inputs: Dict[str, Any], context: Optional[Dict] = None) -> AgentResult:
        start_time = time.time()
        
        try:
            if not self.validate_inputs(inputs):
                return AgentResult(
                    agent_name=self.config.name,
                    status=ExecutionStatus.FAILED,
                    output=None,
                    execution_time=0.0,
                    error="Invalid input: 'query' is required"
                )
            
            query = inputs["query"]
            context = context or {}
            
            result = await self._diagnose_and_fix(query, context)
            
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.COMPLETED,
                output=result,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"OpsDiagnosisAgent execution failed: {e}")
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.FAILED,
                output=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _diagnose_and_fix(self, query: str, context: Dict) -> Dict[str, Any]:
        """主诊断修复逻辑"""
        steps = []
        findings = []
        
        query_lower = query.lower()
        
        # 1. 理解问题类型
        problem_type = self._identify_problem(query_lower)
        steps.append(f"问题识别: {problem_type}")
        
        # 2. 执行诊断
        if "404" in query_lower or "根路径" in query_lower or "root" in query_lower:
            finding = await self._diagnose_root_path()
            findings.append(finding)
        
        if "mcp" in query_lower:
            finding = await self._diagnose_mcp()
            findings.append(finding)
        
        if "缓存" in query_lower or "cache" in query_lower:
            finding = await self._diagnose_cache()
            findings.append(finding)
        
        if "健康" in query_lower or "health" in query_lower:
            finding = await self._diagnose_health()
            findings.append(finding)
        
        if not findings:
            finding = await self._full_diagnosis()
            findings.append(finding)
        
        # 3. 生成修复方案
        fix_plan = self._generate_fix_plan(findings, problem_type)
        steps.extend(fix_plan["steps"])
        
        # 4. 执行修复
        if fix_plan["auto_fix"]:
            for action in fix_plan["actions"]:
                result = await self._execute_action(action)
                steps.append(result)
        
        return {
            "problem_type": problem_type,
            "findings": findings,
            "fix_plan": fix_plan,
            "steps": steps,
            "status": "completed" if fix_plan["actions"] else "no_fix_needed"
        }
    
    def _identify_problem(self, query: str) -> str:
        """识别问题类型"""
        if "404" in query or "根路径" in query or "root" in query:
            return "endpoint_404"
        if "mcp" in query:
            return "mcp_offline"
        if "缓存" in query or "cache" in query:
            return "cache_issue"
        if "内存" in query or "memory" in query:
            return "memory_issue"
        if "cpu" in query:
            return "cpu_issue"
        if "健康" in query or "health" in query:
            return "health_check"
        return "unknown"
    
    async def _diagnose_root_path(self) -> Dict[str, Any]:
        """诊断根路径问题"""
        try:
            import requests
            resp = requests.get("http://localhost:8000/", timeout=5)
            if resp.status_code == 200:
                return {
                    "component": "root_path",
                    "status": "healthy",
                    "message": "根路径正常"
                }
            else:
                return {
                    "component": "root_path",
                    "status": "error",
                    "code": resp.status_code,
                    "message": f"根路径返回 {resp.status_code}",
                    "diagnosis": "API服务可能需要重启，根路径端点可能未定义",
                    "fix_required": True,
                    "fix_action": "restart_api"
                }
        except requests.exceptions.ConnectionError:
            return {
                "component": "root_path",
                "status": "offline",
                "message": "无法连接到API服务",
                "diagnosis": "API服务未运行",
                "fix_required": True,
                "fix_action": "start_api"
            }
        except Exception as e:
            return {
                "component": "root_path",
                "status": "error",
                "message": str(e),
                "diagnosis": "未知错误",
                "fix_required": True,
                "fix_action": "restart_api"
            }
    
    async def _diagnose_mcp(self) -> Dict[str, Any]:
        """诊断MCP服务"""
        try:
            import requests
            resp = requests.get(
                "http://localhost:8000/mcp/status",
                headers={"Authorization": f"Bearer {context.get('api_key', '')}"},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "healthy":
                    return {
                        "component": "mcp",
                        "status": "healthy",
                        "message": "MCP服务正常"
                    }
                else:
                    return {
                        "component": "mcp",
                        "status": "degraded",
                        "message": f"MCP服务状态: {data.get('status')}",
                        "issues": data.get("issues", []),
                        "fix_required": True,
                        "fix_action": "restart_mcp"
                    }
            else:
                return {
                    "component": "mcp",
                    "status": "error",
                    "code": resp.status_code,
                    "message": f"MCP服务返回 {resp.status_code}",
                    "fix_required": True,
                    "fix_action": "restart_mcp"
                }
        except Exception as e:
            return {
                "component": "mcp",
                "status": "offline",
                "message": str(e),
                "fix_required": True,
                "fix_action": "restart_mcp"
            }
    
    async def _diagnose_cache(self) -> Dict[str, Any]:
        """诊断缓存问题"""
        return {
            "component": "cache",
            "status": "checking",
            "message": "缓存检查",
            "fix_required": True,
            "fix_action": "clear_cache"
        }
    
    async def _diagnose_health(self) -> Dict[str, Any]:
        """全面健康检查"""
        endpoints = [
            ("/", "根路径"),
            ("/health", "健康检查"),
            ("/api/v1/agents", "Agent管理"),
        ]
        
        results = []
        for endpoint, name in endpoints:
            try:
                import requests
                resp = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                results.append({
                    "name": name,
                    "endpoint": endpoint,
                    "status": "healthy" if resp.status_code == 200 else "error",
                    "code": resp.status_code
                })
            except:
                results.append({
                    "name": name,
                    "endpoint": endpoint,
                    "status": "offline",
                    "code": None
                })
        
        healthy_count = sum(1 for r in results if r["status"] == "healthy")
        return {
            "component": "health_check",
            "status": "healthy" if healthy_count == len(results) else "degraded",
            "checks": results,
            "summary": f"{healthy_count}/{len(results)} 组件正常"
        }
    
    async def _full_diagnosis(self) -> Dict[str, Any]:
        """全面系统诊断"""
        return await self._diagnose_health()
    
    def _generate_fix_plan(self, findings: List[Dict], problem_type: str) -> Dict[str, Any]:
        """生成修复方案"""
        actions = []
        steps = []
        
        for finding in findings:
            if not finding.get("fix_required"):
                continue
            
            action = finding.get("fix_action")
            if action == "restart_api":
                actions.append({"type": "restart_api"})
                steps.append("需要重启API服务")
            elif action == "restart_mcp":
                actions.append({"type": "restart_mcp"})
                steps.append("需要重启MCP服务")
            elif action == "clear_cache":
                actions.append({"type": "clear_cache"})
                steps.append("需要清理缓存")
            elif action == "start_api":
                actions.append({"type": "start_api"})
                steps.append("需要启动API服务")
        
        return {
            "actions": actions,
            "steps": steps,
            "auto_fix": len(actions) > 0
        }
    
    async def _execute_action(self, action: Dict) -> str:
        """执行修复动作"""
        action_type = action["type"]
        
        if action_type == "restart_api":
            try:
                subprocess.run(["pkill", "-f", "server.py"], capture_output=True)
                await asyncio.sleep(2)
                subprocess.Popen(
                    ["python3", "src/api/server.py"],
                    cwd="/Users/apple/workdata/person/zy/RANGEN-main(syu-python)",
                    env={**__import__("os").environ, "PYTHONPATH": "."},
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return "✅ API服务重启命令已发送"
            except Exception as e:
                return f"❌ API服务重启失败: {str(e)}"
        
        elif action_type == "restart_mcp":
            try:
                import requests
                resp = requests.post(
                    "http://localhost:8000/mcp/restart",
                    headers={"Authorization": "Bearer test"},
                    timeout=10
                )
                if resp.status_code == 200:
                    return "✅ MCP服务重启成功"
                else:
                    return f"⚠️ MCP服务重启返回: {resp.status_code}"
            except Exception as e:
                return f"❌ MCP服务重启失败: {str(e)}"
        
        elif action_type == "clear_cache":
            try:
                import requests
                resp = requests.post(
                    "http://localhost:8000/api/v1/cache/clear",
                    headers={"Authorization": "Bearer test"},
                    timeout=10
                )
                if resp.status_code == 200:
                    return "✅ 缓存清理成功"
                else:
                    return f"⚠️ 缓存清理返回: {resp.status_code}"
            except Exception as e:
                return f"❌ 缓存清理失败: {str(e)}"
        
        elif action_type == "start_api":
            try:
                subprocess.Popen(
                    ["python3", "src/api/server.py"],
                    cwd="/Users/apple/workdata/person/zy/RANGEN-main(syu-python)",
                    env={**__import__("os").environ, "PYTHONPATH": "."},
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return "✅ API服务启动命令已发送"
            except Exception as e:
                return f"❌ API服务启动失败: {str(e)}"
        
        return f"未知动作: {action_type}"
    
    async def _check_health(self) -> Dict[str, Any]:
        """健康检查工具"""
        return await self._diagnose_health()
    
    async def _check_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """检查端点状态工具"""
        try:
            import requests
            resp = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            return {
                "endpoint": endpoint,
                "status_code": resp.status_code,
                "status": "healthy" if resp.status_code == 200 else "error"
            }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "status": "offline",
                "error": str(e)
            }
    
    async def _restart_service(self, service_name: str) -> Dict[str, Any]:
        """重启服务工具"""
        result = await self._execute_action({"type": f"restart_{service_name}"})
        return {"result": result}
    
    async def _clear_cache(self) -> Dict[str, Any]:
        """清理缓存工具"""
        result = await self._execute_action({"type": "clear_cache"})
        return {"result": result}
    
    async def _check_logs(self, lines: int = 50) -> Dict[str, Any]:
        """检查日志工具"""
        try:
            result = subprocess.run(
                ["tail", f"-n{lines}", "logs/api_server.log"],
                capture_output=True,
                text=True,
                cwd="/Users/apple/workdata/person/zy/RANGEN-main(syu-python)"
            )
            return {
                "logs": result.stdout[-5000:] if len(result.stdout) > 5000 else result.stdout,
                "error": result.stderr[-1000:] if result.stderr else None
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标工具"""
        try:
            import requests
            resp = requests.get("http://localhost:8000/health/resource", timeout=5)
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"返回状态码: {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}


# 单例获取函数
_ops_diagnosis_agent: Optional[OpsDiagnosisAgent] = None

def get_ops_diagnosis_agent() -> OpsDiagnosisAgent:
    """获取OpsDiagnosisAgent单例"""
    global _ops_diagnosis_agent
    if _ops_diagnosis_agent is None:
        _ops_diagnosis_agent = OpsDiagnosisAgent()
    return _ops_diagnosis_agent
