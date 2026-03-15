"""
自进化引擎生产环境验证模块
Self-Evolution Engine Production Validation Module

核心功能：
1. 引擎健康检查 - 全面检查引擎各组件状态
2. 持续运行监控 - 监控进化循环的执行状态
3. 指标采集集成 - 与量化指标系统集成
4. 告警管理 - 异常情况自动告警
5. 报告生成 - 定期生成进化报告
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Thread, Event
import traceback

logger = logging.getLogger(__name__)


class EngineStatus(str, Enum):
    """引擎状态"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class ComponentStatus(str, Enum):
    """组件状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class EvolutionHealthReport:
    """进化健康报告"""
    timestamp: str
    engine_status: EngineStatus
    overall_health: str
    components: Dict[str, Dict[str, Any]]
    recent_evolutions: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    recommendations: List[str] = field(default_factory=list)


@dataclass
class EvolutionMetrics:
    """进化指标"""
    total_evolutions: int = 0
    successful_evolutions: int = 0
    failed_evolutions: int = 0
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    last_evolution_time: Optional[str] = None
    evolution_interval_hours: float = 0.0


class EvolutionEngineValidator:
    """自进化引擎验证器"""
    
    def __init__(self, evolution_engine=None):
        self.engine = evolution_engine
        
        # 验证结果缓存
        self._last_health_check: Optional[EvolutionHealthReport] = None
        self._last_check_time: float = 0
        
        # 告警回调
        self._alert_callbacks: List[Callable] = []
        
        # 监控历史
        self._monitoring_history: List[Dict[str, Any]] = []
        self._max_history_size = 100
        
        logger.info("自进化引擎验证器初始化完成")
    
    def set_engine(self, engine) -> None:
        """设置进化引擎"""
        self.engine = engine
        logger.info("已绑定进化引擎实例")
    
    async def health_check(self) -> EvolutionHealthReport:
        """执行健康检查"""
        self._last_check_time = time.time()
        
        # 默认报告
        report = EvolutionHealthReport(
            timestamp=datetime.now().isoformat(),
            engine_status=EngineStatus.INITIALIZING,
            overall_health="unknown",
            components={},
            recent_evolutions=[],
            alerts=[]
        )
        
        try:
            # 1. 检查引擎是否存在
            if not self.engine:
                report.engine_status = EngineStatus.ERROR
                report.alerts.append({
                    'level': 'critical',
                    'message': '进化引擎未初始化'
                })
                self._last_health_check = report
                return report
            
            # 2. 检查各组件状态
            components = await self._check_components()
            report.components = components
            
            # 3. 检查进化历史
            recent_evolutions = await self._check_evolution_history()
            report.recent_evolutions = recent_evolutions
            
            # 4. 确定整体状态
            overall_health, alerts = self._determine_overall_health(components, recent_evolutions)
            report.overall_health = overall_health
            report.alerts.extend(alerts)
            
            # 5. 检查引擎状态
            try:
                status = await self.engine.get_evolution_status()
                report.engine_status = EngineStatus.RUNNING if status.get('engine_status') == 'running' else EngineStatus.PAUSED
            except Exception as e:
                report.engine_status = EngineStatus.ERROR
                report.alerts.append({
                    'level': 'error',
                    'message': f'获取引擎状态失败: {str(e)}'
                })
            
            # 6. 生成建议
            report.recommendations = self._generate_recommendations(components, recent_evolutions)
            
        except Exception as e:
            logger.error(f"健康检查执行失败: {e}")
            report.engine_status = EngineStatus.ERROR
            report.alerts.append({
                'level': 'critical',
                'message': f'健康检查异常: {str(e)}'
            })
        
        self._last_health_check = report
        
        # 触发告警
        for alert in report.alerts:
            if alert.get('level') in ['critical', 'error']:
                await self._trigger_alerts(alert)
        
        return report
    
    async def _check_components(self) -> Dict[str, Dict[str, Any]]:
        """检查各组件"""
        components = {}
        
        # 检查Git集成
        try:
            if hasattr(self.engine, 'git'):
                git_status = {
                    'status': ComponentStatus.HEALTHY.value,
                    'message': 'Git集成正常',
                    'details': {}
                }
            else:
                git_status = {
                    'status': ComponentStatus.DEGRADED.value,
                    'message': 'Git集成未配置',
                    'details': {}
                }
            components['git'] = git_status
        except Exception as e:
            components['git'] = {
                'status': ComponentStatus.FAILED.value,
                'message': f'Git检查失败: {str(e)}',
                'details': {}
            }
        
        # 检查自修改模块
        try:
            if hasattr(self.engine, 'modification'):
                mod_status = {
                    'status': ComponentStatus.HEALTHY.value,
                    'message': '自修改模块正常',
                    'details': {}
                }
            else:
                mod_status = {
                    'status': ComponentStatus.DEGRADED.value,
                    'message': '自修改模块未配置',
                    'details': {}
                }
            components['modification'] = mod_status
        except Exception as e:
            components['modification'] = {
                'status': ComponentStatus.FAILED.value,
                'message': f'自修改模块检查失败: {str(e)}',
                'details': {}
            }
        
        # 检查审查模块
        try:
            if hasattr(self.engine, 'review'):
                review_status = {
                    'status': ComponentStatus.HEALTHY.value,
                    'message': '审查模块正常',
                    'details': {}
                }
            else:
                review_status = {
                    'status': ComponentStatus.DEGRADED.value,
                    'message': '审查模块未配置',
                    'details': {}
                }
            components['review'] = review_status
        except Exception as e:
            components['review'] = {
                'status': ComponentStatus.FAILED.value,
                'message': f'审查模块检查失败: {str(e)}',
                'details': {}
            }
        
        # 检查宪法检查器
        try:
            if hasattr(self.engine, 'constitution'):
                const_status = {
                    'status': ComponentStatus.HEALTHY.value,
                    'message': '宪法检查器正常',
                    'details': {}
                }
            else:
                const_status = {
                    'status': ComponentStatus.DEGRADED.value,
                    'message': '宪法检查器未配置',
                    'details': {}
                }
            components['constitution'] = const_status
        except Exception as e:
            components['constitution'] = {
                'status': ComponentStatus.FAILED.value,
                'message': f'宪法检查器检查失败: {str(e)}',
                'details': {}
            }
        
        # 检查使用分析
        try:
            if hasattr(self.engine, 'usage_analytics'):
                analytics_status = {
                    'status': ComponentStatus.HEALTHY.value,
                    'message': '使用分析正常',
                    'details': {}
                }
            else:
                analytics_status = {
                    'status': ComponentStatus.DEGRADED.value,
                    'message': '使用分析未配置',
                    'details': {}
                }
            components['usage_analytics'] = analytics_status
        except Exception as e:
            components['usage_analytics'] = {
                'status': ComponentStatus.FAILED.value,
                'message': f'使用分析检查失败: {str(e)}',
                'details': {}
            }
        
        return components
    
    async def _check_evolution_history(self) -> List[Dict[str, Any]]:
        """检查进化历史"""
        if not self.engine or not hasattr(self.engine, 'evolution_history'):
            return []
        
        try:
            history = self.engine.evolution_history
            recent = history[-10:] if len(history) > 10 else history
            
            return [
                {
                    'plan_id': getattr(r, 'plan_id', 'unknown'),
                    'status': getattr(r, 'status', 'unknown'),
                    'execution_time': getattr(r, 'execution_time', 0),
                    'completed_at': getattr(r, 'completed_at', 'unknown')
                }
                for r in recent
            ]
        except Exception as e:
            logger.warning(f"获取进化历史失败: {e}")
            return []
    
    def _determine_overall_health(
        self,
        components: Dict[str, Dict[str, Any]],
        recent_evolutions: List[Dict[str, Any]]
    ) -> tuple[str, List[Dict[str, Any]]]:
        """确定整体健康状态"""
        alerts = []
        
        # 1. 检查组件状态
        failed_components = []
        degraded_components = []
        
        for name, status in components.items():
            if status.get('status') == ComponentStatus.FAILED.value:
                failed_components.append(name)
            elif status.get('status') == ComponentStatus.DEGRADED.value:
                degraded_components.append(name)
        
        if failed_components:
            alerts.append({
                'level': 'critical',
                'message': f'组件失败: {", ".join(failed_components)}'
            })
            return 'critical', alerts
        
        if degraded_components:
            alerts.append({
                'level': 'warning',
                'message': f'组件降级: {", ".join(degraded_components)}'
            })
        
        # 2. 检查进化成功率
        if recent_evolutions:
            success_count = sum(1 for e in recent_evolutions 
                              if e.get('status') == 'completed')
            total = len(recent_evolutions)
            success_rate = success_count / total if total > 0 else 0
            
            if success_rate < 0.5:
                alerts.append({
                    'level': 'critical',
                    'message': f'进化成功率过低: {success_rate*100:.1f}%'
                })
                return 'critical', alerts
            
            if success_rate < 0.8:
                alerts.append({
                    'level': 'warning',
                    'message': f'进化成功率较低: {success_rate*100:.1f}%'
                })
        
        # 3. 检查最近进化时间
        if recent_evolutions:
            try:
                last_time = recent_evolutions[0].get('completed_at')
                if last_time:
                    last_dt = datetime.fromisoformat(str(last_time))
                    hours_ago = (datetime.now() - last_dt).total_seconds() / 3600
                    
                    if hours_ago > 48:
                        alerts.append({
                            'level': 'warning',
                            'message': f'超过48小时未执行进化'
                        })
            except Exception:
                pass
        
        return 'healthy' if not alerts else ('degraded' if not any(a.get('level') == 'critical' for a in alerts) else 'critical'), alerts
    
    def _generate_recommendations(
        self,
        components: Dict[str, Dict[str, Any]],
        recent_evolutions: List[Dict[str, Any]]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 组件建议
        for name, status in components.items():
            if status.get('status') == ComponentStatus.FAILED.value:
                recommendations.append(f"⚠️ {name} 组件失败，需要检查配置")
            elif status.get('status') == ComponentStatus.DEGRADED.value:
                recommendations.append(f"📊 {name} 组件降级，建议优化")
        
        # 进化建议
        if recent_evolutions:
            success_count = sum(1 for e in recent_evolutions 
                              if e.get('status') == 'completed')
            total = len(recent_evolutions)
            
            if success_count / total < 0.8:
                recommendations.append("📝 进化成功率较低，建议检查进化策略")
        
        if not recent_evolutions:
            recommendations.append("📝 暂无进化记录，建议启动进化循环")
        
        if not recommendations:
            recommendations.append("✅ 系统运行正常")
        
        return recommendations
    
    async def _trigger_alerts(self, alert: Dict[str, Any]) -> None:
        """触发告警"""
        for callback in self._alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"告警回调执行失败: {e}")
    
    def register_alert_callback(self, callback: Callable) -> None:
        """注册告警回调"""
        self._alert_callbacks.append(callback)
    
    def get_last_report(self) -> Optional[EvolutionHealthReport]:
        """获取上次健康报告"""
        return self._last_health_check
    
    def get_metrics(self) -> EvolutionMetrics:
        """获取进化指标"""
        metrics = EvolutionMetrics()
        
        if not self.engine or not hasattr(self.engine, 'evolution_history'):
            return metrics
        
        try:
            history = self.engine.evolution_history
            
            metrics.total_evolutions = len(history)
            
            completed = [r for r in history if getattr(r, 'status', None) == 'completed']
            metrics.successful_evolutions = len(completed)
            metrics.failed_evolutions = metrics.total_evolutions - metrics.successful_evolutions
            
            if metrics.total_evolutions > 0:
                metrics.success_rate = metrics.successful_evolutions / metrics.total_evolutions
            
            if completed:
                execution_times = [r.execution_time for r in completed if hasattr(r, 'execution_time')]
                if execution_times:
                    metrics.avg_execution_time = sum(execution_times) / len(execution_times)
                
                last = completed[-1]
                if hasattr(last, 'completed_at'):
                    metrics.last_evolution_time = str(last.completed_at)
            
            # 计算进化间隔
            if hasattr(self.engine, 'evolution_interval_hours'):
                metrics.evolution_interval_hours = self.engine.evolution_interval_hours
                
        except Exception as e:
            logger.warning(f"获取进化指标失败: {e}")
        
        return metrics


class EvolutionEngineMonitor:
    """自进化引擎监控器 - 持续运行监控"""
    
    def __init__(self, validator: EvolutionEngineValidator):
        self.validator = validator
        self._monitoring = False
        self._monitor_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._check_interval = 300  # 5分钟检查一次
        
        # 监控回调
        self._monitor_callbacks: List[Callable] = []
        
        logger.info("自进化引擎监控器初始化完成")
    
    def start_monitoring(self) -> None:
        """启动监控"""
        if self._monitoring:
            logger.warning("监控已在运行")
            return
        
        self._monitoring = True
        self._stop_event.clear()
        self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("自进化引擎监控已启动")
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        if not self._monitoring:
            return
        
        self._monitoring = False
        self._stop_event.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=10)
        
        logger.info("自进化引擎监控已停止")
    
    def _monitor_loop(self) -> None:
        """监控循环"""
        while not self._stop_event.is_set():
            try:
                # 执行健康检查
                report = asyncio.run(self.validator.health_check())
                
                # 记录监控历史
                self._record_monitoring(report)
                
                # 触发监控回调
                for callback in self._monitor_callbacks:
                    try:
                        callback(report)
                    except Exception as e:
                        logger.error(f"监控回调执行失败: {e}")
                
                # 记录日志
                logger.info(f"进化引擎健康检查: {report.overall_health}")
                
                if report.alerts:
                    for alert in report.alerts:
                        logger.warning(f"告警: {alert.get('message')}")
                
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                logger.error(traceback.format_exc())
            
            # 等待下一次检查
            self._stop_event.wait(self._check_interval)
    
    def _record_monitoring(self, report: EvolutionHealthReport) -> None:
        """记录监控历史"""
        record = {
            'timestamp': report.timestamp,
            'engine_status': report.engine_status.value,
            'overall_health': report.overall_health,
            'alert_count': len(report.alerts)
        }
        
        self._validator._monitoring_history.append(record)
        
        # 保持历史大小
        if len(self._validator._monitoring_history) > self._validator._max_history_size:
            self._validator._monitoring_history = \
                self._validator._monitoring_history[-self._validator._max_history_size:]
    
    def register_monitor_callback(self, callback: Callable) -> None:
        """注册监控回调"""
        self._monitor_callbacks.append(callback)
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            'monitoring': self._monitoring,
            'check_interval_seconds': self._check_interval,
            'history_count': len(self._validator._monitoring_history)
        }


class EvolutionEngineProductionValidator:
    """自进化引擎生产环境验证器 - 整合所有功能"""
    
    def __init__(self, evolution_engine=None):
        self.engine = evolution_engine
        
        # 初始化组件
        self.validator = EvolutionEngineValidator(evolution_engine)
        self.monitor = EvolutionEngineMonitor(self.validator)
        
        # 集成指标服务
        self._metrics_service = None
        
        logger.info("自进化引擎生产验证器初始化完成")
    
    def set_engine(self, engine) -> None:
        """设置进化引擎"""
        self.engine = engine
        self.validator.set_engine(engine)
    
    async def validate(self) -> Dict[str, Any]:
        """执行完整验证"""
        validation_result = {
            'timestamp': datetime.now().isoformat(),
            'engine_bound': self.engine is not None,
            'health_check': None,
            'metrics': None,
            'recommendations': []
        }
        
        # 1. 健康检查
        if self.engine:
            health_report = await self.validator.health_check()
            validation_result['health_check'] = {
                'engine_status': health_report.engine_status.value,
                'overall_health': health_report.overall_health,
                'component_count': len(health_report.components),
                'alert_count': len(health_report.alerts),
                'recommendations': health_report.recommendations
            }
        
        # 2. 获取指标
        metrics = self.validator.get_metrics()
        validation_result['metrics'] = {
            'total_evolutions': metrics.total_evolutions,
            'successful_evolutions': metrics.successful_evolutions,
            'failed_evolutions': metrics.failed_evolutions,
            'success_rate': metrics.success_rate,
            'avg_execution_time': metrics.avg_execution_time,
            'last_evolution_time': metrics.last_evolution_time,
            'evolution_interval_hours': metrics.evolution_interval_hours
        }
        
        # 3. 生成总体建议
        validation_result['recommendations'] = self._generate_validation_recommendations(
            validation_result
        )
        
        return validation_result
    
    def _generate_validation_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """生成验证建议"""
        recommendations = []
        
        if not result.get('engine_bound'):
            recommendations.append("❌ 未绑定进化引擎实例，请先设置引擎")
            return recommendations
        
        health = result.get('health_check', {})
        
        if health.get('overall_health') == 'critical':
            recommendations.append("🔴 引擎处于危险状态，需要立即处理")
        elif health.get('overall_health') == 'degraded':
            recommendations.append("🟡 引擎处于降级状态，建议优化")
        else:
            recommendations.append("🟢 引擎运行正常")
        
        # 检查组件
        component_count = health.get('component_count', 0)
        if component_count < 5:
            recommendations.append(f"⚠️ 仅 {component_count}/5 组件可用，部分功能可能受限")
        
        # 检查成功率
        metrics = result.get('metrics', {})
        success_rate = metrics.get('success_rate', 0)
        
        if success_rate < 0.5:
            recommendations.append("🔴 进化成功率低于50%，需要检查进化策略")
        elif success_rate < 0.8:
            recommendations.append("🟡 进化成功率低于80%，建议优化")
        
        return recommendations
    
    def start_production_monitoring(self, metrics_service=None) -> None:
        """启动生产监控"""
        # 设置指标服务
        if metrics_service:
            self._metrics_service = metrics_service
            
            # 注册指标采集回调
            self.monitor.register_monitor_callback(lambda r: self._record_metrics(r))
        
        # 启动监控
        self.monitor.start_monitoring()
        
        logger.info("生产环境监控已启动")
    
    def stop_production_monitoring(self) -> None:
        """停止生产监控"""
        self.monitor.stop_monitoring()
        
        logger.info("生产环境监控已停止")
    
    def _record_metrics(self, report: EvolutionHealthReport) -> None:
        """记录指标"""
        if not self._metrics_service:
            return
        
        try:
            # 记录各指标
            self._metrics_service.record(
                'evolution_health_score',
                100 if report.overall_health == 'healthy' else 
                   (50 if report.overall_health == 'degraded' else 0)
            )
            
            self._metrics_service.record(
                'evolution_component_count',
                len([c for c in report.components.values() 
                    if c.get('status') == 'healthy'])
            )
            
            self._metrics_service.record(
                'evolution_alert_count',
                len(report.alerts)
            )
            
            # 获取进化指标
            metrics = self.validator.get_metrics()
            
            self._metrics_service.record(
                'evolution_total_count',
                metrics.total_evolutions
            )
            
            self._metrics_service.record(
                'evolution_success_rate',
                metrics.success_rate * 100
            )
            
        except Exception as e:
            logger.error(f"记录进化指标失败: {e}")


# 便捷函数
def create_evolution_validator(evolution_engine=None) -> EvolutionEngineProductionValidator:
    """创建生产验证器"""
    return EvolutionEngineProductionValidator(evolution_engine)
