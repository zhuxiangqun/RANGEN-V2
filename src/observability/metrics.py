"""
性能监控和指标收集系统
使用OpenTelemetry Metrics收集系统性能指标和业务指标
"""

import os
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass

from src.services.logging_service import get_logger

logger = get_logger("metrics")


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"           # 计数器（只增不减）
    UP_DOWN_COUNTER = "up_down_counter"  # 上下计数器（可增可减）
    HISTOGRAM = "histogram"       # 直方图（用于测量值的分布）
    GAUGE = "gauge"               # 仪表（瞬时值）
    OBSERVABLE_COUNTER = "observable_counter"  # 可观察计数器
    OBSERVABLE_GAUGE = "observable_gauge"      # 可观察仪表
    OBSERVABLE_UP_DOWN_COUNTER = "observable_up_down_counter"  # 可观察上下计数器


class MetricUnit(Enum):
    """指标单位"""
    NONE = "1"                    # 无单位
    SECONDS = "s"                 # 秒
    MILLISECONDS = "ms"           # 毫秒
    BYTES = "By"                  # 字节
    KILOBYTES = "KB"              # 千字节
    MEGABYTES = "MB"              # 兆字节
    REQUESTS = "req"              # 请求
    ERRORS = "err"                # 错误
    PERCENT = "%"                 # 百分比


