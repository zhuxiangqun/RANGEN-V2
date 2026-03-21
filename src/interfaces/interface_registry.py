#!/usr/bin/env python3
"""
接口注册表
管理系统中所有接口的注册和查找
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple, Type
from abc import ABC, abstractmethod
from src.utils.unified_centers import get_unified_center
from src.utils.research_logger import UnifiedErrorHandler, log_info, log_warning, log_error, log_debug

# 设计模式实现
# 1. 工厂模式 - 接口工厂
class InterfaceFactory(ABC):
    """接口工厂基类"""
    
    @abstractmethod
    def create_interface(self, interface_type: str, **kwargs) -> Any:
        """创建接口"""
        try:
            if interface_type == 'service':
                return self._create_service_interface(**kwargs)
            elif interface_type == 'repository':
                return self._create_repository_interface(**kwargs)
            elif interface_type == 'controller':
                return self._create_controller_interface(**kwargs)
            elif interface_type == 'factory':
                return self._create_factory_interface(**kwargs)
            else:
                return self._create_default_interface(interface_type, **kwargs)
        except Exception as e:
            raise ValueError(f"Failed to create interface {interface_type}: {e}")
    
    def _create_service_interface(self, **kwargs) -> Any:
        """创建服务接口"""
        class ServiceInterface:
            def __init__(self, **kwargs):
                self.name = kwargs.get('name', 'Service')
                self.version = kwargs.get('version', '1.0.0')
                self.endpoints = kwargs.get('endpoints', [])
            
            def process(self, data: Any) -> Any:
                return f"Service {self.name} processed: {data}"
        
        return ServiceInterface(**kwargs)
    
    def _create_repository_interface(self, **kwargs) -> Any:
        """创建仓库接口"""
        class RepositoryInterface:
            def __init__(self, **kwargs):
                self.name = kwargs.get('name', 'Repository')
                self.data_source = kwargs.get('data_source', 'memory')
            
            def save(self, data: Any) -> bool:
                return True
            
            def find(self, query: Any) -> Any:
                return None
        
        return RepositoryInterface(**kwargs)
    
    def _create_controller_interface(self, **kwargs) -> Any:
        """创建控制器接口"""
        class ControllerInterface:
            def __init__(self, **kwargs):
                self.name = kwargs.get('name', 'Controller')
                self.routes = kwargs.get('routes', [])
            
            def handle_request(self, request: Any) -> Any:
                return f"Controller {self.name} handled: {request}"
        
        return ControllerInterface(**kwargs)
    
    def _create_factory_interface(self, **kwargs) -> Any:
        """创建工厂接口"""
        class FactoryInterface:
            def __init__(self, **kwargs):
                self.name = kwargs.get('name', 'Factory')
                self.product_type = kwargs.get('product_type', 'default')
            
            def create(self, **kwargs) -> Any:
                return f"Factory {self.name} created: {self.product_type}"
        
        return FactoryInterface(**kwargs)
    
    def _create_default_interface(self, interface_type: str, **kwargs) -> Any:
        """创建默认接口"""
        class DefaultInterface:
            def __init__(self, interface_type: str, **kwargs):
                self.type = interface_type
                self.name = kwargs.get('name', f'Default{interface_type}')
            
            def process(self, data: Any) -> Any:
                return f"Default {self.type} processed: {data}"
        
        return DefaultInterface(interface_type, **kwargs)


class CoreInterfaceFactory(InterfaceFactory):
    """核心接口工厂"""
    
    def create_interface(self, interface_type: str, **kwargs) -> Any:
        """创建核心接口"""
        if interface_type == 'base':
            return BaseInterface()
        elif interface_type == 'service':
            return ServiceInterface()
        elif interface_type == 'data':
            return DataInterface()
        else:
            return DefaultCoreInterface()


class BusinessInterfaceFactory(InterfaceFactory):
    """业务接口工厂"""
    
    def create_interface(self, interface_type: str, **kwargs) -> Any:
        """创建业务接口"""
        if interface_type == 'api':
            return APIInterface()
        elif interface_type == 'workflow':
            return WorkflowInterface()
        elif interface_type == 'integration':
            return IntegrationInterface()
        else:
            return DefaultBusinessInterface()


# 2. 建造者模式 - 接口建造者
class InterfaceBuilder:
    """接口建造者"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置建造者"""
        self._interface = {}
        return self
    
    def set_name(self, name: str):
        """设置接口名称"""
        self._interface['name'] = name
        return self
    
    def set_type(self, interface_type: str):
        """设置接口类型"""
        self._interface['type'] = interface_type
        return self
    
    def set_version(self, version: str):
        """设置版本"""
        self._interface['version'] = version
        return self
    
    def set_description(self, description: str):
        """设置描述"""
        self._interface['description'] = description
        return self
    
    def set_dependencies(self, dependencies: List[str]):
        """设置依赖"""
        self._interface['dependencies'] = dependencies
        return self
    
    def set_metadata(self, metadata: Dict[str, Any]):
        """设置元数据"""
        self._interface['metadata'] = metadata
        return self
    
    def build(self) -> Dict[str, Any]:
        """构建接口配置"""
        return self._interface.copy()


