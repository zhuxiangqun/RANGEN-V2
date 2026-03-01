"""
日志聚合服务
提供统一的日志收集、聚合、分析和检索功能
"""

import asyncio
import logging
import json
import threading
import re
from typing import Dict, Any, List, Optional, Callable, Pattern
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import queue

from src.utils.logging_helper import get_module_logger, ModuleType
from src.utils.unified_centers import get_unified_config_center, get_unified_intelligent_center

logger = logging.getLogger(__name__)

@dataclass
class LogEntry:
    """日志条目数据结构"""
    timestamp: datetime
    level: str
    logger_name: str
    message: str
    module: str = ""
    function: str = ""
    line_number: int = 0
    thread_id: int = 0
    thread_name: str = ""
    process_id: int = 0
    exception_info: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LogPattern:
    """日志模式匹配规则"""
    pattern_id: str
    name: str
    regex: Pattern[str]
    level: str
    category: str
    action: str  # alert, ignore, highlight, aggregate
    description: str = ""

@dataclass
class LogAnalysisResult:
    """日志分析结果"""
    analysis_id: str
    time_range: tuple[datetime, datetime]
    total_entries: int
    error_count: int
    warning_count: int
    info_count: int
    debug_count: int
    patterns_detected: Dict[str, int]
    anomalies: List[Dict[str, Any]]
    trends: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime

