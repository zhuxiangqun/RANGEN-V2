"""
基础检索策略接口

定义检索策略的统一接口，支持策略模式的实现
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)


class BaseRetrievalStrategy(ABC):
    """检索策略基类 - 定义统一接口"""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化检索策略
        
        Args:
            name: 策略名称
            config: 策略配置参数
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.enabled = self.config.get('enabled', True)
        
    @abstractmethod
    async def execute(self, query: str, context: Dict[str, Any]) -> 'RetrievalResult':
        """
        执行检索策略
        
        Args:
            query: 查询字符串
            context: 上下文信息
            
        Returns:
            检索结果
        """
        pass
    
    def is_enabled(self) -> bool:
        """检查策略是否启用"""
        return self.enabled
    
    def enable(self) -> None:
        """启用策略"""
        self.enabled = True
        self.logger.info(f"{self.name} 策略已启用")
    
    def disable(self) -> None:
        """禁用策略"""
        self.enabled = False
        self.logger.info(f"{self.name} 策略已禁用")
    
    def get_config(self) -> Dict[str, Any]:
        """获取策略配置"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新策略配置"""
        self.config.update(new_config)
        self.enabled = self.config.get('enabled', self.enabled)
        # 子类可以重写此方法来更新特定属性
        self._update_instance_attributes(new_config)
        self.logger.info(f"{self.name} 配置已更新")
    
    def _update_instance_attributes(self, new_config: Dict[str, Any]) -> None:
        """更新实例特定属性 - 子类可重写"""
        pass  # 基类为空实现，子类可重写


class RetrievalResult:
    """检索结果包装器 - 标准化输出格式"""
    
    def __init__(
        self,
        documents: List[Dict[str, Any]],
        strategy_name: str,
        execution_time: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        self.documents = documents
        self.strategy_name = strategy_name
        self.execution_time = execution_time
        self.metadata = metadata or {}
        self.success = success
        self.error_message = error_message
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'documents': self.documents,
            'strategy_name': self.strategy_name,
            'execution_time': self.execution_time,
            'metadata': self.metadata,
            'success': self.success,
            'error_message': self.error_message,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_error(cls, strategy_name: str, error_message: str) -> 'RetrievalResult':
        """创建错误结果"""
        return cls(
            documents=[],
            strategy_name=strategy_name,
            success=False,
            error_message=error_message
        )


class StrategyRegistry:
    """策略注册器 - 管理所有可用的检索策略"""
    
    def __init__(self):
        self._strategies: Dict[str, BaseRetrievalStrategy] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def register(self, name: str, strategy: BaseRetrievalStrategy) -> None:
        """注册策略"""
        self._strategies[name] = strategy
        self.logger.info(f"已注册策略: {name}")
    
    def get(self, name: str) -> Optional[BaseRetrievalStrategy]:
        """获取策略"""
        return self._strategies.get(name)
    
    def list_strategies(self) -> List[str]:
        """列出所有已注册的策略"""
        return list(self._strategies.keys())
    
    def get_enabled_strategies(self) -> Dict[str, BaseRetrievalStrategy]:
        """获取所有启用的策略"""
        return {
            name: strategy 
            for name, strategy in self._strategies.items() 
            if strategy.is_enabled()
        }


# 全局策略注册器实例
strategy_registry = StrategyRegistry()