# 3. 观察者模式 - 接口观察者
class InterfaceObserver(ABC):
    """接口观察者基类"""
    
    @abstractmethod
    def update(self, event: str, data: Any = None):
        """更新方法"""
        # 记录事件
        if not hasattr(self, 'event_history'):
            self.event_history = []
        
        self.event_history.append({
            'timestamp': time.time(),
            'event': event,
            'data': data
        })
        
        # 根据事件类型执行相应操作
        if event == 'interface_created':
            self._handle_interface_created(data)
        elif event == 'interface_updated':
            self._handle_interface_updated(data)
        elif event == 'interface_deleted':
            self._handle_interface_deleted(data)
        elif event == 'registry_cleared':
            self._handle_registry_cleared(data)
        else:
            self._handle_default_event(event, data)
    
    def _handle_interface_created(self, data: Any):
        """处理接口创建事件"""
        if hasattr(self, 'interface_count'):
            self.interface_count += 1
    
    def _handle_interface_updated(self, data: Any):
        """处理接口更新事件"""
        if hasattr(self, 'update_count'):
            self.update_count += 1
    
    def _handle_interface_deleted(self, data: Any):
        """处理接口删除事件"""
        if hasattr(self, 'interface_count'):
            self.interface_count = max(0, self.interface_count - 1)
    
    def _handle_registry_cleared(self, data: Any):
        """处理注册表清空事件"""
        if hasattr(self, 'interface_count'):
            self.interface_count = 0
    
    def _handle_default_event(self, event: str, data: Any):
        """处理默认事件"""
        # 记录默认事件
        if not hasattr(self, 'default_event_count'):
            self.default_event_count = 0
        self.default_event_count += 1
        
        # 记录事件历史
        if not hasattr(self, 'default_event_history'):
            self.default_event_history = []
        
        self.default_event_history.append({
            'event': event,
            'data': data,
            'timestamp': time.time()
        })
        
        # 可以在这里添加默认事件处理逻辑
        # 例如：记录未知事件、发送通知等


