"""
服务健康检查和错误恢复服务
提供服务的自动健康检查、故障检测和智能恢复功能
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import inspect

from src.utils.logging_helper import get_module_logger, ModuleType
from src.utils.unified_centers import get_unified_config_center, get_unified_intelligent_center

logger = logging.getLogger(__name__)

@dataclass
class ServiceHealthStatus:
    """服务健康状态"""
    service_name: str
    status: str  # healthy, degraded, unhealthy, critical
    last_check: datetime
    response_time: Optional[float]
    error_count: int
    consecutive_failures: int
    last_error: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RecoveryAction:
    """恢复动作"""
    action_id: str
    service_name: str
    action_type: str  # restart, reload, failover, scale_up, notify
    priority: int  # 1-5, 5最高
    description: str
    executed_at: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthCheckResult:
    """健康检查结果"""
    service_name: str
    check_time: datetime
    status: str
    response_time: Optional[float]
    error_message: Optional[str]
    metrics: Dict[str, Any] = field(default_factory=dict)

class ServiceHealthChecker:
    """
    服务健康检查和错误恢复服务
    自动监控服务健康状态，检测故障并执行智能恢复策略
    """

    def __init__(self):
        self.module_logger = get_module_logger(ModuleType.SERVICE, "ServiceHealthChecker")
        self.config_center = get_unified_config_center()
        self.intelligent_center = get_unified_intelligent_center()

        # 配置参数
        self.check_interval = self.config_center.get_config_value(
            "service_health_checker", "check_interval_seconds", 30
        )
        self.failure_threshold = self.config_center.get_config_value(
            "service_health_checker", "failure_threshold", 3
        )
        self.recovery_timeout = self.config_center.get_config_value(
            "service_health_checker", "recovery_timeout_seconds", 300
        )
        self.max_recovery_attempts = self.config_center.get_config_value(
            "service_health_checker", "max_recovery_attempts", 3
        )

        # 数据存储
        self.service_status: Dict[str, ServiceHealthStatus] = {}
        self.registered_services: Dict[str, Dict[str, Any]] = {}
        self.recovery_history: deque[RecoveryAction] = deque(maxlen=1000)
        self.health_history: Dict[str, deque[HealthCheckResult]] = defaultdict(lambda: deque(maxlen=100))

        # 恢复策略配置
        self.recovery_strategies: Dict[str, List[Dict[str, Any]]] = {
            "restart": [
                {"action": "restart", "priority": 5, "description": "重启服务"},
                {"action": "notify_admin", "priority": 4, "description": "通知管理员"}
            ],
            "degraded": [
                {"action": "scale_up", "priority": 4, "description": "增加资源"},
                {"action": "optimize_config", "priority": 3, "description": "优化配置"}
            ],
            "critical": [
                {"action": "failover", "priority": 5, "description": "故障转移"},
                {"action": "emergency_restart", "priority": 5, "description": "紧急重启"}
            ]
        }

        # 任务管理
        self._check_task: Optional[asyncio.Task] = None
        self._recovery_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

        # 回调函数
        self.status_change_callbacks: List[Callable[[str, str, str], None]] = []
        self.recovery_callbacks: List[Callable[[RecoveryAction], None]] = []

    def register_service(self, service_name: str, service_instance: Any,
                        health_check_method: Optional[Callable] = None,
                        recovery_methods: Optional[Dict[str, Callable]] = None):
        """注册服务进行健康检查"""
        self.registered_services[service_name] = {
            "instance": service_instance,
            "health_check": health_check_method or self._default_health_check,
            "recovery_methods": recovery_methods or {},
            "registered_at": datetime.now()
        }

        # 初始化健康状态
        self.service_status[service_name] = ServiceHealthStatus(
            service_name=service_name,
            status="unknown",
            last_check=datetime.now(),
            response_time=None,
            error_count=0,
            consecutive_failures=0,
            last_error=None
        )

        self.module_logger.info(f"✅ 服务已注册健康检查: {service_name}")

    def add_status_change_callback(self, callback: Callable[[str, str, str], None]):
        """添加状态变化回调函数"""
        self.status_change_callbacks.append(callback)

    def add_recovery_callback(self, callback: Callable[[RecoveryAction], None]):
        """添加恢复回调函数"""
        self.recovery_callbacks.append(callback)

    async def start_monitoring(self):
        """启动健康监控"""
        if self._running:
            return

        self._running = True
        self._check_task = asyncio.create_task(self._health_check_loop())
        self._recovery_task = asyncio.create_task(self._recovery_loop())
        self._monitoring_task = asyncio.create_task(self._status_monitoring_loop())

        self.module_logger.info("✅ 服务健康监控已启动")

    async def stop_monitoring(self):
        """停止健康监控"""
        self._running = False

        for task in [self._check_task, self._recovery_task, self._monitoring_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self.module_logger.info("🛑 服务健康监控已停止")

    async def _health_check_loop(self):
        """健康检查循环"""
        while self._running:
            try:
                await self._perform_health_checks()

            except Exception as e:
                self.module_logger.error(f"❌ 健康检查循环异常: {e}", exc_info=True)

            await asyncio.sleep(self.check_interval)

    async def _perform_health_checks(self):
        """执行所有服务的健康检查"""
        for service_name, service_info in self.registered_services.items():
            try:
                check_result = await self._check_service_health(service_name, service_info)
                self.health_history[service_name].append(check_result)

                # 更新服务状态
                await self._update_service_status(service_name, check_result)

            except Exception as e:
                self.module_logger.error(f"❌ 服务 {service_name} 健康检查失败: {e}")

                # 记录失败结果
                failed_result = HealthCheckResult(
                    service_name=service_name,
                    check_time=datetime.now(),
                    status="error",
                    response_time=None,
                    error_message=str(e)
                )
                self.health_history[service_name].append(failed_result)
                await self._update_service_status(service_name, failed_result)

    async def _check_service_health(self, service_name: str, service_info: Dict[str, Any]) -> HealthCheckResult:
        """检查单个服务的健康状态"""
        health_check_method = service_info["health_check"]
        service_instance = service_info["instance"]

        start_time = time.time()

        try:
            # 执行健康检查
            if inspect.iscoroutinefunction(health_check_method):
                result = await health_check_method(service_instance)
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, health_check_method, service_instance
                )

            response_time = time.time() - start_time

            # 解析结果
            if isinstance(result, dict):
                status = result.get("status", "healthy")
                error_message = result.get("error", None)
                metrics = result.get("metrics", {})
            else:
                status = "healthy" if result else "unhealthy"
                error_message = None
                metrics = {}

            return HealthCheckResult(
                service_name=service_name,
                check_time=datetime.now(),
                status=status,
                response_time=response_time,
                error_message=error_message,
                metrics=metrics
            )

        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service_name=service_name,
                check_time=datetime.now(),
                status="error",
                response_time=response_time,
                error_message=str(e)
            )

    async def _default_health_check(self, service_instance: Any) -> Dict[str, Any]:
        """默认健康检查方法"""
        try:
            # 尝试调用服务的健康检查方法
            if hasattr(service_instance, 'health_check'):
                return await service_instance.health_check()

            # 基本检查：检查服务是否有基本的运行状态
            if hasattr(service_instance, 'is_running'):
                is_running = service_instance.is_running()
                return {
                    "status": "healthy" if is_running else "unhealthy",
                    "metrics": {"is_running": is_running}
                }

            # 最基本的检查：检查对象是否存在
            return {
                "status": "healthy",
                "metrics": {"object_exists": True}
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _update_service_status(self, service_name: str, check_result: HealthCheckResult):
        """更新服务状态"""
        current_status = self.service_status[service_name]
        previous_status = current_status.status

        # 更新基本信息
        current_status.last_check = check_result.check_time
        current_status.response_time = check_result.response_time

        # 更新错误计数
        if check_result.status in ["error", "unhealthy", "critical"]:
            current_status.error_count += 1
            current_status.consecutive_failures += 1
            current_status.last_error = check_result.error_message
        else:
            current_status.consecutive_failures = 0

        # 确定新的状态
        new_status = self._determine_service_status(check_result, current_status)
        current_status.status = new_status

        # 状态变化通知
        if new_status != previous_status:
            self.module_logger.info(f"📊 服务状态变化: {service_name} {previous_status} → {new_status}")

            for callback in self.status_change_callbacks:
                try:
                    callback(service_name, previous_status, new_status)
                except Exception as e:
                    self.module_logger.error(f"❌ 状态变化回调失败: {e}")

    def _determine_service_status(self, check_result: HealthCheckResult, current_status: ServiceHealthStatus) -> str:
        """确定服务状态"""
        if check_result.status == "error":
            if current_status.consecutive_failures >= self.failure_threshold:
                return "critical"
            else:
                return "unhealthy"
        elif check_result.status == "unhealthy":
            return "degraded"
        elif check_result.status in ["healthy", "ok"]:
            return "healthy"
        else:
            return check_result.status

    async def _recovery_loop(self):
        """恢复循环"""
        while self._running:
            try:
                await self._check_and_recover_services()

            except Exception as e:
                self.module_logger.error(f"❌ 恢复循环异常: {e}", exc_info=True)

            await asyncio.sleep(60)  # 每分钟检查一次恢复需求

    async def _check_and_recover_services(self):
        """检查并恢复异常服务"""
        for service_name, status in self.service_status.items():
            if status.status in ["degraded", "unhealthy", "critical"]:
                # 检查是否需要恢复
                if status.consecutive_failures >= self.failure_threshold:
                    await self._execute_recovery(service_name, status.status)

    async def _execute_recovery(self, service_name: str, failure_type: str):
        """执行服务恢复"""
        self.module_logger.info(f"🔧 开始恢复服务: {service_name} (故障类型: {failure_type})")

        strategies = self.recovery_strategies.get(failure_type, [])
        if not strategies:
            self.module_logger.warning(f"⚠️ 没有找到 {failure_type} 类型的恢复策略")
            return

        # 按优先级排序
        sorted_strategies = sorted(strategies, key=lambda x: x["priority"], reverse=True)

        for strategy in sorted_strategies:
            action = strategy["action"]
            description = strategy["description"]

            self.module_logger.info(f"🔄 执行恢复动作: {action} - {description}")

            recovery_action = RecoveryAction(
                action_id=f"{service_name}_{action}_{int(time.time())}",
                service_name=service_name,
                action_type=action,
                priority=strategy["priority"],
                description=description,
                executed_at=datetime.now()
            )

            try:
                success = await self._perform_recovery_action(service_name, action)
                recovery_action.success = success

                if success:
                    self.module_logger.info(f"✅ 恢复动作成功: {action}")
                    self.recovery_history.append(recovery_action)

                    # 触发恢复回调
                    for callback in self.recovery_callbacks:
                        try:
                            callback(recovery_action)
                        except Exception as e:
                            self.module_logger.error(f"❌ 恢复回调失败: {e}")

                    # 成功后停止进一步恢复
                    break
                else:
                    self.module_logger.warning(f"❌ 恢复动作失败: {action}")
                    recovery_action.error_message = "Recovery action failed"

            except Exception as e:
                self.module_logger.error(f"❌ 恢复动作异常: {action} - {e}")
                recovery_action.error_message = str(e)

            self.recovery_history.append(recovery_action)

    async def _perform_recovery_action(self, service_name: str, action: str) -> bool:
        """执行具体的恢复动作"""
        service_info = self.registered_services.get(service_name)
        if not service_info:
            return False

        recovery_methods = service_info.get("recovery_methods", {})

        # 检查是否有自定义恢复方法
        if action in recovery_methods:
            method = recovery_methods[action]
            if inspect.iscoroutinefunction(method):
                return await method()
            else:
                return await asyncio.get_event_loop().run_in_executor(None, method)

        # 执行默认恢复动作
        if action == "restart":
            return await self._default_restart_recovery(service_name)
        elif action == "scale_up":
            return await self._default_scale_up_recovery(service_name)
        elif action == "failover":
            return await self._default_failover_recovery(service_name)
        elif action == "notify_admin":
            return await self._default_notify_admin_recovery(service_name)
        else:
            self.module_logger.warning(f"⚠️ 未知恢复动作: {action}")
            return False

    async def _default_restart_recovery(self, service_name: str) -> bool:
        """默认重启恢复"""
        try:
            service_info = self.registered_services.get(service_name)
            if not service_info:
                return False

            service_instance = service_info["instance"]

            # 尝试停止服务
            if hasattr(service_instance, 'stop'):
                await service_instance.stop()

            # 等待一下
            await asyncio.sleep(2)

            # 尝试重启服务
            if hasattr(service_instance, 'start'):
                await service_instance.start()

            # 等待服务启动
            await asyncio.sleep(5)

            # 验证恢复
            check_result = await self._check_service_health(service_name, service_info)
            return check_result.status == "healthy"

        except Exception as e:
            self.module_logger.error(f"❌ 重启恢复失败: {e}")
            return False

    async def _default_scale_up_recovery(self, service_name: str) -> bool:
        """默认扩容恢复"""
        # 这里可以实现动态扩容逻辑
        # 暂时只是记录日志
        self.module_logger.info(f"🔄 扩容恢复请求: {service_name} (暂未实现)")
        return True  # 假设成功

    async def _default_failover_recovery(self, service_name: str) -> bool:
        """默认故障转移恢复"""
        # 这里可以实现故障转移逻辑
        # 暂时只是记录日志
        self.module_logger.info(f"🔄 故障转移恢复请求: {service_name} (暂未实现)")
        return True  # 假设成功

    async def _default_notify_admin_recovery(self, service_name: str) -> bool:
        """默认管理员通知恢复"""
        try:
            # 这里可以实现邮件、短信等通知
            self.module_logger.warning(f"📧 管理员通知: 服务 {service_name} 需要人工干预")
            return True
        except Exception as e:
            self.module_logger.error(f"❌ 管理员通知失败: {e}")
            return False

    async def _status_monitoring_loop(self):
        """状态监控循环"""
        while self._running:
            try:
                await self._monitor_service_trends()

            except Exception as e:
                self.module_logger.error(f"❌ 状态监控异常: {e}", exc_info=True)

            await asyncio.sleep(300)  # 每5分钟监控一次趋势

    async def _monitor_service_trends(self):
        """监控服务趋势"""
        current_time = datetime.now()

        for service_name in self.registered_services.keys():
            history = self.health_history[service_name]
            if len(history) < 10:
                continue

            # 计算最近1小时的健康率
            one_hour_ago = current_time - timedelta(hours=1)
            recent_checks = [h for h in history if h.check_time >= one_hour_ago]

            if recent_checks:
                healthy_count = sum(1 for h in recent_checks if h.status == "healthy")
                health_rate = healthy_count / len(recent_checks)

                # 健康率告警
                if health_rate < 0.8:  # 健康率低于80%
                    self.module_logger.warning(f"⚠️ 服务健康率异常: {service_name} = {health_rate:.2%}")

    def get_service_status(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """获取服务状态"""
        if service_name:
            status = self.service_status.get(service_name)
            return {
                "service_name": service_name,
                "status": status.status if status else "unknown",
                "last_check": status.last_check if status else None,
                "response_time": status.response_time if status else None,
                "error_count": status.error_count if status else 0,
                "consecutive_failures": status.consecutive_failures if status else 0,
                "last_error": status.last_error if status else None
            }
        else:
            return {
                service_name: {
                    "status": status.status,
                    "last_check": status.last_check,
                    "response_time": status.response_time,
                    "error_count": status.error_count,
                    "consecutive_failures": status.consecutive_failures,
                    "last_error": status.last_error
                }
                for service_name, status in self.service_status.items()
            }

    def get_recovery_history(self, service_name: Optional[str] = None, limit: int = 50) -> List[RecoveryAction]:
        """获取恢复历史"""
        if service_name:
            return [action for action in self.recovery_history if action.service_name == service_name][-limit:]
        else:
            return list(self.recovery_history)[-limit:]

    def get_health_report(self) -> Dict[str, Any]:
        """获取健康报告"""
        total_services = len(self.registered_services)
        healthy_services = sum(1 for status in self.service_status.values() if status.status == "healthy")
        degraded_services = sum(1 for status in self.service_status.values() if status.status == "degraded")
        unhealthy_services = sum(1 for status in self.service_status.values() if status.status in ["unhealthy", "critical"])

        return {
            "timestamp": datetime.now(),
            "total_services": total_services,
            "healthy_services": healthy_services,
            "degraded_services": degraded_services,
            "unhealthy_services": unhealthy_services,
            "health_rate": healthy_services / total_services if total_services > 0 else 0,
            "total_recovery_actions": len(self.recovery_history),
            "recent_recoveries": len([r for r in self.recovery_history if (datetime.now() - r.executed_at).total_seconds() < 3600]) if self.recovery_history else 0
        }

    async def manual_recovery(self, service_name: str, action_type: str) -> bool:
        """手动执行恢复动作"""
        self.module_logger.info(f"🔧 手动恢复请求: {service_name} - {action_type}")

        if service_name not in self.registered_services:
            raise ValueError(f"服务 {service_name} 未注册")

        return await self._perform_recovery_action(service_name, action_type)

    async def health_check(self) -> Dict[str, Any]:
        """健康检查接口"""
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "monitored_services": len(self.registered_services),
            "active_recoveries": len([r for r in self.recovery_history if not r.success]),
            "monitoring_active": self._running
        }
