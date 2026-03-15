"""
Interface Adapter Layer
======================

提供接口适配能力，让基盘能够平滑吸收新标准。

设计模式：
- Adapter Pattern: 适配不同标准实现
- Factory Pattern: 统一创建入口
- Version Control: 多版本共存
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class StandardVersion(str, Enum):
    """标准版本"""
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"
    LATEST = "latest"


@dataclass
class AdapterMetadata:
    """适配器元数据"""
    name: str
    version: StandardVersion
    standard_name: str  # e.g., "agent", "tool", "skill"
    description: str = ""
    author: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    deprecated: bool = False
    deprecation_notice: str = ""


class IAdapter(ABC):
    """
    适配器基接口
    
    所有标准适配器必须实现此接口
    """
    
    @property
    @abstractmethod
    def metadata(self) -> AdapterMetadata:
        """适配器元数据"""
        pass
    
    @abstractmethod
    def adapt(self, source: Any) -> Any:
        """
        将源标准适配为目标标准
        
        Args:
            source: 源标准实现
            
        Returns:
            适配后的标准实现
        """
        pass
    
    @abstractmethod
    def validate(self, target: Any) -> bool:
        """
        验证适配后的实现是否符合标准
        
        Args:
            target: 适配后的实现
            
        Returns:
            是否符合标准
        """
        pass
    
    def is_compatible(self, source_version: StandardVersion) -> bool:
        """检查是否兼容源版本"""
        return True  # 默认兼容


class AdapterRegistry:
    """
    适配器注册中心
    
    管理所有标准适配器的注册和发现
    """
    
    def __init__(self):
        self._adapters: Dict[str, Dict[StandardVersion, Type[IAdapter]]] = {}
        self._instances: Dict[str, Dict[StandardVersion, IAdapter]] = {}
    
    def register(
        self, 
        standard_name: str, 
        version: StandardVersion,
        adapter_class: Type[IAdapter]
    ) -> None:
        """注册适配器"""
        if standard_name not in self._adapters:
            self._adapters[standard_name] = {}
        self._adapters[standard_name][version] = adapter_class
    
    def get_adapter(
        self, 
        standard_name: str, 
        version: StandardVersion = StandardVersion.LATEST
    ) -> Optional[IAdapter]:
        """获取适配器实例"""
        # 如果请求最新版本，找到最新的
        if version == StandardVersion.LATEST:
            version = self._get_latest_version(standard_name)
        
        # 尝试获取已创建的实例
        if standard_name in self._instances:
            if version in self._instances[standard_name]:
                return self._instances[standard_name][version]
        
        # 创建新实例
        if standard_name in self._adapters:
            if version in self._adapters[standard_name]:
                adapter_class = self._adapters[standard_name][version]
                adapter = adapter_class()
                
                # 缓存实例
                if standard_name not in self._instances:
                    self._instances[standard_name] = {}
                self._instances[standard_name][version] = adapter
                
                return adapter
        
        return None
    
    def _get_latest_version(self, standard_name: str) -> StandardVersion:
        """获取某标准的最新版本"""
        if standard_name not in self._adapters:
            return StandardVersion.V1
        
        versions = list(self._adapters[standard_name].keys())
        # 按版本排序 (V1 < V2 < V3)
        sorted_versions = sorted(versions, key=lambda v: v.value)
        return sorted_versions[-1] if sorted_versions else StandardVersion.V1
    
    def list_standards(self) -> List[str]:
        """列出所有已注册的标准"""
        return list(self._adapters.keys())
    
    def list_versions(self, standard_name: str) -> List[StandardVersion]:
        """列出某标准的所有版本"""
        if standard_name not in self._adapters:
            return []
        return list(self._adapters[standard_name].keys())
    
    def get_metadata(self, standard_name: str, version: StandardVersion) -> Optional[AdapterMetadata]:
        """获取适配器元数据"""
        adapter = self.get_adapter(standard_name, version)
        return adapter.metadata if adapter else None


# 全局注册中心实例
_registry: Optional[AdapterRegistry] = None


def get_adapter_registry() -> AdapterRegistry:
    """获取全局适配器注册中心"""
    global _registry
    if _registry is None:
        _registry = AdapterRegistry()
    return _registry


# ========== 示例：创建新标准的适配器 ==========

class V1AgentAdapter(IAdapter):
    """V1 Agent 标准适配器 (兼容旧标准)"""
    
    @property
    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            name="v1_agent_adapter",
            version=StandardVersion.V1,
            standard_name="agent",
            description="V1 Agent 标准适配器 - 兼容旧版接口"
        )
    
    def adapt(self, source: Any) -> Any:
        """将 V1 实现适配到当前标准"""
        # 这里是适配逻辑
        return source
    
    def validate(self, target: Any) -> bool:
        # 验证是否符合当前标准
        return hasattr(target, 'execute')


class V2AgentAdapter(IAdapter):
    """V2 Agent 标准适配器 (新标准)"""
    
    @property
    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            name="v2_agent_adapter",
            version=StandardVersion.V2,
            standard_name="agent",
            description="V2 Agent 标准适配器 - 新版接口"
        )
    
    def adapt(self, source: Any) -> Any:
        """将源实现适配到 V2 标准"""
        # V2 新增了更多字段
        return source
    
    def validate(self, target: Any) -> bool:
        # V2 标准验证
        return hasattr(target, 'execute') and hasattr(target, 'validate')


# 注册示例
def register_standard_adapters():
    """注册标准适配器"""
    registry = get_adapter_registry()
    registry.register("agent", StandardVersion.V1, V1AgentAdapter)
    registry.register("agent", StandardVersion.V2, V2AgentAdapter)
    # 可以继续注册其他标准...


# 使用示例
if __name__ == "__main__":
    # 注册适配器
    register_standard_adapters()
    
    # 获取适配器
    registry = get_adapter_registry()
    
    # 列出所有标准
    print("已注册标准:", registry.list_standards())
    
    # 列出某标准的版本
    print("Agent 版本:", [v.value for v in registry.list_versions("agent")])
    
    # 获取最新版本适配器
    adapter = registry.get_adapter("agent", StandardVersion.LATEST)
    if adapter:
        print(f"使用适配器: {adapter.metadata.name} ({adapter.metadata.version.value})")
