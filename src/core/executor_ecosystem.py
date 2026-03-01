"""
执行器生态系统

构建开放的执行器生态，支持第三方集成和开发者工具
"""

import asyncio
import logging
import importlib
import inspect
from typing import Dict, List, Any, Optional, Type, Callable, Protocol
from dataclasses import dataclass, field
from pathlib import Path
import json
import yaml


logger = logging.getLogger(__name__)


class ExecutorPlugin(Protocol):
    """执行器插件协议"""

    @property
    def name(self) -> str:
        """插件名称"""
        ...

    @property
    def version(self) -> str:
        """插件版本"""
        ...

    @property
    def supported_task_types(self) -> List[str]:
        """支持的任务类型"""
        ...

    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化插件"""
        ...

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        ...

    def get_capabilities(self) -> Dict[str, Any]:
        """获取插件能力"""
        ...


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str
    author: str
    license: str
    homepage: str = ""
    repository: str = ""
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class PluginInfo:
    """插件信息"""
    metadata: PluginMetadata
    capabilities: Dict[str, Any]
    status: str = "inactive"  # inactive, active, error
    load_time: Optional[float] = None
    error_message: Optional[str] = None


class PluginLoader:
    """插件加载器"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.plugin_dirs = [
            Path("plugins"),
            Path("src/plugins"),
            Path("extensions")
        ]

    def discover_plugins(self) -> List[Path]:
        """发现插件"""
        plugin_files = []

        for plugin_dir in self.plugin_dirs:
            if plugin_dir.exists():
                # 查找Python文件
                for py_file in plugin_dir.rglob("*.py"):
                    if not py_file.name.startswith("__"):
                        plugin_files.append(py_file)

                # 查找插件配置文件
                for config_file in plugin_dir.rglob("plugin.yaml"):
                    plugin_files.append(config_file)

        self.logger.info(f"🔍 发现 {len(plugin_files)} 个潜在插件文件")
        return plugin_files

    def load_plugin_from_file(self, plugin_file: Path) -> Optional[Type[ExecutorPlugin]]:
        """从文件加载插件"""
        try:
            if plugin_file.suffix == ".py":
                return self._load_python_plugin(plugin_file)
            elif plugin_file.suffix in [".yaml", ".yml"]:
                return self._load_config_plugin(plugin_file)
            else:
                self.logger.warning(f"⚠️ 不支持的插件文件类型: {plugin_file}")
                return None

        except Exception as e:
            self.logger.error(f"❌ 加载插件失败 {plugin_file}: {e}")
            return None

    def _load_python_plugin(self, plugin_file: Path) -> Optional[Type[ExecutorPlugin]]:
        """加载Python插件"""
        try:
            # 构建模块路径
            relative_path = plugin_file.relative_to(Path.cwd())
            module_path = str(relative_path).replace("/", ".").replace("\\", ".").replace(".py", "")

            # 导入模块
            module = importlib.import_module(module_path)

            # 查找插件类
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, ExecutorPlugin) and
                    obj != ExecutorPlugin):
                    self.logger.info(f"✅ 加载Python插件: {name}")
                    return obj

            self.logger.warning(f"⚠️ 在 {plugin_file} 中未找到有效的插件类")
            return None

        except ImportError as e:
            self.logger.error(f"❌ 导入Python插件失败 {plugin_file}: {e}")
            return None

    def _load_config_plugin(self, config_file: Path) -> Optional[Type[ExecutorPlugin]]:
        """加载配置驱动的插件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 创建配置插件类
            class ConfigDrivenPlugin(ExecutorPlugin):
                def __init__(self):
                    self._config = config
                    self._name = config.get("name", "ConfigPlugin")
                    self._version = config.get("version", "1.0.0")

                @property
                def name(self) -> str:
                    return self._name

                @property
                def version(self) -> str:
                    return self._version

                @property
                def supported_task_types(self) -> List[str]:
                    return self._config.get("supported_task_types", [])

                def initialize(self, config: Dict[str, Any]) -> bool:
                    return True

                async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
                    # 配置驱动的简单执行逻辑
                    task_type = task_input.get("task_type", "")
                    return {
                        "result": f"Config plugin executed {task_type}",
                        "quality_score": 0.8
                    }

                def get_capabilities(self) -> Dict[str, Any]:
                    return self._config.get("capabilities", {})

            self.logger.info(f"✅ 加载配置插件: {config.get('name', 'Unknown')}")
            return ConfigDrivenPlugin

        except Exception as e:
            self.logger.error(f"❌ 加载配置插件失败 {config_file}: {e}")
            return None


class PluginManager:
    """插件管理器"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.loader = PluginLoader()
        self.plugins: Dict[str, ExecutorPlugin] = {}
        self.plugin_info: Dict[str, PluginInfo] = {}
        self.active_plugins: Set[str] = set()

    async def initialize(self):
        """初始化插件管理器"""
        self.logger.info("🚀 初始化插件管理器")

        # 自动发现和加载插件
        await self.discover_and_load_plugins()

        # 初始化内置插件
        await self.initialize_builtin_plugins()

        self.logger.info(f"✅ 插件管理器初始化完成，加载了 {len(self.plugins)} 个插件")

    async def discover_and_load_plugins(self):
        """发现和加载插件"""
        plugin_files = self.loader.discover_plugins()

        for plugin_file in plugin_files:
            plugin_class = self.loader.load_plugin_from_file(plugin_file)
            if plugin_class:
                try:
                    # 实例化插件
                    plugin_instance = plugin_class()

                    # 注册插件
                    await self.register_plugin(plugin_instance)

                except Exception as e:
                    self.logger.error(f"❌ 实例化插件失败 {plugin_file}: {e}")

    async def initialize_builtin_plugins(self):
        """初始化内置插件"""
        # 这里可以初始化一些核心的内置插件
        pass

    async def register_plugin(self, plugin: ExecutorPlugin, config: Optional[Dict[str, Any]] = None):
        """注册插件"""
        plugin_name = plugin.name

        if plugin_name in self.plugins:
            self.logger.warning(f"⚠️ 插件 {plugin_name} 已存在，将被替换")

        try:
            # 初始化插件
            init_config = config or {}
            if plugin.initialize(init_config):
                self.plugins[plugin_name] = plugin

                # 创建插件信息
                metadata = PluginMetadata(
                    name=plugin_name,
                    version=getattr(plugin, 'version', '1.0.0'),
                    description=getattr(plugin, 'description', ''),
                    author=getattr(plugin, 'author', 'Unknown'),
                    license=getattr(plugin, 'license', 'MIT')
                )

                plugin_info = PluginInfo(
                    metadata=metadata,
                    capabilities=plugin.get_capabilities(),
                    status="active",
                    load_time=time.time()
                )

                self.plugin_info[plugin_name] = plugin_info
                self.active_plugins.add(plugin_name)

                self.logger.info(f"✅ 注册插件: {plugin_name} v{plugin.version}")
            else:
                self.logger.error(f"❌ 插件初始化失败: {plugin_name}")

        except Exception as e:
            self.logger.error(f"❌ 注册插件失败 {plugin_name}: {e}")

            # 记录错误信息
            plugin_info = PluginInfo(
                metadata=PluginMetadata(name=plugin_name, version="unknown",
                                      description="", author="", license=""),
                capabilities={},
                status="error",
                error_message=str(e)
            )
            self.plugin_info[plugin_name] = plugin_info

    async def unregister_plugin(self, plugin_name: str) -> bool:
        """注销插件"""
        if plugin_name not in self.plugins:
            return False

        try:
            # 清理插件资源
            plugin = self.plugins[plugin_name]
            if hasattr(plugin, 'cleanup'):
                await plugin.cleanup()

            # 移除插件
            del self.plugins[plugin_name]
            self.active_plugins.discard(plugin_name)

            if plugin_name in self.plugin_info:
                self.plugin_info[plugin_name].status = "inactive"

            self.logger.info(f"✅ 注销插件: {plugin_name}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 注销插件失败 {plugin_name}: {e}")
            return False

    def get_plugin(self, plugin_name: str) -> Optional[ExecutorPlugin]:
        """获取插件"""
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件"""
        result = []

        for name, info in self.plugin_info.items():
            plugin_data = {
                "name": name,
                "version": info.metadata.version,
                "description": info.metadata.description,
                "author": info.metadata.author,
                "status": info.status,
                "capabilities": info.capabilities,
                "supported_task_types": self.plugins.get(name).supported_task_types if name in self.plugins else [],
                "tags": info.metadata.tags,
                "load_time": info.load_time,
                "error_message": info.error_message
            }
            result.append(plugin_data)

        return result

    def get_plugins_by_task_type(self, task_type: str) -> List[str]:
        """获取支持特定任务类型的插件"""
        matching_plugins = []

        for name, plugin in self.plugins.items():
            if task_type in plugin.supported_task_types:
                matching_plugins.append(name)

        return matching_plugins

    async def execute_with_plugin(
        self,
        plugin_name: str,
        task_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用指定插件执行任务"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"插件 '{plugin_name}' 不存在")

        try:
            result = await plugin.execute(task_input)
            return result
        except Exception as e:
            self.logger.error(f"❌ 插件执行失败 {plugin_name}: {e}")
            raise


class IntegrationHub:
    """集成中心"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.integrations: Dict[str, Dict[str, Any]] = {}

    def register_integration(
        self,
        name: str,
        integration_type: str,
        config: Dict[str, Any],
        connector: Callable
    ):
        """注册集成"""
        self.integrations[name] = {
            "type": integration_type,
            "config": config,
            "connector": connector,
            "status": "inactive"
        }

        self.logger.info(f"✅ 注册集成: {name} ({integration_type})")

    async def activate_integration(self, name: str) -> bool:
        """激活集成"""
        if name not in self.integrations:
            return False

        integration = self.integrations[name]

        try:
            # 测试连接
            connector = integration["connector"]
            test_result = await connector.test_connection(integration["config"])

            if test_result:
                integration["status"] = "active"
                self.logger.info(f"✅ 激活集成: {name}")
                return True
            else:
                self.logger.error(f"❌ 集成连接测试失败: {name}")
                return False

        except Exception as e:
            self.logger.error(f"❌ 激活集成失败 {name}: {e}")
            return False

    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态"""
        return {
            name: {
                "type": info["type"],
                "status": info["status"],
                "config": {k: "***" if "key" in k.lower() else v
                          for k, v in info["config"].items()}
            }
            for name, info in self.integrations.items()
        }


class DeveloperToolkit:
    """开发者工具包"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def create_plugin_template(self, plugin_name: str, task_types: List[str]) -> str:
        """创建插件模板"""
        template = f'''"""
{plugin_name} 执行器插件

这是一个示例插件模板
"""

from typing import Dict, List, Any
from src.core.executor_ecosystem import ExecutorPlugin


class {plugin_name}Plugin(ExecutorPlugin):
    """{plugin_name} 执行器插件"""

    def __init__(self):
        self._name = "{plugin_name}"
        self._version = "1.0.0"
        self._initialized = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def description(self) -> str:
        return "{plugin_name} 执行器插件描述"

    @property
    def author(self) -> str:
        return "开发者名称"

    @property
    def supported_task_types(self) -> List[str]:
        return {task_types!r}

    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化插件"""
        try:
            # 初始化逻辑
            self._initialized = True
            self.logger.info(f"✅ {self._name} 插件初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"❌ {self._name} 插件初始化失败: {{e}}")
            return False

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        try:
            task_type = task_input.get("task_type", "")
            task_id = task_input.get("task_id", "")

            # 执行逻辑
            result = {{
                "task_type": task_type,
                "task_id": task_id,
                "result": f"{plugin_name} 执行结果",
                "quality_score": 0.8,
                "execution_time": 0.1
            }}

            return result

        except Exception as e:
            return {{
                "error": str(e),
                "quality_score": 0.0
            }}

    def get_capabilities(self) -> Dict[str, Any]:
        """获取插件能力"""
        return {{
            "async_execution": True,
            "batch_processing": False,
            "custom_config": True,
            "health_checks": True
        }}

    async def health_check(self) -> bool:
        """健康检查"""
        return self._initialized

    async def cleanup(self):
        """清理资源"""
        self._initialized = False
        self.logger.info(f"🧹 {self._name} 插件已清理")
'''
        return template

    def validate_plugin(self, plugin_code: str) -> Dict[str, Any]:
        """验证插件代码"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }

        # 检查必要的类和方法
        required_elements = [
            "class.*Plugin(ExecutorPlugin)",
            "def name",
            "def version",
            "def supported_task_types",
            "def initialize",
            "async def execute",
            "def get_capabilities"
        ]

        for element in required_elements:
            if element not in plugin_code:
                validation_result["errors"].append(f"缺少必要元素: {element}")

        # 检查导入
        if "from src.core.executor_ecosystem import ExecutorPlugin" not in plugin_code:
            validation_result["warnings"].append("建议导入 ExecutorPlugin")

        # 检查异步方法
        if "async def execute" not in plugin_code:
            validation_result["suggestions"].append("execute 方法应该是异步的")

        if validation_result["errors"]:
            validation_result["valid"] = False

        return validation_result

    def generate_plugin_documentation(self, plugin: ExecutorPlugin) -> str:
        """生成插件文档"""
        doc = f"""# {plugin.name} 插件文档

