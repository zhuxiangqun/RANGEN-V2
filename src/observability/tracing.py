"""
OpenTelemetry分布式追踪配置
为RANGEN V2系统提供端到端的请求追踪
"""

import os
import logging
from typing import Dict, Any, Optional

from src.services.logging_service import get_logger

logger = get_logger("opentelemetry_tracing")

# 尝试导入OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource
    
    # 导出器
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.zipkin.json import ZipkinExporter
    
    # 检测器
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    
    OPENTELEMETRY_AVAILABLE = True
except ImportError as e:
    OPENTELEMETRY_AVAILABLE = False
    logger.warning(f"OpenTelemetry不可用: {e}")
    logger.warning("分布式追踪将使用模拟模式运行")


class OpenTelemetryConfig:
    """OpenTelemetry配置类"""
    
    def __init__(self):
        self.enabled = False
        self.tracer_provider = None
        self.exporters = []
        self.resource = None
        
        self._init_config()
    
    def _init_config(self):
        """初始化配置"""
        # 检查是否启用OpenTelemetry
        self.enabled = os.getenv("ENABLE_OPENTELEMETRY", "false").lower() == "true"
        
        if not self.enabled:
            logger.info("OpenTelemetry追踪已禁用")
            return
        
        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry包未安装，追踪已禁用")
            self.enabled = False
            return
        
        # 配置资源
        service_name = os.getenv("OTEL_SERVICE_NAME", "rangen-v2")
        service_version = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
        environment = os.getenv("OTEL_ENVIRONMENT", "development")
        
        self.resource = Resource.create(
            attributes={
                "service.name": service_name,
                "service.version": service_version,
                "deployment.environment": environment,
                "telemetry.sdk.name": "opentelemetry",
                "telemetry.sdk.language": "python",
                "telemetry.sdk.version": "1.0.0",
            }
        )
        
        logger.info(f"OpenTelemetry追踪已启用 - 服务: {service_name}, 环境: {environment}")
    
    def configure_tracing(self, app=None):
        """配置追踪系统"""
        if not self.enabled or not OPENTELEMETRY_AVAILABLE:
            logger.info("跳过OpenTelemetry配置（已禁用或不可用）")
            return
        
        try:
            # 创建TracerProvider
            self.tracer_provider = TracerProvider(resource=self.resource)
            trace.set_tracer_provider(self.tracer_provider)
            
            # 配置导出器
            self._configure_exporters()
            
            # 配置检测器
            self._configure_instrumentation(app)
            
            logger.info("OpenTelemetry追踪配置完成")
            
        except Exception as e:
            logger.error(f"配置OpenTelemetry追踪失败: {e}")
            self.enabled = False
    
    def _configure_exporters(self):
        """配置追踪导出器"""
        if not self.enabled or not OPENTELEMETRY_AVAILABLE:
            return
        
        exporter_type = os.getenv("OTEL_TRACES_EXPORTER", "console").lower()
        
        try:
            if exporter_type == "otlp":
                # OTLP gRPC导出器（用于Jaeger、Tempo等）
                endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
                exporter = OTLPSpanExporter(endpoint=endpoint)
                self.exporters.append(exporter)
                logger.info(f"配置OTLP导出器到: {endpoint}")
                
            elif exporter_type == "jaeger":
                # Jaeger导出器
                endpoint = os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
                exporter = JaegerExporter(
                    agent_host_name=os.getenv("JAEGER_AGENT_HOST", "localhost"),
                    agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
                    collector_endpoint=endpoint,
                )
                self.exporters.append(exporter)
                logger.info(f"配置Jaeger导出器到: {endpoint}")
                
            elif exporter_type == "zipkin":
                # Zipkin导出器
                endpoint = os.getenv("ZIPKIN_ENDPOINT", "http://localhost:9411/api/v2/spans")
                exporter = ZipkinExporter(endpoint=endpoint)
                self.exporters.append(exporter)
                logger.info(f"配置Zipkin导出器到: {endpoint}")
                
            elif exporter_type == "console" or not exporter_type:
                # 控制台导出器（开发环境）
                exporter = ConsoleSpanExporter()
                self.exporters.append(exporter)
                logger.info("配置控制台导出器")
                
            else:
                logger.warning(f"未知的导出器类型: {exporter_type}，使用控制台导出器")
                exporter = ConsoleSpanExporter()
                self.exporters.append(exporter)
            
            # 为每个导出器添加批处理处理器
            for exporter in self.exporters:
                span_processor = BatchSpanProcessor(exporter)
                self.tracer_provider.add_span_processor(span_processor)
                
        except Exception as e:
            logger.error(f"配置导出器失败: {e}")
            # 回退到控制台导出器
            try:
                exporter = ConsoleSpanExporter()
                span_processor = BatchSpanProcessor(exporter)
                self.tracer_provider.add_span_processor(span_processor)
                logger.info("已回退到控制台导出器")
            except Exception as e2:
                logger.error(f"回退到控制台导出器也失败: {e2}")
                self.enabled = False
    
    def _configure_instrumentation(self, app=None):
        """配置检测器"""
        if not self.enabled or not OPENTELEMETRY_AVAILABLE:
            return
        
        try:
            # 配置日志检测（将追踪上下文注入日志）
            LoggingInstrumentor().instrument()
            logger.info("日志检测器已配置")
            
            # 配置请求检测（HTTP客户端）
            RequestsInstrumentor().instrument()
            logger.info("HTTP请求检测器已配置")
            
            # 配置SQLAlchemy检测（数据库操作）
            try:
                SQLAlchemyInstrumentor().instrument()
                logger.info("SQLAlchemy检测器已配置")
            except Exception as e:
                logger.warning(f"SQLAlchemy检测器配置失败: {e}")
            
            # 配置FastAPI检测（如果提供了app）
            if app:
                FastAPIInstrumentor.instrument_app(app)
                logger.info("FastAPI检测器已配置")
                
        except Exception as e:
            logger.error(f"配置检测器失败: {e}")
    
    def get_tracer(self, name: str = None):
        """获取追踪器"""
        if not self.enabled or not OPENTELEMETRY_AVAILABLE:
            # 返回模拟追踪器
            return MockTracer()
        
        if name is None:
            name = "rangen-v2"
        
        return trace.get_tracer(name)
    
    def shutdown(self):
        """关闭追踪系统"""
        if not self.enabled or not OPENTELEMETRY_AVAILABLE:
            return
        
        try:
            if self.tracer_provider:
                self.tracer_provider.shutdown()
                logger.info("OpenTelemetry追踪已关闭")
        except Exception as e:
            logger.error(f"关闭OpenTelemetry追踪失败: {e}")


