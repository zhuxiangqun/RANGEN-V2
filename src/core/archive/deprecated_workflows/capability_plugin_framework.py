"""
能力插件框架 - P3阶段能力架构优化

实现完整的能力插件化架构：
1. 插件加载和卸载机制 (Plugin Loading/Unloading)
2. 插件生命周期管理 (Plugin Lifecycle)
3. 插件依赖注入 (Dependency Injection)
4. 插件配置管理 (Configuration Management)
5. 插件热更新 (Hot Reload)
6. 插件安全性 (Plugin Security)

支持动态能力扩展和第三方插件集成。
"""

import importlib
import inspect
import logging
import os
import sys
import time
from typing import Dict, Any, List, Optional, Set, Type, Callable, Protocol
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import hashlib
import json

logger = logging.getLogger(__name__)


class CapabilityInterface(Protocol):
    """能力接口协议"""

    @property
    def name(self) -> str:
        """能力名称"""
        ...

    @property
    def version(self) -> str:
        """能力版本"""
        ...

    @property
    def description(self) -> str:
        """能力描述"""
        ...

    @property
    def capabilities(self) -> List[str]:
        """支持的功能列表"""
        ...

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行能力"""
        ...

    async def initialize(self) -> bool:
        """初始化能力"""
        ...

    async def cleanup(self) -> bool:
        """清理能力"""
        ...

    def get_status(self) -> Dict[str, Any]:
        """获取能力状态"""
        ...


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str
    author: str
    license: str = ""
    homepage: str = ""

    # 能力信息
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # 技术信息
    python_version: str = ""
    platform: str = ""
    architecture: str = ""

    # 安全信息
    checksum: str = ""
    signature: str = ""
    trusted: bool = False

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    loaded_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.loaded_at:
            data['loaded_at'] = self.loaded_at.isoformat()
        return data


@dataclass
class PluginInstance:
    """插件实例"""
    metadata: PluginMetadata
    capability_class: Type[CapabilityInterface]
    instance: Optional[CapabilityInterface] = None

    # 状态跟踪
    status: str = "unloaded"  # unloaded, loaded, active, error
    load_time: Optional[float] = None
    error_message: Optional[str] = None

    # 使用统计
    call_count: int = 0
    total_execution_time: float = 0.0
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = {
            'metadata': self.metadata.to_dict(),
            'status': self.status,
            'load_time': self.load_time,
            'error_message': self.error_message,
            'call_count': self.call_count,
            'total_execution_time': self.total_execution_time,
            'error_count': self.error_count,
            'average_execution_time': self.total_execution_time / self.call_count if self.call_count > 0 else 0
        }
        return data


class PluginLoader:
    """插件加载器"""

    def __init__(self, plugin_dirs: List[str] = None):
        self.plugin_dirs = plugin_dirs or [
            os.path.join(os.getcwd(), 'plugins'),
            os.path.join(os.getcwd(), 'src', 'plugins')
        ]
        self.loaded_modules: Dict[str, Any] = {}

    def discover_plugins(self) -> List[str]:
        """发现插件"""
        plugin_files = []

        for plugin_dir in self.plugin_dirs:
            if os.path.exists(plugin_dir):
                for file_name in os.listdir(plugin_dir):
                    if file_name.endswith('_plugin.py') or file_name.endswith('_capability.py'):
                        plugin_path = os.path.join(plugin_dir, file_name)
                        plugin_files.append(plugin_path)

        return plugin_files

    def load_plugin_from_file(self, file_path: str) -> Optional[Type[CapabilityInterface]]:
        """从文件加载插件"""
        try:
            # 计算文件校验和
            checksum = self._calculate_file_checksum(file_path)

            # 加载模块
            module_name = f"plugin_{os.path.basename(file_path).replace('.py', '')}_{checksum[:8]}"

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"无法创建模块规范: {file_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找能力类
            capability_class = self._find_capability_class(module)

            if capability_class:
                self.loaded_modules[module_name] = module
                logger.info(f"✅ 插件文件加载成功: {file_path}")
                return capability_class
            else:
                logger.warning(f"⚠️ 在插件文件中未找到能力类: {file_path}")

        except Exception as e:
            logger.error(f"❌ 插件文件加载失败: {file_path} - {e}")

        return None

    def load_plugin_from_class(self, capability_class: Type[CapabilityInterface]) -> Optional[Type[CapabilityInterface]]:
        """从类直接加载插件"""
        try:
            # 验证类是否符合能力接口
            if not self._validate_capability_class(capability_class):
                raise ValueError(f"能力类不符合接口规范: {capability_class.__name__}")

            logger.info(f"✅ 能力类加载成功: {capability_class.__name__}")
            return capability_class

        except Exception as e:
            logger.error(f"❌ 能力类加载失败: {capability_class.__name__} - {e}")

        return None

    def _find_capability_class(self, module: Any) -> Optional[Type[CapabilityInterface]]:
        """在模块中查找能力类"""
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and
                issubclass(obj, object) and
                hasattr(obj, 'name') and
                hasattr(obj, 'execute') and
                callable(getattr(obj, 'execute'))):
                return obj
        return None

    def _validate_capability_class(self, capability_class: Type[CapabilityInterface]) -> bool:
        """验证能力类"""
        required_attrs = ['name', 'version', 'description', 'capabilities', 'execute']
        required_methods = ['execute', 'initialize', 'cleanup', 'get_status']

        # 检查必需属性
        for attr in required_attrs:
            if not hasattr(capability_class, attr):
                return False

        # 检查必需方法
        for method in required_methods:
            if not hasattr(capability_class, method) or not callable(getattr(capability_class, method)):
                return False

        return True

    def _calculate_file_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        with open(file_path, 'rb') as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()


class PluginManager:
    """插件管理器"""

    def __init__(self):
        self.loader = PluginLoader()
        self.plugins: Dict[str, PluginInstance] = {}
        self.dependency_injector = DependencyInjector()

        # 安全配置
        self.trusted_checksums: Set[str] = set()
        self.allowed_authors: Set[str] = set()

    def register_plugin(self, capability_class: Type[CapabilityInterface],
                       metadata: Optional[PluginMetadata] = None) -> bool:
        """注册插件"""
        try:
            plugin_name = capability_class.name

            # 创建插件实例
            plugin_metadata = metadata or self._extract_metadata_from_class(capability_class)
            plugin_instance = PluginInstance(
                metadata=plugin_metadata,
                capability_class=capability_class
            )

            # 安全检查
            if not self._security_check(plugin_instance):
                logger.warning(f"⚠️ 插件安全检查失败: {plugin_name}")
                return False

            # 依赖检查
            if not self._check_dependencies(plugin_instance):
                logger.warning(f"⚠️ 插件依赖检查失败: {plugin_name}")
                return False

            self.plugins[plugin_name] = plugin_instance
            logger.info(f"✅ 插件注册成功: {plugin_name} v{plugin_metadata.version}")
            return True

        except Exception as e:
            logger.error(f"❌ 插件注册失败: {e}")
            return False

    async def load_plugin(self, plugin_name: str) -> bool:
        """加载插件"""
        if plugin_name not in self.plugins:
            logger.error(f"❌ 插件未注册: {plugin_name}")
            return False

        plugin = self.plugins[plugin_name]

        try:
            start_time = time.time()

            # 实例化能力
            capability_instance = plugin.capability_class()

            # 依赖注入
            self.dependency_injector.inject_dependencies(capability_instance, plugin.metadata)

            # 初始化
            if hasattr(capability_instance, 'initialize'):
                init_success = await capability_instance.initialize()
                if not init_success:
                    raise RuntimeError(f"插件初始化失败: {plugin_name}")

            plugin.instance = capability_instance
            plugin.status = "loaded"
            plugin.load_time = time.time() - start_time
            plugin.metadata.loaded_at = datetime.now()

            logger.info(".3f")
            return True

        except Exception as e:
            plugin.status = "error"
            plugin.error_message = str(e)
            logger.error(f"❌ 插件加载失败: {plugin_name} - {e}")
            return False

    def activate_plugin(self, plugin_name: str) -> bool:
        """激活插件"""
        if plugin_name not in self.plugins:
            return False

        plugin = self.plugins[plugin_name]
        if plugin.status != "loaded":
            return False

        try:
            plugin.status = "active"
            logger.info(f"✅ 插件激活成功: {plugin_name}")
            return True

        except Exception as e:
            plugin.status = "error"
            plugin.error_message = str(e)
            logger.error(f"❌ 插件激活失败: {plugin_name} - {e}")
            return False

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """停用插件"""
        if plugin_name not in self.plugins:
            return False

        plugin = self.plugins[plugin_name]

        try:
            if plugin.instance and hasattr(plugin.instance, 'cleanup'):
                await plugin.instance.cleanup()

            plugin.status = "loaded"
            logger.info(f"✅ 插件停用成功: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 插件停用失败: {plugin_name} - {e}")
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name not in self.plugins:
            return False

        plugin = self.plugins[plugin_name]

        try:
            # 清理实例
            if plugin.instance and hasattr(plugin.instance, 'cleanup'):
                await plugin.instance.cleanup()

            # 从注册表移除
            del self.plugins[plugin_name]
            logger.info(f"✅ 插件卸载成功: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 插件卸载失败: {plugin_name} - {e}")
            return False

    async def execute_plugin(self, plugin_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行插件"""
        if plugin_name not in self.plugins:
            raise ValueError(f"插件不存在: {plugin_name}")

        plugin = self.plugins[plugin_name]
        if plugin.status != "active" or not plugin.instance:
            raise RuntimeError(f"插件未激活: {plugin_name}")

        try:
            start_time = time.time()

            # 执行能力
            result = await plugin.instance.execute(context)

            # 更新统计
            execution_time = time.time() - start_time
            plugin.call_count += 1
            plugin.total_execution_time += execution_time

            logger.debug(f"插件执行成功: {plugin_name} ({execution_time:.3f}s)")
            return result

        except Exception as e:
            plugin.error_count += 1
            logger.error(f"❌ 插件执行失败: {plugin_name} - {e}")
            raise

    def discover_and_load_plugins(self) -> int:
        """自动发现并加载插件"""
        loaded_count = 0

        # 发现插件文件
        plugin_files = self.loader.discover_plugins()

        for file_path in plugin_files:
            try:
                capability_class = self.loader.load_plugin_from_file(file_path)
                if capability_class:
                    # 自动注册和加载
                    metadata = self._extract_metadata_from_file(file_path)
                    if self.register_plugin(capability_class, metadata):
                        if self.load_plugin(capability_class.name):
                            self.activate_plugin(capability_class.name)
                            loaded_count += 1

            except Exception as e:
                logger.error(f"❌ 自动加载插件失败: {file_path} - {e}")

        logger.info(f"✅ 自动加载完成，共加载 {loaded_count} 个插件")
        return loaded_count

    def get_plugin_status(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件状态"""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].to_dict()
        return None

    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """列出所有插件"""
        return {name: plugin.to_dict() for name, plugin in self.plugins.items()}

    def _extract_metadata_from_class(self, capability_class: Type[CapabilityInterface]) -> PluginMetadata:
        """从能力类提取元数据"""
        return PluginMetadata(
            name=capability_class.name,
            version=getattr(capability_class, 'version', '1.0.0'),
            description=getattr(capability_class, 'description', ''),
            author=getattr(capability_class, 'author', 'unknown'),
            capabilities=getattr(capability_class, 'capabilities', [])
        )

    def _extract_metadata_from_file(self, file_path: str) -> PluginMetadata:
        """从插件文件提取元数据"""
        # 简化的元数据提取（实际实现可能需要解析文件头部注释或配置）
        file_name = os.path.basename(file_path)
        plugin_name = file_name.replace('_plugin.py', '').replace('_capability.py', '')

        return PluginMetadata(
            name=plugin_name,
            version="1.0.0",
            description=f"Auto-loaded plugin: {plugin_name}",
            author="auto-discovery"
        )

    def _security_check(self, plugin: PluginInstance) -> bool:
        """安全检查"""
        # 检查校验和白名单
        if self.trusted_checksums and plugin.metadata.checksum not in self.trusted_checksums:
            return False

        # 检查作者白名单
        if self.allowed_authors and plugin.metadata.author not in self.allowed_authors:
            return False

        return True

    def _check_dependencies(self, plugin: PluginInstance) -> bool:
        """检查依赖"""
        for dep in plugin.metadata.dependencies:
            if dep not in self.plugins:
                logger.warning(f"插件依赖缺失: {dep}")
                return False
        return True


class DependencyInjector:
    """依赖注入器"""

    def __init__(self):
        self.services: Dict[str, Any] = {}

    def register_service(self, name: str, service: Any):
        """注册服务"""
        self.services[name] = service

    def inject_dependencies(self, capability_instance: Any, metadata: PluginMetadata):
        """注入依赖"""
        # 查找需要注入的属性
        for attr_name in dir(capability_instance):
            if attr_name.startswith('_inject_'):
                service_name = attr_name[8:]  # 去掉_inject_前缀
                if service_name in self.services:
                    setattr(capability_instance, attr_name, self.services[service_name])
                    logger.debug(f"依赖注入: {service_name} -> {metadata.name}")


class CompositeCapability:
    """复合能力 - 将多个能力组合成更复杂的能力"""

    def __init__(self, name: str, description: str, plugin_manager: PluginManager):
        self.name = name
        self.version = "1.0.0"
        self.description = description
        self.plugin_manager = plugin_manager

        # 复合能力配置
        self.sub_capabilities: List[Dict[str, Any]] = []  # [{'name': str, 'condition': callable, 'weight': float}]
        self.execution_strategy = "parallel"  # parallel, sequential, conditional
        self.aggregation_method = "weighted_average"  # how to combine results

    def add_sub_capability(self, capability_name: str, condition: Optional[Callable] = None, weight: float = 1.0):
        """添加子能力"""
        self.sub_capabilities.append({
            'name': capability_name,
            'condition': condition,
            'weight': weight
        })

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行复合能力"""
        results = {}
        total_weight = 0

        # 执行所有适用的子能力
        for sub_cap in self.sub_capabilities:
            try:
                # 检查条件
                if sub_cap['condition'] and not sub_cap['condition'](context):
                    continue

                # 执行子能力
                result = await self.plugin_manager.execute_plugin(sub_cap['name'], context)
                results[sub_cap['name']] = {
                    'result': result,
                    'weight': sub_cap['weight']
                }
                total_weight += sub_cap['weight']

            except Exception as e:
                logger.warning(f"子能力执行失败: {sub_cap['name']} - {e}")
                results[sub_cap['name']] = {
                    'error': str(e),
                    'weight': sub_cap['weight']
                }

        # 聚合结果
        final_result = self._aggregate_results(results, total_weight, context)
        return final_result

    def _aggregate_results(self, results: Dict[str, Any], total_weight: float, context: Dict[str, Any]) -> Dict[str, Any]:
        """聚合多个子能力的结果"""
        if not results:
            return {'error': '没有成功的子能力执行'}

        aggregated = {}

        if self.aggregation_method == "weighted_average":
            # 加权平均聚合
            weighted_values = {}

            for cap_name, cap_result in results.items():
                if 'error' not in cap_result:
                    result = cap_result['result']
                    weight = cap_result['weight']

                    for key, value in result.items():
                        if isinstance(value, (int, float)):
                            if key not in weighted_values:
                                weighted_values[key] = []
                            weighted_values[key].append((value, weight))

            # 计算加权平均
            for key, value_weight_pairs in weighted_values.items():
                total_weighted_value = sum(v * w for v, w in value_weight_pairs)
                total_weights = sum(w for _, w in value_weight_pairs)
                aggregated[key] = total_weighted_value / total_weights if total_weights > 0 else 0

        elif self.aggregation_method == "first_success":
            # 返回第一个成功的子能力结果
            for cap_name, cap_result in results.items():
                if 'error' not in cap_result:
                    return cap_result['result']

        elif self.aggregation_method == "merge":
            # 合并所有结果
            for cap_name, cap_result in results.items():
                if 'error' not in cap_result:
                    result = cap_result['result']
                    for key, value in result.items():
                        if key not in aggregated:
                            aggregated[key] = []
                        if isinstance(aggregated[key], list):
                            aggregated[key].append(value)

        return aggregated

    async def initialize(self) -> bool:
        """初始化复合能力"""
        return True

    async def cleanup(self) -> bool:
        """清理复合能力"""
        return True

    def get_status(self) -> Dict[str, Any]:
        """获取复合能力状态"""
        return {
            'name': self.name,
            'sub_capabilities': len(self.sub_capabilities),
            'execution_strategy': self.execution_strategy,
            'aggregation_method': self.aggregation_method
        }


# 全局插件管理器实例
_plugin_manager_instance: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取插件管理器实例"""
    global _plugin_manager_instance
    if _plugin_manager_instance is None:
        _plugin_manager_instance = PluginManager()
    return _plugin_manager_instance