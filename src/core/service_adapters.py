"""
服务适配器
将现有系统适配到新的接口体系，降低耦合度
"""

import logging
from typing import Dict, Any, List, Optional
from .interfaces import (
    IConfigurationService, ILoggingService, IKnowledgeRetrievalService,
    IReasoningService, IMLService, IRLService, IBusinessLogicService,
    IDataProcessingService, IMonitoringService, ISecurityService,
    IEventService, IServiceLocator, ProcessingResult
)


class ConfigurationServiceAdapter(IConfigurationService):
    """配置服务适配器"""
    
    def __init__(self):
        self._config_center = None
        self._try_get_config_center()
    
    def _try_get_config_center(self):
        """尝试获取配置中心"""
        try:
            from ..utils.unified_centers import get_unified_center
            self._config_center = get_unified_center('get_unified_config_center')
        except ImportError:
            self._config_center = None
    
    def get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """获取配置值"""
        if self._config_center:
            return self._config_center.get_config_value(section, key, default)
        return default
    
    def set_config_value(self, section: str, key: str, value: Any) -> bool:
        """设置配置值"""
        if self._config_center:
            return self._config_center.set_config_value(section, key, value)
        return False
    
    def has_config(self, section: str, key: str) -> bool:
        """检查配置是否存在"""
        if self._config_center:
            return self._config_center.has_config(section, key)
        return False


class LoggingServiceAdapter(ILoggingService):
    """日志服务适配器"""
    
    def __init__(self, logger_name: str = "RANGEN"):
        self.logger = logging.getLogger(logger_name)
    
    def info(self, message: str, **kwargs) -> None:
        """记录信息日志"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """记录错误日志"""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志"""
        self.logger.debug(message, **kwargs)


class KnowledgeRetrievalServiceAdapter(IKnowledgeRetrievalService):
    """知识检索服务适配器"""
    
    def __init__(self):
        self._knowledge_agent = None
        self._try_get_knowledge_agent()
    
    def _try_get_knowledge_agent(self):
        """尝试获取知识检索代理"""
        try:
            from ..services.knowledge_retrieval_service import KnowledgeRetrievalService
            self._knowledge_agent = KnowledgeRetrievalService()
        except ImportError:
            self._knowledge_agent = None
    
    def search(self, query: str, context: Dict[str, Any]) -> ProcessingResult:
        """搜索知识"""
        try:
            if self._knowledge_agent:
                result = self._knowledge_agent.search(query, context)
                return ProcessingResult(
                    success=True,
                    data=result,
                    metadata={'query': query, 'context': context}
                )
            else:
                return ProcessingResult(
                    success=False,
                    data=None,
                    error="Knowledge retrieval service not available"
                )
        except Exception as e:
            return ProcessingResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def retrieve(self, document_id: str) -> ProcessingResult:
        """检索文档"""
        try:
            if self._knowledge_agent:
                result = self._knowledge_agent.retrieve_document(document_id)
                return ProcessingResult(
                    success=True,
                    data=result,
                    metadata={'document_id': document_id}
                )
            else:
                return ProcessingResult(
                    success=False,
                    data=None,
                    error="Knowledge retrieval service not available"
                )
        except Exception as e:
            return ProcessingResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def index_document(self, document: Dict[str, Any]) -> ProcessingResult:
        """索引文档"""
        try:
            if self._knowledge_agent:
                result = self._knowledge_agent.index_document(document)
                return ProcessingResult(
                    success=True,
                    data=result,
                    metadata={'document': document}
                )
            else:
                return ProcessingResult(
                    success=False,
                    data=None,
                    error="Knowledge retrieval service not available"
                )
        except Exception as e:
            return ProcessingResult(
                success=False,
                data=None,
                error=str(e)
            )