class MockSpan:
    """模拟Span（当OpenTelemetry不可用时使用）"""
    
    def __init__(self, name: str):
        self.name = name
        self.attributes = {}
        self.status = None
        self.events = []
    
    def set_attribute(self, key: str, value: Any):
        """设置属性"""
        self.attributes[key] = value
        return self
    
    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        """添加事件"""
        event = {"name": name, "attributes": attributes or {}}
        self.events.append(event)
        return self
    
    def set_status(self, status):
        """设置状态"""
        self.status = status
        return self
    
    def end(self):
        """结束Span"""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()


class MockTracer:
    """模拟追踪器（当OpenTelemetry不可用时使用）"""
    
    def start_span(self, name: str, context=None, kind=None, attributes=None):
        """开始Span"""
        span = MockSpan(name)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        return span
    
    def start_as_current_span(self, name: str, context=None, kind=None, attributes=None):
        """开始当前Span"""
        return MockSpan(name)


# 全局配置实例
_otel_config = None

def get_opentelemetry_config() -> OpenTelemetryConfig:
    """获取OpenTelemetry配置实例"""
    global _otel_config
    if _otel_config is None:
        _otel_config = OpenTelemetryConfig()
    return _otel_config


def configure_tracing(app=None):
    """配置追踪系统"""
    config = get_opentelemetry_config()
    config.configure_tracing(app)
    return config


