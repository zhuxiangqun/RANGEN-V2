"""
智能路由模块 - 自动选择执行模式

根据任务复杂度、资源情况、用户偏好自动选择:
- Lite 模式: SwarmCLI (轻量)
- Full 模式: Gateway (企业级)
"""

import re
import psutil
from enum import Enum
from typing import Literal
from dataclasses import dataclass
from pathlib import Path


class ExecutionMode(Enum):
    """执行模式"""
    LITE = "lite"      # 轻量模式 - SwarmCLI
    FULL = "full"      # 企业模式 - Gateway
    AUTO = "auto"      # 自动选择


@dataclass
class RouteContext:
    """路由上下文"""
    query: str
    user_preference: ExecutionMode = ExecutionMode.AUTO
    critical_task: bool = False
    multi_agent_required: bool = False


@dataclass
class RouteDecision:
    """路由决策结果"""
    mode: ExecutionMode
    reason: str
    confidence: float  # 0.0 - 1.0
    suggestions: list[str]


class SmartSwarmRouter:
    """
    智能路由 - 自动选择执行模式
    
    决策因素:
    1. 任务复杂度 (simple/complex/critical)
    2. 资源情况 (CPU/内存/磁盘)
    3. 用户偏好 (lite/full/auto)
    4. 任务类型 (单Agent/多Agent)
    """
    
    # 复杂度关键词
    COMPLEXITY_PATTERNS = {
        "simple": [
            r"查一下", r"搜索", r"翻译", r"解释",
            r"是什么", r"帮我看", r"写个函数",
            r"简单", r"快速", r"一条",
        ],
        "moderate": [
            r"分析", r"创建", r"实现", r"设计",
            r"优化", r"测试", r"修复",
            r"完整", r"项目",
        ],
        "complex": [
            r"完整系统", r"架构设计", r"多模块",
            r"团队协作", r"跨部门", r"长期",
            r"重构", r"重写", r"改造",
        ],
        "critical": [
            r"生产环境", r"线上", r"正式",
            r"金融", r"医疗", r"安全",
            r"交易", r"支付", r"核心",
            r"关键任务", r"不可失败",
        ],
    }
    
    # 多Agent任务关键词
    MULTI_AGENT_PATTERNS = [
        r"团队", r"多人", r"协作", r"分工",
        r"多个.*一起", r"并行", r"同时",
        r"研究团队", r"开发团队", r"投研",
        r"spawn", r"agent.*spawn",
    ]
    
    # 轻量需求关键词
    LITE_REQUIREMENT_PATTERNS = [
        r"快速", r"简单", r"轻量", r"单机",
        r"不需要", r"本地", r"一个人",
        r"swarm", r"cli",
    ]
    
    def __init__(self):
        self.swarm_available = self._check_swarm_availability()
        self.gateway_available = self._check_gateway_availability()
    
    def _check_swarm_availability(self) -> bool:
        """检查 SwarmCLI 是否可用"""
        # 检查 rangenswarm 命令是否存在
        import shutil
        return shutil.which("rangenswarm") is not None or Path("src/swarm").exists()
    
    def _check_gateway_availability(self) -> bool:
        """检查 Gateway 服务是否可用"""
        import requests
        try:
            resp = requests.get("http://localhost:8000/health", timeout=2)
            return resp.status_code == 200
        except:
            return False
    
    def route(self, context: RouteContext) -> RouteDecision:
        """
        路由决策 - 自动选择执行模式
        
        Args:
            context: 路由上下文
            
        Returns:
            RouteDecision: 路由决策结果
        """
        # 1. 用户偏好优先
        if context.user_preference != ExecutionMode.AUTO:
            return self._decide_by_preference(context)
        
        # 2. 关键任务强制使用 Full
        if context.critical_task or self._is_critical(context.query):
            return RouteDecision(
                mode=ExecutionMode.FULL,
                reason="关键任务，启用企业级保障",
                confidence=0.95,
                suggestions=["启用审计日志", "启用人工审批", "启用回滚机制"]
            )
        
        # 3. 多Agent任务判断
        if context.multi_agent_required or self._requires_multi_agent(context.query):
            return self._decide_multi_agent(context)
        
        # 4. 复杂度评估
        complexity = self._assess_complexity(context.query)
        
        # 5. 资源检测
        resources = self._detect_resources()
        
        # 6. 综合决策
        return self._综合决策(complexity, resources, context)
    
    def _decide_by_preference(self, context: RouteContext) -> RouteDecision:
        """根据用户偏好决策"""
        mode = context.user_preference
        return RouteDecision(
            mode=mode,
            reason=f"用户偏好: {mode.value}",
            confidence=1.0,
            suggestions=[]
        )
    
    def _is_critical(self, query: str) -> bool:
        """判断是否为关键任务"""
        for pattern in self.COMPLEXITY_PATTERNS["critical"]:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    def _requires_multi_agent(self, query: str) -> bool:
        """判断是否需要多Agent"""
        for pattern in self.MULTI_AGENT_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    def _assess_complexity(self, query: str) -> Literal["simple", "moderate", "complex"]:
        """评估任务复杂度"""
        scores = {"simple": 0, "moderate": 0, "complex": 0}
        
        for level, patterns in self.COMPLEXITY_PATTERNS.items():
            if level == "critical":
                continue
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    scores[level] += 1
        
        # 返回得分最高的级别
        return max(scores, key=scores.get)
    
    def _detect_resources(self) -> dict:
        """检测系统资源"""
        memory = psutil.virtual_memory()
        
        return {
            "memory_gb": memory.total / (1024**3),
            "memory_available_gb": memory.available / (1024**3),
            "memory_percent": memory.percent,
            "cpu_count": psutil.cpu_count(),
            "disk_free_gb": psutil.disk_usage("/").free / (1024**3),
        }
    
    def _decide_multi_agent(self, context: RouteContext) -> RouteDecision:
        """多Agent任务决策"""
        resources = self._detect_resources()
        
        # 资源充足 + 需要多Agent = Full 模式
        if resources["memory_available_gb"] > 4:
            return RouteDecision(
                mode=ExecutionMode.FULL,
                reason="多Agent协作任务 + 资源充足，启用企业级编排",
                confidence=0.85,
                suggestions=["启用 MultiAgentCoordinator", "启用 EventBus"]
            )
        
        # 资源不足 = Lite 模式 (Swarm 本身很轻量)
        return RouteDecision(
            mode=ExecutionMode.LITE,
            reason="多Agent协作任务 + 资源有限，启用轻量级 Swarm",
            confidence=0.80,
            suggestions=["使用 SwarmCoordinator", "使用 FileInbox"]
        )
    
    def _综合决策(self, complexity: str, resources: dict, context: RouteContext) -> RouteDecision:
        """综合决策"""
        
        # 检查是否明确需要轻量
        for pattern in self.LITE_REQUIREMENT_PATTERNS:
            if re.search(pattern, context.query, re.IGNORECASE):
                return RouteDecision(
                    mode=ExecutionMode.LITE,
                    reason=f"明确要求轻量模式",
                    confidence=0.90,
                    suggestions=["使用 SwarmCLI", "使用本地执行"]
                )
        
        # 简单任务 + 资源一般 = Lite
        if complexity == "simple":
            return RouteDecision(
                mode=ExecutionMode.LITE,
                reason="简单任务，启用轻量级执行",
                confidence=0.85,
                suggestions=["使用 SwarmCLI", "启动单个 Agent"]
            )
        
        # 复杂任务 + 资源充足 = Full
        if complexity == "complex" and resources["memory_available_gb"] > 4:
            return RouteDecision(
                mode=ExecutionMode.FULL,
                reason="复杂任务 + 资源充足，启用企业级编排",
                confidence=0.80,
                suggestions=["启用 LangGraph", "启用 SOP", "启用审计"]
            )
        
        # 中等任务 = 默认 Lite (更轻更快)
        return RouteDecision(
            mode=ExecutionMode.LITE,
            reason="中等复杂度任务，默认轻量级执行",
            confidence=0.75,
            suggestions=["使用 SwarmCLI", "可升级为 Full 模式"]
        )


# 全局单例
_router: SmartSwarmRouter | None = None


def get_router() -> SmartSwarmRouter:
    """获取路由实例"""
    global _router
    if _router is None:
        _router = SmartSwarmRouter()
    return _router


def auto_route(query: str, **kwargs) -> RouteDecision:
    """
    自动路由 - 一行调用
    
    Usage:
        decision = auto_route("帮我做一个完整的电商系统")
        if decision.mode == ExecutionMode.LITE:
            # 使用 Swarm
        else:
            # 使用 Gateway
    """
    context = RouteContext(query=query, **kwargs)
    return get_router().route(context)


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 测试路由
    test_cases = [
        "帮我查一下今天的天气",
        "写一个Python函数",
        "做一个完整的用户管理系统",
        "帮我优化这个神经网络的架构",
        "使用轻量模式处理",
        "需要多个研究员一起协作研究",
    ]
    
    router = SmartSwarmRouter()
    
    for query in test_cases:
        decision = router.route(RouteContext(query=query))
        print(f"\n📝 Query: {query}")
        print(f"   Mode: {decision.mode.value}")
        print(f"   Reason: {decision.reason}")
        print(f"   Confidence: {decision.confidence:.0%}")
