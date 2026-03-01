"""
OpenTelemetry 监控集成 - 阶段2.5
为工作流节点提供 OpenTelemetry 追踪和指标支持
"""
import logging
import time
from typing import Dict, Any, Callable, Awaitable, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# 尝试导入 OpenTelemetry（可选依赖）
OPENTELEMETRY_AVAILABLE = False
tracer = None
meter = None
node_execution_counter = None
node_execution_duration = None
token_usage_counter = None

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry import metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SpanExportResult
    from opentelemetry.sdk.resources import Resource
    
    OPENTELEMETRY_AVAILABLE = True
    
    # 初始化追踪和指标提供者
    resource = Resource.create({"service.name": "langgraph-workflow"})
    
    # 追踪提供者
    trace_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(trace_provider)
    
    # 指标提供者
    meter_provider = MeterProvider(resource=resource)
    metrics.set_meter_provider(meter_provider)
    
    # 获取追踪器和指标器
    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)
    
    # 创建指标
    node_execution_counter = meter.create_counter(
        "node_execution_total",
        description="节点执行总次数"
    )
    node_execution_duration = meter.create_histogram(
        "node_execution_duration_seconds",
        description="节点执行耗时（秒）"
    )
    token_usage_counter = meter.create_counter(
        "token_usage_total",
        description="Token使用总数"
    )
    
    class SafeConsoleSpanExporter(ConsoleSpanExporter):
        def export(self, spans):
            try:
                return super().export(spans)
            except ValueError as e:
                logger.debug(f"OpenTelemetry 控制台导出器写入错误已忽略: {e}")
                return SpanExportResult.SUCCESS
            except Exception as e:
                logger.debug(f"OpenTelemetry 控制台导出器导出异常: {e}")
                return SpanExportResult.FAILURE
    
    logger.info("✅ OpenTelemetry 初始化成功")
    
except ImportError:
    # 🚀 优化：OpenTelemetry 是可选的，使用 INFO 级别而不是 WARNING
    logger.info("ℹ️ OpenTelemetry 未安装（这是可选的），监控功能将不可用。如需使用，请安装: pip install opentelemetry-api opentelemetry-sdk")
    OPENTELEMETRY_AVAILABLE = False