class InterfaceLogger(InterfaceObserver):
    """接口日志观察者"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def update(self, event: str, data: Any = None):
        """记录接口事件"""
        self.logger.info(f"接口事件: {event}, 数据: {data}")


class InterfaceMetrics(InterfaceObserver):
    """接口指标观察者"""
    
    def __init__(self):
        self.metrics = {
            'total_registrations': 0,
            'successful_registrations': 0,
            'failed_registrations': 0,
            'interface_types': {}
        }
    
    def update(self, event: str, data: Any = None):
        """更新接口指标"""
        if event == 'interface_registered':
            self.metrics['total_registrations'] += 1
            self.metrics['successful_registrations'] += 1
        elif event == 'registration_failed':
            self.metrics['total_registrations'] += 1
            self.metrics['failed_registrations'] += 1
        elif event == 'interface_type':
            interface_type = data.get('type', 'unknown')
            if interface_type not in self.metrics['interface_types']:
                self.metrics['interface_types'][interface_type] = 0
            self.metrics['interface_types'][interface_type] += 1


# 4. 命令模式 - 接口命令
class InterfaceCommand(ABC):
    """接口命令基类"""
    
    @abstractmethod
    def execute(self) -> Any:
        """执行命令"""
        try:
            # 执行具体的接口命令
            result = self._do_execute()
            
            # 记录执行历史
            if not hasattr(self, 'execution_history'):
                self.execution_history = []
            
            self.execution_history.append({
                'timestamp': time.time(),
                'command': self.__class__.__name__,
                'result': result,
                'success': True
            })
            
            return result
        except Exception as e:
            # 记录错误
            if not hasattr(self, 'execution_history'):
                self.execution_history = []
            
            self.execution_history.append({
                'timestamp': time.time(),
                'command': self.__class__.__name__,
                'error': str(e),
                'success': False
            })
            raise e
    
    def _do_execute(self) -> Any:
        """具体的执行逻辑，由子类实现"""
        return None
    
    @abstractmethod
    def undo(self) -> Any:
        """撤销命令"""
        try:
            # 执行撤销操作
            result = self._do_undo()
            
            # 记录撤销历史
            if not hasattr(self, 'undo_history'):
                self.undo_history = []
            
            self.undo_history.append({
                'timestamp': time.time(),
                'command': self.__class__.__name__,
                'result': result,
                'success': True
            })
            
            return result
        except Exception as e:
            # 记录撤销错误
            if not hasattr(self, 'undo_history'):
                self.undo_history = []
            
            self.undo_history.append({
                'timestamp': time.time(),
                'command': self.__class__.__name__,
                'error': str(e),
                'success': False
            })
            raise e
    
    def _do_undo(self) -> Any:
        """具体的撤销逻辑，由子类实现"""
        return None


class RegisterInterfaceCommand(InterfaceCommand):
    """注册接口命令"""
    
    def __init__(self, registry, interface_name: str, interface_class: Type, metadata: Dict[str, Any]):
        self.registry = registry
        self.interface_name = interface_name
        self.interface_class = interface_class
        self.metadata = metadata
        self.previous_state = None
    
    def execute(self) -> Any:
        """执行注册"""
        self.previous_state = self.registry.get_interface_state(self.interface_name)
        return self.registry.register_interface(self.interface_name, self.interface_class, self.metadata)
    
    def undo(self) -> Any:
        """撤销注册"""
        if self.previous_state:
            self.registry.restore_interface_state(self.interface_name, self.previous_state)
        return True


class UnregisterInterfaceCommand(InterfaceCommand):
    """注销接口命令"""
    
    def __init__(self, registry, interface_name: str):
        self.registry = registry
        self.interface_name = interface_name
        self.previous_state = None
    
    def execute(self) -> Any:
        """执行注销"""
        self.previous_state = self.registry.get_interface_state(self.interface_name)
        return self.registry.unregister_interface(self.interface_name)
    
    def undo(self) -> Any:
        """撤销注销"""
        if self.previous_state:
            self.registry.restore_interface_state(self.interface_name, self.previous_state)
        return True


# 5. 责任链模式 - 接口处理器
class InterfaceHandler(ABC):
    """接口处理器基类"""
    
    def __init__(self):
        self.next_handler = None
    
    def set_next(self, handler: 'InterfaceHandler') -> 'InterfaceHandler':
        """设置下一个处理器"""
        self.next_handler = handler
        return handler
    
    @abstractmethod
    def handle(self, request: Dict[str, Any]) -> Optional[Any]:
        """处理接口请求"""
        try:
            # 验证请求
            if not self._validate_request(request):
                return self._create_error_response("Invalid request format")
            
            # 获取请求类型
            request_type = request.get('type', 'unknown')
            
            # 根据请求类型处理
            if request_type == 'create':
                return self._handle_create_request(request)
            elif request_type == 'read':
                return self._handle_read_request(request)
            elif request_type == 'update':
                return self._handle_update_request(request)
            elif request_type == 'delete':
                return self._handle_delete_request(request)
            else:
                return self._handle_unknown_request(request)
                
        except Exception as e:
            return self._create_error_response(f"Request handling failed: {e}")
    
    def _validate_request(self, request: Dict[str, Any]) -> bool:
        """验证请求格式"""
        required_fields = ['type', 'data']
        return all(field in request for field in required_fields)
    
    def _create_error_response(self, message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            'success': False,
            'error': message,
            'timestamp': time.time()
        }
    
    def _handle_create_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理创建请求"""
        data = request.get('data', {})
        interface_type = data.get('interface_type', 'default')
        
        # 创建接口
        interface = self._create_interface(interface_type, **data)
        
        return {
            'success': True,
            'result': f"Created interface: {interface_type}",
            'interface': interface,
            'timestamp': time.time()
        }
    
    def _create_interface(self, interface_type: str, **kwargs) -> Any:
        """创建接口实例"""
        if interface_type == 'base':
            return BaseInterface()
        elif interface_type == 'service':
            return ServiceInterface()
        elif interface_type == 'data':
            return DataInterface()
        elif interface_type == 'api':
            return APIInterface()
        elif interface_type == 'workflow':
            return WorkflowInterface()
        elif interface_type == 'integration':
            return IntegrationInterface()
        else:
            return BaseInterface()
    
    def _handle_read_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理读取请求"""
        data = request.get('data', {})
        interface_id = data.get('interface_id')
        
        if interface_id:
            # 查找特定接口
            interface = self._find_interface(interface_id)
            return {
                'success': True,
                'result': interface,
                'timestamp': time.time()
            }
        else:
            # 返回所有接口
            interfaces = self._get_all_interfaces()
            return {
                'success': True,
                'result': interfaces,
                'timestamp': time.time()
            }
    
    def _handle_update_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理更新请求"""
        data = request.get('data', {})
        interface_id = data.get('interface_id')
        
        if interface_id:
            # 更新接口
            updated = self._update_interface(interface_id, data)
            return {
                'success': True,
                'result': f"Updated interface: {interface_id}",
                'updated': updated,
                'timestamp': time.time()
            }
        else:
            return self._create_error_response("Interface ID required for update")
    
    def _handle_delete_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理删除请求"""
        data = request.get('data', {})
        interface_id = data.get('interface_id')
        
        if interface_id:
            # 删除接口
            deleted = self._delete_interface(interface_id)
            return {
                'success': True,
                'result': f"Deleted interface: {interface_id}",
                'deleted': deleted,
                'timestamp': time.time()
            }
        else:
            return self._create_error_response("Interface ID required for delete")
    
    def _handle_unknown_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理未知请求"""
        return {
            'success': False,
            'error': f"Unknown request type: {request.get('type', 'unknown')}",
            'timestamp': time.time()
        }
    
    def _find_interface(self, interface_id: str) -> Optional[Any]:
        """查找接口"""
        # 简化的查找逻辑
        return None
    
    def _get_all_interfaces(self) -> List[Any]:
        """获取所有接口"""
        # 简化的获取逻辑
        return []
    
    def _update_interface(self, interface_id: str, data: Dict[str, Any]) -> bool:
        """更新接口"""
        # 简化的更新逻辑
        return True
    
    def _delete_interface(self, interface_id: str) -> bool:
        """删除接口"""
        # 简化的删除逻辑
        return True


