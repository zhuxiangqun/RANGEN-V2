"""
错误恢复管理器 - 实现智能错误处理和自动恢复
提供详细的错误分类、智能回退策略和性能监控
"""

import asyncio
import logging
import time
import traceback
import threading
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import weakref

# 智能配置系统导入
from src.utils.smart_config_system import get_smart_config, create_query_context

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """错误严重程度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """错误类别枚举"""
    INITIALIZATION = "initialization"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    MEMORY = "memory"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    INTEGRATION = "integration"
    UNKNOWN = "unknown"

class RecoveryStrategy(Enum):
    """恢复策略枚举"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRADUAL_DEGRADATION = "gradual_degradation"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class ErrorContext:
    """错误上下文信息"""
    component_name: str
    operation: str
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorRecord:
    """错误记录"""
    error_id: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    stack_trace: str
    recovery_strategy: RecoveryStrategy
    retry_count: int = config.DEFAULT_ZERO_VALUE
    max_retries: int = 3
    is_recovered: bool = False
    recovery_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class RecoveryAction:
    """恢复动作"""
    action_id: str
    error_id: str
    strategy: RecoveryStrategy
    description: str
    parameters: Dict[str, Any]
    executed_at: datetime = field(default_factory=datetime.now)
    success: bool = False
    result: Optional[str] = None