@dataclass
class MetricDefinition:
    """指标定义"""
    name: str
    description: str
    unit: MetricUnit
    type: MetricType
    labels: List[str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics = {}
        self._init_metrics()
        self._setup_periodic_collection()
    
    def _init_metrics(self):
        """初始化指标定义"""
        self.metrics_definitions = {
            # HTTP请求指标
            "http_requests_total": MetricDefinition(
                name="http_requests_total",
                description="HTTP请求总数",
                unit=MetricUnit.REQUESTS,
                type=MetricType.COUNTER,
                labels=["method", "path", "status_code"]
            ),
            "http_request_duration_seconds": MetricDefinition(
                name="http_request_duration_seconds",
                description="HTTP请求处理时间（秒）",
                unit=MetricUnit.SECONDS,
                type=MetricType.HISTOGRAM,
                labels=["method", "path"]
            ),
            "http_request_errors_total": MetricDefinition(
                name="http_request_errors_total",
                description="HTTP请求错误总数",
                unit=MetricUnit.ERRORS,
                type=MetricType.COUNTER,
                labels=["method", "path", "error_type"]
            ),
            
            # 系统资源指标
            "system_cpu_usage_percent": MetricDefinition(
                name="system_cpu_usage_percent",
                description="系统CPU使用率",
                unit=MetricUnit.PERCENT,
                type=MetricType.GAUGE
            ),
            "system_memory_usage_bytes": MetricDefinition(
                name="system_memory_usage_bytes",
                description="系统内存使用量（字节）",
                unit=MetricUnit.BYTES,
                type=MetricType.GAUGE
            ),
            "system_disk_usage_percent": MetricDefinition(
                name="system_disk_usage_percent",
                description="系统磁盘使用率",
                unit=MetricUnit.PERCENT,
                type=MetricType.GAUGE
            ),
            
            # 业务指标
            "active_users": MetricDefinition(
                name="active_users",
                description="活跃用户数",
                unit=MetricUnit.NONE,
                type=MetricType.GAUGE
            ),
            "api_calls_total": MetricDefinition(
                name="api_calls_total",
                description="API调用总数",
                unit=MetricUnit.REQUESTS,
                type=MetricType.COUNTER,
                labels=["endpoint", "method"]
            ),
            "api_errors_total": MetricDefinition(
                name="api_errors_total",
                description="API错误总数",
                unit=MetricUnit.ERRORS,
                type=MetricType.COUNTER,
                labels=["endpoint", "method", "error_type"]
            ),
            
            # 数据库指标
            "database_queries_total": MetricDefinition(
                name="database_queries_total",
                description="数据库查询总数",
                unit=MetricUnit.REQUESTS,
                type=MetricType.COUNTER,
                labels=["operation", "table"]
            ),
            "database_query_duration_seconds": MetricDefinition(
                name="database_query_duration_seconds",
                description="数据库查询时间（秒）",
                unit=MetricUnit.SECONDS,
                type=MetricType.HISTOGRAM,
                labels=["operation", "table"]
            ),
            "database_connections_active": MetricDefinition(
                name="database_connections_active",
                description="活跃数据库连接数",
                unit=MetricUnit.NONE,
                type=MetricType.GAUGE
            ),
            
            # 缓存指标
            "cache_hits_total": MetricDefinition(
                name="cache_hits_total",
                description="缓存命中总数",
                unit=MetricUnit.NONE,
                type=MetricType.COUNTER,
                labels=["cache_name"]
            ),
            "cache_misses_total": MetricDefinition(
                name="cache_misses_total",
                description="缓存未命中总数",
                unit=MetricUnit.NONE,
                type=MetricType.COUNTER,
                labels=["cache_name"]
            ),
            "cache_operations_total": MetricDefinition(
                name="cache_operations_total",
                description="缓存操作总数",
                unit=MetricUnit.NONE,
                type=MetricType.COUNTER,
                labels=["cache_name", "operation"]
            ),
            
            # 队列指标
            "queue_size": MetricDefinition(
                name="queue_size",
                description="队列大小",
                unit=MetricUnit.NONE,
                type=MetricType.GAUGE,
                labels=["queue_name"]
            ),
            "queue_processing_duration_seconds": MetricDefinition(
                name="queue_processing_duration_seconds",
                description="队列处理时间（秒）",
                unit=MetricUnit.SECONDS,
                type=MetricType.HISTOGRAM,
                labels=["queue_name"]
            ),
        }
    
    def _setup_periodic_collection(self):
        """设置定期收集任务"""
        self.collection_thread = None
        self.collection_interval = 60  # 60秒
        
        # 启动收集线程
        self.start_collection()
    
    def start_collection(self):
        """启动指标收集"""
        if self.collection_thread and self.collection_thread.is_alive():
            logger.info("指标收集已在进行中")
            return
        
        self.stop_collection_flag = False
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        logger.info(f"指标收集已启动，间隔: {self.collection_interval}秒")
    
    def stop_collection(self):
        """停止指标收集"""
        self.stop_collection_flag = True
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
            logger.info("指标收集已停止")
    
    def _collection_loop(self):
        """收集循环"""
        while not self.stop_collection_flag:
            try:
                self.collect_system_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"指标收集失败: {e}")
                time.sleep(5)  # 错误后短暂等待
    
    def collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.record_gauge("system_cpu_usage_percent", cpu_percent)
            
            # 内存使用量
            memory = psutil.virtual_memory()
            self.record_gauge("system_memory_usage_bytes", memory.used)
            
            # 磁盘使用率
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            self.record_gauge("system_disk_usage_percent", disk_percent)
            
            logger.debug(f"系统指标已收集 - CPU: {cpu_percent}%, 内存: {memory.used}/{memory.total}, 磁盘: {disk_percent}%")
            
        except ImportError:
            logger.warning("psutil未安装，跳过系统指标收集")
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
    
    def record_counter(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        """记录计数器指标"""
        try:
            metric_def = self.metrics_definitions.get(name)
            if not metric_def:
                logger.warning(f"未定义的指标: {name}")
                return
            
            # 这里简化实现，实际应该使用OpenTelemetry Metrics
            key = self._get_metric_key(name, labels)
            if key not in self.metrics:
                self.metrics[key] = 0
            
            self.metrics[key] += value
            logger.debug(f"计数器指标记录: {name}={value}, 标签: {labels}")
            
        except Exception as e:
            logger.error(f"记录计数器指标失败: {e}")
    
    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """记录仪表指标"""
        try:
            metric_def = self.metrics_definitions.get(name)
            if not metric_def:
                logger.warning(f"未定义的指标: {name}")
                return
            
            # 这里简化实现
            key = self._get_metric_key(name, labels)
            self.metrics[key] = value
            logger.debug(f"仪表指标记录: {name}={value}, 标签: {labels}")
            
        except Exception as e:
            logger.error(f"记录仪表指标失败: {e}")
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """记录直方图指标"""
        try:
            metric_def = self.metrics_definitions.get(name)
            if not metric_def:
                logger.warning(f"未定义的指标: {name}")
                return
            
            # 这里简化实现，实际应该记录值的分布
            key = self._get_metric_key(name, labels)
            if key not in self.metrics:
                self.metrics[key] = []
            
            self.metrics[key].append(value)
            logger.debug(f"直方图指标记录: {name}={value}, 标签: {labels}")
            
        except Exception as e:
            logger.error(f"记录直方图指标失败: {e}")
    
    def _get_metric_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """获取指标键"""
        if not labels:
            return name
        
        # 将标签排序以确保一致性
        sorted_labels = sorted(labels.items())
        label_str = "_".join(f"{k}:{v}" for k, v in sorted_labels)
        return f"{name}_{label_str}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        return self.metrics.copy()
    
    def get_metric_value(self, name: str, labels: Dict[str, str] = None) -> Optional[float]:
        """获取指标值"""
        key = self._get_metric_key(name, labels)
        return self.metrics.get(key)
    
    def reset_metrics(self):
        """重置指标"""
        self.metrics.clear()
        logger.info("所有指标已重置")


class OpenTelemetryMetrics:
    """OpenTelemetry指标收集器"""
    
    def __init__(self):
        self.enabled = False
        self.meter = None
        self.metrics = {}
        
        self._init_opentelemetry()
    
    def _init_opentelemetry(self):
        """初始化OpenTelemetry"""
        # 检查是否启用OpenTelemetry指标
        self.enabled = os.getenv("ENABLE_OPENTELEMETRY_METRICS", "false").lower() == "true"
        
        if not self.enabled:
            logger.info("OpenTelemetry指标已禁用")
            return
        
        try:
            from opentelemetry import metrics
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            from opentelemetry.exporter.prometheus import PrometheusMetricExporter
            
            OPENTELEMETRY_AVAILABLE = True
        except ImportError as e:
            logger.warning(f"OpenTelemetry指标包未安装: {e}")
            self.enabled = False
            return
        
        try:
            # 创建MeterProvider
            meter_provider = MeterProvider()
            metrics.set_meter_provider(meter_provider)
            
            # 获取Meter
            self.meter = metrics.get_meter("rangen-v2-metrics")
            
            # 配置导出器
            exporter_type = os.getenv("OTEL_METRICS_EXPORTER", "prometheus").lower()
            
            if exporter_type == "otlp":
                endpoint = os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", "http://localhost:4317")
                exporter = OTLPMetricExporter(endpoint=endpoint)
                reader = PeriodicExportingMetricReader(exporter)
                meter_provider.add_metric_reader(reader)
                logger.info(f"配置OTLP指标导出器到: {endpoint}")
            
            elif exporter_type == "prometheus":
                # Prometheus导出器
                from prometheus_client import start_http_server
                
                prometheus_port = int(os.getenv("PROMETHEUS_PORT", "9090"))
                start_http_server(prometheus_port)
                
                exporter = PrometheusMetricExporter()
                reader = PeriodicExportingMetricReader(exporter)
                meter_provider.add_metric_reader(reader)
                
                logger.info(f"配置Prometheus指标导出器，端口: {prometheus_port}")
            
            else:
                logger.warning(f"未知的指标导出器类型: {exporter_type}")
                self.enabled = False
                return
            
            logger.info("OpenTelemetry指标配置完成")
            
        except Exception as e:
            logger.error(f"配置OpenTelemetry指标失败: {e}")
            self.enabled = False
    
    def create_counter(self, name: str, description: str, unit: str = "1"):
        """创建计数器"""
        if not self.enabled or not self.meter:
            return None
        
        try:
            counter = self.meter.create_counter(
                name=name,
                description=description,
                unit=unit
            )
            return counter
        except Exception as e:
            logger.error(f"创建计数器失败: {e}")
            return None
    
    def create_histogram(self, name: str, description: str, unit: str = "1"):
        """创建直方图"""
        if not self.enabled or not self.meter:
            return None
        
        try:
            histogram = self.meter.create_histogram(
                name=name,
                description=description,
                unit=unit
            )
            return histogram
        except Exception as e:
            logger.error(f"创建直方图失败: {e}")
            return None
    
    def create_gauge(self, name: str, description: str, unit: str = "1"):
        """创建仪表"""
        if not self.enabled or not self.meter:
            return None
        
        try:
            gauge = self.meter.create_gauge(
                name=name,
                description=description,
                unit=unit
            )
            return gauge
        except Exception as e:
            logger.error(f"创建仪表失败: {e}")
            return None
    
    def record_http_request(self, method: str, path: str, status_code: int, duration: float):
        """记录HTTP请求指标"""
        if not self.enabled:
            return
        
        # 记录请求总数
        counter = self.create_counter(
            name="http_requests_total",
            description="HTTP请求总数",
            unit="req"
        )
        if counter:
            counter.add(1, {"method": method, "path": path, "status_code": str(status_code)})
        
        # 记录请求持续时间
        histogram = self.create_histogram(
            name="http_request_duration_seconds",
            description="HTTP请求处理时间（秒）",
            unit="s"
        )
        if histogram:
            histogram.record(duration, {"method": method, "path": path})
        
        # 如果是错误响应（4xx或5xx），记录错误
        if status_code >= 400:
            error_counter = self.create_counter(
                name="http_request_errors_total",
                description="HTTP请求错误总数",
                unit="err"
            )
            if error_counter:
                error_type = "client_error" if 400 <= status_code < 500 else "server_error"
                error_counter.add(1, {"method": method, "path": path, "error_type": error_type})
    
    def record_api_call(self, endpoint: str, method: str, success: bool = True):
        """记录API调用指标"""
        if not self.enabled:
            return
        
        counter = self.create_counter(
            name="api_calls_total",
            description="API调用总数",
            unit="req"
        )
        if counter:
            counter.add(1, {"endpoint": endpoint, "method": method})
        
        if not success:
            error_counter = self.create_counter(
                name="api_errors_total",
                description="API错误总数",
                unit="err"
            )
            if error_counter:
                error_counter.add(1, {"endpoint": endpoint, "method": method, "error_type": "api_error"})


class MetricsMiddleware:
    """指标收集中间件"""
    
    def __init__(self, metrics_collector: MetricsCollector = None, otel_metrics: OpenTelemetryMetrics = None):
        self.metrics_collector = metrics_collector or get_metrics_collector()
        self.otel_metrics = otel_metrics or get_opentelemetry_metrics()
    
    async def __call__(self, request, call_next):
        import time
        
        start_time = time.time()
        method = request.method
        path = request.url.path
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # 记录指标
            self._record_request_metrics(method, path, response.status_code, process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            error_type = type(e).__name__
            
            # 记录错误指标
            self._record_error_metrics(method, path, error_type, process_time)
            
            raise
    
    def _record_request_metrics(self, method: str, path: str, status_code: int, duration: float):
        """记录请求指标"""
        # 使用OpenTelemetry指标（如果可用）
        if self.otel_metrics and self.otel_metrics.enabled:
            self.otel_metrics.record_http_request(method, path, status_code, duration)
        
        # 使用简单指标收集器
        labels = {"method": method, "path": path, "status_code": str(status_code)}
        self.metrics_collector.record_counter("http_requests_total", 1, labels)
        self.metrics_collector.record_histogram("http_request_duration_seconds", duration, {"method": method, "path": path})
    
    def _record_error_metrics(self, method: str, path: str, error_type: str, duration: float):
        """记录错误指标"""
        labels = {"method": method, "path": path, "error_type": error_type}
        self.metrics_collector.record_counter("http_request_errors_total", 1, labels)
        self.metrics_collector.record_histogram("http_request_duration_seconds", duration, {"method": method, "path": path})


# 全局实例
_metrics_collector = None
_otel_metrics = None

def get_metrics_collector() -> MetricsCollector:
    """获取指标收集器实例"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

def get_opentelemetry_metrics() -> OpenTelemetryMetrics:
    """获取OpenTelemetry指标实例"""
    global _otel_metrics
    if _otel_metrics is None:
        _otel_metrics = OpenTelemetryMetrics()
    return _otel_metrics

def get_metrics_middleware():
    """获取指标中间件"""
    metrics_collector = get_metrics_collector()
    otel_metrics = get_opentelemetry_metrics()
    return MetricsMiddleware(metrics_collector, otel_metrics)

# 便捷函数
def record_api_call(endpoint: str, method: str, success: bool = True):
    """记录API调用便捷函数"""
    otel_metrics = get_opentelemetry_metrics()
    if otel_metrics and otel_metrics.enabled:
        otel_metrics.record_api_call(endpoint, method, success)
    
    metrics_collector = get_metrics_collector()
    labels = {"endpoint": endpoint, "method": method}
    metrics_collector.record_counter("api_calls_total", 1, labels)
    
    if not success:
        error_labels = {"endpoint": endpoint, "method": method, "error_type": "api_error"}
        metrics_collector.record_counter("api_errors_total", 1, error_labels)

def record_database_query(operation: str, table: str, duration: float):
    """记录数据库查询便捷函数"""
    metrics_collector = get_metrics_collector()
    labels = {"operation": operation, "table": table}
    metrics_collector.record_counter("database_queries_total", 1, labels)
    metrics_collector.record_histogram("database_query_duration_seconds", duration, labels)

def record_cache_operation(cache_name: str, operation: str, hit: bool = True):
    """记录缓存操作便捷函数"""
    metrics_collector = get_metrics_collector()
    
    # 记录操作总数
    op_labels = {"cache_name": cache_name, "operation": operation}
    metrics_collector.record_counter("cache_operations_total", 1, op_labels)
    
    # 记录命中/未命中
    if hit:
        hit_labels = {"cache_name": cache_name}
        metrics_collector.record_counter("cache_hits_total", 1, hit_labels)
    else:
        miss_labels = {"cache_name": cache_name}
        metrics_collector.record_counter("cache_misses_total", 1, miss_labels)

# 初始化指标系统
logger.info("性能监控和指标收集系统已初始化")