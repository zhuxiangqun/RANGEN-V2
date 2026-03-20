#!/usr/bin/env python3
"""
自动化治理系统
Automated Governance System

V3核心理念：自动化治理，包括监控、告警、修复和优化。
实现自动化决策支持系统，基于数据和规则进行智能治理。
"""
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class GovernanceRulePriority(Enum):
    """治理规则优先级"""
    CRITICAL = "critical"    # 关键问题，需要立即处理
    HIGH = "high"           # 重要问题，需要尽快处理
    MEDIUM = "medium"       # 一般问题，建议处理
    LOW = "low"             # 优化建议，可选处理


class GovernanceActionType(Enum):
    """治理动作类型"""
    ALERT = "alert"              # 发送告警
    AUTOFIX = "autofix"          # 自动修复
    RECOMMENDATION = "recommendation"  # 提供建议
    ESCALATION = "escalation"    # 升级处理
    LOGGING = "logging"          # 记录日志


class GovernanceRule:
    """治理规则定义"""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        condition: Callable[[Dict[str, Any]], bool],
        action: Callable[[Dict[str, Any]], Dict[str, Any]],
        priority: GovernanceRulePriority = GovernanceRulePriority.MEDIUM,
        cooldown_seconds: int = 300,
        enabled: bool = True
    ):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.condition = condition
        self.action = action
        self.priority = priority
        self.cooldown_seconds = cooldown_seconds
        self.enabled = enabled
        self.last_triggered: Optional[float] = None
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """检查是否应该触发规则"""
        if not self.enabled:
            return False
        
        # 检查冷却时间
        if self.last_triggered and (time.time() - self.last_triggered < self.cooldown_seconds):
            return False
        
        # 检查条件
        try:
            return self.condition(context)
        except Exception as e:
            logger.error(f"规则条件检查失败 {self.rule_id}: {e}")
            return False
    
    async def execute(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """执行规则动作"""
        if not self.should_trigger(context):
            return None
        
        try:
            result = self.action(context)
            self.last_triggered = time.time()
            logger.info(f"治理规则执行成功: {self.name} (ID: {self.rule_id})")
            return result
        except Exception as e:
            logger.error(f"治理规则执行失败 {self.rule_id}: {e}")
            return None


class AutomatedGovernanceSystem:
    """自动化治理系统"""
    
    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval_seconds = check_interval_seconds
        self.rules: Dict[str, GovernanceRule] = {}
        self.running = False
        self.check_task: Optional[asyncio.Task] = None
        self.initialize_default_rules()
        logger.info("自动化治理系统初始化完成")
    
    def initialize_default_rules(self):
        """初始化默认治理规则"""
        # V3遵从性检查规则
        self.add_rule(GovernanceRule(
            rule_id="v3_compliance_low",
            name="V3遵从性过低",
            description="系统V3遵从性分数低于阈值",
            condition=self._condition_v3_compliance_low,
            action=self._action_v3_compliance_alert,
            priority=GovernanceRulePriority.HIGH,
            cooldown_seconds=3600  # 1小时冷却
        ))
        
        # 系统健康检查规则
        self.add_rule(GovernanceRule(
            rule_id="system_health_degraded",
            name="系统健康度下降",
            description="系统健康检查失败或性能下降",
            condition=self._condition_system_health_degraded,
            action=self._action_system_health_alert,
            priority=GovernanceRulePriority.CRITICAL,
            cooldown_seconds=300  # 5分钟冷却
        ))
        
        # Agent状态检查规则
        self.add_rule(GovernanceRule(
            rule_id="agent_unresponsive",
            name="Agent无响应",
            description="检测到Agent无响应或心跳丢失",
            condition=self._condition_agent_unresponsive,
            action=self._action_agent_recovery,
            priority=GovernanceRulePriority.HIGH,
            cooldown_seconds=600  # 10分钟冷却
        ))
        
        # 上下文管理优化规则
        self.add_rule(GovernanceRule(
            rule_id="context_bloat",
            name="上下文膨胀",
            description="检测到上下文历史过度膨胀",
            condition=self._condition_context_bloat,
            action=self._action_context_optimization,
            priority=GovernanceRulePriority.MEDIUM,
            cooldown_seconds=1800  # 30分钟冷却
        ))
        
        # 性能优化规则
        self.add_rule(GovernanceRule(
            rule_id="high_response_time",
            name="高响应时间",
            description="检测到系统响应时间过高",
            condition=self._condition_high_response_time,
            action=self._action_performance_optimization,
            priority=GovernanceRulePriority.HIGH,
            cooldown_seconds=900  # 15分钟冷却
        ))
        
        self.add_rule(GovernanceRule(
            rule_id="high_error_rate",
            name="高错误率",
            description="检测到系统错误率过高",
            condition=self._condition_high_error_rate,
            action=self._action_performance_optimization,
            priority=GovernanceRulePriority.CRITICAL,
            cooldown_seconds=600  # 10分钟冷却
        ))
        
        # 资源优化规则
        self.add_rule(GovernanceRule(
            rule_id="high_cpu_usage",
            name="高CPU使用率",
            description="检测到CPU使用率过高",
            condition=self._condition_high_cpu_usage,
            action=self._action_resource_optimization,
            priority=GovernanceRulePriority.MEDIUM,
            cooldown_seconds=1200  # 20分钟冷却
        ))
        
        self.add_rule(GovernanceRule(
            rule_id="high_memory_usage",
            name="高内存使用率",
            description="检测到内存使用率过高",
            condition=self._condition_high_memory_usage,
            action=self._action_resource_optimization,
            priority=GovernanceRulePriority.MEDIUM,
            cooldown_seconds=1200  # 20分钟冷却
        ))
        
        # 安全合规规则
        self.add_rule(GovernanceRule(
            rule_id="security_violation",
            name="安全沙箱违规",
            description="检测到安全沙箱违规",
            condition=self._condition_security_violations,
            action=self._action_security_alert,
            priority=GovernanceRulePriority.CRITICAL,
            cooldown_seconds=300  # 5分钟冷却
        ))
        
        # 自进化建议规则
        self.add_rule(GovernanceRule(
            rule_id="evolution_suggestion",
            name="自进化建议",
            description="检测到自进化引擎的改进建议",
            condition=self._condition_evolution_suggestions,
            action=self._action_evolution_implementation,
            priority=GovernanceRulePriority.LOW,
            cooldown_seconds=3600  # 1小时冷却
        ))
        
        logger.info(f"初始化了{len(self.rules)}个默认治理规则")
    
    def add_rule(self, rule: GovernanceRule):
        """添加治理规则"""
        self.rules[rule.rule_id] = rule
    
    def remove_rule(self, rule_id: str):
        """移除治理规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
    
    async def collect_system_context(self) -> Dict[str, Any]:
        """收集系统上下文信息"""
        context = {
            "timestamp": datetime.now().isoformat(),
            "system_time": time.time(),
            "v3_compliance": await self._get_v3_compliance_data(),
            "system_health": await self._get_system_health_data(),
            "agent_status": await self._get_agent_status_data(),
            "context_metrics": await self._get_context_metrics(),
            "performance_metrics": await self._get_performance_metrics()
        }
        return context
    
    async def _get_v3_compliance_data(self) -> Dict[str, Any]:
        """获取V3遵从性数据"""
        try:
            from src.core.v3_compliance_checker import V3ComplianceChecker
            checker = V3ComplianceChecker()
            report = checker.check_all_principles()
            return report
        except Exception as e:
            logger.warning(f"获取V3遵从性数据失败: {e}")
            return {"error": str(e), "overall_score": 0.0}
    
    async def _get_system_health_data(self) -> Dict[str, Any]:
        """获取系统健康数据"""
        try:
            # 这里可以集成现有的健康检查系统
            return {
                "status": "healthy",  # 假设健康
                "checks_passed": 5,
                "checks_failed": 0,
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"获取系统健康数据失败: {e}")
            return {"status": "unknown", "error": str(e)}
    
    async def _get_agent_status_data(self) -> Dict[str, Any]:
        """获取Agent状态数据"""
        try:
            # 这里可以集成现有的Agent状态监控
            return {
                "total_agents": 5,
                "active_agents": 5,
                "unresponsive_agents": 0,
                "last_heartbeat_check": datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"获取Agent状态数据失败: {e}")
            return {"total_agents": 0, "active_agents": 0, "error": str(e)}
    
    async def _get_context_metrics(self) -> Dict[str, Any]:
        """获取上下文指标"""
        try:
            # 这里可以集成上下文管理器指标
            return {
                "average_context_size": 50,
                "context_compression_rate": 0.2,
                "topic_switch_count": 3,
                "archived_contexts": 10
            }
        except Exception as e:
            logger.warning(f"获取上下文指标失败: {e}")
            return {"error": str(e)}
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            # 这里可以集成现有的指标服务
            return {
                "response_time_ms": 150.5,
                "requests_per_second": 10.2,
                "error_rate_percent": 0.5,
                "cpu_usage_percent": 25.0,
                "memory_usage_percent": 40.0
            }
        except Exception as e:
            logger.warning(f"获取性能指标失败: {e}")
            return {"error": str(e)}
    
    # 规则条件函数
    def _condition_v3_compliance_low(self, context: Dict[str, Any]) -> bool:
        """V3遵从性过低条件"""
        v3_data = context.get("v3_compliance", {})
        overall_score = v3_data.get("overall_score", 1.0)
        return overall_score < 0.5  # 低于50%阈值
    
    def _condition_system_health_degraded(self, context: Dict[str, Any]) -> bool:
        """系统健康度下降条件"""
        health_data = context.get("system_health", {})
        status = health_data.get("status", "healthy")
        checks_failed = health_data.get("checks_failed", 0)
        return status != "healthy" or checks_failed > 0
    
    def _condition_agent_unresponsive(self, context: Dict[str, Any]) -> bool:
        """Agent无响应条件"""
        agent_data = context.get("agent_status", {})
        unresponsive = agent_data.get("unresponsive_agents", 0)
        total = agent_data.get("total_agents", 1)
        return unresponsive > 0 and (unresponsive / total) > 0.2  # 超过20%的Agent无响应
    
    def _condition_context_bloat(self, context: Dict[str, Any]) -> bool:
        """上下文膨胀条件"""
        context_metrics = context.get("context_metrics", {})
        avg_size = context_metrics.get("average_context_size", 0)
        return avg_size > 100  # 平均上下文大小超过100条消息
    
    # 规则动作函数
    def _action_v3_compliance_alert(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """V3遵从性告警动作"""
        v3_data = context.get("v3_compliance", {})
        overall_score = v3_data.get("overall_score", 0.0)
        
        alert_message = f"V3遵从性分数过低: {overall_score:.2f} (阈值: 0.5)"
        
        # 获取改进建议
        recommendations = []
        summary = v3_data.get("summary", {})
        for improvement in summary.get("critical_improvements", []):
            recommendations.append(improvement)
        for weakness in summary.get("weaknesses", []):
            recommendations.append(weakness)
        
        return {
            "action_type": GovernanceActionType.ALERT.value,
            "rule_id": "v3_compliance_low",
            "message": alert_message,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "overall_score": overall_score,
                "recommendations": recommendations[:3]  # 最多3条建议
            },
            "recommended_actions": [
                "检查V3遵从性报告详情",
                "根据建议优化系统实现",
                "重新运行V3遵从性检查"
            ]
        }
    
    def _action_system_health_alert(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """系统健康告警动作"""
        health_data = context.get("system_health", {})
        
        return {
            "action_type": GovernanceActionType.ALERT.value,
            "rule_id": "system_health_degraded",
            "message": "系统健康度下降，需要立即检查",
            "timestamp": datetime.now().isoformat(),
            "data": health_data,
            "recommended_actions": [
                "检查系统日志",
                "验证服务依赖",
                "重启受影响的服务"
            ]
        }
    
    def _action_agent_recovery(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Agent恢复动作"""
        agent_data = context.get("agent_status", {})
        
        return {
            "action_type": GovernanceActionType.RECOMMENDATION.value,
            "rule_id": "agent_unresponsive",
            "message": "检测到Agent无响应，建议检查Agent状态",
            "timestamp": datetime.now().isoformat(),
            "data": agent_data,
            "recommended_actions": [
                "检查Agent心跳监控",
                "重启无响应的Agent",
                "检查Agent配置和依赖"
            ]
        }
    
    def _action_context_optimization(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """上下文优化动作"""
        context_metrics = context.get("context_metrics", {})
        avg_size = context_metrics.get("average_context_size", 0)
        
        return {
            "action_type": GovernanceActionType.RECOMMENDATION.value,
            "rule_id": "context_bloat",
            "message": f"检测到上下文膨胀，平均大小: {avg_size}条消息",
            "timestamp": datetime.now().isoformat(),
            "data": context_metrics,
            "recommended_actions": [
                "调整智能遗忘阈值",
                "优化上下文总结策略",
                "增加上下文归档频率"
            ]
        }
    
    # 新增规则条件函数
    def _condition_high_response_time(self, context: Dict[str, Any]) -> bool:
        """高响应时间条件"""
        performance_metrics = context.get("performance_metrics", {})
        response_time = performance_metrics.get("response_time_ms", 0)
        return response_time > 500  # 响应时间超过500ms
    
    def _condition_high_error_rate(self, context: Dict[str, Any]) -> bool:
        """高错误率条件"""
        performance_metrics = context.get("performance_metrics", {})
        error_rate = performance_metrics.get("error_rate_percent", 0)
        return error_rate > 5.0  # 错误率超过5%
    
    def _condition_high_cpu_usage(self, context: Dict[str, Any]) -> bool:
        """高CPU使用率条件"""
        performance_metrics = context.get("performance_metrics", {})
        cpu_usage = performance_metrics.get("cpu_usage_percent", 0)
        return cpu_usage > 80.0  # CPU使用率超过80%
    
    def _condition_high_memory_usage(self, context: Dict[str, Any]) -> bool:
        """高内存使用率条件"""
        performance_metrics = context.get("performance_metrics", {})
        memory_usage = performance_metrics.get("memory_usage_percent", 0)
        return memory_usage > 85.0  # 内存使用率超过85%
    
    def _condition_security_violations(self, context: Dict[str, Any]) -> bool:
        """安全违规条件"""
        # 这里可以集成安全沙箱的违规数据
        # 当前为模拟实现
        return False  # 默认没有安全违规
    
    def _condition_evolution_suggestions(self, context: Dict[str, Any]) -> bool:
        """自进化建议条件"""
        # 这里可以集成自进化引擎的建议数据
        # 当前为模拟实现
        return False  # 默认没有新建议
    
    # 新增规则动作函数
    def _action_performance_optimization(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """性能优化动作"""
        performance_metrics = context.get("performance_metrics", {})
        response_time = performance_metrics.get("response_time_ms", 0)
        error_rate = performance_metrics.get("error_rate_percent", 0)
        
        message = "检测到性能问题"
        if response_time > 500:
            message = f"响应时间过高: {response_time}ms"
        elif error_rate > 5.0:
            message = f"错误率过高: {error_rate}%"
        
        return {
            "action_type": GovernanceActionType.RECOMMENDATION.value,
            "rule_id": "performance_issue",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": performance_metrics,
            "recommended_actions": [
                "检查系统负载",
                "优化数据库查询",
                "增加缓存策略",
                "调整并发设置"
            ]
        }
    
    def _action_resource_optimization(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """资源优化动作"""
        performance_metrics = context.get("performance_metrics", {})
        cpu_usage = performance_metrics.get("cpu_usage_percent", 0)
        memory_usage = performance_metrics.get("memory_usage_percent", 0)
        
        message = "检测到资源使用问题"
        if cpu_usage > 80.0:
            message = f"CPU使用率过高: {cpu_usage}%"
        elif memory_usage > 85.0:
            message = f"内存使用率过高: {memory_usage}%"
        
        return {
            "action_type": GovernanceActionType.RECOMMENDATION.value,
            "rule_id": "resource_issue",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": performance_metrics,
            "recommended_actions": [
                "优化算法复杂度",
                "检查内存泄漏",
                "增加系统资源",
                "优化资源配置"
            ]
        }
    
    def _action_security_alert(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """安全告警动作"""
        return {
            "action_type": GovernanceActionType.ALERT.value,
            "rule_id": "security_violation",
            "message": "检测到安全沙箱违规",
            "timestamp": datetime.now().isoformat(),
            "data": {},
            "recommended_actions": [
                "检查安全审计日志",
                "审查工具执行权限",
                "更新安全策略",
                "隔离可疑活动"
            ]
        }
    
    def _action_evolution_implementation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """自进化实施动作"""
        return {
            "action_type": GovernanceActionType.RECOMMENDATION.value,
            "rule_id": "evolution_suggestion",
            "message": "自进化引擎生成新的改进建议",
            "timestamp": datetime.now().isoformat(),
            "data": {},
            "recommended_actions": [
                "查看自进化报告",
                "评估改进建议",
                "实施高ROI改进",
                "跟踪改进效果"
            ]
        }
    
    async def run_governance_check(self) -> List[Dict[str, Any]]:
        """运行一次治理检查"""
        logger.info("开始治理检查...")
        context = await self.collect_system_context()
        actions_taken = []
        
        # 评估所有规则
        for rule_id, rule in self.rules.items():
            try:
                action_result = await rule.execute(context)
                if action_result:
                    actions_taken.append(action_result)
                    logger.info(f"治理规则触发: {rule.name} - {action_result.get('message', '')}")
            except Exception as e:
                logger.error(f"规则执行异常 {rule_id}: {e}")
        
        logger.info(f"治理检查完成，触发了{len(actions_taken)}个动作")
        return actions_taken
    
    async def start(self):
        """启动自动化治理系统"""
        if self.running:
            logger.warning("自动化治理系统已经在运行中")
            return
        
        self.running = True
        logger.info("启动自动化治理系统...")
        
        async def governance_loop():
            while self.running:
                try:
                    await self.run_governance_check()
                except Exception as e:
                    logger.error(f"治理检查失败: {e}")
                
                # 等待下一次检查
                await asyncio.sleep(self.check_interval_seconds)
        
        self.check_task = asyncio.create_task(governance_loop())
        logger.info(f"自动化治理系统已启动，检查间隔: {self.check_interval_seconds}秒")
    
    async def stop(self):
        """停止自动化治理系统"""
        if not self.running:
            return
        
        self.running = False
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("自动化治理系统已停止")
    
    async def get_governance_status(self) -> Dict[str, Any]:
        """获取治理系统状态"""
        return {
            "running": self.running,
            "rule_count": len(self.rules),
            "check_interval_seconds": self.check_interval_seconds,
            "enabled_rules": [rule_id for rule_id, rule in self.rules.items() if rule.enabled],
            "last_check_time": datetime.now().isoformat() if self.running else "系统未运行"
        }


# 全局实例和便捷函数
_governance_system: Optional[AutomatedGovernanceSystem] = None

def get_automated_governance_system() -> AutomatedGovernanceSystem:
    """获取自动化治理系统实例"""
    global _governance_system
    if _governance_system is None:
        _governance_system = AutomatedGovernanceSystem()
    return _governance_system

async def start_automated_governance(check_interval_seconds: int = 60):
    """启动自动化治理系统（便捷函数）"""
    system = get_automated_governance_system()
    await system.start()

async def stop_automated_governance():
    """停止自动化治理系统（便捷函数）"""
    system = get_automated_governance_system()
    await system.stop()

async def run_governance_check() -> List[Dict[str, Any]]:
    """运行一次治理检查（便捷函数）"""
    system = get_automated_governance_system()
    return await system.run_governance_check()


if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    async def test_governance():
        print("=" * 60)
        print("测试自动化治理系统")
        print("=" * 60)
        
        system = AutomatedGovernanceSystem(check_interval_seconds=5)
        
        # 运行一次检查
        print("运行治理检查...")
        actions = await system.run_governance_check()
        
        print(f"触发了{len(actions)}个动作:")
        for action in actions:
            print(f"  - {action.get('message', '无消息')}")
        
        print("\n治理系统状态:")
        status = await system.get_governance_status()
        print(f"  规则数量: {status['rule_count']}")
        print(f"  启用的规则: {len(status['enabled_rules'])}")
        
        print("=" * 60)
        print("✅ 自动化治理系统测试完成")
        print("=" * 60)
    
    asyncio.run(test_governance())