def get_tracer(name: str = None):
    """获取追踪器"""
    config = get_opentelemetry_config()
    return config.get_tracer(name)


def create_trace_middleware():
    """创建追踪中间件工厂函数"""
    config = get_opentelemetry_config()
    
    if not config.enabled or not OPENTELEMETRY_AVAILABLE:
        # 返回空中间件
        async def dummy_middleware(request, call_next):
            return await call_next(request)
        return dummy_middleware
    
    try:
        from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
        
        async def otel_middleware(request, call_next):
            """OpenTelemetry中间件"""
            tracer = get_tracer("fastapi-middleware")
            
            # 提取请求信息
            span_name = f"{request.method} {request.url.path}"
            
            with tracer.start_as_current_span(span_name) as span:
                # 添加请求属性
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.url", str(request.url))
                span.set_attribute("http.route", request.url.path)
                span.set_attribute("http.host", request.url.hostname or "")
                span.set_attribute("http.scheme", request.url.scheme)
                
                # 添加客户端信息
                if request.client:
                    span.set_attribute("client.ip", request.client.host)
                    span.set_attribute("client.port", request.client.port)
                
                # 添加用户代理
                user_agent = request.headers.get("user-agent")
                if user_agent:
                    span.set_attribute("http.user_agent", user_agent)
                
                # 添加请求ID（如果存在）
                request_id = request.headers.get("x-request-id")
                if request_id:
                    span.set_attribute("request.id", request_id)
                
                # 处理请求
                response = await call_next(request)
                
                # 添加响应属性
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.status_text", str(response.status_code))
                
                # 根据状态码设置Span状态
                if response.status_code >= 400:
                    span.set_status(trace.StatusCode.ERROR)
                else:
                    span.set_status(trace.StatusCode.OK)
                
                return response
        
        return otel_middleware
        
    except ImportError as e:
        logger.error(f"创建OpenTelemetry中间件失败: {e}")
        
        # 返回空中间件
        async def dummy_middleware(request, call_next):
            return await call_next(request)
        return dummy_middleware


def trace_function(name: str = None, attributes: Dict[str, Any] = None):
    """函数追踪装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or func.__name__
            
            with tracer.start_as_current_span(span_name, attributes=attributes) as span:
                # 添加函数信息
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.StatusCode.OK)
                    return result
                except Exception as e:
                    span.set_status(trace.StatusCode.ERROR)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise
        
        return wrapper
    return decorator


class TraceContext:
    """追踪上下文管理器"""
    
    @staticmethod
    def get_current_context():
        """获取当前追踪上下文"""
        if not OPENTELEMETRY_AVAILABLE:
            return {}
        
        try:
            from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
            
            ctx = trace.get_current_span().get_span_context()
            carrier = {}
            TraceContextTextMapPropagator().inject(carrier)
            
            return {
                "trace_id": format(ctx.trace_id, '032x'),
                "span_id": format(ctx.span_id, '016x'),
                "trace_flags": ctx.trace_flags,
                "is_remote": ctx.is_remote,
                "carrier": carrier
            }
        except Exception as e:
            logger.error(f"获取追踪上下文失败: {e}")
            return {}
    
    @staticmethod
    def extract_from_headers(headers: Dict[str, str]):
        """从HTTP头提取追踪上下文"""
        if not OPENTELEMETRY_AVAILABLE:
            return None
        
        try:
            from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
            
            propagator = TraceContextTextMapPropagator()
            context = propagator.extract(headers)
            return context
        except Exception as e:
            logger.error(f"从HTTP头提取追踪上下文失败: {e}")
            return None


# 初始化追踪系统（在导入时自动配置）
config = get_opentelemetry_config()
logger.info(f"OpenTelemetry追踪系统初始化完成，启用状态: {config.enabled}")