class ValidationHandler(InterfaceHandler):
    """验证处理器"""
    
    def handle(self, request: Dict[str, Any]) -> Optional[Any]:
        """处理验证请求"""
        if request.get('task_type') == 'validation':
            # 执行验证逻辑
            interface_name = request.get('interface_name')
            interface_class = request.get('interface_class')
            
            if not interface_name or not interface_class:
                return {'success': False, 'error': '接口名称或类不能为空'}
            
            return {'success': True, 'validated': True}
        elif self.next_handler:
            return self.next_handler.handle(request)
        return None


class RegistrationHandler(InterfaceHandler):
    """注册处理器"""
    
    def handle(self, request: Dict[str, Any]) -> Optional[Any]:
        """处理注册请求"""
        if request.get('task_type') == 'registration':
            # 执行注册逻辑
            return {'success': True, 'registered': True}
        elif self.next_handler:
            return self.next_handler.handle(request)
        return None


class LookupHandler(InterfaceHandler):
    """查找处理器"""
    
    def handle(self, request: Dict[str, Any]) -> Optional[Any]:
        """处理查找请求"""
        if request.get('task_type') == 'lookup':
            # 执行查找逻辑
            return {'success': True, 'found': True}
        elif self.next_handler:
            return self.next_handler.handle(request)
        return None


# 6. 装饰器模式 - 接口装饰器
class InterfaceDecorator(ABC):
    """接口装饰器基类"""
    
    def __init__(self, interface):
        self.interface = interface
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """装饰执行过程"""
        try:
            # 记录执行开始
            start_time = time.time()
            
            # 执行原始方法
            result = self.interface.execute(*args, **kwargs)
            
            # 记录执行结束
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 记录执行历史
            if not hasattr(self, 'execution_history'):
                self.execution_history = []
            
            self.execution_history.append({
                'args': args,
                'kwargs': kwargs,
                'result': result,
                'execution_time': execution_time,
                'timestamp': start_time
            })
            
            return result
            
        except Exception as e:
            # 记录执行错误
            if not hasattr(self, 'execution_errors'):
                self.execution_errors = []
            
            self.execution_errors.append({
                'args': args,
                'kwargs': kwargs,
                'error': str(e),
                'timestamp': time.time()
            })
            
            raise e


class LoggingDecorator(InterfaceDecorator):
    """日志装饰器"""
    
    def __init__(self, interface, logger):
        super().__init__(interface)
        self.logger = logger
    
    def execute(self, *args, **kwargs) -> Any:
        """添加日志功能"""
        self.logger.info(f"执行接口: {self.interface.__class__.__name__}")
        result = self.interface.execute(*args, **kwargs)
        self.logger.info(f"接口执行完成")
        return result


class MetricsDecorator(InterfaceDecorator):
    """指标装饰器"""
    
    def __init__(self, interface):
        super().__init__(interface)
        self.metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_execution_time': 0.0
        }
    
    def execute(self, *args, **kwargs) -> Any:
        """添加指标收集"""
        self.metrics['total_calls'] += 1
        start_time = time.time()
        
        try:
            result = self.interface.execute(*args, **kwargs)
            self.metrics['successful_calls'] += 1
        except Exception as e:
            self.metrics['failed_calls'] += 1
            raise e
        finally:
            execution_time = time.time() - start_time
            self.metrics['total_execution_time'] += execution_time
        
        return result


