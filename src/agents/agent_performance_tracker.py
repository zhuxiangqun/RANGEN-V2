#!/usr/bin/env python3
"""
智能体性能跟踪器 - 负责性能指标的收集、计算和分析
"""
import time
import threading
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import statistics


@dataclass
class PerformanceSnapshot:
    """性能快照"""
    timestamp: float
    success: bool
    confidence: float
    processing_time: float
    request_size: int = 0
    response_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """性能统计"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_processing_time: float
    average_confidence: float
    min_processing_time: float
    max_processing_time: float
    median_processing_time: float
    p95_processing_time: float
    p99_processing_time: float
    requests_per_minute: float
    uptime_ratio: float
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceAlert:
    """性能告警"""
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    threshold_value: float
    actual_value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentPerformanceTracker:
    """智能体性能跟踪器 - 单一职责：性能指标管理"""
    
    def __init__(self, agent_id: str, max_snapshots: int = 1000, 
                 alert_thresholds: Optional[Dict[str, float]] = None):
        """
        初始化性能跟踪器
        
        Args:
            agent_id: 智能体ID
            max_snapshots: 最大快照数量
            alert_thresholds: 告警阈值配置
        """
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # 快照存储
        self.max_snapshots = max_snapshots
        self._snapshots: deque = deque(maxlen=max_snapshots)
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 基础计数器
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._start_time = time.time()
        self._last_activity = 0
        
        # 实时统计缓存
        self._stats_cache: Optional[PerformanceStats] = None
        self._cache_timestamp = 0
        self._cache_ttl = 60  # 1分钟缓存
        
        # 告警配置
        self.alert_thresholds = alert_thresholds or {
            "success_rate_min": 0.8,
            "avg_processing_time_max": 5.0,
            "confidence_min": 0.6,
            "requests_per_minute_max": 100,
            "uptime_ratio_min": 0.9
        }
        
        # 告警历史
        self._alerts: List[PerformanceAlert] = []
        self._max_alerts = 100
        
        # 性能趋势分析
        self._trend_window = 100  # 趋势分析窗口
        self._performance_trends: Dict[str, List[float]] = {
            "processing_times": deque(maxlen=self._trend_window),
            "confidence_scores": deque(maxlen=self._trend_window),
            "success_rates": deque(maxlen=self._trend_window)
        }
        
        self.logger.info(f"性能跟踪器初始化完成: {agent_id}")
    
    def record_request(self, success: bool, confidence: float, 
                      processing_time: float, request_size: int = 0,
                      response_size: int = 0, 
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        记录请求性能数据
        
        Args:
            success: 是否成功
            confidence: 置信度
            processing_time: 处理时间
            request_size: 请求大小
            response_size: 响应大小
            metadata: 元数据
        """
        with self._lock:
            timestamp = time.time()
            
            # 更新计数器
            self._total_requests += 1
            if success:
                self._successful_requests += 1
            else:
                self._failed_requests += 1
            self._last_activity = timestamp
            
            # 创建快照
            snapshot = PerformanceSnapshot(
                timestamp=timestamp,
                success=success,
                confidence=confidence,
                processing_time=processing_time,
                request_size=request_size,
                response_size=response_size,
                metadata=metadata or {}
            )
            
            # 添加快照
            self._snapshots.append(snapshot)
            
            # 更新趋势数据
            self._update_trends(snapshot)
            
            # 清除缓存
            self._invalidate_cache()
            
            # 检查告警
            self._check_alerts(snapshot)
    
    def _update_trends(self, snapshot: PerformanceSnapshot) -> None:
        """更新性能趋势数据"""
        self._performance_trends["processing_times"].append(snapshot.processing_time)
        self._performance_trends["confidence_scores"].append(snapshot.confidence)
        
        # 计算滑动成功率
        recent_snapshots = list(self._snapshots)[-min(20, len(self._snapshots)):]
        if recent_snapshots:
            success_rate = sum(1 for s in recent_snapshots if s.success) / len(recent_snapshots)
            self._performance_trends["success_rates"].append(success_rate)
    
    def _check_alerts(self, snapshot: PerformanceSnapshot) -> None:
        """检查性能告警"""
        alerts = []
        
        # 检查成功率告警
        if self._total_requests >= 10:  # 至少10个请求才检查
            current_success_rate = self._successful_requests / self._total_requests
            if current_success_rate < self.alert_thresholds["success_rate_min"]:
                alerts.append(PerformanceAlert(
                    alert_type="success_rate_low",
                    severity="warning",
                    message=f"成功率过低: {current_success_rate:.2%}",
                    timestamp=datetime.now(),
                    threshold_value=self.alert_thresholds["success_rate_min"],
                    actual_value=current_success_rate
                ))
        
        # 检查处理时间告警
        if snapshot.processing_time > self.alert_thresholds["avg_processing_time_max"]:
            alerts.append(PerformanceAlert(
                alert_type="processing_time_high",
                severity="warning",
                message=f"处理时间过长: {snapshot.processing_time:.2f}s",
                timestamp=datetime.now(),
                threshold_value=self.alert_thresholds["avg_processing_time_max"],
                actual_value=snapshot.processing_time
            ))
        
        # 检查置信度告警
        if snapshot.confidence < self.alert_thresholds["confidence_min"]:
            alerts.append(PerformanceAlert(
                alert_type="confidence_low",
                severity="info",
                message=f"置信度过低: {snapshot.confidence:.2f}",
                timestamp=datetime.now(),
                threshold_value=self.alert_thresholds["confidence_min"],
                actual_value=snapshot.confidence
            ))
        
        # 添加告警
        for alert in alerts:
            self._add_alert(alert)
    
    def _add_alert(self, alert: PerformanceAlert) -> None:
        """添加告警"""
        self._alerts.append(alert)
        # 限制告警数量
        if len(self._alerts) > self._max_alerts:
            self._alerts = self._alerts[-self._max_alerts:]
        
        self.logger.warning(f"性能告警: {alert.message}")
    
    def get_performance_stats(self, force_refresh: bool = False) -> PerformanceStats:
        """
        获取性能统计
        
        Args:
            force_refresh: 是否强制刷新
            
        Returns:
            性能统计
        """
        with self._lock:
            # 检查缓存
            if not force_refresh and self._is_cache_valid():
                return self._stats_cache
            
            # 计算统计数据
            stats = self._calculate_stats()
            
            # 更新缓存
            self._stats_cache = stats
            self._cache_timestamp = time.time()
            
            return stats
    
    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        return (self._stats_cache is not None and 
                time.time() - self._cache_timestamp < self._cache_ttl)
    
    def _invalidate_cache(self) -> None:
        """使缓存失效"""
        self._stats_cache = None
        self._cache_timestamp = 0
    
    def _calculate_stats(self) -> PerformanceStats:
        """计算性能统计"""
        if not self._snapshots:
            return PerformanceStats(
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                success_rate=0.0,
                average_processing_time=0.0,
                average_confidence=0.0,
                min_processing_time=0.0,
                max_processing_time=0.0,
                median_processing_time=0.0,
                p95_processing_time=0.0,
                p99_processing_time=0.0,
                requests_per_minute=0.0,
                uptime_ratio=0.0
            )
        
        # 提取处理时间列表
        processing_times = [s.processing_time for s in self._snapshots]
        confidence_scores = [s.confidence for s in self._snapshots]
        
        # 计算基础统计
        success_rate = self._successful_requests / self._total_requests if self._total_requests > 0 else 0.0
        avg_processing_time = statistics.mean(processing_times)
        avg_confidence = statistics.mean(confidence_scores)
        
        # 计算分位数
        sorted_times = sorted(processing_times)
        median_time = statistics.median(sorted_times)
        p95_time = self._percentile(sorted_times, 95)
        p99_time = self._percentile(sorted_times, 99)
        
        # 计算请求频率
        current_time = time.time()
        time_window = 300  # 5分钟窗口
        recent_requests = [s for s in self._snapshots if current_time - s.timestamp <= time_window]
        requests_per_minute = len(recent_requests) / (time_window / 60) if time_window > 0 else 0.0
        
        # 计算正常运行时间比率
        uptime = current_time - self._start_time
        active_time = sum(s.processing_time for s in self._snapshots)
        uptime_ratio = (uptime - active_time) / uptime if uptime > 0 else 1.0
        
        return PerformanceStats(
            total_requests=self._total_requests,
            successful_requests=self._successful_requests,
            failed_requests=self._failed_requests,
            success_rate=success_rate,
            average_processing_time=avg_processing_time,
            average_confidence=avg_confidence,
            min_processing_time=min(processing_times),
            max_processing_time=max(processing_times),
            median_processing_time=median_time,
            p95_processing_time=p95_time,
            p99_processing_time=p99_time,
            requests_per_minute=requests_per_minute,
            uptime_ratio=uptime_ratio
        )
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        k = (len(data) - 1) * percentile / 100
        f = int(k)
        c = k - f
        if f + 1 < len(data):
            return data[f] * (1 - c) + data[f + 1] * c
        else:
            return data[f]
    
    def get_recent_snapshots(self, count: int = 10) -> List[PerformanceSnapshot]:
        """
        获取最近的性能快照
        
        Args:
            count: 快照数量
            
        Returns:
            快照列表
        """
        with self._lock:
            return list(self._snapshots)[-count:]
    
    def get_performance_trend(self, metric: str, window: int = 50) -> Dict[str, Any]:
        """
        获取性能趋势
        
        Args:
            metric: 指标名称
            window: 窗口大小
            
        Returns:
            趋势数据
        """
        with self._lock:
            if metric not in self._performance_trends:
                return {"error": f"未知指标: {metric}"}
            
            data = list(self._performance_trends[metric])[-window:]
            
            if len(data) < 2:
                return {"data": data, "trend": "insufficient_data"}
            
            # 计算趋势
            recent_avg = statistics.mean(data[-min(10, len(data)):])
            older_avg = statistics.mean(data[:-min(10, len(data))]) if len(data) > 10 else recent_avg
            
            if recent_avg > older_avg * 1.1:
                trend = "increasing"
            elif recent_avg < older_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
            
            return {
                "data": data,
                "trend": trend,
                "recent_average": recent_avg,
                "older_average": older_avg,
                "change_percent": ((recent_avg - older_avg) / older_avg * 100) if older_avg != 0 else 0
            }
    
    def get_alerts(self, severity: Optional[str] = None, 
                  since: Optional[datetime] = None) -> List[PerformanceAlert]:
        """
        获取告警列表
        
        Args:
            severity: 严重程度过滤
            since: 时间过滤
            
        Returns:
            告警列表
        """
        with self._lock:
            alerts = self._alerts.copy()
            
            # 过滤严重程度
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            
            # 过滤时间
            if since:
                alerts = [a for a in alerts if a.timestamp >= since]
            
            return alerts
    
    def reset_metrics(self) -> None:
        """重置性能指标"""
        with self._lock:
            self._total_requests = 0
            self._successful_requests = 0
            self._failed_requests = 0
            self._start_time = time.time()
            self._last_activity = 0
            self._snapshots.clear()
            self._alerts.clear()
            self._invalidate_cache()
            
            # 清空趋势数据
            for trend_list in self._performance_trends.values():
                trend_list.clear()
            
            self.logger.info("性能指标已重置")
    
    def export_performance_data(self) -> Dict[str, Any]:
        """
        导出性能数据
        
        Returns:
            性能数据字典
        """
        with self._lock:
            return {
                "agent_id": self.agent_id,
                "stats": self.get_performance_stats().__dict__,
                "snapshots": [s.__dict__ for s in list(self._snapshots)[-100:]],  # 最近100个快照
                "alerts": [a.__dict__ for a in self._alerts[-50:]],  # 最近50个告警
                "trends": {k: list(v) for k, v in self._performance_trends.items()},
                "thresholds": self.alert_thresholds,
                "export_timestamp": datetime.now().isoformat()
            }
    
    def get_health_indicators(self) -> Dict[str, Any]:
        """
        获取健康指标
        
        Returns:
            健康指标
        """
        stats = self.get_performance_stats()
        
        # 计算健康分数
        health_score = 0.0
        max_score = 100.0
        
        # 成功率权重 (30%)
        success_score = stats.success_rate * 30
        health_score += success_score
        
        # 处理时间权重 (25%)
        time_score = max(0, (1 - min(stats.average_processing_time / 5.0, 1)) * 25)
        health_score += time_score
        
        # 置信度权重 (20%)
        confidence_score = stats.average_confidence * 20
        health_score += confidence_score
        
        # 正常运行时间权重 (15%)
        uptime_score = stats.uptime_ratio * 15
        health_score += uptime_score
        
        # 请求频率权重 (10%)
        frequency_score = max(0, (1 - min(stats.requests_per_minute / 50.0, 1)) * 10)
        health_score += frequency_score
        
        # 确定健康状态
        if health_score >= 80:
            health_status = "excellent"
        elif health_score >= 60:
            health_status = "good"
        elif health_score >= 40:
            health_status = "fair"
        else:
            health_status = "poor"
        
        return {
            "health_score": round(health_score, 2),
            "health_status": health_status,
            "max_score": max_score,
            "components": {
                "success_rate": round(success_score, 2),
                "processing_time": round(time_score, 2),
                "confidence": round(confidence_score, 2),
                "uptime": round(uptime_score, 2),
                "frequency": round(frequency_score, 2)
            },
            "stats": stats.__dict__
        }
    
    def update_thresholds(self, new_thresholds: Dict[str, float]) -> bool:
        """
        更新告警阈值
        
        Args:
            new_thresholds: 新阈值
            
        Returns:
            是否更新成功
        """
        try:
            self.alert_thresholds.update(new_thresholds)
            self.logger.info(f"告警阈值更新: {new_thresholds}")
            return True
        except Exception as e:
            self.logger.error(f"更新告警阈值失败: {e}")
            return False