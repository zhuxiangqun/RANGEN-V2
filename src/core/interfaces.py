"""
核心接口定义
定义系统核心组件的接口，降低模块间耦合度
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class IConfigurationService(ABC):
    """配置服务接口"""
    
    @abstractmethod
    def get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """获取配置值"""
        pass
    
    @abstractmethod
    def set_config_value(self, section: str, key: str, value: Any) -> bool:
        """设置配置值"""
        pass
    
    @abstractmethod
    def has_config(self, section: str, key: str) -> bool:
        """检查配置是否存在"""
        pass


class ILoggingService(ABC):
    """日志服务接口"""
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """记录信息日志"""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志"""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """记录错误日志"""
        pass
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志"""
        pass


class IKnowledgeRetrievalService(ABC):
    """知识检索服务接口"""
    
    @abstractmethod
    def search(self, query: str, context: Dict[str, Any]) -> ProcessingResult:
        """搜索知识"""
        pass
    
    @abstractmethod
    def retrieve(self, document_id: str) -> ProcessingResult:
        """检索文档"""
        pass
    
    @abstractmethod
    def index_document(self, document: Dict[str, Any]) -> ProcessingResult:
        """索引文档"""
        pass


class IReasoningService(ABC):
    """推理服务接口"""
    
    @abstractmethod
    def reason(self, context: Dict[str, Any], strategy: str) -> ProcessingResult:
        """执行推理"""
        pass
    
    @abstractmethod
    def get_available_strategies(self) -> List[str]:
        """获取可用的推理策略"""
        pass


class IMLService(ABC):
    """机器学习服务接口"""
    
    @abstractmethod
    def train(self, data: Any, model_type: str) -> ProcessingResult:
        """训练模型"""
        pass
    
    @abstractmethod
    def predict(self, data: Any, model_id: str) -> ProcessingResult:
        """预测"""
        pass
    
    @abstractmethod
    def evaluate(self, data: Any, model_id: str) -> ProcessingResult:
        """评估模型"""
        pass


class IRLService(ABC):
    """强化学习服务接口"""
    
    @abstractmethod
    def train_agent(self, environment: Any, agent_config: Dict[str, Any]) -> ProcessingResult:
        """训练智能体"""
        pass
    
    @abstractmethod
    def get_action(self, state: Any, agent_id: str) -> ProcessingResult:
        """获取动作"""
        pass
    
    @abstractmethod
    def update_policy(self, experience: Any, agent_id: str) -> ProcessingResult:
        """更新策略"""
        pass


class IBusinessLogicService(ABC):
    """业务逻辑服务接口"""
    
    @abstractmethod
    def process_request(self, request: Any) -> ProcessingResult:
        """处理请求"""
        pass
    
    @abstractmethod
    def validate_request(self, request: Any) -> ProcessingResult:
        """验证请求"""
        pass
    
    @abstractmethod
    def execute_business_rule(self, rule_name: str, context: Dict[str, Any]) -> ProcessingResult:
        """执行业务规则"""
        pass


class IDataProcessingService(ABC):
    """数据处理服务接口"""
    
    @abstractmethod
    def preprocess(self, data: Any) -> ProcessingResult:
        """预处理数据"""
        pass
    
    @abstractmethod
    def transform(self, data: Any, transformation: str) -> ProcessingResult:
        """转换数据"""
        pass
    
    @abstractmethod
    def validate(self, data: Any, schema: Dict[str, Any]) -> ProcessingResult:
        """验证数据"""
        pass


class IMonitoringService(ABC):
    """监控服务接口"""
    
    @abstractmethod
    def start_monitoring(self, component: str) -> None:
        """开始监控组件"""
        pass
    
    @abstractmethod
    def stop_monitoring(self, component: str) -> None:
        """停止监控组件"""
        pass
    
    @abstractmethod
    def get_metrics(self, component: str) -> Dict[str, Any]:
        """获取指标"""
        pass
    
    @abstractmethod
    def report_error(self, component: str, error: Exception) -> None:
        """报告错误"""
        pass


class ISecurityService(ABC):
    """安全服务接口"""
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> ProcessingResult:
        """认证"""
        pass
    
    @abstractmethod
    def authorize(self, user_id: str, resource: str, action: str) -> ProcessingResult:
        """授权"""
        pass
    
    @abstractmethod
    def encrypt(self, data: Any) -> ProcessingResult:
        """加密数据"""
        pass
    
    @abstractmethod
    def decrypt(self, encrypted_data: Any) -> ProcessingResult:
        """解密数据"""
        pass


class IEventService(ABC):
    """事件服务接口"""
    
    @abstractmethod
    def publish(self, event: str, data: Any) -> None:
        """发布事件"""
        pass
    
    @abstractmethod
    def subscribe(self, event: str, handler: callable) -> None:
        """订阅事件"""
        pass
    
    @abstractmethod
    def unsubscribe(self, event: str, handler: callable) -> None:
        """取消订阅事件"""
        pass


class IServiceLocator(ABC):
    """服务定位器接口"""
    
    @abstractmethod
    def get_service(self, service_type: type) -> Any:
        """获取服务"""
        pass
    
    @abstractmethod
    def register_service(self, service_type: type, service: Any) -> None:
        """注册服务"""
        pass
    
    @abstractmethod
    def is_registered(self, service_type: type) -> bool:
        """检查服务是否已注册"""
        pass
