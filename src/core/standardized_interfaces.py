"""
标准化接口规范 (Standardized Interfaces)

定义统一的接口规范：
- 能力接口标准
- 数据格式标准
- 通信协议标准
- 配置规范标准
- 错误处理标准
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Protocol, Union, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)

T = TypeVar('T')


class InterfaceVersion(Enum):
    """接口版本"""
    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"


class DataFormat(Enum):
    """数据格式"""
    JSON = "json"
    PROTOBUF = "protobuf"
    MSGPACK = "msgpack"
    YAML = "yaml"


class CommunicationProtocol(Enum):
    """通信协议"""
    HTTP = "http"
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    MQTT = "mqtt"


@dataclass
class InterfaceMetadata:
    """接口元数据"""
    interface_id: str
    name: str
    version: InterfaceVersion
    description: str
    supported_data_formats: List[DataFormat]
    communication_protocols: List[CommunicationProtocol]
    authentication_required: bool = False
    rate_limiting_enabled: bool = False
    deprecated: bool = False
    deprecated_at: Optional[datetime] = None
    replacement_interface: Optional[str] = None


@dataclass
class RequestContext:
    """请求上下文"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    destination: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None
    priority: int = 1  # 1-10, 10最高


@dataclass
class ResponseContext:
    """响应上下文"""
    request_id: str
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time: Optional[float] = None
    status_code: int = 200
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StandardizedRequest(Protocol):
    """标准化请求接口"""

    @property
    def context(self) -> RequestContext:
        """获取请求上下文"""
        ...

    @property
    def payload(self) -> Dict[str, Any]:
        """获取请求负载"""
        ...

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardizedRequest':
        """从字典创建请求"""
        ...


class StandardizedResponse(Protocol):
    """标准化响应接口"""

    @property
    def context(self) -> ResponseContext:
        """获取响应上下文"""
        ...

    @property
    def payload(self) -> Dict[str, Any]:
        """获取响应负载"""
        ...

    @property
    def success(self) -> bool:
        """是否成功"""
        ...

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardizedResponse':
        """从字典创建响应"""
        ...