## 概述

**名称**: {plugin.name}
**版本**: {plugin.version}
**描述**: {getattr(plugin, 'description', '无描述')}

## 支持的任务类型

{chr(10).join(f"- {task_type}" for task_type in plugin.supported_task_types)}

## 能力特性

```json
{json.dumps(plugin.get_capabilities(), indent=2)}
```

## 使用示例

```python
from {plugin.__class__.__module__} import {plugin.__class__.__name__}

# 初始化插件
plugin = {plugin.__class__.__name__}()
plugin.initialize({{"param": "value"}})

# 执行任务
result = await plugin.execute({{
    "task_type": "{plugin.supported_task_types[0] if plugin.supported_task_types else 'example'}",
    "task_id": "example_task",
    "data": "example_data"
}})
```

## 配置选项

插件支持以下配置选项：
- 具体配置项请参考插件源码

## 故障排除

### 常见问题
1. 初始化失败：检查配置参数
2. 执行失败：检查输入数据格式
3. 性能问题：调整并发设置

### 日志位置
插件日志输出到标准日志系统，可通过配置调整日志级别。
"""
        return doc


class ExecutorEcosystem:
    """执行器生态系统"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 核心组件
        self.plugin_manager = PluginManager()
        self.integration_hub = IntegrationHub()
        self.developer_toolkit = DeveloperToolkit()

        # 生态统计
        self.ecosystem_stats = {
            "plugins_loaded": 0,
            "integrations_active": 0,
            "tasks_executed": 0,
            "developers_supported": 0
        }

    async def initialize(self):
        """初始化生态系统"""
        self.logger.info("🌍 初始化执行器生态系统")

        # 初始化插件管理器
        await self.plugin_manager.initialize()

        # 初始化集成中心
        await self.initialize_integrations()

        # 更新统计信息
        self.update_ecosystem_stats()

        self.logger.info("✅ 执行器生态系统初始化完成")

    async def initialize_integrations(self):
        """初始化集成"""
        # 示例集成：外部API
        async def external_api_connector():
            class Connector:
                async def test_connection(self, config):
                    # 模拟连接测试
                    return True
            return Connector()

        self.integration_hub.register_integration(
            "external_api",
            "api",
            {"endpoint": "https://api.example.com", "timeout": 30},
            await external_api_connector()
        )

    def update_ecosystem_stats(self):
        """更新生态统计"""
        plugins = self.plugin_manager.list_plugins()
        self.ecosystem_stats.update({
            "plugins_loaded": len([p for p in plugins if p["status"] == "active"]),
            "integrations_active": len([
                i for i in self.integration_hub.get_integration_status().values()
                if i["status"] == "active"
            ]),
            "total_plugins": len(plugins)
        })

    def get_ecosystem_health(self) -> Dict[str, Any]:
        """获取生态健康状态"""
        plugin_health = len([
            p for p in self.plugin_manager.list_plugins()
            if p["status"] == "active"
        ]) / max(len(self.plugin_manager.list_plugins()), 1)

        integration_health = len([
            i for i in self.integration_hub.get_integration_status().values()
            if i["status"] == "active"
        ]) / max(len(self.integration_hub.integrations), 1)

        return {
            "overall_health": (plugin_health + integration_health) / 2,
            "plugin_health": plugin_health,
            "integration_health": integration_health,
            "stats": self.ecosystem_stats
        }

    def create_plugin_from_template(
        self,
        plugin_name: str,
        task_types: List[str],
        output_path: Optional[str] = None
    ) -> str:
        """从模板创建插件"""
        template = self.developer_toolkit.create_plugin_template(plugin_name, task_types)

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(template)

            self.logger.info(f"✅ 插件模板已保存到: {output_path}")

        return template

    def validate_and_load_plugin(self, plugin_code: str, plugin_name: str) -> Dict[str, Any]:
        """验证并加载插件"""
        # 验证插件代码
        validation = self.developer_toolkit.validate_plugin(plugin_code)

        if not validation["valid"]:
            return {
                "success": False,
                "validation": validation
            }

        try:
            # 动态创建插件类
            local_vars = {}
            exec(plugin_code, {"ExecutorPlugin": ExecutorPlugin}, local_vars)

            # 查找插件类
            plugin_class = None
            for name, obj in local_vars.items():
                if (isinstance(obj, type) and
                    issubclass(obj, ExecutorPlugin) and
                    obj != ExecutorPlugin):
                    plugin_class = obj
                    break

            if not plugin_class:
                return {
                    "success": False,
                    "error": "未找到有效的插件类"
                }

            # 实例化并注册
            asyncio.create_task(self.plugin_manager.register_plugin(plugin_class()))

            return {
                "success": True,
                "plugin_class": plugin_class.__name__,
                "validation": validation
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "validation": validation
            }

    def generate_ecosystem_report(self) -> str:
        """生成生态报告"""
        stats = self.ecosystem_stats
        health = self.get_ecosystem_health()

        report = f"""# 执行器生态系统报告

## 概览
- **插件数量**: {stats['total_plugins']} (活跃: {stats['plugins_loaded']})
- **集成数量**: {len(self.integration_hub.integrations)} (活跃: {stats['integrations_active']})
- **生态健康度**: {health['overall_health']:.1%}

## 插件详情
"""

        for plugin in self.plugin_manager.list_plugins():
            report += f"""### {plugin['name']} (v{plugin['version']})
- **状态**: {plugin['status']}
- **支持任务**: {', '.join(plugin['supported_task_types'])}
- **能力**: {', '.join(plugin['capabilities'].keys())}
"""

        report += """
## 集成详情
"""

        for name, info in self.integration_hub.get_integration_status().items():
            report += f"""### {name}
- **类型**: {info['type']}
- **状态**: {info['status']}
"""

        return report


# 全局生态系统实例
_ecosystem_instance = None

def get_executor_ecosystem() -> ExecutorEcosystem:
    """获取执行器生态系统实例"""
    global _ecosystem_instance
    if _ecosystem_instance is None:
        _ecosystem_instance = ExecutorEcosystem()
    return _ecosystem_instance

async def initialize_executor_ecosystem():
    """初始化执行器生态系统"""
    ecosystem = get_executor_ecosystem()
    await ecosystem.initialize()
    logger.info("✅ 执行器生态系统初始化完成")
    return ecosystem
