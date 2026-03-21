"""
技能性能监控系统

监控技能执行性能，包括执行时间、成功率、调用频率、错误统计等指标。
与质量指标跟踪系统集成，提供全面的技能性能分析。
"""

import time
import json
import sqlite3
import threading
import psutil
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import statistics
import warnings
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False
    warnings.warn("resource module not available on this platform")


class PerformanceMetricType(Enum):
    """性能指标类型"""
    EXECUTION_TIME = "execution_time"
    SUCCESS_RATE = "success_rate"
    INVOCATION_COUNT = "invocation_count"
    ERROR_COUNT = "error_count"
    RESOURCE_USAGE = "resource_usage"
    CONCURRENT_EXECUTIONS = "concurrent_executions"
    CACHE_HIT_RATE = "cache_hit_rate"
    LATENCY = "latency"
    THROUGHPUT = "throughput"


class ErrorType(Enum):
    """错误类型"""
    TIMEOUT = "timeout"
    EXECUTION_ERROR = "execution_error"
    VALIDATION_ERROR = "validation_error"
    RESOURCE_LIMIT = "resource_limit"
    CONNECTION_ERROR = "connection_error"
    PERMISSION_ERROR = "permission_error"
    OTHER = "other"


@dataclass
class PerformanceMetric:
    """性能指标数据点"""
    skill_id: str
    metric_type: PerformanceMetricType
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "skill_id": self.skill_id,
            "metric_type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetric':
        """从字典创建"""
        return cls(
            skill_id=data["skill_id"],
            metric_type=PerformanceMetricType(data["metric_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            value=data["value"],
            metadata=data.get("metadata", {})
        )


@dataclass
class PerformanceSnapshot:
    """性能快照 - 技能执行时的性能数据"""
    skill_id: str
    start_time: datetime
    end_time: datetime
    execution_time_ms: float
    success: bool
    error_type: Optional[ErrorType] = None
    error_message: Optional[str] = None
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    concurrent_count: int = 1
    input_size: Optional[int] = None
    output_size: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "skill_id": self.skill_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "execution_time_ms": self.execution_time_ms,
            "success": self.success,
            "error_type": self.error_type.value if self.error_type else None,
            "error_message": self.error_message,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "concurrent_count": self.concurrent_count,
            "input_size": self.input_size,
            "output_size": self.output_size,
            "metadata": self.metadata
        }


@dataclass
class PerformanceThreshold:
    """性能阈值"""
    metric_type: PerformanceMetricType
    skill_id: Optional[str] = None  # 如果为None则适用于所有技能
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    window_minutes: int = 60  # 时间窗口（分钟）
    min_samples: int = 10  # 最小样本数
    
    def should_alert(self, value: float, current_count: int) -> Tuple[bool, str]:
        """检查是否应该告警"""
        if current_count < self.min_samples:
            return False, "样本不足"
            
        if self.critical_threshold is not None and value >= self.critical_threshold:
            return True, f"严重：{self.metric_type.value} = {value:.2f} ≥ {self.critical_threshold}"
            
        if self.warning_threshold is not None and value >= self.warning_threshold:
            return True, f"警告：{self.metric_type.value} = {value:.2f} ≥ {self.warning_threshold}"
            
        return False, "正常"


class PerformanceMonitor:
    """技能性能监控器
    
    监控技能执行性能，收集指标数据，提供告警和分析功能。
    """
    
    def __init__(self, storage_path: Optional[str] = None, enable_resource_monitoring: bool = True):
        """初始化性能监控器
        
        Args:
            storage_path: 存储路径，如果为None则使用默认路径
            enable_resource_monitoring: 是否启用资源监控（CPU/内存）
        """
        if storage_path is None:
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            storage_path = os.path.join(script_dir, "performance_metrics.db")
        
        self.storage_path = storage_path
        self.enable_resource_monitoring = enable_resource_monitoring
        self._lock = threading.RLock()
        self._concurrent_executions = defaultdict(int)  # skill_id -> 并发执行数
        self._error_counts = defaultdict(lambda: defaultdict(int))  # skill_id -> error_type -> count
        self._invocation_counts = defaultdict(int)  # skill_id -> 调用次数
        self._success_counts = defaultdict(int)  # skill_id -> 成功次数
        
        # 默认阈值配置
        self.default_thresholds = [
            PerformanceThreshold(
                metric_type=PerformanceMetricType.EXECUTION_TIME,
                warning_threshold=5000,  # 5秒
                critical_threshold=10000  # 10秒
            ),
            PerformanceThreshold(
                metric_type=PerformanceMetricType.SUCCESS_RATE,
                warning_threshold=0.8,  # 80%成功率警告
                critical_threshold=0.5  # 50%成功率严重
            ),
            PerformanceThreshold(
                metric_type=PerformanceMetricType.ERROR_COUNT,
                warning_threshold=10,  # 10个错误
                critical_threshold=50  # 50个错误
            )
        ]
        
        self.custom_thresholds: List[PerformanceThreshold] = []
        
        # 初始化存储
        self._init_storage()
    
    def _init_storage(self):
        """初始化存储"""
        with self._lock:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            # 创建性能快照表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_id TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    execution_time_ms REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_type TEXT,
                    error_message TEXT,
                    cpu_percent REAL,
                    memory_mb REAL,
                    concurrent_count INTEGER DEFAULT 1,
                    input_size INTEGER,
                    output_size INTEGER,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建性能指标表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    value REAL NOT NULL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建性能摘要表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_summaries (
                    skill_id TEXT PRIMARY KEY,
                    first_seen DATETIME,
                    last_updated DATETIME,
                    total_invocations INTEGER DEFAULT 0,
                    successful_invocations INTEGER DEFAULT 0,
                    avg_execution_time_ms REAL DEFAULT 0.0,
                    avg_cpu_percent REAL DEFAULT 0.0,
                    avg_memory_mb REAL DEFAULT 0.0,
                    max_concurrent INTEGER DEFAULT 1,
                    error_counts TEXT,  -- JSON: {error_type: count}
                    performance_summary TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建阈值配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_thresholds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_id TEXT,
                    metric_type TEXT NOT NULL,
                    warning_threshold REAL,
                    critical_threshold REAL,
                    window_minutes INTEGER DEFAULT 60,
                    min_samples INTEGER DEFAULT 10,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建告警记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_id TEXT,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    threshold_type TEXT NOT NULL,  -- warning/critical
                    message TEXT NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_at DATETIME,
                    acknowledged_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_snapshot_skill ON performance_snapshots(skill_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_snapshot_time ON performance_snapshots(start_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_metric_skill ON performance_metrics(skill_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_metric_type ON performance_metrics(metric_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_metric_time ON performance_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_alerts_time ON performance_alerts(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_alerts_skill ON performance_alerts(skill_id)')
            
            conn.commit()
            conn.close()
    
    def track_execution_start(self, skill_id: str) -> str:
        """跟踪执行开始
        
        Args:
            skill_id: 技能ID
            
        Returns:
            str: 跟踪ID
        """
        with self._lock:
            # 增加并发计数
            self._concurrent_executions[skill_id] += 1
            self._invocation_counts[skill_id] += 1
            
            # 生成跟踪ID
            track_id = f"{skill_id}_{int(time.time() * 1000)}"
            
            return track_id
    
    def track_execution_end(
        self, 
        skill_id: str, 
        success: bool, 
        execution_time_ms: float,
        error_type: Optional[ErrorType] = None,
        error_message: Optional[str] = None,
        input_size: Optional[int] = None,
        output_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PerformanceSnapshot:
        """跟踪执行结束
        
        Args:
            skill_id: 技能ID
            success: 是否成功
            execution_time_ms: 执行时间（毫秒）
            error_type: 错误类型
            error_message: 错误消息
            input_size: 输入数据大小（字节）
            output_size: 输出数据大小（字节）
            metadata: 额外元数据
            
        Returns:
            PerformanceSnapshot: 性能快照
        """
        start_time = datetime.now() - timedelta(milliseconds=execution_time_ms)
        end_time = datetime.now()
        
        # 收集资源使用信息
        cpu_percent = None
        memory_mb = None
        if self.enable_resource_monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024  # 转换为MB
            except Exception as e:
                warnings.warn(f"资源监控失败: {e}")
        
        with self._lock:
            # 减少并发计数
            self._concurrent_executions[skill_id] = max(0, self._concurrent_executions[skill_id] - 1)
            
            # 更新成功计数
            if success:
                self._success_counts[skill_id] += 1
            
            # 更新错误计数
            if error_type:
                self._error_counts[skill_id][error_type] += 1
            
            # 创建快照
            snapshot = PerformanceSnapshot(
                skill_id=skill_id,
                start_time=start_time,
                end_time=end_time,
                execution_time_ms=execution_time_ms,
                success=success,
                error_type=error_type,
                error_message=error_message,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                concurrent_count=self._concurrent_executions[skill_id],
                input_size=input_size,
                output_size=output_size,
                metadata=metadata or {}
            )
            
            # 存储快照
            self._store_snapshot(snapshot)
            
            # 更新性能指标
            self._update_performance_metrics(skill_id, snapshot)
            
            # 检查阈值并告警
            self._check_thresholds(skill_id)
            
            return snapshot
    
    def _store_snapshot(self, snapshot: PerformanceSnapshot):
        """存储性能快照"""
        with self._lock:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_snapshots 
                (skill_id, start_time, end_time, execution_time_ms, success, 
                 error_type, error_message, cpu_percent, memory_mb, 
                 concurrent_count, input_size, output_size, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot.skill_id,
                snapshot.start_time.isoformat(),
                snapshot.end_time.isoformat(),
                snapshot.execution_time_ms,
                snapshot.success,
                snapshot.error_type.value if snapshot.error_type else None,
                snapshot.error_message,
                snapshot.cpu_percent,
                snapshot.memory_mb,
                snapshot.concurrent_count,
                snapshot.input_size,
                snapshot.output_size,
                json.dumps(snapshot.metadata, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
    
    def _update_performance_metrics(self, skill_id: str, snapshot: PerformanceSnapshot):
        """更新性能指标"""
        with self._lock:
            now = datetime.now()
            
            # 1. 执行时间指标
            if snapshot.execution_time_ms > 0:
                time_metric = PerformanceMetric(
                    skill_id=skill_id,
                    metric_type=PerformanceMetricType.EXECUTION_TIME,
                    timestamp=now,
                    value=snapshot.execution_time_ms,
                    metadata={"success": snapshot.success}
                )
                self._store_metric(time_metric)
            
            # 2. 成功率指标（基于最近N次执行）
            total_invocations = self._invocation_counts[skill_id]
            successful_invocations = self._success_counts[skill_id]
            if total_invocations > 0:
                success_rate = successful_invocations / total_invocations
                success_metric = PerformanceMetric(
                    skill_id=skill_id,
                    metric_type=PerformanceMetricType.SUCCESS_RATE,
                    timestamp=now,
                    value=success_rate,
                    metadata={"total": total_invocations, "successful": successful_invocations}
                )
                self._store_metric(success_metric)
            
            # 3. 调用次数指标
            invocation_metric = PerformanceMetric(
                skill_id=skill_id,
                metric_type=PerformanceMetricType.INVOCATION_COUNT,
                timestamp=now,
                value=total_invocations,
                metadata={"period": "cumulative"}
            )
            self._store_metric(invocation_metric)
            
            # 4. 错误计数指标
            if snapshot.error_type:
                error_count = self._error_counts[skill_id][snapshot.error_type]
                error_metric = PerformanceMetric(
                    skill_id=skill_id,
                    metric_type=PerformanceMetricType.ERROR_COUNT,
                    timestamp=now,
                    value=error_count,
                    metadata={"error_type": snapshot.error_type.value}
                )
                self._store_metric(error_metric)
            
            # 5. 资源使用指标
            if snapshot.cpu_percent is not None:
                cpu_metric = PerformanceMetric(
                    skill_id=skill_id,
                    metric_type=PerformanceMetricType.RESOURCE_USAGE,
                    timestamp=now,
                    value=snapshot.cpu_percent,
                    metadata={"resource_type": "cpu_percent"}
                )
                self._store_metric(cpu_metric)
            
            if snapshot.memory_mb is not None:
                memory_metric = PerformanceMetric(
                    skill_id=skill_id,
                    metric_type=PerformanceMetricType.RESOURCE_USAGE,
                    timestamp=now,
                    value=snapshot.memory_mb,
                    metadata={"resource_type": "memory_mb"}
                )
                self._store_metric(memory_metric)
            
            # 6. 并发执行指标
            concurrent_metric = PerformanceMetric(
                skill_id=skill_id,
                metric_type=PerformanceMetricType.CONCURRENT_EXECUTIONS,
                timestamp=now,
                value=snapshot.concurrent_count,
                metadata={}
            )
            self._store_metric(concurrent_metric)
            
            # 更新技能摘要
            self._update_performance_summary(skill_id)
    
    def _store_metric(self, metric: PerformanceMetric):
        """存储性能指标"""
        with self._lock:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_metrics (skill_id, metric_type, timestamp, value, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                metric.skill_id,
                metric.metric_type.value,
                metric.timestamp.isoformat(),
                metric.value,
                json.dumps(metric.metadata, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
    
    def _update_performance_summary(self, skill_id: str):
        """更新性能摘要"""
        with self._lock:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            # 获取最近的快照（最近100次）
            cursor.execute('''
                SELECT * FROM performance_snapshots 
                WHERE skill_id = ? 
                ORDER BY start_time DESC 
                LIMIT 100
            ''', (skill_id,))
            
            snapshots = cursor.fetchall()
            
            if not snapshots:
                return
            
            # 计算统计信息
            total_invocations = len(snapshots)
            successful_invocations = sum(1 for s in snapshots if s[5])  # 第6列是success
            
            execution_times = [s[4] for s in snapshots if s[4] > 0]  # 第5列是execution_time_ms
            avg_execution_time = statistics.mean(execution_times) if execution_times else 0.0
            
            cpu_values = [s[8] for s in snapshots if s[8] is not None]  # 第9列是cpu_percent
            avg_cpu = statistics.mean(cpu_values) if cpu_values else 0.0
            
            memory_values = [s[9] for s in snapshots if s[9] is not None]  # 第10列是memory_mb
            avg_memory = statistics.mean(memory_values) if memory_values else 0.0
            
            concurrent_counts = [s[10] for s in snapshots if s[10] is not None]  # 第11列是concurrent_count
            max_concurrent = max(concurrent_counts) if concurrent_counts else 1
            
            # 错误计数
            error_counts = defaultdict(int)
            for snapshot in snapshots:
                error_type = snapshot[6]  # 第7列是error_type
                if error_type:
                    error_counts[error_type] += 1
            
            # 创建性能摘要
            summary = {
                "skill_id": skill_id,
                "invocation_stats": {
                    "total": total_invocations,
                    "successful": successful_invocations,
                    "success_rate": successful_invocations / total_invocations if total_invocations > 0 else 0
                },
                "execution_time_stats": {
                    "avg_ms": avg_execution_time,
                    "min_ms": min(execution_times) if execution_times else 0,
                    "max_ms": max(execution_times) if execution_times else 0,
                    "p95_ms": statistics.quantiles(execution_times, n=20)[18] if len(execution_times) >= 20 else 0
                },
                "resource_stats": {
                    "avg_cpu_percent": avg_cpu,
                    "avg_memory_mb": avg_memory
                },
                "concurrency_stats": {
                    "max_concurrent": max_concurrent
                },
                "error_stats": dict(error_counts),
                "last_updated": datetime.now().isoformat()
            }
            
            # 获取现有摘要
            cursor.execute('SELECT * FROM performance_summaries WHERE skill_id = ?', (skill_id,))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有摘要
                cursor.execute('''
                    UPDATE performance_summaries 
                    SET last_updated = ?, total_invocations = ?, successful_invocations = ?,
                        avg_execution_time_ms = ?, avg_cpu_percent = ?, avg_memory_mb = ?,
                        max_concurrent = ?, error_counts = ?, performance_summary = ?
                    WHERE skill_id = ?
                ''', (
                    datetime.now().isoformat(),
                    total_invocations,
                    successful_invocations,
                    avg_execution_time,
                    avg_cpu,
                    avg_memory,
                    max_concurrent,
                    json.dumps(dict(error_counts), ensure_ascii=False),
                    json.dumps(summary, ensure_ascii=False),
                    skill_id
                ))
            else:
                # 插入新摘要
                cursor.execute('''
                    INSERT INTO performance_summaries 
                    (skill_id, first_seen, last_updated, total_invocations, successful_invocations,
                     avg_execution_time_ms, avg_cpu_percent, avg_memory_mb, max_concurrent,
                     error_counts, performance_summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    skill_id,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    total_invocations,
                    successful_invocations,
                    avg_execution_time,
                    avg_cpu,
                    avg_memory,
                    max_concurrent,
                    json.dumps(dict(error_counts), ensure_ascii=False),
                    json.dumps(summary, ensure_ascii=False)
                ))
            
            conn.commit()
            conn.close()
    
    def _check_thresholds(self, skill_id: str):
        """检查性能阈值"""
        with self._lock:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            # 获取最近1小时的性能指标
            one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
            
            # 检查所有阈值
            all_thresholds = self.default_thresholds + self.custom_thresholds
            
            for threshold in all_thresholds:
                # 检查是否适用于此技能
                if threshold.skill_id and threshold.skill_id != skill_id:
                    continue
                
                # 获取最近指标
                cursor.execute('''
                    SELECT value FROM performance_metrics 
                    WHERE skill_id = ? AND metric_type = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (
                    skill_id if threshold.skill_id is None else threshold.skill_id,
                    threshold.metric_type.value,
                    one_hour_ago,
                    threshold.min_samples * 2  # 获取更多样本用于计算
                ))
                
                results = cursor.fetchall()
                if len(results) < threshold.min_samples:
                    continue
                
                # 计算指标值（平均值）
                values = [r[0] for r in results[:threshold.min_samples]]
                avg_value = statistics.mean(values)
                
                # 检查阈值
                should_alert, message = threshold.should_alert(avg_value, len(values))
                
                if should_alert:
                    # 确定告警级别
                    threshold_type = "warning"
                    if (threshold.critical_threshold is not None and 
                        avg_value >= threshold.critical_threshold):
                        threshold_type = "critical"
                    
                    # 记录告警
                    cursor.execute('''
                        INSERT INTO performance_alerts 
                        (skill_id, metric_type, value, threshold_type, message)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        skill_id,
                        threshold.metric_type.value,
                        avg_value,
                        threshold_type,
                        message
                    ))
            
            conn.commit()
            conn.close()
    
    def get_performance_summary(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取技能性能摘要
        
        Args:
            skill_id: 技能ID
            
        Returns:
            Dict[str, Any]: 性能摘要，如果技能不存在则返回None
        """
        with self._lock:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT performance_summary FROM performance_summaries WHERE skill_id = ?', (skill_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return json.loads(result[0])
            
            return None
    
    def get_performance_trend(self, skill_id: str, metric_type: PerformanceMetricType, 
                             days: int = 7) -> List[Dict[str, Any]]:
        """获取性能趋势数据
        
        Args:
            skill_id: 技能ID
            metric_type: 指标类型
            days: 天数
            
        Returns:
            List[Dict[str, Any]]: 趋势数据
        """
        with self._lock:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute('''
                SELECT timestamp, value, metadata FROM performance_metrics 
                WHERE skill_id = ? AND metric_type = ? AND timestamp >= ?
                ORDER BY timestamp
            ''', (skill_id, metric_type.value, cutoff))
            
            results = cursor.fetchall()
            conn.close()
            
            trend_data = []
            for timestamp_str, value, metadata_str in results:
                trend_data.append({
                    "timestamp": timestamp_str,
                    "value": value,
                    "metadata": json.loads(metadata_str) if metadata_str else {}
                })
            
            return trend_data
    
    def get_active_alerts(self, acknowledged: bool = False) -> List[Dict[str, Any]]:
        """获取活动告警
        
        Args:
            acknowledged: 是否包含已确认的告警
            
        Returns:
            List[Dict[str, Any]]: 告警列表
        """
        with self._lock:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            if acknowledged:
                cursor.execute('''
                    SELECT * FROM performance_alerts 
                    ORDER BY created_at DESC 
                    LIMIT 100
                ''')
            else:
                cursor.execute('''
                    SELECT * FROM performance_alerts 
                    WHERE acknowledged = FALSE 
                    ORDER BY created_at DESC 
                    LIMIT 100
                ''')
            
            results = cursor.fetchall()
            conn.close()
            
            alerts = []
            for row in results:
                alerts.append({
                    "id": row[0],
                    "skill_id": row[1],
                    "metric_type": row[2],
                    "value": row[3],
                    "threshold_type": row[4],
                    "message": row[5],
                    "acknowledged": bool(row[6]),
                    "acknowledged_at": row[7],
                    "acknowledged_by": row[8],
                    "created_at": row[9]
                })
            
            return alerts
    
    def add_custom_threshold(self, threshold: PerformanceThreshold):
        """添加自定义阈值
        
        Args:
            threshold: 性能阈值
        """
        with self._lock:
            # 检查是否已存在
            for existing in self.custom_thresholds:
                if (existing.skill_id == threshold.skill_id and 
                    existing.metric_type == threshold.metric_type):
                    existing.warning_threshold = threshold.warning_threshold
                    existing.critical_threshold = threshold.critical_threshold
                    existing.window_minutes = threshold.window_minutes
                    existing.min_samples = threshold.min_samples
                    break
            else:
                self.custom_thresholds.append(threshold)
            
            # 存储到数据库
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_thresholds 
                (skill_id, metric_type, warning_threshold, critical_threshold, 
                 window_minutes, min_samples)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                threshold.skill_id,
                threshold.metric_type.value,
                threshold.warning_threshold,
                threshold.critical_threshold,
                threshold.window_minutes,
                threshold.min_samples
            ))
            
            conn.commit()
            conn.close()
    
    def create_execution_context(self, skill_id: str) -> 'PerformanceExecutionContext':
        """创建执行上下文（用于with语句）
        
        Args:
            skill_id: 技能ID
            
        Returns:
            PerformanceExecutionContext: 执行上下文
        """
        return PerformanceExecutionContext(self, skill_id)


class PerformanceExecutionContext:
    """性能执行上下文（上下文管理器）
    
    用于在with语句中自动跟踪执行性能。
    """
    
    def __init__(self, monitor: PerformanceMonitor, skill_id: str):
        """初始化执行上下文
        
        Args:
            monitor: 性能监控器
            skill_id: 技能ID
        """
        self.monitor = monitor
        self.skill_id = skill_id
        self.track_id = None
        self.start_time = None
        self.success = True
        self.error_type = None
        self.error_message = None
    
    def __enter__(self):
        """进入上下文"""
        self.track_id = self.monitor.track_execution_start(self.skill_id)
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        end_time = time.time()
        execution_time_ms = (end_time - self.start_time) * 1000
        
        # 检查是否有异常
        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val)
            
            # 根据异常类型确定错误类型
            if exc_type == TimeoutError:
                self.error_type = ErrorType.TIMEOUT
            elif exc_type == PermissionError:
                self.error_type = ErrorType.PERMISSION_ERROR
            else:
                self.error_type = ErrorType.EXECUTION_ERROR
        
        # 记录执行结束
        self.monitor.track_execution_end(
            skill_id=self.skill_id,
            success=self.success,
            execution_time_ms=execution_time_ms,
            error_type=self.error_type,
            error_message=self.error_message
        )