class ReasoningServiceAdapter(IReasoningService):
    """推理服务适配器"""
    
    def __init__(self):
        self._reasoning_agent = None
        self._try_get_reasoning_agent()
    
    def _try_get_reasoning_agent(self):
        """尝试获取推理代理"""
        try:
            from ..services.reasoning_service import ReasoningService
            self._reasoning_agent = ReasoningService()
        except ImportError:
            self._reasoning_agent = None
    
    def reason(self, context: Dict[str, Any], strategy: str) -> ProcessingResult:
        """执行推理"""
        try:
            if self._reasoning_agent:
                result = self._reasoning_agent.reason(context, strategy)
                return ProcessingResult(
                    success=True,
                    data=result,
                    metadata={'strategy': strategy, 'context': context}
                )
            else:
                return ProcessingResult(
                    success=False,
                    data=None,
                    error="Reasoning service not available"
                )
        except Exception as e:
            return ProcessingResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def get_available_strategies(self) -> List[str]:
        """获取可用的推理策略"""
        if self._reasoning_agent:
            return ['deductive', 'inductive', 'abductive', 'causal', 'analogical']
        return []


class MLServiceAdapter(IMLService):
    """机器学习服务适配器"""
    
    def __init__(self):
        self._ml_integrator = None
        self._try_get_ml_integrator()
    
    def _try_get_ml_integrator(self):
        """尝试获取ML集成器"""
        try:
            from ..ai.ai_algorithm_integrator import AIAlgorithmIntegrator
            self._ml_integrator = AIAlgorithmIntegrator()
        except ImportError:
            self._ml_integrator = None
    
    def train(self, data: Any, model_type: str) -> ProcessingResult:
        """训练模型"""
        try:
            if self._ml_integrator:
                result = self._ml_integrator.train_model(data, model_type)
                return ProcessingResult(
                    success=True,
                    data=result,
                    metadata={'model_type': model_type}
                )
            else:
                return ProcessingResult(
                    success=False,
                    data=None,
                    error="ML service not available"
                )
        except Exception as e:
            return ProcessingResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def predict(self, data: Any, model_id: str) -> ProcessingResult:
        """预测"""
        try:
            if self._ml_integrator:
                result = self._ml_integrator.predict(data, model_id)
                return ProcessingResult(
                    success=True,
                    data=result,
                    metadata={'model_id': model_id}
                )
            else:
                return ProcessingResult(
                    success=False,
                    data=None,
                    error="ML service not available"
                )
        except Exception as e:
            return ProcessingResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def evaluate(self, data: Any, model_id: str) -> ProcessingResult:
        """评估模型"""
        try:
            if self._ml_integrator:
                result = self._ml_integrator.evaluate_model(data, model_id)
                return ProcessingResult(
                    success=True,
                    data=result,
                    metadata={'model_id': model_id}
                )
            else:
                return ProcessingResult(
                    success=False,
                    data=None,
                    error="ML service not available"
                )
        except Exception as e:
            return ProcessingResult(
                success=False,
                data=None,
                error=str(e)
            )


class ServiceLocatorAdapter(IServiceLocator):
    """服务定位器适配器"""
    
    def __init__(self):
        self._services: Dict[type, Any] = {}
        self._register_default_services()
    
    def _register_default_services(self):
        """注册默认服务"""
        self.register_service(IConfigurationService, ConfigurationServiceAdapter())
        self.register_service(ILoggingService, LoggingServiceAdapter())
        self.register_service(IKnowledgeRetrievalService, KnowledgeRetrievalServiceAdapter())
        self.register_service(IReasoningService, ReasoningServiceAdapter())
        self.register_service(IMLService, MLServiceAdapter())
    
    def get_service(self, service_type: type) -> Any:
        """获取服务"""
        return self._services.get(service_type)
    
    def register_service(self, service_type: type, service: Any) -> None:
        """注册服务"""
        self._services[service_type] = service
    
    def is_registered(self, service_type: type) -> bool:
        """检查服务是否已注册"""
        return service_type in self._services


# 全局服务定位器
_service_locator: Optional[ServiceLocatorAdapter] = None


def get_service_locator() -> ServiceLocatorAdapter:
    """获取全局服务定位器"""
    global _service_locator
    if _service_locator is None:
        _service_locator = ServiceLocatorAdapter()
    return _service_locator


def get_service(service_type: type) -> Any:
    """获取服务"""
    return get_service_locator().get_service(service_type)