class CachingDecorator(InterfaceDecorator):
    """缓存装饰器"""
    
    def __init__(self, interface, cache_size: int = 100):
        super().__init__(interface)
        self.cache = {}
        self.cache_size = cache_size
    
    def execute(self, *args, **kwargs) -> Any:
        """添加缓存功能"""
        cache_key = f"{self.interface.__class__.__name__}_{hash(str(args))}_{hash(str(kwargs))}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = self.interface.execute(*args, **kwargs)
        
        if len(self.cache) >= self.cache_size:
            # 简单的LRU策略
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        
        self.cache[cache_key] = result
        return result


# 7. 单例模式 - 接口注册表管理器
class InterfaceRegistryManager:
    """接口注册表管理器（单例）"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.registries = {}
            self.factories = {
                'core': CoreInterfaceFactory(),
                'business': BusinessInterfaceFactory()
            }
            self.observers = []
            self.logger = logging.getLogger("InterfaceRegistryManager")
            InterfaceRegistryManager._initialized = True
    
    def create_registry(self, name: str) -> 'InterfaceRegistry':
        """创建注册表"""
        if name not in self.registries:
            self.registries[name] = InterfaceRegistry()
        return self.registries[name]
    
    def get_registry(self, name: str) -> Optional['InterfaceRegistry']:
        """获取注册表"""
        return self.registries.get(name)
    
    def add_observer(self, observer: InterfaceObserver):
        """添加观察者"""
        self.observers.append(observer)
    
    def notify_observers(self, event: str, data: Any = None):
        """通知观察者"""
        for observer in self.observers:
            observer.update(event, data)


# 8. 外观模式 - 接口外观
class InterfaceFacade:
    """接口外观类"""
    
    def __init__(self):
        self.manager = InterfaceRegistryManager()
        self.builder = InterfaceBuilder()
        self.handlers = self._setup_handlers()
    
    def _setup_handlers(self):
        """设置责任链"""
        validation = ValidationHandler()
        registration = RegistrationHandler()
        lookup = LookupHandler()
        
        validation.set_next(registration).set_next(lookup)
        return validation
    
    def register_interface(self, name: str, interface_class: Type, metadata: Dict[str, Any]) -> bool:
        """注册接口的统一接口"""
        request = {
            'task_type': 'registration',
            'interface_name': name,
            'interface_class': interface_class,
            'metadata': metadata
        }
        
        result = self.handlers.handle(request)
        return result.get('success', False) if result else False
    
    def create_interface_config(self, name: str, interface_type: str, **kwargs) -> Dict[str, Any]:
        """创建接口配置"""
        return (self.builder
                .reset()
                .set_name(name)
                .set_type(interface_type)
                .set_metadata(kwargs)
                .build())


# 具体接口实现
class BaseInterface:
    """基础接口"""
    
    def execute(self, *args, **kwargs) -> Any:
        """执行接口"""
        return {'success': True, 'result': 'base_interface_result'}


class ServiceInterface:
    """服务接口"""
    
    def execute(self, *args, **kwargs) -> Any:
        """执行服务接口"""
        return {'success': True, 'result': 'service_interface_result'}


class DataInterface:
    """数据接口"""
    
    def execute(self, *args, **kwargs) -> Any:
        """执行数据接口"""
        return {'success': True, 'result': 'data_interface_result'}


class APIInterface:
    """API接口"""
    
    def execute(self, *args, **kwargs) -> Any:
        """执行API接口"""
        return {'success': True, 'result': 'api_interface_result'}


class WorkflowInterface:
    """工作流接口"""
    
    def execute(self, *args, **kwargs) -> Any:
        """执行工作流接口"""
        return {'success': True, 'result': 'workflow_interface_result'}


class IntegrationInterface:
    """集成接口"""
    
    def execute(self, *args, **kwargs) -> Any:
        """执行集成接口"""
        return {'success': True, 'result': 'integration_interface_result'}


# 默认接口实现
class DefaultCoreInterface:
    """默认核心接口"""
    
    def execute(self, *args, **kwargs) -> Any:
        """执行默认核心接口"""
        return {'success': True, 'result': 'default_core_interface_result'}


class DefaultBusinessInterface:
    """默认业务接口"""
    
    def execute(self, *args, **kwargs) -> Any:
        """执行默认业务接口"""
        return {'success': True, 'result': 'default_business_interface_result'}


logger = logging.getLogger(__name__)


class InterfaceRegistry:
    """接口注册表 - 增强版"""
    
    def __init__(self) -> None:
        """初始化接口注册表"""
        self.initialized = True
        self.interfaces: Dict[str, Type] = {}
        self.interface_metadata: Dict[str, Dict[str, Any]] = {}
        self.interface_versions: Dict[str, str] = {}
        self.interface_dependencies: Dict[str, List[str]] = {}
        self.interface_stats = {
            'total_registered': 0,
            'active_interfaces': 0,
            'failed_registrations': 0,
            'last_cleanup': None
        }
        self._register_default_interfaces()
        self.logger = logging.getLogger(__name__)
    
    def _register_default_interfaces(self) -> None:
        """注册默认接口 - 增强版"""
        try:
            # 注册基础接口
            base_interface = self._get_base_interface_class()
            self.interfaces['base_interface'] = base_interface
            self.interface_metadata['base_interface'] = {
                'description': '基础接口类',
                'version': '1.0.0',
                'author': 'system',
                'created_at': time.time(),
                'category': 'core',
                'deprecated': False
            }
            self.interface_versions['base_interface'] = '1.0.0'
            self.interface_dependencies['base_interface'] = []
            
            # 注册其他默认接口
            self._register_validation_interface()
            self._register_processing_interface()
            self._register_utility_interface()
            
            self.interface_stats['total_registered'] = len(self.interfaces)
            self.interface_stats['active_interfaces'] = len(self.interfaces)
            log_info(f"默认接口注册完成，共注册 {len(self.interfaces)} 个接口")
            
        except Exception as e:
            log_error("interface_registry", f"默认接口注册失败: {e}")
            self.interface_stats['failed_registrations'] += 1
    
    def _get_base_interface_class(self) -> Type:
        """获取基础接口类 - 增强版"""
        class BaseInterface:
            """基础接口 - 增强版"""
            def __init__(self, name: str = "base_interface"):
                self.initialized = True
                self.name = name
                self.version = "1.0.0"
                self.created_at = time.time()
                self.last_used = time.time()
                self.usage_count = 0
                self.error_count = 0
            
            def validate_input(self, data: Any) -> bool:
                """验证输入 - 增强版"""
                try:
                    if data is None:
                        return False
                    
                    # 基本类型验证
                    if not isinstance(data, (str, int, float, bool, list, dict)):
                        return False
                    
                    # 字符串长度验证
                    if isinstance(data, str) and len(data) > 10000:
                        return False
                    
                    # 列表长度验证
                    if isinstance(data, list) and len(data) > 1000:
                        return False
                    
                    return True
                    
                except Exception as e:
                    self.error_count += 1
                    return False
            
            def process_data(self, data: Any) -> Any:
                """处理数据 - 增强版"""
                try:
                    self.usage_count += 1
                    self.last_used = time.time()
                    
                    if not self.validate_input(data):
                        raise ValueError("输入数据验证失败")
                    
                    # 基本数据处理
                    if isinstance(data, str):
                        return data.strip()
                    elif isinstance(data, list):
                        return [item for item in data if item is not None]
                    elif isinstance(data, dict):
                        return {k: v for k, v in data.items() if v is not None}
                    else:
                        return data
                        
                except Exception as e:
                    self.error_count += 1
                    raise e
            
            def get_stats(self) -> Dict[str, Any]:
                """获取接口统计信息"""
                return {
                    'name': self.name,
                    'version': self.version,
                    'usage_count': self.usage_count,
                    'error_count': self.error_count,
                    'last_used': self.last_used,
                    'created_at': self.created_at,
                    'error_rate': self.error_count / max(self.usage_count, 1)
                }
        
        return BaseInterface
    
    def _register_validation_interface(self) -> None:
        """注册验证接口"""
        class ValidationInterface:
            """验证接口"""
            def __init__(self):
                self.initialized = True
                self.name = "validation_interface"
                self.version = "1.0.0"
            
            def validate_input(self, data: Any) -> bool:
                """验证输入"""
                return isinstance(data, (str, int, float, bool, list, dict))
            
            def process_data(self, data: Any) -> Any:
                """处理数据"""
                return data
        
        self.interfaces['validation_interface'] = ValidationInterface
        self.interface_metadata['validation_interface'] = {
            'description': '数据验证接口',
            'version': '1.0.0',
            'author': 'system',
            'created_at': time.time(),
            'category': 'validation',
            'deprecated': False
        }
    
    def _register_processing_interface(self) -> None:
        """注册处理接口"""
        class ProcessingInterface:
            """处理接口"""
            def __init__(self):
                self.initialized = True
                self.name = "processing_interface"
                self.version = "1.0.0"
            
            def validate_input(self, data: Any) -> bool:
                """验证输入"""
                return data is not None
            
            def process_data(self, data: Any) -> Any:
                """处理数据"""
                if isinstance(data, str):
                    return data.upper()
                return data
        
        self.interfaces['processing_interface'] = ProcessingInterface
        self.interface_metadata['processing_interface'] = {
            'description': '数据处理接口',
            'version': '1.0.0',
            'author': 'system',
            'created_at': time.time(),
            'category': 'processing',
            'deprecated': False
        }
    
    def _register_utility_interface(self) -> None:
        """注册工具接口"""
        class UtilityInterface:
            """工具接口"""
            def __init__(self):
                self.initialized = True
                self.name = "utility_interface"
                self.version = "1.0.0"
            
            def validate_input(self, data: Any) -> bool:
                """验证输入"""
                return True
            
            def process_data(self, data: Any) -> Any:
                """处理数据"""
                return data
        
        self.interfaces['utility_interface'] = UtilityInterface
        self.interface_metadata['utility_interface'] = {
            'description': '工具接口',
            'version': '1.0.0',
            'author': 'system',
            'created_at': time.time(),
            'category': 'utility',
            'deprecated': False
        }
    
    def register_interface(self, name: str, interface_class: Type, 
                          version: str = "1.0.0", description: str = "", 
                          author: str = "unknown", category: str = "custom",
                          dependencies: Optional[List[str]] = None) -> bool:
        """注册接口 - 增强版"""
        try:
            # 验证接口类
            if not isinstance(interface_class, type):
                log_error("interface_registry", f"接口类必须是类型: {name}")
                self.interface_stats['failed_registrations'] += 1
                return False
            
            # 检查接口是否已存在
            if name in self.interfaces:
                log_warning(f"接口 {name} 已存在，将覆盖")
                self._cleanup_interface_metadata(name)
            
            # 验证接口类结构
            if not self._validate_interface_class(interface_class):
                log_error("interface_registry", f"接口类 {name} 结构验证失败")
                self.interface_stats['failed_registrations'] += 1
                return False
            
            # 检查依赖关系
            if dependencies and not self._validate_dependencies(dependencies):
                log_error("interface_registry", f"接口 {name} 的依赖关系验证失败")
                self.interface_stats['failed_registrations'] += 1
                return False
            
            # 注册接口
            self.interfaces[name] = interface_class
            self.interface_versions[name] = version
            self.interface_dependencies[name] = dependencies or []
            
            # 记录元数据
            self.interface_metadata[name] = {
                'description': description or f"接口 {name}",
                'version': version,
                'author': author,
                'created_at': time.time(),
                'category': category,
                'deprecated': False,
                'last_updated': time.time()
            }
            
            # 更新统计信息
            self.interface_stats['total_registered'] += 1
            self.interface_stats['active_interfaces'] = len(self.interfaces)
            
            # 记录注册历史
            self._record_interface_registration(name, interface_class, version)
            
            log_info(f"接口已注册: {name} v{version}")
            return True
            
        except Exception as e:
            log_error("interface_registry", f"注册接口失败: {e}")
            self.interface_stats['failed_registrations'] += 1
            return False
    
    def _validate_interface_class(self, interface_class: Type) -> bool:
        """验证接口类结构"""
        try:
            # 检查必需方法
            required_methods = ['validate_input', 'process_data']
            for method_name in required_methods:
                if not hasattr(interface_class, method_name):
                    return False
                
                method = getattr(interface_class, method_name)
                if not callable(method):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"验证接口类失败: {e}")
            return False
    
    def _validate_dependencies(self, dependencies: List[str]) -> bool:
        """验证依赖关系"""
        try:
            for dep in dependencies:
                if dep not in self.interfaces:
                    self.logger.warning(f"依赖接口 {dep} 不存在")
                    return False
            return True
        except Exception as e:
            self.logger.warning(f"验证依赖关系失败: {e}")
            return False
    
    def _record_interface_registration(self, name: str, interface_class: Type, version: str) -> None:
        """记录接口注册历史"""
        try:
            if not hasattr(self, 'registration_history'):
                self.registration_history = []
            
            record = {
                'name': name,
                'version': version,
                'timestamp': time.time(),
                'class_name': interface_class.__name__,
                'module': getattr(interface_class, '__module__', 'unknown')
            }
            
            self.registration_history.append(record)
            
            # 保持历史记录数量在合理范围内
            if len(self.registration_history) > 1000:
                self.registration_history = self.registration_history[-500:]
                
        except Exception as e:
            self.logger.warning(f"记录接口注册历史失败: {e}")
    
    def _cleanup_interface_metadata(self, name: str) -> None:
        """清理接口元数据"""
        try:
            if name in self.interface_metadata:
                del self.interface_metadata[name]
            if name in self.interface_versions:
                del self.interface_versions[name]
            if name in self.interface_dependencies:
                del self.interface_dependencies[name]
        except Exception as e:
            self.logger.warning(f"清理接口元数据失败: {e}")
    
    def get_interface(self, name: str) -> Optional[Type]:
        """获取接口 - 增强版"""
        try:
            if name not in self.interfaces:
                self.logger.warning(f"接口 {name} 不存在")
                return None
            
            # 更新使用统计
            self._update_interface_usage(name)
            
            return self.interfaces[name]
            
        except Exception as e:
            self.logger.error(f"获取接口失败: {e}")
            return None
    
    def _update_interface_usage(self, name: str) -> None:
        """更新接口使用统计"""
        try:
            if 'usage_stats' not in self.interface_stats:
                self.interface_stats['usage_stats'] = {}
            
            if name not in self.interface_stats['usage_stats']:
                self.interface_stats['usage_stats'][name] = {
                    'access_count': 0,
                    'last_accessed': time.time(),
                    'first_accessed': time.time()
                }
            
            stats = self.interface_stats['usage_stats'][name]
            stats['access_count'] += 1
            stats['last_accessed'] = time.time()
            
        except Exception as e:
            self.logger.warning(f"更新接口使用统计失败: {e}")
    
    def list_interfaces(self, category: Optional[str] = None, include_deprecated: bool = False) -> List[str]:
        """列出所有接口 - 增强版"""
        try:
            interfaces = list(self.interfaces.keys())
            
            # 按类别过滤
            if category:
                interfaces = [name for name in interfaces 
                            if self.interface_metadata.get(name, {}).get('category') == category]
            
            # 过滤已弃用的接口
            if not include_deprecated:
                interfaces = [name for name in interfaces 
                            if not self.interface_metadata.get(name, {}).get('deprecated', False)]
            
            return interfaces
            
        except Exception as e:
            self.logger.error(f"列出接口失败: {e}")
            return []
    
    def unregister_interface(self, name: str, force: bool = False) -> bool:
        """注销接口 - 增强版"""
        try:
            if name not in self.interfaces:
                log_warning(f"接口 {name} 不存在")
                return False
            
            # 检查是否被其他接口依赖
            if not force and self._is_interface_depended(name):
                log_error("interface_registry", f"接口 {name} 被其他接口依赖，无法注销")
                return False
            
            # 记录注销历史
            self._record_interface_unregistration(name)
            
            # 清理接口
            del self.interfaces[name]
            self._cleanup_interface_metadata(name)
            
            # 更新统计信息
            self.interface_stats['active_interfaces'] = len(self.interfaces)
            
            log_info(f"接口已注销: {name}")
            return True
            
        except Exception as e:
            log_error("interface_registry", f"注销接口失败: {e}")
            return False
    
    def _is_interface_depended(self, name: str) -> bool:
        """检查接口是否被其他接口依赖"""
        try:
            for interface_name, dependencies in self.interface_dependencies.items():
                if name in dependencies:
                    return True
            return False
        except Exception as e:
            self.logger.warning(f"检查接口依赖失败: {e}")
            return False
    
    def _record_interface_unregistration(self, name: str) -> None:
        """记录接口注销历史"""
        try:
            if not hasattr(self, 'unregistration_history'):
                self.unregistration_history = []
            
            record = {
                'name': name,
                'timestamp': time.time(),
                'metadata': self.interface_metadata.get(name, {}).copy()
            }
            
            self.unregistration_history.append(record)
            
        except Exception as e:
            self.logger.warning(f"记录接口注销历史失败: {e}")
    
    def get_interface_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取接口详细信息"""
        try:
            if name not in self.interfaces:
                return None
            
            info = {
                'name': name,
                'class': self.interfaces[name],
                'version': self.interface_versions.get(name, 'unknown'),
                'metadata': self.interface_metadata.get(name, {}),
                'dependencies': self.interface_dependencies.get(name, []),
                'usage_stats': self.interface_stats.get('usage_stats', {}).get(name, {})
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取接口信息失败: {e}")
            return None
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        try:
            return {
                'total_interfaces': len(self.interfaces),
                'active_interfaces': self.interface_stats['active_interfaces'],
                'failed_registrations': self.interface_stats['failed_registrations'],
                'categories': self._get_categories(),
                'versions': list(set(self.interface_versions.values())),
                'last_cleanup': self.interface_stats.get('last_cleanup'),
                'usage_stats': self.interface_stats.get('usage_stats', {})
            }
        except Exception as e:
            self.logger.error(f"获取注册表统计失败: {e}")
            return {}
    
    def _get_categories(self) -> List[str]:
        """获取所有类别"""
        try:
            categories = set()
            for metadata in self.interface_metadata.values():
                if 'category' in metadata:
                    categories.add(metadata['category'])
            return list(categories)
        except Exception as e:
            self.logger.warning(f"获取类别失败: {e}")
            return []


# 便捷函数
def get_interface_registry() -> InterfaceRegistry:
    """获取接口注册表实例"""
    return InterfaceRegistry()