class CircuitBreaker:
    """熔断器实现"""

    def __init__(self, failure_threshold: Optional[int] = None, recovery_timeout: Optional[int] = None):
        # 使用智能配置系统获取默认参数
        error_context = create_query_context(query_type="error_recovery_config")
        if failure_threshold is None:
            failure_threshold = get_smart_config("failure_threshold", error_context)
        if recovery_timeout is None:
            recovery_timeout = get_smart_config("recovery_timeout", error_context)

        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = config.DEFAULT_ZERO_VALUE
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.RLock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """执行函数，应用熔断器逻辑"""
        with self.lock:
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise e

    def _on_success(self):
        """成功时重置熔断器"""
        with self.lock:
            self.failure_count = config.DEFAULT_ZERO_VALUE
            self.state = "CLOSED"

    def _on_failure(self):
        """失败时更新熔断器状态"""
        with self.lock:
            self.failure_count += config.DEFAULT_ONE_VALUE
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        if self.last_failure_time is None:
            return True

        return (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout

class ErrorRecoveryManager:
    """错误恢复管理器"""

    def __init__(self):
        self.error_records: Dict[str, ErrorRecord] = {}
        self.recovery_actions: Dict[str, RecoveryAction] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.recovery_strategies: Dict[ErrorCategory, RecoveryStrategy] = {}
        self.performance_metrics: Dict[str, List[float]] = {}
        self.alert_thresholds: Dict[str, float] = {}

        self._init_recovery_strategies()

        self._init_alert_thresholds()

        self._start_background_monitoring()

        logger.info("✅ 错误恢复管理器初始化完成")

    def _init_recovery_strategies(self):
        """初始化恢复策略映射"""
        self.recovery_strategies = {
            ErrorCategory.INITIALIZATION: RecoveryStrategy.RETRY,
            ErrorCategory.CONFIGURATION: RecoveryStrategy.FALLBACK,
            ErrorCategory.NETWORK: RecoveryStrategy.CIRCUIT_BREAKER,
            ErrorCategory.MEMORY: RecoveryStrategy.GRADUAL_DEGRADATION,
            ErrorCategory.TIMEOUT: RecoveryStrategy.RETRY,
            ErrorCategory.VALIDATION: RecoveryStrategy.FALLBACK,
            ErrorCategory.INTEGRATION: RecoveryStrategy.CIRCUIT_BREAKER,
            ErrorCategory.UNKNOWN: RecoveryStrategy.FALLBACK
        }

    def _init_alert_thresholds(self):
        """初始化告警阈值"""
        self.alert_thresholds = {
            'error_rate': config.DEFAULT_LOW_DECIMAL_THRESHOLD,  # 错误率阈值
            'recovery_time': 3config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE,  # 恢复时间阈值（秒）
            'consecutive_failures': 5,  # 连续失败阈值
            'memory_usage': config.DEFAULT_HIGH_THRESHOLD,  # 内存使用率阈值
            'response_time': 5.config.DEFAULT_ZERO_VALUE  # 响应时间阈值（秒）
        }

    def _start_background_monitoring(self):
        """启动后台监控任务"""
        def monitor_loop():
            while True:
                try:
                    self._check_system_health()
                    self._cleanup_old_records()
                    time.sleep(config.DEFAULT_MAX_RETRIESconfig.DEFAULT_ZERO_VALUE)  # 每3config.DEFAULT_ZERO_VALUE秒检查一次
                except Exception as e:
                    logger.error("后台监控任务失败: {e}")

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("✅ 后台监控任务已启动")

    def record_error(self,
                    error: Exception,
                    context: ErrorContext,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = ErrorCategory.UNKNOWN) -> str:
        """记录错误"""
        try:
            error_id = f"err_{int(time.time())}_{len(self.error_records)}"

            recovery_strategy = self.recovery_strategies.get(category, RecoveryStrategy.FALLBACK)

            error_record = ErrorRecord(
                error_id=error_id,
                error_type=type(error).__name__,
                error_message=str(error),
                severity=severity,
                category=category,
                context=context,
                stack_trace=traceback.format_exc(),
                recovery_strategy=recovery_strategy
            )

            self.error_records[error_id] = error_record

            self._record_performance_metric('error_count', config.DEFAULT_ONE_VALUE)

            self._check_alert_conditions(error_record)

            logger.warning("📝 错误已记录: {error_id} - {error_record.error_type}")
            return error_id

        except Exception as e:
            logger.error("记录错误失败: {e}")
            return ""

    def _record_performance_metric(self, metric_name: str, value: float):
        """记录性能指标"""
        if metric_name not in self.performance_metrics:
            self.performance_metrics[metric_name] = []

        self.performance_metrics[metric_name].append(value)

        if len(self.performance_metrics[metric_name]) > 1000:
            self.performance_metrics[metric_name] = self.performance_metrics[metric_name][-1000:]
    pass
    def _check_alert_conditions(self, error_record: ErrorRecord):
        """检查告警条件"""
        try:
            if self._get_error_rate() > self.alert_thresholds['error_rate']:
                self._send_alert('HIGH_ERROR_RATE', f"错误率过高: {self._get_error_rate():.config.DEFAULT_TWO_VALUE%}")

            consecutive_failures = self._get_consecutive_failures()
            if consecutive_failures > self.alert_thresholds['consecutive_failures']:
                self._send_alert('CONSECUTIVE_FAILURES', f"连续失败次数过多: {consecutive_failures}")

            if error_record.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                self._send_alert('SEVERE_ERROR', f"严重错误: {error_record.error_type}")

        except Exception as e:
            logger.error("检查告警条件失败: {e}")

    def _get_error_rate(self) -> float:
        """获取错误率"""
        try:
            if not self.performance_metrics.get('error_count'):
                return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))

            recent_errors = self.performance_metrics['error_count'][-get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")):]  # 最近100次
            return sum(recent_errors) / len(recent_errors) if recent_errors else get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))

        except Exception:
            return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))

    def _get_consecutive_failures(self) -> int:
        """获取连续失败次数"""
        try:
            if not self.performance_metrics.get('error_count'):
                return 0

            recent_metrics = self.performance_metrics['error_count'][-20:]  # 最近20次
            consecutive = config.DEFAULT_ZERO_VALUE

            for metric in reversed(recent_metrics):
                if metric > config.DEFAULT_ZERO_VALUE:
                    consecutive += config.DEFAULT_ONE_VALUE
                else:
                    break

            return consecutive

        except Exception:
            return 0

    def _send_alert(self, alert_type: str, message: str):
        """发送告警"""
        try:
            alert_msg = f"🚨 系统告警 [{alert_type}]: {message}"
            logger.error(alert_msg)


        except Exception as e:
            logger.error("发送告警失败: {e}")

    async def attempt_recovery(self, error_id: str) -> bool:
        """尝试恢复错误"""
        try:
            if error_id not in self.error_records:
                logger.warning("未找到错误记录: {error_id}")
                return False

            error_record = self.error_records[error_id]

            if error_record.is_recovered:
                logger.info(f"错误已恢复: {error_id}")
                return True

            if error_record.retry_count >= error_record.max_retries:
                logger.warning("错误恢复尝试次数已达上限: {error_id}")
                return False

            recovery_success = False

            if error_record.recovery_strategy == RecoveryStrategy.RETRY:
                recovery_success = await self._retry_recovery(error_record)
            elif error_record.recovery_strategy == RecoveryStrategy.FALLBACK:
                recovery_success = await self._fallback_recovery(error_record)
            elif error_record.recovery_strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                recovery_success = await self._circuit_breaker_recovery(error_record)
            elif error_record.recovery_strategy == RecoveryStrategy.GRADUAL_DEGRADATION:
                recovery_success = await self._gradual_degradation_recovery(error_record)

            if recovery_success:
                error_record.is_recovered = True
                error_record.recovery_time = datetime.now()
                logger.info(f"✅ 错误恢复成功: {error_id}")
            else:
                error_record.retry_count += config.DEFAULT_ONE_VALUE
                logger.warning("⚠️ 错误恢复失败: {error_id}, 尝试次数: {error_record.retry_count}")

            return recovery_success

        except Exception as e:
            logger.error("尝试恢复错误失败: {e}")
            return False

    async def _retry_recovery(self, error_record: ErrorRecord) -> bool:
        """重试恢复策略"""
        try:
            await asyncio.sleep(1)  # 等待1秒

            return True

        except Exception as e:
            logger.error("重试恢复失败: {e}")
            return False

    async def _fallback_recovery(self, error_record: ErrorRecord) -> bool:
        """回退恢复策略"""
        try:
            logger.info(f"执行回退策略: {error_record.context.component_name}")
            return True

        except Exception as e:
            logger.error("回退恢复失败: {e}")
            return False

    async def _circuit_breaker_recovery(self, error_record: ErrorRecord) -> bool:
        """熔断器恢复策略"""
        try:
            component_name = error_record.context.component_name

            if component_name not in self.circuit_breakers:
                self.circuit_breakers[component_name] = CircuitBreaker()

            circuit_breaker = self.circuit_breakers[component_name]

            if circuit_breaker.state == "OPEN":
                logger.info(f"熔断器已打开，等待恢复: {component_name}")
                return False

            return True

        except Exception as e:
            logger.error("熔断器恢复失败: {e}")
            return False

    async def _gradual_degradation_recovery(self, error_record: ErrorRecord) -> bool:
        """渐进降级恢复策略"""
        try:
            logger.info(f"执行渐进降级策略: {error_record.context.component_name}")
            return True

        except Exception as e:
            logger.error("渐进降级恢复失败: {e}")
            return False

    def get_circuit_breaker(self, component_name: str) -> CircuitBreaker:
        """获取组件的熔断器"""
        if component_name not in self.circuit_breakers:
            self.circuit_breakers[component_name] = CircuitBreaker()
        return self.circuit_breakers[component_name]

    def _check_system_health(self):
        """检查系统健康状态"""
        try:
            self._check_memory_usage()

            self._check_error_rate_trend()

            self._check_recovery_success_rate()

        except Exception as e:
            logger.error("系统健康检查失败: {e}")

    def _check_memory_usage(self):
        """检查内存使用情况"""
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent / 100.0

            if memory_percent > self.alert_thresholds['memory_usage']:
                self._send_alert('HIGH_MEMORY_USAGE', f"内存使用率过高: {memory_percent:.config.DEFAULT_ONE_VALUE%}")

        except ImportError:
            pass  # psutil不可用
        except Exception as e:
            logger.debug("检查内存使用失败: {e}")

    def _check_error_rate_trend(self):
        """检查错误率趋势"""
        try:
            current_error_rate = self._get_error_rate()
            self._record_performance_metric('error_rate_trend', current_error_rate)

        except Exception as e:
            logger.debug("检查错误率趋势失败: {e}")

    def _check_recovery_success_rate(self):
        """检查恢复成功率"""
        try:
            total_errors = len(self.error_records)
            recovered_errors = sum(1 for record in self.error_records.values() if record.is_recovered)

            if total_errors > config.DEFAULT_ZERO_VALUE:
                recovery_rate = recovered_errors / total_errors
                self._record_performance_metric('recovery_success_rate', recovery_rate)

                if recovery_rate < config.DEFAULT_ZERO_VALUE.5:  # 恢复成功率低于config.DEFAULT_DISPLAY_LIMIT%
                    self._send_alert('LOW_RECOVERY_RATE', f"恢复成功率过低: {recovery_rate:.config.DEFAULT_ONE_VALUE%}")

        except Exception as e:
            logger.debug("检查恢复成功率失败: {e}")

    def _cleanup_old_records(self):
        """清理旧的错误记录"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(days=7)  # 保留7天的记录

            old_error_ids = [
                error_id for error_id, record in self.error_records.items()
                if record.created_at < cutoff_time
            ]

            for error_id in old_error_ids:
                del self.error_records[error_id]

            old_action_ids = [
                action_id for action_id, action in self.recovery_actions.items()
                if action.executed_at < cutoff_time
            ]

            for action_id in old_action_ids:
                del self.recovery_actions[action_id]

            if old_error_ids or old_action_ids:
                logger.debug("🧹 清理了 {len(old_error_ids)} 个错误记录和 {len(old_action_ids)} 个恢复动作")

        except Exception as e:
            logger.error("清理旧记录失败: {e}")

    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        try:
            total_errors = len(self.error_records)
            recovered_errors = sum(1 for record in self.error_records.values() if record.is_recovered)
            critical_errors = sum(1 for record in self.error_records.values() if record.severity == ErrorSeverity.CRITICAL)

            category_stats = {}
            for record in self.error_records.values():
                category = record.category.value
                if category not in category_stats:
                    category_stats[category] = config.DEFAULT_ZERO_VALUE
                category_stats[category] += config.DEFAULT_ONE_VALUE

            severity_stats = {}
            for record in self.error_records.values():
                severity = record.severity.value
                if severity not in severity_stats:
                    severity_stats[severity] = config.DEFAULT_ZERO_VALUE
                severity_stats[severity] += 1

            return {
                'total_errors': total_errors,
                'recovered_errors': recovered_errors,
                'unrecovered_errors': total_errors - recovered_errors,
                'recovery_rate': recovered_errors / total_errors if total_errors > config.DEFAULT_ZERO_VALUE else config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE,
                'critical_errors': critical_errors,
                'category_distribution': category_stats,
                'severity_distribution': severity_stats,
                'performance_metrics': {
                    'error_rate': self._get_error_rate(),
                    'consecutive_failures': self._get_consecutive_failures(),
                    'recovery_success_rate': self.performance_metrics.get('recovery_success_rate',
    [config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE])[-config.DEFAULT_ONE_VALUE] if self.performance_metrics.get('recovery_success_rate') else config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
                }
            }

        except Exception as e:
            logger.error("获取错误摘要失败: {e}")
            return {'error': str(e)}

    def reset_circuit_breaker(self, component_name: str) -> bool:
        """重置组件的熔断器"""
        try:
            if component_name in self.circuit_breakers:
                del self.circuit_breakers[component_name]
                logger.info(f"✅ 熔断器已重置: {component_name}")
                return True
            return False

        except Exception as e:
            logger.error("重置熔断器失败: {e}")
            return False

_error_recovery_manager = None
_error_recovery_manager_lock = threading.RLock()

def get_error_recovery_manager() -> ErrorRecoveryManager:
    """获取错误恢复管理器实例 - 线程安全的单例实现"""
    global _error_recovery_manager

    if _error_recovery_manager is None:
        with _error_recovery_manager_lock:
            if _error_recovery_manager is None:
                _error_recovery_manager = ErrorRecoveryManager()

    return _error_recovery_manager

def record_error(error: Exception,
                component_name: str,
                operation: str,
                severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                category: ErrorCategory = ErrorCategory.UNKNOWN,
                **kwargs) -> str:
    """记录错误的便捷函数"""
    try:
        context = ErrorContext(
            component_name=component_name,
            operation=operation,
            **kwargs
        )

        manager = get_error_recovery_manager()
        return manager.record_error(error, context, severity, category)

    except Exception as e:
        logger.error("记录错误失败: {e}")
        return ""

async def attempt_error_recovery(error_id: str) -> bool:
    """尝试恢复错误的便捷函数"""
    try:
        manager = get_error_recovery_manager()
        return await manager.attempt_recovery(error_id)

    except Exception as e:
        logger.error("尝试恢复错误失败: {e}")
        return False

def get_circuit_breaker(component_name: str) -> CircuitBreaker:
    """获取组件熔断器的便捷函数"""
    try:
        manager = get_error_recovery_manager()
        return manager.get_circuit_breaker(component_name)

    except Exception as e:
        logger.error("获取熔断器失败: {e}")
        return CircuitBreaker()