def configure_opentelemetry_exporter(exporter_type: str = "console", endpoint: Optional[str] = None):
    """配置 OpenTelemetry 导出器
    
    Args:
        exporter_type: 导出器类型（"console", "jaeger", "zipkin", "otlp"）
        endpoint: 导出器端点（可选）
    """
    if not OPENTELEMETRY_AVAILABLE:
        logger.warning("⚠️ OpenTelemetry 未安装，无法配置导出器")
        return False
    
    try:
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        
        if exporter_type == "console":
            exporter = SafeConsoleSpanExporter()
            span_processor = BatchSpanProcessor(exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            logger.info("✅ OpenTelemetry 控制台导出器已配置")
            return True
        
        elif exporter_type == "jaeger":
            # Jaeger 导出器
            try:
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter
                endpoint = endpoint or "http://localhost:14268/api/traces"
                exporter = JaegerExporter(
                    agent_host_name="localhost",
                    agent_port=6831,
                    collector_endpoint=endpoint
                )
                span_processor = BatchSpanProcessor(exporter)
                trace.get_tracer_provider().add_span_processor(span_processor)
                logger.info(f"✅ OpenTelemetry Jaeger 导出器已配置: {endpoint}")
                return True
            except ImportError:
                logger.warning("⚠️ Jaeger 导出器未安装。安装: pip install opentelemetry-exporter-jaeger-thrift")
                return False
        
        elif exporter_type == "zipkin":
            # Zipkin 导出器
            try:
                from opentelemetry.exporter.zipkin.json import ZipkinExporter
                endpoint = endpoint or "http://localhost:9411/api/v2/spans"
                exporter = ZipkinExporter(endpoint=endpoint)
                span_processor = BatchSpanProcessor(exporter)
                trace.get_tracer_provider().add_span_processor(span_processor)
                logger.info(f"✅ OpenTelemetry Zipkin 导出器已配置: {endpoint}")
                return True
            except ImportError:
                logger.warning("⚠️ Zipkin 导出器未安装。安装: pip install opentelemetry-exporter-zipkin-json")
                return False
        
        elif exporter_type == "otlp":
            # OTLP 导出器（通用）
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                endpoint = endpoint or "http://localhost:4317"
                exporter = OTLPSpanExporter(endpoint=endpoint)
                span_processor = BatchSpanProcessor(exporter)
                trace.get_tracer_provider().add_span_processor(span_processor)
                logger.info(f"✅ OpenTelemetry OTLP 导出器已配置: {endpoint}")
                return True
            except ImportError:
                logger.warning("⚠️ OTLP 导出器未安装。安装: pip install opentelemetry-exporter-otlp-proto-grpc")
                return False
        
        else:
            logger.warning(f"⚠️ 未知的导出器类型: {exporter_type}")
            return False
    
    except Exception as e:
        logger.error(f"❌ 配置 OpenTelemetry 导出器失败: {e}")
        return False


def traced_node(node_name: str):
    """装饰器：为节点添加 OpenTelemetry 追踪
    
    使用示例：
    @traced_node("my_node")
    async def my_node(state: ResearchSystemState) -> ResearchSystemState:
        # 节点逻辑
        return state
    """
    def decorator(
        node_func: Callable[[Any], Awaitable[Any]]
    ) -> Callable[[Any], Awaitable[Any]]:
        @wraps(node_func)
        async def wrapper(state: Any) -> Any:
            if not OPENTELEMETRY_AVAILABLE or not tracer:
                # 如果 OpenTelemetry 不可用，直接执行节点
                return await node_func(state)
            
            start_time = time.time()
            
            # 创建追踪 span
            with tracer.start_as_current_span(f"node.{node_name}") as span:
                # 记录节点执行信息
                if isinstance(state, dict):
                    span.set_attributes({
                        "node.name": node_name,
                        "query": str(state.get('query', ''))[:100],
                        "complexity_score": float(state.get('complexity_score', 0.0)),
                        "route_path": str(state.get('route_path', 'unknown')),
                        "retry_count": int(state.get('retry_count', 0))
                    })
                
                try:
                    # 执行节点
                    result = await node_func(state)
                    
                    # 记录成功
                    duration = time.time() - start_time
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("duration_seconds", duration)
                    span.set_attribute("success", True)
                    
                    # 记录指标
                    if node_execution_counter:
                        node_execution_counter.add(1, {"node": node_name, "status": "success"})
                    if node_execution_duration:
                        node_execution_duration.record(duration, {"node": node_name})
                    
                    # 记录 token 使用（如果存在）
                    if isinstance(result, dict) and 'token_usage' in result and token_usage_counter:
                        for key, value in result['token_usage'].items():
                            if isinstance(value, (int, float)):
                                token_usage_counter.add(int(value), {"node": node_name, "type": key})
                    
                    return result
                    
                except Exception as e:
                    # 记录失败
                    duration = time.time() - start_time
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    span.set_attribute("duration_seconds", duration)
                    span.set_attribute("success", False)
                    
                    # 记录指标
                    if node_execution_counter:
                        node_execution_counter.add(1, {"node": node_name, "status": "error"})
                    if node_execution_duration:
                        node_execution_duration.record(duration, {"node": node_name})
                    
                    raise
        
        return wrapper
    return decorator


def initialize_opentelemetry(
    exporter_type: str = "console",
    endpoint: Optional[str] = None,
    enabled: bool = True
) -> bool:
    """初始化 OpenTelemetry
    
    Args:
        exporter_type: 导出器类型（"console", "jaeger", "zipkin", "otlp"）
        endpoint: 导出器端点（可选）
        enabled: 是否启用（默认True）
    
    Returns:
        是否成功初始化
    """
    if not enabled:
        logger.info("ℹ️ OpenTelemetry 已禁用")
        return False
    
    if not OPENTELEMETRY_AVAILABLE:
        logger.info("ℹ️ OpenTelemetry 未安装，无法初始化。安装: pip install opentelemetry-api opentelemetry-sdk")
        return False
    
    # 配置导出器
    return configure_opentelemetry_exporter(exporter_type, endpoint)


# 自动初始化（如果环境变量启用）
def _auto_initialize():
    """自动初始化 OpenTelemetry（根据环境变量）"""
    try:
        import os
        enabled = os.getenv('ENABLE_OPENTELEMETRY', 'false').lower() == 'true'
        if enabled:
            exporter_type = os.getenv('OPENTELEMETRY_EXPORTER', 'console')
            endpoint = os.getenv('OPENTELEMETRY_ENDPOINT')
            initialize_opentelemetry(exporter_type, endpoint, enabled=True)
    except Exception as e:
        logger.debug(f"自动初始化 OpenTelemetry 失败: {e}")


# 模块加载时自动初始化
_auto_initialize()