class LogAggregator:
    """
    日志聚合服务
    提供日志收集、实时分析、模式识别和智能告警功能
    """

    def __init__(self):
        self.module_logger = get_module_logger(ModuleType.SERVICE, "LogAggregator")
        self.config_center = get_unified_config_center()
        self.intelligent_center = get_unified_intelligent_center()

        # 配置参数
        self.max_entries = self.config_center.get_config_value(
            "log_aggregator", "max_entries", 100000
        )
        self.retention_hours = self.config_center.get_config_value(
            "log_aggregator", "retention_hours", 24
        )
        self.analysis_interval = self.config_center.get_config_value(
            "log_aggregator", "analysis_interval_seconds", 60
        )

        # 数据存储
        self.log_entries: deque[LogEntry] = deque(maxlen=self.max_entries)
        self.log_patterns: Dict[str, LogPattern] = {}
        self.log_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.anomaly_patterns: List[Dict[str, Any]] = []

        # 队列和锁
        self.log_queue: queue.Queue = queue.Queue(maxsize=10000)
        self._processing_lock = threading.Lock()

        # 任务管理
        self._collection_task: Optional[asyncio.Task] = None
        self._analysis_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        # 回调函数
        self.alert_callbacks: List[Callable[[LogEntry, LogPattern], None]] = []
        self.anomaly_callbacks: List[Callable[[Dict[str, Any]], None]] = []

        # 初始化
        self._initialize_patterns()
        self._setup_log_capture()

    def _initialize_patterns(self):
        """初始化日志模式"""
        default_patterns = [
            {
                "pattern_id": "error_exception",
                "name": "异常错误",
                "regex": r"(?i)(exception|error|traceback|failed|critical)",
                "level": "ERROR",
                "category": "error",
                "action": "alert",
                "description": "检测异常和错误信息"
            },
            {
                "pattern_id": "performance_warning",
                "name": "性能警告",
                "regex": r"(?i)(slow|timeout|high.*usage|memory.*leak|cpu.*spike)",
                "level": "WARNING",
                "category": "performance",
                "action": "alert",
                "description": "检测性能相关警告"
            },
            {
                "pattern_id": "security_alert",
                "name": "安全告警",
                "regex": r"(?i)(unauthorized|forbidden|attack|hacker|breach|injection)",
                "level": "WARNING",
                "category": "security",
                "action": "alert",
                "description": "检测安全相关事件"
            },
            {
                "pattern_id": "connection_issue",
                "name": "连接问题",
                "regex": r"(?i)(connection.*failed|network.*error|timeout|unreachable)",
                "level": "WARNING",
                "category": "connectivity",
                "action": "highlight",
                "description": "检测连接和网络问题"
            }
        ]

        for pattern_data in default_patterns:
            pattern = LogPattern(
                pattern_id=pattern_data["pattern_id"],
                name=pattern_data["name"],
                regex=re.compile(pattern_data["regex"]),
                level=pattern_data["level"],
                category=pattern_data["category"],
                action=pattern_data["action"],
                description=pattern_data["description"]
            )
            self.log_patterns[pattern.pattern_id] = pattern

        self.module_logger.info(f"✅ 已初始化 {len(self.log_patterns)} 个日志模式")

    def _setup_log_capture(self):
        """设置日志捕获"""
        # 创建自定义处理器来捕获所有日志
        class LogCaptureHandler(logging.Handler):
            def __init__(self, aggregator):
                super().__init__()
                self.aggregator = aggregator

            def emit(self, record):
                try:
                    # 将日志记录转换为LogEntry
                    log_entry = LogEntry(
                        timestamp=datetime.fromtimestamp(record.created),
                        level=record.levelname,
                        logger_name=record.name,
                        message=record.getMessage(),
                        module=getattr(record, 'module', ''),
                        function=getattr(record, 'funcName', ''),
                        line_number=getattr(record, 'lineno', 0),
                        thread_id=getattr(record, 'thread', 0),
                        thread_name=getattr(record, 'threadName', ''),
                        process_id=getattr(record, 'process', 0),
                        exception_info=getattr(record, 'exc_text', None),
                        extra_data=getattr(record, '__dict__', {})
                    )

                    # 添加到队列
                    try:
                        self.aggregator.log_queue.put_nowait(log_entry)
                    except queue.Full:
                        # 队列满时，移除最旧的条目
                        if self.aggregator.log_entries:
                            self.aggregator.log_entries.popleft()
                        self.aggregator.log_entries.append(log_entry)

                except Exception as e:
                    # 避免递归日志
                    pass

        # 添加处理器到根日志器
        capture_handler = LogCaptureHandler(self)
        capture_handler.setLevel(logging.DEBUG)

        # 获取根日志器并添加处理器
        root_logger = logging.getLogger()
        root_logger.addHandler(capture_handler)

        self.module_logger.info("✅ 日志捕获处理器已设置")

    def add_log_pattern(self, pattern: LogPattern):
        """添加日志模式"""
        self.log_patterns[pattern.pattern_id] = pattern
        self.module_logger.info(f"✅ 日志模式已添加: {pattern.name}")

    def add_alert_callback(self, callback: Callable[[LogEntry, LogPattern], None]):
        """添加告警回调函数"""
        self.alert_callbacks.append(callback)

    def add_anomaly_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """添加异常回调函数"""
        self.anomaly_callbacks.append(callback)

    async def start_aggregation(self):
        """启动日志聚合"""
        if self._running:
            return

        self._running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        self._analysis_task = asyncio.create_task(self._analysis_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        self.module_logger.info("✅ 日志聚合已启动")

    async def stop_aggregation(self):
        """停止日志聚合"""
        self._running = False

        for task in [self._collection_task, self._analysis_task, self._cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self.module_logger.info("🛑 日志聚合已停止")

    async def _collection_loop(self):
        """日志收集循环"""
        while self._running:
            try:
                # 处理队列中的日志条目
                while not self.log_queue.empty():
                    try:
                        log_entry = self.log_queue.get_nowait()
                        await self._process_log_entry(log_entry)
                    except queue.Empty:
                        break

            except Exception as e:
                self.module_logger.error(f"❌ 日志收集异常: {e}", exc_info=True)

            await asyncio.sleep(0.1)  # 短暂休眠避免CPU占用过高

    async def _process_log_entry(self, log_entry: LogEntry):
        """处理单个日志条目"""
        with self._processing_lock:
            # 添加到存储
            self.log_entries.append(log_entry)

            # 更新统计信息
            hour_key = log_entry.timestamp.strftime("%Y-%m-%d %H")
            if hour_key not in self.log_stats:
                self.log_stats[hour_key] = {
                    "total": 0, "ERROR": 0, "WARNING": 0, "INFO": 0, "DEBUG": 0
                }

            self.log_stats[hour_key]["total"] += 1
            self.log_stats[hour_key][log_entry.level] += 1

            # 检查模式匹配
            await self._check_pattern_matching(log_entry)

    async def _check_pattern_matching(self, log_entry: LogEntry):
        """检查日志模式匹配"""
        for pattern in self.log_patterns.values():
            if pattern.regex.search(log_entry.message):
                # 执行相应动作
                if pattern.action == "alert":
                    # 触发告警
                    for callback in self.alert_callbacks:
                        try:
                            callback(log_entry, pattern)
                        except Exception as e:
                            self.module_logger.error(f"❌ 告警回调失败: {e}")

                    self.module_logger.warning(f"🚨 日志模式匹配告警: {pattern.name} - {log_entry.message[:100]}")

                elif pattern.action == "highlight":
                    self.module_logger.info(f"🔍 日志模式高亮: {pattern.name} - {log_entry.message[:100]}")

    async def _analysis_loop(self):
        """日志分析循环"""
        while self._running:
            try:
                await self._analyze_log_patterns()
                await self._detect_anomalies()

            except Exception as e:
                self.module_logger.error(f"❌ 日志分析异常: {e}", exc_info=True)

            await asyncio.sleep(self.analysis_interval)

    async def _analyze_log_patterns(self):
        """分析日志模式"""
        try:
            # 分析最近1小时的日志
            current_time = datetime.now()
            one_hour_ago = current_time - timedelta(hours=1)

            recent_entries = [entry for entry in self.log_entries if entry.timestamp >= one_hour_ago]

            # 计算错误率趋势
            error_counts = defaultdict(int)
            for entry in recent_entries:
                hour = entry.timestamp.strftime("%Y-%m-%d %H")
                if entry.level in ["ERROR", "CRITICAL"]:
                    error_counts[hour] += 1

            # 检测错误率激增
            if len(error_counts) >= 2:
                hours = sorted(error_counts.keys())
                if len(hours) >= 2:
                    current_hour = hours[-1]
                    previous_hour = hours[-2]

                    current_errors = error_counts[current_hour]
                    previous_errors = error_counts[previous_hour]

                    if previous_errors > 0 and current_errors > previous_errors * 2:
                        anomaly = {
                            "type": "error_rate_spike",
                            "description": f"错误率激增: {previous_errors} → {current_errors}",
                            "timestamp": current_time,
                            "severity": "high"
                        }
                        self.anomaly_patterns.append(anomaly)

                        for callback in self.anomaly_callbacks:
                            try:
                                callback(anomaly)
                            except Exception as e:
                                self.module_logger.error(f"❌ 异常回调失败: {e}")

        except Exception as e:
            self.module_logger.error(f"❌ 日志模式分析失败: {e}")

    async def _detect_anomalies(self):
        """检测日志异常"""
        try:
            # 检测重复错误模式
            error_messages = defaultdict(int)
            current_time = datetime.now()
            one_hour_ago = current_time - timedelta(hours=1)

            for entry in self.log_entries:
                if entry.timestamp >= one_hour_ago and entry.level in ["ERROR", "CRITICAL"]:
                    # 简化错误消息（移除时间戳和变量部分）
                    simplified_msg = re.sub(r'\d+', '<NUM>', entry.message)
                    simplified_msg = re.sub(r'[a-fA-F0-9]{8,}', '<HEX>', simplified_msg)
                    error_messages[simplified_msg] += 1

            # 检测高频重复错误
            for message, count in error_messages.items():
                if count >= 10:  # 1小时内出现10次以上
                    anomaly = {
                        "type": "repeated_error",
                        "description": f"重复错误模式: {message[:100]} (出现{count}次)",
                        "timestamp": current_time,
                        "severity": "medium"
                    }
                    self.anomaly_patterns.append(anomaly)

        except Exception as e:
            self.module_logger.error(f"❌ 异常检测失败: {e}")

    async def _cleanup_loop(self):
        """数据清理循环"""
        while self._running:
            try:
                await self._cleanup_old_logs()

            except Exception as e:
                self.module_logger.error(f"❌ 日志清理异常: {e}", exc_info=True)

            await asyncio.sleep(3600)  # 每小时清理一次

    async def _cleanup_old_logs(self):
        """清理过期日志"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

        # 清理过期条目
        while self.log_entries and self.log_entries[0].timestamp < cutoff_time:
            self.log_entries.popleft()

        # 清理过期统计
        cutoff_hour = (datetime.now() - timedelta(hours=self.retention_hours)).strftime("%Y-%m-%d %H")
        expired_keys = [key for key in self.log_stats.keys() if key < cutoff_hour]
        for key in expired_keys:
            del self.log_stats[key]

    def generate_analysis_report(self, hours: int = 24) -> LogAnalysisResult:
        """生成日志分析报告"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        analysis_id = f"log_analysis_{int(end_time.timestamp())}"

        # 收集时间范围内的日志
        relevant_entries = [
            entry for entry in self.log_entries
            if start_time <= entry.timestamp <= end_time
        ]

        # 统计信息
        level_counts = defaultdict(int)
        module_counts = defaultdict(int)
        pattern_counts = defaultdict(int)

        for entry in relevant_entries:
            level_counts[entry.level] += 1
            if entry.module:
                module_counts[entry.module] += 1

            # 检查模式匹配
            for pattern in self.log_patterns.values():
                if pattern.regex.search(entry.message):
                    pattern_counts[pattern.name] += 1

        # 分析趋势
        trends = self._analyze_trends(start_time, end_time)

        # 生成建议
        recommendations = self._generate_log_recommendations(level_counts, trends)

        return LogAnalysisResult(
            analysis_id=analysis_id,
            time_range=(start_time, end_time),
            total_entries=len(relevant_entries),
            error_count=level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0),
            warning_count=level_counts.get("WARNING", 0),
            info_count=level_counts.get("INFO", 0),
            debug_count=level_counts.get("DEBUG", 0),
            patterns_detected=dict(pattern_counts),
            anomalies=self.anomaly_patterns[-10:],  # 最近10个异常
            trends=trends,
            recommendations=recommendations,
            generated_at=end_time
        )

    def _analyze_trends(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """分析日志趋势"""
        trends = {
            "error_trend": "stable",
            "warning_trend": "stable",
            "total_trend": "stable"
        }

        # 按小时统计
        hourly_stats = defaultdict(lambda: defaultdict(int))

        for entry in self.log_entries:
            if start_time <= entry.timestamp <= end_time:
                hour = entry.timestamp.strftime("%Y-%m-%d %H")
                hourly_stats[hour]["total"] += 1
                if entry.level in ["ERROR", "CRITICAL"]:
                    hourly_stats[hour]["errors"] += 1
                if entry.level == "WARNING":
                    hourly_stats[hour]["warnings"] += 1

        if len(hourly_stats) >= 3:
            hours = sorted(hourly_stats.keys())
            mid_point = len(hours) // 2

            first_half = hours[:mid_point]
            second_half = hours[mid_point:]

            first_half_avg = sum(hourly_stats[h]["errors"] for h in first_half) / len(first_half) if first_half else 0
            second_half_avg = sum(hourly_stats[h]["errors"] for h in second_half) / len(second_half) if second_half else 0

            if second_half_avg > first_half_avg * 1.5:
                trends["error_trend"] = "increasing"
            elif second_half_avg < first_half_avg * 0.7:
                trends["error_trend"] = "decreasing"

        return trends

    def _generate_log_recommendations(self, level_counts: Dict[str, int], trends: Dict[str, Any]) -> List[str]:
        """生成日志分析建议"""
        recommendations = []

        total_entries = sum(level_counts.values())
        if total_entries == 0:
            return recommendations

        error_rate = (level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0)) / total_entries

        if error_rate > 0.1:
            recommendations.append("错误率过高，建议检查系统稳定性并修复关键问题")

        if trends.get("error_trend") == "increasing":
            recommendations.append("错误率呈上升趋势，建议加强监控和问题排查")

        if level_counts.get("WARNING", 0) > total_entries * 0.2:
            recommendations.append("警告信息过多，建议优化日志级别配置")

        return recommendations

    def search_logs(self, query: str = "", level: str = "", module: str = "",
                   start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                   limit: int = 100) -> List[LogEntry]:
        """搜索日志"""
        results = []

        for entry in reversed(self.log_entries):  # 从最新的开始搜索
            # 时间范围过滤
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue

            # 级别过滤
            if level and entry.level != level:
                continue

            # 模块过滤
            if module and entry.module != module:
                continue

            # 查询过滤
            if query and query.lower() not in entry.message.lower():
                continue

            results.append(entry)
            if len(results) >= limit:
                break

        return results

    def get_log_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取日志统计信息"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        stats = {
            "total_entries": len([e for e in self.log_entries if e.timestamp >= cutoff_time]),
            "level_distribution": defaultdict(int),
            "module_distribution": defaultdict(int),
            "hourly_stats": dict(self.log_stats),
            "active_patterns": len(self.log_patterns),
            "recent_anomalies": len(self.anomaly_patterns)
        }

        for entry in self.log_entries:
            if entry.timestamp >= cutoff_time:
                stats["level_distribution"][entry.level] += 1
                if entry.module:
                    stats["module_distribution"][entry.module] += 1

        return dict(stats)

    async def health_check(self) -> Dict[str, Any]:
        """健康检查接口"""
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "entries_count": len(self.log_entries),
            "queue_size": self.log_queue.qsize(),
            "patterns_count": len(self.log_patterns),
            "aggregation_active": self._running
        }