@dataclass
class StandardRequest(StandardizedRequest):
    """标准请求实现"""
    _context: RequestContext
    _payload: Dict[str, Any]

    def __init__(self, payload: Dict[str, Any], context: Optional[RequestContext] = None):
        self._context = context or RequestContext()
        self._payload = payload

    @property
    def context(self) -> RequestContext:
        return self._context

    @property
    def payload(self) -> Dict[str, Any]:
        return self._payload

    def to_dict(self) -> Dict[str, Any]:
        return {
            'context': {
                'request_id': self._context.request_id,
                'user_id': self._context.user_id,
                'session_id': self._context.session_id,
                'correlation_id': self._context.correlation_id,
                'timestamp': self._context.timestamp.isoformat(),
                'source': self._context.source,
                'destination': self._context.destination,
                'metadata': self._context.metadata,
                'timeout': self._context.timeout,
                'priority': self._context.priority
            },
            'payload': self._payload
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardRequest':
        context_data = data.get('context', {})
        context = RequestContext(
            request_id=context_data.get('request_id', str(uuid.uuid4())),
            user_id=context_data.get('user_id'),
            session_id=context_data.get('session_id'),
            correlation_id=context_data.get('correlation_id'),
            timestamp=datetime.fromisoformat(context_data['timestamp']) if 'timestamp' in context_data else datetime.now(),
            source=context_data.get('source'),
            destination=context_data.get('destination'),
            metadata=context_data.get('metadata', {}),
            timeout=context_data.get('timeout'),
            priority=context_data.get('priority', 1)
        )
        return cls(data.get('payload', {}), context)


@dataclass
class StandardResponse(StandardizedResponse):
    """标准响应实现"""
    _context: ResponseContext
    _payload: Dict[str, Any]
    _success: bool

    def __init__(self, payload: Dict[str, Any], success: bool = True,
                 context: Optional[ResponseContext] = None, error_code: Optional[str] = None,
                 error_message: Optional[str] = None):
        self._context = context or ResponseContext(request_id=str(uuid.uuid4()))
        self._payload = payload
        self._success = success

        if not success:
            self._context.error_code = error_code
            self._context.error_message = error_message
            self._context.status_code = 500  # 默认错误状态码

    @property
    def context(self) -> ResponseContext:
        return self._context

    @property
    def payload(self) -> Dict[str, Any]:
        return self._payload

    @property
    def success(self) -> bool:
        return self._success

    def to_dict(self) -> Dict[str, Any]:
        return {
            'context': {
                'request_id': self._context.request_id,
                'response_id': self._context.response_id,
                'timestamp': self._context.timestamp.isoformat(),
                'processing_time': self._context.processing_time,
                'status_code': self._context.status_code,
                'error_code': self._context.error_code,
                'error_message': self._context.error_message,
                'metadata': self._context.metadata
            },
            'payload': self._payload,
            'success': self._success
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardResponse':
        context_data = data.get('context', {})
        context = ResponseContext(
            request_id=context_data.get('request_id', str(uuid.uuid4())),
            response_id=context_data.get('response_id', str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(context_data['timestamp']) if 'timestamp' in context_data else datetime.now(),
            processing_time=context_data.get('processing_time'),
            status_code=context_data.get('status_code', 200),
            error_code=context_data.get('error_code'),
            error_message=context_data.get('error_message'),
            metadata=context_data.get('metadata', {})
        )
        return cls(
            data.get('payload', {}),
            data.get('success', True),
            context,
            context_data.get('error_code'),
            context_data.get('error_message')
        )


class StandardizedCapabilityInterface(Protocol):
    """标准化能力接口"""

    @property
    def interface_metadata(self) -> InterfaceMetadata:
        """获取接口元数据"""
        ...

    async def process_request(self, request: StandardizedRequest) -> StandardizedResponse:
        """处理标准化请求"""
        ...

    async def validate_request(self, request: StandardizedRequest) -> List[str]:
        """验证请求"""
        ...

    async def get_interface_status(self) -> Dict[str, Any]:
        """获取接口状态"""
        ...


@dataclass
class CapabilityExecutionContext:
    """能力执行上下文"""
    capability_id: str
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=datetime.now)
    parameters: Dict[str, Any] = field(default_factory=dict)
    input_data: Dict[str, Any] = field(default_factory=dict)
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None
    priority: int = 1


@dataclass
class CapabilityExecutionResult:
    """能力执行结果"""
    execution_id: str
    capability_id: str
    success: bool
    output_data: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigurationSchema:
    """配置模式"""

    def __init__(self, schema_definition: Dict[str, Any]):
        self.schema = schema_definition
        self.version = schema_definition.get('version', '1.0')
        self.parameters: Dict[str, Dict[str, Any]] = schema_definition.get('parameters', {})

    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """验证配置"""
        errors = []

        for param_name, param_schema in self.parameters.items():
            if param_name not in config:
                if param_schema.get('required', False):
                    errors.append(f"缺少必需参数: {param_name}")
                continue

            param_value = config[param_name]
            param_type = param_schema.get('type')

            # 类型检查
            if param_type == 'int' and not isinstance(param_value, int):
                errors.append(f"参数 {param_name} 应为整数类型")
            elif param_type == 'float' and not isinstance(param_value, (int, float)):
                errors.append(f"参数 {param_name} 应为数值类型")
            elif param_type == 'bool' and not isinstance(param_value, bool):
                errors.append(f"参数 {param_name} 应为布尔类型")
            elif param_type == 'string' and not isinstance(param_value, str):
                errors.append(f"参数 {param_name} 应为字符串类型")
            elif param_type == 'list' and not isinstance(param_value, list):
                errors.append(f"参数 {param_name} 应为列表类型")
            elif param_type == 'dict' and not isinstance(param_value, dict):
                errors.append(f"参数 {param_name} 应为字典类型")

            # 范围检查
            if 'min_value' in param_schema and param_value < param_schema['min_value']:
                errors.append(f"参数 {param_name} 不能小于 {param_schema['min_value']}")
            if 'max_value' in param_schema and param_value > param_schema['max_value']:
                errors.append(f"参数 {param_name} 不能大于 {param_schema['max_value']}")

            # 枚举值检查
            if 'enum_values' in param_schema and param_value not in param_schema['enum_values']:
                errors.append(f"参数 {param_name} 必须是以下值之一: {param_schema['enum_values']}")

        return errors

    def get_parameter_schema(self, param_name: str) -> Optional[Dict[str, Any]]:
        """获取参数模式"""
        return self.parameters.get(param_name)

    def get_default_configuration(self) -> Dict[str, Any]:
        """获取默认配置"""
        defaults = {}
        for param_name, param_schema in self.parameters.items():
            if 'default' in param_schema:
                defaults[param_name] = param_schema['default']
        return defaults


class ErrorClassification(Enum):
    """错误分类"""
    VALIDATION_ERROR = "validation_error"
    EXECUTION_ERROR = "execution_error"
    TIMEOUT_ERROR = "timeout_error"
    RESOURCE_ERROR = "resource_error"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class StandardizedError:
    """标准化错误"""
    error_code: str
    error_message: str
    error_type: ErrorClassification
    severity: str = "error"  # error, warning, info
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    stack_trace: Optional[str] = None
    suggested_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'error_code': self.error_code,
            'error_message': self.error_message,
            'error_type': self.error_type.value,
            'severity': self.severity,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'stack_trace': self.stack_trace,
            'suggested_actions': self.suggested_actions
        }


class ErrorHandler:
    """错误处理器"""

    def __init__(self):
        self.error_mappings: Dict[str, StandardizedError] = {}
        self.error_handlers: Dict[ErrorClassification, List[callable]] = {}

    def register_error_mapping(self, error_code: str, standardized_error: StandardizedError):
        """注册错误映射"""
        self.error_mappings[error_code] = standardized_error

    def register_error_handler(self, error_type: ErrorClassification, handler: callable):
        """注册错误处理器"""
        if error_type not in self.error_handlers:
            self.error_handlers[error_type] = []
        self.error_handlers[error_type].append(handler)

    async def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> StandardizedError:
        """处理错误"""
        context = context or {}

        # 尝试从异常类型推断错误分类
        error_type = self._classify_error(error)

        # 创建标准化错误
        standardized_error = StandardizedError(
            error_code=f"{error_type.value}_{hash(str(error)) % 10000}",
            error_message=str(error),
            error_type=error_type,
            context=context,
            stack_trace=self._get_stack_trace(error)
        )

        # 调用错误处理器
        if error_type in self.error_handlers:
            for handler in self.error_handlers[error_type]:
                try:
                    await handler(standardized_error)
                except Exception as handler_error:
                    logger.error(f"错误处理器异常: {handler_error}")

        return standardized_error

    def _classify_error(self, error: Exception) -> ErrorClassification:
        """分类错误"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        if 'timeout' in error_str or 'timeout' in error_type:
            return ErrorClassification.TIMEOUT_ERROR
        elif 'validation' in error_str or 'invalid' in error_str:
            return ErrorClassification.VALIDATION_ERROR
        elif 'resource' in error_str or 'memory' in error_str or 'disk' in error_str:
            return ErrorClassification.RESOURCE_ERROR
        elif 'config' in error_str or 'setting' in error_str:
            return ErrorClassification.CONFIGURATION_ERROR
        elif 'network' in error_str or 'connection' in error_str:
            return ErrorClassification.NETWORK_ERROR
        else:
            return ErrorClassification.UNKNOWN_ERROR

    def _get_stack_trace(self, error: Exception) -> Optional[str]:
        """获取堆栈跟踪"""
        import traceback
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))


class DataSerializer:
    """数据序列化器"""

    def __init__(self, format: DataFormat = DataFormat.JSON):
        self.format = format
        self.serializers = {
            DataFormat.JSON: self._serialize_json,
            DataFormat.YAML: self._serialize_yaml,
        }
        self.deserializers = {
            DataFormat.JSON: self._deserialize_json,
            DataFormat.YAML: self._deserialize_yaml,
        }

    def serialize(self, data: Any) -> Union[str, bytes]:
        """序列化数据"""
        if self.format not in self.serializers:
            raise ValueError(f"不支持的数据格式: {self.format}")

        return self.serializers[self.format](data)

    def deserialize(self, data: Union[str, bytes]) -> Any:
        """反序列化数据"""
        if self.format not in self.deserializers:
            raise ValueError(f"不支持的数据格式: {self.format}")

        return self.deserializers[self.format](data)

    def _serialize_json(self, data: Any) -> str:
        """JSON序列化"""
        return json.dumps(data, default=str, ensure_ascii=False)

    def _deserialize_json(self, data: str) -> Any:
        """JSON反序列化"""
        return json.loads(data)

    def _serialize_yaml(self, data: Any) -> str:
        """YAML序列化"""
        try:
            import yaml
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        except ImportError:
            raise ImportError("YAML格式需要安装PyYAML库")

    def _deserialize_yaml(self, data: str) -> Any:
        """YAML反序列化"""
        try:
            import yaml
            return yaml.safe_load(data)
        except ImportError:
            raise ImportError("YAML格式需要安装PyYAML库")


class InterfaceValidator:
    """接口验证器"""

    def __init__(self):
        self.validators: Dict[str, callable] = {}

    def register_validator(self, interface_id: str, validator: callable):
        """注册验证器"""
        self.validators[interface_id] = validator

    async def validate_interface(self, interface_id: str, data: Any) -> List[str]:
        """验证接口"""
        if interface_id not in self.validators:
            return ["未找到接口验证器"]

        validator = self.validators[interface_id]
        try:
            return await validator(data)
        except Exception as e:
            return [f"验证器执行失败: {e}"]


class StandardizedInterfaceRegistry:
    """标准化接口注册表"""

    def __init__(self):
        self.interfaces: Dict[str, InterfaceMetadata] = {}
        self.capability_interfaces: Dict[str, StandardizedCapabilityInterface] = {}
        self.data_serializers: Dict[DataFormat, DataSerializer] = {}
        self.error_handler = ErrorHandler()
        self.interface_validator = InterfaceValidator()

        # 初始化默认序列化器
        for fmt in DataFormat:
            self.data_serializers[fmt] = DataSerializer(fmt)

    def register_interface(self, metadata: InterfaceMetadata):
        """注册接口"""
        self.interfaces[metadata.interface_id] = metadata
        logger.info(f"接口已注册: {metadata.interface_id} v{metadata.version.value}")

    def register_capability_interface(self, capability_id: str,
                                    interface: StandardizedCapabilityInterface):
        """注册能力接口"""
        self.capability_interfaces[capability_id] = interface
        logger.info(f"能力接口已注册: {capability_id}")

    async def process_standardized_request(self, capability_id: str,
                                         request: StandardizedRequest) -> StandardizedResponse:
        """处理标准化请求"""
        if capability_id not in self.capability_interfaces:
            return StandardResponse(
                {},
                success=False,
                error_code="INTERFACE_NOT_FOUND",
                error_message=f"未找到能力接口: {capability_id}"
            )

        interface = self.capability_interfaces[capability_id]

        try:
            # 验证请求
            validation_errors = await interface.validate_request(request)
            if validation_errors:
                return StandardResponse(
                    {'validation_errors': validation_errors},
                    success=False,
                    error_code="VALIDATION_FAILED",
                    error_message="请求验证失败"
                )

            # 处理请求
            response = await interface.process_request(request)
            return response

        except Exception as e:
            # 处理错误
            standardized_error = await self.error_handler.handle_error(e, {
                'capability_id': capability_id,
                'request_id': request.context.request_id
            })

            return StandardResponse(
                {'error': standardized_error.to_dict()},
                success=False,
                error_code=standardized_error.error_code,
                error_message=standardized_error.error_message
            )

    def get_serializer(self, format: DataFormat) -> DataSerializer:
        """获取序列化器"""
        return self.data_serializers[format]

    def get_interface_metadata(self, interface_id: str) -> Optional[InterfaceMetadata]:
        """获取接口元数据"""
        return self.interfaces.get(interface_id)

    def list_interfaces(self, include_deprecated: bool = False) -> List[InterfaceMetadata]:
        """列出接口"""
        interfaces = list(self.interfaces.values())
        if not include_deprecated:
            interfaces = [i for i in interfaces if not i.deprecated]
        return interfaces


# 全局实例
_interface_registry_instance: Optional[StandardizedInterfaceRegistry] = None

def get_standardized_interface_registry() -> StandardizedInterfaceRegistry:
    """获取标准化接口注册表实例"""
    global _interface_registry_instance
    if _interface_registry_instance is None:
        _interface_registry_instance = StandardizedInterfaceRegistry()
    return _interface_registry_instance
